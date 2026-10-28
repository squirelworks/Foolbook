"""Rebuild _books/catalog.json from the books on disk.

  python3 -m foolbook --catalog
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "catalog.json"


def _read_book(path: Path) -> dict:
    try:
        from engine.formats import load
        data = load(path)
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


def scan(root: Path | None = None) -> dict:
    """Return a catalog built from every .fbk under _books/."""
    root = root or HERE
    # subject -> module -> list of course dicts
    tree: dict[str, dict[str, list[dict]]] = {}
    for fbk in sorted(root.rglob("*.fbk")):
        data = _read_book(fbk)
        rel = fbk.relative_to(root.parent)
        course_id = data.get("id") or fbk.stem
        title = data.get("title") or fbk.stem
        # folder layout: _books/<book>/<book>.fbk
        # optional subject/module keys in the book override
        parent = fbk.parent.name
        subject = data.get("subject") or "Courses"
        module = data.get("module") or parent
        tree.setdefault(subject, {}).setdefault(module, []).append({
            "id": course_id,
            "title": title,
            "path": str(rel).replace("\\", "/"),
        })

    subjects = []
    for subject, modules in tree.items():
        subjects.append({
            "name": subject,
            "modules": [
                {"name": mod, "courses": courses}
                for mod, courses in modules.items()
            ],
        })
    return {"title": "Foolbook", "subjects": subjects}


def write(catalog: dict | None = None) -> Path:
    catalog = catalog if catalog is not None else scan()
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return CATALOG


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    catalog = scan()
    path = write(catalog)
    n = sum(
        len(mod.get("courses") or [])
        for sub in catalog.get("subjects") or []
        for mod in sub.get("modules") or []
    )
    print(f"catalog: {n} course(s) -> {path.name}")
    for sub in catalog.get("subjects") or []:
        for mod in sub.get("modules") or []:
            for c in mod.get("courses") or []:
                print(f"  {sub['name']} / {mod['name']} / {c['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
