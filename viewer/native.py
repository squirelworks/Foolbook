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
from engine.engine import enter_page, goto, open_book as open_other, press
from foolbook.model import RuntimeState
from progress.progress import Progress


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
    root.geometry("960x600")

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
                ("Books", "*.fbk *.tbk *.json *.fsk *.sbk"),
                ("ToolBook", "*.tbk *.sbk"),
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
    gfx = tk.Canvas(main, height=0, highlightthickness=0, bg="white")
    gfx.pack(fill="x", padx=8, pady=(8, 0))
    content = tk.Text(main, wrap="word", state="disabled")
    content.pack(fill="both", expand=True, padx=8, pady=8)
    nav = ttk.Frame(main)
    nav.pack(fill="x", padx=8, pady=4)
    painting = {"on": False}

    def show(i: int):
        if painting["on"] or not state.book.pages:
            return
        painting["on"] = True
        try:
            state.index = max(0, min(i, len(state.book.pages) - 1))
            enter_page(state)
            _paint()
        finally:
            painting["on"] = False

    def _paint():
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
        content.config(state="normal")
        content.delete("1.0", "end")
        content.insert("end", p.id + "\n\n")
        for t in (p.text or []):
            content.insert("end", t + "\n\n")
        content.config(state="disabled")
        shapes = extract(p)
        gfx.delete("all")
        if shapes:
            gfx.config(height=min(320, max(48, bottom(shapes) + 8)))
            draw(gfx, shapes, base=Path(state.book.path).parent)
        else:
            gfx.config(height=0)
        for w in nav.winfo_children():
            w.destroy()
        items = p.items or []
        if items:
            for it in items:
                label = it.get("label") or it.get("page") or "Go"
                target = it.get("page") or ""
                other = it.get("book") or ""
                ttk.Button(
                    nav, text=label,
                    command=lambda l=label, t=target, b=other: on_button(l, t, b),
                ).pack(side="left", padx=2)
        else:
            if state.index > 0:
                ttk.Button(nav, text="Back", command=lambda: on_button("Back", "")).pack(side="left", padx=2)
            if state.index + 1 < len(pages):
                ttk.Button(nav, text="Next", command=lambda: on_button("Next", "")).pack(side="left", padx=2)
        if p.quiz:
            for ch in (p.quiz.get("choices") or []):
                ttk.Button(
                    nav, text=ch.get("label") or "?",
                    command=lambda c=ch: answer(c),
                ).pack(side="left", padx=2)

    def on_button(label: str, target: str, book_name: str = ""):
        if book_name and open_other(state, book_name, target or ""):
            show(state.index)
            return
        press(state, label, target)
        show(state.index)

    def answer(choice: dict):
        page = state.page
        if page is None:
            return
        progress.record_answer(held["course"], page.id, bool(choice.get("correct")))
        target = ""
        if choice.get("correct"):
            target = choice.get("next") or (page.quiz or {}).get("next") or ""
        else:
            target = choice.get("again") or (page.quiz or {}).get("again") or ""
        if target:
            goto(state, target)
            show(state.index)

    lb.bind("<<ListboxSelect>>", lambda e: show(lb.curselection()[0]) if lb.curselection() else None)
    show(idx.get())
    root.mainloop()
    return 0


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
