"""Run quiz specs against the real viewer and print PASS or FAIL for each.

    python -m tools.quiz_check.run --courses DIR --all
    python -m tools.quiz_check.run --courses DIR --type letter
    python -m tools.quiz_check.run --courses DIR --spec NAME [--book STEM --page P1234]
    python -m tools.quiz_check.run --list

--book / --page replace the book and the first page a chosen spec starts on, so the same
sequence can be tried on any other book of the catalogue.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .specs import SPECS


def start_xvfb():
    """A private X server on a free display. Returns (process, display)."""
    r, w = os.pipe()
    proc = subprocess.Popen(["Xvfb", "-displayfd", str(w), "-screen", "0", "1280x900x24", "-nolisten", "tcp"],
                            pass_fds=(w,), stderr=subprocess.DEVNULL)
    os.close(w)
    number = os.read(r, 16).decode().strip()
    os.close(r)
    return proc, ":" + number


def select(args):
    chosen = [s for s in SPECS if (args.all or s["name"] in (args.spec or []) or s.get("type") in (args.type or []))]
    out = []
    for spec in chosen:
        spec = copy.deepcopy(spec)
        if args.book:
            spec["book"] = args.book
        if args.page and spec["steps"] and "goto" in spec["steps"][0]:
            spec["steps"][0]["goto"] = args.page
        out.append(spec)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--courses", default=os.environ.get("FOOLBOOK_COURSES", ""))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--type", action="append")
    ap.add_argument("--spec", action="append")
    ap.add_argument("--book")
    ap.add_argument("--page")
    ap.add_argument("--shots", default="quiz_check_shots")
    ap.add_argument("--json", help="write the full result list here")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    if args.list:
        for s in SPECS:
            print(f"{s['name']:32} {s['type']:12} {s['book']:10} {s.get('doc', '')}")
        return 0
    if not args.courses:
        ap.error("--courses (or FOOLBOOK_COURSES) is required")
    specs = select(args)
    if not specs:
        ap.error("no spec chosen: use --all, --type or --spec")
    root = Path(__file__).resolve().parents[2]
    own = None
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(root) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    if not env.get("DISPLAY"):
        own, env["DISPLAY"] = start_xvfb()
    results = []
    try:
        for spec in specs:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
                json.dump(spec, fh)
            try:
                p = subprocess.run([sys.executable, "-m", "tools.quiz_check.child", fh.name, args.courses, args.shots],
                                   capture_output=True, text=True, env=env, cwd=root, timeout=args.timeout)
                line = next((l for l in p.stdout.splitlines() if l.startswith("RESULT ")), None)
                res = json.loads(line[7:]) if line else {"spec": spec["name"], "type": spec["type"], "status": "FAIL",
                                                         "errors": [p.stderr[-800:] or "no result"], "steps": []}
            except subprocess.TimeoutExpired:
                res = {"spec": spec["name"], "type": spec["type"], "status": "FAIL", "errors": ["timeout"], "steps": []}
            finally:
                os.unlink(fh.name)
            results.append(res)
            why = ""
            if res["status"] != "PASS":
                for r in res.get("steps", []):
                    if r.get("fails"):
                        why = f"step {r['n']} {json.dumps(r['step'])[:90]}: " + "; ".join(r["fails"])
                        break
                why = why or "; ".join(res.get("errors") or [])[:200]
            print(f"{res['status']:4} {spec['name']:32} {spec['type']:10} {spec['book']:10} {why}", flush=True)
    finally:
        if own is not None:
            own.terminate()
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))
    return 0 if all(r["status"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
