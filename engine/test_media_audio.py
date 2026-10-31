"""Audio plays through what the platform already has. No codec pack."""

from __future__ import annotations

import unittest
from pathlib import Path

from engine import media


class _Runner:
    def __init__(self):
        self.started = []

    def __call__(self, argv):
        self.started.append(argv)


def _which(found):
    return lambda name: f"/usr/bin/{name}" if name in found else None


class Players(unittest.TestCase):
    def test_linux_uses_the_first_player_on_the_path(self):
        runner = _Runner()
        players = media.platform_players("linux", _which({"paplay", "aplay"}), runner)
        self.assertTrue(players[0](Path("/b/bell.wav")))
        self.assertEqual(runner.started, [["/usr/bin/paplay", "/b/bell.wav"]])

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

    def test_nothing_on_the_path_is_no_player_and_the_clip_says_so(self):
        self.assertEqual(media.platform_players("linux", _which(set()), _Runner()), [])

    def test_a_video_is_not_handed_to_an_audio_player(self):
        runner = _Runner()
        [paplay] = media.platform_players("linux", _which({"paplay"}), runner)
        self.assertFalse(paplay(Path("/b/clip.avi")))
        self.assertEqual(runner.started, [])


if __name__ == "__main__":
    unittest.main()
