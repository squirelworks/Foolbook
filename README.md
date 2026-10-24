# Foolbook

The main tool that opens a book.

Foolbook is not affiliated with Asymetrix, Click2learn, or SumTotal.  
It is a clean-room reader. It opens `.fbk` and `.tbk` books, and processes `.fsk` and `.sbk` system books. A `.tbk` object store is read as pages, field text, polygons, and button bitmaps.

## From scratch

Paste this into a terminal. It clones the repo if `~/FU/Foolbook` is not already a checkout, checks out `main` (a detached tag will not take a plain `git pull`), updates, makes the virtualenv, installs, and opens the book that ships with Foolbook.

```bash
mkdir -p ~/FU
cd ~/FU
if [ ! -d Foolbook/.git ]; then
  git clone https://github.com/squirelworks/Foolbook.git
fi
cd Foolbook
git fetch origin
git checkout -B main origin/main
git pull --ff-only origin main
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e .
python3 -m foolbook
```

`python3 -m pip` is the virtualenv pip. Do not run `pip install` outside the virtualenv. On Debian and Ubuntu that is rejected as an externally managed environment, and it will not see `cryptography` or Pillow.

If `python3 -m venv` says `No module named venv`, install the package and run the block again:

```bash
sudo apt install python3-venv python3-pip
```

Open a book you already have by putting its path last. A folder of a TBX export is opened from its `Book.xml`.

```bash
python3 -m foolbook ~/FU/NIDA_ATT/courses/9e954d01.tbk
python3 -m foolbook "/path/to/Book.xml"
```

## How it starts

- Passed a path: opens that book.
- Started with no path: asks for a file.
- Launched by a course module: the module passes the book path, and Foolbook opens it.

```bash
python3 -m foolbook path/to/Book.xml            # a TBX folder, read from Book.xml
python3 -m foolbook                           # open Using Foolbook, the picture book
python3 -m foolbook --cli path/to/book        # terminal viewer
python3 -m foolbook --menu _courses/catalog.json
python3 -m foolbook --catalog                 # rebuild _courses/catalog.json
python3 -m foolbook --bin path/to/res.bin book.tbk   # override keyword table for .tbk/.sbk
```

A course module (Foolcourse, when it exists) is the driver. It decides which course, then launches Foolbook with the book path.

## Layout

```
Foolbook/
  foolbook/                 # entry point
  engine/                   # parse and interpret
  viewer/                   # CLI and GUI
  menu/                     # course menu
  progress/                 # progression tracking (scaffold)
  core/                     # system books (.fsk standard, .sbk compatible)
  _courses/                 # sample courses and catalog
  _debug/                   # debug package (only with --debug)
  knownbugs.md
  CHANGELOG.md
```

## Formats

- `.fbk` — Foolbook book (standard). Binary envelope, compressed or not.
- `.fsk` — Foolbook system book (standard). Same envelope.
- `.json` — working copy
- `.tbk` — ToolBook book (compatibility)
- `.sbk` — ToolBook system book (compatibility)
- `.pdf`, `.ppt`, `.pptx`, `.doc`, `.docx`, `.odt` — opened as text pages. Pictures and styles are dropped. Writing those files back is FoolbookEditor.

`.fbk` and `.fsk` start with `FBK1` or `FSK1`, then a flags byte, then a JSON payload. Bit 0 of the flags means the payload is zlib-compressed. The engine reads compressed, uncompressed, and the older plain-JSON files.

The loader decodes OpenScript handlers from a `.tbk` using the clean keyword table in `engine/keywords.py`. The original ToolBook resource lives in `engine/compat/res_77.bin` and is only used if that table is missing. `.fbk` and `.fsk` already hold source and never use it.

## Graphics

A page may carry `shapes`. The window draws them for the page on screen. Coordinates are pixels. A `.tbk` is not drawn from its page stream. The object store is read into these shapes, and the page stream is decoded to handlers.

- `rect` and `ellipse`: `x`, `y`, `w`, `h`, `fill`, `outline`. `bounds` as `[x, y, w, h]` works in place of those four.
- `line` and `polygon`: `points` as `[[x, y], ...]`. A class `0x10` outline is mapped onto the object's bounds.
- `arc`: the open curve between its endpoints. It is not filled.
- `text`: `x`, `y`, `text`, and the face, `size`, `bold`, and `italic` from the field's font entry. `marginL` is the first-line indent. `indentRest` is the indent of every line under it, when the two differ. `marginR` is the right indent.
- `button`: the picture stored for that button, or a caption when there is no picture.
- `image`: `x`, `y`, and either `src` (a file beside the book) or `data` (base64 PNG or GIF).

A field named Page# shows the page that is open. A text field named `correct` is the practice answer and stays on the page. The Correct rectangle is the answer key and stays hidden.

A new install opens `using_foolbook`. Its First Light button opens the other example, `first_light`, which is shipped in the same folder.

## Design notes

- Foolbook is the viewer. A course module drives which book it opens.
- The entry point stays in `main/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Editing is not in this repository. It lives in FoolbookEditor, which calls `foolbook.core` for the work.

