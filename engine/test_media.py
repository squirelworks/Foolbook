"""A media clip is drawn as a play box that shows its path."""

from __future__ import annotations

import unittest

try:
    from engine import graphics
except ImportError:  # no Tk in this Python
    graphics = None


def _clip(src="sounds/bell.wav", **extra):
    shape = {"kind": "media", "name": "Bell", "src": src, "x": 10, "y": 10, "w": 160, "h": 40}
    shape.update(extra)
    return shape


class _Canvas:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return len(self.calls)
        return record


@unittest.skipIf(graphics is None, "tkinter is not installed")
class Draw(unittest.TestCase):
    def _drawn(self, shape):
        canvas = _Canvas()
        graphics.draw(canvas, [shape])
        return canvas.calls

    def test_the_clip_is_a_box_with_a_play_mark(self):
        names = [name for name, _a, _kw in self._drawn(_clip())]
        self.assertIn("create_rectangle", names)
        self.assertIn("create_polygon", names)

    def test_the_clip_shows_its_path(self):
        texts = [kw["text"] for name, _a, kw in self._drawn(_clip()) if name == "create_text"]
        self.assertEqual(texts, ["sounds/bell.wav"])

    def test_a_clip_with_no_path_says_so(self):
        texts = [kw["text"] for name, _a, kw in self._drawn(_clip("")) if name == "create_text"]
        self.assertEqual(texts, ["(no file)"])


class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `media` shape (0 mmPlay, mmOpen or .wav lines in
    the course scripts), so no NIDA page draws one. Synthetic loader-shaped input."""

    @unittest.skipIf(graphics is None, "tkinter is not installed")
    def test_a_tbk_button_draws_no_play_mark(self):
        canvas = _Canvas()
        graphics.draw(canvas, [{"kind": "button", "name": "Next", "text": "Next", "x": 10, "y": 10, "w": 80, "h": 24}])
        self.assertNotIn("create_polygon", [name for name, _a, _kw in canvas.calls])


if __name__ == "__main__":
    unittest.main()
