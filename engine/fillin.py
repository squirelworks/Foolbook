"""The part of nc81test that an answer field and its page call.

DoNumeric and DoAlphabetic are the key filters of the fill-in pages. The
field's own keyChar handler asks one of them, and forwards the key only when
the answer is true:

    to handle keyChar key
        if DoNumeric (key) then forward end if
    end

Both functions are in nc81test.sbk. They are read here as written:

    r = uppercase(ansiToChar(xkey))
    conditions
        when r is in "<the allowed characters, comma separated>"   forward
        when xkey is keyBack                                       forward
        when xkey is keyEnter                                      break conditions
        else  result = false  and  beep 1
    return result

so the result is true for an allowed character, Backspace and Enter, and
false (with a beep) for every other key.
"""

from __future__ import annotations

import re

_UNKNOWN = object()

KEY_BACK = 8
KEY_ENTER = 13

NUMERIC = "0,1,2,3,4,5,6,7,8,9,.,+,-"
ALPHABETIC = "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z"


def call(state, name: str, args: str):
    """One call made by a fill-in page script. Unknown names return a sentinel."""
    key = (name or "").lower()
    if key == "donumeric":
        return _filter(state, args, NUMERIC)
    if key == "doalphabetic":
        return _filter(state, args, ALPHABETIC)
    if key == "setupfillinfields":
        return _setup_fields(state, 25, form=False)
    if key == "setupformfields":
        return _setup_fields(state, 12, form=True)
    if key == "asym_isnumber":
        return is_number(_text(state, _args(args)[:1]))
    if key == "asym_isalphabetic":
        return is_alphabetic(_text(state, _args(args)[:1]))
    if key == "writeresponse":
        a = _args(args)
        return write_response(
            state, _int(_page_arg(state, a, 0)), _int(_page_arg(state, a, 1)), 0,
            _page_arg(state, a, 2), _int(_page_arg(state, a, 3)),
        )
    if key == "writeresponseb":
        a = _args(args)
        return write_response(
            state, _int(_page_arg(state, a, 0)), _int(_page_arg(state, a, 1)), _int(_page_arg(state, a, 2)),
            _page_arg(state, a, 3), _int(_page_arg(state, a, 4)),
        )
    if key == "saveembedded":
        return _save_embedded(state, _args(args))
    if key == "incorrectfillin":
        return _incorrect_fill_in(state, _args(args))
    if key == "setupandgoto":
        return _setup_and_goto(state, _args(args))
    return _UNKNOWN


def _filter(state, args: str, allowed: str) -> bool:
    from engine.engine import _eval
    code = _eval(args.strip(), state)
    try:
        code = int(code)
    except (TypeError, ValueError):
        code = -1
    if allows(code, allowed):
        return True
    state.variables["__beep"] = True
    return False


def allows(code: int, allowed: str) -> bool:
    """Would the filter let this key through. `allowed` is the book's list."""
    if code in (KEY_BACK, KEY_ENTER):
        return True
    if not 0 < code < 256:
        return False
    # `r is in "a,b,c"` tests the items of the list, so a comma is not one.
    return chr(code).upper() in allowed.split(",")


def _setup_fields(state, count: int, form: bool) -> int:
    """setupFillinFields and setupFormFields, as nc81test.sbk writes them.

    Each looks for the fields "response" and "response 1" to "response N" on
    this page. At reader level the text is cleared. At author level it is
    "?", which is what the file stores. setupFormFields also sets the stroke
    colour of each of them (the text colour here) to yellow.
    """
    from engine.engine import _var, set_shape_text
    page = state.page
    if page is None:
        return 0
    reader = str(_var(state, "sysLevel")).lower() == "reader"
    text = "" if reader else "?"
    names = ["response"] + [f"response {n}" for n in range(1, count + 1)]
    for shape in page.shapes or []:
        name = (shape.get("name") or "").strip().lower()
        if (shape.get("kind") or "") != "text" or name not in names:
            continue
        set_shape_text(state, shape, text)
        if form:
            shape["outline"] = "#ffff00"
    return 0


_NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)")


def is_number(text: str) -> bool:
    """ASYM_IsNumber: an optional sign, digits and at most one point.

    ASYM_IsNumber is a ToolBook runtime function that no book defines, so
    this is an assumption: it is the plainest reading of a number a numeric
    field can hold. An empty field, `?`, `7a` and `1-2` are not numbers.
    """
    return _NUMBER.fullmatch(text or "") is not None


def is_alphabetic(text: str) -> bool:
    """ASYM_IsAlphabetic: letters only, and at least one (an assumption, as above)."""
    return bool(text) and text.isascii() and text.isalpha()


def _args(text: str) -> list[str]:
    """The arguments of a call as written, split on commas outside quotes and brackets."""
    found: list[str] = []
    cur: list[str] = []
    quote = ""
    depth = 0
    for ch in text or "":
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif ch == "," and depth == 0:
            found.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail or found:
        found.append(tail)
    return found


def _text(state, args: list[str]) -> str:
    from engine.engine import _eval
    if not args:
        return ""
    value = _eval(args[0], state)
    return "" if value is None else str(value)


def _page_arg(state, args: list[str], at: int) -> str:
    from engine.engine import _eval
    if at >= len(args):
        return ""
    value = _eval(args[at], state)
    return "" if value is None else str(value)


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def tries(state) -> int:
    """`__embeddedTries`: the wrong answers so far, kept across pages."""
    return _int(state.variables.get("__embeddedTries"))


def _save_embedded(state, args: list[str]) -> int:
    """saveEmbedded(test, question, response), as nc81test.sbk writes it.

        increment(__embeddedTries)
        score = 100.00 / __embeddedTries
        writeResponse(test, question, response, score)
        __embeddedTries = 0

    So the score is 100 on the first try, 50 after one miss, 33 after two.
    """
    count = tries(state) + 1
    # An int takes the real quotient rounded (an assumption: 100/3 is 33 either way).
    score = int(100.0 / count + 0.5)
    write_response(
        state,
        _int(_page_arg(state, args, 0)),
        _int(_page_arg(state, args, 1)),
        0,
        _page_arg(state, args, 2),
        score,
    )
    state.variables["__embeddedTries"] = 0
    return 0


def _incorrect_fill_in(state, args: list[str]):
    """IncorrectFillIn(try-again page, reveal page), as nc81test.sbk writes it.

        increment(__embeddedTries)
        if __embeddedTries >= 3 then  __embeddedTries = 0 ; setupAndGoto(page2)
        else                          lastpage = name of this page ; setupAndGoto(page1)

    A wrong answer records nothing. The third one shows the reveal page.
    """
    count = tries(state) + 1
    state.variables["__embeddedTries"] = count
    if count >= 3:
        state.variables["__embeddedTries"] = 0
        return _setup_and_goto(state, args[1:2])
    page = state.page
    state.variables["lastpage"] = page.id if page is not None else ""
    return _setup_and_goto(state, args[:1])


def _type_number(question: int) -> int:
    """The record type writeResponseB gives a question number."""
    if 0 <= question < 100:
        return 1
    if 100 <= question < 150:
        return 2
    if 150 <= question < 200:
        return 3
    if 200 <= question < 250:
        return 4
    if question > 32000:
        return 32
    return 3


def write_response(state, test: int, question: int, part: int, response: str, score: int) -> int:
    """writeResponse / writeResponseB.

    The book does nothing unless `__studentRecords` is not 0. Otherwise it
    calls RecWriteResponse in nc81rec.dll, a Windows library this reader does
    not have. The record is kept in `__responses`, one dict per answer, with
    the same fields the DLL is given.
    """
    if not _int(state.variables.get("__studentRecords")):
        return 0
    state.variables.setdefault("__responses", []).append({
        "student": state.variables.get("__studentIndex", ""),
        "type": _type_number(question),
        "test": test,
        "question": question,
        "part": part,
        "response": response,
        "score": score,
    })
    return 0


def _setup_and_goto(state, args: list[str]):
    """setupAndGoto(page): setupAndWait, flushMessageQueue, go to page."""
    name = _page_arg(state, args, 0)
    return ("goto", name) if name else 0
