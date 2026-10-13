# Changelog

## Next

- Browser author moved to FoolbookEditor. This repository is the reader.
- `foolbook.core` is the door the editor calls. Loading, saving, office files, and OpenScript compile stay here.
- Page graphics. A page's `shapes` are drawn in the window for that page: rect, ellipse, line, polygon, text, and image. Coordinates are the book's own pixels.
- A ToolBook book still comes from its page stream. The stream is decoded to handlers and the window runs them with the existing engine. Shapes are not read out of that stream.

## 1.0.1r1

- Package is now `foolbook`. No more `main` collision.


## 1.0.1

- Rudimentary graphics in the GUI viewer: explicit polygons and bounds-only rectangles from the page blob.
- System-book contract: core `.fsk` load first, user `.fsk` load after as mods.
- `projectphilosophy.md` added.

## 1.0.0r1

Revision of 1.0.0. The viewer, the student file, and a first `.tbk` export.

- Viewer on port 1337. `--port` overrides it
- Finish records quiz answers, marks the course complete, saves the score, and closes
- Encrypted `.fcs` student file. Foolcourse Student
- `--student`, `--locale`, `--course`
- A course locale overlay is applied when the course has one
- OpenScript compiler, the inverse of the decoder
- Export `.tbk` writes a shell: locator, book tree, page props, compiled handlers
- Opens the viewer with xdg-open. Chrome is the fallback
- Already-running catch, so a second viewer does not bind the same port

## 1.0.0

First release.

## 1.0.1r2

- Native window viewer; exits when closed
- Splash on bare launch (2+2=5); course and direct open at last page
- Default book using_foolbook.json
- --freshstart and --doctor
- _debug/ dumps diagnostics

