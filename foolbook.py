#!/usr/bin/env python3
"""Launcher.

  python3 foolbook.py                      # course menu
  python3 foolbook.py path/to/book.tbk     # viewer
  python3 foolbook.py --gui path/to/book   # GUI viewer
  python3 foolbook.py --menu catalog.json  # course menu
  python3 foolbook.py --author             # authoring editor
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from foolbook.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
