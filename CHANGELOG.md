# Changelog

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
