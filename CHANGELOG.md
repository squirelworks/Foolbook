# Changelog

## 1.0.7 — 2026-10-25

1.0.6 cleared the 1.0.5 revisions. This stays the version. A small change after it is `1.0.7r1`, then `r2`, and so on. A new version number waits for a real step.

- A book opened from the command line starts on the first page.
- A click on P0 or P1 runs the page's `send next`. The window was calling that handler without importing it, so the click did nothing.
- The type size and the indents scale with the window. A line that is wider than its box wraps. A short label that fits stays one line.

## 1.0.6 — 2026-10-25

This is the release. The `v1.0.5r1` through `v1.0.5r38` tags were interim builds. They are no longer published as releases.

What changed since 1.0.5, for a `.tbk`:

- The object store is what gets drawn. A page is its own list. A field's words are word 1 of the block at `+0x24`.
- The corner label is the page that is open, not the last page that wrote the field.
- A field is drawn in the face, point size, and weight the record names. The P400 body is Arial 12 bold. A style run can name a smaller face, which is why the copyright line is 8 point.
- The first indent word is the first line. The second is every line under it. The third is the right indent. The fourth is tab spacing and is not an inset. On the body those are 360, 360 and 310. On the P1 title the first line is 0 and the line under it is 650.
- A button picture is the bitmap stored in the book, drawn at the button's size. A transparent edge stays clear.
- A polygon is the outline in its own record, mapped onto its bounds. An arc is the open curve between its endpoints. A background fill is the colour stored on that record. A background with no fill leaves the page underneath where it does not paint.
- The window has one scale and one offset, applied before anything is drawn. The page is not shown until that scale is known.
- Next, Back, Menu, and the lesson choices run the script that was stored. A click on P0 or P1 sends next. A jump to another book leaves the first one open, and the return comes back to it.
- A text field named `correct` stays visible. That is the practice answer. The Correct rectangle, which is the answer key, stays hidden.
- Depends on `openscript_analysis` 1.0.1.

## 1.0.5r38

- The P1 title starts at the left of its box. Its first-line indent is 0. The 650 on the next word is only the line under it. Body text is unchanged, because those two words are both 360.

## 1.0.5r37

- Text is drawn in the face, point size, and weight stored on the field. The P400 body is Arial 12 bold. A style run can name a different entry, which is why the copyright line is 8 point.
- A text field named `correct` stays on the page. That is the answer on the practice questions. The Correct rectangle, which is the answer key, stays hidden.

## 1.0.5r36

- The right inset is the paragraph's right indent, not the left one. The tab spacing stays out of the picture. A field with no style runs is drawn in the face the record names. For the P400 body that face is Arial. Bold and 12-point are still not read.

## 1.0.5r35

- A field is drawn inside the margin words the record stored. A copyright inset of 720 twips is 48 pixels, and a body panel's 360 is 24.
- Saving a `.tbk` or `.sbk` writes an object store, not the page-marker shell. ToolBook has not opened one of these yet. Replacing text inside a book it already opens is `splice_text`, and that leaves the store alone.

## 1.0.5r34

- A click on a field runs the group's buttonClick when the field does not have one. The field's own script stays the mouse handlers.

## 1.0.5r33

- A shape keeps the layer it was stored on. Background objects are `background`. Page objects are `page`.

## 1.0.5r32

- A click on P0 or P1 reaches `send next`. Choosing the page in the list no longer puts it back.
- Begin, the choices, OK, Skip and Back run the quiz script. The Correct box stays hidden, so it does not mark the answer.
- Another book is drawn in the page rectangle, which is how ToolBook sizes the viewer. The book is also looked for in the folders next to the course, not only in core/.

## 1.0.5r31

- P450 draws the background bitmap that is stored in the book.
- Menu runs gotoMenuPage. With the default lesson mode, that is P900.
- Final Quiz runs gotoQuizPage. That is P10004 in this book, or P10003 when the lesson mode is the pretest. It does not open another file.
- A book name matches even when the file on disk is a different case, such as NC81BANK.SBK.

## 1.0.5r30

- The page is not drawn until it fits the window. The raw-size flash on load is gone.
- A click on P0 or P1 runs the background script, which sends next.
- The menu pictures on P900 use the group's jump: P1001, p2001, and the quiz call.
- A quiz choice is the field the book stored. It is not labeled correct or incorrect, and the window does not say which it was.
- A jump to nida81 uses the book beside the course, or one folder up, before the stub in core/.

## 1.0.5r29

- README starts with the from-scratch terminal block: clone or pull `main`, activate `.venv`, install, and open.

## 1.0.5r28

- The equipment bar on P300 is drawn on the frame, not under it. A run of spaces in the copyright is one space.

## 1.0.5r27

- The field font is read. A Wingdings `w` is drawn as a bullet. The words stay in Arial.

## 1.0.5r26

- A jump to another book leaves the first one open. The shell's return, `go to page (nextpage) of book(lastbook)`, comes back to it.
- A blank line at the end of a label no longer pushes the words out of the button.

## 1.0.5r25

- Next, Back, and the other picture buttons take a click. Their script runs. `go to page("P1150")` is the same jump as `go to page "P1150"`.

## 1.0.5r24

- The window has one scale and one offset, and both are applied to every bound before anything is drawn. A picture now grows and shrinks with the text. Tk's canvas scale was moving the picture and leaving its pixels behind.

## 1.0.5r23

- A transparent button's grey matte stays clear. Tk was painting those pixels black, which covered the title, the copyright, and the menu frame.

## 1.0.5r22

- Button pictures need Pillow. Without it the menu frame, the cyan buttons, and the text-panel picture were drawn as white rectangles. The bytes were already in the book.

## 1.0.5r21

- The corner field named Page# shows the page that is open. The saved text was the last page that wrote it: P1270 on the Text background, P1291 on the Overlay background, P100 on the menu background.

## 1.0.5r20

- `go to page` keeps the window that is already up. A background with a fill replaces it. A background without one leaves it, and direct objects stay only on the page now showing. Opening P420 by itself does not invent the chips from P400. An arc is the unfilled curve between its endpoints. The analysis package is v1.0.0r19.

## 1.0.5r19

- An arc is the long sweep of its two rays, filled with the record colour. The fan-out marks on P1150 are no longer boxes. The analysis package is v1.0.0r18.

## 1.0.5r18

- A page with no background fill leaves the previous page where it does not paint. P420 keeps the chips from P410.

## 1.0.5r17

- A page header keeps the coloured bar and drops the grey matte around it. The analysis package is v1.0.0r17.

## 1.0.5r16

- A field with a border is drawn as that frame, and the words are kept inside it. A transparent field still has no box. The analysis package is v1.0.0r16.

## 1.0.5r15

- A button picture is drawn at the button's size. The up face is used unless the button is disabled, pressed, or a checked check box or radio button.
- The four bitmaps that lived in the file table are included. The analysis package is v1.0.0r15.

## 1.0.5r14

- A label stays on one line. The box no longer breaks 7400, INTRODUCTION, or Digital Circuit in the middle of a word. A wide field of near-white text is drawn dark so it shows on the white panel.

## 1.0.5r13

- A `.tbk` with an object store is read from that store. Pages follow the book's page list. A field's text is word 1 of the block at `+0x24`. A class `0x10` outline is mapped onto its bounds. The background fill is the colour at `+0x5B`. A button picture is the bitmap one less than the stored id.

## 1.0.5r12

- The page is scaled to the window after the canvas has a size, and centered. A resize during the first paint is not dropped, so a page no longer stays at its raw size in the corner.

## 1.0.5r11

- A page that already has Back or Next is not given a second copy. The corner stub that repeats one is not drawn. The page is fitted again once the window has a size.
- The analysis package is v1.0.0r12.

## 1.0.5r10

- The analysis package is v1.0.0r11, the one that finds the book script.

## 1.0.5r9

- A `.tbk` or `.sbk` is scanned for compressed handlers, not only the plain words `to handle`. Handlers outside a page are the book script.

## 1.0.5r8

- `--fbk` is not a reader command. FoolbookEditor writes the `.fbk` and the `.fsk`.
- `--freshstart` works again. The converter had taken its place.

## 1.0.5r7

- `python3 -m foolbook --fbk book.tbk` writes `book.fbk` beside the source. An `.sbk` writes an `.fsk`. A folder of books is converted in one run. A TBKX is written the same way.
- The file is what the reader loaded. A button bitmap is still not in a `.tbk` record, so that picture is not in the `.fbk`.

## 1.0.5r6

- A script's `to get` and `to set` blocks are handlers, not just `to handle`. The NIDA system books are written that way.
- A button picture is loaded from beside the book when the path is not already a file.

## 1.0.5r5

- `cryptography` is installed with Foolbook. Opening a book reads the student file, and that import was missing from the package.

## 1.0.5r4

- A system-book page is kept when its name is not `P…`. `tb80hyp` keeps `URL Stuff` and `ChooseFromTextLinesDlg`. An unnamed page is `Page0`.
- `enterBook` runs once when a book opens. A handler closed with `end`, including an `if` that uses the same word, runs through.
- A request for `tb80r.sbk`, `tb80anm.sbk`, or `tb80hyp.sbk` opens the `.fsk` in `core/` first. Those three files were built from the TBKX exports. The raw `.sbk` is the fallback.
- Depends on `openscript_analysis` `v1.0.0r10`.

## 1.0.5r3

- The page is fitted inside the window. A drawing that did not start at the corner was shifted off the top and the left. The window itself opens within the screen.
- A class `0x10` record is no longer also drawn as a rectangle. The pin keeps the outline from its vertices.

## 1.0.5r2

- A class `0x10` irregular polygon is read from its own record. The count is at body `+0x30` and the vertices are at body `+0x38`. The outline is mapped onto the bounds at body `+0x0F`, which moves a shared pin outline and scales a house outline. The fill is the RGB at body `+0x1B`. The `14 00 00` scan is no longer how a polygon is found. A pattern other than `0xFE` is still drawn as that solid color.

## 1.0.5r1

- A page mark is `80 65` or `81 65`, then `00 05 00 02 02`. `81 65` is a nested page. In `9e954d01.tbk`, P440 and P2920 are their own pages instead of staying inside the page before them.

## 1.0.5

- A polygon outline is drawn at its page position, not at the outline's own coordinates. Point lists that fall outside the lesson page are not drawn. P430 no longer fills the window with stacked yellow shapes.
- A Next or Back button moves along the page list when its script does not.

## 1.0.4

- Script expansion depends on `openscript_analysis` `v1.0.0r9`. That release reads the keyword count from byte 0, indexes keywords by id, copies a back-reference from the input, and treats `0xFF` as a new character plus a count.
- The viewer's own `.tbk` decoder stops on a `0x00` literal, matching that release. It still does not follow a back-reference that lands on another back-reference.

## 1.0.3

- A book is read to the end, and the edits in it are applied, before the window opens. A later copy of a page replaces the earlier one.
- One page is one surface. Text, graphics, and buttons use the bounds the book stored. There is no separate text pane and no invented Back/Next bar.
- A `.tbk` widget keeps the twip bounds in its record. The name, the field text, and a button script between that widget and the next one stay with it.
- Next and Back follow that script, or move along the settled page list. A quiz click is checked against the page's Answer property.
- A TBX follows `Book.Pages`. Background objects sit under the page's objects. A button keeps the caption or the bitmap the book named.
- The polygon and rectangle placement from 1.0.2 is still how a `.tbk` drawing is placed. Twip `0, 0` is the window origin.

## 1.0.2

- A polygon record becomes the point array `Polygon` is given. Each twip is `(coord * dpi + 720) / 1440`.
- Rectangle, ellipse, round rect, polyline, and arc use the same conversion. `Pie` is not called. A bracket does not invent its points.
- Each object is placed from its twip bounds. Twip `0, 0` is the window origin.
- A `.tbk` page now carries those shapes into the viewer.
- NearScript heap, value stack, resource session, book API, and object layer.
- One module file each for `bas`, `rtm`, `utl`, `rcr`, `w16`, `w32`, and `w64`.

## 1.0.1r2

- Content rectangle extraction. Bounds at -16, fill at -4, marker `01 00 00 04`.

## 1.0.1

- Rudimentary graphics in the GUI viewer: explicit polygons and bounds-only rectangles from the page blob.
- System-book contract: core `.fsk` load first, user `.fsk` load after as mods.
- `projectphilosophy.md` added.

## 1.0.0

First release.
