"""
panels/program_tabs/page_tab.py — Page (feedback §12, BARU).

Custom page: grid tombol scene/chase yang bisa diklik → kirim frame ke ArtNet.
Layout & interaksi: sederhana dulu (grid tombol + tambah/hapus), extendable.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QInputDialog, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from widgets.panel_base import Card


class PageButton(QPushButton):
    """Tombol scene/chase di page (warna = warna scene)."""

    def __init__(self, label: str, color: str = "#FFD600", parent=None) -> None:
        super().__init__(label, parent)
        self.setObjectName("pageButton")
        self.setMinimumHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton#pageButton {{ background:{color}; color:#0A0A0C; "
            f"font-weight:800; border-radius:2px; padding:6px; }}")


class PageTab(QWidget):
    """Kustom page tombol scene/chase."""

    trigger = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, PageButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        head = QHBoxLayout()
        title = QLabel("Page — Custom Scene Buttons")
        title.setObjectName("cardTitle")
        head.addWidget(title)
        head.addStretch(1)
        self.add_btn = QPushButton("+ Add Scene Button")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(self._on_add)
        head.addWidget(self.add_btn)
        self.rm_btn = QPushButton("Remove")
        self.rm_btn.clicked.connect(self._on_remove)
        head.addWidget(self.rm_btn)
        root.addLayout(head)

        card = Card()
        lay = card.body()
        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        lay.addLayout(self.grid)
        root.addWidget(card, 1)

        root.addStretch(0)

    def _on_add(self) -> None:
        label, ok = QInputDialog.getText(self, "Tambah Scene", "Nama scene:", text=f"Scene {len(self._buttons)+1}")
        if not ok or not label.strip():
            return
        btn = PageButton(label.strip())
        btn.clicked.connect(lambda _c=False, l=label.strip(): self.trigger.emit(l))
        self._buttons[label.strip()] = btn
        row = (len(self._buttons) - 1) // 4
        col = (len(self._buttons) - 1) % 4
        self.grid.addWidget(btn, row, col)

    def _on_remove(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        if not self._buttons:
            return
        names = list(self._buttons.keys())
        from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("Hapus tombol")
        form = QFormLayout(dlg)
        combo = QComboBox()
        combo.addItems(names)
        form.addRow("Tombol:", combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = combo.currentText()
        if name in self._buttons:
            self._buttons.pop(name).deleteLater()
            self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for i, (name, btn) in enumerate(self._buttons.items()):
            self.grid.addWidget(btn, i // 4, i % 4)
