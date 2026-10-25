"""A wrong hotspot counts a try, so the right one afterwards scores 100 over the tries."""

from __future__ import annotations

import unittest

from engine import fillin
from engine.engine import follow, run_handler
from foolbook.model import Book, Page, RuntimeState

WRONG = """To Handle ButtonClick
	get IncorrectEmbedded
	system string lastpage
	lastpage = name of this page
	go to page "p1092"
end
"""
RIGHT = """TO HANDLE buttonClick
  get saveEmbedded(testno of this page,  questionno of this page, "area2")
  go to page "p1091"
end buttonClick
"""


def _state():
    pages = [Page(id=i, raw={"props": {"TestNo": "3", "QuestionNo": "301"}}) for i in ("P1090", "P1091", "P1092")]
    state = RuntimeState(book=Book(path="x.tbk", pages=pages), index=0)
    state.variables["__studentRecords"] = 1
    return state


def _click(state, script):
    follow(state, run_handler(state, script))


class Tries(unittest.TestCase):
    def test_a_wrong_hotspot_counts_one_try_and_goes_to_try_again(self):
        state = _state()
        _click(state, WRONG)
        self.assertEqual(fillin.tries(state), 1)
        self.assertEqual(state.page.id, "P1092")

    def test_right_after_one_wrong_scores_50(self):
        state = _state()
        _click(state, WRONG)
        state.index = 0
        _click(state, RIGHT)
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [50])
        self.assertEqual(fillin.tries(state), 0)

    def test_right_after_two_wrong_scores_33(self):
        state = _state()
        for _ in range(2):
            state.index = 0
            _click(state, WRONG)
        state.index = 0
        _click(state, RIGHT)
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [33])

    def test_right_first_time_is_100(self):
        state = _state()
        _click(state, RIGHT)
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [100])


if __name__ == "__main__":
    unittest.main()
