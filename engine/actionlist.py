"""Actions, so a book can move between pages without a script.

A shape may carry `actions`: a list of dicts, each a `do` and its
arguments, run in order when the shape is clicked and it has no script.
A script, when there is one, wins.

  {"do": "goto", "page": "P2"}
  {"do": "next"}                          {"do": "previous"}

An action the reader does not know is left alone.
"""

from __future__ import annotations

DOS = ("goto", "next", "previous")


def of(shape: dict | None) -> list[dict]:
    """The shape's actions the reader knows."""
    return [a for a in (shape or {}).get("actions") or [] if isinstance(a, dict) and a.get("do") in DOS]


def to_run(shape: dict | None) -> list[dict]:
    """The actions a click runs: none when the shape has a script, which wins."""
    from engine.engine import click_script
    return [] if click_script(shape) else of(shape)


def run(actions: list[dict]) -> list[dict]:
    """The page moves the actions ask for, for the window to follow."""
    moves: list[dict] = []
    for act in actions:
        do = act.get("do")
        if do == "goto" and act.get("page"):
            moves.append({"kind": "goto", "page": str(act["page"]), "book": None})
        elif do in ("next", "previous"):
            moves.append({"kind": "send", "name": do})
    return moves
