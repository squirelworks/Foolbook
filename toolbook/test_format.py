"""A ToolBook file is recognized by its bytes. An .fbk names its Foolbook."""

import unittest

from engine.formats import pack, unpack
from toolbook.format import is_toolbook


class ToolbookDoor(unittest.TestCase):
    def test_an_fbk_envelope_is_not_a_toolbook(self):
        blob = pack({"title": "Filing taxes", "pages": []})
        self.assertFalse(is_toolbook(blob))
        self.assertTrue(is_toolbook(b"\x00" * 0x20 + b"\x03JBO"))

    def test_the_book_word_at_the_shell_offset_is_a_toolbook(self):
        blob = b"\x00" * 0xC00 + b"\x22\x22\x22\x22"
        self.assertTrue(is_toolbook(blob))

    def test_a_new_fbk_names_the_foolbook_it_was_written_for(self):
        from foolbook import __version__
        opened = unpack(pack({"title": "Filing taxes", "pages": [{"id": "P0", "text": ["Hi"]}]}))
        self.assertEqual(opened["fbk"], 1)
        self.assertEqual(opened["foolbook"], __version__)
        self.assertEqual(opened["pages"][0]["text"], ["Hi"])


if __name__ == "__main__":
    unittest.main()
