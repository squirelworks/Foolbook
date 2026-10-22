"""The window follows the pages that were entered, not the Next chain."""

import unittest

from engine.window import arrive, show_page_number, visible


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

    def test_page_number_is_the_page_now_open(self):
        shapes = [{"name": "Page#", "text": "P1270"}, {"name": "title", "text": "INTRODUCTION"}]
        show_page_number(shapes, "P400")
        self.assertEqual(shapes[0]["text"], "P400")
        self.assertEqual(shapes[1]["text"], "INTRODUCTION")


class DrawOrderTests(unittest.TestCase):
    def test_a_frame_stays_behind_the_bar_it_holds(self):
        from engine.place import in_front, tighten
        shapes = [
            {"kind": "image", "name": "bar", "x": 100, "y": 80, "w": 200, "h": 30},
            {"kind": "image", "name": "frame", "x": 10, "y": 10, "w": 400, "h": 300},
            {"kind": "text", "name": "label", "x": 110, "y": 84, "w": 180, "h": 20},
        ]
        names = [shape["name"] for shape in in_front(shapes)]
        self.assertEqual(names, ["frame", "bar", "label"])
        self.assertEqual(tighten("all            rights"), "all rights")
