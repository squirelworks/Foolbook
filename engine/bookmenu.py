"""A book's own menu bar.

A Foolbook book may carry `menubar`: a list of menus, each a `label` and
`items`. An item is a `label` and either a `page` to go to or a `script`
to run, as a button's buttonClick runs. A menu with no label or no usable
item is left off the bar, as is an item with no label or nowhere to go.
"""

from __future__ import annotations


def menus(book) -> list[tuple[str, list[dict]]]:
    bar = []
    for menu in getattr(book, "menubar", None) or []:
        if not isinstance(menu, dict):
            continue
        label = str(menu.get("label") or "").strip()
        items = [
            item for item in menu.get("items") or []
            if isinstance(item, dict) and str(item.get("label") or "").strip()
            and (item.get("page") or item.get("script"))
        ]
        if label and items:
            bar.append((label, items))
    return bar


def choose(state, item: dict) -> list[dict]:
    """The actions a menu item asks for. The window follows them."""
    if item.get("page"):
        return [{"kind": "goto", "page": str(item["page"])}]
    from engine.engine import click_script, run_handler
    script = click_script({"script": item.get("script") or ""}) or str(item.get("script") or "")
    return run_handler(state, script) if script else []
