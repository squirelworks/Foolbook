"""ToolBook books open here.

A file that is ToolBook on the inside is opened by ToolBook rules, whatever
its name is. Foolbook drawing changes do not come through this door.
"""

from toolbook.format import is_toolbook
from toolbook.open import open_book

__all__ = ["is_toolbook", "open_book"]
