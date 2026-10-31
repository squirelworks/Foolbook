"""`go to page(n)` with a number goes to the nth page. An element of an array names a page too."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _state():
    pages = [Page(id="P1"), Page(id="P2"), Page(id="P10301")]
    return RuntimeState(book=Book(path="", title="b", pages=pages))


def _goto(actions):
    return [a["page"] for a in actions if a.get("kind") == "goto"]


class GotoPageNumber(unittest.TestCase):
    def test_a_number_in_a_variable_is_a_page_number(self):
        state = _state()
        self.assertEqual(_goto(run_handler(state, "pagename = 2\ngo to page(pagename)")), ["P2"])

    def test_an_array_element_names_the_page(self):
        state = _state()
        script = 'system string pages[]\npages[3] = "P10301"\ngo to page(pages[3])'
        self.assertEqual(_goto(run_handler(state, script)), ["P10301"])

    def test_a_quoted_name_is_still_a_name(self):
        state = _state()
        self.assertEqual(_goto(run_handler(state, 'go to page "P1"')), ["P1"])


if __name__ == "__main__":
    unittest.main()
