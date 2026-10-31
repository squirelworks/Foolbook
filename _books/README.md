# _books/

The books that ship with Foolbook. Each book is a folder with a `.fbk` and a `.json` working copy.

```bash
python3 -m foolbook _books/using_grok/using_grok.fbk
python3 -m foolbook --menu _books/catalog.json
python3 -m foolbook --catalog                    # rebuild catalog.json from the .fbk files
```

`--catalog` scans this folder for `.fbk` files and rewrites `catalog.json`. Subject and module come from optional `subject` / `module` keys in the book; otherwise the parent folder is the module and the subject is "Courses".

Using Foolbook is generated. Edit FoolbookEditor's `examples/using_foolbook.py` and run it into `_books/using_foolbook`, rather than editing the `.fbk` or `.json` by hand.
