# Foolbook

A modular ToolBook-compatible player.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader built to open a `.tbk` or `.sbk` and present it.

## Main focus

Open Foolbook and feed it a book. The engine parses the file, interprets it, and drives the viewer.

```
python3 -m foolbook [book]
    → foolbook (entry)
    → engine (parse .tbk/.sbk, interpret OpenScript)
    → viewer (display)
```

Recovering the NIDA ToolBook environment (and the older ToolBook environment in general) means improving the engine’s ability to read those files and feed the result into the viewer.

## Layout

```
Foolbook/
  README.md
  foolbook/                 # the thing you open
    __init__.py
    __main__.py             # python3 -m foolbook
    model.py                # Book, Page, RuntimeState
  engine/                   # parse and interpret; feeds the viewer
    __init__.py
    loader.py               # .tbk / .sbk / JSON → Book
    engine.py               # OpenScript engine
  viewer/                   # display what the engine produces
    __init__.py
    cli.py                  # terminal viewer
    gui.py                  # browser GUI
  author/                   # secondary authoring / learning
    __init__.py
    decoder.py              # bytecode → source
    author.py               # helper on the decoder
  examples/
    using_grok.json
```

## Open Foolbook

```bash
python3 -m foolbook
python3 -m foolbook examples/using_grok.json
python3 -m foolbook path/to/book.tbk

# GUI
python3 -m foolbook --gui path/to/book.tbk
python3 foolbook.py --gui path/to/book.tbk
```

## Design notes

- The entry point stays in `foolbook/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- The viewer displays what the engine produces.
- Authoring tools stay under `author/` and are not required to view a book.
- System-book and DLL contracts stay outside until a real book needs them.
