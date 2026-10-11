# Foolbook

A modular ToolBook-compatible player.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader built to open a `.tbk` or `.sbk` and present it.

## Main focus

Load a book and run it.

```
.tbk / .sbk
    → loader
    → model (Book / Page / state)
    → engine (OpenScript)
    → viewer (CLI today, GUI later)
```

Everything else is a module that supports that path.

## Layout

```
Foolbook/
  README.md
  foolbook/
    __init__.py
    __main__.py   # main entry: python3 -m foolbook
    model.py      # Book, Page, Handler, RuntimeState
    loader.py     # .tbk / .sbk / JSON → Book
    engine.py     # OpenScript engine: handlers → actions that drive the viewer
    cli.py        # terminal viewer used by the main entry
    decoder.py    # secondary: bytecode → source (authoring / learning)
    author.py     # secondary: simple helper that uses the decoder
  examples/
    using_grok.json
```

## Modules

| Module | Role | Priority |
|--------|------|----------|
| `loader` | Read a `.tbk`, `.sbk`, or JSON shell into a `Book` | core |
| `model` | Data the rest of the system shares | core |
| `engine` | Execute OpenScript so the book itself drives navigation and behavior | core |
| `cli` | Minimal viewer that asks the engine what to do next | core (replaceable) |
| `decoder` | Turn handler bytecode into source | secondary (authoring) |
| `author` | Thin helper on top of the decoder | secondary (authoring) |

## Open Foolbook

```bash
python3 -m foolbook
python3 -m foolbook examples/using_grok.json
python3 -m foolbook path/to/book.tbk
```

That is the main entry. Everything else supports it.

## Design notes

- The engine returns actions (`goto`, `send`, `set`, `note`). It does not paint.
- A GUI can replace the CLI and call the same loader + engine.
- The decoder stays available and will be updated as we learn more, but it is not required to view a book.
- System-book and DLL contracts stay outside the core until a real book needs them.

## Next steps

1. Strengthen the loader for real `.tbk` and `.sbk` files.
2. Grow the engine only when a handler needs a new construct.
3. Point a GUI at the engine so a loaded book produces the Foolbook experience.
4. Keep the decoder and authoring helper improving in parallel, off the main path.
