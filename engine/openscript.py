"""OpenScript bytecode decoder.

Used only for .tbk / .sbk backward compatibility.
.fbk and .fsk already hold source; they never reach this module.

Keyword table is the clean transcription in engine/keywords.py.
engine/compat/res_77.bin is the original ToolBook resource and is only
loaded if the clean table is missing.
"""
import struct
import sys
from pathlib import Path

def load_keywords(res_path):
    """Load the keyword table from resource 0x77.
    
    The offset table starts at byte 2 + count*4.
    Each entry is a word offset into the resource.
    """
    data = Path(res_path).read_bytes()
    count = struct.unpack_from('<H', data, 0)[0]
    fa_start = 2 + count * 4
    keywords = []
    for i in range(count):
        off = struct.unpack_from('<H', data, fa_start + i*2)[0]
        if off >= len(data):
            break
        end = data.find(b'\x00', off)
        if end == -1:
            break
        s = data[off:end].decode('latin-1', errors='replace')
        keywords.append(s)
    return keywords

def decode(bytecode, keywords):
    """Decode a bytecode stream into source text.
    
    Back-references (0xC0-0xFF) copy from the compressed input stream,
    not the output buffer, per FUN_1040_0970.
    """
    output = bytearray()
    pos = 0
    while pos < len(bytecode):
        b = bytecode[pos]
        if b < 0x80:
            output.append(b)
            pos += 1
        elif (b & 0xF0) == 0xF0:
            if b == 0xFF:
                if pos + 2 >= len(bytecode):
                    break
                ch = bytecode[pos + 1]
                count = bytecode[pos + 2] + 1
                output.extend([ch] * count)
                pos += 3
            else:
                output.extend([0x20] * ((b & 0xF) + 2))
                pos += 1
        elif (b & 0xF0) == 0xE0:
            output.extend([0x0D, 0x0A])
            output.extend([0x20] * (b & 0xF))
            pos += 1
        elif (b & 0x40) == 0:
            index = b & 0xF
            if b & 0x10:
                if pos + 1 >= len(bytecode):
                    break
                index = (index << 8) | bytecode[pos + 1]
                pos += 2
            else:
                pos += 1
            if index < len(keywords):
                output.extend(keywords[index].encode('latin-1'))
            if (b & 0x20) == 0:
                output.append(0x20)
        else:
            # back-ref into INPUT stream
            if (b & 0x10) == 0:
                if pos + 1 >= len(bytecode):
                    break
                length = (b & 0xF) + 3
                src = (pos + 1) + (-4 - bytecode[pos + 1])
                pos += 2
            else:
                if pos + 2 >= len(bytecode):
                    break
                length = (b & 0xF) + 4
                import struct
                off = struct.unpack_from('<H', bytecode, pos + 1)[0]
                src = (pos + 1) + (-1 - off)
                pos += 3
            for i in range(length):
                if 0 <= src + i < len(bytecode):
                    output.append(bytecode[src + i])
                else:
                    output.append(0x3F)
    return output.decode('latin-1', errors='replace')

def compile(source: str, keywords: list[str] | None = None) -> bytes:
    """Compile OpenScript source to the bytecode FUN_1040_0970 expands.

    Inverse of decode(). Known opcodes only:

      00-7F   literal
      80-BF   keyword (bit 4 = two-byte index, bit 5 clear = trailing space)
      E0-EF   CRLF plus 0-15 spaces
      F0-FE   2-16 spaces
      FF      repeat

    Back-references (C0-DF) are a compressor. This cut does not emit them.
    The keyword table is the same one the decoder uses.
    """
    if keywords is None:
        from engine.keywords import KEYWORDS
        keywords = KEYWORDS
    table = {w: i for i, w in enumerate(keywords) if w}
    # longest first so "buttonClick" wins over "button"
    words = sorted(table, key=len, reverse=True)
    out = bytearray()
    i = 0
    n = len(source)
    while i < n:
        # newline
        if source[i] == "\n" or source.startswith("\r\n", i):
            if source.startswith("\r\n", i):
                i += 2
            else:
                i += 1
            spaces = 0
            while i < n and source[i] == " " and spaces < 15:
                spaces += 1
                i += 1
            out.append(0xE0 | spaces)
            continue
        # space run
        if source[i] == " ":
            j = i
            while j < n and source[j] == " ":
                j += 1
            run = j - i
            while run >= 2:
                take = min(run, 16)
                out.append(0xF0 | (take - 2))
                run -= take
            if run:
                out.append(0x20)
            i = j
            continue
        # keyword
        matched = None
        for w in words:
            if source.startswith(w, i):
                after = i + len(w)
                # do not eat a keyword that is a prefix of an identifier
                if after < n and (source[after].isalnum() or source[after] == "_"):
                    continue
                matched = w
                break
        if matched is not None:
            idx = table[matched]
            trailing = (i + len(matched) < n and source[i + len(matched)] == " ")
            if idx < 16:
                b = 0x80 | idx
                if not trailing:
                    b |= 0x20
                out.append(b)
            else:
                b = 0x80 | 0x10 | ((idx >> 8) & 0xF)
                if not trailing:
                    b |= 0x20
                out.append(b)
                out.append(idx & 0xFF)
            i += len(matched)
            if trailing:
                i += 1
            continue
        # literal, with a repeat if the same byte runs
        ch = source[i].encode("latin-1", "replace")[0]
        run = 1
        while i + run < n and source[i + run].encode("latin-1", "replace")[0] == ch and run < 256:
            run += 1
        if run >= 4:
            out.append(0xFF)
            out.append(ch)
            out.append(run - 1)
            i += run
        else:
            out.append(ch)
            i += 1
    return bytes(out)


def main():
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <res_77.bin> <bytecode.bin>')
        sys.exit(1)
    keywords = load_keywords(sys.argv[1])
    print(f'Loaded {len(keywords)} keywords')
    bytecode = Path(sys.argv[2]).read_bytes()
    print(f'Bytecode: {len(bytecode)} bytes')
    text = decode(bytecode, keywords)
    print(text)

if __name__ == '__main__':
    main()
