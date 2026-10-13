"""Open a ToolBook TBX folder from its Book.xml.

A TBX is a folder. Book.xml is the entry. Pages live in Page*/Page.xml,
backgrounds in Background*/Background.xml, and scripts in the .script files
beside them. This is not a .tbk.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from foolbook.model import Book, Handler, Page


MARK = "urn:sumtotalsystems:toolbook.tbkx"
_TWIP = 15
_SKIP = {"Page", "Background", "UserProperty", "Group", "Button"}


def is_tbx(path: str | Path) -> bool:
    """True when an XML file carries the ToolBook TBX namespace."""
    path = Path(path)
    if path.suffix.lower() != ".xml" or not path.is_file():
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return False
    return MARK in head


def book_root(path: str | Path) -> Path:
    """The folder that holds Book.xml, starting from the file that was opened."""
    path = Path(path)
    cur = path if path.is_dir() else path.parent
    for _ in range(6):
        if (cur / "Book.xml").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return path if path.is_dir() else path.parent


def load(path: str | Path) -> Book:
    """Read the TBX that contains this XML file into a Foolbook book."""
    root = book_root(path)
    book_xml = root / "Book.xml"
    caption = root.name
    if book_xml.is_file():
        el = ET.parse(book_xml).getroot()
        caption = el.get("Caption") or caption

    backgrounds: dict[str, dict] = {}
    for directory in sorted(p for p in root.glob("Background*") if p.is_dir()):
        xml = directory / "Background.xml"
        if not xml.is_file():
            continue
        bg = _read_unit(xml, directory, root)
        if not bg:
            continue
        backgrounds[bg["id"]] = bg
        if bg["name"]:
            backgrounds[bg["name"]] = bg

    pages: list[Page] = []
    for directory in sorted(p for p in root.glob("Page*") if p.is_dir()):
        xml = directory / "Page.xml"
        if not xml.is_file():
            continue
        unit = _read_unit(xml, directory, root)
        if not unit:
            continue
        bg = backgrounds.get(unit["background"]) or backgrounds.get(
            unit["background"].replace("Background id ", "").strip()
        )
        text = list(bg["text"] if bg else []) + unit["text"]
        shapes = list(bg["shapes"] if bg else []) + unit["shapes"]
        pages.append(Page(
            id=unit["name"] or unit["id"] or directory.name,
            text=text,
            items=unit["items"],
            handlers=unit["handlers"],
            shapes=shapes,
        ))
    _bind_neighbors(pages)
    return Book(path=str(book_xml if book_xml.is_file() else path), title=caption, pages=pages)


def _read_unit(xml_path: Path, directory: Path, root: Path) -> dict | None:
    try:
        el = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return None
    text: list[str] = []
    shapes: list[dict] = []
    items: list[dict] = []
    for obj in el.iter():
        tag = obj.tag.split("}")[-1]
        if tag in _SKIP or not obj.get("IdNumber"):
            continue
        if tag == "Field":
            text.extend(_field_text(obj))
            continue
        shape = _shape(tag, obj)
        if shape:
            shapes.append(shape)
    for obj in el.iter():
        tag = obj.tag.split("}")[-1]
        if tag != "Button" or not obj.get("IdNumber"):
            continue
        script = _script_text(directory, root, f"Button{obj.get('IdNumber')}.script")
        item = _button_item(obj.get("Name") or "", script)
        if item:
            items.append(item)
    handlers = _handlers(_script_text(directory, root, el.get("Script") or ""))
    if not handlers:
        for script in sorted(directory.glob("*.script")):
            if script.name.lower().startswith("button"):
                continue
            handlers = _handlers(script.read_text(encoding="utf-8", errors="replace"))
            if handlers:
                break
    return {
        "id": el.get("IdNumber", ""),
        "name": el.get("Name", ""),
        "background": el.get("Background", ""),
        "text": text,
        "shapes": shapes,
        "items": items,
        "handlers": handlers,
    }


def _field_text(el: ET.Element) -> list[str]:
    found: list[str] = []
    for key in ("Text", "RichText", "Caption"):
        if el.get(key):
            found.append(_plain(el.get(key, "")))
    for child in list(el):
        tag = child.tag.split("}")[-1].lower()
        if tag in ("text", "richtext", "para", "paragraph"):
            found.append(_plain("".join(child.itertext())))
    if not found:
        raw = _plain("".join(el.itertext()))
        if raw:
            found.append(raw)
    return [part for part in found if part]


def _plain(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _shape(tag: str, el: ET.Element) -> dict | None:
    kind = tag.lower()
    bounds = _ints(el.get("Bounds") or "")
    points = _pairs(el.get("Vertices") or "")
    fill = _color(el.get("FillColor") or el.get("Fill") or "")
    outline = _color(el.get("LineColor") or el.get("StrokeColor") or "")
    if kind in ("rectangle", "roundrect") and len(bounds) >= 4:
        return {"kind": "rect", **_box(bounds), "fill": fill, "outline": outline or fill}
    if kind in ("ellipse", "oval", "arc") and len(bounds) >= 4:
        return {"kind": "ellipse", **_box(bounds), "fill": fill, "outline": outline or fill}
    if kind in ("line", "angledline"):
        if len(points) >= 2:
            return {"kind": "line", "points": points, "outline": outline or "#000000"}
        if len(bounds) >= 4:
            return {
                "kind": "line",
                "points": [[bounds[0], bounds[1]], [bounds[2], bounds[3]]],
                "outline": outline or "#000000",
            }
    if kind in ("irregularpolygon", "polygon") and len(points) >= 3:
        return {"kind": "polygon", "points": points, "fill": fill, "outline": outline or fill}
    return None


def _box(bounds: list[int]) -> dict:
    left, top, right, bottom = bounds[:4]
    return {
        "x": min(left, right),
        "y": min(top, bottom),
        "w": abs(right - left),
        "h": abs(bottom - top),
    }


def _ints(value: str) -> list[int]:
    out = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(float(part) / _TWIP))
        except ValueError:
            return []
    return out


def _pairs(value: str) -> list[list[int]]:
    nums = _ints(value)
    return [[nums[i], nums[i + 1]] for i in range(0, len(nums) - 1, 2)]


def _color(value: str) -> str:
    parts = [p.strip() for p in value.split(",")]
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        r, g, b = (max(0, min(255, int(p))) for p in parts)
        return f"#{r:02x}{g:02x}{b:02x}"
    if value.startswith("#") and len(value) in (4, 7):
        return value
    return ""


def _script_text(directory: Path, root: Path, name: str) -> str:
    if not name:
        return ""
    for candidate in (directory / name, root / name, directory / Path(name).name):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8", errors="replace")
    return ""


def _handlers(source: str) -> list[Handler]:
    found = []
    for part in re.split(r"(?im)^[ \t]*to handle[ \t]+", source)[1:]:
        name = part.split(None, 1)[0].strip() if part.split() else ""
        if not name:
            continue
        found.append(Handler(name=name, source="to handle " + part.strip()))
    return found


def _button_item(name: str, script: str) -> dict | None:
    if not script and not name:
        return None
    low = script.lower()
    match = re.search(r'go\s+to\s+page\s+"([^"]+)"(?:\s+of\s+book\s+"([^"]+)")?', script, re.I)
    target = match.group(1) if match else ""
    other = match.group(2) if match and match.group(2) else ""
    if "go to next page" in low or (not target and "send next" in low):
        label = "Next"
    elif "go to previous" in low or "send previous" in low or "send back" in low:
        label = "Back"
    else:
        label = name or target
    if not label:
        return None
    return {"label": label, "page": target, "book": other, "script": script}


def _bind_neighbors(pages: list[Page]) -> None:
    """A send next / send previous uses the next page in the TBX, not a sorted id."""
    ids = [p.id for p in pages]
    for i, page in enumerate(pages):
        for item in page.items:
            if item.get("page"):
                continue
            low = (item.get("script") or "").lower()
            if "send next" in low or "go to next page" in low:
                if i + 1 < len(ids):
                    item["page"] = ids[i + 1]
            elif "send previous" in low or "go to previous" in low or "send back" in low:
                if i > 0:
                    item["page"] = ids[i - 1]
            item.pop("script", None)
        for item in page.items:
            item.pop("script", None)
