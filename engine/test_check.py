"""The compile check: errors with line numbers, not a compile."""

from __future__ import annotations

import unittest

from engine.subset import check


class CheckTests(unittest.TestCase):
    def test_a_good_script_has_no_errors(self):
        script = (
            'to handle buttonClick\n'
            '  if n = 1 then\n'
            '    go to page "P2"\n'
            '  else\n'
            '    go to next page\n'
            '  end if\n'
            '  step i from 1 to 3\n'
            '    show "x"\n'
            '  end step\n'
            'end\n'
        )
        self.assertEqual(check(script), [])

    def test_a_bare_script_is_fine(self):
        self.assertEqual(check('go to page "P2"\nhide "hint"'), [])

    def test_an_open_quote(self):
        self.assertEqual(check('n = 1\ngo to page "P2'), [(2, "a quote is not closed")])

    def test_an_if_left_open(self):
        self.assertEqual(check("if n = 1 then\n  send next\n"), [(1, "if is not closed with end")])

    def test_an_end_with_nothing_open(self):
        self.assertEqual(check("send next\nend if"), [(2, "end with nothing open")])

    def test_go_to_with_no_page(self):
        self.assertEqual(check("go to"), [(1, "go to needs a page")])

    def test_if_with_no_condition(self):
        self.assertEqual(check("if then\nend if"), [(1, "if has no condition")])

    def test_mismatched_end(self):
        errors = check("step i from 1 to 2\nend if")
        self.assertIn((2, "end if closes step"), errors)

    def test_errors_are_in_line_order(self):
        errors = check('if then\n  go to\n')
        self.assertEqual([line for line, _ in errors], sorted(line for line, _ in errors))

    def test_core_gives_the_same_answer(self):
        from foolbook import core
        self.assertEqual(core.check_script("go to"), [(1, "go to needs a page")])


if __name__ == "__main__":
    unittest.main()
