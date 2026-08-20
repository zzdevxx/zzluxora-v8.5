"""
widgets/header_bar.py — HeaderBar (brand, project, artnet pill, play/stop, actions).

Signals:
  play_toggled(bool playing)
  connect_clicked()
  blackout_clicked()
  action_requested(str)   — "new" | "open" | "save"
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QToolButton, QWidget,
)


class HeaderBar(QWidget):
    play_toggled = Signal(bool)
    connect_clicked = Signal()
    blackout_clicked = Signal()
    action_requested = Signal(str)
    sidebar_toggle_requested = Signal()

    def __init__(self, project_name: str = "Untitled.zlx", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("headerBar")
        self.setFixedHeight(52)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 16, 0)
        lay.setSpacing(10)

        # Hamburger (toggle sidebar) — QToolButton + ikon, pola QLC+ toolbar
        self.hamburger = QToolButton()
        self.hamburger.setObjectName("hamburgerBtn")
        self.hamburger.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hamburger.setFixedSize(30, 30)
        self.hamburger.setAutoRaise(True)
        self.hamburger.setToolTip("Toggle sidebar (menu)")
        # Ikon hamburger standar dari style (tidak perlu file gambar)
        self.hamburger.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_TitleBarMenuButton))
        self.hamburger.setIconSize(QSize(18, 18))
        self.hamburger.clicked.connect(self.sidebar_toggle_requested.emit)
        lay.addWidget(self.hamburger)

        # Brand
        brand = QLabel("<b>ZZLUXORA</b>")
        brand.setObjectName("brandLabel")
        brand.setStyleSheet("color:#0A0A0C; font-weight:800; letter-spacing:1px;")
        lay.addWidget(brand)

        # Project label
        self._project_label = QLabel("")
        self._project_label.setObjectName("projectLabel")
        lay.addWidget(self._project_label)
        self.set_project(project_name)

        lay.addStretch(1)

        # Art-Net pill (hijau=connected, merah=disconnected)
        self._pill = QLabel("OFFLINE")
        self._pill.setObjectName("artnetPill")
        self._pill.setProperty("state", "idle")
        self._pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._pill)

        # Connect toggle
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setObjectName("successButton")
        self._connect_btn.setCheckable(True)
        self._connect_btn.clicked.connect(lambda: self.connect_clicked.emit())
        lay.addWidget(self._connect_btn)

        # Blackout
        blackout = QPushButton("Blackout")
        blackout.setObjectName("dangerButton")
        blackout.clicked.connect(self.blackout_clicked.emit)
        lay.addWidget(blackout)

        # Play/Stop
        self._play_btn = QPushButton("PLAY")
        self._play_btn.setObjectName("playButton")
        self._play_btn.setCheckable(True)
        self._play_btn.toggled.connect(self.play_toggled.emit)
        lay.addWidget(self._play_btn)

        self._playing = False
        self._refresh_play_btn()

    # ── API ────────────────────────────────────────────
    def set_project(self, name: str) -> None:
        self._project_label.setText(name or "Untitled.zlx")

    def set_artnet_state(self, connected: bool, text: str = "") -> None:
        if connected:
            self._pill.setProperty("state", "connected")
            self._pill.setText(text or "CONNECTED")
            self._connect_btn.setText("Disconnect")
        else:
            self._pill.setProperty("state", "error" if text else "idle")
            self._pill.setText(text or "OFFLINE")
            self._connect_btn.setText("Connect")
        self._pill.style().unpolish(self._pill)
        self._pill.style().polish(self._pill)

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        self._play_btn.setChecked(playing)
        self._play_btn.setText("STOP" if playing else "PLAY")

    def is_playing(self) -> bool:
        return self._playing

    def _refresh_play_btn(self) -> None:
        self._play_btn.setText("STOP" if self._playing else "PLAY")
