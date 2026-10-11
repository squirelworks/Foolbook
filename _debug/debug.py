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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CHECKSUMS = HERE / "checksums.json"

EXPECTED = [
    "foolbook/__init__.py",
    "foolbook/__main__.py",
    "foolbook/model.py",
    "foolbook.py",
    "engine/__init__.py",
    "engine/engine.py",
    "engine/loader.py",
    "engine/tbk.py",
    "engine/openscript.py",
    "viewer/__init__.py",
    "viewer/cli.py",
    "viewer/gui.py",
    "author/__init__.py",
    "author/formats.py",
    "author/gui.py",
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
    "author": ["author.formats"],
    "menu": ["menu.menu"],
    "progress": ["progress.progress"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def check_files() -> tuple[list[str], list[str]]:
    missing = []
    present = []
    for rel in EXPECTED:
        if (ROOT / rel).exists():
            present.append(rel)
        else:
            missing.append(rel)
    return missing, present


def check_checksums() -> tuple[list[str], list[str]]:
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
    data = {}
    for rel in EXPECTED:
        path = ROOT / rel
        if path.exists():
            data[rel] = sha256(path)
    CHECKSUMS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_module(name: str) -> list[str]:
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
    print("Foolbook debug")
    missing, present = check_files()
    print(f"  files: {len(present)} present, {len(missing)} missing")
    for m in missing:
        print(f"    missing {m}")

    bad, ok = check_checksums()
    if CHECKSUMS.exists():
        print(f"  checksums: {len(ok)} ok, {len(bad)} bad")
        for b in bad:
            print(f"    {b}")
    else:
        print("  checksums: no baseline (run --debug complete to write one)")

    if mode == "complete":
        write_checksums()
        print(f"  wrote {CHECKSUMS.name}")
        for name in MODULES:
            errs = check_module(name)
            if errs:
                for e in errs:
                    print(f"    {e}")
            else:
                print(f"  {name}: ok")
        return 1 if missing or bad else 0

    if mode and mode in MODULES:
        errs = check_module(mode)
        if errs:
            for e in errs:
                print(f"    {e}")
            return 1
        print(f"  {mode}: ok")
        return 0

    if mode and mode not in MODULES and mode != "complete":
        print(f"  unknown debug target: {mode}")
        print(f"  known: complete, {', '.join(MODULES)}")
        return 2

    return 1 if missing or bad else 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    mode = argv[0] if argv else None
    return run(mode)


if __name__ == "__main__":
    raise SystemExit(main())
