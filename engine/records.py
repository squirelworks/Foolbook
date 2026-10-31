"""Records on a Foolbook page: rows of data, one shown at a time.

A page may carry `records`: `fields`, the names of the text shapes that
show a row; `rows`, a list of rows, one string per field; and `at`, the
row shown. A button whose `item` is `{"record": "next"}` or
`{"record": "previous"}` steps one row. The first and last rows do not
wrap. This is data on the page, not a database.
"""

from __future__ import annotations


def _records(page) -> dict | None:
    found = (getattr(page, "raw", None) or {}).get("records")
    if not isinstance(found, dict) or not found.get("fields"):
        return None
    return found


def fill(page) -> None:
    """Put the current row in the fields that name it."""
    found = _records(page)
    if found is None:
        return
    rows = found.get("rows") or []
    at = min(max(0, int(found.get("at") or 0)), max(0, len(rows) - 1))
    found["at"] = at
    row = list(rows[at]) if rows else []
    by_name = {str(name).lower(): n for n, name in enumerate(found["fields"])}
    for shape in page.shapes or []:
        if (shape.get("kind") or "") != "text":
            continue
        n = by_name.get((shape.get("name") or "").lower())
        if n is not None:
            shape["text"] = str(row[n]) if n < len(row) else ""


def step(page, direction: str) -> bool:
    """Next or previous row. True when the row changed."""
    found = _records(page)
    if found is None:
        return False
    rows = found.get("rows") or []
    at = int(found.get("at") or 0)
    to = at + (1 if direction == "next" else -1 if direction == "previous" else 0)
    if to == at or not (0 <= to < len(rows)):
        return False
    found["at"] = to
    fill(page)
    return True
