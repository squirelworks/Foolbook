# Foolbook

A modular ToolBook-compatible player.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader built to open a `.tbk` or `.sbk` and present it.

## Main focus

Open Foolbook and feed it a book. The engine parses the file, interprets it, and drives the viewer.

```
python3 -m foolbook [book]
    → foolbook (viewer entry)
    → engine (parse .tbk/.sbk, interpret OpenScript)
    → model
    → display
```

Recovering the NIDA ToolBook environment (and the older ToolBook environment in general) means improving the engine’s ability to read those files and feed the result into Foolbook.

## Layout

```
Foolbook/
  foolbook/                 # entry point
  engine/                   # parse and interpret
  viewer/                   # the main program (CLI and GUI)
  menu/                     # course menu (subject / module / course)
  progress/                 # progression tracking (scaffold)
  core/                     # system and core books (.fbk/.fsk standard, .tbk/.sbk compatible)
  author/                   # authoring editor (coded Tkinter GUI)
  examples/
```

## Open Foolbook

```bash
python3 -m foolbook                         # course menu
python3 -m foolbook --menu examples/catalog.json
python3 -m foolbook path/to/book.tbk        # viewer
python3 -m foolbook --gui path/to/book.tbk  # GUI viewer
python3 -m author.gui                       # authoring editor
```

The loader decodes OpenScript handlers from a `.tbk` and the viewer follows them. On a page with a `buttonClick` that says `go to page "P400"`, choosing Next goes to P400. Cross-book targets are noted but not followed yet.

## Core books

Drop system and core books in `core/`.

- `.fbk` and `.fsk` are the standard formats.
- `.tbk` and `.sbk` are accepted for backward compatibility with existing ToolBook files.

The loader checks `core/` when a relative path is not found beside the working directory. `core/tb80r.fsk` is the reader system book.

## Formats

`.fbk` (book) and `.fsk` (system book) are the Foolbook standards. New work is authored in these.

`.tbk` and `.sbk` remain supported so existing ToolBook files still open.

The editor saves a `.json` working copy and a sibling `.fbk` on every save. The loader accepts `.json`, `.fbk`, `.fsk`, `.tbk`, and `.sbk`.

## Design notes

- The entry point stays in `foolbook/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Authoring tools stay under `author/` and are not required to view a book.
- System-book and DLL contracts stay outside until a real book needs them.
