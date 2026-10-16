"""Two heaps and the object array. They do not call each other.

This is the Foolbook form of the 2026-10-16 reading (TBdecompile record,
chapter 19). It is the behavior that was read, not a Win16 allocator.

NearScript (`ScriptHeap`) is the BAS `HEAP*` / `TBHEAP*` frame heap.
A value is a 10-bit index plus a tag. The tag's high bit is the mark.
`TBHEAPCLEARCRITSECT` is a real operation: the crit "section" is a
nesting counter, not a lock. The only registration path in ToolBook is
`RESMGRCONNECT`; `ResourceSession` in `engine/resmgr.py` is that path.

`GHeap` is the UTL wrapper: one block, then sub-allocation. The two
startup blocks are `0x2002 + 0x800`. The `0x16E0` printed by the
decompiler is not a size.

`ObjectArray` grows by `count * 0x76`. That is `FUN_1278_3be6`.
Nothing in `ScriptHeap` treats `0x76` as special.

Not modeled, because the bodies were not read: arena carving
(`FUN_11f0_280c` / `21c4` / `1b18`), the `0xCDBF` argument inside
`HEAPFINDCDBVALUE`, and the rest of `HEAPSWEEPFRAME` after the type
`0x22` destructor.
"""

from __future__ import annotations

from dataclasses import dataclass, field


ERR_OOM = 0x1F7A
ERR_BAD = 0x1FFF

# High word of the null value is 0x400: type 1, index 0. Low word is 1.
NULL_TYPE = 1
NULL_OFFSET = 1

MAGIC = 0xCCDD
FRAME_LIMIT = 0x400
INDEX_LIMIT = 0x400
MAX_BLOCK = 0xFFC5
TAG_CLEANUP = 0x22
DIR_START = 10
DIR_GROW = 9
FREE_SENTINEL = 0xFFFF

# Sizes the startup path actually passes to GHEAPCREATE.
GHEAP_DATA = 0x2002
GHEAP_ZERO = 0x800

OBJECT_STRIDE = 0x76


@dataclass(frozen=True)
class Value:
    """One OpenScript value.

    The high word is `(tag << 10) | index`, then `extra`. ToolBook's
    null is high `0x400` and low `1`. `extra` holds the `| 0x800` the
    stack sets for types 8 and `0xC`; it is not a second tag.
    """

    type_code: int
    index: int
    offset: int
    extra: int = 0

    @property
    def high(self) -> int:
        return ((self.type_code & 0x3F) << 10) | (self.index & 0x3FF) | self.extra

    @property
    def is_null(self) -> bool:
        return self.offset == NULL_OFFSET and self.high == 0x400


NULL = Value(NULL_TYPE, 0, NULL_OFFSET)


@dataclass
class Block:
    index: int
    offset: int
    tag: int
    frame: int
    size: int
    payload: object = None
    marked: bool = False
    methods: dict = field(default_factory=dict)


@dataclass
class Frame:
    index: int
    handler: object = None
    bp: int = 0
    blocks: list = field(default_factory=list)
    cleanup: list = field(default_factory=list)


@dataclass
class Errors:
    """`CDBSETPLERR` as far as this runtime needs it: one code."""

    code: int = 0

    def set(self, code: int) -> None:
        self.code = code


class HeapDirectory:
    """The `DAT_1630_11ae` directory. Capacity starts at 10 and grows by 9.

    Word 2 of the original is a free-list head, `0xFFFF` when empty.
    A directory with no heaps is gone, which is what `HEAPDEREGISTER`
    does on the last one.
    """

    def __init__(self) -> None:
        self.capacity = DIR_START
        self.count = 0
        self.free_head = FREE_SENTINEL
        self.slots: list = [None] * DIR_START
        self.alive = True

    def add(self, heap: "ScriptHeap", alloc_ok: bool = True) -> int | None:
        if not alloc_ok:
            return None
        if not self.alive:
            # The last deregister freed the directory. The next register allocates another.
            self.capacity = DIR_START
            self.count = 0
            self.free_head = FREE_SENTINEL
            self.slots = [None] * DIR_START
            self.alive = True
        if self.free_head != FREE_SENTINEL:
            index = self.free_head
            self.free_head = self.slots[index]
        else:
            if self.capacity <= self.count:
                self.capacity += DIR_GROW
                self.slots.extend([None] * DIR_GROW)
            index = self.count
        self.slots[index] = heap
        self.count += 1
        heap.slot = index
        return index

    def remove(self, heap: "ScriptHeap") -> None:
        index = heap.slot
        if index is None or index >= len(self.slots):
            return
        if self.slots[index] is not heap:
            return
        self.slots[index] = self.free_head
        self.free_head = index
        heap.slot = None
        self.count -= 1
        if self.count == 0:
            self.alive = False


class ScriptHeap:
    """NearScript frame heap. One of these is one `GLOBALALLOC(0x303E)`."""

    def __init__(self, callback=None) -> None:
        self.magic = MAGIC
        self.callback = callback
        self.depth = 1
        self.frames = [Frame(index=0)]
        self.by_index: dict[int, Block] = {}
        self._free_indexes: list[int] = []
        self._next_index = 0
        self._next_offset = 0x100
        self.crit_depth = 0
        self.crit_lo = 0
        self.crit_hi = 0
        self.crit_list: list[Block] = []
        self.error = 0
        self.slot: int | None = None
        self.alive = True

    @classmethod
    def register(cls, directory: HeapDirectory, callback=None, alloc_ok: bool = True):
        heap = cls(callback)
        if directory.add(heap, alloc_ok=alloc_ok) is None:
            return None
        return heap

    def deregister(self, directory: HeapDirectory) -> None:
        """Drop the heap. The callback is released here, as `FREEPROCINSTANCE`."""
        self.callback = None
        self.alive = False
        self.frames.clear()
        self.by_index.clear()
        directory.remove(self)

    def create_frame(self, handler=None, bp: int = 0) -> Frame | None:
        if self.depth == FRAME_LIMIT:
            return None
        frame = Frame(index=len(self.frames), handler=handler, bp=bp & ~1)
        self.frames.append(frame)
        self.depth += 1
        return frame

    def handler_of(self, frame: int):
        return self.frames[frame].handler

    def bp_of(self, frame: int) -> int:
        return self.frames[frame].bp

    def alloc(self, size: int, tag: int, frame: int, payload=None, methods=None) -> Value | None:
        """Allocate. The returned value points past a 4-byte header.

        Header word 0 is the tag. Header word 1 is the frame.
        A size that overflows a 16-bit add of 4, or whose total is
        `>= 0xFFC5`, stores `0x1FFF` and returns null. Out of indexes
        stores `0x1F7A`. While the crit depth is nonzero the block is
        recorded; the unread failure path of `FUN_11f0_15aa` is not
        simulated.
        """
        if not self.alive or frame < 0 or frame >= len(self.frames):
            self.error = ERR_BAD
            return None
        if size < 0 or size > 0xFFFB or (size + 4) == 0 or (size + 4) >= MAX_BLOCK:
            self.error = ERR_BAD
            return None
        if self._free_indexes:
            index = self._free_indexes.pop()
        elif self._next_index < INDEX_LIMIT:
            index = self._next_index
            self._next_index += 1
        else:
            self.error = ERR_OOM
            return None
        block = Block(
            index=index,
            offset=self._next_offset,
            tag=tag & 0x7FFF,
            frame=frame,
            size=size,
            payload=payload,
            methods=dict(methods or {}),
        )
        self._next_offset += max(size, 1)
        self.by_index[index] = block
        self.frames[frame].blocks.append(block)
        if self.crit_depth != 0:
            self.crit_list.append(block)
        self.error = 0
        return Value(block.tag, index, block.offset)

    def free(self, value: Value) -> None:
        """User pointer minus 4. A recycled index is not this value."""
        block = self._block_for(value)
        if block is None:
            return
        self.by_index.pop(block.index, None)
        if block in self.crit_list:
            self.crit_list.remove(block)
        frame = self.frames[block.frame] if block.frame < len(self.frames) else None
        if frame is not None and block in frame.blocks:
            frame.blocks.remove(block)
        if frame is not None and block in frame.cleanup:
            frame.cleanup.remove(block)
        self._free_indexes.append(block.index)

    def pointer(self, value: Value) -> Block | None:
        """`HEAPVALUETOPOINTER`. Index is `high & 0x3FF`. Offset must still match."""
        return self._block_for(value)

    def _block_for(self, value: Value) -> Block | None:
        block = self.by_index.get(value.index & 0x3FF)
        if block is None or block.offset != value.offset:
            return None
        return block

    def frame_of(self, value: Value) -> int | None:
        block = self.pointer(value)
        if block is None:
            return None
        return block.frame

    def add_to_cleanup(self, value: Value) -> bool:
        """Only tag `0x22` is accepted. A second add of the same block is a no-op success."""
        block = self.pointer(value)
        if block is None:
            return False
        if (block.tag & 0x7FFF) != TAG_CLEANUP:
            return False
        frame = self.frames[block.frame]
        if block not in frame.cleanup:
            frame.cleanup.append(block)
        return True

    def mark(self, value: Value) -> None:
        block = self.pointer(value)
        if block is not None:
            block.marked = True

    def reclaim(self, value: Value) -> bool:
        """`FUN_11f0_12ac` for one block.

        A set mark is cleared and the block stays. An unmarked type
        `0x22` is taken off the cleanup list, its `+0x2C` method is
        called, and the block is freed. Anything else is left alone:
        the rest of `HEAPSWEEPFRAME` was not read.
        """
        block = self.pointer(value)
        if block is None:
            return False
        if block.marked:
            block.marked = False
            return True
        if (block.tag & 0x7FFF) == TAG_CLEANUP:
            frame = self.frames[block.frame]
            if block in frame.cleanup:
                frame.cleanup.remove(block)
            dtor = block.methods.get(0x2C)
            if dtor is not None:
                dtor(block)
            self.free(value)
        return False

    def notify(self, handler) -> int:
        """`FUN_11f0_103c`: call this heap's registered proc if a frame matches."""
        if self.callback is None:
            return 0
        hits = 0
        for frame in self.frames:
            if frame.handler == handler:
                self.callback(frame.index)
                hits += 1
        return hits

    def enter_crit(self) -> tuple[int, int]:
        if self.crit_depth != -1:
            self.crit_depth += 1
        return self.crit_lo, self.crit_hi

    def leave_crit(self, lo: int, hi: int) -> None:
        if self.crit_depth == 1 or not _cursor_at_most(hi, lo, self.crit_hi, self.crit_lo):
            self.crit_lo = lo
            self.crit_hi = hi
        if self.crit_depth != 0:
            self.crit_depth -= 1

    def save_crit(self) -> tuple[int, int, int]:
        return self.crit_depth, self.crit_lo, self.crit_hi

    def restore_crit(self, saved: tuple[int, int, int]) -> None:
        depth, lo, hi = saved
        self.crit_depth = depth
        if depth != 0 and _cursor_at_most(hi, lo, self.crit_hi, self.crit_lo):
            return
        self.crit_lo = lo
        self.crit_hi = hi

    def clear_crit(self) -> None:
        self.crit_depth = 0
        self.crit_lo = 0
        self.crit_hi = 0


def _cursor_at_most(hi: int, lo: int, cur_hi: int, cur_lo: int) -> bool:
    return hi < cur_hi or (hi == cur_hi and lo <= cur_lo)


class GHeap:
    """One UTL `GHEAPCREATE` block. Sub-allocations do not escape it.

    `zero` is how many leading bytes `GHEAPCREATE` was asked to clear.
    The listing names the destination `DAT_10f8_0010`; that symbol was
    not checked, so this object just remembers the count.
    """

    def __init__(self, data: int, zero: int) -> None:
        self.data = data
        self.zero = zero
        self.size = data + zero + 0x10
        self._live: dict[int, int] = {}
        self._next = 1
        self.used = 0
        self.alive = True

    def alloc(self, size: int) -> int | None:
        if not self.alive or size < 0:
            return None
        need = size or 1
        if self.used + need > self.size:
            return None
        ident = self._next
        self._next += 1
        self.used += need
        self._live[ident] = need
        return ident

    def free(self, ident: int) -> bool:
        need = self._live.pop(ident, None)
        if need is None:
            return False
        self.used -= need
        return True

    def delete(self) -> None:
        self._live.clear()
        self.alive = False


def startup_heaps() -> tuple[GHeap, GHeap]:
    """The pair `FUN_11a8_0000` creates. Not the script heap."""
    return GHeap(GHEAP_DATA, GHEAP_ZERO), GHeap(GHEAP_DATA, GHEAP_ZERO)


class ObjectArray:
    """Counted array of live objects. Stride is `0x76`. Not a script heap."""

    def __init__(self) -> None:
        self.count = 0
        self.storage = 0

    def grow(self, count: int) -> bool:
        if count < self.count:
            return False
        self.count = count
        self.storage = count * OBJECT_STRIDE
        return True
