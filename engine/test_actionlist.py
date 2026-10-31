"""A shape with an action list does those actions when clicked, unless it has a script."""

import unittest

from engine import actionlist, media
from engine.engine import follow
from foolbook.model import Book, Page, RuntimeState


def _state():
    shapes = [
        {"kind": "button", "name": "Go", "actions": [{"do": "show", "shape": "Answer"}]},
        {"kind": "text", "name": "Answer", "text": "Four", "visible": False},
        {"kind": "text", "name": "Note", "text": ""},
        {"kind": "media", "name": "Clip", "src": "missing.wav"},
    ]
    return RuntimeState(book=Book(path="x", pages=[Page(id="P0", shapes=shapes), Page(id="P1"), Page(id="P2")]))


class ActionList(unittest.TestCase):
    def test_goto_next_and_previous_move_the_page(self):
        state = _state()
        self.assertTrue(follow(state, actionlist.run(state, [{"do": "goto", "page": "P2"}])))
        self.assertEqual(state.index, 2)
        self.assertTrue(follow(state, actionlist.run(state, [{"do": "previous"}])))
        self.assertEqual(state.index, 1)
        self.assertTrue(follow(state, actionlist.run(state, [{"do": "next"}])))
        self.assertEqual(state.index, 2)

    def test_show_hide_and_set_text_change_the_named_shapes(self):
        state = _state()
        actionlist.run(state, [{"do": "show", "shape": "Answer"}, {"do": "settext", "shape": "note", "text": "Well done"}])
        shapes = state.page.shapes
        self.assertTrue(shapes[1]["visible"])
        self.assertEqual(shapes[2]["text"], "Well done")
        actionlist.run(state, [{"do": "hide", "shape": "Answer"}])
        self.assertFalse(shapes[1]["visible"])
        self.assertTrue(state.variables.pop("__redraw"))

    def test_play_asks_the_clip_to_play(self):
        state = _state()
        actionlist.run(state, [{"do": "play", "shape": "Clip"}], base="/nowhere", )
        self.assertTrue(state.page.shapes[3].get("note"))

    def test_a_script_wins_over_the_action_list(self):
        shape = {"kind": "button", "actions": [{"do": "next"}],
                 "script": 'to handle buttonClick\n  go to page "P1"\nend'}
        self.assertEqual(actionlist.to_run(shape), [])
        del shape["script"]
        self.assertEqual(actionlist.to_run(shape), [{"do": "next"}])

    def test_only_known_actions_are_kept(self):
        shape = {"actions": [{"do": "goto", "page": "P1"}, {"do": "explode"}, "next"]}
        self.assertEqual(actionlist.of(shape), [{"do": "goto", "page": "P1"}])


if __name__ == "__main__":
    unittest.main()
