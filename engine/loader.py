"""Load a book into the Foolbook model.

Currently supports:
- .json / .fbk / .fsk
- .pdf .ppt .pptx .doc .docx .odt as text pages
- A TBX Book.xml (or any XML in that folder that carries the TBX namespace)
- Raw .tbk via the built-in parser, with handlers decoded from the page stream
"""

from __future__ import annotations

import json
from pathlib import Path

from foolbook.model import Book, Page, Handler


# Optional override set by --bin. Only used when decoding .tbk / .sbk.
_BIN_OVERRIDE: Path | None = None
# Decoded source is written to _debug/decoded only when this is set.
_KEEP_DECODED = False


def set_keyword_bin(path: str | Path | None) -> None:
    """Use this keyword resource instead of the clean table when decoding .tbk/.sbk."""
    global _BIN_OVERRIDE
    _BIN_OVERRIDE = Path(path) if path else None


def set_keep_decoded(keep: bool) -> None:
    """Keep decoded .tbk/.sbk source on disk. Only set by --debug."""
    global _KEEP_DECODED
    _KEEP_DECODED = bool(keep)


def find_book(name: str, near: str | Path) -> Path | None:
    """Find a book named by a jump.

    Looks beside the loaded file, then one directory up, then core/.
    A lesson names nida81.tbk and the system books as .sbk. The course
    ships those as .fbk and .fsk. A settled export is taken before the
    original file and before the stub in core/.
    """
    stem = Path(name).stem
    near = Path(near)
    here = near.parent if near.is_file() else near
    below = here.parent
    root = Path(__file__).resolve().parents[1]
    dirs = []

    def add(directory: Path) -> None:
        if directory not in dirs and directory.is_dir():
            dirs.append(directory)

    add(here)
    add(below)
    # A course folder often sits next to the system books, not inside them.
    for base in (here, below):
        if not base.is_dir():
            continue
        try:
            children = [child for child in base.iterdir() if child.is_dir() and not child.name.startswith(".")]
        except OSError:
            children = []
        for child in children[:40]:
            add(child)
    add(root / "core")
    asked = Path(name).suffix.lower()
    # The shell is an .fbk. A system book is an .fsk. Either one, once
    # it is a real export, wins over a .tbk, a .sbk, and the core stub.
    exports = (".fsk", ".fbk") if asked == ".sbk" else (".fbk", ".fsk")
    for suf in exports:
        for directory in dirs:
            found = _named(directory, stem, suf)
            if found is not None and _usable_export(found):
                return found
    order = []
    for suf in (asked, ".fbk", ".fsk", ".tbk", ".sbk", ".json"):
        if suf and suf not in order:
            order.append(suf)
    # The original file, in any of these directories, before a stub.
    # A settled export beside that file is the same book, already drawn.
    for suf in order:
        for directory in dirs:
            found = _named(directory, stem, suf)
            if found is None:
                continue
            if suf in (".tbk", ".sbk"):
                exported = _settled_beside(found)
                if exported is not None:
                    return exported
            return found
    return None


def _named(directory: Path, stem: str, suf: str) -> Path | None:
    """A book file, ignoring the case Linux would otherwise keep."""
    direct = directory / f"{stem}{suf}"
    if direct.exists():
        return direct
    if not directory.is_dir():
        return None
    want = f"{stem}{suf}".lower()
    for child in directory.iterdir():
        if child.is_file() and child.name.lower() == want:
            return child
    return None


def _settled_beside(original: Path) -> Path | None:
    """An export sitting next to the .tbk or .sbk, if it is a real one."""
    for suf in (".fbk", ".fsk"):
        found = _named(original.parent, original.stem, suf)
        if found is not None and _usable_export(found):
            return found
    return None


def _usable_export(path: Path) -> bool:
    """True when the file is an export, not the old stub with no pictures.

    The export marks each page settled. A short or broken copy does not.
    """
    import zlib
    try:
        stamp = (str(path), path.stat().st_mtime_ns, path.stat().st_size)
    except OSError:
        return False
    cached = _export_ok.get(stamp)
    if cached is not None:
        return cached
    try:
        blob = path.read_bytes()
    except OSError:
        return False
    ok = False
    if len(blob) >= 6 and blob[:4] in (b"FBK1", b"FSK1"):
        payload = blob[5:]
        if blob[4] & 1:
            try:
                payload = zlib.decompress(payload)
            except zlib.error:
                payload = b""
        ok = b'"settled":true' in payload or b'"settled": true' in payload
    _export_ok[stamp] = ok
    return ok


_export_ok: dict = {}


def load(path: str | Path) -> Book:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        core = Path(__file__).resolve().parents[1] / "core" / path.name
        if core.exists():
            path = core
    if path.is_file():
        from toolbook.format import is_toolbook
        if is_toolbook(path):
            from toolbook.open import open_book
            return open_book(path)
    if path.suffix.lower() == ".json":
        return _load_json(path)
    if path.suffix.lower() in (".fbk", ".fsk", ".fsc"):
        return _load_foolbook(path)
    if path.suffix.lower() in {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".odt"}:
        from engine.office import to_book
        return _book_from_dict(path, to_book(path))
    if path.suffix.lower() in {".txt", ".text", ".md", ".markdown", ".rst", ".log", ".rtf"}:
        from engine.notes import to_book
        return _book_from_dict(path, to_book(path))
    if path.is_dir() or path.suffix.lower() in {".xml", ".zip", ".tbkx"} or path.name.lower().endswith(".tbkx.zip"):
        from engine.tbx import is_tbx, load as load_tbx
        if is_tbx(path):
            return load_tbx(path)
    return _load_tbk(path)


def _load_json(path: Path) -> Book:
    return _book_from_dict(path, json.loads(path.read_text(encoding="utf-8")))


def _load_foolbook(path: Path) -> Book:
    """Load an .fbk or .fsk envelope, compressed or not."""
    from engine.formats import unpack
    return _book_from_dict(path, unpack(path.read_bytes()))


def _handlers_of(raw: dict, name: str = "script") -> list:
    """Handlers stored as a list, or one ToolBook script to split.

    An older .fbk page stores a single script with no `to handle` line.
    That stays one handler. On a page it is the page's enterPage, so it
    runs when the page is shown. A system book from a TBKX has many.
    """
    import re
    listed = raw.get("handlers")
    if listed:
        return [
            Handler(name=h.get("name") or "", source=h.get("source") or "")
            for h in listed
            if isinstance(h, dict)
        ]
    script = raw.get("script") or ""
    if not str(script).strip():
        return []
    if re.search(r"(?im)^\s*to\s+(?:handle|get|set)\s+", str(script)):
        from engine.engine import split_handlers
        return split_handlers(str(script))
    return [Handler(name=name, source=str(script))]


def flatten_groups(shapes: list) -> list:
    """A ``group`` shape from the editor becomes its children, in its place.

    The editor stores a group as ``{"kind": "group", "name": ..., "children": [...]}``
    with each child's bounds already on the page. The reader paints and clicks
    single shapes, so the children take the group's place in paint order and
    nested groups open the same way. Every other shape is passed through as it
    is. The stored book keeps the group; only the list the reader runs is flat.
    """
    out = []
    for shape in shapes or []:
        if isinstance(shape, dict) and (shape.get("kind") or "").lower() == "group":
            out.extend(flatten_groups(shape.get("children") or []))
        else:
            out.append(shape)
    return out


def _book_from_dict(path: Path, data: dict) -> Book:
    pages = []
    for raw in data.get("pages") or []:
        pages.append(Page(
            id=raw.get("id") or raw.get("name") or "",
            text=list(raw.get("text") or []),
            items=list(raw.get("items") or []),
            jumps=list(raw.get("jumps") or []),
            quiz=raw.get("quiz"),
            handlers=_handlers_of(raw, "enterPage"),
            shapes=flatten_groups(raw.get("shapes") or []),
            raw=raw,
        ))
    return Book(
        path=str(path),
        title=data.get("title") or path.stem,
        pages=pages,
        shells=list(data.get("shells") or []),
        handlers=_handlers_of(data),
        props=dict(data.get("props") or {}),
    )


def _tbk_shapes(blob: bytes) -> list[dict]:
    """Page-blob shapes, placed by their twip bounds, in the viewer's pixel form."""
    try:
        from .place import place_page
        from .shapes import extract_shapes
    except Exception:
        return []
    laid = place_page(extract_shapes(blob))
    out = []
    for shape in laid["shapes"]:
        fill = shape.get("fill") or ""
        if shape.get("type") == "polygon":
            out.append({
                "kind": "polygon",
                "points": shape.get("pixels") or [],
                "fill": fill,
                "outline": "#000000",
            })
            continue
        at = shape.get("at") or [0, 0, 1, 1]
        out.append({
            "kind": "rect",
            "x": at[0],
            "y": at[1],
            "w": at[2],
            "h": at[3],
            "fill": fill,
            "outline": "#000000",
        })
    return out


def _words(value) -> str:
    """Shared with the note reader. Rich text becomes the words, not the font table."""
    if not value:
        return ""
    from engine.notes import plain
    return plain(str(value))


def _load_store(path: Path, file_bytes: bytes) -> Book:
    """A ToolBook 8 object store. Pages come from the book's page list."""
    from openscript_analysis.formats.tbk import read_store
    from .openscript import load_keywords
    from .polygon import to_pixel
    from .window import show_page_number

    keywords = _keywords()

    def decode(source: bytes) -> str:
        from openscript_analysis.formats.tbk.expand import decompress
        return decompress(source, keywords or load_keywords())

    stored = read_store(file_bytes, decode if keywords else None, pictures=False)
    pages = []
    for raw in stored["pages"]:
        shapes = []
        handlers = []
        text = []
        items = []
        for obj in raw["objects"]:
            shape = _store_shape(obj, to_pixel)
            if shape is None:
                continue
            show_page_number([shape], raw["id"])
            shapes.append(shape)
            if shape.get("kind") == "text" and shape.get("text") and not obj.get("hidden"):
                text.append(shape["text"])
            script = obj.get("script") or ""
            if script and not obj.get("hidden"):
                # The script stays on the object. Copying it onto the page
                # made an empty click run Next, and asked the exit question twice.
                item = _item_from_script(obj.get("name") or "", script)
                if item:
                    items.append(item)
                    shape["item"] = item
        from engine.engine import split_handlers
        from engine.place import clip_to_page
        page_size = (to_pixel(raw["size"][0]), to_pixel(raw["size"][1])) if raw.get("size") else None
        if page_size:
            shapes = clip_to_page(shapes, page_size[0], page_size[1])
        for source in (raw.get("script") or "", raw.get("background_script") or ""):
            handlers.extend(split_handlers(source))
        pages.append(Page(
            id=raw["id"],
            text=text,
            items=items,
            handlers=handlers,
            shapes=shapes,
            raw={
                "store": True,
                "props": raw.get("props") or {},
                "size": page_size,
            },
        ))
    book = Book(path=str(path), title=path.stem, pages=pages, handlers=_book_scripts(file_bytes, keywords, pages))
    book.props = _quester_props(file_bytes)
    return book


def _quester_props(data: bytes) -> dict:
    """__questerQuestionCount and the other book settings beside it.

    The value follows the name: a short header, then ``06 00 02 00``, a
    signed int16, and ``00 08``. A value that is not in that shape is left
    unread rather than guessed.
    """
    import re
    import struct

    anchor = data.find(b"__questerQuestionCount(1)\x00")
    if anchor < 0:
        return {}
    blob = data[max(0, anchor - 2500):anchor + 4000]
    found = {}
    for match in re.finditer(rb"__[A-Za-z0-9_()]+\x00", blob):
        name = match.group()[:-1].decode("latin-1")
        if not name.lower().startswith("__quester"):
            continue
        after = blob[match.end():match.end() + 14]
        at = after.find(b"\x06\x00\x02\x00")
        if at < 0 or at > 8 or at + 8 > len(after):
            continue
        if after[at + 6:at + 8] != b"\x00\x08":
            continue
        found[name] = struct.unpack_from("<h", after, at + 4)[0]
    return found


def _book_scripts(data: bytes, keywords, pages) -> list:
    """Handlers the page list does not already hold.

    A system book keeps its procedures in the file, not on the one
    title page. The export is the book, so those scripts stay.
    """
    try:
        from openscript_analysis.formats.tbk.expand import read_handlers
    except ImportError:
        return []
    from foolbook.model import Handler
    have = []
    for page in pages:
        for handler in page.handlers or []:
            text = " ".join((handler.source or "").split())
            if text:
                have.append(text)
        for shape in page.shapes or []:
            for key in ("script", "group_script"):
                text = " ".join((shape.get(key) or "").split())
                if text:
                    have.append(text)
    known = set(have)
    found = []
    seen = set()
    for item in read_handlers(data, keywords or None):
        source = item.get("source") or ""
        name = item.get("name") or ""
        key = " ".join(source.split())
        if not name or not key or key in known or key in seen:
            continue
        if any(key in script or script in key for script in have):
            continue
        seen.add(key)
        found.append(Handler(name=name, source=source, offset=item.get("offset") or 0))
    return found


def _book_keyup(data: bytes, keywords) -> list:
    """The book-level key handler. F2 asks before leaving the lesson."""
    try:
        from openscript_analysis.formats.tbk.expand import read_handlers
    except ImportError:
        return []
    from foolbook.model import Handler
    found = []
    for item in read_handlers(data, keywords or None):
        source = item.get("source") or ""
        if (item.get("name") or "").lower() != "keyup":
            continue
        if "exit the lesson" not in source.lower():
            continue
        found.append(Handler(name="keyup", source=source))
    return found


def _store_shape(obj: dict, to_pixel) -> dict | None:
    bounds = obj.get("bounds") or (0, 0, 0, 0)
    x0, y0 = to_pixel(bounds[0]), to_pixel(bounds[1])
    x1, y1 = to_pixel(bounds[2]), to_pixel(bounds[3])
    shape = {
        "kind": obj["kind"],
        "name": obj.get("name") or "",
        "x": x0,
        "y": y0,
        "w": max(1, x1 - x0),
        "h": max(1, y1 - y0),
        "text": (obj.get("text") or "").replace("\r\n", "\n").replace("\r", "\n"),
        "font": obj.get("font") or "",
        "size": int(obj["size"]) if obj.get("size") else 0,
        "bold": bool(obj.get("bold")),
        "italic": bool(obj.get("italic")),
        "fill": obj.get("fill") or "",
        "outline": obj.get("outline") or "",
        "script": obj.get("script") or "",
        "group_script": obj.get("group_script") or "",
        "align": int(obj.get("align") or 0),
        "border": int(obj["border"]) if obj.get("border") is not None else 1,
        "direct": bool(obj.get("direct")),
        # The Correct rectangle is the answer key, so Reader level hides it.
        # A text field of that name is the choice the lesson asks for.
        "visible": not (
            obj.get("hidden")
            or ((obj.get("name") or "").lower() == "correct" and obj.get("kind") != "text")
        ),
        "layer": obj.get("layer") or "page",
    }
    if obj.get("groups"):
        # Names of the groups this object is in, nearest first. hide group,
        # show group and visible of group read them.
        shape["groups"] = list(obj["groups"])
    if obj.get("marginL"):
        shape["marginL"] = to_pixel(int(obj["marginL"]))
    if obj.get("indentRest"):
        shape["indentRest"] = to_pixel(int(obj["indentRest"]))
    if obj.get("marginR"):
        shape["marginR"] = to_pixel(int(obj["marginR"]))
    if obj.get("runs"):
        shape["runs"] = obj["runs"]
    points = obj.get("points") or []
    if obj.get("kind") == "arc" and obj.get("ends"):
        shape["ends"] = [[to_pixel(x), to_pixel(y)] for x, y in obj["ends"]]
    elif points:
        shape["points"] = [[to_pixel(x), to_pixel(y)] for x, y in points]
        shape["kind"] = obj["kind"] if obj["kind"] in ("polygon", "line") else "line"
    later = obj.get("later")
    if later:
        # The bitmap stays in the file until this page is shown.
        shape["later"] = tuple(later)
        shape["transparent"] = bool(obj.get("transparent"))
        shape["edge"] = obj.get("kind") == "rect"
        return shape
    picture = _png(obj.get("bmp"))
    if picture:
        shape["kind"] = "image"
        shape["data"] = picture
        if obj.get("transparent"):
            shape["transparent"] = True
        elif obj.get("kind") == "rect":
            shape["edge"] = True
    invert = _png(obj.get("invert_bmp"))
    if invert:
        shape["invert_data"] = invert
    chosen = _png(obj.get("checked_bmp"))
    if chosen:
        # The face a choice turns on. The page does not start on it.
        shape["checked_data"] = chosen
    return shape


def _png(blob: bytes | None, transparent: bool = False, edge: bool = False) -> str:
    """The bitmap as it is stored in the book, not a 32-bit PNG.

    A transparent button and a white mat are marked on the shape. The
    viewer applies them when the page is drawn. Baking either one into
    a PNG made a 2 MB book into a 20 MB book.
    """
    del transparent, edge
    if not blob or blob[:2] != b"BM":
        return ""
    import base64
    return base64.b64encode(blob).decode("ascii")


_drawn: dict = {}
_open_stores: dict = {}


def realize(path: str | Path, shapes: list[dict]) -> None:
    """Draw the pictures on this page. The rest of the book stays unread."""
    if not path or not shapes:
        return
    pending = [shape for shape in shapes if shape.get("later") and not shape.get("data")]
    if not pending:
        return
    store = _open_store(path)
    if store is None:
        return
    key = str(Path(path))
    for shape in pending:
        later = tuple(shape["later"])
        cached = _drawn.get((key, later))
        if cached is None:
            bmp, invert, checked = _later_bmps(store, later)
            cached = (
                _png(bmp),
                _png(invert),
                _png(checked),
            )
            _drawn[(key, later)] = cached
        picture, invert, checked = cached
        if picture:
            shape["kind"] = "image"
            shape["data"] = picture
        if invert:
            shape["invert_data"] = invert
        if checked:
            shape["checked_data"] = checked
        shape.pop("later", None)


def realize_book(book) -> None:
    """Every page. The export wants the pictures in the file."""
    path = getattr(book, "path", None)
    if not path:
        return
    for page in book.pages or []:
        realize(path, page.shapes or [])


def _open_store(path: str | Path):
    path = Path(path)
    if path.suffix.lower() not in (".tbk", ".sbk"):
        return None
    found = _open_stores.get(str(path))
    if found is not None:
        return found
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x03JBO" not in data[:0x1000]:
        return None
    from openscript_analysis.formats.tbk.store import _Store
    store = _Store(data)
    _open_stores[str(path)] = store
    return store


def _later_bmps(store, later: tuple):
    kind = later[0]
    if kind == "picture":
        return store._picture(later[1]), None, None
    seg = store.segs.get(later[1])
    if seg is None or len(later) < 3:
        return None, None, None
    rec = later[2]
    if kind == "paint":
        return store._paint_bmp(seg, rec), None, None
    if kind != "button":
        return None, None, None
    invert = store._button_face(seg, rec, 0x27)
    words = store._button_words(seg, rec)
    checked = None
    if words and words["style"] in (5, 6, 8, 9):
        checked = store._button_face(seg, rec, 0x4B)
    return store._button_bmp(seg, rec), invert, checked


def _matte(image) -> None:
    """A transparent button's top-left pixel is the matte, not the header."""
    key = image.getpixel((0, 0))[:3]
    image.putdata([
        (red, green, blue, 0 if (red, green, blue) == key else 255)
        for red, green, blue, _alpha in image.getdata()
    ])


def _clear_edge(image) -> None:
    """White that touches the edge of a picture is the page, not the device.

    The computer on nida81 P310 is stored on a white mat. ToolBook draws
    that mat in the page colour. White shut inside the device stays.
    """
    width, height = image.size
    if width < 2 or height < 2:
        return
    pix = image.load()

    def paper(x, y) -> bool:
        red, green, blue, alpha = pix[x, y]
        return alpha and red >= 250 and green >= 250 and blue >= 250

    if not any(paper(x, y) for x, y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))):
        return
    seen = bytearray(width * height)
    stack = [(x, 0) for x in range(width)]
    stack.extend((x, height - 1) for x in range(width))
    stack.extend((0, y) for y in range(height))
    stack.extend((width - 1, y) for y in range(height))
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        mark = y * width + x
        if seen[mark]:
            continue
        seen[mark] = 1
        if not paper(x, y):
            continue
        red, green, blue, _alpha = pix[x, y]
        pix[x, y] = (red, green, blue, 0)
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))


def _load_tbk(path: Path) -> Book:
    """Load a raw .tbk. An object store is read by its segment index."""
    try:
        file_bytes = path.read_bytes()
        if b"\x03JBO" in file_bytes[:0x1000]:
            return _load_store(path, file_bytes)
        from . import tbk as rtbk
        from .openscript import load_keywords, decode
        keywords = _keywords()
        raw = rtbk.load(path)
        scanned = _scan_handlers(file_bytes, keywords)
        page_handlers, book_handlers = _place_handlers(scanned, raw.pages)
        pages = []
        for n, p in enumerate(raw.pages):
            text = []
            for f in getattr(p, "fields", []) or []:
                t = _words(getattr(f, "text", None))
                if t:
                    text.append(t)
            for para in getattr(p, "paragraphs", []) or []:
                t = _words(para)
                if t and t not in text:
                    text.append(t)
            handlers = page_handlers[n]
            if not handlers:
                handlers = _handlers_from_blob(p.blob, keywords, decode)
            surface = _surface(p.blob, keywords)
            shapes = _tbk_shapes(p.blob)
            objects = _compose_tbk(surface, shapes)
            if any(obj.get("script") for obj in objects):
                handlers = [h for h in handlers if h.name.lower() != "buttonclick"]
            if objects and any(obj.get("name") or obj.get("text") or obj.get("script") for obj in objects):
                text = [obj["text"] for obj in objects if obj.get("kind") == "text" and obj.get("text")]
            else:
                objects = []
            items = [obj["item"] for obj in objects if obj.get("item")]
            if not objects:
                items = _items_from_handlers(handlers)
            quiz = {"answer": surface["answer"]} if surface.get("answer") else None
            pages.append(Page(
                id=p.name,
                text=text,
                items=items,
                jumps=list(getattr(p, "quoted_jumps", None) or []),
                handlers=handlers,
                shapes=objects or shapes,
                quiz=quiz,
                raw={"offset": p.offset, "objects": objects or None},
            ))
        pages = _settle_tbk(pages)
        if _KEEP_DECODED:
            _write_decoded(path, pages)
        return Book(path=str(path), title=path.stem, pages=pages, handlers=book_handlers)
    except Exception as exc:
        book = Book(path=str(path), title=path.stem)
        book.pages.append(Page(
            id="(unloadable)",
            text=[f"Could not parse {path.name}: {exc}"],
        ))
        return book


def _settle_tbk(pages: list) -> list:
    """The file is a log. A later copy of a page replaces the earlier one.

    Object bounds are already on the page. This does not move them.
    """
    try:
        from openscript_analysis.formats.tbk import settle_pages
    except ImportError:
        return pages
    rows = settle_pages([
        {"id": page.id, "page": page, "deleted": False} for page in pages
    ])
    return [row["page"] for row in rows]


def _surface(blob: bytes, keywords) -> dict:
    try:
        from openscript_analysis.formats.tbk import read_surface
    except ImportError:
        return {"objects": [], "answer": ""}

    def decode_script(raw: bytes) -> str:
        from .openscript import decode
        return decode(raw, keywords)

    try:
        return read_surface(blob, decode_script if keywords else None)
    except Exception:
        return {"objects": [], "answer": ""}


def _compose_tbk(surface: dict, shapes: list) -> list:
    """One page. Plates first, then the drawing, then text and buttons."""
    widgets = _place_widgets(surface.get("objects") or [])
    if not widgets:
        return []
    plates = []
    rest = []
    for obj in widgets:
        if obj["kind"] == "rect" and (obj["w"] > 400 or obj["h"] > 300):
            plates.append(obj)
        else:
            rest.append(obj)
    return plates + list(shapes) + rest


def _place_widgets(records: list) -> list:
    from .polygon import to_pixel
    placed = []
    for src in records:
        bounds = src.get("bounds") or [0, 0, 0, 0]
        if len(bounds) < 4:
            continue
        x = to_pixel(bounds[0]) + 8
        y = to_pixel(bounds[1]) + 8
        w = max(1, to_pixel(bounds[2]) - to_pixel(bounds[0]))
        h = max(1, to_pixel(bounds[3]) - to_pixel(bounds[1]))
        kind = src.get("kind") or "rect"
        name = src.get("name") or ""
        script = src.get("script") or ""
        caption = src.get("text") or ""
        if kind == "button" and not caption and w < 160 and h < 80:
            caption = name
        obj = {
            "kind": kind,
            "name": name,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "text": caption,
            "font": "Arial",
            "size": 12,
            "bold": kind == "text",
            "fill": "" if kind == "button" else (src.get("fill") or ""),
            "outline": "black" if kind == "button" else (src.get("outline") or ""),
            "visible": not (name.lower() == "correct" and kind != "text"),
            "script": script,
        }
        item = _item_from_script(name, script)
        if item:
            obj["item"] = item
        placed.append(obj)
    return placed


def _item_from_script(name: str, script: str):
    import re
    if not script:
        return None
    low = script.lower()
    match = re.search(r'go\s+to\s+page\s+"([^"]+)"', script, re.IGNORECASE)
    if match:
        return {"label": name or match.group(1), "page": match.group(1)}
    if "send next" in low:
        return {"label": name or "Next", "page": ""}
    if "send previous" in low or "send back" in low:
        return {"label": name or "Back", "page": ""}
    return None


def _write_decoded(path: Path, pages: list) -> None:
    """Save decoded handler source under _debug/decoded/ so a load can be inspected later."""
    import json
    from datetime import datetime
    root = Path(__file__).resolve().parents[1]
    dest_dir = root / "_debug" / "decoded"
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    record = {
        "book": path.name,
        "decoded": stamp,
        "pages": [
            {
                "id": p.id,
                "handlers": [
                    {"name": h.name, "offset": h.offset, "source": h.source}
                    for h in (p.handlers or [])
                ],
            }
            for p in pages
            if p.handlers
        ],
    }
    out = dest_dir / f"{path.stem}-{stamp}.json"
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _keywords():
    """Keyword table for decoding .tbk / .sbk handlers.

    --bin overrides everything. Otherwise the clean transcription in
    keywords.py is used. engine/compat/res_77.bin is only a fallback.
    .fbk and .fsk never call this.
    """
    if _BIN_OVERRIDE is not None:
        from .openscript import load_keywords
        if not _BIN_OVERRIDE.exists():
            raise FileNotFoundError(f"keyword bin not found: {_BIN_OVERRIDE}")
        return load_keywords(_BIN_OVERRIDE)
    try:
        from .keywords import KEYWORDS
        if KEYWORDS:
            return KEYWORDS
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    bin_path = here / "compat" / "res_77.bin"
    if bin_path.exists():
        from .openscript import load_keywords
        return load_keywords(bin_path)
    json_path = here / "keywords.json"
    if json_path.exists():
        try:
            import json
            return json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _scan_handlers(data: bytes, keywords) -> list[dict] | None:
    """Whole-file handler scan. None means the expander is not installed."""
    try:
        from openscript_analysis.formats.tbk.expand import read_handlers
    except ImportError:
        return None
    return read_handlers(data, keywords)


def _place_handlers(found, pages) -> tuple[list[list], list]:
    """A stream inside a page belongs to that page. The rest is the book script."""
    if not found:
        return [[] for _ in pages], []
    ranges = []
    for i, page in enumerate(pages):
        blob = getattr(page, "blob", b"") or b""
        ranges.append((page.offset, page.offset + len(blob), i))
    by_page = [[] for _ in pages]
    book = []
    for item in found:
        handler = Handler(name=item["name"], source=item["source"], offset=item["offset"])
        placed = False
        for lo, hi, i in ranges:
            if lo <= item["offset"] < hi:
                by_page[i].append(handler)
                placed = True
                break
        if not placed:
            book.append(handler)
    return by_page, book


def _handlers_from_blob(blob: bytes, keywords, decode) -> list:
    """Find 'to handle' streams in a page blob and decode them."""
    import re
    found = []
    if not blob or not keywords:
        return found
    for match in re.finditer(rb"(?i)to handle [A-Za-z][A-Za-z0-9]*", blob):
        start = match.start()
        # handlers end at a standalone END; cap the search
        end = blob.find(b"\rend", start)
        if end < 0 or end - start > 4000:
            end = blob.find(b"\nEND", start)
        if end < 0 or end - start > 4000:
            end = min(len(blob), start + 800)
        else:
            end = min(len(blob), end + 4)
        raw = blob[start:end]
        try:
            source = decode(raw, keywords)
        except Exception:
            source = ""
        if not source:
            continue
        kind = match.group().split()[-1].decode("latin1")
        found.append(Handler(name=kind, source=source, offset=start))
    return found


def _items_from_handlers(handlers: list) -> list:
    """Build next/back items from decoded buttonClick handlers."""
    import re
    items = []
    goto = re.compile(r'go\s+to\s+page\s+"([^"]+)"(?:\s+of\s+book\s+"([^"]+)")?', re.IGNORECASE)
    for h in handlers:
        if h.name.lower() != "buttonclick":
            continue
        src = h.source or ""
        # cut at the first END so trailing garbage does not confuse the label
        low = src.lower()
        cut = low.find("\nend")
        if cut > 0:
            src = src[:cut]
            low = src.lower()
        m = goto.search(src)
        target = m.group(1) if m else ""
        other = m.group(2) if m else None
        if "go to next page" in low or (not target and "send next" in low):
            label = "Next"
        elif "go to previous" in low or "send previous" in low:
            label = "Back"
        elif other:
            label = f"{target}@{other}"
        elif target:
            label = target
        else:
            continue
        items.append({"label": label, "page": target, "book": other})
    return items
