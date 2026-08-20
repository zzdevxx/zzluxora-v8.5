"""
panels/chase_panel.py — Chase: daftar chase tersimpan + preview + play.

Chase engine (engines/chase.py) menyediakan list/save/load/delete.
Panel ini: list, pilih → preview steps, play via artnet play_chase.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QVBoxLayout,
)

from engines.chase import (
    delete_chase, list_chases, load_chase,
)
from widgets.empty_state import EmptyState
from widgets.panel_base import BasePanel, Card


class ChasePanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Chases", "Sequence & chase editor")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("playButton")
        self.play_btn.clicked.connect(self._on_play)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self._on_stop)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("dangerButton")
        self.del_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.play_btn)
        toolbar.addWidget(self.stop_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.del_btn)
        self.add_layout(toolbar)

        mode = QHBoxLayout()

        # Chase list
        list_card = Card()
        list_lay = list_card.body()
        list_lay.addWidget(self._label("Chase Tersimpan", "cardTitle"))
        self.chase_list = QListWidget()
        self.chase_list.itemSelectionChanged.connect(self._on_select)
        list_lay.addWidget(self.chase_list)
        mode.addWidget(list_card)

        # Step preview
        step_card = Card()
        step_lay = step_card.body()
        step_lay.addWidget(self._label("Step Preview", "cardTitle"))
        self.step_list = QListWidget()
        step_lay.addWidget(self.step_list)
        mode.addWidget(step_card)
        self.add_layout(mode)

        self.empty = EmptyState("04", "Belum ada chase",
                                "Generate dari Analyze (auto-chase) atau import")
        self.add_widget(self.empty)
        self.add_stretch()

    # ── Handlers ───────────────────────────────────────
    def _on_select(self) -> None:
        item = self.chase_list.currentItem()
        if not item:
            return
        name = item.text().split("  ·")[0]
        chase = load_chase(name)
        self.step_list.clear()
        if not chase:
            return
        for s in chase.steps:
            c = s.drgbw
            self.step_list.addItem(
                f"{s.label or 'Step'}  {s.start:.1f}-{s.end():.1f}s  "
                f"D{c.get('d', 0)} RGB({c.get('r', 0)},{c.get('g', 0)},{c.get('b', 0)})")

    def _on_play(self) -> None:
        item = self.chase_list.currentItem()
        if not item:
            return
        name = item.text().split("  ·")[0]
        chase = load_chase(name)
        if not chase:
            return
        # Konversi steps → frames
        frames = []
        for s in chase.steps:
            c = s.drgbw
            dmx = [0] * 512
            dmx[0] = int(c.get("d", c.get("dimmer", 0)))
            dmx[1] = int(c.get("r", 0))
            dmx[2] = int(c.get("g", 0))
            dmx[3] = int(c.get("b", 0))
            dmx[4] = int(c.get("w", 0))
            frames.append({"dmx": dmx, "hold_ms": int(s.duration * 1000), "fade_ms": 400})
        self.ctx.artnet.chase_frames = frames
        if self.ctx.artnet.is_running:
            self.ctx.artnet.play_chase(frames)
            self.play_btn.setText("Playing…")
        else:
            from widgets.toast import show_toast
            show_toast(self, "Connect Art-Net dulu (Output panel)", kind="warn")

    def _on_stop(self) -> None:
        self.ctx.artnet.stop_chase()
        self.play_btn.setText("Play")

    def _on_delete(self) -> None:
        item = self.chase_list.currentItem()
        if not item:
            return
        name = item.text().split("  ·")[0]
        ret = QMessageBox.question(self, "Hapus chase", f"Hapus '{name}'?")
        if ret == QMessageBox.StandardButton.Yes:
            delete_chase(name)
            self.refresh()

    # ── Refresh ────────────────────────────────────────
    def refresh(self) -> None:
        self.chase_list.clear()
        for name in list_chases():
            chase = load_chase(name)
            n = len(chase.steps) if chase else 0
            self.chase_list.addItem(f"{name}  ·  {n} steps")
        self.step_list.clear()
        self.empty.setVisible(not list_chases())

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l

