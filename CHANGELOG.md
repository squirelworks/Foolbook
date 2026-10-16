# Changelog

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
