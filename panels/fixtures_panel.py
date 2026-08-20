"""
panels/fixtures_panel.py — Fixtures: list CRUD + address patch + drag to Address.

Tampilan grandMA3: daftar fixture expandable (segitiga ▶) menurunkan kanal
(channel label + type). Item fixture bisa di-drag (MIME application/x-zzlx-fixture)
dan di-drop ke Address tab untuk patch otomatis (feedback §16).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QStackedWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from panels.fixture_editor import FixtureEditorForm
from widgets.empty_state import EmptyState
from widgets.panel_base import BasePanel, Card

FIXTURE_MIME = "application/x-zzlx-fixture"


class FixturesPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Fixtures", "Kelola definisi fixture & DMX addresses")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.new_btn = QPushButton("+ New")
        self.new_btn.clicked.connect(self._on_new)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("dangerButton")
        self.del_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)

        toolbar.addSpacing(16)
        toolbar.addWidget(self._label("Addr", "cardSub"))
        self.addr_spin = QSpinBox()
        self.addr_spin.setRange(1, 512)
        self.patch_btn = QPushButton("Patch")
        self.patch_btn.setObjectName("successButton")
        self.patch_btn.clicked.connect(self._on_patch)
        self.unpatch_btn = QPushButton("Unpatch")
        self.unpatch_btn.clicked.connect(self._on_unpatch)
        toolbar.addWidget(self.addr_spin)
        toolbar.addWidget(self.patch_btn)
        toolbar.addWidget(self.unpatch_btn)
        toolbar.addStretch(1)
        self.add_layout(toolbar)

        # Stack: list vs editor
        self.stack = QStackedWidget()

        self.list_card = Card()
        self.list_lay = self.list_card.body()
        # QTreeWidget: expandable ke bawah, item fixture bisa di-drag
        self.fixture_tree = QTreeWidget()
        self.fixture_tree.setHeaderLabels(["Fixture", "Kan", "Address"])
        self.fixture_tree.setAlternatingRowColors(True)
        self.fixture_tree.setDragEnabled(True)
        self.fixture_tree.setAcceptDrops(False)
        self.fixture_tree.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        self.fixture_tree.itemSelectionChanged.connect(self._on_select)
        self.list_lay.addWidget(self.fixture_tree)
        self.patch_lbl = QLabel("")
        self.patch_lbl.setObjectName("hintLabel")
        self.list_lay.addWidget(self.patch_lbl)

        self.empty = EmptyState("◈", "Belum ada fixture",
                                "Klik '+ New' untuk membuat fixture pertama")
        self.stack.addWidget(self.empty)
        self.stack.addWidget(self.list_card)

        self.editor_host = QWidget()
        self.editor_lay = QVBoxLayout(self.editor_host)
        self.editor_lay.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.editor_host)

        self.add_widget(self.stack)

    # ── Handlers ───────────────────────────────────────
    def _on_new(self) -> None:
        self._show_editor(None)

    def _on_edit(self) -> None:
        sel = self._selected()
        if sel:
            self._show_editor(sel)

    def _on_delete(self) -> None:
        sel = self._selected()
        if not sel:
            return
        ret = QMessageBox.question(self, "Hapus fixture",
                                   f"Hapus '{sel}'? Address patch ikut dihapus.")
        if ret == QMessageBox.StandardButton.Yes:
            ok, msg = self.ctx.fixtures.delete_fixture(sel)
            if not ok:
                QMessageBox.warning(self, "Gagal", msg)
            self.refresh()

    def _on_patch(self) -> None:
        sel = self._selected()
        if not sel:
            QMessageBox.information(self, "Pilih fixture", "Pilih fixture dulu.")
            return
        ok, msg = self.ctx.fixtures.patch(self.addr_spin.value(), sel)
        if not ok:
            QMessageBox.warning(self, "Patch gagal", msg)
        self.refresh()

    def _on_unpatch(self) -> None:
        addr = self.addr_spin.value()
        ok, msg = self.ctx.fixtures.unpatch(addr)
        if not ok:
            QMessageBox.information(self, "Unpatch", msg)
        self.refresh()

    def _show_editor(self, name: str | None) -> None:
        self._clear_editor()
        form = FixtureEditorForm(self.ctx.fixtures, name)
        form.saved.connect(lambda n: (self._clear_editor(), self.refresh()))
        form.cancelled.connect(self._clear_editor)
        self.editor_lay.addWidget(form)
        self.stack.setCurrentWidget(self.editor_host)

    def _clear_editor(self) -> None:
        while self.editor_lay.count():
            item = self.editor_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.stack.setCurrentWidget(
            self.list_card if self.ctx.fixtures.list_fixtures() else self.empty)

    def _selected(self) -> str | None:
        item = self.fixture_tree.currentItem()
        if item is None:
            return None
        # Item parent (top-level) = fixture; child = kanal
        if item.parent() is not None:
            item = item.parent()
        name = item.text(0).replace("◈  ", "").split("   ·")[0].strip()
        return name or None

    def _on_select(self) -> None:
        sel = self._selected()
        if not sel:
            self.patch_lbl.setText("")
            return
        addrs = [str(a) for a, info in self.ctx.fixtures.get_address_map().items()
                 if info.get("fixture_name") == sel]
        self.patch_lbl.setText(
            f"{sel}: addresses {' '.join(addrs) if addrs else '(belum di-patch — drag ke Address)'}")

    # ── Refresh ────────────────────────────────────────
    def refresh(self) -> None:
        self.fixture_tree.clear()
        amap = self.ctx.fixtures.get_address_map()
        for name in self.ctx.fixtures.list_fixtures():
            fx = self.ctx.fixtures.get_fixture(name)
            ch = fx.get("channels", "-") if fx else "-"
            top = QTreeWidgetItem([f"◈  {name}", f"{ch}ch", ""])
            addrs = sorted(a for a, info in amap.items()
                           if info.get("fixture_name") == name)
            if addrs:
                top.setText(2, ", ".join(str(a) for a in addrs))
            # Expandable: node kanal di bawah (segitiga)
            for i in range(1, int(ch) + 1):
                child = QTreeWidgetItem([f"    Ch {i}", "", ""])
                top.addChild(child)
            top.setExpanded(bool(addrs))  # otomatis terbuka kalau sudah di-patch
            self.fixture_tree.addTopLevelItem(top)
        self.stack.setCurrentWidget(
            self.list_card if self.ctx.fixtures.list_fixtures() else self.empty)
        self._on_select()

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
