# Changelog

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
