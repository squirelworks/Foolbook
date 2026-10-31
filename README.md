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

- Passed a path: opens that book on its first page.
- Started with no path: opens Using Foolbook, the picture book that ships with it.
- Launched by Foolcourse: Foolcourse passes the book path, and Foolbook opens it.

```bash
python3 -m foolbook path/to/Book.xml            # a TBX folder, read from Book.xml
python3 -m foolbook                             # Using Foolbook
python3 -m foolbook --cli path/to/book          # terminal viewer
python3 -m foolbook --export path/to/book.tbk   # write an .fbk beside it
python3 -m foolbook --export path/to/folder     # that folder first, then the folders inside it
python3 -m foolbook --menu _books/catalog.json
python3 -m foolbook --catalog                   # rebuild _books/catalog.json
python3 -m foolbook --bin path/to/res.bin book.tbk   # override keyword table for .tbk/.sbk
```

`--export` on an `.sbk` writes an `.fsk`. A file already written is left alone. `--force` writes it again. A file that will not parse is named, and the rest continue.

The window opens across most of the screen. A resize is remembered for the next book. A click redraws once, at that size.

A jump to another book opens the `.tbk` or `.sbk` when that file is there. A settled `.fbk` or `.fsk` beside it is the copy that opens. A stub is not. The books the course names start opening in the background, up to three at a time.

A course module is the driver. Foolcourse decides which course, then launches Foolbook with the book path.

## Layout

```
Foolbook/
  foolbook/                 # entry point
  engine/                   # parse and interpret
  viewer/                   # CLI and GUI
  menu/                     # course menu
  progress/                 # progression tracking (scaffold)
  core/                     # system books (.fsk standard, .sbk compatible)
  _books/                   # the books that ship with Foolbook, and the catalog
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

A page may carry `shapes`. The window draws the page on screen. The other pictures stay in the file until that page is shown. Coordinates are pixels. A `.tbk` is not drawn from its page stream. The object store is read into these shapes, and the page stream is decoded to handlers.

- `rect` and `ellipse`: `x`, `y`, `w`, `h`, `fill`, `outline`. `bounds` as `[x, y, w, h]` works in place of those four.
- `roundrect`: a `rect` with quarter-circle corners. `radius` is in pixels, 8 when missing, and never more than half the short side.
- `line` and `polygon`: `points` as `[[x, y], ...]`. A class `0x10` outline is mapped onto the object's bounds.
- `curve`: `points` as `[[x, y], ...]`. It is drawn as straight segments through the points until a real curve is drawn.
- `stroke` on any of those is the outline or line width in pixels. Missing means 1.
- `arc`: the open curve between its endpoints. It is not filled. An `.fbk` arc that stores `start` and `sweep` (degrees, zero east, counterclockwise) is that part of the ellipse in its bounds.
- `pie`: the same `start` and `sweep`, filled back to the centre. Missing angles are 0 and 90.
- `chord`: the same `start` and `sweep`, closed by the straight line between the two ends and filled.
- `hotspot`: `x`, `y`, `w`, `h`, and an `item`. It is not drawn. A click inside it follows the item.
- `text`: `x`, `y`, `text`, and the face, `size`, `bold`, and `italic` from the field's font entry. An `.fbk` text shape may also set `underline`, and `align` as `left`, `center`, or `right`. `marginL` is the first-line indent. `indentRest` is the indent of every line under it, when the two differ. `marginR` is the right indent.
- `button`: the picture stored for that button, or a caption when there is no picture.
- `image`: `x`, `y`, and either `src` (a file beside the book) or `data` (base64 PNG or GIF).

A field named Page# shows the page that is open. A text field named `correct` is the practice answer and stays on the page. The Correct rectangle is the answer key and stays hidden.

A new install opens `using_foolbook`. Its First Light button opens `first_light`. Both are folders under `_books/`.

## A click on a button

The button's script runs first. A script with no `to handle` line, which is how FoolbookEditor saves one, is read as the click. Then the page's `buttonClick` runs, then the button's `item` (a page, a book, or the Next or Back label), each only if nothing before it changed the page. `engine.engine.click` is that order without a window, and `engine/test_click_order.py` tests it.

A script shows or hides a shape by the name the editor gave it: `show "Feedback"`, `hide shape "Hint"`, `show "Hint" of page "P2"`. The kind does not matter. `show button "Next"` with a class still works.

In a ToolBook file, `go to next page` and `go to previous page` (or `prev`, with or without `of this book`) go to the page beside this one in the book's order. In a Foolbook book, `send next` and `send previous` are the Next and Back buttons, and take the page's Next or Back item first.

`engine.subset.check(script)` checks a script without running it and returns errors with line numbers: a quote left open at the end of the script, an `if`, `step`, `while`, or `linkDLL` block left open, an `end` with nothing open, a `go to` with no page. FoolbookEditor shows the first one. It does not stop a save.

A quiz the editor writes is graded by the choice index on the button (`choice`, into `page.quiz.choices`), not by the button's name, in a book of Foolbook's own format. A ToolBook quiz is still graded by the clicked name against the page's Answer.

Each graded page leaves `{"page", "choice", "right"}` in the book's `props["results"]`, one entry per page, the last answer winning. `engine.choice.score(state)` is (right, answered). It is kept in memory and not written to Foolcourse yet.

Two script lines put a quiz back. `send tryAgain` hides the page's feedback shapes and keeps the book's results. `send resetScore` forgets the results. Neither moves the page.

## Page scripts

A page's script runs when the page is shown. A page script with no `to handle` line is the page's `enterPage`. A script with `to handle enterPage` works the same way. `engine/test_page_enter.py` tests it.

`to handle leavePage` runs before the next page is shown. If it goes to a page, that page is shown instead. `engine/test_page_leave.py` tests it.

## Design notes

- Foolbook is the viewer. A course module drives which book it opens.
- The entry point stays in `main/`. Supporting work lives in subdirectories.
- The engine is responsible for understanding the files the user points at.
- Editing is not in this repository. It lives in FoolbookEditor, which calls `foolbook.core` for the work.

