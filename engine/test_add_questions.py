"""addQuestions(start, stop, count) fills the quiz with `count` different questions of the range."""

from __future__ import annotations

import unittest

from engine import quiz
from foolbook.model import Book, RuntimeState


def _state():
    state = RuntimeState(book=Book(path="x.tbk", pages=[]), index=0)
    quiz.call(state, "setupQuizEx", '"Assessment", 2, "P10301", "P10302", "P10303"')
    return state


class AddQuestions(unittest.TestCase):
    def test_count_questions_from_the_range(self):
        state = _state()
        self.assertEqual(quiz.call(state, "addQuestions", "110, 119, 5"), 0)
        numbers = state.variables["__quizNumbers"][1:]
        self.assertEqual(len(numbers), 5)
        self.assertEqual(len(set(numbers)), 5)
        self.assertTrue(all(110 <= n <= 119 for n in numbers))
        self.assertEqual(state.variables["__quizCount"], 5)

    def test_second_call_adds_after_the_first(self):
        state = _state()
        quiz.call(state, "addQuestions", "110, 119, 4")
        quiz.call(state, "addQuestions", "120, 129, 3")
        numbers = state.variables["__quizNumbers"][1:]
        self.assertEqual(len(numbers), 7)
        self.assertEqual(sum(1 for n in numbers if n >= 120), 3)
        self.assertEqual(state.variables["__quizCount"], 7)

    def test_more_than_the_range_holds_adds_nothing(self):
        state = _state()
        self.assertEqual(quiz.call(state, "addQuestions", "110, 112, 4"), 1)
        self.assertEqual(state.variables["__quizCount"], 0)


if __name__ == "__main__":
    unittest.main()
