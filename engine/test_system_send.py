"""`send NAME` runs the system book's handler of that name."""

import tempfile
import unittest
from pathlib import Path

from engine.engine import follow, run_handler
from engine.formats import pack
from engine.loader import load
from foolbook.model import RuntimeState

SHARED = """to handle goEnd
    go to page "P200"
end
"""


def _open(tmp: Path, system: str | None):
    data = {"id": "lesson", "title": "Lesson", "pages": [{"id": "P0"}, {"id": "P100"}, {"id": "P200"}]}
    if system:
        data["system"] = system
    (tmp / "shared.fsk").write_bytes(pack({"id": "shared", "title": "Shared", "script": SHARED, "pages": []}, "fsk", compress=False))
    path = tmp / "lesson.fbk"
    path.write_bytes(pack(data, compress=False))
    return RuntimeState(book=load(path))


class SystemSend(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_send_runs_the_system_handler(self):
        state = _open(self.tmp, "shared.fsk")
        self.assertTrue(follow(state, run_handler(state, "send goEnd")))
        self.assertEqual(state.page.id, "P200")

    def test_an_unknown_send_is_still_recorded(self):
        state = _open(self.tmp, "shared.fsk")
        self.assertEqual(run_handler(state, "send nothingHere"), [{"kind": "send", "name": "nothingHere"}])

    def test_without_a_system_book_send_stays_on_the_page(self):
        state = _open(self.tmp, None)
        self.assertFalse(follow(state, run_handler(state, "send goEnd")))
        self.assertEqual(state.page.id, "P0")


if __name__ == "__main__":
    unittest.main()
