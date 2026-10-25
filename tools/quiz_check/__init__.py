"""Quiz checker: drives the real Tk viewer under Xvfb with xdotool and asserts what a quiz page does.

    python -m tools.quiz_check.run --courses /path/to/courses --all
    python -m tools.quiz_check.run --courses /path/to/courses --spec letter_choice_mark
    python -m tools.quiz_check.run --courses /path/to/courses --type fillin

No course file is part of this repository. A spec names a book by file stem and the courses folder
is given on the command line (or FOOLBOOK_COURSES).
"""
