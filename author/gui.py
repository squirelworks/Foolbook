"""Foolbook author.

Slide editor. Produces .fbk (and .fsk). Export .tbk writes a shell with compiled OpenScript.

  python3 -m author.gui
  python3 -m author.gui path/to/book.fbk
"""

from __future__ import annotations

import sys
from pathlib import Path

from .formats import save_book, load as load_book

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
        self.root.geometry("1100x720")
        self.book: dict = {"id": "new", "title": "New book", "pages": []}
        self.path: Path | None = path
        self.current = 0
        self.tool = tk.StringVar(value="select")
        self._build()
        if path and path.exists():
            self._load(path)
        else:
            self._new()
        self.root.mainloop()

    def _build(self):
        # toolbar
        bar = ttk.Frame(self.root, padding=4)
        bar.pack(fill="x")
        ttk.Button(bar, text="New", command=self._new).pack(side="left")
        ttk.Button(bar, text="Open", command=self._open).pack(side="left", padx=2)
        ttk.Button(bar, text="Save", command=self._save).pack(side="left")
        ttk.Button(bar, text="Save as", command=self._save_as).pack(side="left", padx=2)
        ttk.Button(bar, text="Export .tbk", command=self._export_tbk).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        for name, label in (("select", "Select"), ("text", "Text"), ("box", "Box"), ("button", "Button")):
            ttk.Radiobutton(bar, text=label, value=name, variable=self.tool).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar, text="Bold", command=lambda: self._wrap("**")).pack(side="left")
        ttk.Button(bar, text="List", command=self._make_list).pack(side="left", padx=2)
        self.status = ttk.Label(bar, text="")
        self.status.pack(side="right")

        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=4, pady=4)

        # page list
        left = ttk.Frame(body, width=160)
        body.add(left, weight=0)
        ttk.Label(left, text="Slides").pack(anchor="w")
        self.pages = tk.Listbox(left, exportselection=False, width=18)
        self.pages.pack(fill="both", expand=True)
        self.pages.bind("<<ListboxSelect>>", self._on_select)
        row = ttk.Frame(left)
        row.pack(fill="x", pady=4)
        ttk.Button(row, text="Add", command=self._add_page).pack(side="left")
        ttk.Button(row, text="Delete", command=self._del_page).pack(side="left", padx=4)

        # center: preview + editor
        center = ttk.Frame(body)
        body.add(center, weight=3)

        ttk.Label(center, text="Preview").pack(anchor="w")
        self.canvas = tk.Canvas(center, bg="white", height=280, highlightthickness=1, highlightbackground="#888")
        self.canvas.pack(fill="x", pady=(0, 6))
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        form = ttk.Frame(center)
        form.pack(fill="x")
        ttk.Label(form, text="Page id").grid(row=0, column=0, sticky="w")
        self.pid = ttk.Entry(form, width=20)
        self.pid.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(form, text="Next").grid(row=0, column=2, sticky="w")
        self.next = ttk.Entry(form, width=16)
        self.next.grid(row=0, column=3, sticky="w", padx=4)
        ttk.Label(form, text="Back").grid(row=0, column=4, sticky="w")
        self.back = ttk.Entry(form, width=16)
        self.back.grid(row=0, column=5, sticky="w", padx=4)

        ttk.Label(center, text="Text  (blank line = new paragraph; lines starting with - or * are a list)").pack(anchor="w", pady=(6, 0))
        self.text = tk.Text(center, height=10, wrap="word")
        self.text.pack(fill="both", expand=True)
        self.text.bind("<KeyRelease>", lambda e: self._preview())

        ttk.Button(center, text="Apply", command=self._apply).pack(anchor="e", pady=4)

    def _new(self):
        self.book = {
            "id": "new",
            "title": "New book",
            "pages": [{"id": "P0", "text": ["New slide"], "items": [], "widgets": []}],
        }
        self.path = None
        self.current = 0
        self._refresh_list()
        self.status.config(text="New book")

    def _open(self):
        p = filedialog.askopenfilename(
            title="Open book",
            filetypes=[("Foolbook", "*.fbk *.json"), ("All", "*.*")],
        )
        if p:
            self._load(Path(p))

    def _load(self, path: Path):
        self.book = load_book(path)
        self.path = path
        self.current = 0
        self._refresh_list()
        self.status.config(text=str(path.name))

    def _save(self):
        self._apply()
        if not self.path:
            self._save_as()
            return
        save_book(self.path, self.book)
        self.status.config(text=f"Saved {self.path.with_suffix('.json').name} and .fbk")

    def _save_as(self):
        self._apply()
        p = filedialog.asksaveasfilename(
            title="Save book",
            defaultextension=".fbk",
            filetypes=[("Foolbook book", "*.fbk"), ("JSON", "*.json")],
        )
        if not p:
            return
        self.path = Path(p)
        save_book(self.path, self.book)
        self.status.config(text=f"Saved {self.path.with_suffix('.json').name} and .fbk")


    def _export_tbk(self):
        """Write a best-effort .tbk with compiled OpenScript handlers.

        The shell is what we know: JBO stub, one page record per page,
        field text, and a buttonClick handler compiled by engine.openscript.
        It is not a book the ToolBook 8.1 engine would open.
        """
        self._apply()
        p = filedialog.asksaveasfilename(
            title="Export .tbk",
            defaultextension=".tbk",
            filetypes=[("ToolBook shell", "*.tbk")],
        )
        if not p:
            return
        from engine.openscript import compile as compile_script
        from author.tbkexport import write_tbk
        dest = Path(p)
        write_tbk(dest, self.book, compile_script)
        self.status.config(text=f"Exported {dest.name} (shell, compiled handlers)")

    def _refresh_list(self):
        self.pages.delete(0, "end")
        for p in self.book.get("pages") or []:
            self.pages.insert("end", p.get("id") or "?")
        if self.book.get("pages"):
            self.pages.selection_set(self.current)
            self._show(self.current)

    def _on_select(self, _evt=None):
        sel = self.pages.curselection()
        if not sel:
            return
        self._apply()
        self.current = sel[0]
        self._show(self.current)

    def _show(self, idx: int):
        pages = self.book.get("pages") or []
        if not (0 <= idx < len(pages)):
            return
        p = pages[idx]
        self.pid.delete(0, "end")
        self.pid.insert(0, p.get("id") or "")
        items = { (i.get("label") or "").lower(): i.get("page") for i in p.get("items") or [] }
        self.next.delete(0, "end")
        self.next.insert(0, items.get("next") or "")
        self.back.delete(0, "end")
        self.back.insert(0, items.get("back") or "")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n\n".join(p.get("text") or []))
        self._preview()

    def _apply(self):
        pages = self.book.get("pages") or []
        if not (0 <= self.current < len(pages)):
            return
        p = pages[self.current]
        p["id"] = self.pid.get().strip() or p.get("id") or "P0"
        raw = self.text.get("1.0", "end").strip()
        p["text"] = [b.strip() for b in raw.split("\n\n") if b.strip()]
        items = []
        if self.next.get().strip():
            items.append({"label": "Next", "page": self.next.get().strip()})
        if self.back.get().strip():
            items.append({"label": "Back", "page": self.back.get().strip()})
        p["items"] = items
        self.pages.delete(self.current)
        self.pages.insert(self.current, p["id"])
        self.pages.selection_set(self.current)
        self._preview()

    def _add_page(self):
        self._apply()
        n = len(self.book.get("pages") or [])
        self.book.setdefault("pages", []).append({
            "id": f"P{n * 100}",
            "text": ["New slide"],
            "items": [],
            "widgets": [],
        })
        self.current = n
        self._refresh_list()

    def _del_page(self):
        pages = self.book.get("pages") or []
        if len(pages) <= 1:
            return
        del pages[self.current]
        self.current = max(0, self.current - 1)
        self._refresh_list()

    def _preview(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 600
        h = 280
        self.canvas.create_rectangle(8, 8, w - 8, h - 8, outline="#ccc")
        raw = self.text.get("1.0", "end").strip()
        y = 24
        for block in raw.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            lines = block.split("\n")
            is_list = all(ln.lstrip().startswith(("-", "*")) for ln in lines if ln.strip())
            if is_list:
                for ln in lines:
                    ln = ln.lstrip().lstrip("-*").strip()
                    self.canvas.create_text(28, y, anchor="w", text=f"• {ln}", font=("TkDefaultFont", 11))
                    y += 18
            else:
                for ln in lines:
                    self.canvas.create_text(24, y, anchor="w", text=ln, font=("TkDefaultFont", 11))
                    y += 18
            y += 8
        # widgets
        page = (self.book.get("pages") or [None])[self.current] if self.book.get("pages") else None
        for wdg in (page or {}).get("widgets") or []:
            x, y_, ww, hh = wdg.get("x", 20), wdg.get("y", 20), wdg.get("w", 80), wdg.get("h", 24)
            kind = wdg.get("kind", "box")
            if kind == "button":
                self.canvas.create_rectangle(x, y_, x + ww, y_ + hh, fill="#c0c0c0", outline="#000")
                self.canvas.create_text(x + ww // 2, y_ + hh // 2, text=wdg.get("label", "Button"))
            else:
                self.canvas.create_rectangle(x, y_, x + ww, y_ + hh, outline="#448")

    def _on_canvas_click(self, evt):
        tool = self.tool.get()
        if tool == "select":
            return
        page = (self.book.get("pages") or [None])[self.current]
        if page is None:
            return
        page.setdefault("widgets", [])
        if tool == "text":
            page["widgets"].append({"kind": "text", "x": evt.x, "y": evt.y, "w": 160, "h": 24, "label": "Text"})
        elif tool == "box":
            page["widgets"].append({"kind": "box", "x": evt.x, "y": evt.y, "w": 100, "h": 60})
        elif tool == "button":
            page["widgets"].append({"kind": "button", "x": evt.x, "y": evt.y, "w": 80, "h": 24, "label": "Button"})
        self._preview()

    def _wrap(self, mark: str):
        try:
            sel = self.text.get("sel.first", "sel.last")
            self.text.delete("sel.first", "sel.last")
            self.text.insert("insert", f"{mark}{sel}{mark}")
        except tk.TclError:
            pass
        self._preview()

    def _make_list(self):
        try:
            sel = self.text.get("sel.first", "sel.last")
        except tk.TclError:
            return
        lines = ["- " + ln.strip() if ln.strip() and not ln.strip().startswith(("-", "*")) else ln for ln in sel.split("\n")]
        self.text.delete("sel.first", "sel.last")
        self.text.insert("insert", "\n".join(lines))
        self._preview()


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else None
    Editor(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
