"""
panels/program_tabs/address_tab.py — Address grid (feedback §8).

Grid 24 kotak per baris, scroll vertikal. Kotak kosong: angka pojok kanan.
Kotak terisi: label channel di tengah + angka tetap pojok. Warna menyesuaikan
type channel (Dimmer=icon lampu, Red=merah, Strobe=strip, dsb).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout,
    QWidget,
)

FIXTURE_MIME = "application/x-zzlx-fixture"

COLS = 24  # maks 24 kotak per baris (feedback §8)

# Label per tipe channel (grandMA3 dark palette, teks singkat bukan emoji)
TYPE_COLORS = {
    "dimmer": ("#8A8A92", "D"),
    "red": ("#C0392B", "R"),
    "green": ("#27AE60", "G"),
    "blue": ("#2980B9", "B"),
    "white": ("#ECF0F1", "W"),
    "strobe": ("#F39C12", "S"),
    "color": ("#9B59B6", "CL"),
    "empty": ("#2A2A30", ""),
    "unknown": ("#3A3A42", "?"),
}


class AddressCell(QWidget):
    """Satu kotak address (mirip grid QLC+ / grandMA3)."""

    clicked = Signal(int)
    drop_requested = Signal(int, str)  # (address, fixture_name)

    def __init__(self, address: int, parent=None) -> None:
        super().__init__(parent)
        self.address = address
        self.setObjectName("addressCell")
        self.setFixedSize(56, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(0)

        self.role = QLabel("")
        self.role.setObjectName("cellRole")
        self.role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.role.setStyleSheet("color:#FFD600; font-size:12px; font-weight:700;")
        lay.addWidget(self.role, 1)

        self.num = QLabel(str(address))
        self.num.setObjectName("cellNum")
        self.num.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.num.setStyleSheet("color:#8A8A92; font-size:9px;")
        lay.addWidget(self.num)

    def set_channel(self, label: str, ch_type: str) -> None:
        color, icon = TYPE_COLORS.get(ch_type, TYPE_COLORS["unknown"])
        self.role.setText(f"{icon} {label}" if icon else label)
        self.role.setStyleSheet(f"color:{color}; font-size:11px; font-weight:700;")
        self.setStyleSheet("QWidget#addressCell { background:#3A3A42; border:1px solid #4A4A52; }")

    def clear_channel(self) -> None:
        self.role.setText("")
        self.setStyleSheet("QWidget#addressCell { background:#1E1E24; border:1px solid #2A2A30; }")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.address)
        super().mousePressEvent(event)

    # Drag-drop target (fixture → patch otomatis)
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(FIXTURE_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        if not event.mimeData().hasFormat(FIXTURE_MIME):
            event.ignore()
            return
        name = bytes(event.mimeData().data(FIXTURE_MIME)).decode("utf-8", "replace")
        self.drop_requested.emit(self.address, name)
        event.acceptProposedAction()


class AddressTab(QWidget):
    """Grid address 1-512, 24 per baris, scroll vertikal."""

    cell_clicked = Signal(int)
    patch_requested = Signal(int, str)  # (address, fixture_name) via drop
    auto_patch_requested = Signal()     # tombol Auto Patch (popup di parent)

    def __init__(self, ctx=None, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._cells: dict[int, AddressCell] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        head = QHBoxLayout()
        title = QLabel("Address Grid")
        title.setObjectName("cardTitle")
        head.addWidget(title)
        head.addStretch(1)
        self.auto_patch_btn = QPushButton("Auto Patch…")
        self.auto_patch_btn.setObjectName("toolButton")
        self.auto_patch_btn.clicked.connect(self.auto_patch_requested.emit)
        head.addWidget(self.auto_patch_btn)
        self.clear_btn = QPushButton("Clear All Patch")
        self.clear_btn.setObjectName("dangerButton")
        head.addWidget(self.clear_btn)
        self.info = QLabel("")
        self.info.setObjectName("value")
        head.addWidget(self.info)
        root.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("mixerScroll")
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(2)
        grid.setContentsMargins(4, 4, 4, 4)

        for i in range(1, 513):
            cell = AddressCell(i)
            cell.clicked.connect(self.cell_clicked.emit)
            cell.drop_requested.connect(self.patch_requested.emit)
            row = (i - 1) // COLS
            col = (i - 1) % COLS
            grid.addWidget(cell, row, col)
            self._cells[i] = cell

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

    # ── API ────────────────────────────────────────────
    def update_map(self, address_map: dict[int, dict],
                   channel_labels: dict[str, dict] | None = None) -> None:
        """address_map: {addr: {fixture_name, start_address}}.
        channel_labels: {fixture_name: {offset: (label, type)}} untuk warna."""
        for addr, cell in self._cells.items():
            cell.clear_channel()
        for addr, info in address_map.items():
            cell = self._cells.get(addr)
            if not cell:
                continue
            fx = info.get("fixture_name", "")
            off = addr - int(info.get("start_address", addr))
            label, ch_type = "ch", "unknown"
            if channel_labels and fx in channel_labels and off in channel_labels[fx]:
                label, ch_type = channel_labels[fx][off]
            cell.set_channel(label, ch_type)

    def clear(self) -> None:
        for cell in self._cells.values():
            cell.clear_channel()

    def set_ctx(self, ctx) -> None:
        self.ctx = ctx
