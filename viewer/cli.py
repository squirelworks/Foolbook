"""Foolbook viewer (terminal).

Called by the main entry point. Prefer:

  python3 -m foolbook [book]
"""

from __future__ import annotations

import sys
from pathlib import Path

from engine.loader import load
from engine.engine import run_handler, goto, follow, run_page_handlers
from foolbook.model import RuntimeState
from progress.progress import Progress


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    print("Foolbook")
    if not argv:
        print("No book given. Pass a .tbk, .sbk, or .json to open one.")
        print("  python3 -m foolbook path/to/book.tbk")
        return 0
    path = Path(argv[0])
    if not path.exists():
        print(f"not found: {path}")
        return 1

    book = load(path)
    print(f"{book.title or path.name}  ({len(book.pages)} pages)")
    scripted = sum(1 for p in book.pages if p.handlers)
    if scripted:
        print(f"  {scripted} pages with handlers")
    state = RuntimeState(book=book)
    # reader defaults so EnterPage does not bounce to another book
    state.variables.setdefault("__import", True)
    state.variables.setdefault("sysLevel", "reader")

    progress = Progress(_progress_path())
    course_id = path.stem
    last = progress.last_page(course_id)
    if last and book.index_of(last) >= 0 and last != book.pages[0].id:
        print(f"  resume at {last}")
        state.index = book.index_of(last)

    entered = None
    while True:
        page = state.page
        if page is None:
            print("(no page)")
            break
        if entered != page.id:
            entered = page.id
            progress.mark_page(course_id, page.id)
            actions = run_page_handlers(state, "enterpage")
            if follow(state, actions):
                continue
        print(f"\n=== {page.id} ===")
        for line in page.text[:6]:
            print(f"  {line}")
        if page.quiz and page.quiz.get("choices"):
            print("  [quiz]")
            for i, c in enumerate(page.quiz["choices"], 1):
                mark = "*" if c.get("correct") else " "
                print(f"   {mark} {i}. {c.get('label')}")
        buttons = page.items or [{"label": j, "page": j} for j in page.jumps]
        prompts = []
        if buttons:
            prompts.extend(b.get("label", "?").lower() for b in buttons)
        else:
            if state.index > 0:
                prompts.append("back")
            if state.index + 1 < len(state.book.pages):
                prompts.append("next")
        if page.quiz and page.quiz.get("choices"):
            prompts.extend(str(i) for i in range(1, len(page.quiz["choices"]) + 1))
        prompts = [p for p in prompts if p]
        prompt = "> (" + ", ".join(f"'{p}'" for p in prompts) + ") " if prompts else "> "

        try:
            cmd = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd or cmd.lower() in ("q", "quit", "exit"):
            break
        if page.quiz and page.quiz.get("choices") and cmd.isdigit():
            n = int(cmd) - 1
            choices = page.quiz["choices"]
            if 0 <= n < len(choices):
                c = choices[n]
                print("  Correct" if c.get("correct") else "  Incorrect")
                if c.get("correct") and page.quiz.get("next"):
                    goto(state, page.quiz["next"])
                elif not c.get("correct") and page.quiz.get("again"):
                    goto(state, page.quiz["again"])
            continue
        # match a button, then follow it; fall back to running buttonClick
        matched = None
        for b in buttons:
            if (b.get("label") or "").lower() == cmd.lower():
                matched = b
                break
        if cmd.lower() in ("n", "next"):
            matched = matched or next((b for b in buttons if (b.get("label") or "").lower() == "next"), None)
        if cmd.lower() in ("b", "back", "previous"):
            matched = matched or next((b for b in buttons if (b.get("label") or "").lower() == "back"), None)
        if matched:
            if matched.get("book"):
                print(f"  (cross-book {matched['book']} {matched.get('page')})")
                continue
            if matched.get("page") and state.book.page(matched["page"]):
                goto(state, matched["page"])
                continue
        if cmd.lower() in ("n", "next", "back", "previous", "menu"):
            actions = run_page_handlers(state, "buttonclick")
            if follow(state, actions):
                continue
        if cmd.lower() in ("n", "next"):
            if state.index + 1 < len(state.book.pages):
                state.index += 1
            continue
        if cmd.lower() in ("b", "back"):
            if state.index > 0:
                state.index -= 1
            continue
        if state.book.page(cmd):
            goto(state, cmd)
            continue
        actions = run_handler(state, cmd)
        for act in actions:
            print(f"  action: {act}")
        follow(state, actions)
    return 0


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


if __name__ == "__main__":
    raise SystemExit(main())
