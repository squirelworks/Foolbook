"""Progression tracking.

Scaffold. The viewer records which pages have been visited and resumes
at the last page. A path ending in .fcs is an encrypted student file. Extracted, it is
JSON. Anything else is plain JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from progress.fcs import pack, unpack


class Progress:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data: dict = {"courses": {}}
        if self.path.exists():
            try:
                self.data = self._read()
            except Exception:
                self.data = {"courses": {}}
        self.data.setdefault("courses", {})

    def status(self, course_id: str) -> str:
        rec = (self.data.get("courses") or {}).get(course_id) or {}
        if rec.get("completed"):
            return "done"
        if rec.get("opened"):
            return "started"
        return ""

    def touch(self, course_id: str) -> None:
        if not course_id:
            return
        courses = self.data.setdefault("courses", {})
        rec = courses.setdefault(course_id, {})
        rec["opened"] = True
        self._save()

    def mark_page(self, course_id: str, page_id: str) -> None:
        """Record that a page was visited. Called by the viewer later."""
        if not course_id or not page_id:
            return
        courses = self.data.setdefault("courses", {})
        rec = courses.setdefault(course_id, {})
        rec["opened"] = True
        visited = rec.setdefault("visited", [])
        if page_id not in visited:
            visited.append(page_id)
        rec["last_page"] = page_id
        self._save()

    def last_page(self, course_id: str) -> str:
        rec = (self.data.get("courses") or {}).get(course_id) or {}
        return rec.get("last_page") or ""

    def visited(self, course_id: str) -> list[str]:
        rec = (self.data.get("courses") or {}).get(course_id) or {}
        return list(rec.get("visited") or [])

    def complete(self, course_id: str) -> None:
        courses = self.data.setdefault("courses", {})
        rec = courses.setdefault(course_id, {})
        rec["completed"] = True
        self._save()

    def _read(self) -> dict:
        blob = self.path.read_bytes()
        if self.path.suffix.lower() == ".fcs" or blob[:4] == b"FCS1":
            return unpack(blob)
        return json.loads(blob.decode("utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.suffix.lower() == ".fcs":
            self.path.write_bytes(pack(self.data))
        else:
            self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
