"""Book resource session.

`RESMGRCONNECT` is the only static caller of `HEAPREGISTER`. It keeps
seven words: an instance, the heap, and two proc-instances. The second
proc-instance is the heap callback at heap `+0x20`.

`send` is `RESMGRSENDMSG`. Cases that were read:

| Word | Export |
|---|---|
| 2 | extract (`RESMGREXTRACT` / `RESMGREXTRACTGDI` differ by a 0/1 flag; the shared body was not read, so both return the same bytes) |
| 3 | replace |
| 4 | enum, which stops when the callback returns 0 |
| 5 | set a flag and call `RESMGRSENDMESSAGE` (that body was not read) |
| 6 | get name |
| 7 | set name |

Case 1 and the default are not handled. `LOADRESSTR` is not this module.

Replace of type `0x13` asks the refcount. A nonzero count keeps the
previous bytes. Type `0x10` is the other message that carries extra
words; it does not ask the refcount. Those two type numbers are the
ones `RESMGRREPLACE` tests, not a claim about what the bytes mean.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.heap import ERR_OOM, Errors, HeapDirectory, ScriptHeap
from engine.stack import ValueStack


ERR_SESSION = 0x0F
ERR_HEAP = 0x0D
ERR_PROC = 0x39

MSG_EXTRACT = 2
MSG_REPLACE = 3
MSG_ENUM = 4
MSG_FORWARD = 5
MSG_GETNAME = 6
MSG_SETNAME = 7

TYPE_KEEP = 0x10
TYPE_REF = 0x13

_SHARED = HeapDirectory()


@dataclass
class LiveResource:
    book: int
    name: str
    type_id: int
    data: bytes
    refcount: int = 0
    held: bytes | None = None
    extended: bool = False


@dataclass
class ResourceSession:
    heap: ScriptHeap
    on_heap: object
    on_instance: object
    directory: HeapDirectory
    instance: int
    errors: Errors = field(default_factory=Errors)
    books: dict = field(default_factory=dict)
    resources: list = field(default_factory=list)
    frame: object = None
    stack: ValueStack | None = None
    book_ref: int | None = None
    last_gdi: bool = False
    forwarded: bool = False
    unhandled: int | None = None
    alive: bool = True
    _next_book: int = 1

    def adopt(self, book) -> int:
        """Open this book and register the resources its loader found."""
        if self.book_ref is not None:
            self.close_book(self.book_ref)
        title = getattr(book, "title", "") or getattr(book, "path", "")
        self.book_ref = self.open_book(str(title))
        for raw in getattr(book, "resources", None) or []:
            if not isinstance(raw, dict):
                continue
            data = raw.get("data", b"")
            if isinstance(data, str):
                data = data.encode("latin-1", "replace")
            type_id = raw.get("type") or 0
            refcount = raw.get("refcount") or 0
            try:
                type_id = int(type_id)
                refcount = int(refcount)
            except (TypeError, ValueError):
                continue
            self.add(
                self.book_ref,
                raw.get("name") or "",
                type_id,
                bytes(data),
                refcount,
            )
        self.begin_script()
        return self.book_ref

    def begin_script(self) -> ValueStack | None:
        if self.frame is None:
            self.frame = self.heap.create_frame(handler=self.on_heap, bp=0)
            if self.frame is None:
                self.errors.set(ERR_OOM)
                return None
        if self.stack is not None:
            self.stack.free()
        self.stack = ValueStack(self.heap, self.frame.index, self.errors)
        if not self.stack.alive:
            return None
        return self.stack

    def open_book(self, name: str) -> int:
        ref = self._next_book
        self._next_book += 1
        self.books[ref] = name
        return ref

    def close_book(self, ref: int) -> None:
        self.books.pop(ref, None)
        self.resources = [r for r in self.resources if r.book != ref]
        if self.book_ref == ref:
            self.book_ref = None

    def add(self, book: int, name: str, type_id: int, data: bytes, refcount: int = 0) -> LiveResource:
        res = LiveResource(book, name, type_id, data, refcount)
        self.resources.append(res)
        return res

    def find(self, name: str, book: int | None = None, type_id: int | None = None) -> LiveResource | None:
        for res in self.resources:
            if book is not None and res.book != book:
                continue
            if type_id is not None and res.type_id != type_id:
                continue
            if res.name == name:
                return res
        return None

    def extract(self, res: LiveResource, gdi: bool = False) -> bytes:
        self.last_gdi = gdi
        return res.data

    def refcount(self, res: LiveResource) -> int:
        return res.refcount

    def replace(self, res: LiveResource, data: bytes) -> bool:
        if res.type_id in (TYPE_KEEP, TYPE_REF):
            res.extended = True
        if res.type_id == TYPE_REF and self.refcount(res):
            res.held = res.data
        res.data = data
        return True

    def enum(self, callback, book: int | None = None) -> int:
        """Visit resources. A callback result of 0 stops, and that visit counts.

        Running out of resources is the `'B'` status the decompile clears.
        It does not add a visit.
        """
        visited = 0
        for res in list(self.resources):
            if book is not None and res.book != book:
                continue
            visited += 1
            if callback(res) == 0:
                break
        return visited

    def get_name(self, res: LiveResource) -> str:
        return res.name

    def set_name(self, res: LiveResource, name: str) -> bool:
        res.name = name
        return True

    def send(self, kind: int, **kw):
        """`RESMGRSENDMSG`. Unknown kinds, including case 1, are refused."""
        if kind == MSG_FORWARD:
            self.forwarded = True
            hook = kw.get("hook")
            return hook(**kw) if hook else None
        if kind == MSG_EXTRACT:
            return self.extract(kw["resource"], gdi=bool(kw.get("gdi")))
        if kind == MSG_REPLACE:
            return self.replace(kw["resource"], kw["data"])
        if kind == MSG_ENUM:
            return self.enum(kw["callback"], kw.get("book"))
        if kind == MSG_GETNAME:
            return self.get_name(kw["resource"])
        if kind == MSG_SETNAME:
            return self.set_name(kw["resource"], kw["name"])
        self.unhandled = kind
        return None

    def disconnect(self) -> None:
        if self.stack is not None:
            self.stack.free()
            self.stack = None
        if self.heap is not None and self.heap.alive:
            self.heap.deregister(self.directory)
        self.alive = False


def connect(on_heap, on_instance, directory: HeapDirectory | None = None,
            alloc_ok: bool = True, session_ok: bool = True):
    """Open a session the way `RESMGRCONNECT` does.

    Missing either callback is `0x39`. A heap that cannot be registered
    is `0x0D`. `session_ok=False` is the `0x0F` path: the 14-byte
    session block, which does not fail on its own in Python.
    """
    if not session_ok:
        return None, ERR_SESSION
    if on_heap is None or on_instance is None:
        return None, ERR_PROC
    directory = directory if directory is not None else _SHARED
    heap = ScriptHeap.register(directory, on_heap, alloc_ok=alloc_ok)
    if heap is None:
        return None, ERR_HEAP
    session = ResourceSession(
        heap=heap,
        on_heap=on_heap,
        on_instance=on_instance,
        directory=directory,
        instance=1,
    )
    return session, 0
