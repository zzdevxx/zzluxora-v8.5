"""
panels/fixture_editor.py — FixtureEditorForm (grandMA3 style).

Form CRUD fixture: name / manufacturer / channels / type template +
3-col channel table (Ch | Label | Role). Save ke FixtureManager.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.fixture_types import (
    FIXTURE_TYPES, BUILTIN_CHANNEL_LABELS, CHANNEL_ROLES, infer_role,
)


class FixtureEditorForm(QWidget):
    """Single fixture edit form. Emits `saved` + `cancel`."""

    saved = Signal(str)      # fixture name
    cancelled = Signal()

    def __init__(self, manager, fixture_name: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.fixture_name = fixture_name
        self.setObjectName("panel")
        self._build_ui()
        if fixture_name:
            self._load_existing(fixture_name)
        else:
            self._sync_table()

    # ── UI ─────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Generic PAR RGBW 4ch")
        self.mfr_edit = QLineEdit("Generic")
        self.ch_spin = QSpinBox()
        self.ch_spin.setRange(1, 64)
        self.ch_spin.setValue(4)
        self.ch_spin.valueChanged.connect(self._sync_table)

        self.type_combo = QComboBox()
        self.type_combo.addItems(list(FIXTURE_TYPES.keys()))
        self.type_combo.setCurrentText("Custom")
        self.type_combo.currentTextChanged.connect(self._on_type_change)

        form.addRow("Name *:", self.name_edit)
        form.addRow("Manufacturer:", self.mfr_edit)
        form.addRow("Channels:", self.ch_spin)
        form.addRow("Type:", self.type_combo)
        root.addLayout(form)

        lbl = QLabel("Channel Map")
        lbl.setObjectName("sectionTitle")
        root.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setObjectName("channelTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Ch", "Label", "Role"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.itemChanged.connect(self._on_cell_changed)
        root.addWidget(self.table, 1)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.save_btn = QPushButton("Save Fixture")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancelled.emit)
        row.addWidget(cancel_btn)
        row.addStretch(1)
        row.addWidget(self.save_btn)
        root.addLayout(row)

    # ── Table sync ─────────────────────────────────────
    def _sync_table(self) -> None:
        """Rebuild table rows to match channel count; keep existing labels."""
        self.table.blockSignals(True)
        old_labels: dict[int, str] = {}
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.text():
                old_labels[r] = item.text()

        n = self.ch_spin.value()
        self.table.setRowCount(n)
        for r in range(n):
            ch_item = QTableWidgetItem(str(r + 1))
            ch_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(r, 0, ch_item)

            label = old_labels.get(r, "Dimmer" if r == 0 else "")
            label_item = QTableWidgetItem(label)
            self.table.setItem(r, 1, label_item)

            role_item = QTableWidgetItem(infer_role(label))
            role_item.setFlags(Qt.ItemFlag.ItemIsEnabled
                               | Qt.ItemFlag.ItemIsSelectable)
            role_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(r, 2, role_item)
        self.table.blockSignals(False)

    def _on_cell_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 1:  # label → update role
            self.table.blockSignals(True)
            role_item = QTableWidgetItem(infer_role(item.text()))
            role_item.setFlags(Qt.ItemFlag.ItemIsEnabled
                               | Qt.ItemFlag.ItemIsSelectable)
            role_item.setFont(self.table.font())
            self.table.setItem(item.row(), 2, role_item)
            self.table.blockSignals(False)

    def _on_type_change(self, type_name: str) -> None:
        channels = list(FIXTURE_TYPES.get(type_name, []))
        if not channels:
            return
        # Prompt jika ada label non-default dimodifikasi
        has_custom = False
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.text() and item.text() not in BUILTIN_CHANNEL_LABELS:
                has_custom = True
                break
        if has_custom:
            ret = QMessageBox.question(
                self, "Ganti type?",
                "Channel labels sudah dimodifikasi. Ganti dengan template?")
            if ret != QMessageBox.StandardButton.Yes:
                return
        self.ch_spin.blockSignals(True)
        self.ch_spin.setValue(len(channels))
        self.ch_spin.blockSignals(False)
        self.table.blockSignals(True)
        self.table.setRowCount(len(channels))
        for r, label in enumerate(channels):
            self.table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.table.setItem(r, 1, QTableWidgetItem(label))
            role_item = QTableWidgetItem(infer_role(label))
            self.table.setItem(r, 2, role_item)
        self.table.blockSignals(False)

    # ── Load existing ──────────────────────────────────
    def _load_existing(self, name: str) -> None:
        fx = self.manager.get_fixture(name)
        if not fx:
            return
        self.name_edit.setText(name)
        self.mfr_edit.setText(str(fx.get("manufacturer", "Generic")))
        self.ch_spin.setValue(int(fx.get("channels", 4)))
        cmap = fx.get("channel_map", [])
        self.table.blockSignals(True)
        self.table.setRowCount(len(cmap))
        for r, label in enumerate(cmap):
            self.table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.table.setItem(r, 1, QTableWidgetItem(label))
            self.table.setItem(r, 2, QTableWidgetItem(infer_role(label)))
        self.table.blockSignals(False)

    # ── Save ───────────────────────────────────────────
    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nama kosong", "Nama fixture wajib diisi.")
            return
        labels = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            labels.append(item.text() if item else "")
        data = {
            "name": name,
            "manufacturer": self.mfr_edit.text().strip() or "Generic",
            "channels": self.ch_spin.value(),
            "channel_map": labels,
            "type": self.type_combo.currentText(),
            "x": 0.5, "y": 0.5,
        }
        ok, msg = self.manager.save_fixture(data)
        if not ok:
            QMessageBox.warning(self, "Gagal simpan", msg)
            return
        self.saved.emit(name)
