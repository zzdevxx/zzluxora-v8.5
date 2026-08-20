"""
panels/program_tabs/scenes_tab.py — Scenes (feedback §10).

Kotak kiri: song list. Kotak kanan: mapping scene hasil analyze (section lagu:
intro/verse/chorus/bridge/outro dengan warna). Kumpulkan scene → Chase.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout,
    QWidget,
)

from engines.chase import Chase, save_chase
from widgets.panel_base import Card


class ScenesTab(QWidget):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Kiri: songs
        left = Card()
        llay = left.body()
        llay.addWidget(self._label("Songs", "cardTitle"))
        self.song_list = QListWidget()
        self.song_list.itemSelectionChanged.connect(self._on_song_select)
        llay.addWidget(self.song_list)
        root.addWidget(left, 1)

        # Kanan: scenes
        right = Card()
        rlay = right.body()
        head = QHBoxLayout()
        head.addWidget(self._label("Scene Mapping", "cardTitle"))
        head.addStretch(1)
        self.chase_btn = QPushButton("Buat Chase")
        self.chase_btn.setObjectName("primaryButton")
        self.chase_btn.setEnabled(False)
        self.chase_btn.clicked.connect(self._on_make_chase)
        head.addWidget(self.chase_btn)
        rlay.addLayout(head)
        self.scene_list = QListWidget()
        rlay.addWidget(self.scene_list)
        root.addWidget(right, 2)

    def refresh(self) -> None:
        self.song_list.clear()
        for idx, song in enumerate(self.ctx.songs.list()):
            item = QListWidgetItem(song.get("filename", f"Song {idx+1}"))
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.song_list.addItem(item)

    def _on_song_select(self) -> None:
        item = self.song_list.currentItem()
        self.scene_list.clear()
        self.chase_btn.setEnabled(item is not None)
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        songs = self.ctx.songs.list()
        if idx is None or idx >= len(songs):
            return
        song = songs[idx]
        for sc in song.get("scenes", []):
            start = float(sc.get("start", 0))
            end = float(sc.get("end", start + 1))
            color = sc.get("dmx", {})
            label = sc.get("label", "auto")
            self.scene_list.addItem(
                f"{label:8s}  {start:6.1f}-{end:6.1f}s  "
                f"D{color.get('d', 0):3d}  "
                f"RGB({color.get('r', 0):3d},{color.get('g', 0):3d},{color.get('b', 0):3d})")

    def _on_make_chase(self) -> None:
        item = self.song_list.currentItem()
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        songs = self.ctx.songs.list()
        if idx is None or idx >= len(songs):
            return
        song = songs[idx]
        sid = self.ctx.songs.ids()[idx]
        chase = Chase(name=f"{song.get('filename', 'song')} (chase)", song_id=sid)
        for sc in song.get("scenes", []):
            dmx = sc.get("dmx", {})
            start = float(sc.get("start", 0))
            end = float(sc.get("end", start + 1))
            chase.add_step(
                start=start, duration=max(0.1, end - start),
                drgbw={"r": int(dmx.get("r", 0)), "g": int(dmx.get("g", 0)),
                       "b": int(dmx.get("b", 0)), "w": int(dmx.get("w", 0)),
                       "dimmer": int(dmx.get("d", 200))},
                label=sc.get("label", ""))
        save_chase(chase)
        parent = self.window()
        if parent and hasattr(parent, "_set_status"):
            parent._set_status(f"Chase '{chase.name}' dibuat", "ok")

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
