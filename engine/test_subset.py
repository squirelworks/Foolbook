"""unknown_words asks the interpreter which lines it runs, so the editor's warning cannot drift."""

from __future__ import annotations

import unittest

from engine.engine import run_handler
from engine.subset import MESSAGES, unknown_words
from foolbook.model import Book, Page, RuntimeState


class SubsetTests(unittest.TestCase):
    def test_a_known_script_has_no_warning(self):
        script = (
            'to handle buttonClick\n'
            '  -- a note\n'
            '  if n = 1 then\n'
            '    go to page "P2"\n'
            '  else\n'
            '    send next\n'
            '  end if\n'
            '  n = 1\n'
            '  rgbfill of field "x" = 0,0,0\n'
            'end buttonClick\n'
        )
        self.assertEqual(unknown_words(script), [])

    def test_a_line_the_interpreter_only_notes_is_named_with_its_line(self):
        script = 'to handle buttonClick\n  flash button "x"\n  go to page "P2"\nend\n'
        self.assertEqual(unknown_words(script), [(2, "flash")])

    def test_the_answer_is_the_interpreters(self):
        # beep runs; beep(1) is a form the interpreter does not read yet.
        self.assertEqual(unknown_words("beep\nbeep(1)"), [(2, "beep")])
        for line in ("beep", "beep(1)", "pause 2 seconds", 'show "x"'):
            noted = any(a["kind"] == "note" for a in run_handler(
                RuntimeState(book=Book(path="", pages=[Page(id="P1")])), line))
            self.assertEqual(bool(unknown_words(line)), noted, line)

    def test_block_lines_are_not_judged_alone(self):
        self.assertEqual(unknown_words("end\nend if\nelse\nwhen x = 1\nto handle enterPage"), [])

    def test_the_messages_move_the_reader(self):
        for message in MESSAGES:
            if message == "exit":
                continue
            state = RuntimeState(book=Book(path="x", pages=[Page(id="P1"), Page(id="P2")]))
            actions = run_handler(state, f"send {message}")
            self.assertEqual(actions[0], {"kind": "send", "name": message})


if __name__ == "__main__":
    unittest.main()
