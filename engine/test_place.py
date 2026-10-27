"""Objects sit where their twip bounds say, not packed to the corner."""

import unittest

from engine.place import clip_to_page, click_target, content_box, fit_view, in_front, opening_size, place_page, place_window


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

    def test_a_colour_run_does_not_grow_a_size(self):
        shapes = [{
            "kind": "text", "x": 0, "y": 0, "w": 100, "h": 40, "size": 12, "text": "TTL",
            "runs": [{"start": 0, "end": 3, "color": "#ffff00"}, {"start": 0, "end": 3, "font": "Arial", "size": 10, "bold": True}],
        }]
        placed = place_window(shapes, 1, 0, 0, 0, 0)
        runs = placed[0]["runs"]
        self.assertNotIn("size", runs[0])
        self.assertEqual(runs[1]["size"], 13)

    def test_a_field_past_the_page_is_cut_at_the_page(self):
        shapes = [{"kind": "text", "x": 17, "y": 300, "w": 626, "h": 120, "text": "Copyright"}]
        clipped = clip_to_page(shapes, 624, 442)
        self.assertEqual(clipped[0]["w"], 607)
        self.assertEqual(clipped[0]["h"], 120)

    def test_a_frame_does_not_cover_the_button_inside_it(self):
        frame = {"kind": "image", "name": "MenuFrame", "x": 20, "y": 10, "w": 400, "h": 300}
        button = {"kind": "image", "name": "selection1", "x": 100, "y": 70, "w": 200, "h": 30}
        ordered = in_front([button, frame])
        self.assertIs(ordered[-1], button)

    def test_a_chip_field_stays_under_the_pins_it_holds(self):
        field = {"kind": "text", "name": "correct", "x": 400, "y": 200, "w": 180, "h": 120, "fill": "#40ffff"}
        pin = {"kind": "polygon", "x": 430, "y": 280, "w": 10, "h": 16}
        body = {"kind": "rect", "x": 420, "y": 230, "w": 150, "h": 70}
        label = {"kind": "text", "x": 470, "y": 250, "w": 40, "h": 16, "text": "7408"}
        ordered = in_front([field, pin, body, label])
        self.assertLess(ordered.index(field), ordered.index(pin))
        self.assertLess(ordered.index(field), ordered.index(body))
        self.assertGreater(ordered.index(label), ordered.index(body))
        lone = {"kind": "text", "x": 0, "y": 0, "w": 40, "h": 16, "text": "Output"}
        dot = {"kind": "polygon", "x": 200, "y": 0, "w": 4, "h": 4}
        ordered = in_front([lone, dot])
        self.assertIs(ordered[-1], lone)

    def test_the_begin_label_clicks_the_button_under_it(self):
        label = {
            "kind": "text", "name": "selection1", "x": 110, "y": 80, "w": 180, "h": 20,
            "script": 'to handle buttonDown\nset invert of button "selection1" to true\nend\n',
        }
        button = {
            "kind": "image", "name": "selection1", "x": 100, "y": 70, "w": 200, "h": 40,
            "script": 'to handle buttonClick\nget setupQuizEx("Quiz", 2, "P10301", "P10302", "P10303")\nend\n',
        }
        self.assertIs(click_target([button, label], 150, 85), button)
        word = {"kind": "text", "name": "C", "x": 200, "y": 80, "w": 80, "h": 20, "text": "propagation."}
        letter = {"kind": "image", "name": "C", "x": 160, "y": 80, "w": 20, "h": 20}
        self.assertIs(click_target([letter, word], 220, 85), word)

    def test_a_blank_stub_page_keeps_its_words(self):
        from engine.place import blank_book_lines
        lines = blank_book_lines(
            ["INPUT DEVICE - Use your mouse to make selections."],
            "core/nida81.fsk",
        )
        self.assertIn("nida81.fbk", lines[0]["text"])
        self.assertIn("INPUT DEVICE", lines[1]["text"])
        self.assertEqual(blank_book_lines([], "nida81.tbk"), [])

    def test_the_window_opens_large_and_keeps_a_resize(self):
        wide, high = opening_size(1920, 1080)
        self.assertGreater(wide, 1200)
        self.assertGreater(high, 700)
        again = opening_size(1920, 1080, (1400, 900))
        self.assertEqual(again, (1400, 900))
        small = opening_size(800, 600)
        self.assertLess(small[0], 800)
        self.assertLess(small[1], 600)



if __name__ == "__main__":
    unittest.main()
