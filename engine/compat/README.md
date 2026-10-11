# engine/compat/

Optional resources for reading existing ToolBook files.

`res_77.bin` is the original ToolBook keyword resource. Foolbook does not need it. The same keyword list lives in `engine/keywords.py` as a clean transcription, and that is what the loader uses.

The binary is only consulted when decoding a `.tbk` or `.sbk` and the clean table is missing. `.fbk` and `.fsk` never use it.
