import unittest

from engine import graphics


class TypeSize(unittest.TestCase):
    def test_a_wide_desktop_face_is_divided_back_to_arial(self):
        graphics._FACTOR = 1.5
        graphics._FONTS.clear()
        face = graphics._typeface({"font": "Arial", "size": 19, "bold": True, "px": True}, 19)
        size = face[1] if isinstance(face, tuple) else int(face.cget("size"))
        self.assertEqual(size, -13)

    def tearDown(self):
        graphics._FACTOR = None
        graphics._FONTS.clear()


class Underline(unittest.TestCase):
    def setUp(self):
        graphics._FONTS.clear()

    def tearDown(self):
        graphics._FONTS.clear()

    def underlined(self, face) -> bool:
        if isinstance(face, tuple):
            return "underline" in str(face[2:])
        return bool(int(face.cget("underline")))

    def test_an_underlined_field_is_drawn_underlined(self):
        self.assertTrue(self.underlined(graphics._typeface({"font": "Arial", "size": 12, "underline": True}, 12)))

    def test_a_plain_field_is_not(self):
        self.assertFalse(self.underlined(graphics._typeface({"font": "Arial", "size": 12}, 12)))


if __name__ == "__main__":
    unittest.main()
