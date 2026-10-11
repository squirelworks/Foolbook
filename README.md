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

The menu lists courses by subject, module, and course. Selecting one opens it in the viewer. Progression (opened / started / done) is stored by the progress module and will grow as page tracking is wired in.

## Authoring formats

The goal is to author original `.tbk` files. Until that format is ready:

- `.json` is the working copy (default).
- `.fbk` is written beside it. It is a Foolbook book and will become a `.tbk`.
- `.fsk` is a Foolbook system book and will become a `.sbk`.

The editor saves both `.json` and `.fbk` on every save. The loader accepts all three.

## Design notes

- The entry point stays in `foolbook/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Authoring tools stay under `author/` and are not required to view a book.
- System-book and DLL contracts stay outside until a real book needs them.
