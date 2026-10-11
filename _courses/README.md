# _courses/

Sample courses live here. Each course is a folder with a `.fbk` (the standard) and a `.json` working copy.

```bash
python3 -m foolbook _courses/using_grok/using_grok.fbk
python3 -m foolbook --menu _courses/catalog.json
python3 -m foolbook --catalog                    # rebuild catalog.json from the .fbk files
```

`--catalog` scans this folder for `.fbk` files and rewrites `catalog.json`. Subject and module come from optional `subject` / `module` keys in the book; otherwise the parent folder is the module and the subject is "Courses".
