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
        from datetime import date
        courses = self.data.setdefault("courses", {})
        rec = courses.setdefault(course_id, {})
        rec["completed"] = True
        rec.setdefault("completed_on", date.today().isoformat())
        self._save()

    def record_answer(self, course_id: str, page_id: str, correct: bool) -> dict:
        """Record one quiz answer. Same shape Foolcourse reads."""
        if not course_id or not page_id:
            return {}
        courses = self.data.setdefault("courses", {})
        rec = courses.setdefault(course_id, {})
        rec["opened"] = True
        score = rec.setdefault("score", {})
        answers = score.setdefault("answers", {})
        answers[page_id] = bool(correct)
        correct_n = sum(1 for v in answers.values() if v)
        answered = len(answers)
        percent = (100.0 * correct_n / answered) if answered else 0.0
        score["correct"] = correct_n
        score["answered"] = answered
        score["percent"] = round(percent, 1)
        best = score.get("best")
        score["best"] = round(percent, 1) if best is None else round(max(best, percent), 1)
        rec["attempts"] = int(rec.get("attempts") or 0) + 1
        self._save()
        return {"correct": correct_n, "answered": answered, "percent": score["percent"], "best": score["best"]}

    def course_score(self, course_id: str) -> dict:
        rec = (self.data.get("courses") or {}).get(course_id) or {}
        score = rec.get("score") or {}
        return {
            "correct": score.get("correct") or 0,
            "answered": score.get("answered") or 0,
            "percent": score.get("percent"),
            "best": score.get("best"),
        }

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
