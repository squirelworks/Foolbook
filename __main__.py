"""Repo-root entry.

Lets `python3 -m foolbook` work when this folder is the package
(for example, the clone is named foolbook and you are in its parent).

The outer folder would otherwise shadow the real foolbook package
inside it, so it is dropped from sys.modules before the import.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
for name in list(sys.modules):
    if name == "foolbook" or name.startswith("foolbook."):
        del sys.modules[name]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from foolbook.__main__ import main

raise SystemExit(main())
