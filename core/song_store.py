"""
core/song_store.py — Song registry (ADR-4, entity: Song).

Stores analyzed songs in memory; persistence to .zlx happens via project_io.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional


class SongStore:
    """In-memory registry of analyzed songs keyed by song_id."""

    def __init__(self) -> None:
        self._songs: dict[str, dict[str, Any]] = {}
        self.current_song_id: Optional[str] = None

    def add(self, song: dict[str, Any], song_id: str | None = None) -> str:
        """Register a song dict. Returns its song_id."""
        sid = song_id or uuid.uuid4().hex
        self._songs[sid] = song
        self.current_song_id = sid
        return sid

    def get(self, song_id: str) -> dict[str, Any] | None:
        return self._songs.get(song_id)

    def remove(self, song_id: str) -> bool:
        if song_id not in self._songs:
            return False
        del self._songs[song_id]
        if self.current_song_id == song_id:
            self.current_song_id = None
        return True

    def list(self) -> list[dict[str, Any]]:
        return [self._songs[sid] for sid in sorted(self._songs)]

    def ids(self) -> list[str]:
        return sorted(self._songs)

    def clear(self) -> None:
        self._songs.clear()
        self.current_song_id = None

    def __len__(self) -> int:
        return len(self._songs)
