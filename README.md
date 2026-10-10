# Foolbook

A modular, incrementally improvable ToolBook-compatible player.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader and interpreter built from reverse-engineering work on ToolBook II 8.x books.

## Goals

- Load a `.tbk` and walk its pages.
- Decode OpenScript bytecode into source.
- Execute the common navigation and conditional patterns so a viewer can be driven by the book itself.
- Stay small and replaceable: each module has a narrow job and can be improved independently.

## Layout

```
Foolbook/
  README.md
  foolbook/
    __init__.py
    model.py        # Book, Page, Handler, RuntimeState
    loader.py       # .tbk → Book (uses runtime.tbk when available)
    decoder.py      # bytecode → source (wraps openscript_decode)
    interpreter.py  # source → actions (go, send, assign, if)
    cli.py          # simple command-line walker
  examples/
    using_grok.json # sample book in the internal format
```

## Modules

| Module | Responsibility | Status |
|--------|----------------|--------|
| `model` | Data classes for books, pages, handlers, and runtime state | scaffold |
| `loader` | Read a `.tbk` (or a JSON shell) into a `Book` | scaffold (delegates) |
| `decoder` | Turn handler bytecode into source text | scaffold (delegates) |
| `interpreter` | Execute a small OpenScript subset and return actions | scaffold |
| `cli` | Walk a book from the terminal | scaffold |

## Usage (once filled in)

```bash
cd Foolbook
python3 -m foolbook.cli path/to/book.tbk
python3 -m foolbook.cli examples/using_grok.json
```

## Design notes

- The interpreter does not paint. It only mutates state and yields actions (`goto`, `send`, `set`, `note`).
- A GUI (Brickwall or otherwise) can sit on top and ask the interpreter what to do next.
- New language features are added only when a real handler needs them.
- System-book and DLL contracts (`nc81int`, `nc81rec`) stay outside the core until required.

## Next steps

1. Wire `loader` fully to the existing `runtime.tbk` parser.
2. Wire `decoder` to `openscript_decode.py` + `res_77.bin`.
3. Implement the interpreter subset: `go to page`, `send`, simple `if`, assignments.
4. Point the Brickwall GUI at Foolbook’s interpreter instead of pre-translated JSON.
