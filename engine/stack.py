"""OpenScript value stack. Tag `0x10` on the NearScript heap.

Not the CPU stack. A chunk holds `0x19` elements. An empty element is
the null value (low word 1, high word `0x400`).

`push` follows the `STACKPUSH` switch on `type >> 10`:

- `1, 2, 5, 7, 10, 0xB, 0x14, 0x15, 0x16` push one element
- `8` and `0xC` push one element with `| 0x800` in the high word
  (`VALUEVALUE` itself was not read; the value is not rewritten)
- `0xD` pushes four words, last-in-the-object ending on top
- `0x10` pushes each element of a stack, oldest first
- anything else is stringified and split on commas

A string with no comma is pushed as itself. Pieces are pushed last
first, so the first piece is the one `pop` returns. An empty piece is
null. `CDBCHUNK*` also classifies quotes and whitespace; this splitter
only does the comma, which is what this call site was read for.

Index `0` is the top (the last push). A bad index is `0x38`.
Pop or slip of an empty stack is `0x1FA2`. A count of `0xFFFF` is
`0x1FFF`. Out of memory is `0x1F7A`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.heap import ERR_BAD, ERR_OOM, NULL, Block, ScriptHeap, Value


CHUNK = 0x19
TAG_STACK = 0x10
HEADER_SIZE = 0xC
ERR_EMPTY = 0x1FA2
ERR_INDEX = 0x38

_SCALAR = frozenset({1, 2, 5, 7, 10, 0xB, 0x14, 0x15, 0x16})
_BIT = frozenset({8, 0xC})


@dataclass
class ChunkBlock:
    cap: int
    slots: list
    used: int = 0
    alloc_size: int = 0
    value: Value | None = None


@dataclass
class ValueStack:
    heap: ScriptHeap
    frame: int
    errors: object
    count: int = 0
    chunks: list = field(default_factory=list)
    header: Value | None = None
    alive: bool = True

    def __post_init__(self) -> None:
        self.header = self.heap.alloc(HEADER_SIZE, TAG_STACK, self.frame, payload=self)
        if self.header is None:
            self.errors.set(self.heap.error or ERR_OOM)
            self.alive = False
            return
        self._new_chunk(0)
        if not self.chunks:
            if self.header is not None:
                self.heap.free(self.header)
                self.header = None
            self.alive = False

    def _new_chunk(self, requested: int) -> ChunkBlock | None:
        n = requested
        if n == 0 or n > CHUNK:
            n = CHUNK
        size = (n + 3) * 4
        value = self.heap.alloc(size, 0, self.frame)
        if value is None:
            self.errors.set(ERR_OOM)
            return None
        chunk = ChunkBlock(cap=n, slots=[NULL] * n, alloc_size=size, value=value)
        self.chunks.append(chunk)
        return chunk

    def _current(self) -> ChunkBlock | None:
        return self.chunks[-1] if self.chunks else None

    def push_one(self, value: Value) -> bool:
        if not self.alive:
            return False
        if self.count == 0xFFFF:
            self.errors.set(ERR_BAD)
            return False
        chunk = self._current()
        if chunk is None or chunk.used == chunk.cap:
            chunk = self._new_chunk(0)
            if chunk is None:
                return False
        chunk.slots[chunk.used] = value
        chunk.used += 1
        self.count += 1
        self.errors.set(0)
        return True

    def push(self, value: Value) -> bool:
        """`STACKPUSH`. See the module note for the switch."""
        code = value.type_code
        if code in _SCALAR or value.is_null:
            return self.push_one(value)
        if code in _BIT:
            return self.push_one(Value(value.type_code, value.index, value.offset, extra=0x800))
        if code == 0xD:
            return self._push_quad(value)
        if code == TAG_STACK:
            return self._push_stack(value)
        return self._push_text(value)

    def _payload(self, value: Value):
        block = self.heap.pointer(value)
        return None if block is None else block.payload

    def _push_quad(self, value: Value) -> bool:
        payload = self._payload(value)
        if not isinstance(payload, (list, tuple)) or len(payload) != 4:
            self.errors.set(ERR_BAD)
            return False
        boxed: list[Value] = []
        for word in payload:
            if isinstance(word, Value):
                boxed.append(word)
            else:
                made = self.heap.alloc(4, 0xB, self.frame, payload=word)
                if made is None:
                    self.errors.set(ERR_OOM)
                    return False
                boxed.append(made)
        # Words 3, 2, 1, then 0, so word 0 is what pop returns.
        for item in reversed(boxed):
            flagged = Value(item.type_code, item.index, item.offset, extra=item.extra | 0x800)
            if not self.push_one(flagged):
                return False
        return True

    def _push_stack(self, value: Value) -> bool:
        other = self._payload(value)
        if not isinstance(other, ValueStack):
            self.errors.set(ERR_BAD)
            return False
        # element(size-1) is the oldest. Push that first.
        for index in range(other.count - 1, -1, -1):
            item = other.element(index)
            if item is None or not self.push_one(item):
                return False
        return True

    def _push_text(self, value: Value) -> bool:
        payload = self._payload(value)
        text = payload if isinstance(payload, str) else _as_text(payload)
        if "," not in text:
            return self.push_one(value)
        parts = text.split(",")
        # Last piece first. pop then yields the first piece.
        for part in reversed(parts):
            if part == "":
                item = NULL
            else:
                made = self.heap.alloc(len(part) + 3, 9, self.frame, payload=part)
                if made is None:
                    self.errors.set(ERR_OOM)
                    return False
                item = made
            if not self.push_one(item):
                return False
        return True

    def pop(self) -> Value | None:
        chunk = self._current()
        if chunk is None or chunk.used == 0:
            self.errors.set(ERR_EMPTY)
            return None
        chunk.used -= 1
        value = chunk.slots[chunk.used]
        chunk.slots[chunk.used] = NULL
        self._note_removed()
        if chunk.used == 0 and len(self.chunks) > 1:
            self.chunks.pop()
        self.errors.set(0)
        return value

    def slip(self) -> Value | None:
        """Take the front element and slide the rest of that chunk down."""
        if not self.chunks or self.chunks[0].used == 0:
            self.errors.set(ERR_EMPTY)
            return None
        chunk = self.chunks[0]
        value = chunk.slots[0]
        for i in range(chunk.used - 1):
            chunk.slots[i] = chunk.slots[i + 1]
        chunk.used -= 1
        chunk.slots[chunk.used] = NULL
        self._note_removed()
        if chunk.used == 0 and len(self.chunks) > 1:
            self.chunks.pop(0)
        self.errors.set(0)
        return value

    def _note_removed(self) -> None:
        if self.count != 0xFFFF:
            self.count -= 1

    def element(self, index: int) -> Value | None:
        """`index` 0 is the top. Past the end is error `0x38`."""
        if self.count == 0xFFFF:
            self.errors.set(ERR_BAD)
            return None
        if index < 0 or index >= self.count:
            self.errors.set(ERR_INDEX)
            return None
        # Forward position of "index from the end".
        want = self.count - index - 1
        seen = 0
        for chunk in self.chunks:
            if want < seen + chunk.used:
                self.errors.set(0)
                return chunk.slots[want - seen]
            seen += chunk.used
        self.errors.set(ERR_INDEX)
        return None

    def set_element(self, index: int, value: Value) -> bool:
        if index < 0 or index >= self.count:
            self.errors.set(ERR_INDEX)
            return False
        want = self.count - index - 1
        seen = 0
        for chunk in self.chunks:
            if want < seen + chunk.used:
                chunk.slots[want - seen] = value
                self.errors.set(0)
                return True
            seen += chunk.used
        self.errors.set(ERR_INDEX)
        return False

    def size_of(self, value: Value) -> int:
        """Null is 0. A stack header returns its count. `0xFFFF` is `0x1FFF`."""
        if value.is_null:
            return 0
        block = self.heap.pointer(value)
        if block is None or not isinstance(block.payload, ValueStack):
            self.errors.set(ERR_BAD)
            return 0
        stack = block.payload
        if stack.count == 0xFFFF:
            self.errors.set(ERR_BAD)
            return 0
        return stack.count

    def mark(self) -> None:
        """Mark every element, every chunk, and the header."""
        if self.header is not None:
            self.heap.mark(self.header)
        for chunk in self.chunks:
            if chunk.value is not None:
                self.heap.mark(chunk.value)
            for i in range(chunk.used):
                slot = chunk.slots[i]
                if not slot.is_null:
                    self.heap.mark(slot)

    def free(self) -> None:
        if self.header is not None:
            self.heap.free(self.header)
            self.header = None
        for chunk in self.chunks:
            if chunk.value is not None:
                self.heap.free(chunk.value)
        self.chunks.clear()
        self.count = 0
        self.alive = False

    def push_py(self, obj) -> bool:
        """Box a Python value and push it. Lists become a nested stack."""
        if obj is None:
            return self.push(NULL)
        if isinstance(obj, bool):
            made = self.heap.alloc(4, 0xB, self.frame, payload=int(obj))
        elif isinstance(obj, int):
            made = self.heap.alloc(4, 0xB, self.frame, payload=obj)
        elif isinstance(obj, float):
            made = self.heap.alloc(8, 0xA, self.frame, payload=obj)
        elif isinstance(obj, str):
            made = self.heap.alloc(len(obj) + 3, 9, self.frame, payload=obj)
        elif isinstance(obj, (list, tuple)):
            nested = ValueStack(self.heap, self.frame, self.errors)
            if not nested.alive:
                return False
            for item in obj:
                if not nested.push_py(item):
                    return False
            return self.push(nested.header)
        else:
            made = self.heap.alloc(0, 0, self.frame, payload=obj)
        if made is None:
            self.errors.set(self.heap.error or ERR_OOM)
            return False
        return self.push(made)

    def pop_py(self):
        value = self.pop()
        if value is None:
            return None
        return python_of(self.heap, value)


def python_of(heap: ScriptHeap, value: Value):
    if value.is_null:
        return None
    block: Block | None = heap.pointer(value)
    if block is None:
        return None
    if isinstance(block.payload, ValueStack):
        return [python_of(heap, block.payload.element(i)) for i in range(block.payload.count - 1, -1)]
    return block.payload


def _as_text(payload) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    return str(payload)
