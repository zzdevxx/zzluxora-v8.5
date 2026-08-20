"""
panels/dashboard_panel.py — Dashboard: ringkasan status sistem.

Menampilkan: jumlah fixtures, jumlah songs, status Art-Net, project aktif,
preset aktif, dan shortcut hints.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from widgets.panel_base import BasePanel, Card


class StatCard(Card):
    """Card dengan nilai besar + label."""

    def __init__(self, label: str, value: str = "0", icon: str = "•") -> None:
        super().__init__()
        lay = self.body()

        row = QHBoxLayout()
        row.setSpacing(8)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        title = QLabel(label)
        title.setObjectName("cardTitle")
        row.addWidget(icon_lbl)
        row.addWidget(title)
        row.addStretch(1)
        lay.addLayout(row)

        self._value = QLabel(value)
        self._value.setObjectName("valueBig")
        lay.addWidget(self._value)

    def set_value(self, v: str) -> None:
        self._value.setText(v)


class DashboardPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Dashboard", "Ringkasan proyek & status sistem")

        # ── Stat cards ────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_fixtures = StatCard("Fixtures", "0", "01")
        self.card_songs = StatCard("Songs", "0", "02")
        self.card_artnet = StatCard("Art-Net", "OFF", "03")
        self.card_preset = StatCard("V-A Preset", "—", "04")

        grid.addWidget(self.card_fixtures, 0, 0)
        grid.addWidget(self.card_songs, 0, 1)
        grid.addWidget(self.card_artnet, 1, 0)
        grid.addWidget(self.card_preset, 1, 1)
        self.add_layout(grid)

        # ── Project card ─────────────────────────────
        self.project_card = Card()
        lay = self.project_card.body()
        lay.addWidget(self._label("Project", "cardTitle"))
        self.project_lbl = QLabel("Belum ada project")
        self.project_lbl.setObjectName("value")
        lay.addWidget(self.project_lbl)
        self.add_widget(self.project_card)

        # ── Shortcut hints ───────────────────────────
        hints = Card()
        hlay = hints.body()
        hlay.addWidget(self._label("Shortcuts", "cardTitle"))
        for text in (
            "Space  →  Play / Stop",
            "B      →  Blackout",
            "E      →  Emergency Stop",
            "Ctrl+1..8  →  Ganti panel",
            "F1     →  Daftar shortcut lengkap",
        ):
            h = QLabel(text)
            h.setObjectName("hintLabel")
            h.setStyleSheet("font-size: 12px; font-style: normal;")
            hlay.addWidget(h)
        self.add_widget(hints)

        self.add_stretch()
        self.refresh()

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l

    def refresh(self) -> None:
        fx = self.ctx.fixtures
        songs = self.ctx.songs
        artnet = self.ctx.artnet

        self.card_fixtures.set_value(str(len(fx.list_fixtures())))
        self.card_songs.set_value(str(len(songs)))
        self.card_artnet.set_value("ON" if artnet.is_running else "OFF")
        preset = self.ctx.cfg.active_va_preset
        self.card_preset.set_value(preset or "—")

        self.project_lbl.setText(self.ctx.project_name or "Belum ada project")

