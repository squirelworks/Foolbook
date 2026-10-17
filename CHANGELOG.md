# Changelog

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
