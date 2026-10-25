"""getObjectiveScore(n) is the average score of the questions whose objective is n (nc81test.sbk)."""

from __future__ import annotations

import unittest

from engine import quiz
from engine.engine import _eval
from foolbook.model import Book, RuntimeState


def _state():
    state = RuntimeState(book=Book(path="x.tbk", pages=[]), index=0)
    quiz.call(state, "setupQuizEx", '"Assessment", 2, "P10301", "P10302", "P10303"')
    quiz.call(state, "clearpool", "")
    quiz.call(state, "addObjectiveToPoolEX", '1, "110,111,112", 3')
    quiz.call(state, "addObjectiveToPool", "2, 120, 129, 4")
    quiz.call(state, "setuppool", "")
    return state


class ObjectiveScore(unittest.TestCase):
    def test_each_question_remembers_its_objective(self):
        self.assertEqual(_state().variables["__quizTestNo"][1:], [1, 1, 1, 2, 2, 2, 2])

    def test_the_score_is_the_average_over_that_objectives_questions(self):
        state = _state()
        state.variables["__quizScore"] = {1: 100, 2: 100, 3: 100, 4: 100, 5: 0, 6: 100, 7: 0}
        self.assertEqual(quiz.call(state, "getObjectiveScore", "1"), 100)
        self.assertEqual(quiz.call(state, "getObjectiveScore", "2"), 50)

    def test_the_average_is_cut_down_as_div_does(self):
        state = _state()
        state.variables["__quizScore"] = {1: 100, 2: 100, 3: 0}
        self.assertEqual(quiz.call(state, "getObjectiveScore", "1"), 66)

    def test_an_objective_with_no_questions_is_zero(self):
        self.assertEqual(quiz.call(_state(), "getObjectiveScore", "3"), 0)

    def test_the_argument_may_be_a_variable_in_an_expression(self):
        state = _state()
        state.variables["__quizScore"] = {n: 100 for n in range(1, 4)}
        state.variables["i"] = 1
        self.assertIs(_eval("getObjectiveScore(i) = 100", state), True)
        state.variables["i"] = 2
        self.assertIs(_eval("getObjectiveScore(i) = 100", state), False)


if __name__ == "__main__":
    unittest.main()
