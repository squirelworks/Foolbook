"""A click on a media clip plays it with the platform's own player, only for a file
under the book's folder, as one argument and never through a shell."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine import media

try:
    from engine import graphics
except ImportError:  # no Tk in this Python
    graphics = None


class _Runner:
    def __init__(self):
        self.started = []

    def __call__(self, argv):
        self.started.append(argv)


def _which(found):
    return lambda name: f"/usr/bin/{name}" if name in found else None


def _clip(src):
    return {"kind": "media", "name": "Bell", "src": src, "x": 10, "y": 10, "w": 160, "h": 40}


class Book(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = self.root / "course"
        (self.book / "sounds").mkdir(parents=True)
        (self.book / "sounds" / "bell.wav").write_bytes(b"RIFF")
        (self.root / "outside.wav").write_bytes(b"RIFF")
        self.runner = _Runner()
        self.players = media.platform_players("linux", _which({"paplay"}), self.runner)

    def tearDown(self):
        self.tmp.cleanup()

    def _click(self, src):
        shape = _clip(src)
        media.click(shape, self.book, self.players)
        return shape["note"]


class Plays(Book):
    def test_a_file_under_the_book_goes_to_the_player_as_one_argument(self):
        self.assertEqual(self._click("sounds/bell.wav"), "Playing bell.wav")
        path = str((self.book / "sounds" / "bell.wav").resolve())
        self.assertEqual(self.runner.started, [["/usr/bin/paplay", path]])

    def test_the_player_is_started_without_a_shell(self):
        with mock.patch("subprocess.Popen") as popen:
            media._start(["/usr/bin/paplay", "/b/bell.wav"])
        args, kwargs = popen.call_args
        self.assertEqual(args[0], ["/usr/bin/paplay", "/b/bell.wav"])
        self.assertFalse(kwargs.get("shell", False))

    def test_no_player_on_the_path_says_so_on_the_clip(self):
        shape = _clip("sounds/bell.wav")
        media.click(shape, self.book, media.platform_players("linux", _which(set()), self.runner))
        self.assertEqual(shape["note"], "Cannot play here: sounds/bell.wav")

    def test_a_missing_file_is_named_on_the_clip(self):
        self.assertEqual(self._click("sounds/gone.wav"), "Not found: sounds/gone.wav")
        self.assertEqual(self.runner.started, [])


class Refuses(Book):
    def _refused(self, src):
        note = self._click(src)
        self.assertTrue(note.startswith("Not played, outside the book's folder"), note)
        self.assertEqual(self.runner.started, [])

    def test_a_parent_folder_is_not_played(self):
        self._refused("../outside.wav")

    def test_an_absolute_path_is_not_played(self):
        self._refused(str(self.root / "outside.wav"))

    def test_shell_characters_are_not_played(self):
        for src in ("bell.wav; rm -rf ~", "$(whoami).wav", "`id`.wav", "a|b.wav", "a&b.wav", "a>b.wav"):
            with self.subTest(src=src):
                self._refused(src)

    @unittest.skipUnless(hasattr(os, "symlink"), "no symlinks here")
    def test_a_link_that_leads_out_of_the_book_is_not_played(self):
        try:
            (self.book / "sounds" / "out.wav").symlink_to(self.root / "outside.wav")
        except OSError:
            self.skipTest("cannot make a symlink here")
        self._refused("sounds/out.wav")

    def test_an_unsaved_book_plays_nothing(self):
        shape = _clip("sounds/bell.wav")
        media.click(shape, None, self.players)
        self.assertEqual(shape["note"], "Not beside a saved book: sounds/bell.wav")
        self.assertEqual(self.runner.started, [])


class Players(unittest.TestCase):
    def test_aplay_is_only_asked_for_a_wav(self):
        runner = _Runner()
        [aplay] = media.platform_players("linux", _which({"aplay"}), runner)
        self.assertFalse(aplay(Path("/b/song.mp3")))
        self.assertTrue(aplay(Path("/b/bell.WAV")))
        self.assertEqual(runner.started, [["/usr/bin/aplay", "/b/bell.WAV"]])

    def test_a_mac_uses_afplay(self):
        runner = _Runner()
        [afplay] = media.platform_players("darwin", _which({"afplay"}), runner)
        self.assertTrue(afplay(Path("/b/bell.aiff")))
        self.assertEqual(runner.started, [["/usr/bin/afplay", "/b/bell.aiff"]])

    def test_a_video_is_not_handed_to_an_audio_player(self):
        runner = _Runner()
        [paplay] = media.platform_players("linux", _which({"paplay"}), runner)
        self.assertFalse(paplay(Path("/b/clip.avi")))
        self.assertEqual(runner.started, [])


class _Canvas:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return len(self.calls)
        return record


@unittest.skipIf(graphics is None, "tkinter is not installed")
class Note(unittest.TestCase):
    def test_the_note_is_drawn_under_the_path(self):
        canvas = _Canvas()
        shape = dict(_clip("sounds/bell.wav"), note="Not found: sounds/bell.wav")
        graphics.draw(canvas, [shape])
        texts = [kw["text"] for name, _a, kw in canvas.calls if name == "create_text"]
        self.assertEqual(texts, ["sounds/bell.wav", "Not found: sounds/bell.wav"])


class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `media` shape and no course script plays sound
    (0 mmPlay, mmOpen or .wav lines), so no NIDA click reaches a player."""

    def test_only_a_media_shape_is_played(self):
        import inspect
        from viewer import native
        source = inspect.getsource(native)
        self.assertIn('get("kind") == "media"', source)
        self.assertEqual(source.count("media.click("), 1)


if __name__ == "__main__":
    unittest.main()
