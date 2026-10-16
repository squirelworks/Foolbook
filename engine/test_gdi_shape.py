"""GDI's arguments for the shapes that are not polygons."""

import unittest

from engine.gdi_shape import arc, bracket, ellipse, pie, polyline, rectangle, round_rect


class GdiShapeTests(unittest.TestCase):
    def test_rectangle_is_four_pixels(self):
        call = rectangle(0, 0, 15, 30, fill="#404040")
        self.assertEqual(call["gdi"], "Rectangle")
        self.assertEqual(call["box"], {"left": 0, "top": 0, "right": 1, "bottom": 2})
        self.assertEqual(call["fill"], "#404040")
        self.assertIsNone(call["pen"])

    def test_ellipse_uses_the_same_box(self):
        call = ellipse(0, 0, 15, 15)
        self.assertEqual(call["gdi"], "Ellipse")
        self.assertEqual(call["box"]["right"], 1)
        self.assertEqual(call["box"]["bottom"], 1)

    def test_round_rect_converts_the_corner(self):
        call = round_rect(0, 0, 150, 150, 15, 30)
        self.assertEqual(call["box"]["corner_w"], 1)
        self.assertEqual(call["box"]["corner_h"], 2)

    def test_polyline_does_not_close_or_fill(self):
        call = polyline([(0, 0), (15, 0), (15, 15)])
        self.assertEqual(call["gdi"], "Polyline")
        self.assertEqual(call["count"], 3)
        self.assertEqual(call["pixels"], [[0, 0], [1, 0], [1, 1]])
        self.assertIsNone(call["fill"])

    def test_arc_keeps_the_two_rays(self):
        call = arc(0, 0, 1440, 1440, (1440, 720), (720, 0))
        self.assertEqual(call["gdi"], "Arc")
        self.assertEqual(call["start"], [96, 48])
        self.assertEqual(call["end"], [48, 0])
        self.assertIsNone(call["fill"])

    def test_pie_is_not_a_toolbook_call(self):
        self.assertIsNone(pie()["gdi"])

    def test_a_bracket_does_not_invent_points(self):
        call = bracket(4801, 3015, 5370, 3570)
        self.assertIsNone(call["pixels"])
        self.assertIn("formula", call["reason"])


if __name__ == "__main__":
    unittest.main()
