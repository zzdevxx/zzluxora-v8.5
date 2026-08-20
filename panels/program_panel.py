"""
panels/program_panel.py — Program panel (feedback §8-15).

Program jadi QTabWidget 8 tab:
  Address | Analyze | Scenes | Chase | Page | Mixer | Preview | Output
Semua tab di-build sekali, stateless-ish, dan berbagi ctx yang sama.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QTabWidget, QVBoxLayout, QWidget

from panels.program_tabs.address_tab import AddressTab
from panels.program_tabs.analyze_tab import AnalyzeTab
from panels.program_tabs.chase_tab import ChaseTab
from panels.program_tabs.mixer_tab import MixerTab
from panels.program_tabs.output_tab import OutputTab
from panels.program_tabs.page_tab import PageTab
from panels.program_tabs.preview_tab import PreviewTab
from panels.program_tabs.scenes_tab import ScenesTab
from widgets.panel_base import BasePanel


class ProgramPanel(BasePanel):
    """Container QTabWidget 8 tab (replacement list+flatten play)."""

    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Program", "Address / Analyze / Scenes / Chase / Page / Mixer / Preview / Output")
        self.player = None  # di-set oleh MainWindow (RealtimePlayer)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setObjectName("programTabs")

        self.address_tab = AddressTab(self.ctx)
        self.address_tab.patch_requested.connect(self._on_drop_patch)
        self.address_tab.auto_patch_requested.connect(self._on_auto_patch)
        self.analyze_tab = AnalyzeTab(self.ctx)
        self.scenes_tab = ScenesTab(self.ctx)
        self.chase_tab = ChaseTab(self.ctx, self.player)
        self.page_tab = PageTab()
        self.mixer_tab = MixerTab(self.ctx)
        self.preview_tab = PreviewTab()
        self.output_tab = OutputTab(self.ctx)

        self.tabs.addTab(self.address_tab, "Address")
        self.tabs.addTab(self.analyze_tab, "Analyze")
        self.tabs.addTab(self.scenes_tab, "Scenes")
        self.tabs.addTab(self.chase_tab, "Chase")
        self.tabs.addTab(self.page_tab, "Page")
        self.tabs.addTab(self.mixer_tab, "Mixer")
        self.tabs.addTab(self.preview_tab, "Preview")
        self.tabs.addTab(self.output_tab, "Output")

        self.add_widget(self.tabs)

    def refresh(self) -> None:
        # Wire player ke chase tab setelah main window set
        if self.player is not None:
            self.chase_tab.player = self.player
        # Refresh children yang butuh ctx
        if hasattr(self, "scenes_tab"):
            self.scenes_tab.refresh()
        if hasattr(self, "analyze_tab"):
            self.analyze_tab.refresh()

    def set_player(self, player) -> None:
        self.player = player
        self.chase_tab.player = player

    # ── Drop fixture dari FixturesPanel ke Address ─────
    def _on_drop_patch(self, addr: int, name: str) -> None:
        ok, msg = self.ctx.fixtures.patch(addr, name)
        if ok:
            self._refresh_address_map()
            self._toast(msg, kind="ok")
        else:
            self._toast(msg, kind="err")

    def _on_auto_patch(self) -> None:
        """Auto Patch: popup pilih fixture → patch berurutan ke address kosong."""
        fixtures = self.ctx.fixtures.list_fixtures()
        if not fixtures:
            self._toast("Tidak ada fixture — buat dulu di Fixture Editor", kind="warn")
            return
        name, ok = QInputDialog.getItem(
            self, "Auto Patch", "Pilih fixture:", fixtures, 0, False)
        if not ok or not name:
            return
        # Address kosong pertama (1-based)
        taken = set(self.ctx.fixtures.get_address_map().keys())
        start = next((a for a in range(1, 513) if a not in taken), None)
        if start is None:
            self._toast("Semua address sudah ter-patch", kind="warn")
            return
        ok2, msg = self.ctx.fixtures.patch(start, name)
        if ok2:
            self._refresh_address_map()
            self._toast(f"{name} di-patch ke ch {start}", kind="ok")
        else:
            self._toast(msg, kind="err")

    def _toast(self, msg: str, kind: str = "") -> None:
        parent = self.window()
        if parent and hasattr(parent, "_set_status"):
            parent._set_status(msg, kind if kind else "info")

    def _refresh_address_map(self) -> None:
        """Sinkronkan Address grid dengan patch fixtures."""
        amap = self.ctx.fixtures.get_address_map()
        channel_labels: dict[str, dict[int, tuple[str, str]]] = {}
        for name in self.ctx.fixtures.list_fixtures():
            fx = self.ctx.fixtures.get_fixture(name)
            chans = fx.get("channel_labels", []) if fx else []
            channel_labels[name] = {
                i: (chans[i].get("label", f"Ch {i+1}"), chans[i].get("type", "unknown"))
                for i in range(len(chans))
            }
        self.address_tab.update_map(amap, channel_labels)
        self.address_tab.info.setText(f"{len(amap)} channel ter-patch")

    def current_tab_name(self) -> str:
        return self.tabs.tabText(self.tabs.currentIndex())
