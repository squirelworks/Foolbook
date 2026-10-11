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

from viewer.cli import main as cli_main
from viewer.gui import main as gui_main

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] in ("--gui", "-g"):
        raise SystemExit(gui_main(args[1:]))
    raise SystemExit(cli_main(args))
