"""The click target is an object reference: `object of target`, `name of target`."""

from __future__ import annotations

import unittest

from engine import objects
from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _state():
    page = Page(id="P10210", shapes=[
        {"kind": "image", "name": "B", "layer": "page", "invert_data": "x", "enabled": True},
        {"kind": "text", "name": "B", "layer": "page", "text": "Check the results."},
        {"kind": "image", "name": "OK", "layer": "background", "invert_data": "x"},
    ])
    return RuntimeState(book=Book(path="", title="b", pages=[page])), page


SCRIPT = """
if object of target is not button and object of target is not page then
    kind = "other"
end if
if object of target is button then
    kind = "button"
    n = name of target
    temp = "b"
    if n is temp then
        if enabled of button temp is true then
            on = 1
        end if
    end if
end if
"""


class TargetObject(unittest.TestCase):
    def test_a_button_click(self):
        state, page = _state()
        state.variables["target"] = objects.reference(state, page.shapes[0])
        self.assertEqual(state.variables["target"], 'button "B" of page "P10210"')
        run_handler(state, SCRIPT)
        self.assertEqual((state.variables["kind"], state.variables["n"], state.variables.get("on")), ("button", "B", 1))

    def test_a_field_and_a_background_button_and_the_page(self):
        state, page = _state()
        state.variables["target"] = objects.reference(state, page.shapes[1])
        run_handler(state, SCRIPT)
        self.assertEqual(state.variables["kind"], "other")
        self.assertEqual(objects.reference(state, page.shapes[2]), 'button "OK" of parent of page "P10210"')
        state.variables["target"] = objects.reference(state, None)
        run_handler(state, 'k = object of target\nn = name of target\nyes = target is button "OK"')
        self.assertEqual((state.variables["k"], state.variables["n"], state.variables["yes"]), ("page", "P10210", False))


if __name__ == "__main__":
    unittest.main()
