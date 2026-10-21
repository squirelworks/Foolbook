"""Native Foolbook window.

Opens a book in a desktop window. Exits when the window closes.
No server. No browser.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from engine.loader import load
from engine.graphics import bottom, draw, extract
from engine.place import fit_view
from engine.engine import enter_book, enter_page, follow, goto, open_book as open_other, press, run_handler
from foolbook.model import RuntimeState
from progress.progress import Progress


def _corner_stub(shape: dict, others: list[dict]) -> bool:
    """The 85 by 20 box at the corner. It repeats a button that is already on the page."""
    if (shape.get("kind") or "") != "button":
        return False
    x, y = int(shape.get("x") or 0), int(shape.get("y") or 0)
    w, h = int(shape.get("w") or 0), int(shape.get("h") or 0)
    if not (x <= 16 and y <= 16 and w <= 90 and h <= 24):
        return False
    label = (shape.get("text") or shape.get("name") or "").lower()
    return any(
        other is not shape and (other.get("kind") or "") == "button"
        and (other.get("text") or other.get("name") or "").lower() == label
        for other in others
    )


def open_book(path: str | Path, student: str = "", course: str = "", splash: bool = False) -> int:
    """Open a book in a native window. Returns when the window closes.

    splash=True only for the bare launch. Course and direct file skip it
    and open at the last page.
    """
    book = load(path)
    course_id = course or Path(path).stem
    progress = Progress(Path(student) if student else _progress_path())
    progress.touch(course_id)

    root = tk.Tk()
    root.title(book.title or Path(path).name)
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{max(800, screen_w - 24)}x{max(600, screen_h - 80)}")

    pages = book.pages
    last = progress.last_page(course_id)
    start_at = 0

    if splash:
        win = tk.Toplevel(root)
        win.title("Foolbook")
        win.geometry("480x280")
        win.transient(root)
        win.grab_set()
        tk.Label(win, text="2+2=5", font=("TkDefaultFont", 18, "bold")).pack(pady=(16, 4))
        tk.Label(win, text="Open last page? Or start fresh?").pack(pady=8)
        chosen = tk.IntVar(value=-1)

        def pick(fresh: bool):
            chosen.set(0 if fresh else 1)
            win.destroy()

        btns = ttk.Frame(win)
        btns.pack(pady=8)
        ttk.Button(btns, text="Start fresh", command=lambda: pick(True)).pack(side="left", padx=6)
        if last:
            ttk.Button(btns, text="Open last page", command=lambda: pick(False)).pack(side="left", padx=6)
        tk.Label(win, text="For greater values of 2.").pack(side="bottom", pady=8)
        root.wait_window(win)
        if chosen.get() == 1 and last:
            for i, p in enumerate(pages):
                if p.id == last:
                    start_at = i
                    break
    elif last:
        for i, p in enumerate(pages):
            if p.id == last:
                start_at = i
                break

    idx = tk.IntVar(value=start_at)
    state = RuntimeState(book=book, index=start_at)
    enter_book(state)
    state.variables.setdefault("__import", True)
    state.variables.setdefault("sysLevel", "reader")

    sidebar = ttk.Frame(root, width=160)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    held = {"course": course_id}

    def choose():
        path = filedialog.askopenfilename(
            parent=root,
            title="Open a book",
            filetypes=[
                ("Books", "*.fbk *.tbk *.json *.fsk *.sbk *.xml *.zip *.tbkx *.txt *.md *.rtf"),
                ("Notes", "*.txt *.text *.md *.markdown *.rst *.log *.rtf"),
                ("ToolBook", "*.tbk *.sbk"),
                ("TBX", "*.xml *.zip *.tbkx"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            opened = load(path)
        except Exception as exc:
            messagebox.showerror("Foolbook", str(exc), parent=root)
            return
        state.book = opened
        state.index = 0
        held["course"] = Path(path).stem
        progress.touch(held["course"])
        show(0)

    ttk.Button(sidebar, text="Open", command=choose).pack(fill="x", padx=4, pady=(4, 2))
    lb = tk.Listbox(sidebar)
    lb.pack(fill="both", expand=True)

    main = ttk.Frame(root)
    main.pack(side="left", fill="both", expand=True)
    gfx = tk.Canvas(main, highlightthickness=0, bg="white")
    gfx.pack(fill="both", expand=True)
    view = {"scale": 1.0, "ox": 0.0, "oy": 0.0, "x0": 0.0, "y0": 0.0}
    painting = {"on": False}

    def show(i: int):
        if painting["on"] or not state.book.pages:
            return
        painting["on"] = True
        try:
            state.index = max(0, min(i, len(state.book.pages) - 1))
            enter_page(state)
            _redraw()
        finally:
            painting["on"] = False
        _schedule_fit()

    def _objects(page):
        stored = list((page.raw or {}).get("objects") or [])
        if stored:
            return stored
        objects = [dict(shape) for shape in extract(page)]
        objects = [shape for shape in objects if not _corner_stub(shape, objects)]
        y = bottom(objects) + 16
        have = {
            (shape.get("text") or shape.get("name") or "").lower()
            for shape in objects
            if (shape.get("kind") or "") == "button"
        }
        for item in page.items or []:
            label = item.get("label") or item.get("page") or "Go"
            if label.lower() in have:
                continue
            have.add(label.lower())
            objects.append({
                "kind": "button", "name": label, "text": label,
                "x": 24, "y": y, "w": max(72, 10 * len(label)), "h": 28,
                "fill": "", "outline": "black", "item": item, "visible": True,
            })
            y += 36
        return objects

    def _redraw():
        pages = state.book.pages
        p = state.page
        if p is None:
            return
        progress.mark_page(held["course"], p.id)
        ids = tuple(page.id for page in pages)
        if tuple(lb.get(0, "end")) != ids:
            lb.delete(0, "end")
            for page_id in ids:
                lb.insert("end", page_id)
        idx.set(state.index)
        lb.selection_clear(0, "end")
        lb.selection_set(state.index)
        lb.see(state.index)
        root.title(state.book.title or Path(state.book.path).name)
        gfx.delete("all")
        objects = _objects(p)
        p.raw["objects"] = objects
        draw(gfx, objects, base=Path(state.book.path).parent)

    def _paint():
        _redraw()
        _schedule_fit()

    def _schedule_fit():
        pending["fit"] = True
        if pending["job"] is None:
            pending["job"] = gfx.after_idle(_apply_fit)

    def _apply_fit():
        # Drawn once the canvas has a real size, and again when that size
        # changes. A configure that arrives during the draw is remembered
        # and run once more, so the first paint cannot lock the page at
        # its raw size.
        pending["job"] = None
        if painting["on"]:
            _schedule_fit()
            return
        cw, ch = fitted["size"]
        if cw < 2 or ch < 2:
            cw, ch = gfx.winfo_width(), gfx.winfo_height()
        if cw < 2 or ch < 2:
            pending["fit"] = True
            pending["job"] = gfx.after(50, _apply_fit)
            return
        pending["fit"] = False
        painting["on"] = True
        try:
            _redraw()
            box = gfx.bbox("all")
            if not box:
                return
            scale, dx, dy, ox, oy = fit_view(box, cw, ch)
            x0, y0 = box[0], box[1]
            gfx.scale("all", x0, y0, scale, scale)
            gfx.move("all", dx, dy)
            view.update(scale=scale, ox=ox, oy=oy, x0=x0, y0=y0)
            gfx.configure(scrollregion=(0, 0, cw, ch))
        finally:
            painting["on"] = False
        if pending["fit"]:
            _schedule_fit()

    pending = {"fit": False, "job": None}
    fitted = {"size": (0, 0)}

    def _on_configure(event):
        if event.widget is not gfx:
            return
        if event.width < 2 or event.height < 2:
            return
        if fitted["size"] == (event.width, event.height):
            return
        fitted["size"] = (event.width, event.height)
        if painting["on"]:
            pending["fit"] = True
            return
        _schedule_fit()

    def _hit(event):
        page = state.page
        if page is None or view["scale"] == 0:
            return None
        x = (event.x - view["ox"]) / view["scale"] + view["x0"]
        y = (event.y - view["oy"]) / view["scale"] + view["y0"]
        for obj in reversed(page.raw.get("objects") or []):
            if obj.get("kind") != "button" or obj.get("visible") is False:
                continue
            left, top = obj.get("x") or 0, obj.get("y") or 0
            if left <= x <= left + (obj.get("w") or 0) and top <= y <= top + (obj.get("h") or 0):
                return obj
        return None

    def on_canvas(event):
        page = state.page
        obj = _hit(event)
        if page is None or obj is None:
            return
        script = obj.get("script") or ""
        if script and follow(state, run_handler(state, script)):
            show(state.index)
            return
        quiz = page.quiz or {}
        answer = quiz.get("answer") or ""
        item = obj.get("item") or {}
        name = (obj.get("name") or "").lower()
        if answer and not item.get("page") and name not in ("next", "back", "previous", "ok", "help", "skip", "menu"):
            from openscript_analysis.core.quiz import grade
            right = grade(answer, obj.get("name") or obj.get("text") or "")
            progress.record_answer(held["course"], page.id, right)
            for thing in page.raw.get("objects") or []:
                if (thing.get("name") or "").lower() == "correct":
                    thing["visible"] = right
            _paint()
            return
        if item.get("page") or item.get("book") or item.get("label"):
            on_button(item.get("label") or obj.get("text") or "", item.get("page") or "", item.get("book") or "")

    def on_button(label: str, target: str, book_name: str = ""):
        if book_name and open_other(state, book_name, target or ""):
            show(state.index)
            return
        press(state, label, target)
        show(state.index)

    gfx.bind("<Configure>", _on_configure)
    gfx.bind("<Button-1>", on_canvas)
    lb.bind("<<ListboxSelect>>", lambda e: show(lb.curselection()[0]) if lb.curselection() else None)
    show(idx.get())
    root.mainloop()
    return 0


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
