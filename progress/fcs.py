""".fcs student file.

On disk this is encrypted. Extracted, it is the student JSON.
The password for this cut is UwU. A later module can replace that.

    FCS1            magic
    1 byte          version (1)
    16 bytes        salt
    12 bytes        nonce
    rest            AES-GCM ciphertext of the UTF-8 JSON
"""

from __future__ import annotations

import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"FCS1"
VERSION = 1
PASSWORD = "UwU"
_ITERATIONS = 200_000


class FcsError(ValueError):
    pass


def pack(data: dict, password: str = PASSWORD) -> bytes:
    """Encrypt a student dict. Without the password this cannot be read back."""
    payload = json.dumps(data, indent=2).encode("utf-8")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _key(password, salt)
    cipher = AESGCM(key).encrypt(nonce, payload, MAGIC)
    return MAGIC + bytes([VERSION]) + salt + nonce + cipher


def unpack(blob: bytes, password: str = PASSWORD) -> dict:
    """Decrypt an .fcs blob to the student dict."""
    if len(blob) < 4 + 1 + 16 + 12 + 16 or blob[:4] != MAGIC:
        raise FcsError("not an .fcs file")
    if blob[4] != VERSION:
        raise FcsError(f"unsupported .fcs version {blob[4]}")
    salt = blob[5:21]
    nonce = blob[21:33]
    cipher = blob[33:]
    try:
        payload = AESGCM(_key(password, salt)).decrypt(nonce, cipher, MAGIC)
    except Exception as exc:
        raise FcsError("cannot extract student file") from exc
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise FcsError("student file is not an object")
    return data


def _key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))
