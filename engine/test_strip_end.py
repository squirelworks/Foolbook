"""The last choice of an end-of-test strip ends the test on the end page."""

from __future__ import annotations

import unittest

from engine import quiz
from foolbook.model import Book, Page, RuntimeState


def _strip(letters="AB", stem="You skipped X question(s).  Do you want to _________"):
    shapes = [{"name": n, "kind": "image"} for n in letters] + [{"name": "Stem", "kind": "text", "text": stem}]
    page = Page(id="P10301", shapes=shapes)
    state = RuntimeState(book=Book(path="x.tbk", pages=[page, Page(id="P10303")]), index=0)
    return state


class Strip(unittest.TestCase):
    def test_second_of_two_ends_the_test(self):
        state = _strip("AB")
        state.variables["__choice"] = "B"
        self.assertEqual(quiz.finish(state), ("goto", "P10303"))

    def test_third_of_three_ends_the_test(self):
        state = _strip("ABC")
        state.variables["__choice"] = "C"
        self.assertEqual(quiz.finish(state), ("goto", "P10303"))

    def test_the_page_given_to_setupQuizEx_is_the_end(self):
        state = _strip("AB")
        state.variables["__choice"] = "B"
        state.variables["__quizPages"] = {1: "P10301", 2: "P10302", 3: "P10399"}
        self.assertEqual(quiz.finish(state), ("goto", "P10399"))

    def test_nothing_marked_beeps_and_stays(self):
        state = _strip("AB")
        self.assertEqual(quiz.finish(state), 0)
        self.assertTrue(state.variables["__beep"])

    def test_the_results_page_is_not_a_strip(self):
        state = _strip("AB", stem="The test is complete and your score is XX%.  Do you want to _________")
        state.variables["__choice"] = "B"
        self.assertEqual(quiz.finish(state), ("goto", "P10410"))

    def test_ok_on_a_strip_never_walks_to_the_next_page(self):
        state = _strip("AB")
        self.assertEqual(quiz.call(state, "handleQuizClick", '"OK"'), 0)


if __name__ == "__main__":
    unittest.main()
