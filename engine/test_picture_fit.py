"""A picture fits its frame: fill stretches, contain keeps the shape, none clips."""

from __future__ import annotations

import unittest

try:
    from PIL import Image
    from engine import graphics
except ImportError:  # no Tk or no Pillow in this Python
    graphics = None


def _wide():
    """A 40 by 20 red picture."""
    return Image.new("RGBA", (40, 20), (255, 0, 0, 255))


@unittest.skipIf(graphics is None, "tkinter or Pillow is not installed")
class Fit(unittest.TestCase):
    def test_fill_stretches_to_the_frame(self):
        out = graphics._fit_image(_wide(), 30, 30, "fill")
        self.assertEqual(out.size, (30, 30))
        self.assertEqual(out.getpixel((0, 0))[3], 255)

    def test_no_fit_is_fill_as_before(self):
        self.assertEqual(graphics._fit_image(_wide(), 30, 30, None).getpixel((0, 0))[3], 255)

    def test_contain_keeps_the_shape_and_centres_it(self):
        out = graphics._fit_image(_wide(), 30, 30, "contain")
        self.assertEqual(out.size, (30, 30))
        # 40 by 20 scaled into 30 by 30 is 30 by 15, with 7 or 8 clear rows above and below.
        self.assertEqual(out.getpixel((15, 2))[3], 0)
        self.assertEqual(out.getpixel((15, 15))[3], 255)
        self.assertEqual(out.getpixel((15, 27))[3], 0)

    def test_none_keeps_the_size_and_clips_at_the_frame(self):
        out = graphics._fit_image(_wide(), 30, 30, "none")
        self.assertEqual(out.size, (30, 30))
        self.assertEqual(out.getpixel((29, 19))[3], 255)
        self.assertEqual(out.getpixel((29, 20))[3], 0)


if __name__ == "__main__":
    unittest.main()
