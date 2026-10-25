# Known bugs

Things that are still wrong in 1.0.8.

## OpenScript

The reader runs the handlers it has decoded for this course: next and previous, the menu and quiz calls, and a click that is `go to page`. Most other OpenScript does not run.

- A script that is only bytecode is not executed.
- A handler that lives in a system book is run only when that book was decoded and the call is one the reader knows. The rest are skipped.
- The scored test still stops on the results page. The percent stays at the placeholder, and OK does not open the review page.

## Paint

- An 8×8 pattern tile is not drawn. A class `0x10` pattern other than solid fill (`0xFE`) is painted as the record's colour.
- A style run is used when it names a font or a colour. Two flag bits in the font entry, `0x10` and `0x40`, are unread, as are the words at `+0x30` and `+0x32`.

## Writing a book back

`write_store` writes an object store. ToolBook has not opened one of those files. `splice_text` can replace a string of the same length inside a book ToolBook already opens, and it leaves the rest of the store alone. A script is not written back as bytecode.

## Other formats

A `.tbk` button picture is the bitmap embedded in the file. A TBX button picture is a path beside `Book.xml`. The two are still different readers. An `.rtf` shows the words. The font is not applied.
