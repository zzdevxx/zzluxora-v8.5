"""
core/paths.py — app base path resolution (dev vs frozen).

Dev mode:      project root (next to main.py)
Frozen mode:   %APPDATA%\\zzluxora (install dir is read-only under Program Files)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_APP_NAME = "zzluxora"


def get_app_base() -> Path:
    """Writable base path for user data (fixtures, chases, config, logs).

    Frozen: %APPDATA%/zzluxora — install dir under Program Files is read-only.
    Dev:    project folder (parent of this file's package root).
    """
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA") or Path.home()) / _APP_NAME
        base.mkdir(parents=True, exist_ok=True)
        return base
    return Path(__file__).resolve().parent.parent


def get_bundle_base() -> Path | None:
    """Read-only PyInstaller bundle path (_MEIPASS), or None in dev."""
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else None


def get_data_dir(subdir: str = "") -> Path:
    """Return (and create if needed) a writable data subdirectory.

    Args:
        subdir: optional subdirectory name under the app base (e.g. "chases").

    Returns:
        Path to the (existing) directory.
    """
    base = get_app_base() / subdir if subdir else get_app_base()
    base.mkdir(parents=True, exist_ok=True)
    return base
