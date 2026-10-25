"""Native Foolbook window.

Opens a book in a desktop window. Exits when the window closes.
No server. No browser.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from engine.loader import load, realize
from engine.preload import start as open_ahead, stop as stop_ahead
from engine.graphics import bottom, draw, extract
from engine.place import fit_view, page_box, place_window, click_target, shapes_at, blank_book_lines, opening_size
from engine.engine import enter_book, enter_page, follow, goto, leave_page, open_book as open_other, press, run_handler, run_page_handlers, click_script, one_handler
from engine import fields
from engine.window import arrive, visible
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

    splash=True only for the bare launch, which can reopen the last page.
    A book passed on the command line starts at the first page.
    """
    book = load(path)
    open_ahead(book)
    course_id = course or Path(path).stem
    progress = Progress(Path(student) if student else _progress_path())
    progress.touch(course_id)

    root = tk.Tk()
    root.title(book.title or Path(path).name)
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w, win_h = opening_size(screen_w, screen_h, _saved_window())
    root.geometry(f"{win_w}x{win_h}")
    root.minsize(640, 480)

    def _keep_window(event=None):
        if event is not None and event.widget is not root:
            return
        width, height = root.winfo_width(), root.winfo_height()
        if width < 400 or height < 300:
            return
        try:
            _window_path().write_text(json.dumps({"w": width, "h": height}))
        except OSError:
            pass

    root.bind("<Configure>", _keep_window)

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

    idx = tk.IntVar(value=start_at)
    state = RuntimeState(book=book, index=start_at)
    state.ask = lambda text: "Yes" if messagebox.askyesno("Foolbook", text, parent=root) else "No"
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
        held["pile"] = []
        held["piles"] = {}
        progress.touch(held["course"])
        open_ahead(opened)
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
            nxt = max(0, min(i, len(state.book.pages) - 1))
            if nxt != state.index:
                leave_page(state)
            state.index = nxt
            enter_page(state)
        finally:
            painting["on"] = False
        root.update_idletasks()
        fitted["size"] = (gfx.winfo_width(), gfx.winfo_height())
        _apply_fit()

    def _objects(page):
        stored = list((page.raw or {}).get("objects") or [])
        if stored:
            return stored
        objects = list(extract(page))
        objects = [shape for shape in objects if not _corner_stub(shape, objects)]
        y = bottom(objects) + 16
        named = {(shape.get("name") or "").lower() for shape in objects}
        have = {
            (shape.get("text") or shape.get("name") or "").lower()
            for shape in objects
            if (shape.get("kind") or "") in ("button", "image")
        }
        for item in page.items or []:
            label = item.get("label") or item.get("page") or "Go"
            if label.lower() in have or label.lower() in named:
                continue
            have.add(label.lower())
            objects.append({
                "kind": "button", "name": label, "text": label,
                "x": 24, "y": y, "w": max(72, 10 * len(label)), "h": 28,
                "fill": "", "outline": "black", "item": item, "visible": True,
            })
            y += 36
        if not objects:
            name = ""
            if state.book is not None and state.book.path:
                name = Path(state.book.path).name
            objects.extend(blank_book_lines(getattr(page, "text", None), name))
        return objects

    def _redraw(window=None):
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
        held["lock"] = True
        try:
            lb.selection_clear(0, "end")
            lb.selection_set(state.index)
            lb.see(state.index)
        finally:
            held["lock"] = False
        root.title(state.book.title or Path(state.book.path).name)
        gfx.delete("all")
        objects = _objects(p)
        realize(state.book.path, objects)
        p.raw["objects"] = objects
        pile = held.setdefault("piles", {}).setdefault(state.book.path, [])
        arrive(pile, state.index, objects)
        shown = visible(pile)
        if window is not None:
            scale, x0, y0, dx, dy = window
            shown = place_window(shown, scale, x0, y0, dx, dy)
        base = Path(state.book.path).parent
        draw(gfx, shown, base=base)

    def _paint():
        # One draw, at the size already fitted. Drawing the raw page and
        # then fitting it again is the flash on a click.
        scale = view.get("scale") or 0
        if scale:
            _redraw((scale, view["x0"], view["y0"], view["ox"] - view["x0"], view["oy"] - view["y0"]))
            return
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
            page = state.page
            if page is None:
                return
            objects = _objects(page)
            pile = held.setdefault("piles", {}).setdefault(state.book.path, [])
            arrive(pile, state.index, objects)
            box = page_box(page, visible(pile))
            scale, dx, dy, ox, oy = fit_view(box, cw, ch)
            x0, y0 = box[0], box[1]
            _redraw((scale, x0, y0, dx, dy))
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

    def _page_xy(event):
        if view["scale"] == 0:
            return None
        return (
            (event.x - view["ox"]) / view["scale"] + view["x0"],
            (event.y - view["oy"]) / view["scale"] + view["y0"],
        )

    def _run_named(obj, name: str) -> None:
        if not obj:
            return
        body = one_handler(obj.get("script") or "", name)
        if body:
            run_handler(state, body)

    def on_press(event):
        page = state.page
        point = _page_xy(event)
        if page is None or point is None:
            return
        x, y = point
        found = shapes_at(_objects(page), x, y)
        top = found[0] if found else None
        target = click_target(_objects(page), x, y)
        held["press"] = (top, target)
        # The canvas has the keyboard after any click, so a key reaches on_key.
        gfx.focus_set()
        if fields.is_field(top):
            fields.focus(state, top)
        elif fields.focused(state) is not None:
            fields.blur(state)
        seen = set()
        for item in (top, target):
            if item is None or id(item) in seen:
                continue
            seen.add(id(item))
            _run_named(item, "buttonDown")
        if state.variables.get("__redraw"):
            _paint()

    def on_release(event):
        page = state.page
        top, target = held.get("press") or (None, None)
        held["press"] = None
        if page is None:
            return
        seen = set()
        for item in (top, target):
            if item is None or id(item) in seen:
                continue
            seen.add(id(item))
            _run_named(item, "buttonUp")
        point = _page_xy(event)
        still = shapes_at(_objects(page), *point) if point else []
        if target is None or target not in still:
            if state.variables.pop("__redraw", None):
                _paint()
            return
        _activate(target)
        if state.variables.pop("__beep", None):
            try:
                root.bell()
            except tk.TclError:
                pass

    def on_key(event):
        # A typed key goes to the field that was clicked, or to the quiz question on the page.
        if not fields.handle_key(state, event.keysym, event.char):
            # Not a field: the book's keyChar passes it to handleQuizKey.
            from engine.quiz import key_letter, ok_button
            if event.keysym in ("Return", "KP_Enter"):
                # keyEnter: send buttonClick to button "OK" of the page.
                ok = ok_button(state)
                if ok is None:
                    return None
                _activate(ok)
                if state.variables.pop("__beep", None):
                    try:
                        root.bell()
                    except tk.TclError:
                        pass
                return "break"
            if not (event.char and key_letter(state, event.char)):
                return None
        if state.variables.pop("__beep", None):
            try:
                root.bell()
            except tk.TclError:
                pass
        if state.variables.pop("__redraw", None):
            _paint()
        return "break"

    def on_key_up(event):
        # keyUp is the handler that reads the answer and moves the page.
        actions = fields.key_up(state, event.keysym, event.char)
        if not actions:
            return None
        moved = follow(state, actions)
        if state.variables.pop("__beep", None):
            try:
                root.bell()
            except tk.TclError:
                pass
        if moved:
            show(state.index)
        elif state.variables.pop("__redraw", None):
            _paint()
        return "break"

    def _activate(obj):
        state.variables["target"] = (obj or {}).get("name") or "page"
        picked = ((obj or {}).get("name") or "").upper()
        if picked in ("A", "B", "C", "D", "E"):
            from engine.quiz import call
            call(state, "handleQuizClick", f'"{picked}"')
        script = click_script(obj)
        moved = False
        revealed = False
        if script:
            actions = run_handler(state, script)
            # A Next that shows what the page was holding back has done its
            # job. It does not also turn the page.
            revealed = any(a.get("kind") == "setprop" and str(a.get("target") or "").startswith("visible of")
                           for a in actions)
            moved = follow(state, actions)
        if not moved:
            moved = follow(state, run_page_handlers(state, "buttonclick"))
        if not moved and not revealed and picked in ("OK", "NEXT", "SKIP", "BACK", "HELP"):
            from engine.quiz import call
            result = call(state, "handleQuizClick", f'"{picked}"')
            if isinstance(result, tuple) and result and result[0] == "goto" and result[1]:
                book = result[2] if len(result) > 2 else None
                moved = follow(state, [{"kind": "goto", "page": result[1], "book": book}])
        if state.variables.pop("__exit", None):
            root.destroy()
            return
        if moved:
            show(state.index)
            return
        if state.variables.pop("__redraw", None):
            _paint()
            return
        item = (obj or {}).get("item") or {}
        if item.get("page") or item.get("book") or item.get("label"):
            on_button(item.get("label") or (obj or {}).get("text") or "", item.get("page") or "", item.get("book") or "")

    def on_button(label: str, target: str, book_name: str = ""):
        if book_name and open_other(state, book_name, target or ""):
            show(state.index)
            return
        press(state, label, target)
        show(state.index)

    gfx.bind("<Configure>", _on_configure)
    gfx.bind("<ButtonPress-1>", on_press)
    gfx.bind("<ButtonRelease-1>", on_release)
    gfx.bind("<KeyPress>", on_key)
    gfx.bind("<KeyRelease>", on_key_up)
    lb.bind("<<ListboxSelect>>", lambda e: show(lb.curselection()[0]) if lb.curselection() and not held.get("lock") else None)
    show(idx.get())
    try:
        root.mainloop()
    finally:
        stop_ahead()
    return 0


def _window_path() -> Path:
    return _progress_path().with_name("window.json")


def _saved_window():
    path = _window_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data["w"]), int(data["h"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
