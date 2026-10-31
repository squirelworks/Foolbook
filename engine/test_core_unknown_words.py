"""FoolbookEditor asks foolbook.core, not the engine, which lines the reader does not run."""

from __future__ import annotations

import unittest


class CoreUnknownWordsTests(unittest.TestCase):
    def test_core_gives_the_engine_answer(self):
        from engine.subset import unknown_words
        from foolbook import core
        script = 'flash button "x"\ngo to page "P2"\npause 2 seconds'
        self.assertEqual(core.unknown_words(script), unknown_words(script))
        self.assertEqual(core.unknown_words(script), [(1, "flash"), (3, "pause")])


if __name__ == "__main__":
    unittest.main()
