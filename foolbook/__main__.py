"""Foolbook main entry.

  python3 -m foolbook                      # course menu
  python3 -m foolbook path/to/book.tbk     # open a book in the viewer
  python3 -m foolbook --gui path/to/book   # open a book in the GUI viewer
  python3 -m foolbook --menu catalog.json  # course menu with a catalog
  python3 -m author.gui                    # authoring editor
"""

from __future__ import annotations

import sys


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
