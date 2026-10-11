"""Course menu.

Lists courses by subject, module, and course.
Selecting a course launches the Foolbook viewer.
Progression is recorded through the progress module.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("Tkinter is required for the course menu.")
    raise SystemExit(1)

from progress.progress import Progress


class Menu:
    def __init__(self, catalog_path: Path | None = None):
        self.root = tk.Tk()
        self.root.title("Foolbook")
        self.root.geometry("900x520")
        self.catalog: dict = {"title": "", "subjects": []}
        self.rows: list[dict] = []
        self.progress = Progress(Path("progress.json"))
        self._build()
        if catalog_path and catalog_path.exists():
            self._load(catalog_path)
        self.root.mainloop()

    def _build(self):
        bar = ttk.Frame(self.root, padding=4)
        bar.pack(fill="x")
        ttk.Button(bar, text="Open catalog", command=self._open).pack(side="left")
        ttk.Button(bar, text="Author", command=self._author).pack(side="left", padx=4)
        self.title = ttk.Label(bar, text="Foolbook")
        self.title.pack(side="left", padx=12)
        self.status = ttk.Label(bar, text="")
        self.status.pack(side="right")

        cols = ("subject", "module", "course", "id", "progress")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("subject", text="Subject")
        self.tree.heading("module", text="Module")
        self.tree.heading("course", text="Course")
        self.tree.heading("id", text="Id")
        self.tree.heading("progress", text="Progress")
        self.tree.column("subject", width=160)
        self.tree.column("module", width=220)
        self.tree.column("course", width=260)
        self.tree.column("id", width=100)
        self.tree.column("progress", width=80)
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.tree.bind("<Double-1>", lambda _e: self._launch())

        bot = ttk.Frame(self.root, padding=4)
        bot.pack(fill="x")
        ttk.Button(bot, text="Open in viewer", command=self._launch).pack(side="left")
        ttk.Button(bot, text="Open in GUI", command=lambda: self._launch(gui=True)).pack(side="left", padx=4)

    def _open(self):
        p = filedialog.askopenfilename(
            title="Open catalog",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if p:
            self._load(Path(p))

    def _load(self, path: Path):
        self.catalog = json.loads(path.read_text(encoding="utf-8"))
        self.title.config(text=self.catalog.get("title") or path.stem)
        self._fill()
        self.status.config(text=str(path.name))

    def _fill(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows = []
        for subj in self.catalog.get("subjects") or []:
            for mod in subj.get("modules") or []:
                for course in mod.get("courses") or []:
                    cid = course.get("id") or ""
                    prog = self.progress.status(cid)
                    self.rows.append({
                        "subject": subj.get("title") or "",
                        "module": mod.get("title") or "",
                        "course": course.get("title") or "",
                        "id": cid,
                        "path": course.get("path") or "",
                    })
                    self.tree.insert("", "end", values=(
                        subj.get("title") or "",
                        mod.get("title") or "",
                        course.get("title") or "",
                        cid,
                        prog,
                    ))

    def _selected(self) -> dict | None:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return self.rows[idx] if 0 <= idx < len(self.rows) else None

    def _launch(self, gui: bool = False):
        row = self._selected()
        if not row:
            messagebox.showinfo("Foolbook", "Select a course first.")
            return
        path = row.get("path")
        if not path or not Path(path).exists():
            messagebox.showwarning("Foolbook", f"Course file not found:\n{path}")
            return
        cid = row.get("id") or ""
        self.progress.touch(cid)
        self._fill()
        cmd = [sys.executable, "-m", "foolbook", path]
        if gui:
            cmd = [sys.executable, "-m", "foolbook", "--gui", path]
        subprocess.Popen(cmd)

    def _author(self):
        subprocess.Popen([sys.executable, "-m", "author.gui"])


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else None
    Menu(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
