"""Chip and host.

The Python models can run on any host in this table. The NE images
cannot. ToolBook II 8.1 in this record is 16-bit. There is no W64
binary. `w64` is the thunk a 64-bit host would load instead of `w16`.
The slot is empty on purpose.

macOS, iOS, and Android are hosts. They are not chips. The chip is
`x86_64` or `arm64`. A host that does not list the chip is refused.
"""

from __future__ import annotations

CHIPS = {
    "i86": {"bits": 16, "endian": "le"},
    "i386": {"bits": 32, "endian": "le"},
    "x86_64": {"bits": 64, "endian": "le"},
    "arm64": {"bits": 64, "endian": "le"},
}

HOSTS = {
    "windows": ("i86", "i386", "x86_64"),
    "macos": ("x86_64", "arm64"),
    "ios": ("arm64",),
    "android": ("arm64",),
}

# Width thunk. Not a claim that the file exists.
THUNK = {16: "w16", 32: "w32", 64: "w64"}

# Native images in the 8.1 set this record has. One chip.
NATIVE = {
    "i86": ("bas", "rtm", "utl", "rcr", "w16", "bmp", "jpg"),
}

MODELS = ("bas", "rtm", "utl", "rcr", "w16", "w32", "w64", "bmp", "jpg")


def plan(chip: str, host: str) -> dict:
    """What a host can load. Models are Python. Native is the old image."""
    if chip not in CHIPS:
        raise KeyError(chip)
    if host not in HOSTS:
        raise KeyError(host)
    if chip not in HOSTS[host]:
        raise ValueError(f"{chip} is not a {host} chip")
    bits = CHIPS[chip]["bits"]
    return {
        "chip": chip,
        "host": host,
        "bits": bits,
        "endian": CHIPS[chip]["endian"],
        "thunk": THUNK[bits],
        "native": list(NATIVE.get(chip, ())),
        "models": list(MODELS),
    }
