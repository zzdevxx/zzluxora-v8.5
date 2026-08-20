"""
panels/placeholder_panel.py — Placeholder untuk panel yang belum diimplementasi.

M5 akan menggantikan dengan panel lengkap (Program, Chase, Analyze).
"""
from __future__ import annotations

from widgets.empty_state import EmptyState
from widgets.panel_base import BasePanel


class PlaceholderPanel(BasePanel):
    def __init__(self, ctx, title: str, sub: str = "", icon: str = "•") -> None:
        super().__init__(ctx, title, sub)
        self.add_widget(EmptyState(
            icon,
            f"{title} — segera hadir",
            "Panel ini akan diimplementasikan pada milestone berikutnya.",
        ))
        self.add_stretch()
