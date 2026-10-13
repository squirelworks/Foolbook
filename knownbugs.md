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

- Field text comes through. Rectangles, ellipses, lines, and polygons are drawn from bounds and vertices, scaled from twips. Groups, buttons, bitmaps, and the other object kinds are not.
- Scripts run through the same small OpenScript subset as a `.tbk`. Most of the language is not.
- A `.tbx` written by the editor is the folder Foolbook itself writes. It is not a SumTotal export.

