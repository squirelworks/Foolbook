"""The part of nc81test the lesson actually calls.

Begin builds a pool and opens the first question. A question page does not
carry that script itself: its background calls handleQuizClick with the
object that was clicked. The Correct rectangle is not part of this. Reader
level leaves it hidden, which is why the page must not draw it.
"""

from __future__ import annotations

import random

_UNKNOWN = object()
_CHOICES = ("A", "B", "C", "D", "E")


def call(state, name: str, args: str):
    """Run one quiz call. Unknown names return a sentinel, not a guess."""
    key = name.lower()
    fn = _CALLS.get(key)
    if fn is None:
        return _UNKNOWN
    return fn(state, _args(args))


def known(name: str) -> bool:
    return name.lower() in _CALLS


def _args(text: str) -> list[str]:
    found = []
    cur = []
    quote = ""
    for ch in text:
        if quote:
            if ch == quote:
                quote = ""
            else:
                cur.append(ch)
            continue
        if ch in "\"'":
            quote = ch
            continue
        if ch == ",":
            found.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail or found:
        found.append(tail)
    return found


def _num(text: str, default: int = 0) -> int:
    try:
        return int(str(text).strip())
    except (TypeError, ValueError):
        return default


def _numbers(state) -> list:
    numbers = state.variables.get("__quizNumbers")
    if not isinstance(numbers, list) or not numbers:
        numbers = [None]
        state.variables["__quizNumbers"] = numbers
    return numbers


def _setup(state, args):
    # setupQuizEx("Quiz", objectives, passed, review, end)
    pages = {}
    if len(args) >= 5:
        pages = {1: args[2], 2: args[3], 3: args[4]}
    state.variables["__quizPages"] = pages
    state.variables["__quizPass"] = 1
    state.variables["__quizMode"] = 0
    state.variables["__quizIndex"] = 0
    state.variables["__quizCount"] = 0
    state.variables["__quizNumbers"] = [None]
    state.variables["__choice"] = ""
    state.variables["__pools"] = []
    return 0


def _clear(state, _args):
    state.variables["__pools"] = []
    state.variables["__quizNumbers"] = [None]
    state.variables["__quizCount"] = 0
    state.variables["__quizIndex"] = 0
    state.variables["__choice"] = ""
    return 0


def _add_pool(state, args):
    if len(args) < 4:
        return 0
    pools = state.variables.setdefault("__pools", [])
    pools.append((_num(args[1]), _num(args[2]), _num(args[3])))
    return 0


def _from_pool(state, words: list[str], count: int, keep: bool = False) -> int:
    if count > len(words):
        return 1 if keep else -1
    picked = random.sample(words, count)
    numbers = _numbers(state)
    for word in picked:
        numbers.append(_num(word))
    state.variables["__quizCount"] = len(numbers) - 1
    state.variables["__quizIndex"] = 0
    return 0


def _add_questions(state, args):
    """addQuestions(start, stop, count) as nc81test.sbk writes it (addToRandomSetX).

    `count` different question numbers from start to stop are added after the
    ones already chosen, and the count of the quiz grows by `count`. It is 1
    (nothing added) when count is more than the range holds.
    """
    if len(args) < 3:
        return 1
    start, stop, count = _num(args[0]), _num(args[1]), _num(args[2])
    if count > stop - start + 1:
        return 1
    words = [str(number) for number in range(start, stop + 1)]
    return _from_pool(state, words, count, keep=True)


def _setup_pool(state, _args):
    pools = list(state.variables.get("__pools") or [])
    state.variables["__quizNumbers"] = [None]
    state.variables["__quizCount"] = 0
    for start, stop, count in pools:
        words = [str(number) for number in range(start, stop + 1)]
        if _from_pool(state, words, count) < 0:
            return -1
    return 0


def _page_question(page) -> str:
    return str(((page.raw or {}).get("props") or {}).get("QuestionNo") or "")


def _find_page(state, number: int):
    for page in state.book.pages:
        if _page_question(page) == str(number):
            return page.id
    return ""


def _shape(page, name: str):
    for shape in page.shapes or []:
        if (shape.get("name") or "").lower() == name.lower():
            return shape
    return None


def _prepare(state, page_id: str, index: int) -> None:
    page = next((item for item in state.book.pages if item.id == page_id), None)
    if page is None:
        return
    state.variables["__choice"] = ""
    for shape in page.shapes or []:
        if (shape.get("name") or "").upper() in _CHOICES:
            shape["checked"] = False
        if (shape.get("name") or "").lower() == "correct":
            shape["visible"] = False
    label = _shape(page, "Index")
    if label is not None:
        label["text"] = f"Question {index}."


def _percent(state) -> int:
    scores = state.variables.get("__quizScore") or {}
    count = int(state.variables.get("__quizCount") or 0) or len(scores)
    total = sum(int(value) for value in scores.values())
    return round(total / count) if count else 0


def _stamp(page, percent: int) -> None:
    if page is None:
        return
    for shape in page.shapes or []:
        text = shape.get("text")
        if isinstance(text, str) and "XX" in text:
            shape["text"] = text.replace("XX", str(percent))


def finish(state):
    """P10303. The handler is okClicked in the lesson at file 0xb34aa.

    A starts the critique pass. B goes to the menu only when the score is
    100, and to P10410 otherwise. Neither choice beeps and stays.
    """
    percent = _percent(state)
    _stamp(state.page, percent)
    state.variables["__redraw"] = True
    # saveQuizResults marks the menu when the score reaches the pass mark.
    # The guest has no INI override, so the mark is 70.
    mark = state.variables.get("__quizObjectiveLevel", 70)
    try:
        mark = int(mark)
    except (TypeError, ValueError):
        mark = 70
    if percent >= mark:
        from engine.menu import set_flag
        set_flag(state, 10)
    choice = str(state.variables.get("__choice") or "").upper()
    if choice == "A":
        state.variables["__quizPass"] = 4
        state.variables["__quizIndex"] = 0
        return _next(state, [])
    if choice == "B":
        if percent == 100:
            return ("goto", "P900")
        return ("goto", "P10410")
    return 0


def _score(state) -> None:
    page = state.page
    if page is None:
        return
    answer = str(((page.raw or {}).get("props") or {}).get("Answer") or "")
    choice = str(state.variables.get("__choice") or "")
    scores = state.variables.setdefault("__quizScore", {})
    index = int(state.variables.get("__quizIndex") or 0)
    scores[index] = 100 if choice and choice.upper() == answer.upper() else 0


def _next(state, _args):
    index = int(state.variables.get("__quizIndex") or 0)
    if index > 0:
        _score(state)
    count = int(state.variables.get("__quizCount") or 0)
    pages = state.variables.get("__quizPages") or {}
    end = pages.get(3) or pages.get("3") or ""
    if index >= count:
        state.variables["__choice"] = ""
        if end:
            destination = next((item for item in state.book.pages if item.id == end), None)
            _stamp(destination, _percent(state))
        return ("goto", end) if end else 0
    index += 1
    state.variables["__quizIndex"] = index
    number = _numbers(state)[index]
    page_id = _find_page(state, number)
    if not page_id:
        return ("goto", end) if end else 0
    _prepare(state, page_id, index)
    return ("goto", page_id)


def _previous(state, _args):
    index = int(state.variables.get("__quizIndex") or 0)
    if index <= 1:
        return 0
    index -= 1
    state.variables["__quizIndex"] = index
    number = _numbers(state)[index]
    page_id = _find_page(state, number)
    if not page_id:
        return 0
    _prepare(state, page_id, index)
    return ("goto", page_id)


def _choose(state, letter: str) -> int:
    page = state.page
    letter = letter.upper()
    if page is None:
        return 0
    state.variables["__choice"] = letter
    for shape in page.shapes or []:
        name = (shape.get("name") or "").upper()
        if name in _CHOICES and shape.get("kind") != "text":
            shape["checked"] = name == letter
    state.variables["__redraw"] = True
    return 0


def _running(state) -> bool:
    return int(state.variables.get("__quizCount") or 0) > 0


def _neighbor(state, step: int):
    """The next page in the book, when the quiz itself was never started.

    Opening a question from the page list does not build the pool. OK,
    Next, Skip and Back still have to leave the page.
    """
    pages = state.book.pages if state.book is not None else []
    nxt = state.index + step
    if 0 <= nxt < len(pages):
        return ("goto", pages[nxt].id)
    return 0


def _click(state, args):
    target = args[0] if args else str(state.variables.get("target") or "")
    if target.lower() == "target":
        target = str(state.variables.get("target") or "")
    name = target.strip().strip('"').upper()
    if name in _CHOICES:
        return _choose(state, name)
    if name == "OK":
        if not _running(state):
            return _neighbor(state, 1)
        if int(state.variables.get("__quizPass") or 1) in (1, 2) and not state.variables.get("__choice"):
            # ToolBook beeps and stays. A silent return looks like a stall.
            state.variables["__beep"] = True
            return 0
        return _next(state, [])
    if name in ("SKIP", "NEXT"):
        if not _running(state):
            return _neighbor(state, 1)
        # Pass 1 and 2 at Quiz Mode 0 leave Skip disabled. The file still
        # stores the enabled face, and the setup script is what turns it off.
        if (
            name == "SKIP"
            and int(state.variables.get("__quizMode") or 0) == 0
            and int(state.variables.get("__quizPass") or 1) in (1, 2)
        ):
            return 0
        if name == "SKIP":
            state.variables["__choice"] = ""
        return _next(state, [])
    if name == "BACK":
        if not _running(state):
            return _neighbor(state, -1)
        return _previous(state, [])
    if name == "HELP":
        page = state.page
        help_page = str(((page.raw or {}).get("props") or {}).get("HelpPage") or "") if page else ""
        if help_page and any(item.id.lower() == help_page.lower() for item in state.book.pages):
            return ("goto", help_page)
        return 0
    return 0


_CALLS = {
    "setupquizex": _setup,
    "clearpool": _clear,
    "addobjectivetopool": _add_pool,
    "setuppool": _setup_pool,
    "addquestions": _add_questions,
    "gotonextquestionex": _next,
    "gotopreviousquestionex": _previous,
    "handlequizclick": _click,
}
