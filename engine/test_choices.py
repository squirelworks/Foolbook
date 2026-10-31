"""Checkbox and radio: the reader draws them and a click toggles them."""

from __future__ import annotations

import unittest

from engine import choices

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


class Toggle(unittest.TestCase):
    def test_a_click_flips_a_checkbox(self):
        box = _check()
        choices.toggle([box], box)
        self.assertIs(box["value"], True)
        choices.toggle([box], box)
        self.assertIs(box["value"], False)

    def test_a_radio_turns_off_the_others_in_its_group(self):
        small, large, other = _radio("Small", value=True), _radio("Large"), _radio("Red", group="colour", value=True)
        shapes = [small, large, other]
        choices.toggle(shapes, large)
        self.assertEqual([s.get("value") for s in shapes], [False, True, True])

    def test_a_second_click_on_a_radio_leaves_it_on(self):
        small = _radio("Small", value=True)
        choices.toggle([small], small)
        self.assertIs(small["value"], True)

    def test_only_checkboxes_and_radios_are_choices(self):
        self.assertTrue(choices.is_choice(_check()))
        self.assertTrue(choices.is_choice(_radio("A")))
        self.assertFalse(choices.is_choice({"kind": "button"}))
        self.assertFalse(choices.is_choice(None))


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


if __name__ == "__main__":
    unittest.main()
