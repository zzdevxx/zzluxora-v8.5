"""
main_window.py — MainWindow v8 (M4): header + sidebar + stacked panels.

Layout:
  HeaderBar (52px) — brand | project | artnet pill | connect | blackout | play
  ─────────────────────────────────────────────────────────────
  Sidebar (210px) | QStackedWidget panels
  ─────────────────────────────────────────────────────────────
  Statusbar (24px)

Shortcuts: Space (play/stop), B (blackout), E (emergency), F1 (help),
Ctrl+1..8 (panel), Ctrl+O/S/Shift+S (project).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from app import AppContext
from core import project_io
from engines.realtime import RealtimePlayer
from panels.about_panel import AboutPanel
from panels.analyze_panel import AnalyzePanel
from panels.chase_panel import ChasePanel
from panels.dashboard_panel import DashboardPanel
from panels.fixture_editor_panel import FixtureEditorPanel
from panels.fixtures_panel import FixturesPanel
from panels.output_panel import OutputPanel
from panels.program_panel import ProgramPanel
from panels.settings_panel import SettingsPanel
from panels.songs_panel import SongsPanel
from styles import DARK_QSS
from widgets.header_bar import HeaderBar
from widgets.help_modal import HelpDialog
from widgets.sidebar import Sidebar, SIDEBAR_ITEMS, PANEL_TITLE
from widgets.toast import show_toast

# Program tab → panel lama yang dipetakan ke tab baru (Fase 3 rebuild)
# Untuk sekarang: program=ProgramPanel, fixtures=FixturesPanel, fixture_editor,
# settings, about. Home/Songs/Output/Chase/Analyze masih sebagai panel legacy
# (belum di-tab-kan; Fase 3 menata ulang).
PANEL_FACTORY = {
    "program": ProgramPanel,
    "fixtures": FixturesPanel,
    "fixture_editor": FixtureEditorPanel,
    "settings": SettingsPanel,
    "about": AboutPanel,
}

# Panel legacy yang tetap diakses via menu (sementara, Fase 3 di-tab-kan)
LEGACY_PANELS = {
    "home": DashboardPanel,
    "songs": SongsPanel,
    "output": OutputPanel,
    "chase": ChasePanel,
    "analyze": AnalyzePanel,
}


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("ZZLUXORA")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)
        self.setStyleSheet(DARK_QSS)

        self.panels: dict[str, QWidget] = {}
        self._pending_play = False
        self.player = RealtimePlayer()

        self._build_menubar()
        self._build_central()
        self._build_statusbar()
        self._lock_sidebar(locked=True)
        self._build_shortcuts()

        # Wire player ke ProgramPanel (chase tab)
        if "program" in self.panels:
            self.panels["program"].set_player(self.player)

        # Auto-connect artnet jika config punya default (no-op jika gagal)
        self._auto_connect()

    # ─────────────────────────────────────
    # Menubar
    # ─────────────────────────────────────
    def _build_menubar(self) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu("&File")
        act_new = QAction("New Project", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._new_project)
        file_menu.addAction(act_new)

        act_open = QAction("Open Project…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._open_project)
        file_menu.addAction(act_open)

        act_save = QAction("Save Project", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._save_project)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save Project As…", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()
        act_quit = QAction("Exit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = bar.addMenu("&View")
        self._view_actions: dict[str, QAction] = {}
        for idx, (key, _icon, label) in enumerate(SIDEBAR_ITEMS):
            act = QAction(label, self)
            act.setShortcut(QKeySequence(f"Ctrl+{idx + 1}"))
            act.triggered.connect(lambda _c=False, k=key: self._show_panel(k))
            view_menu.addAction(act)
            self._view_actions[key] = act

        help_menu = bar.addMenu("&Help")
        act_about = QAction("About", self)
        act_about.setShortcut(QKeySequence("Ctrl+H"))
        act_about.triggered.connect(lambda: self._show_panel("about"))
        help_menu.addAction(act_about)
        act_help = QAction("Keyboard Shortcuts", self)
        act_help.setShortcut(QKeySequence("F1"))
        act_help.triggered.connect(self._show_help)
        help_menu.addAction(act_help)

    # ─────────────────────────────────────
    # Central
    # ─────────────────────────────────────
    def _build_central(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        self.header = HeaderBar(self.ctx.project_name)
        self.header.play_toggled.connect(self._on_play_toggled)
        self.header.connect_clicked.connect(self._on_header_connect)
        self.header.blackout_clicked.connect(self._blackout)
        self.header.sidebar_toggle_requested.connect(self._toggle_sidebar)
        outer.addWidget(self.header)

        # Body: sidebar + panels
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.panel_selected.connect(self._show_panel)
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("panelContainer")
        body.addWidget(self.stack, 1)
        outer.addLayout(body, 1)

        self.setCentralWidget(central)

        # Build main panels (5)
        for key, factory in PANEL_FACTORY.items():
            panel = factory(self.ctx)
            self.panels[key] = panel
            self.stack.addWidget(panel)

        # Build legacy panels (diakses via menu/header, tidak di sidebar)
        for key, factory in LEGACY_PANELS.items():
            panel = factory(self.ctx)
            self.panels[key] = panel
            self.stack.addWidget(panel)

        # Locked state: belum load project → sidebar items disabled, tapi hamburger tetap tampil
        self._sidebar_visible = True
        self.stack.setCurrentWidget(self.panels["program"])
        self._show_panel("program")

    # ─────────────────────────────────────
    # Statusbar
    # ─────────────────────────────────────
    def _build_statusbar(self) -> None:
        self.status_lbl = QLabel("Siap")
        self.status_lbl.setObjectName("statusLabel")
        self.statusBar().addWidget(self.status_lbl)
        self.statusBar().setSizeGripEnabled(False)

    def _set_status(self, text: str, state: str = "") -> None:
        self.status_lbl.setText(text)
        self.status_lbl.setProperty("state", state)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

    # ─────────────────────────────────────
    # Shortcuts
    # ─────────────────────────────────────
    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Space"), self, activated=self._toggle_play)
        QShortcut(QKeySequence("B"), self, activated=self._blackout)
        QShortcut(QKeySequence("E"), self, activated=self._emergency_stop)
        QShortcut(QKeySequence("F1"), self, activated=self._show_help)

    def _toggle_play(self) -> None:
        playing = self.header.is_playing()
        self.header.set_playing(not playing)
        self._on_play_toggled(not playing)

    def _blackout(self) -> None:
        self.ctx.artnet.blackout()
        self._set_status("Blackout", "")
        show_toast(self, "Blackout — semua channel 0", kind="warn")

    def _emergency_stop(self) -> None:
        self.header.set_playing(False)
        self.ctx.artnet.emergency_stop()
        self._set_status("Emergency stop — blackout + chase dihentikan", "err")
        show_toast(self, "EMERGENCY STOP", kind="err")

    def _show_help(self) -> None:
        HelpDialog(self).exec()

    # ─────────────────────────────────────
    # Handlers
    # ─────────────────────────────────────
    def _show_panel(self, key: str) -> None:
        if self.sidebar.is_locked() and key in PANEL_FACTORY:
            return  # sidebar terkunci sebelum project di-load
        if key in self.panels:
            self.sidebar.select(key)
            self.stack.setCurrentWidget(self.panels[key])
            panel = self.panels[key]
            if hasattr(panel, "refresh"):
                panel.refresh()
        self._update_view_marker(key)

    def _update_view_marker(self, key: str) -> None:
        """Marker View menu: item aktif dipertebal (feedback §5)."""
        for k, act in self._view_actions.items():
            font = act.font()
            font.setBold(k == key)
            act.setFont(font)

    def set_player(self, player) -> None:
        """Set RealtimePlayer bersama (dipanggil app bootstrap)."""
        self.player = player
        if "program" in self.panels:
            self.panels["program"].set_player(player)

    def _toggle_sidebar(self) -> None:
        # Feedback §7: sidebar baru bisa dibuka setelah load project.
        # Saat locked, hamburger tidak membuka apa-apa — cukup prompt status.
        if self.sidebar.is_locked():
            self._set_status("Silakan buka project (.zlx) untuk mulai", "")
            return
        self._sidebar_visible = not self._sidebar_visible
        self.sidebar.setVisible(self._sidebar_visible)

    def _lock_sidebar(self, locked: bool) -> None:
        self.sidebar.set_locked(locked)
        if locked:
            # Feedback §7: sidebar TERTUTUP secara default, tapi hamburger tetap
            # tampil. Sidebar di-hide; brand samar bisa dilihat via hamburger.
            self._sidebar_visible = False
            self.sidebar.setVisible(False)
            self.stack.setCurrentWidget(self.panels["program"])
            self._set_status("Silakan buka project (.zlx) untuk mulai", "")
        else:
            # Unlock → sidebar langsung muncul (list bisa diklik)
            self._sidebar_visible = True
            self.sidebar.setVisible(True)

    def _on_play_toggled(self, playing: bool) -> None:
        if playing:
            # Ambil scenes dari song saat ini (jika ada) untuk realtime playback
            song = self._current_song()
            scenes = []
            if song:
                scenes = song.get("scenes", [])
            if not scenes and self.ctx.artnet.chase_frames:
                # Fallback: chase frames yang sudah di-set (auto-chase)
                self.ctx.artnet.play_chase(self.ctx.artnet.chase_frames)
                self._set_status("Memutar chase…", "ok")
                return
            if not scenes:
                show_toast(self, "Belum ada song/scenes untuk diputar — Analyze dulu", kind="warn")
                self.header.set_playing(False)
                return

            self.player.load_scenes(scenes)
            self.player.on_status = lambda st: self._set_status(
                f"scene {st.get('scene_index', 0)}/{len(scenes)} {st.get('time', 0):.1f}s", "ok")
            self.player.play(self._send_dmx)
            self._set_status("Memutar audio-reactive…", "ok")
        else:
            self.player.stop()
            self.ctx.artnet.stop_chase()
            self._set_status("Playback dihentikan")

    def _send_dmx(self, dmx: list[int]) -> None:
        self.ctx.artnet.send_frame(dmx)

    def _current_song(self) -> dict | None:
        sid = self.ctx.songs.current_song_id
        if sid:
            return self.ctx.songs.get(sid)
        # Fallback: song terakhir
        ids = self.ctx.songs.ids()
        if ids:
            return self.ctx.songs.get(ids[-1])
        return None

    def _on_header_connect(self) -> None:
        # Route ke OutputPanel (buka panel + trigger connect di sana)
        self._show_panel("output")
        out = self.panels["output"]
        if hasattr(out, "_on_connect"):
            out._on_connect()

    def _auto_connect(self) -> None:
        # Tidak auto-connect saat boot — menunggu aksi user (lebih aman)
        pass

    # ─────────────────────────────────────
    # Project I/O
    # ─────────────────────────────────────
    def _new_project(self) -> None:
        self.ctx.project_name = "Untitled.zlx"
        self.ctx.project_filepath = None
        self.ctx.project_created_at = ""
        self.ctx.fixtures.clear_all()
        self.ctx.songs.clear()
        self.header.set_project("Untitled.zlx")
        self._set_status("Project baru")
        self._refresh_all_panels()

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "zzluxora Project (*.zlx)")
        if not path:
            return
        if project_io.load_project(self.ctx, path):
            self.header.set_project(self.ctx.project_name)
            self._set_status(f"Project dimuat: {path}", "ok")
            show_toast(self, "Project dimuat", kind="ok")
            self._lock_sidebar(locked=False)
            self._show_panel("program")
            self._refresh_all_panels()
        else:
            show_toast(self, "Gagal memuat project", kind="err")

    def _save_project(self) -> None:
        if not self.ctx.project_filepath:
            self._save_project_as()
            return
        if project_io.save_project(self.ctx, self.ctx.project_filepath):
            self.header.set_project(self.ctx.project_name)
            self._set_status(f"Project disimpan: {self.ctx.project_filepath}", "ok")
            show_toast(self, "Project disimpan", kind="ok")

    def _save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "Untitled.zlx", "zzluxora Project (*.zlx)")
        if not path:
            return
        if not path.endswith(".zlx"):
            path += ".zlx"
        if project_io.save_project(self.ctx, path):
            self.header.set_project(self.ctx.project_name)
            self._set_status(f"Project disimpan: {path}", "ok")
            show_toast(self, "Project disimpan", kind="ok")

    def _refresh_all_panels(self) -> None:
        for key, panel in self.panels.items():
            if hasattr(panel, "refresh"):
                panel.refresh()

    # ─────────────────────────────────────
    # Close
    # ─────────────────────────────────────
    def closeEvent(self, event) -> None:
        self.player.stop()
        self.ctx.artnet.emergency_stop()
        self.ctx.cfg.save()
        event.accept()
