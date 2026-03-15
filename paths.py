"""PyInstaller-aware path resolution."""

import os
import sys


def resolve_bundle_path(filename: str) -> str:
    """Resolve path for read-only data bundled into the exe."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def resolve_runtime_path(filename: str) -> str:
    """Resolve path for read/write data alongside the exe."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)
