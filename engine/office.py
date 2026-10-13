"""Office files as Foolbook books.

Read turns each of these into the same page dict the loader already uses:

  .pdf .ppt .pptx .doc .docx .odt

Write turns a book back into .pdf, .pptx, .docx, or .odt.
.ppt and .doc can be read. Writing those two stores the text in a
small compound file this module can open again. Word and PowerPoint
do not open that file. Use .docx and .pptx for those programs.

Text only. No pictures, styles, or animations.
"""

from __future__ import annotations

import io
import re
import struct
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET


SUFFIXES = frozenset({".pdf", ".ppt", ".pptx", ".doc", ".docx", ".odt"})

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
_FO = "{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}"
_STYLE = "{urn:oasis:names:tc:opendocument:xmlns:style:1.0}"

_OLE_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1")
_FREE = 0xFFFFFFFF
_ENDOFCHAIN = 0xFFFFFFFE
_FATSECT = 0xFFFFFFFD


def is_office(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUFFIXES


def to_book(path: str | Path) -> dict:
    """Read an office file into a book dict."""
    path = Path(path)
    suffix = path.suffix.lower()
    blob = path.read_bytes()
    if suffix == ".pdf":
        pages = _read_pdf(blob)
    elif suffix == ".pptx":
        pages = _read_pptx(blob)
    elif suffix == ".ppt":
        pages = _read_ppt(blob)
    elif suffix == ".docx":
        pages = _read_docx(blob)
    elif suffix == ".doc":
        pages = _read_doc(blob)
    elif suffix == ".odt":
        pages = _read_odt(blob)
    else:
        raise ValueError(f"not an office file: {path.name}")
    pages = [blocks for blocks in pages if any(part.strip() for part in blocks)]
    if not pages:
        pages = [[path.stem]]
    return _book(path.stem, pages)


def write(path: str | Path, book: dict) -> Path:
    """Write a book dict to an office file. Returns the path."""
    path = Path(path)
    suffix = path.suffix.lower()
    title, pages = _from_book(book)
    if suffix == ".pdf":
        path.write_bytes(_write_pdf(pages))
    elif suffix == ".pptx":
        path.write_bytes(_write_pptx(title, pages))
    elif suffix == ".ppt":
        path.write_bytes(_write_ppt(pages))
    elif suffix == ".docx":
        path.write_bytes(_write_docx(pages))
    elif suffix == ".doc":
        path.write_bytes(_write_doc(pages))
    elif suffix == ".odt":
        path.write_bytes(_write_odt(pages))
    else:
        raise ValueError(f"cannot write {path.suffix}")
    return path


def _book(title: str, pages: list[list[str]]) -> dict:
    out = []
    for i, blocks in enumerate(pages):
        page_id = "P0" if i == 0 else f"P{i * 100}"
        items = []
        if i + 1 < len(pages):
            nxt = "P100" if i == 0 else f"P{(i + 1) * 100}"
            items.append({"label": "Next", "page": nxt})
        if i:
            prev = "P0" if i == 1 else f"P{(i - 1) * 100}"
            items.append({"label": "Back", "page": prev})
        out.append({"id": page_id, "text": [b for b in blocks if b.strip()], "items": items})
    return {"title": title, "pages": out}


def _from_book(book: dict) -> tuple[str, list[list[str]]]:
    title = book.get("title") or "Book"
    pages = []
    for page in book.get("pages") or []:
        text = [str(part) for part in (page.get("text") or []) if str(part).strip()]
        pages.append(text or [""])
    return title, pages or [[""]]


def _xml(text: str) -> str:
    amp = "&" + "amp;"
    lt = "&" + "lt;"
    gt = "&" + "gt;"
    return text.replace("&", amp).replace("<", lt).replace(">", gt)


def _zip(parts: list[tuple[str, str | bytes]], stored_first: str | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if stored_first is not None:
            info = zipfile.ZipInfo("mimetype")
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, stored_first)
        for name, data in parts:
            raw = data if isinstance(data, bytes) else data.encode("utf-8")
            archive.writestr(name, raw)
    return buf.getvalue()


def _read_docx(blob: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    pages: list[list[str]] = [[]]
    for para in root.iter(_W + "p"):
        chunks = []
        broke = False
        for el in para.iter():
            if el.tag == _W + "t" and el.text:
                chunks.append(el.text)
            if el.tag == _W + "br" and el.get(_W + "type") == "page":
                broke = True
        line = "".join(chunks).strip()
        if line:
            pages[-1].append(line)
        if broke:
            pages.append([])
    return pages


def _write_docx(pages: list[list[str]]) -> bytes:
    body = []
    for i, blocks in enumerate(pages):
        if i:
            body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        for block in blocks:
            body.append(f"<w:p><w:r><w:t>{_xml(block)}</w:t></w:r></w:p>")
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}</w:body></w:document>"
    )
    types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    return _zip([
        ("[Content_Types].xml", types),
        ("_rels/.rels", rels),
        ("word/document.xml", document),
    ])


def _read_pptx(blob: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = [n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        names.sort(key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        pages = []
        for name in names:
            root = ET.fromstring(archive.read(name))
            lines = [el.text.strip() for el in root.iter(_A + "t") if el.text and el.text.strip()]
            pages.append(lines)
    return pages


def _write_pptx(title: str, pages: list[list[str]]) -> bytes:
    overrides = []
    rels = []
    slides = []
    sld_ids = []
    for i, blocks in enumerate(pages, start=1):
        paras = "".join(f"<a:p><a:r><a:t>{_xml(b)}</a:t></a:r></a:p>" for b in blocks)
        slide = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            "<p:cSld><p:spTree><p:sp><p:txBody>"
            f"<a:bodyPr/>{paras}"
            "</p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
        )
        slides.append((f"ppt/slides/slide{i}.xml", slide))
        overrides.append(
            f'<Override PartName="/ppt/slides/slide{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        )
        rels.append(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
            f'Target="slides/slide{i}.xml"/>'
        )
        sld_ids.append(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>')
    presentation = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f"<p:sldIdLst>{''.join(sld_ids)}</p:sldIdLst>"
        '<p:sldSz cx="9144000" cy="6858000"/>'
        "</p:presentation>"
    )
    types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/ppt/presentation.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        f"{''.join(overrides)}</Types>"
    )
    package_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="ppt/presentation.xml"/>'
        "</Relationships>"
    )
    pres_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels)}</Relationships>"
    )
    return _zip([
        ("[Content_Types].xml", types),
        ("_rels/.rels", package_rels),
        ("ppt/presentation.xml", presentation),
        ("ppt/_rels/presentation.xml.rels", pres_rels),
        *slides,
    ])


def _read_odt(blob: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    breaks = set()
    for style in root.iter(_STYLE + "style"):
        name = style.get(_STYLE + "name")
        for prop in style.iter(_STYLE + "paragraph-properties"):
            if prop.get(_FO + "break-before") == "page" and name:
                breaks.add(name)
    pages: list[list[str]] = [[]]
    for para in root.iter(_TEXT + "p"):
        if para.get(_TEXT + "style-name") in breaks:
            pages.append([])
        line = "".join(para.itertext()).strip()
        if line:
            pages[-1].append(line)
    return pages


def _write_odt(pages: list[list[str]]) -> bytes:
    body = []
    for i, blocks in enumerate(pages):
        if i:
            body.append('<text:p text:style-name="FoolbookPage"/>')
        for block in blocks:
            body.append(f"<text:p>{_xml(block)}</text:p>")
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0">'
        "<office:automatic-styles>"
        '<style:style style:name="FoolbookPage" style:family="paragraph">'
        '<style:paragraph-properties fo:break-before="page"/>'
        "</style:style></office:automatic-styles>"
        f"<office:body><office:text>{''.join(body)}</office:text></office:body>"
        "</office:document-content>"
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" manifest:full-path="/"/>'
        '<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>'
        "</manifest:manifest>"
    )
    return _zip(
        [("META-INF/manifest.xml", manifest), ("content.xml", content)],
        stored_first="application/vnd.oasis.opendocument.text",
    )


def _pdf_escape(text: str) -> bytes:
    raw = text.encode("latin-1", "replace")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _write_pdf(pages: list[list[str]]) -> bytes:
    count = len(pages)
    font = 3 + 2 * count
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(count))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {count} >>".encode())
    for blocks in pages:
        lines = ["BT", "/F1 12 Tf", "72 740 Td"]
        for block in blocks:
            for line in block.split("\n"):
                lines.append(f"({_pdf_escape(line).decode('latin-1')}) Tj")
                lines.append("0 -16 Td")
        lines.append("ET")
        stream = "\n".join(lines).encode("latin-1")
        contents = b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        page = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            + f"/Contents {len(objects) + 2} 0 R ".encode()
            + f"/Resources << /Font << /F1 {font} 0 R >> >> >>".encode()
        )
        objects.append(page)
        objects.append(contents)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


def _pdf_strings(data: bytes) -> list[str]:
    out = []
    i = 0
    while i < len(data):
        if data[i:i + 1] == b"(":
            i += 1
            chars = []
            while i < len(data):
                c = data[i]
                if c == 0x5C and i + 1 < len(data):
                    chars.append(chr(data[i + 1]))
                    i += 2
                    continue
                if c == 0x29:
                    i += 1
                    break
                chars.append(chr(c))
                i += 1
            text = "".join(chars).strip()
            if text:
                out.append(text)
            continue
        i += 1
    return out


def _pdf_stream(body: bytes) -> list[str]:
    match = re.search(rb"stream\r?\n(.*?)\r?\n?endstream", body, re.S)
    if not match:
        return []
    data = match.group(1)
    if b"FlateDecode" in body:
        data = zlib.decompress(data)
    return _pdf_strings(data)


def _read_pdf(blob: bytes) -> list[list[str]]:
    objects = {}
    for match in re.finditer(rb"(\d+)\s+0\s+obj\s*(.*?)\s*endobj", blob, re.S):
        objects[int(match.group(1))] = match.group(2)
    order = []
    for body in objects.values():
        if b"/Type" in body and re.search(rb"/Type\s*/Pages\b", body):
            kids = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
            if kids:
                order.extend(int(n) for n in re.findall(rb"(\d+)\s+0\s+R", kids.group(1)))
    if not order:
        order = [
            num for num, body in sorted(objects.items())
            if re.search(rb"/Type\s*/Page(?!s)", body)
        ]
    pages = []
    for num in order:
        body = objects.get(num, b"")
        refs = []
        one = re.search(rb"/Contents\s+(\d+)\s+0\s+R", body)
        many = re.search(rb"/Contents\s*\[(.*?)\]", body, re.S)
        if many:
            refs = [int(n) for n in re.findall(rb"(\d+)\s+0\s+R", many.group(1))]
        elif one:
            refs = [int(one.group(1))]
        lines = []
        for ref in refs:
            lines.extend(_pdf_stream(objects.get(ref, b"")))
        pages.append(lines)
    return pages


def _ole_streams(blob: bytes) -> dict[str, bytes]:
    if blob[:8] != _OLE_MAGIC:
        raise ValueError("not a compound file")
    sector = 1 << int.from_bytes(blob[0x1E:0x20], "little")
    mini = 1 << int.from_bytes(blob[0x20:0x22], "little")
    dir_start = int.from_bytes(blob[0x30:0x34], "little")
    cutoff = int.from_bytes(blob[0x38:0x3C], "little")
    mini_fat_start = int.from_bytes(blob[0x3C:0x40], "little")
    difat = []
    for i in range(109):
        value = int.from_bytes(blob[0x4C + i * 4:0x50 + i * 4], "little")
        if value == _FREE:
            break
        difat.append(value)
    fat = bytearray()
    for sect in difat:
        off = (sect + 1) * sector
        fat += blob[off:off + sector]

    def chain(start: int) -> list[int]:
        found = []
        seen = set()
        sect = start
        while sect < 0xFFFFFFF0 and sect not in seen:
            seen.add(sect)
            found.append(sect)
            sect = int.from_bytes(fat[sect * 4:sect * 4 + 4], "little")
        return found

    def read_chain(start: int) -> bytes:
        if start >= 0xFFFFFFF0:
            return b""
        return b"".join(blob[(s + 1) * sector:(s + 2) * sector] for s in chain(start))

    directory = read_chain(dir_start)
    mini_fat = read_chain(mini_fat_start) if mini_fat_start < 0xFFFFFFF0 else b""
    entries = []
    for i in range(0, len(directory), 128):
        ent = directory[i:i + 128]
        if len(ent) < 128:
            break
        name_len = int.from_bytes(ent[64:66], "little")
        name = ent[:max(0, name_len - 2)].decode("utf-16-le", "ignore")
        entries.append((
            name,
            ent[66],
            int.from_bytes(ent[116:120], "little"),
            int.from_bytes(ent[120:124], "little"),
        ))
    root = next((ent for ent in entries if ent[1] == 5), None)
    mini_stream = read_chain(root[2]) if root else b""

    def read_mini(start: int, size: int) -> bytes:
        parts = []
        seen = set()
        sect = start
        while sect < 0xFFFFFFF0 and sect not in seen and sum(len(p) for p in parts) < size:
            seen.add(sect)
            parts.append(mini_stream[sect * mini:sect * mini + mini])
            sect = int.from_bytes(mini_fat[sect * 4:sect * 4 + 4], "little") if sect * 4 + 4 <= len(mini_fat) else _ENDOFCHAIN
        return b"".join(parts)[:size]

    streams = {}
    for name, kind, start, size in entries:
        if kind != 2 or not name:
            continue
        streams[name] = read_mini(start, size) if size < cutoff else read_chain(start)[:size]
    return streams


def _ole_write(name: str, data: bytes) -> bytes:
    """One-stream compound file. The stream is larger than the mini cutoff."""
    sector = 512
    data_sectors = max(1, (len(data) + sector - 1) // sector)
    # sector 0 is the FAT, sector 1 is the directory, then the stream
    fat = [_FATSECT, _ENDOFCHAIN]
    for i in range(data_sectors - 1):
        fat.append(2 + i + 1)
    if data_sectors:
        fat.append(_ENDOFCHAIN)
    while len(fat) < sector // 4:
        fat.append(_FREE)
    directory = bytearray(sector)
    _dir_entry(directory, 0, "Root Entry", 5, 1, _ENDOFCHAIN, 0)
    _dir_entry(directory, 1, name, 2, _FREE, 2, len(data))
    header = bytearray(sector)
    header[0:8] = _OLE_MAGIC
    header[0x18:0x1A] = (0x003E).to_bytes(2, "little")  # minor
    header[0x1A:0x1C] = (0x0003).to_bytes(2, "little")  # major
    header[0x1C:0x1E] = (0xFFFE).to_bytes(2, "little")
    header[0x1E:0x20] = (9).to_bytes(2, "little")
    header[0x20:0x22] = (6).to_bytes(2, "little")
    header[0x2C:0x30] = (1).to_bytes(4, "little")  # one FAT sector
    header[0x30:0x34] = (1).to_bytes(4, "little")  # directory at sector 1
    header[0x38:0x3C] = (0).to_bytes(4, "little")
    header[0x3C:0x40] = _ENDOFCHAIN.to_bytes(4, "little")
    header[0x44:0x48] = _ENDOFCHAIN.to_bytes(4, "little")
    header[0x4C:0x50] = (0).to_bytes(4, "little")  # FAT at sector 0
    for i in range(1, 109):
        header[0x4C + i * 4:0x50 + i * 4] = _FREE.to_bytes(4, "little")
    fat_bytes = b"".join(struct.pack("<I", n) for n in fat[:sector // 4])
    pad = data + b"\x00" * (data_sectors * sector - len(data))
    return bytes(header + fat_bytes + directory + pad)


def _dir_entry(buf: bytearray, index: int, name: str, kind: int, child: int, start: int, size: int) -> None:
    off = index * 128
    encoded = (name + "\x00").encode("utf-16-le")
    buf[off:off + len(encoded)] = encoded
    struct.pack_into("<H", buf, off + 64, len(encoded))
    buf[off + 66] = kind
    buf[off + 67] = 1  # black
    struct.pack_into("<I", buf, off + 68, _FREE)  # left
    struct.pack_into("<I", buf, off + 72, _FREE)  # right
    struct.pack_into("<I", buf, off + 76, child if child != _FREE else _FREE)
    struct.pack_into("<I", buf, off + 116, start)
    struct.pack_into("<I", buf, off + 120, size)


def _runs(blob: bytes) -> list[str]:
    """Pull readable UTF-16 text. A form feed starts a new page marker."""
    if len(blob) % 2:
        blob = blob[:-1]
    chunks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        text = "".join(current).strip()
        current.clear()
        letters = sum(ch.isalpha() or ch.isspace() or ch in ".,;:'\"-()&" for ch in text)
        if len(text) >= 4 and letters >= 0.6 * len(text):
            chunks.append(text)

    for i in range(0, len(blob), 2):
        code = int.from_bytes(blob[i:i + 2], "little")
        if code == 0x0C:
            flush()
            chunks.append("\x0c")
            continue
        if code in (9, 10, 13) or 32 <= code < 0xFFFE:
            current.append(chr(code))
        else:
            flush()
    flush()
    return chunks


def _pages_from_runs(chunks: list[str]) -> list[list[str]]:
    pages: list[list[str]] = [[]]
    for chunk in chunks:
        if chunk == "\x0c":
            pages.append([])
        else:
            for line in chunk.splitlines():
                if line.strip():
                    pages[-1].append(line.strip())
    return pages


def _read_doc(blob: bytes) -> list[list[str]]:
    streams = _ole_streams(blob)
    raw = streams.get("WordDocument") or b""
    return _pages_from_runs(_runs(raw))


def _write_doc(pages: list[list[str]]) -> bytes:
    parts = []
    for i, blocks in enumerate(pages):
        if i:
            parts.append("\x0c")
        parts.append("\n".join(blocks))
    data = "".join(parts).encode("utf-16-le")
    return _ole_write("WordDocument", data)


def _ppt_atoms(blob: bytes):
    i = 0
    while i + 8 <= len(blob):
        version = blob[i] & 0x0F
        kind = int.from_bytes(blob[i + 2:i + 4], "little")
        length = int.from_bytes(blob[i + 4:i + 8], "little")
        end = i + 8 + length
        if end > len(blob):
            break
        if version == 0xF:
            yield from _ppt_atoms(blob[i + 8:end])
        else:
            yield kind, blob[i + 8:end]
        i = end


def _read_ppt(blob: bytes) -> list[list[str]]:
    streams = _ole_streams(blob)
    raw = streams.get("PowerPoint Document") or b""
    pages: list[list[str]] = []
    current: list[str] = []
    seen_slide = False
    for kind, data in _ppt_atoms(raw):
        if kind == 0x03EE:
            if seen_slide:
                pages.append(current)
            current = []
            seen_slide = True
        elif kind == 0x0FA0:
            text = data.decode("utf-16-le", "ignore").strip("\x00").strip()
            if text:
                current.append(text)
        elif kind == 0x0FA8:
            text = data.decode("latin-1", "ignore").strip("\x00").strip()
            if text:
                current.append(text)
    if current or seen_slide:
        pages.append(current)
    return pages


def _write_ppt(pages: list[list[str]]) -> bytes:
    out = bytearray()

    def atom(kind: int, data: bytes, version: int = 0) -> None:
        out.extend(struct.pack("<HHI", version, kind, len(data)))
        out.extend(data)

    for blocks in pages:
        atom(0x03EE, b"")
        for block in blocks:
            atom(0x0FA0, block.encode("utf-16-le"))
    return _ole_write("PowerPoint Document", bytes(out))
