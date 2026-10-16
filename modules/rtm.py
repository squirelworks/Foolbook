"""Shell. The 43 `TB80RTM` exports, by the job the name names.

A dialog is not implemented. The group is the lookup. The window
roles are the ones this shell can point at.
"""

NAME = "rtm"
IMAGE = "TB80RTM.EXE"
BITS = 16
ROLE = "shell"

GROUPS = {
    "ASCIIFILEDLGHOOKPROC": "file",
    "ASCIIFORMATDLGPROC": "file",
    "ASYM_ASCIIFILEDLGHOOK": "file",
    "ASYM_CDROMSAHPCBK": "file",
    "BOOKQUERYSAVE": "book",
    "CACHEFILEOPTIONSDIALOGPROC": "file",
    "CDROMSAVEASHOOK": "file",
    "CHANGEPRINTERDIALOGPROC": "print",
    "CONDITIONDIALOGPROC": "find",
    "DDEWNDPROC": "window",
    "EGCDBSAVEBOOK": "book",
    "EGDYNALINKERRORFUNC": "book",
    "EGYPTCHILDWNDPROC": "window",
    "EGYPTCLIENTWNDPROC": "window",
    "EGYPTNOTIFYPROC": "window",
    "ENUMWINSFOROPEN": "book",
    "FONTDLGHOOKPROC": "print",
    "FONTSTATUSWNDPROC": "print",
    "HANDLEREMOVESCRIPTPROC": "book",
    "HEADERDIALOGPROC": "print",
    "HEADERNOTIFYPROC": "print",
    "HEADFOOTWNDPROC": "print",
    "IMAGESTORESTATUS": "picture",
    "MAINWNDPROC": "window",
    "MMRESDLGCHOOSE": "resource",
    "OPTIMIZEDSAVESTATUSDIALOGPROC": "file",
    "PARAGRAPHDIALOGPROC": "print",
    "PLASKDIALOGPROC": "ask",
    "PLREQUESTDIALOGPROC": "ask",
    "POSTPALCHNGTOOTHERS": "picture",
    "PREVIEWNOTIFYPROC": "print",
    "PRINTOPTIONSDIALOGPROC": "print",
    "PRINTPAGEDIALOGPROC": "print",
    "PRINTREPORTDIALOGPROC": "print",
    "RESCHOOSEDLGPROC": "resource",
    "RESOURCELISTENUM": "resource",
    "SEARCHDIALOGPROC": "find",
    "STATUSBARWNDPROC": "window",
    "SUBEDITCONTROLPROC": "window",
    "TOOLNOTIFY": "tool",
    "XCTOLEREMOTECOMMAND": "remote",
    "XCTOLEREMOTEGET": "remote",
    "XDLLTRANSWINPROC": "window",
}

WINDOWS = {
    "MAINWNDPROC": "frame",
    "EGYPTCLIENTWNDPROC": "client",
    "EGYPTCHILDWNDPROC": "child",
    "EGYPTNOTIFYPROC": "notify",
    "STATUSBARWNDPROC": "status",
    "DDEWNDPROC": "dde",
    "SUBEDITCONTROLPROC": "edit",
    "XDLLTRANSWINPROC": "foreign",
}


def which(name: str) -> str | None:
    return GROUPS.get((name or "").strip().upper())


def open():
    return {"image": IMAGE, "draws": False, "exports": len(GROUPS), "windows": dict(WINDOWS)}
