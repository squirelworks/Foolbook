"""A click runs the object's buttonClick, or the group's, not the field's mouse script."""

from __future__ import annotations

import unittest

from engine.engine import click_script


class ClickScriptTests(unittest.TestCase):
    def test_the_field_does_not_use_its_mouse_script(self):
        field = {
            "script": 'to handle mouseenter\n  send mouseenter to button "selection1"\nend\n',
            "group_script": 'to handle buttonClick\n  go to page "P310"\nend\n',
        }
        self.assertIn("buttonclick", click_script(field).lower())
        self.assertNotIn("mouseenter", click_script(field).lower())

    def test_a_button_uses_its_own_click(self):
        button = {"script": "to handle buttonClick\n  send next\nend\n", "group_script": "nope"}
        self.assertIn("send next", click_script(button))


if __name__ == "__main__":
    unittest.main()
