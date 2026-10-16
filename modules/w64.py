"""64-bit thunk. Scaffold only.

There is no `TB80W64` in the 8.1 set. A 64-bit host (Windows
`x86_64`, or macOS, iOS, and Android on `arm64`) loads this slot
instead of `w16`. It has no image and no body.
"""

NAME = "w64"
IMAGE = None
BITS = 64
ROLE = "thunk"


def open():
    return {"image": None, "body": "scaffold"}
