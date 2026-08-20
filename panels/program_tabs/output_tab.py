"""
panels/program_tabs/output_tab.py — Output Art-Net (feedback §15).

Scan IP seperti QLC+: localhost 127.0.0.1, 192.168.4.1 (ESP32 AP), custom.
TANPA setting universe/FPS. Tombol hanya Save — connect/disconnect/blackout
sudah ada di header kanan atas.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from app import AppContext


def _ip_valid(ip: str) -> bool:
    parts = ip.split(".")
    return len(parts) == 4 and all(
        p.isdigit() and 0 <= int(p) <= 255 for p in parts)


PRESET_IPS = ["127.0.0.1", "192.168.4.1", "Custom…"]


class OutputTab(QWidget):
    def __init__(self, ctx: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        title = QLabel("Output Art-Net")
        title.setObjectName("cardTitle")
        root.addWidget(title)

        # IP selector
        row = QHBoxLayout()
        row.addWidget(QLabel("Target IP:"))
        self.ip_combo = QComboBox()
        self.ip_combo.addItems(PRESET_IPS)
        self.ip_combo.setEditable(False)
        self.ip_combo.currentIndexChanged.connect(self._on_ip_change)
        row.addWidget(self.ip_combo)

        self.custom_ip = QLineEdit()
        self.custom_ip.setPlaceholderText("192.168.1.100")
        self.custom_ip.setVisible(False)
        row.addWidget(self.custom_ip)
        root.addLayout(row)

        # Info
        self.info = QLabel("Connect/Disconnect/Blackout tersedia di header (kanan atas).")
        self.info.setObjectName("hintLabel")
        self.info.setWordWrap(True)
        root.addWidget(self.info)

        root.addStretch(1)

        # Save only
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("successButton")
        self.save_btn.clicked.connect(self._on_save)
        root.addWidget(self.save_btn)

    def _on_ip_change(self) -> None:
        self.custom_ip.setVisible(self.ip_combo.currentText() == "Custom…")

    def _selected_ip(self) -> str:
        if self.ip_combo.currentText() == "Custom…":
            ip = self.custom_ip.text().strip()
            return ip or "127.0.0.1"
        return self.ip_combo.currentText()

    def _on_save(self) -> None:
        ip = self._selected_ip()
        if not _ip_valid(ip):
            QMessageBox.warning(self, "IP tidak valid", f"'{ip}' bukan alamat IPv4 valid")
            return
        self.ctx.cfg.artnet_default_ip = ip
        self.ctx.cfg.save()
        QMessageBox.information(self, "Tersimpan",
                                f"Target Art-Net disimpan: {ip}\nGunakan tombol Connect di header untuk menghubungkan.")

    def current_ip(self) -> str:
        return self._selected_ip()

    def set_ip(self, ip: str) -> None:
        if ip in PRESET_IPS:
            self.ip_combo.setCurrentText(ip)
        else:
            self.ip_combo.setCurrentText("Custom…")
            self.custom_ip.setText(ip)
