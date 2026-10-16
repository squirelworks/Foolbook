"""ToolBook-shaped modules. One file each.

`bas`, `rtm`, `utl`, `rcr`, `w16`, `w32`, `w64`. Loading one does
not import the others. `w64` is a scaffold. It is not an 8.1 binary.

The chip plan is `arch.plan`. The Python models are what a later
macOS, iOS, or Android host would run. The NE images stay on `i86`.
"""

from .arch import plan
from .host import ORDER, load

__all__ = ["ORDER", "load", "plan"]
