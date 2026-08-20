"""
panels/about_panel.py — About (feedback §19): info 9 item urutan detail.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout

from widgets.panel_base import BasePanel, Card

ABOUT_INFO: list[tuple[str, str]] = [
    ("Application", "ZZLUXORA v8.5.0"),
    ("Deskripsi", "Audio-Reactive Lighting Design untuk lagu rohani "
                  "(Praise & Worship) berbasis analisis mood dengan pemetaan "
                  "warna HSV-RGBW dan protokol Art-Net DMX512"),
    ("Author", "Andreas Restuawanta Christwara"),
    ("NIM", "5312422036"),
    ("Prodi", "Teknik Komputer"),
    ("Jurusan", "Teknik Elektro"),
    ("Fakultas", "Fakultas Teknik"),
    ("Universitas", "Universitas Negeri Semarang"),
    ("Judul Skripsi", "Rancang Bangun Sistem Audio-Reactive Lighting Design "
                      "Berbasis Analisis Mood Lagu Rohani dengan Pemetaan "
                      "Warna HSV-RGBW dan Protokol Art-Net DMX512"),
]


class AboutPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "About", "Informasi aplikasi dan pengembang")
        self._build_ui()

    def _build_ui(self) -> None:
        card = Card()
        lay = card.body()
        for label, value in ABOUT_INFO:
            row = QVBoxLayout()
            row.setSpacing(0)
            lbl = QLabel(label.upper())
            lbl.setObjectName("hintLabel")
            val = QLabel(value)
            val.setObjectName("value")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val)
            lay.addLayout(row)
        self.add_widget(card)
        self.add_stretch()
