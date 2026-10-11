# Foolbook milestones

## v1.0.0

Opens a book and follows its handlers. Authoring produces .fbk and .fsk.

Done:

- Opens `.fbk` and `.tbk`
- `.fbk` and `.fsk` are a real envelope (compressed or not), not renamed JSON
- Asks for a file if none is passed; a course module can launch it with a path
- Decodes OpenScript handlers and follows next / back / goto
- CLI and GUI viewers
- Authoring: slide editor with page list, preview, toolbar, text and lists; saves `.fbk` / `.fsk`
- `--debug` keeps decoded `.tbk` source; a normal run writes nothing
- `--bin` overrides the keyword table for `.tbk` / `.sbk`
- A jump to another book opens it if found below the loaded file, beside it, or in `core/`

## v1.x authorship

- Produce backwards-compatible `.tbk` and `.sbk` files

## v2.0.0 (planned)

- Graphics: polygons, bounds, and pictures drawn in the viewer
- Quizzes extracted from raw `.tbk` (books that already carry quiz data follow it)
- System books used as a runtime shell, not only as a jump target
- Cross-book navigation beyond the shell lookup
