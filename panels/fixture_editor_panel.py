"""
panels/fixture_editor_panel.py — Fixture Editor (feedback §17).

Embedded FixtureEditorForm dengan kontrak v8 (manager + fixture_name,
signal saved(str)/cancelled). Open .json langsung dari folder fixtures/
(membuat fixture def baru), New → form kosong.
"""
from __future__ import annotations

import json
import os

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QStackedWidget,
)

from core import paths
from panels.fixture_editor import FixtureEditorForm
from widgets.empty_state import EmptyState
from widgets.panel_base import BasePanel, Card


class FixtureEditorPanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Fixture Editor", "Edit atau buat definisi fixture")
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = QHBoxLayout()
        open_btn = QPushButton("Open…")
        open_btn.clicked.connect(self._on_open)
        new_btn = QPushButton("New")
        new_btn.setObjectName("primaryButton")
        new_btn.clicked.connect(self._on_new)
        toolbar.addWidget(open_btn)
        toolbar.addWidget(new_btn)
        toolbar.addStretch(1)
        self.add_layout(toolbar)

        card = Card()
        self.stack = QStackedWidget()
        card.body().addWidget(self.stack)
        self.add_widget(card)

        self.empty = EmptyState("03", "Fixture Editor",
                                "Klik New untuk buat fixture baru,\natau Open untuk memuat .json dari folder fixtures")
        self.stack.addWidget(self.empty)
        self.add_stretch()

    # ── Form management ────────────────────────────────
    def _form(self, fixture_name: str | None = None) -> FixtureEditorForm:
        form = FixtureEditorForm(self.ctx.fixtures, fixture_name=fixture_name)
        form.saved.connect(self._on_saved)
        form.cancelled.connect(self._on_cancelled)
        return form

    def _show_form(self, form) -> None:
        self._current_form = form
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _close_form(self) -> None:
        if hasattr(self, "_current_form") and self._current_form is not None:
            w = self._current_form
            self.stack.removeWidget(w)
            w.deleteLater()
            self._current_form = None
        self.stack.setCurrentWidget(self.empty)

    def _on_saved(self, _name: str) -> None:
        self._close_form()
        self._ctx_status("Fixture disimpan")

    def _on_cancelled(self) -> None:
        self._close_form()

    def _ctx_status(self, text: str) -> None:
        parent = self.window()
        if parent and hasattr(parent, "_set_status"):
            parent._set_status(text, "ok")

    # ── Actions ────────────────────────────────────────
    def _on_new(self) -> None:
        self._show_form(self._form(None))

    def _on_open(self) -> None:
        fixtures_dir = paths.get_data_dir("fixtures")
        start = str(fixtures_dir) if fixtures_dir.exists() else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Fixture", start, "Fixture JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Gagal", f"Tidak dapat membaca fixture:\n{exc}")
            return
        name = str(data.get("name", os.path.splitext(os.path.basename(path))[0])).strip()
        if not name:
            QMessageBox.warning(self, "Gagal", "Fixture JSON tidak punya 'name'")
            return
        # Import ke manager (save ulang ke folder fixtures)
        channels = int(data.get("channels", 1))
        data.setdefault("channel_map", [])
        ok, msg = self.ctx.fixtures.save_fixture(
            {"name": name,
             "manufacturer": data.get("manufacturer", "Generic"),
             "channels": channels,
             "channel_map": data["channel_map"],
             "type": data.get("type", "Custom")})
        if not ok:
            QMessageBox.warning(self, "Gagal", msg)
            return
        form = self._form(name)
        self._show_form(form)
        self._ctx_status(f"Fixture '{name}' dimuat untuk edit")

