"""Shapes an .fbk names by kind are drawn as that kind.

The canvas here records each call. No window is opened.
"""

import unittest

from engine import graphics
from engine.place import place_window


class Recorder:
    """Stands in for a Tk canvas and keeps what was drawn."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        if not name.startswith("create_"):
            raise AttributeError(name)

        def record(*args, **kwargs):
            self.calls.append((name[len("create_"):], list(args), kwargs))
            return len(self.calls)

        return record

    def find_all(self):
        return tuple(range(1, len(self.calls) + 1))

    def kinds(self):
        return [call[0] for call in self.calls]


def drawn(*shapes):
    canvas = Recorder()
    graphics.draw(canvas, list(shapes))
    return canvas


class RoundRect(unittest.TestCase):
    def test_a_rounded_rectangle_is_not_a_square_box(self):
        canvas = drawn({"kind": "roundrect", "x": 10, "y": 20, "w": 100, "h": 50, "fill": "#f7f4ee", "radius": 12})
        self.assertEqual(canvas.kinds(), ["polygon"])
        _kind, flat, options = canvas.calls[0]
        self.assertEqual(options["fill"], "#f7f4ee")
        points = list(zip(flat[0::2], flat[1::2]))
        for px, py in points:
            self.assertGreaterEqual(px, 10 - 0.01)
            self.assertLessEqual(px, 110 + 0.01)
            self.assertGreaterEqual(py, 20 - 0.01)
            self.assertLessEqual(py, 70 + 0.01)
        # The top-left corner is cut off by the radius.
        self.assertNotIn((10, 20), [(round(px), round(py)) for px, py in points])
        self.assertIn((10, 32), [(round(px), round(py)) for px, py in points])

    def test_the_radius_defaults_to_8(self):
        flat = drawn({"kind": "roundrect", "x": 0, "y": 0, "w": 100, "h": 50}).calls[0][1]
        self.assertIn((0, 8), [(round(px), round(py)) for px, py in zip(flat[0::2], flat[1::2])])

    def test_a_radius_past_half_the_short_side_is_clamped(self):
        flat = drawn({"kind": "roundrect", "x": 0, "y": 0, "w": 100, "h": 20, "radius": 50}).calls[0][1]
        ys = flat[1::2]
        self.assertEqual((round(min(ys)), round(max(ys))), (0, 20))

    def test_the_window_scale_scales_the_radius(self):
        placed = place_window([{"kind": "roundrect", "x": 0, "y": 0, "w": 100, "h": 50, "radius": 10}], 2, 0, 0, 0, 0)
        self.assertEqual(placed[0]["radius"], 20)


class Stroke(unittest.TestCase):
    def test_stroke_is_the_outline_width(self):
        for shape in (
            {"kind": "rect", "x": 0, "y": 0, "w": 40, "h": 20},
            {"kind": "roundrect", "x": 0, "y": 0, "w": 40, "h": 20},
            {"kind": "ellipse", "x": 0, "y": 0, "w": 40, "h": 20},
            {"kind": "line", "points": [[0, 0], [40, 20]]},
            {"kind": "polygon", "points": [[0, 0], [40, 0], [20, 20]]},
        ):
            shape["stroke"] = 3
            canvas = drawn(shape)
            self.assertEqual(canvas.calls[0][2].get("width"), 3, shape["kind"])

    def test_no_stroke_leaves_the_width_alone(self):
        canvas = drawn({"kind": "rect", "x": 0, "y": 0, "w": 40, "h": 20})
        self.assertNotIn("width", canvas.calls[0][2])

    def test_the_window_scale_scales_the_stroke(self):
        placed = place_window([{"kind": "rect", "x": 0, "y": 0, "w": 10, "h": 10, "stroke": 2}], 1.5, 0, 0, 0, 0)
        self.assertEqual(placed[0]["stroke"], 3)


class Curve(unittest.TestCase):
    def test_a_curve_goes_through_every_point(self):
        points = [[0, 0], [20, 30], [40, 0], [60, 30]]
        canvas = drawn({"kind": "curve", "points": points, "outline": "#071428"})
        self.assertEqual(canvas.kinds(), ["line"])
        self.assertEqual(canvas.calls[0][1], [0, 0, 20, 30, 40, 0, 60, 30])
        self.assertEqual(canvas.calls[0][2]["fill"], "#071428")

class Arc(unittest.TestCase):
    def test_an_arc_with_angles_is_not_the_whole_ellipse(self):
        canvas = drawn({"kind": "arc", "x": 0, "y": 0, "w": 80, "h": 60, "start": 30, "sweep": 120, "fill": "#ff0000"})
        self.assertEqual(canvas.kinds(), ["arc"])
        _kind, box, options = canvas.calls[0]
        self.assertEqual(box, [0, 0, 80, 60])
        self.assertEqual((options["start"], options["extent"], options["style"]), (30, 120, "arc"))
        self.assertNotIn("fill", options)

class Pie(unittest.TestCase):
    def test_a_pie_is_a_filled_slice(self):
        canvas = drawn({"kind": "pie", "x": 0, "y": 0, "w": 80, "h": 80, "start": 90, "sweep": -45, "fill": "#ff0000"})
        self.assertEqual(canvas.kinds(), ["arc"])
        options = canvas.calls[0][2]
        self.assertEqual((options["start"], options["extent"], options["style"]), (90, -45, "pieslice"))
        self.assertEqual(options["fill"], "#ff0000")

    def test_a_pie_with_no_angles_is_a_quarter(self):
        options = drawn({"kind": "pie", "x": 0, "y": 0, "w": 80, "h": 80}).calls[0][2]
        self.assertEqual((options["start"], options["extent"]), (0, 90))

class Chord(unittest.TestCase):
    def test_a_chord_is_closed_by_a_straight_line(self):
        canvas = drawn({"kind": "chord", "x": 0, "y": 0, "w": 80, "h": 80, "start": 0, "sweep": 180, "fill": "#00ff00"})
        self.assertEqual(canvas.kinds(), ["arc"])
        options = canvas.calls[0][2]
        self.assertEqual((options["start"], options["extent"], options["style"]), (0, 180, "chord"))
        self.assertEqual(options["fill"], "#00ff00")

class Hotspot(unittest.TestCase):
    spot = {"kind": "hotspot", "name": "Door", "x": 10, "y": 10, "w": 40, "h": 40, "outline": "#071428",
            "item": {"page": "P200"}}

    def test_a_hotspot_is_not_drawn(self):
        self.assertEqual(drawn(dict(self.spot)).calls, [])

    def test_a_click_inside_a_hotspot_is_the_hotspot(self):
        from engine.place import click_target
        under = {"kind": "rect", "x": 0, "y": 0, "w": 100, "h": 100, "fill": "#ffffff"}
        target = click_target([under, dict(self.spot)], 20, 20)
        self.assertEqual(target["name"], "Door")
        self.assertEqual(target["item"]["page"], "P200")


    def test_a_tbk_arc_with_ends_draws_as_before(self):
        # What main drew for this arc before start and sweep were read.
        canvas = drawn({"kind": "arc", "x": 0, "y": 0, "w": 80, "h": 60, "ends": [[80, 30], [40, 0]], "outline": "#071428"})
        self.assertEqual(canvas.calls, [("line", [
            80, 30, 80, 29, 80, 28, 80, 26, 80, 25, 79, 24, 79, 23, 78, 22, 78, 21, 78, 20,
            77, 19, 76, 17, 76, 16, 75, 15, 74, 14, 73, 13, 72, 12, 71, 11, 70, 11, 69, 10,
            68, 9, 67, 8, 66, 7, 65, 6, 64, 6, 62, 5, 61, 4, 60, 4, 58, 3, 57, 3,
            55, 2, 54, 2, 52, 1, 51, 1, 49, 1, 48, 1, 46, 0, 45, 0, 43, 0, 42, 0, 40, 0,
        ], {"fill": "#071428", "width": 2})])


if __name__ == "__main__":
    unittest.main()
