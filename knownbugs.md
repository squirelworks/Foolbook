# Known bugs

Things that are wrong in the current release.

## ToolBook is settled, and it is still not ToolBook

The file is read to the end before a page is shown. A later copy of a page replaces the earlier one. A later copy of an object does the same. A TBX is then ordered by `Book.Pages`. One page is one surface: the bounds the book stored, then the text or the bitmap that belongs there.

That is still not ToolBook.

- A button picture is the bitmap whose directory id is one less than the word stored in the graphics block. The 8x8 pattern tiles are not drawn.
- Field text is the handle in word 1 of the block at `+0x24`. A script that lives in another book is not run.
- Most OpenScript still does not run. A quiz is graded by comparing the clicked button's name with the page's Answer property. `handleQuizClick` itself is not run. Help, Skip, and OK do nothing.
- Next and Back move along the settled page list. A button that has its own `send next` or `send previous` uses that.
- Bitmaps are drawn only when a TBX export left the file beside `Book.xml`.
- Groups inside one page are still skipped. A nested page (`81 65`) is its own page.
- A class `0x10` pattern other than solid fill (`0xFE`) is drawn as a solid of the record's RGB. The 8×8 tile is not applied.

## TBX

`Book.xml` opens through `Book.Pages`. Text keeps the font face the file named. A button keeps its caption or its bitmap path. The rich-text face table is not drawn as words.

What a `.tbk` and a `.tbx` share is the settled page: bounds, then the thing that goes in them. The two files are still not the same reader.

## Notes

`.txt`, `.text`, `.md`, `.markdown`, `.rst`, `.log`, and `.rtf` open in the viewer. An `.rtf` shows the words. The font is not applied.
