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
from foolbook.model import RuntimeState
from engine.engine import goto


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Foolbook</title>
<style>
  body { margin: 0; font-family: system-ui, sans-serif; display: flex; height: 100vh; }
  #sidebar { width: 220px; background: #1e1e1e; color: #ddd; overflow-y: auto; }
  #sidebar h1 { font-size: 1rem; padding: 12px; margin: 0; background: #111; }
  #pages { list-style: none; padding: 0; margin: 0; }
  #pages li { padding: 6px 12px; cursor: pointer; border-bottom: 1px solid #333; }
  #pages li:hover, #pages li.active { background: #333; }
  #main { flex: 1; display: flex; flex-direction: column; }
  #content { flex: 1; padding: 24px; overflow-y: auto; }
  #content h2 { margin-top: 0; }
  #nav { padding: 12px 24px; background: #f4f4f4; border-top: 1px solid #ddd; }
  button { margin-right: 8px; padding: 6px 14px; }
  .quiz { margin-top: 16px; }
  .choice { display: block; margin: 4px 0; }
</style>
</head>
<body>
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
let index = 0;

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
  show(0);
}

function show(i) {
  index = i;
  const p = book.pages[i];
  document.querySelectorAll('#pages li').forEach((el, j) => {
    el.classList.toggle('active', j === i);
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


def book_to_json(book) -> dict:
    return {
        "title": book.title,
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


def serve(path: str | Path, port: int = 8765) -> None:
    book = load(path)
    payload = json.dumps(book_to_json(book)).encode("utf-8")

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
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
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


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python3 -m viewer.gui <book.tbk|book.json>")
        return 2
    path = Path(argv[0])
    if not path.exists():
        print(f"not found: {path}")
        return 1
    serve(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
