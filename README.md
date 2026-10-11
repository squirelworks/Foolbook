# Foolbook

The main tool that opens a book.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader. It opens `.fbk` and `.tbk` books, and processes `.fsk` and `.sbk` system books.

## How it starts

- Passed a path: opens that book.
- Started with no path: asks for a file.
- Launched by a course module: the module passes the book path, and Foolbook opens it.

```bash
python3 -m foolbook path/to/book.fbk          # open a Foolbook book
python3 -m foolbook path/to/book.tbk          # open a ToolBook book
python3 -m foolbook                           # ask for a file
python3 -m foolbook --gui path/to/book        # GUI viewer
python3 -m foolbook --menu _courses/catalog.json
python3 -m foolbook --catalog                 # rebuild _courses/catalog.json
python3 -m foolbook --author                  # slide editor
python3 -m foolbook --debug                   # files and checksums
```

A course module (Foolcourse, when it exists) is the driver. It decides which course, then launches Foolbook with the book path.

## Layout

```
Foolbook/
  foolbook/                 # entry point
  engine/                   # parse and interpret
  viewer/                   # CLI and GUI
  author/                   # slide editor
  menu/                     # course menu
  progress/                 # progression tracking (scaffold)
  core/                     # system books (.fsk standard, .sbk compatible)
  _courses/                 # sample courses and catalog
  _debug/                   # debug package (only with --debug)
```

## Formats

- `.fbk` — Foolbook book (standard)
- `.fsk` — Foolbook system book (standard)
- `.tbk` — ToolBook book (compatibility)
- `.sbk` — ToolBook system book (compatibility)

The loader decodes OpenScript handlers from a `.tbk` and the viewer follows them. On a page with a `buttonClick` that says `go to page "P400"`, choosing Next goes to P400. Cross-book targets are noted but not followed yet.

## Design notes

- Foolbook is the viewer. A course module drives which book it opens.
- The entry point stays in `foolbook/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Authoring tools stay under `author/` and are not required to view a book.

