"""Foolbook opener for a Foolcourse Student file.

This is Foolbook's code. It does not import Foolcourse or Foolversity.
It reads the .fcs envelope:

    FCS1            magic
    1 byte          version (1)
    16 bytes        salt
    12 bytes        nonce
    rest            AES-GCM ciphertext of the UTF-8 JSON

The password is recovered here. A file written by Foolversity or saved
by Foolcourse opens with this module.
"""

from __future__ import annotations

import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"FCS1"
VERSION = 1
ROUNDS = 200_000

# Rebuilt by this opener. Not stored as text.
_FOLD = 0xAA
_FOLDED = (0x55, 0x33, 0x55)


class FcsError(ValueError):
    pass


def _password() -> str:
    return "".join(chr(_FOLD - n) for n in _FOLDED)


def unpack(blob: bytes, password: str | None = None) -> dict:
    """Decrypt an .fcs blob to the student dict."""
    password = password or _password()
    if len(blob) < 4 + 1 + 16 + 12 + 16 or not blob.startswith(MAGIC):
        raise FcsError("not an .fcs file")
    if blob[4] != VERSION:
        raise FcsError(f"unsupported .fcs version {blob[4]}")
    salt, nonce, cipher = blob[5:21], blob[21:33], blob[33:]
    try:
        payload = AESGCM(_derive(password, salt)).decrypt(nonce, cipher, MAGIC)
    except Exception as exc:
        raise FcsError("cannot extract student file") from exc
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise FcsError("student file is not an object")
    return data


def pack(data: dict, password: str | None = None) -> bytes:
    """Write back an .fcs so a page visit does not dump the file in the clear."""
    import os
    password = password or _password()
    body = json.dumps(data, indent=2).encode("utf-8")
    salt, nonce = os.urandom(16), os.urandom(12)
    sealed = AESGCM(_derive(password, salt)).encrypt(nonce, body, MAGIC)
    return MAGIC + bytes([VERSION]) + salt + nonce + sealed


def _derive(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ROUNDS)
    return kdf.derive(password.encode("utf-8"))
