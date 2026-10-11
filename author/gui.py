"""Foolbook course editor.

Coded GUI (Tkinter). Not HTML.

  python3 -m author.gui
  python3 -m author.gui path/to/book.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("Tkinter is required for the authoring GUI.")
    print("On Windows it ships with Python. On Linux install python3-tk.")
    raise SystemExit(1)


class Editor:
    def __init__(self, path: Path | None = None):
        self.root = tk.Tk()
        self.root.title("Foolbook Author")
        self.root.geometry("960x640")
        self.book: dict = {"id": "new", "title": "New book", "pages": []}
        self.path: Path | None = path
        self._build()
        if path and path.exists():
            self._load(path)
        else:
            self._new()
        self.root.mainloop()

    def _build(self):
        bar = ttk.Frame(self.root, padding=4)
        bar.pack(fill="x")
        ttk.Button(bar, text="New", command=self._new).pack(side="left")
        ttk.Button(bar, text="Open", command=self._open).pack(side="left", padx=4)
        ttk.Button(bar, text="Save", command=self._save).pack(side="left")
        ttk.Button(bar, text="Save as", command=self._save_as).pack(side="left", padx=4)
        self.status = ttk.Label(bar, text="")
        self.status.pack(side="right")

        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=4, pady=4)

        left = ttk.Frame(body, width=180)
        body.add(left, weight=1)
        ttk.Label(left, text="Pages").pack(anchor="w")
        self.pages = tk.Listbox(left, exportselection=False)
        self.pages.pack(fill="both", expand=True)
        self.pages.bind("<<ListboxSelect>>", self._on_select)
        row = ttk.Frame(left)
        row.pack(fill="x", pady=4)
        ttk.Button(row, text="Add", command=self._add_page).pack(side="left")
        ttk.Button(row, text="Delete", command=self._del_page).pack(side="left", padx=4)

        right = ttk.Frame(body)
        body.add(right, weight=3)
        form = ttk.Frame(right)
        form.pack(fill="x")
        ttk.Label(form, text="Page id").grid(row=0, column=0, sticky="w")
        self.pid = ttk.Entry(form)
        self.pid.grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Label(form, text="Next").grid(row=1, column=0, sticky="w")
        self.next = ttk.Entry(form)
        self.next.grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Label(form, text="Back").grid(row=2, column=0, sticky="w")
        self.back = ttk.Entry(form)
        self.back.grid(row=2, column=1, sticky="ew", padx=4)
        form.columnconfigure(1, weight=1)

        ttk.Label(right, text="Text (one paragraph per line)").pack(anchor="w", pady=(8, 0))
        self.text = tk.Text(right, height=12, wrap="word")
        self.text.pack(fill="both", expand=True)

        ttk.Label(right, text="Quiz choices (one per line, prefix * for correct)").pack(anchor="w")
        self.quiz = tk.Text(right, height=6, wrap="word")
        self.quiz.pack(fill="x")

        ttk.Button(right, text="Apply page", command=self._apply).pack(anchor="e", pady=4)

    def _new(self):
        self.book = {
            "id": "new",
            "title": "New book",
            "pages": [{"id": "P0", "text": ["New page"], "items": []}],
        }
        self.path = None
        self._refresh_list()
        self.status.config(text="New book")

    def _open(self):
        p = filedialog.askopenfilename(
            title="Open book",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if p:
            self._load(Path(p))

    def _load(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.book = data
        self.path = path
        self._refresh_list()
        self.status.config(text=str(path.name))

    def _save(self):
        self._apply()
        if not self.path:
            self._save_as()
            return
        self.path.write_text(json.dumps(self.book, indent=2), encoding="utf-8")
        self.status.config(text=f"Saved {self.path.name}")

    def _save_as(self):
        self._apply()
        p = filedialog.asksaveasfilename(
            title="Save book",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not p:
            return
        self.path = Path(p)
        self.path.write_text(json.dumps(self.book, indent=2), encoding="utf-8")
        self.status.config(text=f"Saved {self.path.name}")

    def _refresh_list(self):
        self.pages.delete(0, "end")
        for p in self.book.get("pages") or []:
            self.pages.insert("end", p.get("id") or "?")
        if self.book.get("pages"):
            self.pages.selection_set(0)
            self._show(0)

    def _on_select(self, _evt=None):
        sel = self.pages.curselection()
        if sel:
            self._show(sel[0])

    def _show(self, index: int):
        pages = self.book.get("pages") or []
        if not (0 <= index < len(pages)):
            return
        p = pages[index]
        self.pid.delete(0, "end")
        self.pid.insert(0, p.get("id") or "")
        items = p.get("items") or []
        nxt = next((i.get("page") for i in items if (i.get("label") or "").lower() == "next"), "")
        bak = next((i.get("page") for i in items if (i.get("label") or "").lower() == "back"), "")
        self.next.delete(0, "end")
        self.next.insert(0, nxt)
        self.back.delete(0, "end")
        self.back.insert(0, bak)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(p.get("text") or []))
        self.quiz.delete("1.0", "end")
        q = p.get("quiz") or {}
        lines = []
        for c in q.get("choices") or []:
            mark = "* " if c.get("correct") else ""
            lines.append(f"{mark}{c.get('label', '')}")
        self.quiz.insert("1.0", "\n".join(lines))

    def _apply(self):
        sel = self.pages.curselection()
        if not sel:
            return
        index = sel[0]
        pages = self.book.setdefault("pages", [])
        if not (0 <= index < len(pages)):
            return
        p = pages[index]
        p["id"] = self.pid.get().strip() or p.get("id") or "P0"
        text = [ln for ln in self.text.get("1.0", "end").splitlines() if ln.strip()]
        p["text"] = text
        items = []
        if self.next.get().strip():
            items.append({"label": "Next", "page": self.next.get().strip()})
        if self.back.get().strip():
            items.append({"label": "Back", "page": self.back.get().strip()})
        p["items"] = items
        choices = []
        for ln in self.quiz.get("1.0", "end").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            correct = ln.startswith("*")
            label = ln.lstrip("* ").strip()
            choices.append({"label": label, "correct": correct})
        p["quiz"] = {"choices": choices} if choices else None
        self.pages.delete(index)
        self.pages.insert(index, p["id"])
        self.pages.selection_set(index)

    def _add_page(self):
        self._apply()
        n = len(self.book.get("pages") or [])
        pid = f"P{n * 100}"
        self.book.setdefault("pages", []).append({"id": pid, "text": [""], "items": []})
        self._refresh_list()
        self.pages.selection_clear(0, "end")
        self.pages.selection_set("end")
        self._show(len(self.book["pages"]) - 1)

    def _del_page(self):
        sel = self.pages.curselection()
        if not sel:
            return
        if not messagebox.askyesno("Delete", "Delete this page?"):
            return
        del self.book["pages"][sel[0]]
        self._refresh_list()


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else None
    Editor(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
