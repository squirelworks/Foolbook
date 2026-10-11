"""Foolbook main entry.

From the Foolbook directory:

  python3 -m foolbook path/to/book.tbk
  python3 foolbook.py path/to/book.tbk

Do not run `python3 foolbook` (that treats the package directory as a script
and loses the sibling packages).
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
        from menu.menu import main as menu_main
        return menu_main([])
    if args[0] == "--menu":
        from menu.menu import main as menu_main
        return menu_main(args[1:])
    if args[0] in ("--gui", "-g"):
        from viewer.gui import main as gui_main
        return gui_main(args[1:])
    if args[0] == "--author":
        from author.gui import main as author_main
        return author_main(args[1:])
    from viewer.cli import main as cli_main
    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
