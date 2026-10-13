# Known bugs

Things that are wrong in the current release.

## ToolBook implementation is still broken

Opening a `.tbk` or `.sbk` does not yet show the book ToolBook would show.

- The page stream is only partly read. Field text and a best-effort handler decode come out. Graphics, object bounds, and most of the property tree do not.
- Page order is the order of the records in the file. A book can open on a high id such as P20000 and walk back toward P0. That is not a reading order.
- Handlers that do decode are run with the small OpenScript subset already implemented. Most of the language is not.
- A `.tbk` written by FoolbookEditor is a shell. ToolBook has not been shown to open one.
