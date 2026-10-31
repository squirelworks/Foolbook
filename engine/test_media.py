"""A media clip shows its path, and a clip the reader cannot play says so on the page."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine import media

try:
    from engine import graphics
except ImportError:  # no Tk in this Python
    graphics = None


def _clip(src="sounds/bell.wav", **extra):
    shape = {"kind": "media", "name": "Bell", "src": src, "x": 10, "y": 10, "w": 160, "h": 40}
    shape.update(extra)
    return shape


class Play(unittest.TestCase):
    def test_a_missing_file_is_named_on_the_clip(self):
        shape = _clip()
        with tempfile.TemporaryDirectory() as tmp:
            media.click(shape, tmp, players=[])
        self.assertEqual(shape["note"], "Not found: sounds/bell.wav")

    def test_a_file_no_player_takes_is_named_on_the_clip(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "sounds").mkdir()
            (Path(tmp) / "sounds" / "bell.wav").write_bytes(b"RIFF")
            shape = _clip()
            media.click(shape, tmp, players=[])
        self.assertEqual(shape["note"], "Cannot play here: sounds/bell.wav")

    def test_a_player_that_takes_the_file_clears_the_note(self):
        played = []
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "bell.wav").write_bytes(b"RIFF")
            shape = _clip("bell.wav", note="old")
            media.click(shape, tmp, players=[lambda path: played.append(path.name) or True])
        self.assertEqual(played, ["bell.wav"])
        self.assertEqual(shape["note"], "Playing bell.wav")

    def test_a_clip_with_no_path_says_so(self):
        shape = _clip("")
        media.click(shape, None, players=[])
        self.assertEqual(shape["note"], "No file named")


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
    def test_the_clip_shows_its_path_and_its_note(self):
        canvas = _Canvas()
        graphics.draw(canvas, [_clip(note="Cannot play here: sounds/bell.wav")])
        texts = [kw["text"] for name, _a, kw in canvas.calls if name == "create_text"]
        self.assertIn("sounds/bell.wav", texts[0])
        self.assertIn("Cannot play here: sounds/bell.wav", texts)


if __name__ == "__main__":
    unittest.main()
