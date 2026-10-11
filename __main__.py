"""Repo-root entry.

Lets `python3 -m foolbook` work when this folder is the package
(for example, the clone is named foolbook and you are in its parent).
"""

import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

inner = root / "foolbook" / "__main__.py"
spec = importlib.util.spec_from_file_location("foolbook_entry", inner)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
raise SystemExit(mod.main())
