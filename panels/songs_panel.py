"""
panels/songs_panel.py — Songs: daftar lagu + hasil analisis + pilih active.

Klik item → set current_song_id (dipakai header Play untuk realtime playback).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
)

from widgets.empty_state import EmptyState
from widgets.panel_base import BasePanel, Card


class SongsPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Songs", "Daftar lagu & hasil analisis mood")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        card = Card()
        lay = card.body()
        lay.addWidget(self._label("Library", "cardTitle"))

        self.song_list = QListWidget()
        self.song_list.itemSelectionChanged.connect(self._on_select)
        lay.addWidget(self.song_list)

        self.detail_lbl = QLabel("")
        self.detail_lbl.setObjectName("value")
        self.detail_lbl.setWordWrap(True)
        lay.addWidget(self.detail_lbl)

        row = QHBoxLayout()
        self.analyze_btn = QPushButton("+ Analyze Audio…")
        self.analyze_btn.clicked.connect(self._go_analyze)
        row.addStretch(1)
        row.addWidget(self.analyze_btn)
        lay.addLayout(row)
        self.add_widget(card)

        self.empty = EmptyState("02", "Belum ada lagu",
                                "Tambahkan lagu lewat panel Analyze")
        self.add_widget(self.empty)
        self.add_stretch()

    def _go_analyze(self) -> None:
        parent = self.window()
        if hasattr(parent, "_show_panel"):
            parent._show_panel("analyze")

    def _on_select(self) -> None:
        item = self.song_list.currentItem()
        if not item:
            self.detail_lbl.setText("")
            return
        idx = self.song_list.row(item)
        song = self.ctx.songs.list()[idx]
        sid = self.ctx.songs.ids()[idx]
        self.ctx.songs.current_song_id = sid

        va = song.get("va", {})
        scenes = song.get("scenes", [])
        text = (f"{song.get('filename', '?')}\n"
                f"Arousal: {va.get('arousal', 0):.3f} · Valence: {va.get('valence', 0):.3f} · "
                f"Quadrant: {va.get('quadrant', '?')}\n"
                f"Scenes: {len(scenes)} · Play via header ▶")
        self.detail_lbl.setText(text)

    def refresh(self) -> None:
        self.song_list.clear()
        for idx, song in enumerate(self.ctx.songs.list()):
            va = song.get("va", {})
            q = va.get("quadrant", "?")
            item = QListWidgetItem(
                f"02  {song.get('filename', '?')}   ·   {q}")
            self.song_list.addItem(item)
        self.empty.setVisible(not self.ctx.songs.list())

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
