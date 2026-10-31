"""A page book names one system book. Its handlers run before the approximations."""

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
to get echo word
    return word
end
to get handleQuizClick choice
    return "shared"
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


class SystemHandlers(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_book_names_its_system_book(self):
        state = _open(self.tmp, "shared.fsk")
        self.assertEqual(state.book.shells, ["shared.fsk"])

    def test_send_runs_the_system_handler(self):
        state = _open(self.tmp, "shared.fsk")
        self.assertTrue(follow(state, run_handler(state, "send goEnd")))
        self.assertEqual(state.page.id, "P200")

    def test_a_call_returns_the_system_value(self):
        state = _open(self.tmp, "shared.fsk")
        run_handler(state, 'x = echo("hello")')
        self.assertEqual(state.variables["x"], "hello")

    def test_the_system_book_wins_over_the_approximation(self):
        state = _open(self.tmp, "shared.fsk")
        run_handler(state, 'answer = handleQuizClick("A")')
        self.assertEqual(state.variables["answer"], "shared")

    def test_without_a_system_book_the_approximation_answers(self):
        state = _open(self.tmp, None)
        run_handler(state, 'answer = handleQuizClick("A")')
        self.assertNotEqual(state.variables.get("answer"), "shared")
        self.assertFalse(follow(state, run_handler(state, "send goEnd")))
        self.assertEqual(state.page.id, "P0")


if __name__ == "__main__":
    unittest.main()
