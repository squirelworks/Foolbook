"""Foolbook GUI viewer.

Serves a local browser interface. Uses the same loader and engine as the CLI.

  python3 -m foolbook --gui path/to/book.tbk
  python3 -m viewer.gui path/to/book.tbk
"""

from __future__ import annotations

import json
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine.loader import load
from foolbook.model import RuntimeState
from engine.engine import goto
from progress.progress import Progress


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Foolbook</title>
<style>
  /* shared */
  body { margin: 0; display: flex; height: 100vh; }
  #sidebar { overflow-y: auto; }
  #pages { list-style: none; padding: 0; margin: 0; }
  #pages li { cursor: pointer; }
  #main { flex: 1; display: flex; flex-direction: column; }
  #content { flex: 1; overflow-y: auto; }
  #nav button, .choice { cursor: pointer; }
  #themebar { position: absolute; top: 4px; right: 8px; z-index: 2; }

  /* default: Windows 95 */
  body.win95 {
    font-family: "MS Sans Serif", Tahoma, sans-serif;
    font-size: 11px;
    background: #c0c0c0;
  }
  body.win95 #sidebar {
    width: 180px;
    background: #c0c0c0;
    border-right: 2px solid #808080;
    color: #000;
  }
  body.win95 #sidebar h1 {
    margin: 0; padding: 4px 6px;
    background: #000080; color: #fff;
    font-weight: bold; font-size: 12px;
  }
  body.win95 #pages li {
    padding: 2px 6px;
    border-bottom: 1px solid #dfdfdf;
  }
  body.win95 #pages li:hover { background: #000080; color: #fff; }
  body.win95 #pages li.active { background: #000080; color: #fff; }
  body.win95 #content {
    background: #fff;
    margin: 4px;
    border: 2px inset #fff;
    padding: 8px;
  }
  body.win95 #content h2 { margin: 0 0 8px 0; font-size: 14px; }
  body.win95 #nav {
    background: #c0c0c0;
    padding: 4px;
    border-top: 2px solid #fff;
  }
  body.win95 button, body.win95 .choice {
    font-family: inherit; font-size: 11px;
    background: #c0c0c0; color: #000;
    border: 2px outset #fff;
    padding: 2px 10px; margin-right: 4px;
  }
  body.win95 button:active, body.win95 .choice:active {
    border-style: inset;
  }
  body.win95 #themebar button { font-size: 10px; padding: 1px 6px; }

  /* modern */
  body.modern {
    font-family: system-ui, sans-serif;
    background: #fafafa;
  }
  body.modern #sidebar {
    width: 220px;
    background: #1e1e1e;
    color: #ddd;
  }
  body.modern #sidebar h1 {
    font-size: 1rem; padding: 12px; margin: 0; background: #111;
  }
  body.modern #pages li {
    padding: 6px 12px;
    border-bottom: 1px solid #333;
  }
  body.modern #pages li:hover, body.modern #pages li.active { background: #333; }
  body.modern #content { padding: 24px; }
  body.modern #content h2 { margin-top: 0; }
  body.modern #nav {
    padding: 12px 24px;
    background: #f4f4f4;
    border-top: 1px solid #ddd;
  }
  body.modern button, body.modern .choice {
    margin-right: 8px; padding: 6px 14px;
    border: 1px solid #ccc; border-radius: 4px;
    background: #fff;
  }
  body.modern #themebar button { padding: 4px 8px; }
</style>
</head>
<body class="win95">
  <div id="themebar">
    <button onclick="setTheme('win95')">Classic</button>
    <button onclick="setTheme('modern')">Modern</button>
  </div>
  <div id="sidebar">
    <h1>Foolbook</h1>
    <ul id="pages"></ul>
  </div>
  <div id="main">
    <div id="content"></div>
    <div id="nav"></div>
  </div>
<script>
let book = null;

function setTheme(name) {
  document.body.className = name;
  localStorage.setItem('foolbook-theme', name);
}
(function() {
  const saved = localStorage.getItem('foolbook-theme');
  if (saved) setTheme(saved);
})();

async function loadBook() {
  const r = await fetch('/api/book');
  book = await r.json();
  const ul = document.getElementById('pages');
  ul.innerHTML = '';
  book.pages.forEach((p, i) => {
    const li = document.createElement('li');
    li.textContent = p.id;
    li.onclick = () => show(i);
    ul.appendChild(li);
  });
  let start = 0;
  if (book.last_page) {
    const idx = book.pages.findIndex(p => p.id === book.last_page);
    if (idx >= 0) start = idx;
  }
  show(start);
}

function show(i) {
  const p = book.pages[i];
  fetch('/api/visit?page=' + encodeURIComponent(p.id));
  document.querySelectorAll('#pages li').forEach((el, j) => {
    el.classList.toggle('active', j === i);
    if (book.visited && book.visited.indexOf(book.pages[j].id) >= 0) {
      el.style.opacity = '0.6';
    }
  });
  const c = document.getElementById('content');
  c.innerHTML = '';
  const h = document.createElement('h2');
  h.textContent = p.id;
  c.appendChild(h);
  (p.text || []).forEach(t => {
    const d = document.createElement('p');
    d.textContent = t;
    c.appendChild(d);
  });
  if (p.quiz && p.quiz.choices) {
    const q = document.createElement('div');
    q.className = 'quiz';
    p.quiz.choices.forEach(ch => {
      const b = document.createElement('button');
      b.className = 'choice';
      b.textContent = ch.label;
      b.onclick = () => {
        fetch('/api/answer?page=' + encodeURIComponent(p.id) + '&correct=' + (ch.correct ? '1' : '0'));
        alert(ch.correct ? 'Correct' : 'Incorrect');
        const target = ch.correct ? p.quiz.next : p.quiz.again;
        if (target) {
          const idx = book.pages.findIndex(x => x.id.toLowerCase() === target.toLowerCase());
          if (idx >= 0) show(idx);
        }
      };
      q.appendChild(b);
    });
    c.appendChild(q);
  }
  const nav = document.getElementById('nav');
  nav.innerHTML = '';
  const items = p.items && p.items.length ? p.items : (p.jumps || []).map(j => ({label: j, page: j}));
  items.forEach(it => {
    const b = document.createElement('button');
    b.textContent = it.label || it.page;
    b.onclick = () => {
      const idx = book.pages.findIndex(x => x.id === it.page);
      if (idx >= 0) show(idx);
    };
    nav.appendChild(b);
  });
  if (i > 0) {
    const finish = document.createElement('button');
    finish.textContent = 'Finish';
    finish.onclick = () => {
      fetch('/api/finish').then(r => r.json()).then(s => {
        const pct = (s.percent === null || s.percent === undefined) ? 'no quiz' : s.percent + '%';
        document.getElementById('content').innerHTML =
          '<h2>Course closed</h2><p>Score saved: ' + pct + '.</p><p>You can close this window.</p>';
        document.getElementById('nav').innerHTML = '';
      });
    };
    nav.appendChild(finish);
  }
  if (!items.length) {
    if (i > 0) {
      const back = document.createElement('button');
      back.textContent = 'Back';
      back.onclick = () => show(i - 1);
      nav.appendChild(back);
    }
    if (i + 1 < book.pages.length) {
      const next = document.createElement('button');
      next.textContent = 'Next';
      next.onclick = () => show(i + 1);
      nav.appendChild(next);
    }
  }
}

loadBook();
</script>
</body>
</html>
"""



_LOCALE_ALIASES = {"tlh": "klingon", "tlhingan": "klingon"}


def _apply_locale(book, path: Path, locale: str):
    """Overlay a sibling <stem>.<locale>.json onto the book.

    Missing overlay leaves the course as written. Item and quiz labels
    overlay by index so the page targets stay in the book.
    """
    import json
    key = _LOCALE_ALIASES.get(locale.strip().lower(), locale.strip().lower())
    if not key or key in ("en", "en_us", "en-us"):
        return False
    overlay = path.with_name(f"{path.stem}.{key}.json")
    if not overlay.exists():
        return False
    try:
        data = json.loads(overlay.read_text(encoding="utf-8"))
    except Exception:
        return False
    if data.get("title"):
        book.title = data["title"]
    pages = {p.get("id"): p for p in (data.get("pages") or {}).values()} if isinstance(data.get("pages"), dict) else {}
    if isinstance(data.get("pages"), dict):
        pages = data["pages"]
    for page in book.pages:
        loc = pages.get(page.id) or {}
        if loc.get("text"):
            page.text = list(loc["text"])
        for i, item in enumerate(loc.get("items") or []):
            if i < len(page.items) and item.get("label"):
                page.items[i]["label"] = item["label"]
        quiz = loc.get("quiz") or {}
        if page.quiz and quiz.get("choices"):
            for i, choice in enumerate(quiz["choices"]):
                if i < len(page.quiz.get("choices") or []) and choice.get("label"):
                    page.quiz["choices"][i]["label"] = choice["label"]
    return True


def book_to_json(book, progress=None, course_id="") -> dict:
    visited = progress.visited(course_id) if progress else []
    last = progress.last_page(course_id) if progress else ""
    return {
        "title": book.title,
        "last_page": last,
        "visited": visited,
        "pages": [
            {
                "id": p.id,
                "text": p.text,
                "items": p.items,
                "jumps": p.jumps,
                "quiz": p.quiz,
            }
            for p in book.pages
        ],
    }


def serve(path: str | Path | None = None, port: int = 1337, student: str = "", locale: str = "", course: str = "") -> None:
    """Long-lived server. Sessions switch books without restart.

    One process holds multiple sessions. A session is a student plus a
    course. Idle sessions drop after five minutes. /api/load creates or
    replaces a session. Finish marks the course done; it does not exit.
    """
    sessions: dict[str, dict] = {}
    lock = threading.Lock()
    IDLE = 300  # seconds

    def touch(sid: str):
        with lock:
            if sid in sessions:
                sessions[sid]["seen"] = time.time()

    def load_session(sid: str, book_path: Path, student_path: str, loc: str, cid: str):
        book = load(book_path)
        if loc:
            _apply_locale(book, book_path, loc)
        course_id = cid or book_path.stem
        prog = Progress(Path(student_path) if student_path else _progress_path())
        prog.touch(course_id)
        with lock:
            sessions[sid] = {
                "book": book,
                "progress": prog,
                "course_id": course_id,
                "path": book_path,
                "seen": time.time(),
            }
        return course_id

    def get(sid: str):
        with lock:
            s = sessions.get(sid)
            if s:
                s["seen"] = time.time()
            return s

    def expire():
        while True:
            time.sleep(30)
            now = time.time()
            with lock:
                dead = [k for k, v in sessions.items() if now - v["seen"] > IDLE]
                for k in dead:
                    del sessions[k]

    threading.Thread(target=expire, daemon=True).start()

    # Optional first book
    if path:
        load_session("default", Path(path), student, locale, course)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _sid(self, u):
            from urllib.parse import parse_qs
            return (parse_qs(u.query).get("s") or ["default"])[0]

        def do_GET(self):
            u = urlparse(self.path)
            sid = self._sid(u)
            if u.path == "/api/load":
                from urllib.parse import parse_qs
                q = parse_qs(u.query)
                bp = (q.get("path") or [""])[0]
                st = (q.get("student") or [""])[0]
                loc = (q.get("locale") or [""])[0]
                cid = (q.get("course") or [""])[0]
                nsid = (q.get("s") or ["default"])[0]
                if not bp or not Path(bp).exists():
                    self.send_response(400)
                    self.end_headers()
                    return
                load_session(nsid, Path(bp), st, loc, cid)
                body = json.dumps({"ok": True, "session": nsid}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            sess = get(sid)
            if u.path in ("/", "/index.html"):
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if not sess:
                self.send_response(404)
                self.end_headers()
                return
            book = sess["book"]
            progress = sess["progress"]
            course_id = sess["course_id"]
            if u.path == "/api/book":
                payload = json.dumps(book_to_json(book, progress, course_id)).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            elif u.path == "/api/visit":
                from urllib.parse import parse_qs
                page = (parse_qs(u.query).get("page") or [""])[0]
                if page:
                    progress.mark_page(course_id, page)
                self.send_response(204)
                self.end_headers()
            elif u.path == "/api/answer":
                from urllib.parse import parse_qs
                q = parse_qs(u.query)
                page = (q.get("page") or [""])[0]
                correct = (q.get("correct") or ["0"])[0] == "1"
                score = progress.record_answer(course_id, page, correct) if page else {}
                body = json.dumps(score).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif u.path == "/api/finish":
                progress.complete(course_id)
                score = progress.course_score(course_id)
                body = json.dumps(score).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                # Drop the session; server stays up
                with lock:
                    sessions.pop(sid, None)
            else:
                self.send_response(404)
                self.end_headers()

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        if exc.errno in (98, 48):
            print("Server already running")
            raise SystemExit(1)
        raise
    url = f"http://127.0.0.1:{port}/"
    print(f"Foolbook server on {url}")
    if path:
        print(f"Loaded {Path(path).name}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()



def _open_browser(url: str) -> bool:
    """Open the viewer.

    xdg-open first. webbrowser.open goes straight at Chrome on this
    desktop and dies in the zygote (broken pipe), so it is the fallback.
    """
    import shutil
    import subprocess
    for cmd in ("xdg-open", "gio"):
        if shutil.which(cmd):
            try:
                args = [cmd, url] if cmd == "xdg-open" else [cmd, "open", url]
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue
    try:
        return bool(webbrowser.open(url, new=2))
    except Exception:
        return False


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def main(argv: list[str] | None = None, port: int = 1337, student: str = "", locale: str = "", course: str = "") -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if "--port" in argv:
        i = argv.index("--port")
        if i + 1 >= len(argv):
            print("--port needs a number")
            return 2
        try:
            port = int(argv[i + 1])
        except ValueError:
            print(f"--port needs a number, got {argv[i + 1]}")
            return 2
        del argv[i:i + 2]
    if "--student" in argv:
        i = argv.index("--student")
        if i + 1 >= len(argv):
            print("--student needs a path")
            return 2
        student = argv[i + 1]
        del argv[i:i + 2]
    if "--locale" in argv:
        i = argv.index("--locale")
        if i + 1 >= len(argv):
            print("--locale needs an id")
            return 2
        locale = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print("usage: python3 -m viewer.gui [--port N] <book.tbk|book.json>")
        return 2
    path = Path(argv[0].replace("\\", "/")).expanduser()
    if not path.exists():
        print(f"not found: {path}")
        return 1
    serve(path, port, student, locale, course)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
