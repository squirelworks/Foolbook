"""addObjectiveToPoolEx takes its questions from a list."""

from __future__ import annotations

import unittest

from engine import quiz
from foolbook.model import Book, RuntimeState


class PoolList(unittest.TestCase):
    def test_list_and_range_pools_together(self):
        state = RuntimeState(book=Book(path="x.tbk", pages=[]), index=0)
        quiz.call(state, "setupQuizEx", '"Assessment", 2, "P10301", "P10302", "P10303"')
        quiz.call(state, "clearpool", "")
        quiz.call(state, "addObjectiveToPoolEX", '1, "110,111,112,113,114,115,116", 3')
        quiz.call(state, "addObjectiveToPool", "2, 120, 129, 7")
        self.assertEqual(quiz.call(state, "setuppool", ""), 0)
        numbers = state.variables["__quizNumbers"][1:]
        self.assertEqual(len(numbers), 10)
        self.assertEqual(sum(1 for n in numbers if 110 <= n <= 116), 3)
        self.assertEqual(sum(1 for n in numbers if 120 <= n <= 129), 7)

    def test_a_list_shorter_than_the_count_is_insufficient(self):
        state = RuntimeState(book=Book(path="x.tbk", pages=[]), index=0)
        quiz.call(state, "setupQuizEx", '"Quiz", 1, "a", "b", "c"')
        quiz.call(state, "addObjectiveToPoolEx", '1, "110,111", 3')
        self.assertEqual(quiz.call(state, "setuppool", ""), -1)


if __name__ == "__main__":
    unittest.main()
