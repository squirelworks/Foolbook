"""show and hide a shape by its name, whatever its kind, for .fbk scripts.

The NIDA guard runs when NIDA_BOOKS names a folder holding the book.
The books are not in this repository.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from engine.engine import run_handler, run_page_handlers
from engine.loader import load
from foolbook.model import Book, Page, RuntimeState


def _state():
    shapes = [
        {"kind": "text", "name": "Feedback", "visible": False},
        {"kind": "hotspot", "name": "map"},
        {"kind": "button", "name": "Next", "visible": False},
    ]
    other = [{"kind": "rect", "name": "far", "visible": False}]
    book = Book(path="b.fbk", pages=[Page(id="P1", shapes=shapes), Page(id="P2", shapes=other)])
    return RuntimeState(book=book), shapes, other


class ShowHideByNameTests(unittest.TestCase):
    def test_show_a_name(self):
        state, shapes, _ = _state()
        run_handler(state, 'show "feedback"')
        self.assertIs(shapes[0]["visible"], True)
        self.assertIs(shapes[2]["visible"], False)

    def test_hide_shape_of_a_kind_with_no_class_word(self):
        state, shapes, _ = _state()
        run_handler(state, 'hide shape "Map"')
        self.assertIs(shapes[1]["visible"], False)

    def test_of_page(self):
        state, _, other = _state()
        run_handler(state, 'show "far" of page "P2"')
        self.assertIs(other[0]["visible"], True)

    def test_the_class_form_still_works(self):
        state, shapes, _ = _state()
        run_handler(state, 'show button "next"')
        self.assertIs(shapes[2]["visible"], True)

    def test_show_group_is_not_a_name(self):
        state, shapes, _ = _state()
        actions = run_handler(state, 'show group "feedback"')
        self.assertEqual(actions[0]["target"], "visible of group")
        self.assertIs(shapes[0]["visible"], False)


class NidaShowHideTests(unittest.TestCase):
    def test_93951104_p3080_hide_ellipse_blank_on_leave(self):
        path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / "93951104.fbk"
        if not path.exists():
            raise unittest.SkipTest("93951104.fbk is not here; set NIDA_BOOKS")
        book = load(path)
        state = RuntimeState(book=book)
        state.index = [p.id for p in book.pages].index("P3080")
        state.variables["syslevel"] = "reader"
        blank = [s for s in state.page.shapes if (s.get("name") or "").lower() == "blank"]
        run_page_handlers(state, "enterpage")
        self.assertEqual([s.get("visible") for s in blank], [True])
        actions = run_page_handlers(state, "leavepage")
        self.assertEqual([s.get("visible") for s in blank], [False])
        self.assertNotIn("visible of shape", [a.get("target") for a in actions])


if __name__ == "__main__":
    unittest.main()
