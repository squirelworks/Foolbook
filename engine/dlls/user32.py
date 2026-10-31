"""user32.dll: the window message functions.

The reader gives a script no window handle of its own (sysWindowHandle is
not answered), so a handle a script holds comes from outside, such as the
records window NIDAREC.INI names, and the reader cannot reach it. A
message is kept in `__windowMessages` as (function, handle, message,
wParam, lParam) so it is not lost, and the call answers 0: nothing
received it.
"""

from __future__ import annotations


def _keep(state, name, args):
    values = (list(args) + [0, 0, 0, 0])[:4]
    state.variables.setdefault("__windowMessages", []).append((name, *values))
    return 0


def send_message(state, args, refs):
    return _keep(state, "SendMessageA", args)


def post_message(state, args, refs):
    return _keep(state, "PostMessageA", args)


FUNCTIONS = {
    "sendmessagea": send_message,
    "postmessagea": post_message,
    "sendmessage": send_message,
    "postmessage": post_message,
}
