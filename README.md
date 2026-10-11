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
  README.md
  foolbook/                 # the thing you open
    __init__.py
    __main__.py             # python3 -m foolbook
    cli.py                  # terminal viewer
    model.py                # Book, Page, RuntimeState
  engine/                   # parse and interpret; feeds Foolbook
    __init__.py
    loader.py               # .tbk / .sbk / JSON → Book
    engine.py               # OpenScript engine
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
```

## Design notes

- The entry point stays in `foolbook/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Authoring tools stay under `author/` and are not required to view a book.
- System-book and DLL contracts stay outside until a real book needs them.
