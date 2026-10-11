"""Foolbook main entry.

Foolbook is the tool that opens a book. A course module (or Foolcourse)
can launch it with a path; if none is given, Foolbook asks for one.

  python3 -m foolbook path/to/book.fbk     # open that book in the GUI
  python3 -m foolbook                      # ask for a file, then open the GUI
  python3 -m foolbook --cli path/to/book   # terminal viewer
  python3 -m foolbook --catalog            # rebuild _courses/catalog.json
  python3 -m foolbook --debug              # files and checksums
  python3 -m foolbook --debug book.tbk     # keep decoded source
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the Foolbook root is on the path so viewer/, engine/, menu/, author/
# resolve even if this file is launched as a script.
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def main() -> int:
    args = sys.argv[1:]
    bin_path = _take_bin(args)
    if bin_path:
        from engine.loader import set_keyword_bin
        set_keyword_bin(bin_path)
    debug_mode = _take_debug(args)
    if debug_mode is not None and not args:
        from _debug.debug import main as debug_main
        return debug_main([debug_mode] if debug_mode else [])
    if debug_mode is not None:
        from engine.loader import set_keep_decoded
        set_keep_decoded(True)
    if not args:
        path = _ask_for_book()
        if not path:
            return 0
        args = [path]
    if args[0] == "--menu":
        from menu.menu import main as menu_main
        return menu_main(args[1:])
    if args[0] == "--cli":
        from viewer.cli import main as cli_main
        return cli_main(args[1:])
    if args[0] in ("--gui", "-g"):
        args = args[1:]
    if args and args[0] == "--catalog":
        from _courses.catalog import main as catalog_main
        return catalog_main(args[1:])
    if args and args[0] == "--author":
        from author.gui import main as author_main
        return author_main(args[1:])
    from viewer.gui import main as gui_main
    return gui_main(args)


def _take_debug(args: list[str]) -> str | None:
    """Pull --debug [mode] out of argv.

    Returns None if --debug was not given, '' for a bare --debug, or the mode.
    A mode that is a book path is left in argv so the book still opens.
    """
    if "--debug" not in args:
        return None
    i = args.index("--debug")
    mode = ""
    if i + 1 < len(args) and not args[i + 1].startswith("-"):
        nxt = args[i + 1]
        if not Path(nxt).exists() and not nxt.lower().endswith((".tbk", ".sbk", ".fbk", ".fsk", ".json")):
            mode = nxt
            del args[i + 1]
    del args[i]
    return mode


def _take_bin(args: list[str]) -> str:
    """Pull --bin PATH out of argv. Returns the path or ''."""
    if "--bin" not in args:
        return ""
    i = args.index("--bin")
    if i + 1 >= len(args):
        print("--bin needs a path")
        raise SystemExit(2)
    path = args[i + 1]
    del args[i:i + 2]
    return path


def _ask_for_book() -> str:
    """Prompt for a book path when none was passed in.

    Loops until a real file is given or the line is empty.
    Expands ~ and accepts either slash.
    """
    print("Foolbook")
    print("Open a book. Pass a path, or type one now.")
    print("  .fbk / .tbk   book")
    print("  .fsk / .sbk   system book")
    print("  (empty to quit)")
    while True:
        try:
            raw = input("book> ").strip().strip('"').strip("'")
        except (EOFError, KeyboardInterrupt):
            print()
            return ""
        if not raw:
            return ""
        path = Path(raw.replace("\\", "/")).expanduser()
        if path.exists():
            return str(path)
        print(f"not found: {path}")
        print(f"  looked in {path.resolve()}")
        print("  try again, or empty to quit")


if __name__ == "__main__":
    raise SystemExit(main())
