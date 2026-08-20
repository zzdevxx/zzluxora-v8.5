"""
widgets/splash.py — Splash screen (feedback §2): icon lampu putih bg hitam +
tulisan besar ZZLUXORA, durasi 3 detik. Style grandMA3 dark.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSplashScreen, QVBoxLayout, QWidget


def render_logo(size: int = 96, color: str = "#FFFFFF") -> QPixmap:
    """Lampu PAR sederhana (bulatan + reflektor) — warna putih di bg hitam."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Reflektor (trapesium)
    p.setPen(QPen(QColor(color), 3))
    p.drawLine(int(size * 0.30), int(size * 0.70), int(size * 0.70), int(size * 0.70))
    p.drawLine(int(size * 0.30), int(size * 0.70), int(size * 0.42), int(size * 0.42))
    p.drawLine(int(size * 0.70), int(size * 0.70), int(size * 0.58), int(size * 0.42))
    # Lensa (lingkaran)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(int(size * 0.32), int(size * 0.20), int(size * 0.36), int(size * 0.36))
    # Aksen kuning grandMA3
    p.setBrush(QColor("#FFD600"))
    p.drawEllipse(int(size * 0.42), int(size * 0.30), int(size * 0.16), int(size * 0.16))
    p.end()
    return pm


class SplashScreen(QSplashScreen):
    def __init__(self) -> None:
        bg = QPixmap(560, 360)
        bg.fill(QColor("#0A0A0C"))
        super().__init__(bg)

        wrap = QWidget(self)
        lay = QVBoxLayout(wrap)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(render_logo(96))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)

        title = QLabel("ZZLUXORA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#FFD600; font-size:42px; font-weight:800; letter-spacing:4px;")
        lay.addWidget(title)

        sub = QLabel("Audio-Reactive Lighting Design")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#A7A7AA; font-size:13px; letter-spacing:1px;")
        lay.addWidget(sub)

        wrap.setGeometry(0, 0, 560, 360)
        self.show()
