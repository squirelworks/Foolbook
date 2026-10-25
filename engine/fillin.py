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
