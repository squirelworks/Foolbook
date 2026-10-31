"""The part of nc81test the lesson actually calls.

Begin builds a pool and opens the first question. A question page does not
carry that script itself: its background calls handleQuizClick with the
object that was clicked. The Correct rectangle is not part of this. Reader
level leaves it hidden, which is why the page must not draw it.
"""

from __future__ import annotations

import random
import re

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
    state.variables["__quizTestNo"] = [None]
    state.variables["__choice"] = ""
    state.variables["__pools"] = []
    state.variables["__poolObjectives"] = []
    return 0


def _clear(state, _args):
    state.variables["__pools"] = []
    state.variables["__poolObjectives"] = []
    state.variables["__quizNumbers"] = [None]
    state.variables["__quizTestNo"] = [None]
    state.variables["__quizCount"] = 0
    state.variables["__quizIndex"] = 0
    state.variables["__choice"] = ""
    return 0


def _add_pool(state, args):
    if len(args) < 4:
        return 0
    pools = state.variables.setdefault("__pools", [])
    pools.append((_num(args[1]), _num(args[2]), _num(args[3])))
    _objective(state, len(pools), _num(args[0]))
    return 0


def _objective(state, size: int, number: int) -> None:
    """Which objective the pool just added belongs to, kept beside the pool list."""
    objectives = state.variables.setdefault("__poolObjectives", [])
    objectives.extend([0] * (size - 1 - len(objectives)))
    objectives.append(number)


def _add_pool_ex(state, args):
    """addObjectiveToPoolEx(objective, "110,111,115", count): the questions are a list, not a range."""
    if len(args) < 3:
        return 0
    words = [word.strip() for word in args[1].split(",") if word.strip()]
    pools = state.variables.setdefault("__pools", [])
    pools.append((words, _num(args[2])))
    _objective(state, len(pools), _num(args[0]))
    return 0


def _test_nos(state) -> list:
    """__quizTestNo: the objective of each question, in step with __quizNumbers."""
    found = state.variables.get("__quizTestNo")
    if not isinstance(found, list) or not found:
        found = [None]
        state.variables["__quizTestNo"] = found
    return found


def _from_pool(state, words: list[str], count: int, keep: bool = False, objective: int = 0) -> int:
    if count > len(words):
        return 1 if keep else -1
    picked = random.sample(words, count)
    numbers = _numbers(state)
    test_nos = _test_nos(state)
    test_nos.extend([None] * (len(numbers) - len(test_nos)))
    for word in picked:
        numbers.append(_num(word))
        test_nos.append(objective)
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
    state.variables["__quizTestNo"] = [None]
    state.variables["__quizCount"] = 0
    objectives = list(state.variables.get("__poolObjectives") or [])
    for at, entry in enumerate(pools):
        objective = objectives[at] if at < len(objectives) else 0
        if len(entry) == 2:
            words, count = entry
        else:
            start, stop, count = entry
            words = [str(number) for number in range(start, stop + 1)]
        if _from_pool(state, words, count, objective=objective) < 0:
            return -1
    return 0


def _objective_score(state, args):
    """getObjectiveScore(n): the average of __quizScore over the questions whose TestNo is n.

    nc81test.sbk adds the scores of those questions and divides by how many
    there are (`score div count`), and is 0 when there are none.
    """
    from engine.engine import _eval
    number = _num(str(_eval(args[0], state))) if args else 0
    scores = state.variables.get("__quizScore") or {}
    test_nos = _test_nos(state)
    total = count = 0
    for index in range(1, int(state.variables.get("__quizCount") or 0) + 1):
        if index < len(test_nos) and test_nos[index] == number:
            count += 1
            total += int(scores.get(index) or 0)
    return total // count if count else 0


def _page_question(page) -> str:
    return str(((page.raw or {}).get("props") or {}).get("QuestionNo") or "")


def _page_test(page) -> str:
    return str(((page.raw or {}).get("props") or {}).get("TestNo") or "")


def _encoded(page_id: str):
    """P01150 is test 1, question 150. A lesson page such as P10218 is not."""
    match = re.fullmatch(r"[Pp](\d{2})(\d{3})", page_id or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _test_ok(page, test) -> bool:
    if test is None:
        return True
    try:
        wanted = int(test)
    except (TypeError, ValueError):
        return True
    prop = _page_test(page)
    if prop.lstrip("-").isdigit() and int(prop) > 0:
        return int(prop) == wanted
    encoded = _encoded(page.id)
    if encoded:
        return encoded[0] == wanted
    return True


def _find_page(state, number, test=None):
    try:
        number = int(number)
    except (TypeError, ValueError):
        return ""
    by_id = ""
    for page in state.book.pages:
        if not _test_ok(page, test):
            continue
        if _page_question(page) == str(number):
            return page.id
        encoded = _encoded(page.id)
        # The exported property is the bank the question was copied from.
        # The id is the number addQuesterQuestions actually asks for.
        if encoded and encoded[1] == number and number >= 100 and not by_id:
            prop = _page_question(page)
            if not (prop.lstrip("-").isdigit() and int(prop) == number):
                by_id = page.id
    return by_id


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
    # setupQuizPage: PageText says Testing, or the page name when
    # NIDAREC.INI asks to show page numbers (Show Page Numbers, default 0).
    shown = _shape(page, "PageText")
    if shown is not None:
        shown["text"] = page.id if int(state.variables.get("__quizShowPageNumbers") or 0) else "Testing"


def _percent(state) -> int:
    """The average of every question, as getQuizScore divides.

    A question that was never answered counts as 0. An empty quiz is 0,
    not 100. 100 is every question answered and right.
    """
    scores = state.variables.get("__quizScore") or {}
    if not isinstance(scores, dict):
        scores = {}
    count = int(state.variables.get("__quizCount") or 0)
    if count <= 0:
        return 0
    total = 0
    for index in range(1, count + 1):
        total += int(scores.get(index) or 0)
    return total // count


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
    ended = _strip_end(state)
    if ended is not None:
        return ended
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


def _is_strip(state) -> bool:
    """P10301 and P10302, the "You skipped X question(s)" pages, not the results page."""
    page = state.page
    if page is None:
        return False
    pages = state.variables.get("__quizPages") or {}
    if page.id.lower() in (str(pages.get(1) or "").lower(), str(pages.get(2) or "").lower()) and pages.get(1):
        return True
    stem = _shape(page, "Stem")
    return stem is not None and "skipped" in str(stem.get("text") or "").lower()


def _strip_end(state):
    """okClicked of the end-of-test strips, the choice that ends the test.

    P10301 has two choices and P10302 has three. The last one is
    `go to page "P10303"`. The others start a pass and are not read here.
    Returns None when this is not a strip or the choice is not the last one.
    """
    if not _is_strip(state):
        return None
    page = state.page
    letters = [n for n in _CHOICES if any((s.get("name") or "").upper() == n and s.get("kind") != "text" for s in page.shapes or [])]
    choice = str(state.variables.get("__choice") or "").upper()
    if not choice:
        state.variables["__beep"] = True
        return 0
    if letters and choice == letters[-1]:
        pages = state.variables.get("__quizPages") or {}
        end = pages.get(3) or "P10303"
        return ("goto", end)
    return None


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
    # Nothing was built. That is not a finished test.
    if count <= 0:
        return 0
    pages = state.variables.get("__quizPages") or {}
    end = pages.get(3) or pages.get("3") or ""
    test = None
    if int(state.variables.get("__quizCheckTestAndQuestion") or 0) == 1:
        test = state.variables.get("__quizCheckTestNo")
    numbers = _numbers(state)
    while index < count:
        index += 1
        state.variables["__quizIndex"] = index
        number = numbers[index] if index < len(numbers) else None
        page_id = _find_page(state, number, test)
        if page_id:
            _prepare(state, page_id, index)
            return ("goto", page_id)
    # Every number was missing. Do not tell the learner the test is over.
    if not any(_find_page(state, numbers[i], test) for i in range(1, min(count + 1, len(numbers)))):
        state.variables["__quizIndex"] = 0
        return 0
    state.variables["__choice"] = ""
    if end:
        destination = next((item for item in state.book.pages if item.id == end), None)
        _stamp(destination, _percent(state))
        return ("goto", end)
    return 0


def _previous(state, _args):
    index = int(state.variables.get("__quizIndex") or 0)
    if index <= 1:
        return 0
    test = None
    if int(state.variables.get("__quizCheckTestAndQuestion") or 0) == 1:
        test = state.variables.get("__quizCheckTestNo")
    numbers = _numbers(state)
    while index > 1:
        index -= 1
        state.variables["__quizIndex"] = index
        number = numbers[index] if index < len(numbers) else None
        page_id = _find_page(state, number, test)
        if page_id:
            _prepare(state, page_id, index)
            return ("goto", page_id)
    return 0


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


def key_letter(state, char: str) -> bool:
    """handleQuizKey, the letters. True when the key marked an answer.

    The book's keyChar hands every key but F3 to handleQuizKey. In passes 1 to 3
    a or A to e or E calls manageQuizButtons on that letter when the page has
    the button: it is checked and the other letters are cleared.
    """
    if int(state.variables.get("__quizPass") or 1) > 3 or len(char or "") != 1:
        return False
    letter = char.upper()
    page = state.page
    if letter not in _CHOICES or page is None:
        return False
    if not any((s.get("name") or "").upper() == letter and s.get("kind") != "text" for s in page.shapes or []):
        return False
    _choose(state, letter)
    return True


def ok_button(state):
    """The OK button of the page, the one Return presses (handleQuizKey, key = keyEnter)."""
    page = state.page
    for shape in (page.shapes if page is not None else None) or []:
        if (shape.get("name") or "").upper() == "OK" and shape.get("kind") != "text" and shape.get("visible") is not False:
            return shape
    return None


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
    from engine.engine import _object_name
    target = args[0] if args else str(state.variables.get("target") or "")
    if target.lower() == "target":
        target = str(state.variables.get("target") or "")
    target = _object_name(target)
    name = target.strip().strip('"').upper()
    if name in _CHOICES:
        return _choose(state, name)
    if name == "OK":
        if _is_strip(state):
            # okClicked of the page's own script decides, and it stays when it has nothing to do.
            return 0
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


# nc81trnr.sbk getTrainerType: __trainerType 3 is "130E". initializeTrnr reads
# [Trainer] Type from NIDAREC.INI and uses 3 when there is no such file.
_TRAINER_TYPES = {-1: "THEORY", 0: "TD2000", 1: "130C", 2: "130A", 3: "130E"}


def _trainer_type(state, args):
    raw = state.variables.get("__trainerType", 3)
    try:
        return _TRAINER_TYPES.get(int(raw), "THEORY")
    except (TypeError, ValueError):
        return "THEORY"


def _trainer_code(state, args):
    # getTrainerCode looks the code up in NIDA2.INI and returns "" when the
    # file has none, which is the case with no INI file.
    return ""


def _book_props(state) -> dict:
    raw = getattr(state.book, "props", None) or {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def _book_prop(props: dict, name: str, default=None):
    want = name.lower()
    for key, value in props.items():
        if str(key).lower() == want:
            return value
    return default


def _override(state, props, source: str, dest: str) -> None:
    """Copy a quester setting when the book stored one. -1 means leave it."""
    value = _book_prop(props, source, None)
    if value is None:
        return
    try:
        number = int(value)
    except (TypeError, ValueError):
        return
    if number != -1:
        state.variables[dest] = number


def _quester_numbers(state, testno: int, start: int, count: int) -> list[int]:
    if count > 0:
        return list(range(start, start + count))
    found = []
    for page in state.book.pages:
        encoded = _encoded(page.id)
        if encoded and encoded[0] == testno and encoded[1] >= start:
            found.append(encoded[1])
    return sorted(set(found))


def _install_numbers(state, numbers: list[int], testno: int) -> None:
    state.variables["__quizNumbers"] = [None, *numbers]
    state.variables["__quizCount"] = len(numbers)
    state.variables["__quizIndex"] = 0
    if testno:
        state.variables["__quizTestNo"] = [None, *([testno] * len(numbers))]


def _add_quester(state, args):
    """addQuesterQuestions(testno), as nc81test.sbk writes it.

    Question numbers start at 150 (or 4001 when the style is 2). A test
    count of 1 walks every category. Anything else is the one test the
    button named, in order unless the book asked for a shuffled sequence.
    """
    testno = _num(args[0], 1) if args else 1
    if testno <= 0:
        testno = 1
    props = _book_props(state)
    start = 4001 if _num(_book_prop(props, "__questerStyle", 0)) == 2 else 150
    sequence = _num(_book_prop(props, "__questerSequence", 0))
    _setup(state, ["Quiz", "1", "P10301", "P10302", "P10303"])
    _override(state, props, "__questerTimed", "__quizTimed")
    _override(state, props, "__questerTimeType", "__quizTimeType")
    _override(state, props, "__questerTimeLimit", "__quizTimeLimit")
    _override(state, props, "__questerCritiqueMode", "__quizCritique")
    _override(state, props, "__questerObjectiveLevel", "__quizObjectiveLevel")
    mode = _book_prop(props, "__questerQuizMode", None)
    if mode is not None and _num(mode, -1) != -1:
        state.variables["__quizReview"] = _num(mode)
    whole = _book_prop(props, "__questerTestCount", None)
    if whole is not None and _num(whole) == 1:
        state.variables["__quizCheckTestAndQuestion"] = 0
        categories = _num(_book_prop(props, "__questerCategoryCount", 0))
        if categories <= 0:
            categories = 9
        numbers = []
        total = 0
        for index in range(1, categories + 1):
            count = _num(_book_prop(props, f"__questerQuestionCount({index})", 0))
            if count <= 0:
                continue
            numbers.extend(range(start + total, start + total + count))
            total += count
        test_for_rows = 0
    else:
        state.variables["__quizCheckTestAndQuestion"] = 1
        state.variables["__quizCheckTestNo"] = testno
        count = _num(_book_prop(props, f"__questerQuestionCount({testno})", 0))
        numbers = _quester_numbers(state, testno, start, count)
        test_for_rows = testno
    if sequence and numbers:
        numbers = random.sample(numbers, len(numbers))
    _install_numbers(state, numbers, test_for_rows)
    return 0


def _quiz_score(state, _args):
    return _percent(state)


def _skipped(state, _args):
    count = int(state.variables.get("__quizCount") or 0)
    scores = state.variables.get("__quizScore") or {}
    if not isinstance(scores, dict):
        scores = {}
    return sum(1 for index in range(1, count + 1) if index not in scores)


_CALLS = {
    "gettrainertype": _trainer_type,
    "gettrainercode": _trainer_code,
    "setupquizex": _setup,
    "clearpool": _clear,
    "addobjectivetopool": _add_pool,
    "addobjectivetopoolex": _add_pool_ex,
    "setuppool": _setup_pool,
    "addquestions": _add_questions,
    "addquesterquestions": _add_quester,
    "getquizscore": _quiz_score,
    "getskippedcount": _skipped,
    "gotonextquestionex": _next,
    "gotopreviousquestionex": _previous,
    "handlequizclick": _click,
    "getobjectivescore": _objective_score,
}
