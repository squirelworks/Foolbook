"""user32.dll: the window message functions.

The reader runs no other Windows programs, so a message sent or posted to
another window reaches nobody. SendMessageA answers 0 and PostMessageA
answers 0, as Windows does for a window that is not there.
"""

from __future__ import annotations


def send_message(state, args, refs):
    return 0


def post_message(state, args, refs):
    return 0


FUNCTIONS = {
    "sendmessagea": send_message,
    "postmessagea": post_message,
    "sendmessage": send_message,
    "postmessage": post_message,
}
