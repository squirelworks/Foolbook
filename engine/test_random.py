"""random(n) gives a whole number from 1 to n."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


class RandomFunction(unittest.TestCase):
    def test_random_stays_between_one_and_n(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        seen = set()
        for _ in range(200):
            run_handler(state, "r = random(4 - 1 + 1) + 1 - 1")
            seen.add(state.variables["r"])
        self.assertEqual(seen, {1, 2, 3, 4})

    def test_random_indexes_a_list_that_counts_from_one(self):
        # A shuffle that swaps numbers[random(n)] over n items, as system books do.
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, "local int numbers[]\nstep i from 1 to 3\nnumbers[i] = i * 10\nend step\n"
                           "step i from 1 to 60\nj = random(3)\nk = random(3)\n"
                           "number = numbers[j]\nnumbers[j] = numbers[k]\nnumbers[k] = number\nend step")
        numbers = state.variables["numbers"]
        self.assertEqual(sorted(numbers[i] for i in (1, 2, 3)), [10, 20, 30])
        self.assertNotIn(0, numbers)

    def test_random_of_one_is_one(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, "r = random(1)")
        self.assertEqual(state.variables["r"], 1)


if __name__ == "__main__":
    unittest.main()
