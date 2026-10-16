"""Modules are the ToolBook split. W64 is a scaffold, not an image."""

from __future__ import annotations

import unittest

from modules.arch import plan
from modules.host import load


class Modules(unittest.TestCase):
    def test_the_16_bit_image_is_not_the_64_bit_slot(self):
        old = plan("i86", "windows")
        self.assertEqual(old["thunk"], "w16")
        self.assertIn("bas", old["native"])
        self.assertNotIn("w64", old["native"])
        self.assertEqual(load("bas").IMAGE, "TB80BAS.DLL")
        self.assertIsNone(load("w64").IMAGE)
        self.assertEqual(load("w64").open()["body"], "scaffold")
        self.assertFalse(load("rcr").open()["classified"])

    def test_later_hosts_run_the_models_and_not_the_ne_image(self):
        for chip, host in (("arm64", "ios"), ("arm64", "android"), ("arm64", "macos"), ("x86_64", "macos")):
            got = plan(chip, host)
            self.assertEqual(got["native"], [])
            self.assertEqual(got["thunk"], "w64")
            self.assertIn("bas", got["models"])
        with self.assertRaises(ValueError):
            plan("i86", "ios")

    def test_one_module_reloads_without_the_others(self):
        bas = load("bas")
        w64 = load("w64")
        bas._sentinel = 1
        w64._sentinel = 2
        load("bas", refresh=True)
        self.assertFalse(hasattr(load("bas"), "_sentinel"))
        self.assertEqual(load("w64")._sentinel, 2)
        self.assertIn("heap", load("bas").open())

    def test_the_shell_names_its_windows(self):
        from modules.rtm import GROUPS, which
        self.assertEqual(which("MAINWNDPROC"), "window")
        self.assertEqual(which("SEARCHDIALOGPROC"), "find")
        self.assertEqual(which("BOOKQUERYSAVE"), "book")
        self.assertEqual(len(GROUPS), 43)
        self.assertIsNone(which("NOPE"))


if __name__ == "__main__":
    unittest.main()
