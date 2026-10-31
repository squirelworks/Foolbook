"""A quiz in Foolbook's own format: grade a button by the choice it stores.

The page holds the quiz (``page.quiz``: ``choices``, each with ``label``
and ``correct``). Each answer button stores ``choice``, its index into
``choices``. A ToolBook quiz, graded by the clicked name against the
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

    The answer is kept in ``__answer``. A ToolBook file is never graded here.
    """
    page = state.page
    index = choice_of(obj)
    if page is None or index is None or is_toolbook(state.book):
        return None
    choices = (page.quiz or {}).get("choices") or []
    if not 0 <= index < len(choices):
        return None
    right = bool((choices[index] or {}).get("correct"))
    state.variables["__answer"] = {"page": page.id, "choice": index, "right": right}
    return right
