"""Foolbook main entry.

Open Foolbook and optionally load a book:

  python3 -m foolbook
  python3 -m foolbook path/to/book.tbk
  python3 -m foolbook examples/using_grok.json

Supporting modules (loader, engine, model, decoder, author) sit behind this.
"""

from __future__ import annotations

import sys

from viewer.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
