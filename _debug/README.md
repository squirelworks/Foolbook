# _debug/

Debug files live here. The package is only used when `--debug` is passed.

```bash
python3 -m foolbook --debug              # files present and checksums match
python3 -m foolbook --debug complete     # full check, writes checksums.json
python3 -m foolbook --debug engine       # one module
```

Each run writes its results to `_debug/db-<timestamp>`. Those files are gitignored.
