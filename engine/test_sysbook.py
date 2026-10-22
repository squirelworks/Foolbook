"""System-book pages keep their names, and a handler survives a bare end."""

import unittest

from engine.engine import RuntimeState, run_handler, split_handlers
from engine.tbk import load
from foolbook.model import Book
from pathlib import Path
import tempfile


def _mark(name: str, ident: int = 1) -> bytes:
    head = bytes.fromhex("80650005000202") + ident.to_bytes(4, "little")
    raw = name.encode("latin1") + b"\x00"
    return head + raw + b"\x00" * 8


class PageNames(unittest.TestCase):
    def test_a_system_page_is_kept(self):
        blob = _mark("Initialization", 3) + _mark("URL Stuff", 1) + _mark("", 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sys.sbk"
            path.write_bytes(blob)
            book = load(path)
        self.assertEqual([p.name for p in book.pages], ["Initialization", "URL Stuff", "Page2"])


class Handlers(unittest.TestCase):
    def test_an_if_closed_with_end_still_runs(self):
        source = """
        to handle enterBook
            if target = self
                seen = 1
            end
            after = 2
        end
        to handle leaveBook
            gone = 1
        end
        """
        handlers = split_handlers(source)
        self.assertEqual([h.name for h in handlers], ["enterBook", "leaveBook"])
        state = RuntimeState(book=Book(path="x", title="tb80r"))
        state.variables["target"] = "self"
        # The comparison is text unless target is the string self.
        state.variables["target"] = state.variables.get("target")
        run_handler(state, handlers[0].source)
        self.assertEqual(state.variables.get("seen"), 1)
        self.assertEqual(state.variables.get("after"), 2)


class Lookup(unittest.TestCase):
    def test_an_sbk_request_opens_the_fsk(self):
        from engine.loader import find_book
        found = find_book("tb80r.sbk", Path("/tmp/nowhere/course.tbk"))
        self.assertIsNotNone(found)
        self.assertTrue(str(found).endswith("tb80r.fsk"))


class ButtonScripts(unittest.TestCase):
    def test_a_parenthesised_page_is_a_jump(self):
        actions = run_handler(RuntimeState(book=Book(path="x", title="t")), 'go to page("P1150")')
        self.assertEqual(actions[0]["page"], "P1150")

    def test_send_next_is_a_step(self):
        actions = run_handler(RuntimeState(book=Book(path="x", title="t")), "send next")
        self.assertEqual(actions[0], {"kind": "send", "name": "next"})


if __name__ == "__main__":
    unittest.main()
