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

## v1.x

Furthering v1.

- Graphics: polygons, bounds, and pictures drawn in the viewer
- Quizzes extracted from a raw `.tbk`
- System books used as a runtime shell, not only as a jump target
- Produce backwards-compatible `.tbk` and `.sbk` files

### Next check: TB80RTM opens a generated shell

The shells are closer to a real book. TB80RTM has not been asked to open one.

Done on disk:

- Locator at file `0x9EC`: dword `0xC00`, magic `0x22222222` (`ZZZTBKBOOKLOC`)
- JBO signature and version at `0xC00`
- Book-level `14 00 00` property tree before the pages
- Page records with `14 00 00 11` and the bounds words from a live page
- OpenScript handlers compiled by `engine/openscript.py` (`FUN_1040_0970` inverse)

Still open, and only a live open settles it:

- Whether the property tree is walked by length or by a count we have not found
- Whether a minimal book needs the resource directory that fills the gap in a real book
- Whether `go to page "P100"` is accepted, or the operand must be tokenized
- Whatever `CDBSENDCREATE` and `FUN_12c8_0850` reject before they write bounds

Test: Win98, TB80RTM, break at the JBO check, open a Filing taxes shell.
The failure should be a specific check, not "not a book."

## v2.0.0 (planned)

- Cross-book navigation beyond the shell lookup

