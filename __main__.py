"""Repo-root entry.

Lets ``python3 foolbook.py`` and ``python3 -m foolbook`` from this folder
open a book. The program itself is foolbook/__main__.py.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from foolbook.__main__ import main

raise SystemExit(main())
