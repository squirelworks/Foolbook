"""getTrainerType and getTrainerCode, as nc81trnr.sbk answers them with no NIDAREC.INI."""

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book


def _state():
    return RuntimeState(book=Book(path="x.tbk"), index=0)


PICK = (
    'trainer = gettrainertype()\n'
    'conditions\n'
    '  when trainer is "130A"\n'
    '    go to page "P330"\n'
    '    break\n'
    '  when trainer is "130E"\n'
    '    go to page "P320"\n'
    '    break\n'
    '  else\n'
    '    request "Your trainer type is set to"&&trainer&"." with OK\n'
    '    break\n'
    'end conditions\n'
    'send next\n'
)


class TrainerType(unittest.TestCase):
    def test_default_trainer_is_130e(self):
        state = _state()
        acts = run_handler(state, PICK)
        self.assertIn({"kind": "goto", "page": "P320"}, [{k: a.get(k) for k in ("kind", "page")} for a in acts])
        self.assertEqual(state.variables.get("trainer"), "130E")

    def test_each_trainer_type(self):
        for number, name in ((-1, "THEORY"), (0, "TD2000"), (1, "130C"), (2, "130A"), (3, "130E")):
            state = _state()
            state.variables["__trainerType"] = number
            run_handler(state, "trainer = gettrainertype()")
            self.assertEqual(state.variables.get("trainer"), name)

    def test_unknown_number_is_theory(self):
        state = _state()
        state.variables["__trainerType"] = 9
        run_handler(state, "trainer = gettrainertype()")
        self.assertEqual(state.variables.get("trainer"), "THEORY")

    def test_trainer_code_is_empty_without_an_ini(self):
        state = _state()
        run_handler(state, 'code = gettrainercode("I")\nif code is "CC"\n  x = 1\nelse\n  x = 2\nend if')
        self.assertEqual(state.variables.get("code"), "")
        self.assertEqual(state.variables.get("x"), 2)


if __name__ == "__main__":
    unittest.main()
