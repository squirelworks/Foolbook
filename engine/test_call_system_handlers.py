"""A call reaches the `to get` handler of a system book in sysBooks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.engine import RuntimeState, run_handler
from engine.formats import FSK, pack
from foolbook.model import Book, Handler, Page


def _system_book(folder: Path, name: str, script: str) -> None:
    path = folder / name
    path.write_bytes(pack({"title": path.stem, "pages": [{"id": "P1"}], "script": script}, FSK))


SHARED = """
to get setFlag index
    system int __flag
    scratch = 9
    __flag = index
    return 0
end

to get getQuizScore
    return 77
end

to get gotoMenu
    go to page "P900"
    return 0
end
"""


class CallsReachSystemHandlers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name)
        _system_book(folder, "shared.fsk", SHARED)
        course = Book(path=str(folder / "course.fbk"), title="course", pages=[Page(id="P1")])
        self.state = RuntimeState(book=course)
        run_handler(self.state, 'push "shared.sbk" onto sysBooks')

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_call_binds_its_argument_and_returns(self):
        run_handler(self.state, "get setFlag(3)")
        self.assertEqual(self.state.variables.get("__flag"), 3)

    def test_the_handler_names_stay_its_own(self):
        self.state.variables["index"] = "mine"
        run_handler(self.state, "y = setFlag(5)")
        self.assertEqual(self.state.variables.get("y"), 0)
        self.assertEqual(self.state.variables.get("index"), "mine")
        self.assertNotIn("scratch", self.state.variables)

    def test_the_system_book_answers_before_the_built_in(self):
        # getQuizScore also has a built-in answer. The system book is asked first.
        run_handler(self.state, "s = getQuizScore()")
        self.assertEqual(self.state.variables.get("s"), 77)

    def test_a_go_to_in_the_handler_is_the_callers(self):
        actions = run_handler(self.state, "get gotoMenu()")
        self.assertIn({"kind": "goto", "page": "P900", "book": None}, actions)

    def test_the_book_answers_before_the_system_book(self):
        self.state.book.handlers = [Handler(name="getQuizScore", source="\n    return 5\nend")]
        run_handler(self.state, "s = getQuizScore()")
        self.assertEqual(self.state.variables.get("s"), 5)


if __name__ == "__main__":
    unittest.main()
