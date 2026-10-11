"""Foolbook viewer (terminal).

Called by the main entry point. Prefer:

  python3 -m foolbook [book]
"""

from __future__ import annotations

import sys
from pathlib import Path

from engine.loader import load
from engine.engine import run_handler, goto
from foolbook.model import RuntimeState


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
    state = RuntimeState(book=book)

    while True:
        page = state.page
        if page is None:
            print("(no page)")
            break
        print(f"\n=== {page.id} ===")
        for line in page.text[:6]:
            print(f"  {line}")
        if page.quiz and page.quiz.get("choices"):
            print("  [quiz]")
            for c in page.quiz["choices"]:
                mark = "*" if c.get("correct") else " "
                print(f"   {mark} {c.get('label')}")
        buttons = page.items or [{"label": j, "page": j} for j in page.jumps]
        if buttons:
            print("  actions:", ", ".join(b.get("label", "?") for b in buttons))

        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd or cmd.lower() in ("q", "quit", "exit"):
            break
        if cmd.lower() in ("n", "next"):
            if buttons:
                target = buttons[0].get("page")
                if target:
                    goto(state, target)
                    continue
            if state.index + 1 < len(state.book.pages):
                state.index += 1
            continue
        if cmd.lower() in ("b", "back"):
            if len(buttons) > 1:
                target = buttons[1].get("page")
                if target:
                    goto(state, target)
                    continue
            if state.index > 0:
                state.index -= 1
            continue
        # treat as a page id or a handler source snippet
        if state.book.page(cmd):
            goto(state, cmd)
            continue
        actions = run_handler(state, cmd)
        for act in actions:
            print(f"  action: {act}")
            if act["kind"] == "goto":
                goto(state, act["page"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
