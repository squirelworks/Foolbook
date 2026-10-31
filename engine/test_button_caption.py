"""A drawn button puts its caption where a named `align` says, and keeps the left edge otherwise."""

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


def _button(**extra):
    shape = {"kind": "button", "name": "Next", "text": "Next", "x": 100, "y": 40, "w": 90, "h": 28,
             "fill": "#c0c0c0", "outline": "#000000"}
    shape.update(extra)
    return shape


@unittest.skipIf(graphics is None, "tkinter is not installed")
class ButtonCaption(unittest.TestCase):
    def test_align_center_puts_the_caption_in_the_middle(self):
        canvas = _Canvas()
        graphics.draw(canvas, [_button(align="center")])
        [(args, kwargs)] = canvas.texts()
        self.assertEqual(args, (145, 54))
        self.assertEqual(kwargs["anchor"], "center")
        self.assertEqual(kwargs["justify"], "center")
        self.assertEqual(kwargs["text"], "Next")

    def test_align_right(self):
        canvas = _Canvas()
        graphics.draw(canvas, [_button(align="right")])
        [(args, kwargs)] = canvas.texts()
        self.assertEqual(args, (182, 54))
        self.assertEqual(kwargs["anchor"], "e")


@unittest.skipIf(graphics is None, "tkinter is not installed")
class TbkButtons(unittest.TestCase):
    # As main draws them: x + 8, anchor "w". A .tbk button's align is a number.
    def test_a_button_with_a_number_align_draws_as_before(self):
        for align in (0, 1, 2, 3):
            canvas = _Canvas()
            graphics.draw(canvas, [_button(align=align)])
            [(args, kwargs)] = canvas.texts()
            self.assertEqual((args, kwargs["anchor"]), ((108, 54), "w"), align)

    def test_a_button_without_align_draws_as_before(self):
        canvas = _Canvas()
        graphics.draw(canvas, [_button()])
        [(args, kwargs)] = canvas.texts()
        self.assertEqual((args, kwargs["anchor"]), ((108, 54), "w"))

    def test_align_left_draws_as_before(self):
        canvas = _Canvas()
        graphics.draw(canvas, [_button(align="left")])
        [(args, kwargs)] = canvas.texts()
        self.assertEqual((args, kwargs["anchor"]), ((108, 54), "w"))

if __name__ == "__main__":
    unittest.main()
