"""
panels/program_tabs/chase_tab.py — Chase control (feedback §11).

Layout feedback: kotak KIRI = song list, kotak KANAN = control chase
(daftar chase: Play/Stop/Delete + fade timing).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QSlider,
    QVBoxLayout, QWidget,
)

from engines.chase import Chase, list_chases, load_chase, delete_chase
from widgets.panel_base import Card


class ChaseTab(QWidget):
    def __init__(self, ctx, player=None, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.player = player
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # KIRI: song list
        left = Card()
        llay = left.body()
        llay.addWidget(self._label("Songs", "cardTitle"))
        self.song_list = QListWidget()
        self.song_list.itemSelectionChanged.connect(self._on_song_select)
        llay.addWidget(self.song_list)
        root.addWidget(left, 1)

        # KANAN: chase control
        right = Card()
        rlay = right.body()

        head = QHBoxLayout()
        head.addWidget(self._label("Chase Control", "cardTitle"))
        head.addStretch(1)
        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("successButton")
        self.play_btn.clicked.connect(self._on_play)
        head.addWidget(self.play_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        head.addWidget(self.stop_btn)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("dangerButton")
        self.del_btn.clicked.connect(self._on_delete)
        head.addWidget(self.del_btn)
        rlay.addLayout(head)

        self.chase_list = QListWidget()
        self.chase_list.itemDoubleClicked.connect(lambda _i: self._on_play())
        rlay.addWidget(self.chase_list, 1)

        # Fade control
        flay = QHBoxLayout()
        flay.addWidget(self._label("Fade", "cardTitle"))
        self.fade_slider = QSlider(Qt.Orientation.Horizontal)
        self.fade_slider.setRange(100, 5000)
        self.fade_slider.setValue(1500)
        flay.addWidget(self.fade_slider, 1)
        self.fade_spin = QDoubleSpinBox()
        self.fade_spin.setRange(0.1, 5.0)
        self.fade_spin.setSingleStep(0.1)
        self.fade_spin.setValue(1.5)
        self.fade_spin.setSuffix(" s")
        self.fade_slider.valueChanged.connect(
            lambda v: self.fade_spin.setValue(v / 1000))
        self.fade_spin.valueChanged.connect(
            lambda v: self.fade_slider.setValue(int(v * 1000)))
        flay.addWidget(self.fade_spin)
        rlay.addLayout(flay)

        self.fade_info = QLabel("")
        self.fade_info.setObjectName("hintLabel")
        rlay.addWidget(self.fade_info)
        root.addWidget(right, 2)

    def refresh(self) -> None:
        self.chase_list.clear()
        # Refresh song list juga (konsisten)
        self.song_list.clear()
        for idx, song in enumerate(self.ctx.songs.list()):
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(song.get("filename", f"Song {idx+1}"))
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.song_list.addItem(item)

        for name in list_chases():
            ch = load_chase(name)
            n = len(ch.steps) if ch else 0
            self.chase_list.addItem(f"{name} — {n} steps")

    def _on_song_select(self) -> None:
        """Pilih song → highlight chase terkait (jika ada)."""
        item = self.song_list.currentItem()
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        songs = self.ctx.songs.list()
        if idx is None or idx >= len(songs):
            return
        song = songs[idx]
        fname = song.get("filename", "")
        # highlight chase yang dibuat dari song ini
        for i in range(self.chase_list.count()):
            txt = self.chase_list.item(i).text()
            if fname in txt:
                self.chase_list.setCurrentRow(i)
                break

    def _on_play(self) -> None:
        item = self.chase_list.currentItem()
        if not item:
            return
        name = item.text().split(" — ")[0]
        chase = load_chase(name)
        if chase is None:
            return
        if self.player is not None:
            self.player.play_chase(chase)
            self._fade_info(f"Playing: {chase.name}")
        else:
            self._fade_info(f"Player belum dikonfigurasi — {chase.name}")

    def _on_stop(self) -> None:
        if self.player is not None:
            self.player.stop()
        self._fade_info("Stopped")

    def _on_delete(self) -> None:
        item = self.chase_list.currentItem()
        if not item:
            return
        name = item.text().split(" — ")[0]
        delete_chase(name)
        self.refresh()

    def _fade_info(self, msg: str) -> None:
        self.fade_info.setText(msg)

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
