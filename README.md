# Foolbook

The main tool that opens a book.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader. It opens `.fbk` and `.tbk` books, and processes `.fsk` and `.sbk` system books.

## How it starts

- Passed a path: opens that book.
- Started with no path: asks for a file.
- Launched by a course module: the module passes the book path, and Foolbook opens it.

```bash
python3 -m foolbook path/to/book.fbk          # open in the GUI
python3 -m foolbook                           # ask for a file, then open the GUI
python3 -m foolbook --cli path/to/book        # terminal viewer
python3 -m foolbook --menu _courses/catalog.json
python3 -m foolbook --catalog                 # rebuild _courses/catalog.json
python3 -m foolbook --bin path/to/res.bin book.tbk   # override keyword table for .tbk/.sbk
```

A course module (Foolcourse, when it exists) is the driver. It decides which course, then launches Foolbook with the book path.

## Layout

```
Foolbook/
  foolbook/                 # entry point
  engine/                   # parse and interpret
  viewer/                   # CLI and GUI
  menu/                     # course menu
  progress/                 # progression tracking (scaffold)
  core/                     # system books (.fsk standard, .sbk compatible)
  _courses/                 # sample courses and catalog
  _debug/                   # debug package (only with --debug)
  knownbugs.md
  CHANGELOG.md
```

## Formats

- `.fbk` — Foolbook book (standard). Binary envelope, compressed or not.
- `.fsk` — Foolbook system book (standard). Same envelope.
- `.json` — working copy
- `.tbk` — ToolBook book (compatibility)
- `.sbk` — ToolBook system book (compatibility)
- `.pdf`, `.ppt`, `.pptx`, `.doc`, `.docx`, `.odt` — opened as text pages. Pictures and styles are dropped. Writing those files back is FoolbookEditor.

`.fbk` and `.fsk` start with `FBK1` or `FSK1`, then a flags byte, then a JSON payload. Bit 0 of the flags means the payload is zlib-compressed. The engine reads compressed, uncompressed, and the older plain-JSON files.

The loader decodes OpenScript handlers from a `.tbk` using the clean keyword table in `engine/keywords.py`. The original ToolBook resource lives in `engine/compat/res_77.bin` and is only used if that table is missing. `.fbk` and `.fsk` already hold source and never use it.

## Design notes

- Foolbook is the viewer. A course module drives which book it opens.
- The entry point stays in `main/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Editing is not in this repository. It lives in FoolbookEditor, which calls `foolbook.core` for the work.

