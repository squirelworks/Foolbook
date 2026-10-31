"""`a is b` and `a is not b` compare like = and <>, whatever is on the right."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, _eval
from foolbook.model import Book, Page


class IsCompare(unittest.TestCase):
    def setUp(self):
        self.state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        self.state.variables.update(n="B", temp="b", kind="button", shown=True, blank="")

    def check(self, expr, want):
        self.assertIs(_eval(expr, self.state), want, expr)

    def test_variables_on_both_sides(self):
        self.check("n is temp", True)
        self.check("n is not temp", False)

    def test_a_bare_word_on_the_right(self):
        self.check("kind is button", True)
        self.check("kind is not button", False)
        self.check("kind is not page", True)

    def test_quoted_and_numbers_and_flags(self):
        self.check('n is not "b"', False)
        self.check('n is "c"', False)
        self.check("3 is 3", True)
        self.check("shown is true", True)
        self.check("shown is false", False)

    def test_null_is_blank(self):
        self.check("blank is null", True)
        self.check("n is not null", True)

    def test_an_object_on_the_right_is_matched_by_name(self):
        self.state.variables["target"] = "OK"
        self.check('target is button "OK" of parent of this page', True)
        self.check('target is not button "Next"', True)

    def test_is_inside_quotes_is_text(self):
        self.check('"this is it" = "this is it"', True)


if __name__ == "__main__":
    unittest.main()
