"""
panels/program_tabs/preview_tab.py — Preview (feedback §14).

Visual fixture: lingkaran (front view), bisa di-select & drag. Sidebar kanan:
panel posisi X/Y. Elemen disusun dengan posisi relatif (0-100) supaya responsif.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from panels.program_tabs.mixer_tab import DMX_SIZE


class PreviewCanvas(QWidget):
    """Kanvas fixture (lingkaran). Item punya posisi relatif (0-1)."""

    item_moved = Signal(int, float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("previewCanvas")
        self.setMinimumSize(400, 260)
        self._items: dict[int, dict] = {}  # id -> {x, y, label, color}
        self._selected: int | None = None
        self._drag_id: int | None = None

    def set_items(self, items: dict[int, dict]) -> None:
        self._items = items
        self.update()

    def add_item(self, item_id: int, label: str, x: float = 0.5,
                 y: float = 0.5, color: str = "#FFD600") -> None:
        self._items[item_id] = {"x": x, "y": y, "label": label, "color": color}
        self.update()

    def remove_item(self, item_id: int) -> None:
        self._items.pop(item_id, None)
        self.update()

    def item_count(self) -> int:
        return len(self._items)

    def _pos_to_xy(self, pos: QPointF) -> tuple[float, float]:
        w, h = max(self.width(), 1), max(self.height(), 1)
        return pos.x() / w, pos.y() / h

    def _hit(self, pos: QPointF) -> int | None:
        w, h = max(self.width(), 1), max(self.height(), 1)
        for item_id, it in self._items.items():
            cx, cy = it["x"] * w, it["y"] * h
            r = 34
            if (pos.x() - cx) ** 2 + (pos.y() - cy) ** 2 <= r * r:
                return item_id
        return None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        hit = self._hit(event.position())
        if hit is not None:
            self._selected = hit
            self._drag_id = hit
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_id is not None:
            x, y = self._pos_to_xy(event.position())
            x = max(0.05, min(0.95, x))
            y = max(0.05, min(0.95, y))
            self._items[self._drag_id]["x"] = x
            self._items[self._drag_id]["y"] = y
            self.item_moved.emit(self._drag_id, x, y)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_id = None
        super().mouseReleaseEvent(event)

    def selected_id(self) -> int | None:
        return self._selected

    def select_id(self, item_id: int | None) -> None:
        self._selected = item_id
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Grid halus
        pen = QPen(QColor("#1E1E24"), 1)
        p.setPen(pen)
        for gx in range(0, w, 32):
            p.drawLine(gx, 0, gx, h)
        for gy in range(0, h, 32):
            p.drawLine(0, gy, w, gy)

        for item_id, it in self._items.items():
            cx, cy = it["x"] * w, it["y"] * h
            color = QColor(it["color"])
            selected = (item_id == self._selected)
            # Lingkaran luar
            p.setBrush(color.darker(160) if not selected else color)
            p.setPen(QPen(QColor("#FFD600") if selected else QColor("#4A4A52"), 2))
            p.drawEllipse(QPointF(cx, cy), 34, 34)
            # Titik tengah
            p.setBrush(QColor("#FFD600" if selected else "#FFFFFF"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx, cy), 5, 5)
            # Label
            p.setPen(QPen(QColor("#FFFFFF"), 1))
            p.drawText(int(cx - 30), int(cy - 44), 60, 16,
                       Qt.AlignmentFlag.AlignCenter, it.get("label", ""))


class PreviewTab(QWidget):
    """Preview + panel X/Y (feedback §14)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Kiri: kanvas
        left = QVBoxLayout()
        title = QLabel("Preview — tampak depan")
        title.setObjectName("cardTitle")
        left.addWidget(title)

        self.canvas = PreviewCanvas()
        self.canvas.item_moved.connect(self._on_item_moved)
        left.addWidget(self.canvas, 1)

        add_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Fixture")
        self.add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.add_btn)
        self.rm_btn = QPushButton("Remove Selected")
        self.rm_btn.clicked.connect(self._on_remove)
        add_row.addWidget(self.rm_btn)
        add_row.addStretch(1)
        left.addLayout(add_row)
        root.addLayout(left, 1)

        # Kanan: panel posisi
        side = QVBoxLayout()
        side_lbl = QLabel("Position")
        side_lbl.setObjectName("cardTitle")
        side.addWidget(side_lbl)

        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0.0, 1.0)
        self.x_spin.setSingleStep(0.01)
        self.x_spin.setDecimals(2)
        self.x_spin.valueChanged.connect(lambda v: self._on_spin(0, v))
        side.addWidget(QLabel("X"))
        side.addWidget(self.x_spin)

        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0.0, 1.0)
        self.y_spin.setSingleStep(0.01)
        self.y_spin.setDecimals(2)
        self.y_spin.valueChanged.connect(lambda v: self._on_spin(1, v))
        side.addWidget(QLabel("Y"))
        side.addWidget(self.y_spin)

        side.addStretch(1)
        root.addLayout(side)

        # Seed: 4 lampu contoh
        for i in range(4):
            self.canvas.add_item(i, f"PAR {i+1}", x=0.2 + i * 0.2, y=0.45)

    # ── Handlers ───────────────────────────────────────
    def _on_item_moved(self, item_id: int, x: float, y: float) -> None:
        if self.canvas.selected_id() == item_id:
            self.x_spin.blockSignals(True)
            self.y_spin.blockSignals(True)
            self.x_spin.setValue(round(x, 2))
            self.y_spin.setValue(round(y, 2))
            self.x_spin.blockSignals(False)
            self.y_spin.blockSignals(False)
        self._push()

    def _on_spin(self, axis: int, v: float) -> None:
        sid = self.canvas.selected_id()
        if sid is None:
            return
        it = self.canvas._items[sid]
        if axis == 0:
            it["x"] = v
        else:
            it["y"] = v
        self.canvas.update()
        self._push()

    def _on_add(self) -> None:
        n = self.canvas.item_count() + 1
        self.canvas.add_item(n, f"PAR {n}")
        self.canvas.select_id(n)

    def _on_remove(self) -> None:
        sid = self.canvas.selected_id()
        if sid is not None:
            self.canvas.remove_item(sid)

    def _push(self) -> None:
        """Kirim frame preview ke ArtNet (placeholder — di-M6 wire)."""
        pass
