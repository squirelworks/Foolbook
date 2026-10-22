"""The window follows the pages that were entered, not the Next chain."""

import unittest

from engine.window import arrive, visible


def _paper():
    return [
        {"kind": "rect", "x": 0, "y": 0, "w": 624, "h": 442, "fill": "#0000bf"},
        {"kind": "text", "text": "74LS174N", "direct": False},
        {"kind": "text", "text": "Digital Circuit", "direct": True},
    ]


def _overlay(keep, drop):
    return [
        {"kind": "rect", "x": 0, "y": 0, "w": 624, "h": 442, "fill": ""},
        {"kind": "text", "text": keep, "direct": False},
        {"kind": "text", "text": drop, "direct": True},
    ]


class WindowTests(unittest.TestCase):
    def test_a_filled_page_replaces_the_window(self):
        window = arrive([], 0, _paper())
        window = arrive(window, 1, _overlay("MM54240", "TMS"))
        window = arrive(window, 0, _paper())
        self.assertEqual([item["text"] for item in visible(window) if item.get("text")],
                         ["74LS174N", "Digital Circuit"])

    def test_an_overlay_keeps_what_was_entered_and_drops_direct(self):
        window = arrive([], 0, _paper())
        window = arrive(window, 1, _overlay("MM54240", "TMS"))
        window = arrive(window, 2, _overlay("10V", "flames"))
        text = [item["text"] for item in visible(window) if item.get("text")]
        self.assertEqual(text, ["74LS174N", "MM54240", "10V", "flames"])

    def test_a_cold_jump_does_not_invent_the_next_chain(self):
        window = arrive([], 2, _overlay("10V", "flames"))
        text = [item["text"] for item in visible(window) if item.get("text")]
        self.assertEqual(text, ["10V", "flames"])
