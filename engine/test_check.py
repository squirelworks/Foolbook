"""The compile check: errors with line numbers, not a compile.

The NIDA guard runs when NIDA_BOOKS names a folder holding the book.
The books are not in this repository.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

from engine.loader import load
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


class ToolBookFormTests(unittest.TestCase):
    def test_end_with_the_handler_name(self):
        self.assertEqual(check("to handle buttonClick\n  beep\nend buttonClick\n"), [])

    def test_else_in_conditions(self):
        script = 'conditions\n  when n = 1\n    beep\n  else\n    beep\nend conditions\n'
        self.assertEqual(check(script), [])

    def test_notify_after_is_a_handler(self):
        self.assertEqual(check("notifyAfter idle\n  beep\nend idle\n"), [])

    def test_go_to_previous_page_of_this_book(self):
        self.assertEqual(check("go to previous page of this book"), [])

    def test_go_to_an_expression(self):
        self.assertEqual(check("go to __pageStack[__pageIndex]"), [])

    def test_while_and_linkdll32_blocks(self):
        script = ('to get f\n  linkDLL32 "kernel32.dll"\n    WORD GlobalFree(WORD)\n  end linkDLL32\n'
                  '  while n < 3\n    increment(n)\n  end while\nend\n')
        self.assertEqual(check(script), [])

    def test_a_stored_body_ends_with_its_handler_name(self):
        self.assertEqual(check("get setSection(\"Intro\")\nforward\nend enterPage\n"), [])

    def test_a_quote_may_run_onto_the_next_line(self):
        self.assertEqual(check('text = "one line\nand the next"\n'), [])

    def test_the_end_of_the_script_closes_a_handler(self):
        self.assertEqual(check("to handle reader\n--  forward\n--end\n"), [])

    def test_an_if_left_open_in_a_handler_is_still_an_error(self):
        self.assertEqual(check("to handle x\n  if n = 1 then\n    beep\nend x\n"), [(2, "if is not closed with end"), (4, "end x closes if")])


class NidaCheckTests(unittest.TestCase):
    def test_93950101_every_script_checks_clean(self):
        path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / "93950101.fbk"
        if not path.exists():
            raise unittest.SkipTest("93950101.fbk is not here; set NIDA_BOOKS")
        book = load(path)
        handlers = [("book", h) for h in book.handlers] + [(p.id, h) for p in book.pages for h in p.handlers]
        for where, h in handlers:
            self.assertEqual(check(h.source or ""), [], (where, h.name))
        for page in book.pages:
            for shape in page.shapes:
                self.assertEqual(check(shape.get("script") or ""), [], (page.id, shape.get("name")))


if __name__ == "__main__":
    unittest.main()
