"""
widgets/panel_base.py — BasePanel + SectionHeader helper untuk semua panels.

Panel v8 pattern:
    class XPanel(BasePanel):
        def __init__(self, ctx):
            super().__init__(ctx, "Judul", "sub judul")
            self._build_ui()
            self.refresh()
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)


class SectionHeader(QWidget):
    """Title + subtitle row untuk tiap panel."""

    def __init__(self, title: str, sub: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(2)

        t = QLabel(title)
        t.setObjectName("sectionTitle")
        lay.addWidget(t)

        if sub:
            s = QLabel(sub)
            s.setObjectName("sectionSub")
            s.setWordWrap(True)
            lay.addWidget(s)


class Card(QFrame):
    """Elevated card container (objectName 'card')."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")

    def body(self) -> QVBoxLayout:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        return lay


class BasePanel(QScrollArea):
    """Scrollable panel with header — semua panels inherit ini."""

    def __init__(self, ctx, title: str, sub: str = "") -> None:
        super().__init__()
        self.ctx = ctx
        self.setObjectName("panel")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._container.setObjectName("panel")
        self._root = QVBoxLayout(self._container)
        self._root.setContentsMargins(28, 24, 28, 24)
        self._root.setSpacing(14)

        self._root.addWidget(SectionHeader(title, sub))
        self.setWidget(self._container)

    # ── API ────────────────────────────────────────────
    def add_widget(self, w: QWidget) -> None:
        self._root.addWidget(w)

    def add_layout(self, lay) -> None:
        self._root.addLayout(lay)

    def add_stretch(self) -> None:
        self._root.addStretch(1)

    def refresh(self) -> None:
        """Override di subclass — dipanggil tiap panel ditampilkan."""
