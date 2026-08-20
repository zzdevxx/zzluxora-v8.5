"""
app.py — AppContext: service registry (ADR-2).

Single source of truth for app-wide services:
  - config (AppConfig)
  - fixture_manager (FixtureManager)
  - song_store (SongStore)
  - artnet (ArtNetController)

Panels receive `ctx: AppContext` and read services from it — no global
singletons scattered across modules (unlike v7).
"""
from __future__ import annotations

from config import AppConfig, app_config
from core.fixture_manager import FixtureManager
from core.song_store import SongStore
from engines.artnet_sender import ArtNetController


class AppContext:
    """Registry of app services, injected into panels."""

    def __init__(self) -> None:
        self.cfg: AppConfig = app_config()
        self.fixtures: FixtureManager = FixtureManager()
        self.songs: SongStore = SongStore()
        self.artnet: ArtNetController = ArtNetController()
        # Apply saved defaults from config.ini (universe default 0 = ESP32 firmware)
        self.artnet.target_ip = self.cfg.artnet_default_ip
        self.artnet.universe = self.cfg.artnet_default_universe
        self.artnet.fps = self.cfg.artnet_default_fps

        # Project state
        self.project_filepath: str | None = None
        self.project_name: str = "Untitled.zlx"
        self.project_created_at: str = ""

    # ── Project helpers ────────────────────────────────
    def set_project(self, filepath: str) -> None:
        from pathlib import Path
        self.project_filepath = filepath
        self.project_name = Path(filepath).name
