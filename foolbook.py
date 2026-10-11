#!/usr/bin/env python3
"""Launcher so both of these work from the Foolbook directory:

  python3 -m foolbook [book]
  python3 foolbook.py [book]
"""

import sys
from pathlib import Path

# Allow running from the repo root without installing the package
root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from viewer.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
