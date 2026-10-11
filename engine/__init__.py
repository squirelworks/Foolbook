"""Engine: parse .tbk/.sbk and interpret OpenScript to feed Foolbook."""

from .loader import load
from .engine import run_handler, goto

__all__ = ["load", "run_handler", "goto"]
