"""Actions, so a book can do things without a script.

A shape may carry `actions`: a list of dicts, each a `do` and its
arguments, run in order when the shape is clicked and it has no script.
A script, when there is one, wins.

  {"do": "goto", "page": "P2"}
  {"do": "next"}                          {"do": "previous"}
  {"do": "show", "shape": "Answer"}       {"do": "hide", "shape": "Answer"}
  {"do": "settext", "shape": "Note", "text": "Well done"}
  {"do": "play", "shape": "Clip"}

Show, hide, set text, and play act on the named shapes on this page.
An action the reader does not know is left alone.
"""

from __future__ import annotations

from pathlib import Path

DOS = ("goto", "next", "previous", "show", "hide", "settext", "play")


def of(shape: dict | None) -> list[dict]:
    """The shape's actions the reader knows."""
    return [a for a in (shape or {}).get("actions") or [] if isinstance(a, dict) and a.get("do") in DOS]


def to_run(shape: dict | None) -> list[dict]:
    """The actions a click runs: none when the shape has a script, which wins."""
    from engine.engine import click_script
    return [] if click_script(shape) else of(shape)


def _named(state, name) -> list[dict]:
    page = state.page
    wanted = str(name or "").strip().lower()
    if page is None or not wanted:
        return []
    return [s for s in page.shapes or [] if isinstance(s, dict) and (s.get("name") or "").strip().lower() == wanted]


def run(state, actions: list[dict], base: str | Path | None = None) -> list[dict]:
    """Do the actions. The page moves are returned for the window to follow."""
    moves: list[dict] = []
    for act in actions:
        do = act.get("do")
        if do == "goto" and act.get("page"):
            moves.append({"kind": "goto", "page": str(act["page"]), "book": None})
        elif do in ("next", "previous"):
            moves.append({"kind": "send", "name": do})
        elif do in ("show", "hide"):
            for shape in _named(state, act.get("shape")):
                shape["visible"] = do == "show"
            state.variables["__redraw"] = True
            moves.append({"kind": "setprop", "target": "visible of object", "value": do})
        elif do == "settext":
            for shape in _named(state, act.get("shape")):
                shape["text"] = str(act.get("text") or "")
                if "value" in shape:
                    shape["value"] = shape["text"]
            state.variables["__redraw"] = True
        elif do == "play":
            from engine import media
            for shape in _named(state, act.get("shape")):
                if shape.get("kind") == "media":
                    media.click(shape, base)
            state.variables["__redraw"] = True
    return moves
