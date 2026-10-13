"""Native Foolbook window.

Opens a book in a desktop window. Exits when the window closes.
No server. No browser.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from engine.loader import load
from engine.graphics import bottom, draw, extract
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

    sidebar = ttk.Frame(root, width=160)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    lb = tk.Listbox(sidebar)
    lb.pack(fill="both", expand=True)
    for p in pages:
        lb.insert("end", p.id)

    main = ttk.Frame(root)
    main.pack(side="left", fill="both", expand=True)
    content = tk.Text(main, wrap="word", state="disabled")
    content.pack(fill="both", expand=True, padx=8, pady=8)
    gfx = tk.Canvas(main, height=0, highlightthickness=0, bg="white")
    gfx.pack(fill="x", padx=8)
    nav = ttk.Frame(main)
    nav.pack(fill="x", padx=8, pady=4)

    def show(i: int):
        if not pages:
            return
        i = max(0, min(i, len(pages) - 1))
        idx.set(i)
        p = pages[i]
        progress.mark_page(course_id, p.id)
        lb.selection_clear(0, "end")
        lb.selection_set(i)
        lb.see(i)
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
            draw(gfx, shapes, base=Path(book.path).parent)
        else:
            gfx.config(height=0)
        for w in nav.winfo_children():
            w.destroy()
        items = p.items or []
        if items:
            for it in items:
                label = it.get("label") or it.get("page") or "Go"
                target = it.get("page") or ""
                ttk.Button(nav, text=label, command=lambda t=target: jump(t)).pack(side="left", padx=2)
        else:
            if i > 0:
                ttk.Button(nav, text="Back", command=lambda: show(i - 1)).pack(side="left", padx=2)
            if i + 1 < len(pages):
                ttk.Button(nav, text="Next", command=lambda: show(i + 1)).pack(side="left", padx=2)
        if p.quiz:
            for ch in (p.quiz.get("choices") or []):
                ttk.Button(
                    nav, text=ch.get("label") or "?",
                    command=lambda c=ch: answer(c, p),
                ).pack(side="left", padx=2)

    def jump(page_id: str):
        for i, p in enumerate(pages):
            if p.id.lower() == page_id.lower():
                show(i)
                return

    def answer(choice: dict, page):
        progress.record_answer(course_id, page.id, bool(choice.get("correct")))
        target = choice.get("next") if choice.get("correct") else choice.get("again")
        if target:
            jump(target)

    lb.bind("<<ListboxSelect>>", lambda e: show(lb.curselection()[0]) if lb.curselection() else None)
    show(idx.get())
    root.mainloop()
    return 0


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
