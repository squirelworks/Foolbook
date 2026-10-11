"""Foolbook main entry.

Foolbook is the tool that opens a book. A course module (or Foolcourse)
can launch it with a path; if none is given, Foolbook asks for one.

  python3 -m foolbook path/to/book.fbk     # open that book
  python3 -m foolbook path/to/book.tbk     # open a ToolBook book
  python3 -m foolbook                      # ask for a file
  python3 -m foolbook --gui path/to/book   # GUI viewer
  python3 -m foolbook --debug              # files and checksums
  python3 -m foolbook --debug complete     # full check
  python3 -m foolbook --debug engine       # one module
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
    if not args:
        path = _ask_for_book()
        if not path:
            return 0
        args = [path]
    if args[0] == "--menu":
        from menu.menu import main as menu_main
        return menu_main(args[1:])
    if args[0] in ("--gui", "-g"):
        from viewer.gui import main as gui_main
        return gui_main(args[1:])
    if args[0] == "--debug":
        from _debug.debug import main as debug_main
        return debug_main(args[1:])
    if args[0] == "--author":
        from author.gui import main as author_main
        return author_main(args[1:])
    from viewer.cli import main as cli_main
    return cli_main(args)


def _ask_for_book() -> str:
    """Prompt for a book path when none was passed in."""
    print("Foolbook")
    print("Open a book. Pass a path, or type one now.")
    print("  .fbk / .tbk   book")
    print("  .fsk / .sbk   system book")
    print("  (empty to quit)")
    try:
        path = input("book> ").strip().strip('"').strip("'")
    except (EOFError, KeyboardInterrupt):
        print()
        return ""
    if not path:
        return ""
    if not Path(path).exists():
        print(f"not found: {path}")
        return ""
    return path


if __name__ == "__main__":
    raise SystemExit(main())
