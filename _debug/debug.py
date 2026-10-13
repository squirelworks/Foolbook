"""Foolbook debug.

Only runs when --debug is passed. All debug files live in this folder.

  python3 -m foolbook --debug              # files present and checksums match
  python3 -m foolbook --debug complete     # full check
  python3 -m foolbook --debug engine       # one module
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CHECKSUMS = HERE / "checksums.json"

# Expected layout. Paths are relative to the Foolbook root.
EXPECTED = [
    "main/__init__.py",
    "main/__main__.py",
    "main/model.py",
    "foolbook.py",
    "engine/__init__.py",
    "engine/engine.py",
    "engine/loader.py",
    "engine/tbk.py",
    "engine/openscript.py",
    "engine/compat/res_77.bin",
    "viewer/__init__.py",
    "viewer/cli.py",
    "viewer/gui.py",
    "author/__init__.py",
    "author/document.py",
    "author/formats.py",
    "author/gui.py",
    "author/web.py",
    "menu/__init__.py",
    "menu/menu.py",
    "progress/__init__.py",
    "progress/progress.py",
    "core/README.md",
    "README.md",
    "plannedmilestones.md",
]

MODULES = {
    "engine": ["engine.loader", "engine.engine", "engine.tbk"],
    "viewer": ["viewer.cli"],
    "author": ["author.formats", "author.document", "author.web"],
    "menu": ["menu.menu"],
    "progress": ["progress.progress"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def check_files() -> tuple[list[str], list[str]]:
    """Return (missing, present)."""
    missing = []
    present = []
    for rel in EXPECTED:
        if (ROOT / rel).exists():
            present.append(rel)
        else:
            missing.append(rel)
    return missing, present


def check_checksums() -> tuple[list[str], list[str]]:
    """Return (mismatches, ok). Empty checksums file means no baseline yet."""
    if not CHECKSUMS.exists():
        return [], []
    try:
        baseline = json.loads(CHECKSUMS.read_text(encoding="utf-8"))
    except Exception:
        return ["checksums.json unreadable"], []
    bad = []
    ok = []
    for rel, expected in baseline.items():
        path = ROOT / rel
        if not path.exists():
            bad.append(f"{rel} missing")
            continue
        got = sha256(path)
        if got != expected:
            bad.append(f"{rel} checksum mismatch")
        else:
            ok.append(rel)
    return bad, ok


def write_checksums() -> None:
    """Write current checksums as the baseline."""
    data = {}
    for rel in EXPECTED:
        path = ROOT / rel
        if path.exists():
            data[rel] = sha256(path)
    CHECKSUMS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_module(name: str) -> list[str]:
    """Import the named module's parts. Return error strings."""
    errors = []
    targets = MODULES.get(name)
    if not targets:
        return [f"unknown module {name}"]
    for mod in targets:
        try:
            importlib.import_module(mod)
        except Exception as exc:
            errors.append(f"{mod}: {exc}")
    return errors


def run(mode: str | None = None) -> int:
    """Run the requested debug. mode is None, 'complete', or a module name."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    lines = [f"Foolbook debug  {stamp}", f"mode: {mode or 'default'}"]

    missing, present = check_files()
    lines.append(f"files: {len(present)} present, {len(missing)} missing")
    for m in missing:
        lines.append(f"  missing {m}")

    bad, ok = check_checksums()
    if CHECKSUMS.exists():
        lines.append(f"checksums: {len(ok)} ok, {len(bad)} bad")
        for b in bad:
            lines.append(f"  {b}")
    else:
        lines.append("checksums: no baseline (run --debug complete to write one)")

    rc = 0
    if mode == "complete":
        write_checksums()
        lines.append(f"wrote {CHECKSUMS.name}")
        for name in MODULES:
            errs = check_module(name)
            if errs:
                for e in errs:
                    lines.append(f"  {e}")
                rc = 1
            else:
                lines.append(f"{name}: ok")
        if missing or bad:
            rc = 1
    elif mode and mode in MODULES:
        errs = check_module(mode)
        if errs:
            for e in errs:
                lines.append(f"  {e}")
            rc = 1
        else:
            lines.append(f"{mode}: ok")
    elif mode and mode not in MODULES and mode != "complete":
        lines.append(f"unknown debug target: {mode}")
        lines.append(f"known: complete, {', '.join(MODULES)}")
        rc = 2
    else:
        if missing or bad:
            rc = 1

    lines.append(f"exit: {rc}")
    report = "\n".join(lines) + "\n"
    print(report, end="")

    dest = HERE / f"db-{stamp}"
    dest.write_text(report, encoding="utf-8")
    print(f"wrote {dest.relative_to(ROOT)}")
    return rc


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    mode = argv[0] if argv else None
    return run(mode)


if __name__ == "__main__":
    raise SystemExit(main())
