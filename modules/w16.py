"""16-bit thunk. The `TB80W16.DLL` role.

The `DoCmd*` bus. Not book open. The body is not ported.
"""

NAME = "w16"
IMAGE = "TB80W16.DLL"
BITS = 16
ROLE = "thunk"


def open():
    return {"image": IMAGE, "body": "not-read"}
