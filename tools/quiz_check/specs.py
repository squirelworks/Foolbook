"""The checks. One spec is a list of steps in one window of the real viewer.

A step is one of  goto PAGE | click NAME [kind] | type TEXT | key KEYSYM | set {VAR: value} | wait SECONDS | shot NAME
and may carry  expect  (what must be true afterwards) and  shot_after.

What `expect` says comes from the book's own scripts and the nc81test.sbk system book, not from the
reader: the click sequence is the sequence a student types, and the outcome is what ToolBook does.
Defaults of NIDAREC.INI apply (Quiz Mode 0, no critique, not timed, page numbers hidden).
"""
from __future__ import annotations


def _begin(book, menu_page="P10004", button="selection1"):
    """Open the quiz menu and press Begin. The first question page must come up."""
    return [
        {"goto": menu_page, "expect": {"page": menu_page}},
        {"click": button, "kind": "button",
         "expect": {"has_prop": "QuestionNo", "var_ops": [["__quizCount", ">=", 1]]},
         "shot_after": "first_question"},
    ]


def _letter_run(count, letter="A"):
    """Answer `count` questions with one letter each and press OK."""
    steps = []
    for n in range(1, count + 1):
        steps.append({"click": letter, "kind": "button", "expect": {"checked": {letter: True}}})
        steps.append({"click": "OK", "kind": "button", "expect": {"moved": True, "var": {"__choice": ""}}})
    return steps


SPECS = [
    # ---- letter choice, through handleQuizClick ------------------------------------------------------
    {"name": "letter_mark_one_of_many", "type": "letter", "book": "93951303",
     "doc": "a letter marks only itself; the second letter moves the mark",
     "steps": _begin("93951303") + [
         {"click": "B", "kind": "button", "expect": {"checked": {"B": True, "A": False}, "var": {"__choice": "B"}}},
         {"click": "C", "kind": "button", "expect": {"checked": {"C": True, "B": False}, "var": {"__choice": "C"}}},
         {"shot": "c_marked"}]},
    {"name": "letter_ok_without_choice", "type": "letter", "book": "93951303",
     "doc": "OK with nothing marked beeps and stays (handleQuizClick, pass 1)",
     "steps": _begin("93951303") + [
         {"click": "OK", "kind": "button", "expect": {"moved": False, "beeps_since": 1}}]},
    {"name": "letter_ok_advances", "type": "letter", "book": "93951303",
     "doc": "mark a letter, OK: next question, mark cleared, index counts up, score stored",
     "steps": _begin("93951303") + [
         {"click": "B", "kind": "button"},
         {"click": "OK", "kind": "button",
          "expect": {"moved": True, "var": {"__quizIndex": 2, "__choice": ""}, "has_prop": "QuestionNo",
                     "checked": {"A": False, "B": False, "C": False, "D": False}}},
         {"shot": "second_question"}]},
    {"name": "letter_full_pass", "type": "letter", "book": "93951303",
     "doc": "ten questions, one letter and OK each; the pass ends on the end page P10303",
     "steps": _begin("93951303") + _letter_run(10) + [
         {"wait": 0.2, "expect": {"page": "P10303"}}]},
    {"name": "letter_skip_mode0", "type": "letter", "book": "93951303",
     "doc": "Skip is disabled at Quiz Mode 0 in pass 1: it must not leave the page",
     "steps": _begin("93951303") + [
         {"click": "Skip", "kind": "button", "expect": {"moved": False}}]},
    {"name": "letter_text_index", "type": "letter", "book": "93951303",
     "doc": "setupQuizPage writes Question N and, with Show Page Numbers 0, the word Testing",
     "steps": _begin("93951303") + [
         {"wait": 0.1, "expect": {"text": {"Index": "Question 1.", "PageText": "Testing"}}}]},
    {"name": "letter_unused_fields_hidden", "type": "letter", "book": "93951303",
     "doc": "Correct and Mark are hidden in a running quiz (setupQuizPage, pass 1)",
     "steps": _begin("93951303") + [
         {"wait": 0.1, "expect": {"visible": {"Correct": False}}}]},
    {"name": "letter_second_book", "type": "letter", "book": "93951103",
     "doc": "three objectives: mark, OK, the next question opens",
     "steps": _begin("93951103") + [
         {"click": "A", "kind": "button", "expect": {"checked": {"A": True}}},
         {"click": "OK", "kind": "button", "expect": {"moved": True, "var": {"__quizIndex": 2}}}]},

    # ---- how a quiz is launched ------------------------------------------------------------------
    {"name": "launch_pool_by_objective", "type": "launch", "book": "93951303",
     "doc": "clearpool / addObjectiveToPool / setuppool: 10 questions in the pool",
     "steps": _begin("93951303") + [{"wait": 0.1, "expect": {"var": {"__quizCount": 10}}}]},
    {"name": "launch_add_questions", "type": "launch", "book": "93950102",
     "doc": "addQuestions(110,119,5) + addQuestions(120,129,5): 10 questions",
     "steps": _begin("93950102") + [{"wait": 0.1, "expect": {"var": {"__quizCount": 10}}}]},
    {"name": "launch_add_questions_3", "type": "launch", "book": "93950101",
     "doc": "addQuestions x3 (4+3+3): 10 questions",
     "steps": _begin("93950101") + [{"wait": 0.1, "expect": {"var": {"__quizCount": 10}}}]},
    {"name": "launch_pool_list_ex", "type": "launch", "book": "93952201",
     "doc": "addObjectiveToPoolEX(1, list, 3) + addObjectiveToPool(2,120,129,7): 10 questions",
     "steps": _begin("93952201") + [{"wait": 0.1, "expect": {"var": {"__quizCount": 10}}}]},

    # ---- keyboard, through handleQuizKey --------------------------------------------------------------
    {"name": "key_letter_marks", "type": "keyboard", "book": "93951303",
     "doc": "pressing b on a question marks B (keyChar -> handleQuizKey -> manageQuizButtons)",
     "steps": _begin("93951303") + [
         {"key": "b", "expect": {"checked": {"B": True, "A": False}, "var": {"__choice": "B"}}}]},
    {"name": "key_enter_is_ok", "type": "keyboard", "book": "93951303",
     "doc": "a letter key and Return: Return sends buttonClick to OK, so the next question opens",
     "steps": _begin("93951303") + [
         {"key": "c", "expect": {"checked": {"C": True}}},
         {"key": "Return", "expect": {"moved": True, "var": {"__quizIndex": 2}}}]},
    {"name": "key_return_without_choice", "type": "keyboard", "book": "93951303",
     "doc": "Return with nothing marked is OK with nothing marked: beep, stay",
     "steps": _begin("93951303") + [
         {"key": "Return", "expect": {"moved": False, "beeps_since": 1}}]},

    # ---- embedded answers: a hotspot is a text/rectangle with its own buttonClick ---------------------
    {"name": "embedded_correct_first_try", "type": "embedded", "book": "93950103",
     "doc": "P1090: the right answer first time goes to P1091 (CORRECT) and records 100",
     "steps": [
         {"goto": "P1090"}, {"set": {"__studentRecords": 1}},
         {"click": "correct", "kind": "text", "expect": {"page": "P1091", "var": {"__embeddedTries": 0}, "last_score": 100}}]},
    {"name": "embedded_wrong_goes_try_again", "type": "embedded", "book": "93950103",
     "doc": "P1090: a wrong answer goes to P1092 (TRY AGAIN) and counts one try",
     "steps": [
         {"goto": "P1090"},
         {"click": "incorrect1", "kind": "text", "expect": {"page": "P1092", "var": {"__embeddedTries": 1}}}]},
    {"name": "embedded_right_after_wrong_scores_half", "type": "embedded", "book": "93950103",
     "doc": "P1090: wrong, back, right: the score is 100 / 2 = 50 (saveEmbedded)",
     "steps": [
         {"goto": "P1090"}, {"set": {"__studentRecords": 1}},
         {"click": "incorrect1", "kind": "text", "expect": {"page": "P1092"}},
         {"click": "Back", "kind": "button", "expect": {"page": "P1090"}},
         {"click": "correct", "kind": "text", "expect": {"page": "P1091", "last_score": 50, "var": {"__embeddedTries": 0}}}]},
    {"name": "embedded_two_wrong_scores_third", "type": "embedded", "book": "93950103",
     "doc": "P1090: two wrong answers then the right one record 100 / 3 = 33",
     "steps": [
         {"goto": "P1090"}, {"set": {"__studentRecords": 1}},
         {"click": "incorrect1", "kind": "text", "expect": {"page": "P1092"}},
         {"click": "Back", "kind": "button", "expect": {"page": "P1090"}},
         {"click": "incorrect2", "kind": "text", "expect": {"page": "P1092", "var": {"__embeddedTries": 2}}},
         {"click": "Back", "kind": "button", "expect": {"page": "P1090"}},
         {"click": "correct", "kind": "text", "expect": {"page": "P1091", "last_score": 33}}]},

    # ---- fill-in family (merged in 1.0.8r1) -------------------------------------------------------------
    {"name": "fillin_numeric_right", "type": "fillin", "book": "93950101",
     "doc": "P2070: type 7, Return: P2071 says CORRECT",
     "steps": [{"goto": "P2070"}, {"click": "Response", "kind": "text"}, {"type": "7"},
               {"key": "Return", "expect": {"page": "P2071"}}]},
    {"name": "fillin_numeric_wrong", "type": "fillin", "book": "93950101",
     "doc": "P2070: type 5, Return: P2072 says TRY AGAIN",
     "steps": [{"goto": "P2070"}, {"click": "Response", "kind": "text"}, {"type": "5"},
               {"key": "Return", "expect": {"page": "P2072"}}]},
    {"name": "fillin_numeric_refuses_letter", "type": "fillin", "book": "93950101",
     "doc": "P2070: a letter is refused by doNumeric (field stays empty, one beep)",
     "steps": [{"goto": "P2070"}, {"click": "Response", "kind": "text"}, {"type": "x",
               "expect": {"text": {"Response": ""}, "beeps_since": 1}}]},
    {"name": "fillin_alpha_right", "type": "fillin", "book": "93950502",
     "doc": "P2760: letters only field, a word that is the answer goes to the right page",
     "steps": [{"goto": "P2760"}, {"click": "Response", "kind": "text"}, {"type": "x",
               "expect": {"text": {"Response": "X"}}}]},
    {"name": "fillin_enter_moves_field", "type": "fillin", "book": "93950102",
     "doc": "P1090: Return in Response 1 moves the focus to Response 2",
     "steps": [{"goto": "P1090"}, {"click": "Response 1", "kind": "text"}, {"type": "1"},
               {"key": "Return", "expect": {"page": "P1090"}}, {"type": "2", "expect": {"text": {"Response 2": "2"}}}]},
]
