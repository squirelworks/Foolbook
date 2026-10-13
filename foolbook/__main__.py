"""Foolbook main entry.

Foolbook is the tool that opens a book. A course module (or Foolcourse)
can launch it with a path; if none is given, Foolbook asks for one.

  python3 -m foolbook path/to/book.fbk     # open that book in the GUI
  python3 -m foolbook --port 8080 book.fbk # viewer on that port (default 1337)
  python3 -m foolbook --student _student/alex.json book.fbk
  python3 -m foolbook                      # ask for a file, then open the GUI
  python3 -m foolbook --cli path/to/book   # terminal viewer
  python3 -m foolbook --catalog            # rebuild _courses/catalog.json
  python3 -m foolbook --debug              # files and checksums
  python3 -m foolbook --debug book.tbk     # keep decoded source
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the Foolbook root is on the path so viewer/, engine/, menu/, author/
# resolve even if this file is launched as a script.
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def main() -> int:
    args = sys.argv[1:]
    if "--freshstart" in args:
        return _freshstart()
    if "--doctor" in args:
        from foolbook._debug.dump import dump
        path = dump("doctor")
        print(f"Wrote {path}")
        return 0
    port = _take_port(args)
    student = _take_student(args)
    locale = _take_locale(args)
    course = _take_course(args)
    bin_path = _take_bin(args)
    if bin_path:
        from engine.loader import set_keyword_bin
        set_keyword_bin(bin_path)
    debug_mode = _take_debug(args)
    if debug_mode is not None and not args:
        from _debug.debug import main as debug_main
        return debug_main([debug_mode] if debug_mode else [])
    if debug_mode is not None:
        from engine.loader import set_keep_decoded
        set_keep_decoded(True)
    if "--from" in args:
        i = args.index("--from")
        src = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
        from viewer.gui import open_from
        return open_from(src, course=course)
    if "--server" in args:
        args.remove("--server")
        from viewer.gui import serve
        serve(path=None, port=port, student=student, locale=locale, course=course)
        return 0
    if not args:
        # Default book ships with Foolbook
        default = Path(__file__).resolve().parent / "books" / "using_foolbook.json"
        if default.exists():
            args = [str(default)]
        else:
            path = _ask_for_book()
            if not path:
                return 0
            args = [path]
    if args[0] == "--menu":
        from menu.menu import main as menu_main
        return menu_main(args[1:])
    if args[0] == "--cli":
        from viewer.cli import main as cli_main
        return cli_main([str(normalize_path(a)) if i == 0 else a for i, a in enumerate(args[1:])])
    if args[0] in ("--gui", "-g"):
        args = args[1:]
    if args and args[0] == "--catalog":
        from _courses.catalog import main as catalog_main
        return catalog_main(args[1:])
    if args and args[0] == "--author":
        from author.gui import main as author_main
        return author_main(args[1:])
    if args:
        args = [str(normalize_path(args[0]))] + args[1:]
    from viewer.native import open_book
    # Splash only when no path was given (default book)
    show_splash = not sys.argv[1:] or (len(sys.argv) == 2 and "using_foolbook" in sys.argv[1])
    return open_book(args[0], student=student, course=course, splash=show_splash)





def _freshstart() -> int:
    """Force-reinstall Foolbook and everything under it."""
    import subprocess
    cmd = [
        sys.executable, "-m", "pip", "install", "--force-reinstall",
        "git+https://github.com/squirelworks/Foolbook.git@v1.0.1r2",
    ]
    return subprocess.call(cmd)


def _take_locale(args: list[str]) -> str:
    """Pull --locale ID out of argv. Empty means the viewer default."""
    if "--locale" not in args:
        return ""
    i = args.index("--locale")
    if i + 1 >= len(args):
        print("--locale needs an id")
        raise SystemExit(2)
    locale = args[i + 1]
    del args[i:i + 2]
    return locale



def _take_course(args: list[str]) -> str:
    """Pull --course ID out of argv. Empty means the book stem."""
    if "--course" not in args:
        return ""
    i = args.index("--course")
    if i + 1 >= len(args):
        print("--course needs an id")
        raise SystemExit(2)
    course = args[i + 1]
    del args[i:i + 2]
    return course


def _take_student(args: list[str]) -> str:
    """Pull --student PATH out of argv. Empty means the viewer's own file."""
    if "--student" not in args:
        return ""
    i = args.index("--student")
    if i + 1 >= len(args):
        print("--student needs a path")
        raise SystemExit(2)
    path = args[i + 1]
    del args[i:i + 2]
    return path


def _take_port(args: list[str]) -> int:
    """Pull --port N out of argv. Default is 1337."""
    if "--port" not in args:
        return 1337
    i = args.index("--port")
    if i + 1 >= len(args):
        print("--port needs a number")
        raise SystemExit(2)
    raw = args[i + 1]
    try:
        port = int(raw)
    except ValueError:
        print(f"--port needs a number, got {raw}")
        raise SystemExit(2)
    if not 1 <= port <= 65535:
        print(f"--port out of range: {port}")
        raise SystemExit(2)
    del args[i:i + 2]
    return port


def _take_debug(args: list[str]) -> str | None:
    """Pull --debug [mode] out of argv.

    Returns None if --debug was not given, '' for a bare --debug, or the mode.
    A mode that is a book path is left in argv so the book still opens.
    """
    if "--debug" not in args:
        return None
    i = args.index("--debug")
    mode = ""
    if i + 1 < len(args) and not args[i + 1].startswith("-"):
        nxt = args[i + 1]
        nxt_path = normalize_path(nxt)
        if not nxt_path.exists() and not nxt.lower().endswith((".tbk", ".sbk", ".fbk", ".fsk", ".json")):
            mode = nxt
            del args[i + 1]
    del args[i]
    return mode


def _take_bin(args: list[str]) -> str:
    """Pull --bin PATH out of argv. Returns the path or ''."""
    if "--bin" not in args:
        return ""
    i = args.index("--bin")
    if i + 1 >= len(args):
        print("--bin needs a path")
        raise SystemExit(2)
    path = args[i + 1]
    del args[i:i + 2]
    return path


def normalize_path(raw: str) -> Path:
    """Accept either slash and expand ~."""
    return Path(raw.strip().strip('"').strip("'").replace("\\", "/")).expanduser()


def _ask_for_book() -> str:
    """Open a file picker when no path was given."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Open a book",
            filetypes=[
                ("Books", "*.fbk *.tbk *.json *.fsk *.sbk"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return path or ""
    except Exception:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
