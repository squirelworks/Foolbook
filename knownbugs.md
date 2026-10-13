# Known bugs

Things that are wrong in the current release.

## ToolBook implementation is still broken

Opening a `.tbk` or `.sbk` does not yet show the book ToolBook would show.

- The page stream is only partly read. Field text and a best-effort handler decode come out. Graphics, object bounds, and most of the property tree do not.
- Pages stay in the order the stream gave them. Do not sort that order.
- Handlers that do decode are run with the small OpenScript subset already implemented. Most of the language is not.
- A `.tbk` written by FoolbookEditor is a shell. ToolBook has not been shown to open one.

## TBX support is spotty, at best

`Book.xml` opens. That is not the same as showing the book.

- Page navigation is bonkers. The order of the pages, and the buttons that follow it, is not the reading order of the book.
- Text is still garbled. The rich-text protocol is not implemented, so a font table is shown as text. One page displayed the font chooser asking for Arial.
- Field text comes through only as that raw string. Rectangles, ellipses, lines, and polygons are drawn from bounds and vertices, scaled from twips. Groups, buttons, bitmaps, and the other object kinds are not.
- Scripts run through the same small OpenScript subset as a `.tbk`. Most of the language is not.
- A `.tbx` written by the editor is the folder Foolbook itself writes. It is not a SumTotal export.

What is learned from a `.tbk` has to be applied to a `.tbx`, and the other way around. The two readers do not share that work yet.

## Notes

`.txt`, `.rtf`, `.md`, and the other plain note suffixes are not opened as notes. They are handed to the `.tbk` reader.


