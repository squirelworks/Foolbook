# quiz_check

Drives the real Tk viewer under Xvfb with xdotool, the way a student would (click, type, press keys),
and asserts what the book's own scripts say should happen. PASS or FAIL per spec.

    # needs: python with foolbook installed or on PYTHONPATH, Xvfb, xdotool, a folder of the original .tbk/.sbk books
    python -m tools.quiz_check.run --courses /path/to/courses --all
    python -m tools.quiz_check.run --courses /path/to/courses --type keyboard
    python -m tools.quiz_check.run --courses /path/to/courses --spec embedded_right_after_wrong_scores_half
    python -m tools.quiz_check.run --list
    # the same sequence on another book or first page:
    python -m tools.quiz_check.run --courses DIR --spec letter_ok_advances --book 93951103

Run it from the repository root. No course file is in this repository: a spec names a book by file stem and the
folder comes from `--courses` or `FOOLBOOK_COURSES`. Screenshots (`--shots`, default `quiz_check_shots/`) and a
JSON result (`--json`) are written outside the books. The viewer's progress file is redirected to a scratch folder. The page list is the developer one, which shows every page id, so a `goto` step can find its page.

Types covered: letter choice (handleQuizClick), keyboard (handleQuizKey), embedded answers (saveEmbedded /
incorrectEmbedded), fill-in (doNumeric / doAlphabetic / incorrectFillin), form fields (setupFormFields), the
`checked of` set on the review strips, review passes, timed, and the launchers (clearpool / addObjectiveToPool /
setuppool, addQuestions, addObjectiveToPoolEx). A spec with `gated` needs a NIDAREC.INI setting that Foolbook
does not read yet (Quiz Mode 1 or 2, Timed Test 1); it is expected to FAIL until then.

A spec is a list of steps (`goto`, `click`, `type`, `key`, `set`, `wait`, `shot`) with `expect` blocks; see
`specs.py`. What `expect` says is taken from the book's scripts and nc81test.sbk, not from the reader.
