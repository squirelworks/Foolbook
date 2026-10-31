"""Run one spec in one real viewer window. Prints one JSON result line.

    python -m tools.quiz_check.child SPEC.json COURSES_DIR SHOTS_DIR

DISPLAY must point at an X server. Nothing is written to the book or to the repository; the
progress file is redirected to a scratch folder.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
import tkinter as tk
import tkinter.messagebox as messagebox
from pathlib import Path

sys.dont_write_bytecode = True

SPEC = json.loads(Path(sys.argv[1]).read_text())
COURSES = Path(sys.argv[2])
SHOTS = Path(sys.argv[3])
SHOTS.mkdir(parents=True, exist_ok=True)

WATCH = ("__choice", "__quizPass", "__quizMode", "__quizIndex", "__quizCount", "__quizScore", "__quizNumbers",
         "__embeddedTries", "__responses", "__menuFlags", "__studentRecords", "lastpage", "nextpage")

result = {"spec": SPEC["name"], "type": SPEC.get("type", ""), "book": SPEC["book"], "steps": [],
          "errors": [], "dialogs": [], "beeps": 0, "status": "FAIL"}
for name in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askquestion",
             "askretrycancel", "askyesnocancel"):
    setattr(messagebox, name, (lambda n: lambda *a, **k: (result["dialogs"].append(
        [n, str(k.get("message") or (a[1] if len(a) > 1 else ""))[:200]]),
        "yes" if n == "askquestion" else True)[1])(name))


def book_path() -> Path:
    stem = SPEC["book"].lower()
    for item in sorted(COURSES.iterdir()):
        if item.suffix.lower() in (".tbk", ".sbk") and item.stem.lower() == stem:
            return item
    raise FileNotFoundError(f"{SPEC['book']} not in {COURSES}")


import viewer.native as native  # noqa: E402
import foolbook.model as model  # noqa: E402

scratch = tempfile.mkdtemp(prefix="quizcheck_")
native._progress_path = lambda: Path(scratch) / "progress.json"
# A spec goes to a page by its id, and the page list shows every id only to a developer.
# This is the list --debug shows, without --debug writing decoded files beside the book.
native._developer = lambda state: True

held: dict = {}
_Original = model.RuntimeState


class _State(_Original):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        held["state"] = self


native.RuntimeState = _State
_Tk_init = tk.Tk.__init__


def _tk_init(self, *a, **k):
    _Tk_init(self, *a, **k)
    held["root"] = self


tk.Tk.__init__ = _tk_init
_bind = tk.Misc.bind


def _record_bind(self, sequence=None, func=None, add=None):
    if func is not None:
        held.setdefault("binds", {})[(str(self), sequence)] = func
    return _bind(self, sequence, func, add)


tk.Misc.bind = _record_bind
_bell = tk.Misc.bell


def _count_bell(self, *a, **k):
    result["beeps"] += 1
    return _bell(self, *a, **k)


tk.Misc.bell = _count_bell
tk.Tk.report_callback_exception = lambda self, e, v, t: result["errors"].append(
    "".join(traceback.format_exception(e, v, t))[-1200:])


def walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from walk(child)


def pump(n: int = 12, pause: float = 0.04) -> None:
    root = held["root"]
    for _ in range(n):
        root.update()
        time.sleep(pause)


def find_view():
    """The viewer's page-to-window mapping, read out of the closures of its mouse bindings."""
    seen = set()

    def look(fn, depth):
        if fn is None or id(fn) in seen or depth > 3:
            return None
        seen.add(id(fn))
        for cell in getattr(fn, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, dict) and set(value) == {"scale", "ox", "oy", "x0", "y0"}:
                return value
            if callable(value):
                found = look(value, depth + 1)
                if found is not None:
                    return found
        return None

    for fn in held.get("binds", {}).values():
        found = look(fn, 0)
        if found is not None:
            return found
    return None


class Driver:
    def __init__(self):
        self.root = held["root"]
        self.state = held["state"]
        widgets = list(walk(self.root))
        self.gfx = [w for w in widgets if isinstance(w, tk.Canvas)][0]
        self.lb = [w for w in widgets if isinstance(w, tk.Listbox)][0]
        self.view = find_view()
        self.last_page = None
        self.shot_no = 0

    # --- reading -------------------------------------------------------------------------
    @property
    def page(self):
        return self.state.page

    def shape(self, name, kind=None, nth=0, visible=True):
        found = []
        for s in (self.page.shapes if self.page else None) or []:
            if (s.get("name") or "").lower() != name.lower():
                continue
            if kind == "button" and (s.get("kind") or "") not in ("button", "image"):
                continue   # a realized button is drawn from its picture, kind "image"
            if kind and kind != "button" and (s.get("kind") or "") != kind:
                continue
            if visible and s.get("visible") is False:
                continue
            found.append(s)
        return found[nth] if len(found) > nth else None

    def snapshot(self):
        st = self.state
        page = st.page
        vars_ = {}
        for key in WATCH:
            if key in st.variables:
                vars_[key] = json.loads(json.dumps(st.variables[key], default=str))
        checked = {}
        for s in (page.shapes if page else None) or []:
            if s.get("kind") != "text" and s.get("checked"):
                checked[s.get("name")] = True
        return {"page": page.id if page else None, "index": st.index, "vars": vars_, "checked": checked,
                "props": dict(((page.raw or {}).get("props") or {})) if page else {}}

    def screen_xy(self, shape):
        v = self.view
        cx = shape["x"] + shape["w"] / 2.0
        cy = shape["y"] + shape["h"] / 2.0
        x = self.gfx.winfo_rootx() + v["ox"] + (cx - v["x0"]) * v["scale"]
        y = self.gfx.winfo_rooty() + v["oy"] + (cy - v["y0"]) * v["scale"]
        return int(round(x)), int(round(y))

    # --- acting --------------------------------------------------------------------------
    def shot(self, label):
        self.shot_no += 1
        pump(4, 0.05)
        try:
            from PIL import ImageGrab
            path = SHOTS / f"{SPEC['name']}_{self.shot_no:02d}_{label}.png"
            x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).crop(
                (x, y, x + self.root.winfo_width(), y + self.root.winfo_height())).save(path)
            return str(path)
        except Exception as exc:  # a missing screenshot never fails a check
            return f"(no shot: {exc})"

    def goto(self, page_id):
        ids = [t.split()[0] for t in self.lb.get(0, "end")]
        low = [i.lower() for i in ids]
        if page_id.lower() not in low:
            raise LookupError(f"page {page_id} not in the page list")
        i = low.index(page_id.lower())
        self.lb.selection_clear(0, "end")
        self.lb.selection_set(i)
        self.lb.see(i)
        self.lb.event_generate("<<ListboxSelect>>")
        pump()

    def click(self, name, kind=None, nth=0):
        shape = self.shape(name, kind, nth)
        if shape is None:
            raise LookupError(f"no visible object {name!r} on {self.page.id}")
        x, y = self.screen_xy(shape)
        from engine.place import shapes_at
        v = self.view
        px = (x - self.gfx.winfo_rootx() - v["ox"]) / v["scale"] + v["x0"]
        py = (y - self.gfx.winfo_rooty() - v["oy"]) / v["scale"] + v["y0"]
        top = (shapes_at(list(self.page.raw.get("objects") or self.page.shapes), px, py) or [None])[0]
        result.setdefault("hits", []).append(
            [name, (top or {}).get("name"), (top or {}).get("kind"), [round(px), round(py)]])
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=True)
        pump(14)

    def dblclick(self, name, kind=None, nth=0):
        shape = self.shape(name, kind, nth)
        if shape is None:
            raise LookupError(f"no visible object {name!r} on {self.page.id}")
        x, y = self.screen_xy(shape)
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "--repeat", "2", "--delay", "80", "1"], check=True)
        pump(16)

    def click_xy(self, px, py):
        v = self.view
        x = self.gfx.winfo_rootx() + v["ox"] + (px - v["x0"]) * v["scale"]
        y = self.gfx.winfo_rooty() + v["oy"] + (py - v["y0"]) * v["scale"]
        subprocess.run(["xdotool", "mousemove", str(int(x)), str(int(y)), "click", "1"], check=True)
        pump(14)

    def focus_window(self):
        self.root.focus_force()
        self.gfx.focus_force()
        x = self.gfx.winfo_rootx() + 5
        y = self.gfx.winfo_rooty() + 5
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=True)
        pump(4)

    def type(self, text):
        self.focus_window_keep()
        subprocess.run(["xdotool", "type", "--delay", "60", text], check=True)
        pump(10)

    def focus_window_keep(self):
        # keep the pointer where it is (a click may have focused a field); only make sure Tk has the keys
        (self.root.focus_get() or self.gfx).focus_force()
        pump(2)

    def key(self, keysym):
        self.focus_window_keep()
        subprocess.run(["xdotool", "key", keysym], check=True)
        pump(14)

    # --- asserting -----------------------------------------------------------------------
    def check(self, expect, before):
        snap = self.snapshot()
        fails = []

        def want(label, ok, got):
            if not ok:
                fails.append(f"{label}: got {got!r}")

        for key, value in expect.items():
            if key == "page":
                want(f"page == {value}", (snap["page"] or "").lower() == value.lower(), snap["page"])
            elif key == "page_in":
                want(f"page in {value}", (snap["page"] or "").lower() in [v.lower() for v in value], snap["page"])
            elif key == "page_not":
                want(f"page != {value}", (snap["page"] or "").lower() != value.lower(), snap["page"])
            elif key == "moved":
                moved = snap["page"] != before["page"]
                want(f"moved == {value}", moved == value, f"{before['page']} -> {snap['page']}")
            elif key == "checked":
                for name, flag in value.items():
                    s = self.shape(name, "button", visible=False)
                    want(f"checked {name} == {flag}", bool(s and s.get("checked")) == flag, bool(s and s.get("checked")))
            elif key == "visible":
                for name, flag in value.items():
                    s = self.shape(name, visible=False)
                    want(f"visible {name} == {flag}", bool(s and s.get("visible") is not False) == flag,
                         None if s is None else s.get("visible"))
            elif key == "hidden":
                for name, flag in value.items():
                    s = self.shape(name, visible=False)
                    want(f"{name} is loaded and hidden == {flag}", bool(s is not None and s.get("visible") is False) == flag,
                         None if s is None else s.get("visible"))
            elif key == "group_visible":
                for name, flag in value.items():
                    mem = [x for x in (self.page.shapes or [])
                           if any((g or "").lower() == name.lower() for g in x.get("groups") or ())]
                    shown = [x.get("visible") is not False for x in mem]
                    want(f"group {name} members == {len(mem) or '>=1'}", bool(mem), len(mem))
                    want(f"group {name} visible == {flag}", bool(mem) and all(v == flag for v in shown), shown)
            elif key == "text":
                for name, text in value.items():
                    s = self.shape(name, "text", visible=False)
                    got = (s or {}).get("text")
                    want(f"text {name} == {text!r}", got == text, got)
            elif key == "text_contains":
                for name, text in value.items():
                    s = self.shape(name, "text", visible=False)
                    got = (s or {}).get("text") or ""
                    want(f"text {name} contains {text!r}", text.lower() in got.lower(), got)
            elif key == "var":
                for name, expected in value.items():
                    got = self.state.variables.get(name)
                    want(f"var {name} == {expected!r}", got == expected, got)
            elif key == "var_ops":
                for name, op, expected in value:
                    got = self.state.variables.get(name)
                    try:
                        ok = {">=": got >= expected, ">": got > expected, "<=": got <= expected,
                              "<": got < expected, "!=": got != expected, "==": got == expected}[op]
                    except TypeError:
                        ok = False
                    want(f"var {name} {op} {expected!r}", ok, got)
            elif key == "last_score":
                rec = (self.state.variables.get("__responses") or [None])[-1]
                got = (rec or {}).get("score")
                want(f"last recorded score == {value}", got == value, got)
            elif key == "has_prop":
                want(f"page has property {value}", value in snap["props"], list(snap["props"]))
            elif key == "beeps_since":
                want(f"beeps since last step == {value}", result["beeps"] - before["beeps"] == value,
                     result["beeps"] - before["beeps"])
            elif key == "field_text_changed":
                s = self.shape(value, "text", visible=False)
                want(f"field {value} text changed", (s or {}).get("text") != before.get("text_" + value), (s or {}).get("text"))
            elif key == "no_dialog":
                want("no dialog", not result["dialogs"], result["dialogs"])
            else:
                fails.append(f"unknown expectation {key}")
        return fails, snap


def run_steps():
    d = Driver()
    d.root.geometry("1100x800+0+0")
    pump(10)
    d.root.focus_force()
    for number, step in enumerate(SPEC["steps"], 1):
        before = d.snapshot()
        before["beeps"] = result["beeps"]
        for name in d_names(d):
            before["text_" + name] = (d.shape(name, "text", visible=False) or {}).get("text")
        row = {"n": number, "step": step, "page_before": before["page"]}
        try:
            if "goto" in step:
                d.goto(step["goto"])
            elif "click" in step:
                d.click(step["click"], step.get("kind"), step.get("nth", 0))
            elif "answer" in step:
                # click the letter this question's own Answer property names (right) or any other one (wrong)
                right = str(((d.page.raw or {}).get("props") or {}).get("Answer") or "").upper()
                letters = [n for n in "ABCDE" if d.shape(n, "button")]
                pick = right if step["answer"] in (True, "right") else next((n for n in letters if n != right), right)
                row["picked"] = pick
                d.click(pick, "button")
            elif "dblclick" in step:
                d.dblclick(step["dblclick"], step.get("kind"), step.get("nth", 0))
            elif "click_xy" in step:
                d.click_xy(*step["click_xy"])
            elif "type" in step:
                d.type(step["type"])
            elif "key" in step:
                for k in (step["key"] if isinstance(step["key"], list) else [step["key"]]):
                    d.key(k)
            elif "set" in step:
                d.state.variables.update(step["set"])
            elif "wait" in step:
                pump(int(step["wait"] * 20), 0.05)
            elif "shot" in step:
                row["shot"] = d.shot(step["shot"])
            if "expect" in step:
                fails, snap = d.check(step["expect"], before)
                row["fails"] = fails
            else:
                snap = d.snapshot()
            row["page_after"] = snap["page"]
            row["vars"] = snap["vars"]
            row["checked"] = sorted(snap["checked"])
            if step.get("shot_after"):
                row["shot"] = d.shot(step["shot_after"])
        except Exception as exc:
            row["fails"] = [f"step error: {exc!r}"]
            row["shot"] = d.shot("error")
        result["steps"].append(row)
        if row.get("fails") and step.get("stop", True):
            break
    if SPEC.get("final_shot", True):
        result["final_shot"] = d.shot("final")


def d_names(d):
    return SPEC.get("watch_text", [])


def main():
    path = book_path()

    def mainloop(self, n=0):
        try:
            run_steps()
        except BaseException:
            result["errors"].append(traceback.format_exc()[-1500:])
        finally:
            ok = (not result["errors"]) and result["steps"] and all(not r.get("fails") for r in result["steps"]) \
                and len(result["steps"]) == len(SPEC["steps"])
            result["status"] = "PASS" if ok else "FAIL"
            try:
                self.destroy()
            except tk.TclError:
                pass

    tk.Tk.mainloop = mainloop
    native.open_book(str(path))
    print("RESULT " + json.dumps(result, default=str), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        result["errors"].append(traceback.format_exc()[-1500:])
        print("RESULT " + json.dumps(result, default=str), flush=True)
