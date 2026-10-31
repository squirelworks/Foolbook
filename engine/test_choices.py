"""Checkbox and radio: the reader draws the mark, the caption, and the state."""

from __future__ import annotations

import unittest

try:
    from engine import graphics
except ImportError:  # no Tk in this Python
    graphics = None


class _Canvas:
    """Records what draw() asks for. No window."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return len(self.calls)
        return record

    def texts(self):
        return [(args, kwargs) for name, args, kwargs in self.calls if name == "create_text"]


def _check(name="Agree", **extra):
    shape = {"kind": "check", "name": name, "text": name, "x": 10, "y": 10, "w": 120, "h": 20}
    shape.update(extra)
    return shape


def _radio(name, group="size", **extra):
    shape = {"kind": "radio", "name": name, "text": name, "group": group, "x": 10, "y": 40, "w": 120, "h": 20}
    shape.update(extra)
    return shape


@unittest.skipIf(graphics is None, "tkinter is not installed")
class Draw(unittest.TestCase):
    def _drawn(self, shape):
        canvas = _Canvas()
        graphics.draw(canvas, [shape])
        return [name for name, _args, _kwargs in canvas.calls], canvas

    def test_a_checkbox_is_a_box_and_its_caption(self):
        names, canvas = self._drawn(_check())
        self.assertIn("create_rectangle", names)
        self.assertEqual(canvas.texts()[0][1]["text"], "Agree")
        self.assertNotIn("create_line", names)

    def test_a_checked_box_has_a_mark(self):
        names, _canvas = self._drawn(_check(value=True))
        self.assertIn("create_line", names)

    def test_a_radio_is_a_circle_and_a_chosen_one_has_a_dot(self):
        names, _canvas = self._drawn(_radio("Small"))
        self.assertEqual(names.count("create_oval"), 1)
        names, _canvas = self._drawn(_radio("Small", value=True))
        self.assertEqual(names.count("create_oval"), 2)


@unittest.skipIf(graphics is None, "tkinter is not installed")
class NidaStrip(unittest.TestCase):
    """The NIDA A/B choice strip is ToolBook buttons with a `checked_data` face, not
    `check` or `radio` shapes. Synthetic .tbk-loader-shaped input; NIDA books are not here."""

    def test_a_strip_button_draws_no_tick_and_no_circle(self):
        canvas = _Canvas()
        graphics.draw(canvas, [{"kind": "button", "name": "A", "text": "A", "checked": True,
                                "x": 10, "y": 10, "w": 30, "h": 20}])
        names = [name for name, _args, _kwargs in canvas.calls]
        self.assertNotIn("create_line", names)
        self.assertNotIn("create_oval", names)


if __name__ == "__main__":
    unittest.main()
