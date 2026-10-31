"""What an editable install writes into the checkout is not committed."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("git") and (ROOT / ".git").exists(), "needs a git checkout")
class IgnoredFilesTests(unittest.TestCase):
    def test_egg_info_is_ignored(self):
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "foolbook.egg-info/PKG-INFO"],
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
