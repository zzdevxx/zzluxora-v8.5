"""
widgets/empty_state.py — EmptyState placeholder (icon + title + hint).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyState(QWidget):
    def __init__(self, icon: str = "◌", title: str = "Belum ada data",
                 hint: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.addStretch(1)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 52px; color: #2A2F3C;")
        lay.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 15px;")
        lay.addWidget(title_label)

        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("hintLabel")
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_label.setWordWrap(True)
            lay.addWidget(hint_label)

        lay.addStretch(1)

        self._title_label = title_label
        self._hint_label = hint_label if hint else None

    # ── API ────────────────────────────────────────────
    def set_title(self, title: str) -> None:
        self._title_label.setText(title)

    def set_hint(self, hint: str) -> None:
        if self._hint_label:
            self._hint_label.setText(hint)
        elif hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("hintLabel")
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_label.setWordWrap(True)
            self.layout().insertWidget(self.layout().count() - 1, hint_label)
            self._hint_label = hint_label
