"""Foolbook GUI viewer.

Serves a local browser interface. Uses the same loader and engine as the CLI.

  python3 -m foolbook --gui path/to/book.tbk
  python3 -m viewer.gui path/to/book.tbk
"""

from __future__ import annotations

import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine.loader import load
from main.model import RuntimeState
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


def serve(path: str | Path, port: int = 1337) -> None:
    book = load(path)
    course_id = Path(path).stem
    progress = Progress(_progress_path())
    progress.touch(course_id)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif u.path == "/api/book":
                payload = json.dumps(book_to_json(book, progress, course_id)).encode("utf-8")
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
            else:
                self.send_response(404)
                self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Foolbook GUI  {book.title or Path(path).name}  ({len(book.pages)} pages)")
    print(f"Open {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        server.shutdown()


def _progress_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python3 -m viewer.gui <book.tbk|book.json>")
        return 2
    path = Path(argv[0].replace("\\", "/")).expanduser()
    if not path.exists():
        print(f"not found: {path}")
        return 1
    serve(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
