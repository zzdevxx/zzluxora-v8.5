"""
config.py — AppConfig (configparser-backed, thread-safe).

Sections:
  [General]  — version, last project
  [UI]       — sidebar state, theme (locked to dark)
  [Audio]    — last_audio_dir, sample_rate
  [ArtNet]   — default_ip, default_universe, default_fps
  [Color]    — active_va_preset
  [Fixtures] — search paths (fallback chain)

File location:
  - Dev:   <project root>/config.ini
  - Frozen: %APPDATA%/zzluxora/config.ini
"""
from __future__ import annotations

import configparser
import logging
from pathlib import Path
from threading import Lock

from core.paths import get_app_base

logger = logging.getLogger(__name__)


def _resolve_config_path() -> Path:
    return get_app_base() / "config.ini"


class AppConfig:
    """Thread-safe wrapper around configparser with sensible defaults."""

    DEFAULTS = {
        "General": {
            "version": "8.5.0",
            "last_project": "",
        },
        "UI": {
            "sidebar_collapsed": "false",
            "theme": "dark",  # locked to dark
        },
        "Audio": {
            "last_audio_dir": "",
            "sample_rate": "22050",
        },
        "ArtNet": {
            "default_ip": "127.0.0.1",
            "default_universe": "0",
            "default_fps": "30",
        },
        "Color": {
            "active_va_preset": "Default Praise",
        },
        "Fixtures": {
            "search_paths": "fixtures",
        },
    }

    def __init__(self, path: Path | None = None):
        self._path = path or _resolve_config_path()
        self._cfg = configparser.ConfigParser()
        self._lock = Lock()
        self._load()

    # ── IO ─────────────────────────────────────────────
    def _load(self) -> None:
        with self._lock:
            if not self._path.exists():
                for section, opts in self.DEFAULTS.items():
                    self._cfg[section] = opts
                self._save_unlocked()
                return
            try:
                self._cfg.read(self._path, encoding="utf-8")
            except (OSError, configparser.Error) as exc:
                logger.warning("Corrupt config %s — falling back to defaults: %s", self._path, exc)
                self._cfg = configparser.ConfigParser()
                for section, opts in self.DEFAULTS.items():
                    self._cfg[section] = opts
            for section, opts in self.DEFAULTS.items():
                if not self._cfg.has_section(section):
                    self._cfg[section] = opts
                else:
                    for key, val in opts.items():
                        if not self._cfg.has_option(section, key):
                            self._cfg.set(section, key, val)

    def _save_unlocked(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w", encoding="utf-8") as fh:
                self._cfg.write(fh)
        except OSError as exc:
            logger.warning("Config write failed (read-only FS?): %s", exc)

    def save(self) -> None:
        with self._lock:
            self._save_unlocked()

    # ── Accessors ──────────────────────────────────────
    def get(self, section: str, key: str, fallback: str = "") -> str:
        with self._lock:
            return self._cfg.get(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        raw = self.get(section, key, "").strip().lower()
        if raw in ("true", "1", "yes", "on"):
            return True
        if raw in ("false", "0", "no", "off"):
            return False
        return fallback

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return int(self.get(section, key, str(fallback)))
        except ValueError:
            return fallback

    def get_list(self, section: str, key: str, sep: str = ",") -> list[str]:
        raw = self.get(section, key, "")
        return [x.strip() for x in raw.split(sep) if x.strip()]

    def set(self, section: str, key: str, value: str) -> None:
        with self._lock:
            if not self._cfg.has_section(section):
                self._cfg.add_section(section)
            self._cfg.set(section, key, str(value))
            self._save_unlocked()

    # ── Convenience properties ─────────────────────────
    @property
    def path(self) -> Path:
        return self._path

    @property
    def sidebar_collapsed(self) -> bool:
        return self.get_bool("UI", "sidebar_collapsed", False)

    @sidebar_collapsed.setter
    def sidebar_collapsed(self, val: bool) -> None:
        self.set("UI", "sidebar_collapsed", "true" if val else "false")

    @property
    def last_audio_dir(self) -> str:
        return self.get("Audio", "last_audio_dir", "")

    @last_audio_dir.setter
    def last_audio_dir(self, val: str) -> None:
        self.set("Audio", "last_audio_dir", val)

    @property
    def artnet_default_ip(self) -> str:
        return self.get("ArtNet", "default_ip", "127.0.0.1")

    @property
    def artnet_default_universe(self) -> int:
        return self.get_int("ArtNet", "default_universe", 0)

    @property
    def artnet_default_fps(self) -> int:
        return self.get_int("ArtNet", "default_fps", 30)

    @property
    def active_va_preset(self) -> str:
        return self.get("Color", "active_va_preset", "Default Praise")

    @active_va_preset.setter
    def active_va_preset(self, val: str) -> None:
        self.set("Color", "active_va_preset", val)


# Module-level singleton (lazy)
_singleton: AppConfig | None = None


def app_config() -> AppConfig:
    global _singleton
    if _singleton is None:
        _singleton = AppConfig()
    return _singleton
