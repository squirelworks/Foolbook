"""handleQuizKey: a letter key marks that answer, as manageQuizButtons does for a click."""

from __future__ import annotations

import unittest

from engine import quiz
from foolbook.model import Book, Page, RuntimeState


def _state(pass_no=1):
    shapes = [{"name": n, "kind": "image", "checked": False} for n in "ABCD"]
    shapes += [{"name": "A", "kind": "text", "text": "answer"}]
    page = Page(id="P10210", shapes=shapes, raw={"props": {"Answer": "B"}})
    state = RuntimeState(book=Book(path="x.tbk", pages=[page]), index=0)
    state.variables["__quizPass"] = pass_no
    return state, page


class Letters(unittest.TestCase):
    def test_lower_and_upper_case_mark_the_letter(self):
        state, page = _state()
        self.assertTrue(quiz.key_letter(state, "b"))
        self.assertEqual(state.variables["__choice"], "B")
        self.assertTrue(quiz.key_letter(state, "C"))
        self.assertEqual([s["checked"] for s in page.shapes[:4]], [False, False, True, False])

    def test_the_text_of_an_answer_is_not_the_button(self):
        state, page = _state()
        quiz.key_letter(state, "a")
        self.assertTrue(page.shapes[0]["checked"])
        self.assertNotIn("checked", {k for k in page.shapes[4] if page.shapes[4][k] is True})

    def test_a_letter_without_a_button_does_nothing(self):
        state, _ = _state()
        self.assertFalse(quiz.key_letter(state, "e"))
        self.assertFalse(quiz.key_letter(state, "z"))
        self.assertEqual(state.variables.get("__choice", ""), "")

    def test_the_review_pass_ignores_letters(self):
        state, _ = _state(pass_no=4)
        self.assertFalse(quiz.key_letter(state, "a"))


class Return(unittest.TestCase):
    def test_return_finds_the_ok_button(self):
        state, page = _state()
        self.assertIsNone(quiz.ok_button(state))
        page.shapes.append({"name": "OK", "kind": "image"})
        self.assertIs(quiz.ok_button(state), page.shapes[-1])

    def test_a_hidden_ok_or_a_text_called_ok_is_not_pressed(self):
        state, page = _state()
        page.shapes.append({"name": "OK", "kind": "text", "text": "OK"})
        page.shapes.append({"name": "ok", "kind": "image", "visible": False})
        self.assertIsNone(quiz.ok_button(state))


if __name__ == "__main__":
    unittest.main()
