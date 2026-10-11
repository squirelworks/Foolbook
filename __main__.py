"""Repo-root entry.

Lets `python3 -m foolbook` work when this folder is the package.
The real package is main/.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from main.__main__ import main

raise SystemExit(main())
