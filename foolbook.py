#!/usr/bin/env python3
"""Launcher.

  python3 foolbook.py path/to/book.fbk     # open in the GUI
  python3 foolbook.py                      # ask for a file, then open the GUI
  python3 foolbook.py --cli path/to/book   # terminal viewer
  python3 foolbook.py --menu _courses/catalog.json
  python3 foolbook.py --catalog             # rebuild catalog
  python3 foolbook.py --author              # authoring editor
  python3 foolbook.py --debug               # files and checksums

A course module launches this with the book path so Foolbook opens
straight into that course.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from main.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
