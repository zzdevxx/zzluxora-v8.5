"""
panels/settings_panel.py — Settings: preferensi aplikasi.

M4: VA preset aktif + artnet defaults (baca/tulis config.ini).
"""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox

from widgets.toast import show_toast
from widgets.panel_base import BasePanel, Card


class SettingsPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Settings", "Preferensi aplikasi")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        card = Card()
        lay = card.body()
        lay.addWidget(self._label("Umum", "cardTitle"))

        row = QHBoxLayout()
        row.addWidget(self._label("V-A Preset aktif", "cardSub"))
        self.preset_combo = QComboBox()
        self.preset_combo.setEditable(True)
        row.addWidget(self.preset_combo, 1)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(self._label("Default IP", "cardSub"))
        self.ip_edit = QLineEdit()
        row2.addWidget(self.ip_edit, 1)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(self._label("Default Universe", "cardSub"))
        self.universe_spin = QSpinBox()
        self.universe_spin.setRange(0, 15)
        row3.addWidget(self.universe_spin, 1)
        lay.addLayout(row3)

        save_btn = QPushButton("Simpan")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        lay.addWidget(save_btn)
        self.add_widget(card)
        self.add_stretch()

    def _on_save(self) -> None:
        cfg = self.ctx.cfg
        cfg.active_va_preset = self.preset_combo.currentText()
        cfg.set("ArtNet", "default_ip", self.ip_edit.text().strip() or "127.0.0.1")
        cfg.set("ArtNet", "default_universe", str(self.universe_spin.value()))
        show_toast(self, "Settings disimpan", kind="ok")

    def refresh(self) -> None:
        cfg = self.ctx.cfg
        self.preset_combo.clear()
        self.preset_combo.addItem(cfg.active_va_preset)
        self.preset_combo.addItem("Default Praise")
        self.preset_combo.addItem("Worship Calm")
        self.preset_combo.addItem("Intens Worship")
        self.ip_edit.setText(cfg.artnet_default_ip)
        self.universe_spin.setValue(cfg.artnet_default_universe)

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
