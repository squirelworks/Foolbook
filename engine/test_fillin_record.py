"""Tries are counted, the score is 100 over the tries, and a record is kept only when the course keeps them."""

from __future__ import annotations

import unittest

from engine import fields, fillin
from engine.engine import follow, goto
from engine.test_fillin_answer import NUMERIC_KEYUP, _book


def _enter(state, field, typed):
    """Back on P2070, type an answer and press Return. The page the learner lands on."""
    goto(state, "P2070")
    field["text"] = ""
    fields.focus(state, field)
    for char in typed:
        fields.handle_key(state, "x", char)
    fields.handle_key(state, "Return", "\r")
    follow(state, fields.key_up(state, "Return", "\r"))
    return state.page.id


def _course(records=True):
    state, field = _book(NUMERIC_KEYUP)
    if records:
        state.variables["__studentRecords"] = 1
        state.variables["__studentIndex"] = 4
    return state, field


class Score(unittest.TestCase):
    def test_first_try_is_100(self):
        state, field = _course()
        self.assertEqual(_enter(state, field, "7"), "P2071")
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [100])

    def test_one_miss_is_50(self):
        state, field = _course()
        self.assertEqual(_enter(state, field, "3"), "P2072")
        self.assertEqual(_enter(state, field, "7"), "P2071")
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [50])

    def test_two_misses_is_33(self):
        state, field = _course()
        _enter(state, field, "3")
        _enter(state, field, "4")
        self.assertEqual(_enter(state, field, "7"), "P2071")
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [33])

    def test_the_count_starts_again_after_a_correct_answer(self):
        state, field = _course()
        _enter(state, field, "3")
        _enter(state, field, "7")
        self.assertEqual(fillin.tries(state), 0)
        _enter(state, field, "7")
        self.assertEqual([r["score"] for r in state.variables["__responses"]], [50, 100])


class Branch(unittest.TestCase):
    def test_the_third_wrong_answer_shows_the_reveal_page(self):
        state, field = _course()
        self.assertEqual(_enter(state, field, "3"), "P2072")
        self.assertEqual(fillin.tries(state), 1)
        self.assertEqual(_enter(state, field, "4"), "P2072")
        self.assertEqual(fillin.tries(state), 2)
        self.assertEqual(_enter(state, field, "5"), "P2073")
        self.assertEqual(fillin.tries(state), 0)

    def test_a_wrong_answer_records_nothing(self):
        state, field = _course()
        _enter(state, field, "3")
        _enter(state, field, "4")
        _enter(state, field, "5")
        self.assertNotIn("__responses", state.variables)

    def test_the_helper_pages_return_to_the_question(self):
        state, field = _course()
        _enter(state, field, "3")
        self.assertEqual(state.variables["lastpage"], "P2070")

    def test_a_fourth_question_starts_a_new_count(self):
        state, field = _course()
        for typed in ("3", "4", "5"):
            _enter(state, field, typed)
        self.assertEqual(_enter(state, field, "3"), "P2072")
        self.assertEqual(fillin.tries(state), 1)

    def test_the_count_is_kept_when_the_learner_leaves(self):
        state, field = _course()
        _enter(state, field, "3")
        goto(state, "P1700")
        self.assertEqual(fillin.tries(state), 1)
        self.assertEqual(_enter(state, field, "7"), "P2071")
        self.assertEqual(state.variables["__responses"][0]["score"], 50)


class Recording(unittest.TestCase):
    def test_nothing_is_kept_unless_the_course_keeps_records(self):
        state, field = _course(records=False)
        self.assertEqual(_enter(state, field, "7"), "P2071")
        self.assertNotIn("__responses", state.variables)
        state.variables["__studentRecords"] = 0
        _enter(state, field, "7")
        self.assertNotIn("__responses", state.variables)

    def test_the_record_has_what_the_dll_is_given(self):
        state, field = _course()
        _enter(state, field, "07")
        self.assertEqual(state.variables["__responses"], [{
            "student": 4, "type": 1, "test": 2, "question": 20, "part": 0, "response": "07", "score": 100,
        }])

    def test_the_record_type_follows_the_question_number(self):
        for question, kind in ((0, 1), (99, 1), (100, 2), (149, 2), (150, 3), (199, 3), (200, 4), (249, 4), (250, 3), (32001, 32)):
            self.assertEqual(fillin._type_number(question), kind, question)

    def test_write_response_and_part(self):
        state, _ = _course()
        fillin.call(state, "writeResponse", '2, 20, "7", 100')
        fillin.call(state, "writeResponseB", '2, 20, 3, "x", 50')
        parts = [(r["part"], r["response"], r["score"]) for r in state.variables["__responses"]]
        self.assertEqual(parts, [(0, "7", 100), (3, "x", 50)])


if __name__ == "__main__":
    unittest.main()
