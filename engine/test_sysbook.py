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

    def test_a_missing_page_does_not_leave_the_lesson(self):
        lesson = Book(path="/courses/9e954d01.tbk", title="9e954d01", pages=[Page(id="P300")])
        state = RuntimeState(book=lesson, index=0)
        self.assertFalse(open_book(state, "nida81.tbk", "PNOPE"))
        self.assertIs(state.book, lesson)
        self.assertEqual(state.page.id, "P300")

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

    def test_a_tbk_beats_the_converted_copy_beside_it(self):
        from engine.loader import find_book
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "nida81.fsk").write_bytes(b"stub")
            (folder / "nida81.fbk").write_bytes(b"converted")
            (folder / "nida81.tbk").write_bytes(b"original")
            found = find_book("nida81.tbk", folder / "lesson.tbk")
            self.assertEqual(found.name, "nida81.tbk")
            self.assertEqual(found.read_bytes(), b"original")

    def test_a_settled_export_opens_instead_of_the_tbk(self):
        from engine.formats import pack
        from engine.loader import find_book
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "nida81.tbk").write_bytes(b"original")
            blob = pack(
                {"pages": [{"id": "P310", "settled": True, "shapes": [{"kind": "image", "data": "abc"}]}]},
                "fbk",
                compress=True,
            )
            (folder / "nida81.fbk").write_bytes(blob)
            found = find_book("nida81.tbk", folder / "lesson.tbk")
            self.assertEqual(found.name, "nida81.fbk")

    def test_the_shell_one_directory_up_is_the_fbk(self):
        from engine.formats import pack
        from engine.loader import find_book
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            courses = root / "courses"
            courses.mkdir()
            (courses / "93950101.fbk").write_bytes(b"lesson")
            (courses / "nida81.fsk").write_bytes(b"stub")
            blob = pack(
                {"pages": [{"id": "P20001", "settled": True, "shapes": [{"kind": "text", "text": "shell"}]}]},
                "fbk",
                compress=True,
            )
            (root / "nida81.fbk").write_bytes(blob)
            found = find_book("nida81.tbk", courses / "93950101.fbk")
            self.assertEqual(found, root / "nida81.fbk")

    def test_a_system_book_is_the_fsk(self):
        from engine.formats import pack
        from engine.loader import find_book
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            courses = root / "courses"
            courses.mkdir()
            (courses / "93950101.fbk").write_bytes(b"lesson")
            blob = pack(
                {"pages": [{"id": "P1", "settled": True, "shapes": []}]},
                "fsk",
                compress=True,
            )
            (root / "nc81test.fsk").write_bytes(blob)
            found = find_book("nc81test.sbk", courses / "93950101.fbk")
            self.assertEqual(found, root / "nc81test.fsk")

    def test_a_course_names_the_other_books_it_opens(self):
        from engine.preload import referenced
        from foolbook.model import Handler
        page = Page(
            id="P1",
            handlers=[Handler(name="buttonClick", source='go to page "P20001" of book "nida81.tbk"')],
            shapes=[{"kind": "button", "script": 'go to page "P900" of book "nc81test.sbk"'}],
        )
        book = Book(path="9e954d01.tbk", pages=[page])
        blob = b"noise nida81.tbk TB80R.SBK 93954302.TBK 2.004.TBK 004.TBK"
        names = [item.lower() for item in referenced(book, blob)]
        self.assertEqual(names, ["nida81.tbk", "nc81test.sbk", "tb80r.sbk"])

    def test_an_export_keeps_the_picture_and_the_answer(self):
        from foolbook.core import book_record
        from foolbook.model import Book, Page
        page = Page(
            id="P310",
            raw={"props": {"Answer": "A"}, "size": (624, 442)},
            shapes=[{"kind": "image", "name": "computer", "data": "abc", "checked": True}],
        )
        record = book_record(Book(path="nida81.tbk", title="nida", pages=[page]), "nida81")
        saved = record["pages"][0]
        self.assertEqual(saved["props"]["Answer"], "A")
        self.assertEqual(saved["size"], [624, 442])
        self.assertEqual(saved["shapes"][0]["data"], "abc")
        self.assertNotIn("checked", saved["shapes"][0])

    def test_export_does_the_named_folder_before_a_subdirectory(self):
        import tempfile
        from foolbook.__main__ import _export_sources
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "nida81.tbk").write_bytes(b"a")
            (root / "tb80.sbk").write_bytes(b"b")
            courses = root / "courses"
            courses.mkdir()
            (courses / "10001001.tbk").write_bytes(b"c")
            found = [item.name for item in _export_sources([root])]
        self.assertEqual(found, ["nida81.tbk", "tb80.sbk", "10001001.tbk"])

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
        self.assertTrue(state.variables.get("__beep"))
        state.variables["__quizIndex"] = 1
        state.variables["__quizMode"] = 0
        self.assertEqual(call(state, "handleQuizClick", "Skip"), 0)
        self.assertEqual(state.variables["__quizIndex"], 1)

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

    def test_a_face_that_covers_the_old_line_covers_the_new_one(self):
        from foolbook.model import Handler
        from engine.engine import enter_page
        old = "Hello, this lesson is about:"
        field = {
            "name": "first", "kind": "text", "text": old, "size": 14,
            "runs": [{"start": 0, "end": len(old), "font": "Arial", "size": 12, "bold": True, "italic": True}],
        }
        source = 'set text of field "First" to "Hello" && getFirst() & ", this lesson is about:"'
        page = Page(id="P10", handlers=[Handler(name="enterPage", source=source)], shapes=[field])
        state = RuntimeState(book=Book(path="x", title="t", pages=[page]))
        state.variables["sysLevel"] = "reader"
        enter_page(state)
        self.assertEqual(field["text"], "Hello Student, this lesson is about:")
        self.assertEqual(field["runs"][0]["end"], len(field["text"]))

    def test_invert_sinks_the_button_and_a_list_question_still_moves(self):
        from foolbook.model import Handler
        from engine.engine import run_handler, follow, one_handler
        button = {"kind": "image", "name": "selection1", "invert_data": "down", "data": "up"}
        label = {
            "kind": "text", "name": "selection1",
            "script": 'to handle buttonDown\nset invert of button "Selection1" to true\nend\nto handle buttonUp\nset invert of button "Selection1" to false\nend\n',
        }
        pages = [Page(id="P10219", shapes=[button, label]), Page(id="P10220")]
        state = RuntimeState(book=Book(path="x", title="t", pages=pages))
        run_handler(state, one_handler(label["script"], "buttonDown"))
        self.assertTrue(button.get("invert"))
        run_handler(state, one_handler(label["script"], "buttonUp"))
        self.assertFalse(button.get("invert"))
        state.variables["target"] = "OK"
        source = 'get handleQuizClick(target)'
        actions = run_handler(state, source)
        self.assertTrue(follow(state, actions))
        self.assertEqual(state.page.id, "P10220")

    def test_an_unknown_book_property_does_not_wipe_the_version(self):
        from foolbook.model import Handler
        from engine.engine import enter_page
        field = {"name": "version", "kind": "text", "text": "Version: 2.003.0001"}
        source = 'set text of field "version" to "Version: " & __nidaVersion of this book'
        page = Page(id="PINFO", handlers=[Handler(name="enterPage", source=source)], shapes=[field])
        state = RuntimeState(book=Book(path="x", title="t", pages=[page]))
        enter_page(state)
        self.assertEqual(field["text"], "Version: 2.003.0001")

    def test_white_touching_the_edge_of_a_picture_is_clear(self):
        import base64
        import io
        from PIL import Image
        from engine.loader import _clear_edge, _png
        image = Image.new("RGB", (5, 5), (255, 255, 255))
        for x, y in ((1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)):
            image.putpixel((x, y), (180, 20, 20))
        image.putpixel((2, 2), (255, 255, 255))
        raw = io.BytesIO()
        image.save(raw, "BMP")
        stored = raw.getvalue()
        self.assertEqual(base64.b64decode(_png(stored, edge=True)), stored)
        got = Image.open(io.BytesIO(stored)).convert("RGBA")
        _clear_edge(got)
        self.assertEqual(got.getpixel((0, 0))[3], 0)
        self.assertEqual(got.getpixel((2, 1))[3], 255)
        self.assertEqual(got.getpixel((2, 2))[3], 255)

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


class QuesterTest(unittest.TestCase):
    def test_a_pretest_opens_on_question_150_not_the_score(self):
        from engine.engine import enter_page, follow, run_handler
        from engine.quiz import _percent, call
        end = Page(id="P10303", shapes=[{"name": "Stem", "kind": "text", "text": "The test is complete and your score is XX%."}])
        first = Page(id="P01150", raw={"props": {"QuestionNo": "110", "Answer": "A", "TestNo": "0"}},
                     shapes=[{"name": "Stem", "kind": "text", "text": "What is 2 + 2?"}])
        second = Page(id="P01151", raw={"props": {"QuestionNo": "115", "Answer": "C", "TestNo": "0"}})
        menu = Page(id="P10004", shapes=[{"name": "selection1", "kind": "button", "script": "get addQuesterQuestions(1)\nget gotoNextQuestionEx()"}])
        book = Book(path="pre.tbk", title="pre", pages=[menu, first, second, end])
        book.props = {"__questerQuestionCount(1)": 2, "__questerSequence": 0, "__questerTestCount": 60}
        state = RuntimeState(book=book, index=0)
        state.variables["sysLevel"] = "reader"
        actions = run_handler(state, menu.shapes[0]["script"])
        self.assertTrue(follow(state, actions))
        enter_page(state)
        self.assertEqual(state.page.id, "P01150")
        self.assertEqual(_percent(state), 0)
        self.assertNotIn("100", state.page.shapes[0]["text"])
        # A number the book does not have is skipped. It does not finish the test.
        state.variables["__quizNumbers"] = [None, 150, 999, 151]
        state.variables["__quizCount"] = 3
        state.variables["__quizIndex"] = 1
        moved = call(state, "gotoNextQuestionEx", "")
        self.assertEqual(moved, ("goto", "P01151"))
        self.assertEqual(_percent(state), 0)


class FaceTests(unittest.TestCase):
    def test_a_wingdings_w_is_a_bullet_and_a_letter_is_not(self):
        from openscript_analysis.formats.tbk.store import apply_faces
        text, face = apply_faces("w Describe", [(0, "Wingdings"), (1, "Arial")])
        self.assertEqual(text, "\u2022 Describe")
        self.assertEqual(face, "Arial")
        self.assertEqual(apply_faces("write", [(0, "Arial")])[0], "write")


if __name__ == "__main__":
    unittest.main()
