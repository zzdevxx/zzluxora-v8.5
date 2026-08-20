"""
panels/output_panel.py — Output: kontrol Art-Net DMX + live preview.

Fitur M4:
  - Target IP / Universe / FPS fields
  - Connect / Disconnect / Blackout
  - Status frames counter
  - Preview swatch (warna terakhir terkirim)
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
)

from widgets.panel_base import BasePanel, Card


class OutputPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Output", "Art-Net DMX output & live preview")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # ── Connection card ──────────────────────────
        card = Card()
        lay = card.body()
        lay.addWidget(self._label("Art-Net Connection", "cardTitle"))

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(self._label("Target IP", "cardSub"), 0, 0)
        self.ip_edit = QLineEdit(self.ctx.artnet.target_ip)
        self.ip_edit.setPlaceholderText("192.168.1.50")
        grid.addWidget(self.ip_edit, 0, 1)

        grid.addWidget(self._label("Universe", "cardSub"), 1, 0)
        self.universe_spin = QSpinBox()
        self.universe_spin.setRange(0, 15)
        self.universe_spin.setValue(self.ctx.artnet.universe)
        grid.addWidget(self.universe_spin, 1, 1)

        grid.addWidget(self._label("FPS", "cardSub"), 2, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(self.ctx.artnet.fps)
        grid.addWidget(self.fps_spin, 2, 1)
        lay.addLayout(grid)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("successButton")
        self.connect_btn.clicked.connect(self._on_connect)
        self.blackout_btn = QPushButton("Blackout")
        self.blackout_btn.setObjectName("dangerButton")
        self.blackout_btn.clicked.connect(self._on_blackout)
        row.addWidget(self.connect_btn)
        row.addWidget(self.blackout_btn)
        row.addStretch(1)
        lay.addLayout(row)

        self.status_lbl = QLabel("● Tidak terhubung")
        self.status_lbl.setObjectName("artnetPill")
        lay.addWidget(self.status_lbl)
        self.add_widget(card)

        # ── Preview card ─────────────────────────────
        preview = Card()
        play = preview.body()
        play.addWidget(self._label("Last Frame Preview", "cardTitle"))
        self.preview_lbl = QLabel("—")
        self.preview_lbl.setObjectName("value")
        play.addWidget(self.preview_lbl)
        self.frames_lbl = QLabel("Frames sent: 0")
        self.frames_lbl.setObjectName("hintLabel")
        play.addWidget(self.frames_lbl)
        self.add_widget(preview)

        self.add_stretch()

    # ── Handlers ─────────────────────────────────────
    def _on_connect(self) -> None:
        art = self.ctx.artnet
        if art.is_running:
            art.disconnect()
        else:
            ip = self.ip_edit.text().strip() or "127.0.0.1"
            uni = self.universe_spin.value()
            fps = self.fps_spin.value()
            result = art.connect(ip, uni, fps)
            if result.get("ok"):
                self.ctx.cfg.set("ArtNet", "default_ip", ip)
                self.ctx.cfg.set("ArtNet", "default_universe", str(uni))
                self.ctx.cfg.set("ArtNet", "default_fps", str(fps))
            else:
                self.status_lbl.setText(f"● Connect gagal: {result.get('error', '?')}")
                self.status_lbl.setProperty("state", "error")
                self._restyle(self.status_lbl)
                return
        self.refresh()

    def _on_blackout(self) -> None:
        self.ctx.artnet.blackout()
        self.refresh()

    def refresh(self) -> None:
        art = self.ctx.artnet
        if art.is_running:
            self.connect_btn.setText("Disconnect")
            self.status_lbl.setText(f"● {art.target_ip} · U{art.universe} · {art.fps}fps")
            self.status_lbl.setProperty("state", "connected")
        else:
            self.connect_btn.setText("Connect")
            self.status_lbl.setText("● Tidak terhubung")
            self.status_lbl.setProperty("state", "idle")
        self._restyle(self.status_lbl)

        status = art.get_status()
        self.frames_lbl.setText(f"Frames sent: {status['frames_sent']} · "
                                f"chase: {status['chase_total']} frames")

        current = art.current_dmx
        if any(current):
            r, g, b = current[1], current[2], current[3]
            self.preview_lbl.setText(f"RGB({r},{g},{b})")
            self.preview_lbl.setStyleSheet(
                f"color:#7AA2F7; font-size:15px; font-weight:900;"
            )
        else:
            self.preview_lbl.setText("— blackout —")
            self.preview_lbl.setStyleSheet("color:#7982A8;")

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l

    @staticmethod
    def _restyle(w: QLabel) -> None:
        w.style().unpolish(w)
        w.style().polish(w)
