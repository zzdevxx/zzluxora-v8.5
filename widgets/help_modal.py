"""
widgets/help_modal.py — HelpDialog (F1): daftar shortcut lengkap.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

SHORTCUTS: list[tuple[str, str]] = [
    ("Space", "Play / Stop (audio-reactive)"),
    ("B", "Blackout semua channel"),
    ("E", "Emergency Stop (blackout + stop chase)"),
    ("F1", "Help / shortcuts ini"),
    ("Ctrl+1..8", "Pindah panel (Dashboard→Settings)"),
    ("Ctrl+S", "Save project"),
    ("Ctrl+Shift+S", "Save project as…"),
    ("Ctrl+O", "Open project…"),
]


class HelpDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Shortcut")
        self.setMinimumWidth(460)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # Header: 'Shortcut' saja
        title = QLabel("Shortcut")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 18px; font-weight:800;")
        lay.addWidget(title)

        # Close atas (rata kanan)
        top_row = QHBoxLayout()
        top_row.addStretch(1)
        close_top = QPushButton("Close")
        close_top.setObjectName("primaryButton")
        close_top.clicked.connect(self.accept)
        top_row.addWidget(close_top)
        lay.addLayout(top_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(8)
        for row, (key, desc) in enumerate(SHORTCUTS):
            k = QLabel(key)
            k.setStyleSheet(
                "background:#12141B; border:1px solid #24283A; border-radius:6px;"
                "padding:4px 10px; font-weight:800; color:#7AA2F7;"
            )
            d = QLabel(desc)
            d.setStyleSheet("color:#C0CAF5;")
            grid.addWidget(k, row, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(d, row, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addLayout(grid)

        lay.addSpacing(8)
        # Close bawah (rata tengah)
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        close_bottom = QPushButton("Close")
        close_bottom.setObjectName("primaryButton")
        close_bottom.clicked.connect(self.accept)
        bottom_row.addWidget(close_bottom)
        bottom_row.addStretch(1)
        lay.addLayout(bottom_row)
