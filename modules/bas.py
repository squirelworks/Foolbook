"""Book server. The `TB80BAS.DLL` role.

Objects, properties, file open, the value bus, the script heap.
Not the window. The window is `rtm`.
"""

NAME = "bas"
IMAGE = "TB80BAS.DLL"
BITS = 16
ROLE = "book server"


def open():
    """The Python model. Loaded when asked, not at import."""
    from engine import cdb, heap, obj, resmgr, stack
    return {"cdb": cdb, "obj": obj, "heap": heap, "stack": stack, "resmgr": resmgr}
