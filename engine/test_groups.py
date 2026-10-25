"""hide group, show group and visible of group act on the shapes that carry the group's name."""

from __future__ import annotations

import unittest

from engine.engine import _eval, run_handler, split_handlers
from foolbook.model import Book, Page, RuntimeState


def _shape(name, *groups):
    return {"kind": "text", "name": name, "x": 0, "y": 0, "w": 10, "h": 10, "visible": True, "groups": list(groups)}


def _state(source="", other_page=False):
    shapes = [_shape("standard1", "Review 1"), _shape("Review 1", "Review 1"), _shape("standard2", "Review 2"),
              _shape("Review 2", "Review 2"), _shape("Next"), _shape("inner", "Outer Thing", "Review 1")]
    pages = [Page(id="P1", shapes=shapes, handlers=split_handlers(source))]
    if other_page:
        pages.append(Page(id="P2", shapes=[_shape("far", "Far")]))
    return RuntimeState(book=Book(path="x", pages=pages)), shapes


def _visible(shapes):
    return {s["name"]: s["visible"] for s in shapes}


class GroupVisible(unittest.TestCase):
    def test_hide_group_hides_every_member_and_no_other(self):
        state, shapes = _state('to handle buttonClick\n  hide group "Review 1"\nend\n')
        run_handler(state, state.page.handlers[0].source)
        self.assertEqual(_visible(shapes), {"standard1": False, "Review 1": False, "standard2": True, "Review 2": True,
                                           "Next": True, "inner": False})

    def test_show_group_brings_them_back(self):
        state, shapes = _state('to handle buttonClick\n  show group "review 2"\nend\n')
        for s in shapes:
            s["visible"] = False
        run_handler(state, state.page.handlers[0].source)
        self.assertEqual([s["name"] for s in shapes if s["visible"]], ["standard2", "Review 2"])

    def test_set_visible_of_group_to_false(self):
        state, shapes = _state('to handle buttonClick\n  set visible of group "Review 2" to false\nend\n')
        run_handler(state, state.page.handlers[0].source)
        self.assertFalse(shapes[2]["visible"] or shapes[3]["visible"])
        self.assertTrue(shapes[0]["visible"])

    def test_the_name_may_be_an_expression_of_a_variable(self):
        state, shapes = _state()
        state.variables["i"] = 2
        run = split_handlers('to handle buttonClick\n  set visible of group("Review" && i) to false\nend\n')[0]
        run_handler(state, run.source)
        self.assertFalse(shapes[3]["visible"])
        self.assertTrue(shapes[1]["visible"])

    def test_of_page_reaches_another_page_of_the_book(self):
        state, _shapes = _state(other_page=True)
        run = split_handlers('to handle buttonClick\n  hide group "Far" of page "P2"\nend\n')[0]
        run_handler(state, run.source)
        self.assertFalse(state.book.pages[1].shapes[0]["visible"])

    def test_play_animation_ends_with_the_group_shown(self):
        state, shapes = _state()
        for s in shapes:
            s["visible"] = False
        run = split_handlers('to handle buttonClick\n  send playanimation 1, null, true to group "Review 2"\nend\n')[0]
        run_handler(state, run.source)
        self.assertEqual([s["name"] for s in shapes if s["visible"]], ["standard2", "Review 2"])

    def test_visible_of_group_reads_back(self):
        state, shapes = _state()
        self.assertIs(_eval('visible of group "Review 1"', state), True)
        self.assertIs(_eval('visible of group "Review 1" is true', state), True)
        self.assertIs(_eval('visible of group "Review 1" is false', state), False)
        for s in shapes:
            if "Review 1" in s["groups"]:
                s["visible"] = False
        self.assertIs(_eval('visible of group "Review 1" is false', state), True)
        self.assertIs(_eval('visible of group "Review 1" = true', state), False)

    def test_is_object_is_true_only_for_a_group_the_page_has(self):
        state, _ = _state()
        state.variables["i"] = 1
        self.assertIs(_eval('isobject(group("Review" && i))', state), True)
        state.variables["i"] = 3
        self.assertIs(_eval('isobject(group("Review" && i))', state), False)
        self.assertIs(_eval('isObject(group "Nope")', state), False)


if __name__ == "__main__":
    unittest.main()
