"""A hotword click is the span, and a stored stroke of 0 stays none."""

from __future__ import annotations

import unittest

from engine.hotword import _measure, _wrap, hotword_under
from engine.loader import _store_shape
from engine.place import place_window


def _field(text, hotwords, width=400):
    return {
        "kind": "text",
        "name": "Text",
        "x": 10,
        "y": 20,
        "w": width,
        "h": 80,
        "text": text,
        "size": 12,
        "hotwords": hotwords,
    }


class HotwordTests(unittest.TestCase):
    def test_the_word_is_the_link_and_the_rest_is_not(self):
        text = "The tolerance is more exact."
        start = text.index("tolerance")
        shape = _field(text, [{"start": start, "end": start + len("tolerance"), "name": "tolerance", "script": "to handle buttonClick\nend"}])
        prefix = _measure(shape, 12, "The ")
        whole = _measure(shape, 12, "The tolerance")
        self.assertIsNotNone(hotword_under(shape, 10 + prefix + 1, 44))
        self.assertEqual(hotword_under(shape, 10 + prefix + 1, 44)["name"], "tolerance")
        self.assertIsNone(hotword_under(shape, 10 + 2, 44))
        self.assertIsNone(hotword_under(shape, 10 + whole + 8, 44))

    def test_a_click_outside_the_field_is_not_the_link(self):
        shape = _field("tolerance", [{"start": 0, "end": 9, "name": "tolerance", "script": "to handle buttonClick\nend"}])
        self.assertIsNone(hotword_under(shape, 1, 44))

    def test_a_span_with_no_script_does_not_take_the_click(self):
        shape = _field("tolerance", [{"start": 0, "end": 9, "name": "tolerance", "script": ""}])
        self.assertIsNone(hotword_under(shape, 14, 44))

    def test_the_wrap_keeps_a_word_whole(self):
        measure = lambda sample: len(sample) * 10
        self.assertEqual(_wrap("The tolerance is", 50, measure), ["The", "tolerance", "is"])


class StrokeTests(unittest.TestCase):
    def _obj(self, **extra):
        obj = {
            "kind": "line",
            "bounds": (0, 0, 15, 0),
            "name": "",
            "text": "",
            "fill": "",
            "outline": "#000000",
            "script": "",
            "align": 0,
        }
        obj.update(extra)
        return _store_shape(obj, lambda value: value)

    def test_a_stored_none_is_kept(self):
        self.assertEqual(self._obj(stroke=0)["stroke"], 0)

    def test_a_width_is_kept(self):
        self.assertEqual(self._obj(stroke=3)["stroke"], 3)

    def test_a_shape_with_no_stroke_is_unchanged(self):
        self.assertNotIn("stroke", self._obj())

    def test_hotwords_are_kept_on_the_field(self):
        shape = self._obj(kind="text", bounds=(0, 0, 100, 40), hotwords=[{"start": 1, "end": 4, "name": "pin", "script": "go"}])
        self.assertEqual(shape["hotwords"], [{"start": 1, "end": 4, "name": "pin", "script": "go"}])

    def test_none_stays_none_when_the_page_is_scaled(self):
        placed = place_window([{"kind": "line", "x": 0, "y": 0, "w": 10, "h": 1, "stroke": 0}], 2, 0, 0, 0, 0)
        self.assertEqual(placed[0]["stroke"], 0)


if __name__ == "__main__":
    unittest.main()
