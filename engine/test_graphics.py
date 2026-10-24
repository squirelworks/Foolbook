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


if __name__ == "__main__":
    unittest.main()
