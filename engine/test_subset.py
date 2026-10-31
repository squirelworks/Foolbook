"""The table of words the reader runs, which the editor warns from."""

from __future__ import annotations

import unittest

from engine.engine import run_handler
from engine.subset import COMMANDS, MESSAGES, unknown_words
from foolbook.model import Book, Page, RuntimeState


class SubsetTests(unittest.TestCase):
    def test_a_known_script_has_no_warning(self):
        script = 'to handle buttonClick\n  -- a note\n  go to page "P2"\n  send next\n  n = 1\nend\n'
        self.assertEqual(unknown_words(script), [])

    def test_an_unknown_word_is_named_with_its_line(self):
        script = 'to handle buttonClick\n  flash button "x"\n  go to page "P2"\nend\n'
        self.assertEqual(unknown_words(script), [(2, "flash")])

    def test_send_is_judged_by_its_message(self):
        self.assertEqual(unknown_words("send next\nsend tumble"), [(2, "send tumble")])

    def test_the_messages_move_the_reader(self):
        for message in MESSAGES:
            if message == "exit":
                continue
            state = RuntimeState(book=Book(path="x", pages=[Page(id="P1"), Page(id="P2")]))
            actions = run_handler(state, f"send {message}")
            self.assertEqual(actions[0], {"kind": "send", "name": message})

    def test_foolbook_core_gives_the_editor_the_same_answer(self):
        from foolbook import core
        self.assertEqual(core.unknown_words("flash"), [(1, "flash")])

    def test_every_command_is_a_word(self):
        for word in COMMANDS:
            self.assertTrue(word.isalpha() and word.islower(), word)


if __name__ == "__main__":
    unittest.main()
