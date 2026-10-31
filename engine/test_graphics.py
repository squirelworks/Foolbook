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

class NamedAlignment(unittest.TestCase):
    def fit(self, align, text="Next"):
        shape = {"kind": "text", "text": text, "size": 12, "align": align}
        graphics._FONTS.clear()
        return graphics._fit_text(shape, 0, 0, 400, 40)

    def test_center_is_the_middle_of_the_box(self):
        _text, _size, _wrap, anchor, tx, _ty = self.fit("center")
        self.assertEqual((anchor, tx), ("center", 200))

    def test_right_is_the_right_edge(self):
        _text, _size, _wrap, anchor, tx, _ty = self.fit("right")
        self.assertEqual((anchor, tx), ("e", 400))

    def test_left_is_the_left_edge(self):
        self.assertEqual(self.fit("left")[3:5], ("w", 0))

    def test_a_tbk_number_draws_as_before(self):
        # What main drew for the .tbk numbers before names were read.
        self.assertEqual(self.fit(0), ("Next", 12, 0, "w", 0, 20.0))
        self.assertEqual(self.fit(1), ("Next", 12, 0, "e", 400, 20.0))
        self.assertEqual(self.fit(2), ("Next", 12, 0, "center", 200.0, 20.0))
        from engine.test_draw_kinds import drawn
        canvas = drawn({"kind": "text", "x": 0, "y": 0, "w": 200, "h": 80, "text": "one\ntwo", "align": 2})
        texts = [call for call in canvas.calls if call[0] == "text"]
        self.assertEqual(texts, [("text", [0, 4], {
            "text": "one\ntwo", "anchor": "nw", "font": ("TkDefaultFont", 12), "fill": "black", "width": 200,
        })])

    def test_a_wrapped_centered_field_is_justified_centre(self):
        from engine.test_draw_kinds import drawn
        canvas = drawn({"kind": "text", "x": 0, "y": 0, "w": 200, "h": 80, "text": "one\ntwo", "align": "center"})
        texts = [call for call in canvas.calls if call[0] == "text"]
        self.assertEqual(texts[0][2].get("justify"), "center")


if __name__ == "__main__":
    unittest.main()
