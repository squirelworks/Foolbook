"""The sidebar lists the sections a book names, not every page id."""

import unittest
from types import SimpleNamespace

from engine.outline import outline


def page(pid, shapes):
    return SimpleNamespace(id=pid, shapes=shapes)


class OutlineTests(unittest.TestCase):
    def test_a_menu_field_is_the_list(self):
        pages = [
            page("P1", [{"name": "Title", "kind": "text", "text": "Title: INTRODUCTION TO CAI"}]),
            page("P100", [{"name": "text", "kind": "text", "text": "a long page of discussion that is not a heading"}]),
            page("P1001", [{"name": "menutext", "kind": "text", "text": "COMPUTER COMMUNICATION    COMPUTER COMMUNICATION"}]),
            page("P1020", [{"name": "text", "kind": "text", "text": "DISCUSSION"}]),
            page("P2001", [{"name": "menutext", "kind": "text", "text": "TYPES OF PAGES"}]),
        ]
        self.assertEqual(
            outline(pages),
            [(0, "INTRODUCTION TO CAI"), (2, "COMPUTER COMMUNICATION"), (4, "TYPES OF PAGES")],
        )

    def test_a_shell_uses_the_heading_on_the_page(self):
        pages = [
            page("P22010", [{"name": "", "kind": "text", "text": "TRAINER SETUP"}]),
            page("P22020", [{"name": "", "kind": "text", "text": "TRAINER SETUP"}]),
            page("P12031", [{"name": "", "kind": "text", "text": "SYNTAX ERROR"}]),
        ]
        self.assertEqual(outline(pages), [(0, "TRAINER SETUP"), (2, "SYNTAX ERROR")])

    def test_a_book_with_no_headings_keeps_the_ids(self):
        pages = [page("P10", []), page("P20", [])]
        self.assertEqual(outline(pages), [(0, "P10"), (1, "P20")])


if __name__ == "__main__":
    unittest.main()
