"""Native Foolbook window.

Opens a book in a desktop window. Exits when the window closes.
No server. No browser.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from engine.loader import load
from progress.progress import Progress


def open_book(path: str | Path, student: str = "", course: str = "") -> int:
    """Open a book in a native window. Returns when the window closes."""
    book = load(path)
    course_id = course or Path(path).stem
    progress = Progress(Path(student) if student else _progress_path())
    progress.touch(course_id)

    root = tk.Tk()
    root.title(book.title or Path(path).name)
    root.geometry("800x500")

    pages = book.pages
    idx = tk.IntVar(value=0)

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
