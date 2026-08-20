"""
widgets/toast.py — Toast notification (non-blocking, auto-hide).

Usage:
    show_toast(parent, "Project saved", kind="ok")
    show_toast(parent, "Connect failed", kind="err")
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget

KIND_COLORS = {
    "ok": "#2ECC71",
    "err": "#E74C3C",
    "warn": "#E0AF68",
    "info": "#FFD600",
}


def show_toast(parent: QWidget, message: str, kind: str = "info",
               duration_ms: int = 2600) -> None:
    """Floating toast bottom-right of parent, auto-hides."""
    if not parent:
        return
    toast = QLabel(message, parent)
    toast.setObjectName("toast")
    color = KIND_COLORS.get(kind, KIND_COLORS["info"])
    toast.setStyleSheet(
        f"background:#1A1A20; border:1px solid {color}; color:{color};"
        "border-radius:4px; padding:10px 18px; font-weight:800;"
    )
    toast.adjustSize()
    toast.move(
        parent.width() - toast.width() - 24,
        parent.height() - toast.height() - 48,
    )
    toast.show()
    toast.raise_()

    QTimer.singleShot(duration_ms, toast.deleteLater)
