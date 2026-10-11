# _debug/

Debug files live here. The package is only used when `--debug` is passed.

```bash
python3 -m foolbook --debug              # files present and checksums match
python3 -m foolbook --debug complete     # full check, writes checksums.json
python3 -m foolbook --debug engine       # one module
```

Each run writes its results to `_debug/db-<timestamp>`. Those files are gitignored.

Loading a `.tbk` or `.sbk` writes the decoded handler source to `_debug/decoded/<book>-<timestamp>.json`. That is the record of what the decoder produced. `.fbk` and `.fsk` already hold source and are not written there.
