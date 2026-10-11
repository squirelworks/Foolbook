"""Foolbook main entry.

Open Foolbook and optionally load a book:

  python3 -m foolbook
  python3 -m foolbook path/to/book.tbk
  python3 -m foolbook examples/using_grok.json

Supporting modules (loader, engine, model, decoder, author) sit behind this.
"""

from __future__ import annotations

import sys

from viewer.cli import main as cli_main
from viewer.gui import main as gui_main


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ("--gui", "-g"):
        raise SystemExit(gui_main(args[1:]))
    raise SystemExit(cli_main(args))
