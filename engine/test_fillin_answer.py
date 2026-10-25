"""Enter in an answer field reads it, compares it, and goes to the page that says so."""

from __future__ import annotations

import unittest

from engine import fields, fillin
from engine.engine import _eval, run_handler, follow
from foolbook.model import Book, Page, RuntimeState

NUMERIC_KEYUP = """to handle keyChar key
  if DoNumeric (key) then
    forward
  end if
end

TO HANDLE KeyUp key
  system string nextpage
  system string lastpage
  if key <> KeyEnter
    forward
    break
  end if
  response = text of field "Response"
  if ASYM_IsNumber(response) = false then
    beep 1
    break
  end if
  pos = true
  if char 1 of response ="-" then
    clear char 1 of response
    pos=false
  end if
  if response =7 then
    if pos=true then
      get saveEmbedded(testno of this page,  questionno of this page, Response)
      lastpage = "p2070"
      nextpage = "p2080"
      go to page "p2071"
    else
      nextpage = "p2080"
      lastpage = "P2070"
      get IncorrectFillIn ("P2072", "P2073")
    end if
    else
      nextpage = "p2080"
      lastpage = "P2070"
      get IncorrectFillIn ("P2072", "P2073")
    end if
end
"""

TEXT_KEYUP = """TO HANDLE KeyUp key
  system string nextpage
  system string lastpage
  if key <> KeyEnter
    forward
    break
  end if
  response = text of field "Response"
  if (response = "(3,5)") then
    get saveEmbedded(testno of this page,  questionno of this page, Response)
    go to page "p1801"
  else
    get IncorrectFillIn ("P1800", "P1703")
  end if
end
"""

ALPHA_KEYUP = """TO HANDLE KeyUp key
  if key <> KeyEnter
    forward
    break
  end if
  response = text of field "Response"
  if ASYM_IsAlphabetic(response) = false then
    beep 1
    break
  end if
  if (response = "backspace") then
    go to page "p1801"
  else
    get IncorrectFillIn ("P1800", "P2763")
  end if
end
"""


def _book(script):
    field = {"kind": "text", "name": "Response", "text": "", "script": script, "x": 0, "y": 0, "w": 40, "h": 20}
    names = ("P2070", "P2071", "P2072", "P2073", "P1700", "P1800", "P1801", "P2760")
    pages = [Page(id=n, shapes=[field] if n in ("P2070",) else [], raw={"props": {"TestNo": "2", "QuestionNo": "20"}}) for n in names]
    state = RuntimeState(book=Book(path="x", pages=pages))
    state.variables["sysLevel"] = "reader"
    fields.focus(state, field)
    return state, field


def _answer(script, text):
    """Type text, then Return. The page the learner ends on, and whether it beeped."""
    state, field = _book(script)
    field["text"] = ""
    for char in text:
        fields.handle_key(state, "x", char)
    state.variables.pop("__beep", None)
    fields.handle_key(state, "Return", "\r")
    actions = fields.key_up(state, "Return", "\r")
    beeped = bool(state.variables.pop("__beep", None))
    follow(state, actions)
    return state.page.id, beeped


class Numeric(unittest.TestCase):
    def test_the_right_answer_goes_to_the_correct_page(self):
        for typed in ("7", "07", "7.0", "+7"):
            self.assertEqual(_answer(NUMERIC_KEYUP, typed), ("P2071", False), typed)

    def test_a_wrong_answer_goes_to_try_again(self):
        for typed in ("3", "70", "7.5", "-7", "-3"):
            self.assertEqual(_answer(NUMERIC_KEYUP, typed), ("P2072", False), typed)

    def test_a_non_number_beeps_and_stays(self):
        for typed in ("", "1-2", "1.2.3", "+", "."):
            self.assertEqual(_answer(NUMERIC_KEYUP, typed), ("P2070", True), repr(typed))

    def test_another_key_does_nothing(self):
        state, field = _book(NUMERIC_KEYUP)
        field["text"] = "7"
        self.assertIn("forward", [a["kind"] for a in fields.key_up(state, "a", "a")])
        self.assertEqual(state.page.id, "P2070")


class Text(unittest.TestCase):
    def test_a_text_answer_is_compared(self):
        self.assertEqual(_answer(TEXT_KEYUP, "(3,5)")[0], "P1801")
        self.assertEqual(_answer(TEXT_KEYUP, "(3,4)")[0], "P1800")

    def test_the_compare_ignores_case(self):
        self.assertEqual(_answer(ALPHA_KEYUP, "BackSpace")[0], "P1801")

    def test_alphabetic(self):
        self.assertEqual(_answer(ALPHA_KEYUP, "abc")[0], "P1800")
        self.assertEqual(_answer(ALPHA_KEYUP, "")[1], True)


class Interpreter(unittest.TestCase):
    def _state(self):
        state, field = _book("")
        field["text"] = "42"
        return state

    def test_text_of_a_field(self):
        state = self._state()
        self.assertEqual(_eval('text of field "Response"', state), "42")
        self.assertEqual(_eval('text of field "response" of this page', state), "42")
        self.assertEqual(_eval('text of field "nothing"', state), "")

    def test_a_property_of_the_page(self):
        state = self._state()
        self.assertEqual(_eval("testno of this page", state), 2)
        self.assertEqual(_eval("questionno of this page", state), 20)

    def test_char_of(self):
        state = self._state()
        state.variables["r"] = "-7"
        self.assertEqual(_eval("char 1 of r", state), "-")
        self.assertEqual(_eval("char 9 of r", state), "")

    def test_clear_char(self):
        state = self._state()
        run_handler(state, 'r = "-7"\nclear char 1 of r\n')
        self.assertEqual(state.variables["r"], "7")

    def test_compare_needs_no_spaces(self):
        state = self._state()
        state.variables["r"] = "7"
        for text in ("r =7", "r=7", "r = 7", "r= 7"):
            self.assertTrue(_eval(text, state), text)
        self.assertFalse(_eval("r<>7", state))
        self.assertTrue(_eval("r>=7", state))
        self.assertTrue(_eval("r<8", state))

    def test_numbers_compare_as_numbers_and_text_ignores_case(self):
        state = self._state()
        self.assertTrue(_eval('"07" = 7', state))
        self.assertTrue(_eval('"+7.0" = "7"', state))
        self.assertFalse(_eval('"7a" = 7', state))
        self.assertTrue(_eval('"ABC" = "abc"', state))
        self.assertFalse(_eval('"a = b" = "a"', state))

    def test_a_bracketed_compare(self):
        state = self._state()
        state.variables["r"] = "x"
        self.assertTrue(_eval('(r = "x")', state))
        self.assertTrue(_eval('(r = "x") and (r <> "y")', state))

    def test_break_ends_the_handler(self):
        state = self._state()
        run_handler(state, 'a = 1\nif a = 1\n  break\nend if\nb = 2\n')
        self.assertEqual(state.variables["a"], 1)
        self.assertNotIn("b", state.variables)

    def test_break_in_a_parent_does_not_end_the_child(self):
        state = self._state()
        run_handler(state, 'a = 1\nforward\nb = 2\n', ["break\n"])
        self.assertEqual(state.variables["b"], 2)

    def test_beep(self):
        state = self._state()
        run_handler(state, "beep 1\n")
        self.assertTrue(state.variables.pop("__beep"))


class Helpers(unittest.TestCase):
    def test_is_number(self):
        for text in ("7", "-7", "+7", "7.5", ".5", "7."):
            self.assertTrue(fillin.is_number(text), text)
        for text in ("", "?", "7a", "1-2", "--7", ".", "1.2.3", " 7"):
            self.assertFalse(fillin.is_number(text), repr(text))

    def test_is_alphabetic(self):
        self.assertTrue(fillin.is_alphabetic("abC"))
        for text in ("", "a1", "a b", "é"):
            self.assertFalse(fillin.is_alphabetic(text), repr(text))


if __name__ == "__main__":
    unittest.main()
