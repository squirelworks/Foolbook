"""Objects sit where their twip bounds say, not packed to the corner."""

import unittest

from engine.place import content_box, fit_view, in_front, place_page, place_window


class PlaceTests(unittest.TestCase):
    def test_a_bound_at_one_inch_is_one_inch_across_the_window(self):
        page = place_page([
            {"type": "rect", "points": [[0, 0], [15, 15]], "fill": "#fff"},
            {"type": "rect", "points": [[1440, 0], [2880, 1440]], "fill": "#ccc"},
        ])
        first, second = page["shapes"]
        self.assertEqual(first["at"][0], 8)
        self.assertEqual(second["at"][0], 8 + 96)
        self.assertGreater(page["width"], second["at"][0] + second["at"][2])

    def test_a_polygon_moves_with_its_bounds(self):
        page = place_page([
            {"type": "polygon", "points": [[1440, 1440], [2880, 1440], [2880, 2880]], "fill": "#c0c0c0"},
        ])
        shape = page["shapes"][0]
        self.assertEqual(shape["bounds"], [1440, 1440, 2880, 2880])
        self.assertEqual(shape["pixels"][0], [8 + 96, 8 + 96])

    def test_a_negative_bound_is_shifted_onto_the_window(self):
        page = place_page([
            {"type": "rect", "points": [[-15, -15], [15, 15]], "fill": "#fff"},
        ])
        self.assertEqual(page["shapes"][0]["at"][0], 8)
        self.assertEqual(page["shapes"][0]["at"][1], 8)


class FitTests(unittest.TestCase):
    def test_a_wide_drawing_uses_the_width_and_stays_inside(self):
        scale, dx, dy, ox, oy = fit_view((0, 0, 1000, 200), 500, 400)
        self.assertAlmostEqual(scale, 476 / 1000)
        self.assertAlmostEqual(ox, 12)
        self.assertGreater(oy, 12)
        self.assertAlmostEqual(dx, ox)
        self.assertAlmostEqual(dy, oy)

    def test_a_corner_drawing_is_moved_onto_the_window(self):
        scale, dx, dy, ox, oy = fit_view((800, 600, 900, 700), 400, 300)
        self.assertAlmostEqual(scale, 276 / 100)
        self.assertAlmostEqual(ox, (400 - 100 * scale) / 2)
        self.assertAlmostEqual(dx, ox - 800)
        self.assertAlmostEqual(dy, oy - 600)


class WindowTests(unittest.TestCase):
    def test_the_same_scale_and_offset_move_a_picture_and_a_label(self):
        shapes = [
            {"kind": "image", "x": 10, "y": 20, "w": 100, "h": 40},
            {"kind": "text", "x": 10, "y": 20, "w": 100, "h": 40, "text": "Hello"},
        ]
        placed = place_window(shapes, 2, 0, 0, 5, 6)
        self.assertEqual(placed[0]["x"], 25)
        self.assertEqual(placed[0]["y"], 46)
        self.assertEqual(placed[0]["w"], 200)
        self.assertEqual(placed[1]["w"], 200)
        self.assertEqual(content_box(shapes), (10, 20, 110, 60))

    def test_the_face_and_the_indent_scale_with_the_box(self):
        shapes = [{"kind": "text", "x": 0, "y": 0, "w": 100, "h": 40, "size": 12, "marginL": 24, "text": "Hello"}]
        placed = place_window(shapes, 2, 0, 0, 0, 0)
        self.assertEqual(placed[0]["w"], 200)
        self.assertEqual(placed[0]["size"], 32)
        self.assertTrue(placed[0]["px"])
        self.assertEqual(placed[0]["marginL"], 48)

    def test_a_frame_does_not_cover_the_button_inside_it(self):
        frame = {"kind": "image", "name": "MenuFrame", "x": 20, "y": 10, "w": 400, "h": 300}
        button = {"kind": "image", "name": "selection1", "x": 100, "y": 70, "w": 200, "h": 30}
        ordered = in_front([button, frame])
        self.assertIs(ordered[-1], button)



if __name__ == "__main__":
    unittest.main()
