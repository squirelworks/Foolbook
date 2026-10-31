"""A graded answer goes to the quiz's next page when right, its again page when wrong.

The question is written for this test.
"""

from __future__ import annotations

import unittest

from engine.engine import click
from foolbook.model import Book, Page, RuntimeState


def _state(**quiz):
    quiz = dict({"question": "What is frozen water called?",
                 "choices": [{"label": "Steam", "correct": False}, {"label": "Ice", "correct": True}]}, **quiz)
    shapes = [{"kind": "button", "name": "Choice 1", "choice": 0},
              {"kind": "button", "name": "Choice 2", "choice": 1}]
    pages = [Page(id="Q", quiz=quiz, shapes=shapes), Page(id="Again"), Page(id="Done")]
    return RuntimeState(book=Book(path="q.fbk", pages=pages)), shapes


class ChoiceNextTests(unittest.TestCase):
    def test_right_goes_to_next(self):
        state, shapes = _state(next="Done", again="Again")
        self.assertTrue(click(state, shapes[1]))
        self.assertEqual(state.page.id, "Done")

    def test_wrong_goes_to_again(self):
        state, shapes = _state(next="Done", again="Again")
        self.assertTrue(click(state, shapes[0]))
        self.assertEqual(state.page.id, "Again")

    def test_no_page_named_stays(self):
        state, shapes = _state()
        self.assertFalse(click(state, shapes[1]))
        self.assertEqual(state.page.id, "Q")

    def test_the_button_script_wins(self):
        state, shapes = _state(next="Done", again="Again")
        shapes[1]["script"] = 'go to page "Again"\n'
        self.assertTrue(click(state, shapes[1]))
        self.assertEqual(state.page.id, "Again")


if __name__ == "__main__":
    unittest.main()
