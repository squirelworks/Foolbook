"""A click turns a checkbox over and moves a radio's dot within its group."""

from __future__ import annotations

import unittest

from engine import choices


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


class NidaStrip(unittest.TestCase):
    """The NIDA A/B choice strip is ToolBook buttons named A to E with a `checked_data`
    face; the book's own handleQuizClick checks them. The toggle leaves them to it.
    Synthetic .tbk-loader-shaped input; NIDA books are not here."""

    def _strip(self):
        return [{"kind": "button", "name": letter, "checked": letter == "A", "checked_data": "face"}
                for letter in "AB"]

    def test_a_strip_button_is_not_a_choice(self):
        for button in self._strip():
            self.assertFalse(choices.is_choice(button))

    def test_a_click_on_a_strip_button_changes_nothing(self):
        strip = self._strip()
        before = [dict(b) for b in strip]
        choices.toggle(strip, strip[1])
        self.assertEqual(strip, before)


if __name__ == "__main__":
    unittest.main()
