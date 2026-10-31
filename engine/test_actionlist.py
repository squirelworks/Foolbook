"""A shape with an action list moves the page when clicked, unless it has a script."""

import unittest

from engine import actionlist
from engine.engine import follow
from foolbook.model import Book, Page, RuntimeState


def _state():
    return RuntimeState(book=Book(path="x", pages=[Page(id="P0"), Page(id="P1"), Page(id="P2")]))


class ActionList(unittest.TestCase):
    def test_goto_next_and_previous_move_the_page(self):
        state = _state()
        self.assertTrue(follow(state, actionlist.run([{"do": "goto", "page": "P2"}])))
        self.assertEqual(state.index, 2)
        self.assertTrue(follow(state, actionlist.run([{"do": "previous"}])))
        self.assertEqual(state.index, 1)
        self.assertTrue(follow(state, actionlist.run([{"do": "next"}])))
        self.assertEqual(state.index, 2)

    def test_a_script_wins_over_the_action_list(self):
        shape = {"kind": "button", "actions": [{"do": "next"}],
                 "script": 'to handle buttonClick\n  go to page "P1"\nend'}
        self.assertEqual(actionlist.to_run(shape), [])
        del shape["script"]
        self.assertEqual(actionlist.to_run(shape), [{"do": "next"}])

    def test_only_known_actions_are_kept(self):
        shape = {"actions": [{"do": "goto", "page": "P1"}, {"do": "show", "shape": "A"}, {"do": "explode"}, "next"]}
        self.assertEqual(actionlist.of(shape), [{"do": "goto", "page": "P1"}])

    def test_a_shape_without_actions_has_none(self):
        # Every .tbk shape: the loader never sets `actions`.
        self.assertEqual(actionlist.to_run({"kind": "button", "name": "next"}), [])


if __name__ == "__main__":
    unittest.main()
