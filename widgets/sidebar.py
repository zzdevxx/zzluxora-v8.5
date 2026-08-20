"""
widgets/sidebar.py — Sidebar navigation v8.2 (feedback §7).

Konsep feedback:
- Hamburger ☰ ada di HeaderBar (selalu tampil, kiri atas) — BUKAN di sidebar
- Sidebar hanya berisi brand + 5 item nav
- Saat locked (belum load project): sidebar di-collapse (item disabled +
  brand samar) tapi hamburger/brand bisa dilihat saat toggle
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget,
)

SIDEBAR_ITEMS: list[tuple[str, str, str]] = [
    ("program", "01", "Program"),
    ("fixtures", "02", "Fixture List"),
    ("fixture_editor", "03", "Fixture Editor"),
    ("settings", "04", "Settings"),
    ("about", "05", "About"),
]

PANEL_TITLE: dict[str, tuple[str, str]] = {
    "program": ("Program", "Address · Analyze · Scenes · Chase · Page · Mixer · Preview · Output"),
    "fixtures": ("Fixture List", "Daftar fixture dari folder fixtures"),
    "fixture_editor": ("Fixture Editor", "Edit atau buat definisi fixture"),
    "settings": ("Settings", "Preferensi aplikasi"),
    "about": ("About", "Informasi aplikasi dan pengembang"),
}


class Sidebar(QWidget):
    """Dock area berisi brand + 5 item nav (hamburger ada di HeaderBar)."""

    panel_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(210)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(2)

        # Brand
        self.brand = QLabel("ZZLUXORA")
        self.brand.setObjectName("sidebarTitle")
        self.brand.setContentsMargins(22, 12, 10, 6)
        lay.addWidget(self.brand)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        for key, num, label in SIDEBAR_ITEMS:
            btn = QPushButton(f"{num}   {label}")
            btn.setObjectName("sidebarItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setEnabled(False)  # locked sampai project di-load
            btn.clicked.connect(lambda _c=False, k=key: self.panel_selected.emit(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            lay.addWidget(btn)

        lay.addStretch(1)

        ver = QLabel("zzluxora v8.1.0")
        ver.setObjectName("sidebarTitle")
        ver.setStyleSheet("color:#8A8A92; font-weight:600; font-size:11px; padding:8px 22px;")
        lay.addWidget(ver)

        self._unlocked = False
        self._update_lock_ui()

    # ── Lock state ─────────────────────────────────────
    def set_locked(self, locked: bool) -> None:
        """locked=True → item tak bisa dipakai (belum load project)."""
        self._unlocked = not locked
        self._update_lock_ui()

    def is_locked(self) -> bool:
        return not self._unlocked

    def _update_lock_ui(self) -> None:
        for btn in self._buttons.values():
            btn.setEnabled(self._unlocked)
        # Brand samar saat locked (masih tampil, transparan)
        self.brand.setStyleSheet(
            "color:#3A3A40; padding:12px 22px 6px;" if not self._unlocked else
            "color:#FFD600; font-weight:800; letter-spacing:1px; padding:12px 22px 6px;")

    # ── API ────────────────────────────────────────────
    def select(self, key: str) -> None:
        if key in self._buttons and self._unlocked:
            self._buttons[key].setChecked(True)

    def current(self) -> str:
        for key, btn in self._buttons.items():
            if btn.isChecked():
                return key
        return "program"
