"""Book API.

This is the `CDB*` layer of TB80BAS (record chapter 20). Ordinals 1
through 56 are this family. RTM links it. It is not the object memory,
and it is not the record reader.

`CDBFILEOPEN` does not call `OBJFILEOPEN`. The decompile reaches the
object file through unnamed helpers in the same segment. Foolbook takes
that as one open. The helper bodies were not read.

`CDBGETVALUE`, `CDBSETVALUE`, and `CDBSENDVALUE` are one call into the
`EX` form, with `0` in the extra argument. The `EX` form locks, runs
the object's behavior, and unlocks.
"""

from __future__ import annotations

from engine.obj import ObjectLayer


class BookApi:
    def __init__(self, objects: ObjectLayer | None = None) -> None:
        self.objects = objects if objects is not None else ObjectLayer()
        self.trace = self.objects.trace

    def init(self) -> None:
        """`CDBINIT`. Starts `OBJINIT` once."""
        self.trace.append("CDBINIT")
        self.objects.init(0x242, 7)

    def adopt(self, book) -> None:
        """Host side, not a `CDB*` export.

        Opens through `file_open`, then registers named objects. The
        book exports do not allocate. Allocation is `OBJNEWNEAR`.
        """
        self.file_open(str(getattr(book, "path", "") or ""))
        raws = list(getattr(book, "objects", None) or [])
        for page in getattr(book, "pages", None) or []:
            for item in getattr(page, "items", None) or []:
                if isinstance(item, dict) and item.get("name"):
                    raws.append(item)
        for raw in raws:
            if not isinstance(raw, dict):
                continue
            obj = self.objects.new_near(str(raw.get("name") or ""))
            props = raw.get("props") if isinstance(raw.get("props"), dict) else {}
            for key, value in props.items():
                obj.props[str(key).lower()] = value

    def file_open(self, path: str) -> int:
        self.trace.append("CDBFILEOPEN")
        return self._open_helper(path)

    def file_merge(self, path: str) -> int:
        """Also reaches the helper. `CDBFILEMERGE` calls `FUN_1048_1cc4`."""
        self.trace.append("CDBFILEMERGE")
        return self._open_helper(path)

    def create_book_ref(self, path: str) -> int:
        """`CDBCREATEBOOKREF` calls the same helper as file open."""
        self.trace.append("CDBCREATEBOOKREF")
        return self._open_helper(path)

    def _open_helper(self, path: str) -> int:
        """`FUN_1048_1cc4` then `FUN_1048_1766`. Both were not read.

        `FUN_1030_02fc` is the other caller of `1766` from `CDBFILEOPEN`.
        One open stands for that graph. It is not two opens.
        """
        self.trace.append("FUN_1048_1cc4")
        self.trace.append("FUN_1048_1766")
        return self.objects.file_open(path)

    def file_close(self) -> None:
        """`CDBFILECLOSE` does not call `OBJFILECLOSE`."""
        self.trace.append("CDBFILECLOSE")

    def file_save_as(self, path: str) -> None:
        """`CDBFILESAVEAS` closes the object file and copies it."""
        self.trace.append("CDBFILESAVEAS")
        self.objects.file_close()
        self.objects.file_copy()
        self.objects.file.path = str(path)

    def file_new(self, index: int) -> None:
        """`CDBFILENEW`: lock, touch, unlock."""
        self.trace.append("CDBFILENEW")
        self.objects.lock(index)
        self.objects.touch(index)
        self.objects.unlock(index)

    def get_value(self, index: int, prop: str):
        self.trace.append("CDBGETVALUE")
        return self.get_value_ex(index, prop, 0)

    def set_value(self, index: int, prop: str, value):
        self.trace.append("CDBSETVALUE")
        return self.set_value_ex(index, prop, value, 0)

    def send_value(self, index: int, prop: str, value=None):
        self.trace.append("CDBSENDVALUE")
        return self.send_value_ex(index, prop, value, 0)

    def get_value_ex(self, index: int, prop: str, extra: int = 0):
        self.trace.append("CDBGETVALUEEX")
        return self._dispatch(index, "get", prop, None, extra)

    def set_value_ex(self, index: int, prop: str, value, extra: int = 0):
        self.trace.append("CDBSETVALUEEX")
        return self._dispatch(index, "set", prop, value, extra)

    def send_value_ex(self, index: int, prop: str, value=None, extra: int = 0):
        self.trace.append("CDBSENDVALUEEX")
        return self._dispatch(index, "send", prop, value, extra)

    def _dispatch(self, index: int, op: str, prop: str, value, extra: int):
        obj = self.objects.lock_near(index)
        if obj is None:
            return None
        try:
            key = prop.lower()
            got = None
            if obj.behavior is not None:
                got = obj.behavior(op, key, value, extra)
            if op == "get":
                if obj.behavior is not None:
                    return got
                return obj.props.get(key)
            if op == "set":
                obj.props[key] = value
                return value
            return got if obj.behavior is not None else value
        finally:
            self.objects.unlock(index)
