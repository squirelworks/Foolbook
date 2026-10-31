"""quiz_check goes to a page by its id, so its page list shows every id.

The NIDA guard runs when FOOLBOOK_COURSES names a folder holding 93950103.tbk.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(code: str, spec: dict, courses: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "spec.json"
        spec_path.write_text(json.dumps(spec))
        argv = [str(spec_path), courses, str(Path(tmp) / "shots")]
        return subprocess.run([sys.executable, "-c", code, *argv], cwd=ROOT, capture_output=True,
                              text=True, timeout=300)


class PageListTests(unittest.TestCase):
    def test_the_child_lists_every_page_id_for_a_reader(self):
        try:
            import tkinter  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("no tkinter")
        code = ("import sys; sys.argv = ['child'] + sys.argv[1:]\n"
                "import tools.quiz_check.child\n"
                "import viewer.native as native\n"
                "from foolbook.model import Book, RuntimeState\n"
                "state = RuntimeState(book=Book(path='', title='t'))\n"
                "state.variables['sysLevel'] = 'reader'\n"
                "print('DEV', native._developer(state))\n")
        p = _run(code, {"name": "ids", "book": "none", "steps": []}, tempfile.gettempdir())
        self.assertIn("DEV True", p.stdout, p.stderr[-800:])


class NidaGotoTests(unittest.TestCase):
    def test_a_goto_step_finds_its_page(self):
        courses = os.environ.get("FOOLBOOK_COURSES")
        if not courses or not any(p.name.lower() == "93950103.tbk" for p in Path(courses).iterdir()):
            raise unittest.SkipTest("93950103.tbk is not here; set FOOLBOOK_COURSES")
        if not os.environ.get("DISPLAY") or shutil.which("xdotool") is None:
            raise unittest.SkipTest("needs a display and xdotool")
        spec = {"name": "goto_ids", "book": "93950103",
                "steps": [{"goto": "P1090", "expect": {"page": "P1090"}}]}
        code = "import sys, runpy; runpy.run_module('tools.quiz_check.child', run_name='__main__')"
        p = _run(code, spec, courses)
        line = [x for x in p.stdout.splitlines() if x.startswith("RESULT ")]
        self.assertTrue(line, p.stderr[-800:])
        result = json.loads(line[-1][len("RESULT "):])
        self.assertEqual(result["status"], "PASS", json.dumps(result)[-1200:])


if __name__ == "__main__":
    unittest.main()
