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
- Text is still garbled when it is not rich text. A field that is rich text is reduced to the words, so the font table is no longer shown. The font itself, such as Arial, is not applied.
- Field text comes through only as that raw string. Rectangles, ellipses, lines, and polygons are drawn from bounds and vertices, scaled from twips. Groups, buttons, bitmaps, and the other object kinds are not.
- Scripts run through the same small OpenScript subset as a `.tbk`. Most of the language is not.
- A `.tbx` written by the editor is the folder Foolbook itself writes. It is not a SumTotal export.

What is learned from a `.tbk` has to be applied to a `.tbx`, and the other way around. The two readers do not share that work yet.

## Notes

`.txt`, `.text`, `.md`, `.markdown`, `.rst`, `.log`, and `.rtf` open in the viewer. An `.rtf` shows the words, not the font table. The font is not applied.



