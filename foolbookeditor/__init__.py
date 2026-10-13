"""FoolbookEditor imports Foolbook.

Only if the installed build is not the current stable.
"""

def _needs(package: str, stable: str) -> bool:
    try:
        from importlib.metadata import version
        return version(package) != stable
    except Exception:
        return True

if _needs("foolbook", "1.0.1r2"):
    import foolbook  # noqa: F401

from author.gui import main

__all__ = ["main"]
