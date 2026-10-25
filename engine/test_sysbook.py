"""System-book pages keep their names, and a handler survives a bare end."""

import unittest

from engine.engine import RuntimeState, follow, open_book, run_handler, split_handlers
from engine.tbk import load
from foolbook.model import Book, Page
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

    def test_the_shell_returns_to_the_book_still_open(self):
        lesson = Book(path="/courses/9e954d01.tbk", title="9e954d01", pages=[
            Page(id="P10"), Page(id="P100"),
        ])
        state = RuntimeState(book=lesson, index=1)
        state.variables["lastbook"] = "9e954d01"
        state.variables["nextpage"] = "P100"
        self.assertTrue(open_book(state, "nida81.tbk", "P20001"))
        self.assertEqual(state.page.id, "P20001")
        actions = run_handler(state, "go to page (nextpage) of book(lastbook)")
        self.assertTrue(follow(state, actions))
        self.assertIs(state.book, lesson)
        self.assertEqual(state.page.id, "P100")

    def test_the_menu_goes_to_p900_and_the_final_quiz_to_p10004(self):
        lesson = Book(path="x", title="t", pages=[
            Page(id="P450"), Page(id="P900"), Page(id="P10003"), Page(id="P10004"),
        ])
        state = RuntimeState(book=lesson, index=0)
        actions = run_handler(state, "get gotoMenuPage()")
        self.assertEqual(actions[0]["page"], "P900")
        actions = run_handler(state, "get gotoQuizPage()")
        self.assertEqual(actions[0]["page"], "P10004")
        state.variables["__lessonMode"] = 1
        actions = run_handler(state, "get gotoQuizPage()")
        self.assertEqual(actions[0]["page"], "P10003")

    def test_a_uppercase_book_name_still_matches(self):
        from engine.loader import find_book
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "NIDA81.TBK").write_bytes(b"x")
            found = find_book("nida81.tbk", folder / "lesson.tbk")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "NIDA81.TBK")

    def test_a_quiz_opens_on_a_question_and_the_choice_is_not_the_marker(self):
        pages = [Page(id="P10004"), Page(id="P10303")]
        for number in range(110, 130):
            pages.append(Page(
                id=f"Q{number}",
                raw={"props": {"QuestionNo": str(number), "Answer": "C"}},
                shapes=[
                    {"name": "A", "kind": "image"},
                    {"name": "A", "kind": "text", "text": "7400"},
                    {"name": "C", "kind": "image"},
                    {"name": "Correct", "kind": "rect", "visible": False},
                    {"name": "Index", "kind": "text", "text": "Question 10."},
                ],
            ))
        state = RuntimeState(book=Book(path="lesson.tbk", title="lesson", pages=pages))
        state.variables["__pools"] = [(110, 119, 6), (120, 129, 4)]
        from engine.quiz import call
        self.assertEqual(call(state, "setupPool", ""), 0)
        landed = call(state, "gotoNextQuestionEx", "")
        self.assertEqual(landed[0], "goto")
        self.assertNotEqual(landed[1], "P10303")
        page = next(item for item in pages if item.id == landed[1])
        self.assertTrue(page.shapes[-2]["visible"] is False)
        self.assertIn("Question 1", page.shapes[-1]["text"])
        state.index = pages.index(page)
        state.variables["target"] = "A"
        self.assertEqual(call(state, "handleQuizClick", "target"), 0)
        self.assertEqual(state.variables["__choice"], "A")
        self.assertTrue(page.shapes[0]["checked"])
        self.assertFalse(page.shapes[1].get("checked"))
        moved = call(state, "handleQuizClick", "OK")
        self.assertEqual(moved[0], "goto")
        self.assertNotEqual(moved[1], landed[1])

    def test_a_list_opened_question_still_leaves_the_page(self):
        from engine.quiz import call
        pages = [Page(id="P10213"), Page(id="P10214"), Page(id="P10215")]
        state = RuntimeState(book=Book(path="lesson.tbk", title="lesson", pages=pages), index=1)
        self.assertEqual(call(state, "handleQuizClick", "OK"), ("goto", "P10215"))
        self.assertEqual(call(state, "handleQuizClick", "Back"), ("goto", "P10213"))
        state.variables["__quizCount"] = 10
        state.variables["__quizPass"] = 1
        state.variables["__choice"] = ""
        self.assertEqual(call(state, "handleQuizClick", "OK"), 0)

    def test_the_end_page_shows_the_percent_and_review_is_a_choice(self):
        from engine.engine import run_handler, follow
        from engine.quiz import finish
        end = Page(id="P10303", shapes=[{"name": "Stem", "kind": "text", "text": "score is XX%"}])
        question = Page(id="Q110", raw={"props": {"QuestionNo": "110", "Answer": "A"}}, shapes=[{"name": "Index", "kind": "text", "text": ""}])
        state = RuntimeState(book=Book(path="lesson.tbk", title="lesson", pages=[end, Page(id="P10410"), Page(id="P900"), question]))
        state.variables["__quizScore"] = {1: 100, 2: 0}
        state.variables["__quizCount"] = 2
        state.variables["__quizNumbers"] = [0, 110]
        script = 'if  target is button "OK" of parent of this page  then\n\tsend okClicked to this page\nend if'
        state.variables["target"] = "OK"
        state.variables["__choice"] = ""
        self.assertFalse(follow(state, run_handler(state, script)))
        self.assertEqual(state.page.id, "P10303")
        state.variables["__choice"] = "B"
        self.assertTrue(follow(state, run_handler(state, script)))
        self.assertEqual(state.page.id, "P10410")
        self.assertEqual((state.variables.get("__menuFlags") or [1] * 10)[9], 1)
        state.index = 0
        state.variables["__quizScore"] = {1: 100, 2: 100}
        state.variables["__choice"] = "B"
        self.assertEqual(finish(state)[1], "P900")
        self.assertEqual(state.variables["__menuFlags"][9], 2)
        state.variables["__choice"] = "A"
        state.variables["__pools"] = [(110, 110, 1)]
        landed = finish(state)
        self.assertEqual(landed[1], "Q110")

    def test_exit_asks_and_no_stays(self):
        from engine.engine import run_handler
        source = '''to handle keyup key
\tconditions
\t\twhen key = keyf2
\t\t\trequest "Are you sure you want to Exit the Lesson?" with "&Yes" or "&No"
\t\t\tif it is "Yes" then
\t\t\t\tsend exit
\t\t\tend if
\tend conditions
end'''
        state = RuntimeState(book=Book(path="lesson.tbk", title="lesson", pages=[Page(id="P900")], handlers=[]))
        state.book.handlers = [type("H", (), {"name": "keyup", "source": source})()]
        state.ask = lambda text: "No"
        actions = run_handler(state, 'send keyup keyF2')
        self.assertFalse(state.variables.get("__exit"))
        self.assertNotIn("Are you sure", "")
        state.ask = lambda text: "Yes"
        actions = run_handler(state, 'send keyup keyF2')
        self.assertTrue(state.variables.get("__exit"))
        self.assertTrue(actions)

    def test_a_practice_answer_takes_the_fill_the_script_names(self):
        page = Page(id="P1310", shapes=[{"name": "correct", "kind": "text", "text": "10", "fill": "#40ffff"}])
        state = RuntimeState(book=Book(path="x", title="t", pages=[page, Page(id="P1311")]))
        actions = run_handler(state, 'rgbfill of field "correct" = 255,255,63\ngo to page "p1311"\n')
        self.assertEqual(page.shapes[0]["fill"], "#ffff3f")
        self.assertTrue(follow(state, actions))
        self.assertEqual(state.page.id, "P1311")

    def test_leaving_the_section_recolours_the_menu_label(self):
        from foolbook.model import Handler
        from engine.engine import enter_page, goto
        labels = [
            {"name": "Selection 1", "kind": "text", "text": "1. TTL", "outline": "#000000"},
            {"name": "Selection 2", "kind": "text", "text": "2. Other", "outline": "#000000"},
            {"name": "Selection T", "kind": "text", "text": "3. Final Quiz", "outline": "#000000"},
            {"name": "Exit", "kind": "text", "text": "* Lesson Exit", "outline": "#000000"},
        ]
        menu = Page(id="P900", handlers=[Handler(name="enterPage", source="get setupMenuPageLocal()")], shapes=labels)
        end = Page(id="P1910", handlers=[Handler(name="leavePage", source="get SetMenuFlag(1)")])
        state = RuntimeState(book=Book(path="x", title="t", pages=[menu, end]), index=1)
        self.assertTrue(goto(state, "P900"))
        enter_page(state)
        ink = {shape["name"]: shape["outline"] for shape in state.page.shapes}
        self.assertEqual(ink["Selection 1"], "#bf80ff")
        self.assertEqual(ink["Selection 2"], "#000000")
        self.assertEqual(ink["Selection T"], "#000000")
        self.assertEqual(ink["Exit"], "#000000")

    def test_reader_level_greets_the_student(self):
        from foolbook.model import Handler
        from engine.engine import enter_page
        source = '''if syslevel = reader then
\tset text of field "First" to "Hello" && getFirst() & ", this lesson is about:"
else
\tset text of field "First" to "Hello, this lesson is about:"
end if
get setSection("Intro")
forward'''
        field = {"name": "first", "kind": "text", "text": "stored"}
        page = Page(id="P10", handlers=[Handler(name="enterPage", source=source)], shapes=[field])
        state = RuntimeState(book=Book(path="x", title="t", pages=[page]))
        state.variables["sysLevel"] = "reader"
        enter_page(state)
        self.assertEqual(field["text"], "Hello Student, this lesson is about:")
        field["text"] = "stored"
        state.variables["__studentFirst"] = " Ada "
        enter_page(state)
        self.assertEqual(field["text"], "Hello Ada, this lesson is about:")
        field["text"] = "stored"
        state.variables["sysLevel"] = "author"
        enter_page(state)
        self.assertEqual(field["text"], "Hello, this lesson is about:")

    def test_the_score_line_is_filled_when_the_page_opens(self):
        from engine.engine import enter_page
        line = "The test is complete and your score is XX%.  Do you want to _________"
        field = {"name": "Stem", "kind": "text", "text": line}
        page = Page(id="P10303", shapes=[field])
        state = RuntimeState(book=Book(path="x", title="t", pages=[page]))
        state.variables["__quizScore"] = {1: 100, 2: 0}
        state.variables["__quizCount"] = 2
        enter_page(state)
        self.assertEqual(field["text"], "The test is complete and your score is 50%.  Do you want to _________")
        field["text"] = line
        state.variables["sysLevel"] = "author"
        enter_page(state)
        self.assertEqual(field["text"], line)


class FaceTests(unittest.TestCase):
    def test_a_wingdings_w_is_a_bullet_and_a_letter_is_not(self):
        from openscript_analysis.formats.tbk.store import apply_faces
        text, face = apply_faces("w Describe", [(0, "Wingdings"), (1, "Arial")])
        self.assertEqual(text, "\u2022 Describe")
        self.assertEqual(face, "Arial")
        self.assertEqual(apply_faces("write", [(0, "Arial")])[0], "write")


if __name__ == "__main__":
    unittest.main()
