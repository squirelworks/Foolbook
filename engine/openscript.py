"""OpenScript bytecode decoder.

Self-contained. Uses engine/res_77.bin or engine/keywords.json as the keyword table.
The loader calls this to turn handler streams into source the engine can run.
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
    not the output buffer.
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
                off = struct.unpack_from('<H', bytecode, pos + 1)[0]
                src = (pos + 1) + (-1 - off)
                pos += 3
            for i in range(length):
                if 0 <= src + i < len(bytecode):
                    output.append(bytecode[src + i])
                else:
                    output.append(0x3F)
    return output.decode('latin-1', errors='replace')
