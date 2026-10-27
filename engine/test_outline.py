"""The sidebar lists main pages by title, not every page."""

import unittest
from types import SimpleNamespace

from engine.outline import every_page, outline


def page(pid, shapes=None, items=None):
    return SimpleNamespace(id=pid, shapes=shapes or [], items=items or [])


class OutlineTests(unittest.TestCase):
    def test_a_menu_field_is_the_list(self):
        pages = [
            page("P1", [{"name": "Title", "kind": "text", "text": "Title: INTRODUCTION TO CAI"}]),
            page("P100", [{"name": "text", "kind": "text", "text": "DISCUSSION"}]),
            page("P1001", [{"name": "menutext", "kind": "text", "text": "COMPUTER COMMUNICATION    COMPUTER COMMUNICATION"}]),
            page("P1020", [{"name": "text", "kind": "text", "text": "DISCUSSION"}]),
            page("P2001", [{"name": "menutext", "kind": "text", "text": "TYPES OF PAGES"}]),
        ]
        self.assertEqual(
            outline(pages),
            [(0, "INTRODUCTION TO CAI"), (2, "COMPUTER COMMUNICATION"), (4, "TYPES OF PAGES")],
        )

    def test_a_demo_menu_is_not_the_main_list(self):
        pages = [
            page("P1", [{"name": "Title", "kind": "text", "text": "Title: INTRODUCTION TO CAI"}]),
            page("P900", items=[{"page": "P1001"}, {"page": "P2001"}]),
            page("P1001", [{"name": "menutext", "kind": "text", "text": "COMPUTER COMMUNICATION"}]),
            page("P2001", [{"name": "menutext", "kind": "text", "text": "TYPES OF PAGES"}], [{"page": "P2020"}]),
            page("P2020", items=[{"page": "P2030"}]),
            page("P2030", items=[{"page": "P2032"}, {"page": "P2043"}]),
            page("P2032", [{"name": "menutext", "kind": "text", "text": "OBJECTIVES"}]),
            page("P2043", [{"name": "menutext", "kind": "text", "text": "FINAL QUIZ"}]),
            page("P10004", [{"name": "menutext", "kind": "text", "text": "FINAL QUIZ"}]),
        ]
        self.assertEqual(
            [label for _index, label in outline(pages)],
            ["INTRODUCTION TO CAI", "COMPUTER COMMUNICATION", "TYPES OF PAGES", "FINAL QUIZ"],
        )

    def test_a_setup_page_is_not_listed(self):
        pages = [
            page("P22010", [{"name": "", "kind": "text", "text": "TRAINER SETUP"}]),
            page("P12031", [{"name": "", "kind": "text", "text": "SYNTAX ERROR"}]),
        ]
        self.assertEqual(outline(pages), [])

    def test_developer_mode_lists_every_id(self):
        pages = [page("P10"), page("P20")]
        self.assertEqual(every_page(pages), [(0, "P10"), (1, "P20")])


if __name__ == "__main__":
    unittest.main()
