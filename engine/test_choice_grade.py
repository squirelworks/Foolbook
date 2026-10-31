"""A quiz answer button is graded by the choice index it stores.

The question is written for this test.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.choice import grade
from engine.engine import click
from foolbook.model import Book, Page, RuntimeState

QUIZ = {
    "version": 1,
    "question": "How many legs does a spider have?",
    "choices": [{"label": "Six", "correct": False}, {"label": "Eight", "correct": True}],
}


def _state(quiz=QUIZ):
    shapes = [
        {"kind": "text", "name": "Question", "text": QUIZ["question"]},
        {"kind": "button", "name": "Six", "text": "Six", "choice": 0},
        {"kind": "button", "name": "Eight", "text": "Eight", "choice": 1},
        {"kind": "text", "name": "Feedback right", "feedback": "right", "visible": False},
        {"kind": "text", "name": "Feedback wrong", "feedback": "wrong", "visible": False},
    ]
    pages = [Page(id="P1", quiz=dict(quiz), shapes=shapes), Page(id="P2"), Page(id="P3")]
    return RuntimeState(book=Book(path="q.fbk", pages=pages)), shapes


class ChoiceGradeTests(unittest.TestCase):
    def test_the_right_choice(self):
        state, shapes = _state()
        self.assertIs(grade(state, shapes[2]), True)
        self.assertEqual(state.variables["__answer"], {"page": "P1", "choice": 1, "right": True})

    def test_a_wrong_choice(self):
        state, shapes = _state()
        self.assertIs(grade(state, shapes[1]), False)
        self.assertEqual(state.variables["__answer"], {"page": "P1", "choice": 0, "right": False})

    def test_the_name_does_not_matter(self):
        state, shapes = _state()
        shapes[2]["name"] = "Something"
        shapes[2]["text"] = "Something else"
        self.assertIs(grade(state, shapes[2]), True)

    def test_a_button_with_no_choice_is_not_graded(self):
        state, shapes = _state()
        self.assertIsNone(grade(state, {"kind": "button", "name": "Eight"}))
        self.assertIsNone(grade(state, {"kind": "button", "choice": 7}))
        self.assertNotIn("__answer", state.variables)

    def test_a_click_grades(self):
        state, shapes = _state()
        self.assertFalse(click(state, shapes[2]))
        self.assertTrue(state.variables["__answer"]["right"])

    def test_a_toolbook_file_is_not_graded(self):
        from toolbook.format import _AT, _BOOK
        state, shapes = _state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "q.fbk"
            path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
            state.book.path = str(path)
            self.assertIsNone(grade(state, shapes[2]))
        self.assertNotIn("__answer", state.variables)


class NidaToolBookClickTests(unittest.TestCase):
    """A ToolBook click takes the old path, even on a button carrying `choice`.

    Runs when FOOLBOOK_COURSES names a folder holding 93951303.tbk.
    """

    def test_a_letter_click_on_93951303_is_not_graded_by_choice(self):
        import copy
        import os
        from engine.loader import load
        from foolbook.model import RuntimeState
        folder = Path(os.environ.get("FOOLBOOK_COURSES") or "/nonexistent")
        found = [p for p in folder.glob("*") if p.name.lower() == "93951303.tbk"] if folder.is_dir() else []
        if not found:
            raise unittest.SkipTest("93951303.tbk is not here; set FOOLBOOK_COURSES")
        book = load(found[0])
        index = next(i for i, p in enumerate(book.pages)
                     if (p.raw or {}).get("props", {}).get("QuestionNo")
                     and any((s.get("name") or "").upper() == "A" for s in p.shapes or []))

        def run(extra):
            state = RuntimeState(book=copy.deepcopy(book))
            state.index = index
            # Give the page a Foolbook quiz too, so only the ToolBook check stops a grade.
            state.page.quiz = dict(state.page.quiz or {}, choices=[{"label": "A", "correct": True}])
            letter = next(s for s in state.page.shapes if (s.get("name") or "").upper() == "A")
            click(state, dict(letter, **extra))
            return state

        plain, with_choice = run({}), run({"choice": 0})
        self.assertNotIn("__answer", with_choice.variables)
        self.assertEqual(with_choice.index, plain.index)
        self.assertEqual(repr(sorted(with_choice.variables.items())), repr(sorted(plain.variables.items())))


if __name__ == "__main__":
    unittest.main()
