"""Object file and object memory.

This is the `OBJ*` layer of TB80BAS (record chapter 20). It is not the
book API, and it is not the record reader. Twenty-six of these exports
live in one NE segment. Other modules do not link them, except
`OBJBOOKVERSION`.

`OBJLOCK` and `OBJLOCKNEAR` were not compared. This layer keeps one
lock count. A missing index does not lock.

The object file returns a handle. It does not parse a page.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.heap import OBJECT_STRIDE, ObjectArray


@dataclass
class LiveObject:
    index: int
    name: str = ""
    props: dict = field(default_factory=dict)
    locked: int = 0
    touched: bool = False
    behavior: object = None


@dataclass
class ObjectFile:
    """What `OBJFILEOPEN` keeps. A handle, not a parsed book."""

    path: str = ""
    is_open: bool = False
    handle: int = 0
    copies: list = field(default_factory=list)

    def open(self, path: str) -> int:
        self.path = str(path)
        self.is_open = True
        self.handle += 1
        return self.handle

    def close(self) -> None:
        self.is_open = False

    def copy(self) -> None:
        self.copies.append(self.path)


class ObjectLayer:
    def __init__(self) -> None:
        self.ready = False
        self.profile = 0
        self.slots: list[LiveObject] = []
        self.file = ObjectFile()
        self.array = ObjectArray()
        self.trace: list[str] = []

    def init(self, size: int = 0x242, count: int = 7) -> None:
        """`OBJINIT`. The second call does not run the body again."""
        if self.ready:
            return
        self.profile = count
        self.ready = True
        self.trace.append("OBJINIT")
        del size  # the 0x242 argument was not read past the call

    def new_near(self, name: str = "") -> LiveObject:
        """`OBJNEWNEAR`. Grows the `0x76` array. Not a book-API call."""
        obj = LiveObject(len(self.slots), name)
        self.slots.append(obj)
        self.array.grow(len(self.slots))
        self.trace.append("OBJNEWNEAR")
        return obj

    def find(self, name: str) -> LiveObject | None:
        key = name.lower()
        for obj in self.slots:
            if obj.name.lower() == key:
                return obj
        return None

    def slot(self, index: int) -> LiveObject | None:
        """The get path masks the index with `0xFF` before the stride."""
        masked = index & 0xFF
        if masked >= len(self.slots):
            return None
        return self.slots[masked]

    def lock(self, index: int) -> LiveObject | None:
        return self._lock(index, "OBJLOCK")

    def lock_near(self, index: int) -> LiveObject | None:
        return self._lock(index, "OBJLOCKNEAR")

    def _lock(self, index: int, name: str) -> LiveObject | None:
        obj = self.slot(index)
        if obj is None:
            return None
        obj.locked += 1
        self.trace.append(name)
        return obj

    def unlock(self, index: int) -> None:
        obj = self.slot(index)
        if obj is None or obj.locked == 0:
            return
        obj.locked -= 1
        self.trace.append("OBJUNLOCK")

    def touch(self, index: int) -> None:
        obj = self.slot(index)
        if obj is None:
            return
        obj.touched = True
        self.trace.append("OBJTOUCH")

    def file_open(self, path: str) -> int:
        self.trace.append("OBJFILEOPEN")
        return self.file.open(path)

    def file_close(self) -> None:
        self.trace.append("OBJFILECLOSE")
        self.file.close()

    def file_copy(self) -> None:
        self.trace.append("OBJFILECOPY")
        self.file.copy()

    @property
    def storage(self) -> int:
        return self.array.storage

    def stride_ok(self) -> bool:
        return self.storage == len(self.slots) * OBJECT_STRIDE
