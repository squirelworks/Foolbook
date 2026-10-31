"""`send NAME` runs the nearest `to handle NAME`, up to the system books."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.engine import RuntimeState, run_handler
from engine.formats import FSK, pack
from foolbook.model import Book, Handler, Page


SHARED = """
to handle markDone n
    system int __done
    __done = n
end

to handle showMenu
    go to page "P900"
end
"""


class SendReachesHandlers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name)
        (folder / "shared.fsk").write_bytes(
            pack({"title": "shared", "pages": [{"id": "P1"}], "script": SHARED}, FSK))
        course = Book(path=str(folder / "course.fbk"), title="course", pages=[Page(id="P1"), Page(id="P900")])
        self.state = RuntimeState(book=course)
        run_handler(self.state, 'push "shared.sbk" onto sysBooks')

    def tearDown(self):
        self.tmp.cleanup()

    def test_send_runs_the_system_handler_with_its_argument(self):
        run_handler(self.state, "send markDone 4")
        self.assertEqual(self.state.variables.get("__done"), 4)

    def test_a_go_to_in_the_sent_handler_moves_the_page(self):
        actions = run_handler(self.state, "send showMenu")
        self.assertIn({"kind": "goto", "page": "P900", "book": None}, actions)
        self.assertNotIn({"kind": "send", "name": "showMenu"}, actions)

    def test_the_book_handler_runs_first_and_forward_reaches_the_system_book(self):
        self.state.book.handlers = [Handler(name="markDone", source=" n\n    seen = 1\n    forward\nend")]
        run_handler(self.state, "send markDone 7")
        self.assertEqual(self.state.variables.get("__done"), 7)

    def test_a_send_with_no_handler_is_left_to_the_reader(self):
        actions = run_handler(self.state, "send next")
        self.assertIn({"kind": "send", "name": "next"}, actions)

    def test_a_send_to_a_named_object_is_not_sent_up_from_here(self):
        actions = run_handler(self.state, 'send showMenu to button "OK"')
        self.assertNotIn({"kind": "goto", "page": "P900", "book": None}, actions)


if __name__ == "__main__":
    unittest.main()
