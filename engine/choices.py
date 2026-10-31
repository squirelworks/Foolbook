"""Checkboxes and radio buttons on a Foolbook page.

A `check` shape is on when its `value` is true. A click turns it over.
A `radio` shape has a `group`. A click turns it on and every other radio
of that group on the page off. A second click on a chosen radio leaves
it on, as a radio button does.
"""

from __future__ import annotations

KINDS = ("check", "radio")


def is_choice(shape: dict | None) -> bool:
    return bool(shape) and (shape.get("kind") or "") in KINDS


def toggle(shapes: list, shape: dict) -> None:
    """One click on a checkbox or a radio. Other shapes are left alone."""
    kind = shape.get("kind") or ""
    if kind == "check":
        shape["value"] = not bool(shape.get("value"))
        return
    if kind != "radio":
        return
    group = shape.get("group") or ""
    for other in shapes or []:
        if other is shape or not isinstance(other, dict):
            continue
        if (other.get("kind") or "") == "radio" and (other.get("group") or "") == group:
            other["value"] = False
    shape["value"] = True
