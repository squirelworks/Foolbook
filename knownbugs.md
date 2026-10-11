# Known bugs

Things that are wrong or incomplete in the current release.

- Cross-book jumps are noted, not followed. `go to page "P" of book "B"` does not open the other book.
- The OpenScript runner covers the common constructs (goto, send, assignment, put, set, get, increment, nested if, step). The rest of the language is not run.
- Quizzes are followed on the `.json` / `.fbk` path. They are not extracted from a raw `.tbk`.
- Graphics are not drawn. Polygons, bounds, and pictures are not placed in the viewer.
- System books (`.sbk` / `.fsk`) open as files. They are not used at runtime.
