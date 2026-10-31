"""A quiz in Foolbook's own format: grade a button by the choice it stores.

The page holds the quiz (``page.quiz``: ``choices``, each with ``label``
and ``correct``). Each answer button stores ``choice``, its index into
``choices``. The feedback shapes store ``feedback``: ``"right"`` or
``"wrong"``, and start hidden. A ToolBook quiz, graded by the clicked name against the
page's Answer, is not this path and is left as it is.
"""

from __future__ import annotations

from engine.origin import is_toolbook
from foolbook.model import RuntimeState


def choice_of(obj: dict | None) -> int | None:
    value = (obj or {}).get("choice")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def grade(state: RuntimeState, obj: dict | None) -> bool | None:
    """True for the right choice, False for a wrong one, None when not a quiz answer.

    The answer is kept in ``__answer``, and the feedback shape for the
    result is shown and the other hidden. A ToolBook file is never graded here.
    """
    page = state.page
    index = choice_of(obj)
    if page is None or index is None or is_toolbook(state.book):
        return None
    choices = (page.quiz or {}).get("choices") or []
    if not 0 <= index < len(choices):
        return None
    right = bool((choices[index] or {}).get("correct"))
    want = "right" if right else "wrong"
    for shape in page.shapes or []:
        side = shape.get("feedback")
        if side in ("right", "wrong"):
            shape["visible"] = side == want
    state.variables["__redraw"] = True
    answer = {"page": page.id, "choice": index, "right": right}
    state.variables["__answer"] = answer
    record(state, answer)
    return right


def results(state: RuntimeState) -> list[dict]:
    """The book's list of page results, in memory. One entry per page, the last answer."""
    return state.book.props.setdefault("results", [])


def record(state: RuntimeState, answer: dict) -> None:
    rows = results(state)
    key = str(answer["page"]).lower()
    rows[:] = [row for row in rows if str(row.get("page")).lower() != key]
    rows.append(dict(answer))


def after(state: RuntimeState, right: bool) -> str:
    """The page the quiz names for this result (``next`` or ``again``), or ""."""
    quiz = (state.page.quiz if state.page else None) or {}
    return str(quiz.get("next" if right else "again") or "")
