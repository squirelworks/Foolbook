"""The reader does not install the editor's packages.

FoolbookEditor owns ``author`` and ``foolbookeditor``. When the reader
installed packages of the same names, whichever was found first won.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_pyproject_does_not_package_the_editor(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        found = re.search(r"^include\s*=\s*\[(.*?)\]", text, re.M | re.S)
        self.assertIsNotNone(found)
        names = re.findall(r'"([^"]+)"', found.group(1))
        self.assertNotIn("author*", names)
        self.assertNotIn("foolbookeditor*", names)

    def test_no_editor_package_in_the_reader(self):
        self.assertFalse((ROOT / "foolbookeditor").exists())
        self.assertFalse((ROOT / "author").exists())


if __name__ == "__main__":
    unittest.main()
