"""Progression tracking.

Scaffold. The menu records which courses have been opened and, later,
which pages have been completed.

Stored as a small JSON file next to the catalog.
"""

from __future__ import annotations

import json
from pathlib import Path


class Progress:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data: dict = {"courses": {}}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {"courses": {}}

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

    def complete(self, course_id: str) -> None:
        courses = self.data.setdefault("courses", {})
        rec = courses.setdefault(course_id, {})
        rec["completed"] = True
        self._save()

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
