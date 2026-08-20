"""
panels/program_tabs/analyze_tab.py — Analyze in tab (feedback §9).

Tambah di atas AnalyzePanel yang ada: status deskripsi progress (3 detik),
Remove Song, Export to Scene. Tombol Analyze disabled sampai file dipilih —
sesuai feedback "disabled rules".
"""
from __future__ import annotations

import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget,
)

from panels.analyze_panel import AnalyzePanel as _AP
from widgets.panel_base import Card


class AnalyzeTab(QWidget):
    """Wrap AnalyzePanel + kontrol daftar song (Remove/Export)."""

    def __init__(self, ctx, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        # Status / deskripsi progress (3 detik opacity)
        self.status_card = Card()
        slay = self.status_card.body()
        self.stage_lbl = QLabel("Siap — pilih file audio untuk mulai.")
        self.stage_lbl.setObjectName("hintLabel")
        slay.addWidget(self.stage_lbl)
        root.addWidget(self.status_card)

        self.analyze = _AP(self.ctx)
        root.addWidget(self.analyze, 1)

        # Song library quick actions
        lib = Card()
        llay = lib.body()
        llay.addWidget(self._label("Song Library", "cardTitle"))
        self.song_list = QListWidget()
        llay.addWidget(self.song_list)
        btn_row = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Song")
        self.remove_btn.setObjectName("dangerButton")
        self.remove_btn.clicked.connect(self._on_remove_song)
        btn_row.addWidget(self.remove_btn)
        self.export_btn = QPushButton("Export to Scene")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.clicked.connect(self._on_export_scene)
        btn_row.addWidget(self.export_btn)
        btn_row.addStretch(1)
        llay.addLayout(btn_row)
        root.addWidget(lib)

        self._stage_timer = QTimer(self)
        self._stage_timer.setSingleShot(True)
        self._stage_timer.timeout.connect(self._clear_stage)

        self.refresh()

    def refresh(self) -> None:
        self.song_list.clear()
        for idx, song in enumerate(self.ctx.songs.list()):
            name = song.get("filename", f"Song {idx + 1}")
            self.song_list.addItem(name)

    # ── Stage description (progress, 3 detik) ──────────
    def set_stage(self, msg: str, kind: str = "info") -> None:
        self.stage_lbl.setText(msg)
        self.status_card.setProperty("kind", kind)
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)
        self._stage_timer.start(3000)

    def _clear_stage(self) -> None:
        self.stage_lbl.setText("")

    # ── Actions ────────────────────────────────────────
    def _on_remove_song(self) -> None:
        item = self.song_list.currentItem()
        if not item:
            self.set_stage("Pilih song di daftar dulu.", "warn")
            return
        idx = self.song_list.row(item)
        ids = self.ctx.songs.ids()
        if idx < 0 or idx >= len(ids):
            return
        name = item.text()
        self.ctx.songs.remove(ids[idx])
        self.refresh()
        self.set_stage(f"Song dihapus: {name}", "ok")

    def _on_export_scene(self) -> None:
        item = self.song_list.currentItem()
        if not item:
            self.set_stage("Pilih song yang sudah dianalisa dulu.", "warn")
            return
        idx = self.song_list.row(item)
        ids = self.ctx.songs.ids()
        if idx >= len(ids):
            return
        song = self.ctx.songs.get(ids[idx])
        if not song:
            return
        scenes = song.get("scenes", [])
        # Export → chase frames untuk ArtNet header
        frames = _AP._scenes_to_frames(scenes)
        self.ctx.artnet.chase_frames = frames
        self.set_stage(f"Export {len(scenes)} scene ke ArtNet.", "ok")

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
