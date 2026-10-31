"""OpenScript sums: + - * / div mod, left to right, with brackets."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _value(source: str, **variables):
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
    state.variables.update(variables)
    run_handler(state, f"result = {source}")
    return state.variables["result"]


class Arithmetic(unittest.TestCase):
    def test_a_sum_of_variables(self):
        self.assertEqual(_value("score + 25", score=50), 75)

    def test_minus_goes_left_to_right(self):
        self.assertEqual(_value("10 - 3 - 2"), 5)

    def test_times_before_plus(self):
        self.assertEqual(_value("2 + 3 * 4"), 14)

    def test_div_and_mod_are_whole_numbers(self):
        self.assertEqual(_value("score div count", score=250, count=3), 83)
        self.assertEqual(_value("7 mod 3"), 1)

    def test_brackets_come_first(self):
        self.assertEqual(_value("(2 + 3) * 4"), 20)

    def test_a_negative_number_is_not_a_minus(self):
        self.assertEqual(_value("5 * -2"), -10)

    def test_an_array_element_in_a_sum(self):
        state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
        run_handler(state, "system int flags[10]\nflags[2] = 2\nresult = flags[2] - 1")
        self.assertEqual(state.variables["result"], 1)

    def test_a_side_that_is_not_a_number_leaves_the_sum_unknown(self):
        state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
        run_handler(state, 'result = "abc" + 1')
        self.assertNotIn(state.variables.get("result"), ("abc1", 1))


if __name__ == "__main__":
    unittest.main()
