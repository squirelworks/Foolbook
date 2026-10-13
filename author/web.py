"""Browser author.

The desktop slide editor stays at author.gui. This is the one that
runs without Tk, which is what a GitHub install can actually open.

  python3 -m foolbook --author
  python3 -m foolbook --author path/to/book.fbk
  python3 -m foolbook --author --desktop     # the Tk window
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from author.document import blank_book
from author.formats import load as load_book
from author.formats import save_book


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Foolbook Author</title>
<style>
  body { margin: 0; display: flex; height: 100vh;
    font-family: "MS Sans Serif", Tahoma, sans-serif; font-size: 11px; background: #c0c0c0; }
  #side { width: 180px; display: flex; flex-direction: column; border-right: 2px solid #808080; }
  #side h1 { margin: 0; padding: 4px 6px; background: #000080; color: #fff; font-size: 12px; }
  #pages { list-style: none; padding: 0; margin: 0; overflow-y: auto; flex: 1; }
  #pages li { padding: 2px 6px; cursor: pointer; border-bottom: 1px solid #dfdfdf; }
  #pages li.active { background: #000080; color: #fff; }
  #main { flex: 1; display: flex; flex-direction: column; padding: 8px; gap: 6px; }
  label { display: block; }
  input, textarea { font: inherit; width: 100%; box-sizing: border-box; }
  textarea { flex: 1; min-height: 160px; }
  .row { display: flex; gap: 8px; }
  .row label { flex: 1; }
  button { font: inherit; background: #c0c0c0; border: 2px outset #fff; padding: 2px 10px; }
  #bar { display: flex; gap: 4px; align-items: center; }
  #status { margin-left: auto; }
</style>
</head>
<body>
  <div id="side">
    <h1>Author</h1>
    <ul id="pages"></ul>
    <div style="padding:4px">
      <button type="button" id="add">Add page</button>
      <button type="button" id="del">Delete</button>
    </div>
  </div>
  <div id="main">
    <div id="bar">
      <button type="button" id="save">Save</button>
      <span id="status"></span>
    </div>
    <label>Title <input id="title"></label>
    <div class="row">
      <label>Page id <input id="pid"></label>
      <label>Next <input id="next"></label>
      <label>Back <input id="back"></label>
    </div>
    <label>Text. A blank line starts a paragraph. A line starting with - or * is a list.
      <textarea id="text"></textarea>
    </label>
  </div>
<script>
let book = null;
let index = 0;

function navOf(page) {
  let nxt = "", back = "";
  for (const item of page.items || []) {
    const label = (item.label || "").toLowerCase();
    if (label === "next") nxt = item.page || "";
    else if (label === "back") back = item.page || "";
  }
  return [nxt, back];
}

function setNav(page, nxt, back) {
  const kept = (page.items || []).filter(item => {
    const label = (item.label || "").toLowerCase();
    return label !== "next" && label !== "back";
  });
  const items = [];
  if (nxt.trim()) items.push({label: "Next", page: nxt.trim()});
  if (back.trim()) items.push({label: "Back", page: back.trim()});
  page.items = items.concat(kept);
}

function freshId() {
  const used = new Set((book.pages || []).map(p => p.id));
  let n = 0;
  while (true) {
    const id = n === 0 ? "P0" : "P" + (n * 100);
    if (!used.has(id)) return id;
    n++;
  }
}

function readForm() {
  const page = book.pages[index];
  if (!page) return;
  book.title = document.getElementById("title").value;
  page.id = document.getElementById("pid").value.trim() || page.id || "P0";
  const raw = document.getElementById("text").value.trim();
  page.text = raw ? raw.split(/\\n\\n/).map(b => b.trim()).filter(Boolean) : [];
  setNav(page, document.getElementById("next").value, document.getElementById("back").value);
}

function show(i, flush) {
  if (flush && book.pages[index]) readForm();
  index = i;
  const page = book.pages[i];
  document.getElementById("title").value = book.title || "";
  document.getElementById("pid").value = page.id || "";
  const nav = navOf(page);
  document.getElementById("next").value = nav[0];
  document.getElementById("back").value = nav[1];
  document.getElementById("text").value = (page.text || []).join("\\n\\n");
  const ul = document.getElementById("pages");
  ul.innerHTML = "";
  book.pages.forEach((p, j) => {
    const li = document.createElement("li");
    li.textContent = p.id || "?";
    li.className = j === index ? "active" : "";
    li.onclick = () => show(j, true);
    ul.appendChild(li);
  });
}

async function openBook() {
  const r = await fetch("/api/book");
  book = await r.json();
  if (!book.pages || !book.pages.length) book.pages = [{id: "P0", text: ["New slide"], items: []}];
  index = 0;
  show(0, false);
  document.getElementById("status").textContent = book.path || "New book";
}

document.getElementById("add").onclick = () => {
  readForm();
  book.pages.push({id: freshId(), text: ["New slide"], items: [], widgets: []});
  show(book.pages.length - 1, false);
};

document.getElementById("del").onclick = () => {
  if (book.pages.length <= 1) return;
  book.pages.splice(index, 1);
  show(Math.min(index, book.pages.length - 1), false);
};

document.getElementById("save").onclick = async () => {
  readForm();
  const r = await fetch("/api/book", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(book),
  });
  const data = await r.json();
  document.getElementById("status").textContent = r.ok ? ("Saved " + data.path) : (data.error || "Save failed");
  if (data.path) book.path = data.path;
};

openBook();
</script>
</body>
</html>
"""


def serve(path: Path | None, port: int = 1340) -> None:
    state = {"book": blank_book(), "path": None}
    if path is not None:
        state["book"] = load_book(path)
        state["book"].setdefault("pages", [blank_book()["pages"][0]])
        state["path"] = Path(path).resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
                return
            if u.path == "/api/book":
                payload = dict(state["book"])
                if state["path"]:
                    payload["path"] = str(state["path"])
                self._send(200, json.dumps(payload).encode("utf-8"), "application/json")
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            u = urlparse(self.path)
            if u.path != "/api/book":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length") or 0)
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send(400, b'{"error":"not json"}', "application/json")
                return
            if not isinstance(data, dict) or not isinstance(data.get("pages"), list) or not data["pages"]:
                self._send(400, b'{"error":"book needs pages"}', "application/json")
                return
            data.pop("path", None)
            dest = state["path"] or Path.cwd() / "new-book.fbk"
            saved = save_book(dest, data)
            state["book"] = data
            state["path"] = saved.with_suffix(".fbk").resolve()
            body = json.dumps({"ok": True, "path": str(state["path"])}).encode("utf-8")
            self._send(200, body, "application/json")

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        if getattr(exc, "errno", None) in (98, 48):
            print("Author already running, cannot start a new instance")
            raise SystemExit(1)
        raise
    url = f"http://127.0.0.1:{port}/"
    name = state["path"].name if state["path"] else "New book"
    print(f"Foolbook Author  {name}")
    print(f"Open {url}")
    _open_browser(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        server.shutdown()


def _open_browser(url: str) -> None:
    import shutil
    import subprocess
    import webbrowser
    for cmd in ("xdg-open", "gio"):
        if shutil.which(cmd):
            try:
                args = [cmd, url] if cmd == "xdg-open" else [cmd, "open", url]
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                continue
    try:
        webbrowser.open(url, new=2)
    except Exception:
        print(f"Browser did not open. Go to {url}")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    port = 1340
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
    path = None
    if argv:
        path = Path(argv[0].replace("\\", "/")).expanduser()
        if path.suffix.lower() not in (".fbk", ".fsk", ".json"):
            print("The browser author edits .fbk, .fsk, and .json.")
            return 2
        if not path.exists():
            print(f"not found: {path}")
            return 1
    serve(path, port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
