"""
styles.py — zzluxora v8 design system — "grandMA3 dark" theme.

Referensi UI: grandMA3 (MA Lighting onPC) — konsol lighting profesional.
Karakteristik yang diadopsi:
  - Background hitam pekat (#0A0A0C) — bukan abu gelap
  - Warna aksen KUNING #FFD600 (signature grandMA3) untuk selection/active
  - Surface abu gelap berlapis: #121215 / #1A1A20 / #26262C / #32323A
  - Header strip abu terang (#A7A7AA) di atas — khas grandMA3
  - Text putih terang (#E8E8EA) + muted abu (#8A8A92)
  - Aksen pendukung: hijau (#2ECC71 status ok), merah (#E74C3C error),
    biru (#519CE7 info/links)

Design tokens (v8 grandMA3):
  BG_DEEP    #0A0A0C  (window)
  BG_SURFACE #121215  (sidebar, cards)
  BG_RAISED  #1A1A20  (buttons, inputs)
  BG_HOVER   #26262C  (hover)
  BG_ACTIVE  #32323A  (checked/pressed)
  ACCENT     #FFD600  (grandMA3 yellow)
  ACCENT_ALT #519CE7  (blue secondary)
  OK         #2ECC71  (green)
  WARN       #E0AF68
  ERR        #E74C3C  (red)
  TEXT       #E8E8EA
  TEXT_MUTED #8A8A92
  BORDER     #2A2A32

Object names (referenced by panels):
  centralWidget, headerBar, brandLabel, projectLabel, artnetPill,
  headerButton, playButton, stopButton, sidebar, sidebarTitle, sidebarItem,
  panelContainer, panel, sectionTitle, sectionSub, card, cardTitle, cardSub,
  value, valueBig, hintLabel, statusLabel, inputField, primaryButton,
  successButton, dangerButton, toast
"""
from __future__ import annotations

# ── Design tokens (grandMA3 dark) ─────────────────────
BG_DEEP = "#0A0A0C"
BG_SURFACE = "#121215"
BG_RAISED = "#1A1A20"
BG_HOVER = "#26262C"
BG_ACTIVE = "#32323A"
BG_HEADER = "#A7A7AA"        # header strip terang khas grandMA3

ACCENT = "#FFD600"           # grandMA3 yellow
ACCENT_HOVER = "#FFE033"
ACCENT_ALT = "#519CE7"       # blue secondary
OK = "#2ECC71"
WARN = "#E0AF68"
ERR = "#E74C3C"

TEXT = "#E8E8EA"
TEXT_MUTED = "#8A8A92"
BORDER = "#2A2A32"

FONT_STACK = "'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif"

DARK_QSS = f"""
/* ── Global ─────────────────────────────────────────── */
* {{
    font-family: {FONT_STACK};
    font-size: 13px;
    color: {TEXT};
    outline: none;
}}
QMainWindow, QWidget#centralWidget {{
    background: {BG_DEEP};
}}

/* ── Header bar (grandMA3: strip terang) ───────────── */
QWidget#headerBar {{
    background: {BG_HEADER};
    border-bottom: 1px solid {BG_ACTIVE};
}}
QLabel#brandLabel {{
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 2px;
    color: {BG_DEEP};
}}
QLabel#projectLabel {{
    color: {BG_DEEP};
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#artnetPill {{
    background: {BG_DEEP};
    border: 1px solid {BG_ACTIVE};
    border-radius: 12px;
    padding: 4px 12px;
    color: {BG_HEADER};
    font-weight: 800;
    font-size: 12px;
}}
QLabel#artnetPill[state="connected"] {{
    color: {OK};
    border-color: {OK};
}}
QLabel#artnetPill[state="error"] {{
    color: {ERR};
    border-color: {ERR};
}}

/* ── Buttons (grandMA3 console style) ─────────────── */
QPushButton {{
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    border-radius: 2px;           /* grandMA3: sudut hampir siku */
    padding: 6px 14px;
    font-weight: 700;
    color: {TEXT};
    min-height: 18px;
}}
QPushButton:hover {{
    background: {BG_HOVER};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background: {ACCENT};
    color: {BG_DEEP};
}}
QPushButton:checked {{
    background: {ACCENT};
    color: {BG_DEEP};
    border-color: {ACCENT};
    font-weight: 900;
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}
/* hamburger — QToolButton icon-only, jelas bisa diklik (pola QLC+) */
QToolButton#hamburgerBtn {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 2px;
}}
QToolButton#hamburgerBtn:hover {{
    background: {BG_HOVER};
    border-color: {BORDER};
}}
QToolButton#hamburgerBtn:pressed {{
    background: {ACCENT};
}}
QPushButton#primaryButton {{
    background: {ACCENT};
    color: {BG_DEEP};
    border: none;
    font-weight: 900;
}}
QPushButton#primaryButton:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton#dangerButton {{
    background: transparent;
    color: {ERR};
    border: 1px solid {ERR};
}}
QPushButton#dangerButton:hover {{
    background: rgba(231, 76, 60, 0.12);
}}
QPushButton#successButton {{
    background: {OK};
    color: {BG_DEEP};
    border: none;
    font-weight: 900;
}}
QPushButton#playButton {{
    background: {ACCENT};
    color: {BG_DEEP};
    border: none;
    font-weight: 900;
    padding: 8px 24px;
    font-size: 14px;
}}
QPushButton#stopButton {{
    background: transparent;
    color: {ERR};
    border: 2px solid {ERR};
    font-weight: 900;
    padding: 8px 24px;
    font-size: 14px;
}}

/* ── Sidebar ────────────────────────────────────────── */
QWidget#sidebar {{
    background: {BG_SURFACE};
    border-right: 1px solid {BORDER};
}}
QLabel#sidebarTitle {{
    color: {ACCENT};
    font-weight: 900;
    letter-spacing: 1.5px;
    font-size: 12px;
    padding: 14px 8px 6px 22px;
}}
QPushButton#sidebarItem {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 10px 6px 10px 20px;
    color: {TEXT_MUTED};
    text-align: left;
    font-weight: 600;
}}
QPushButton#sidebarItem:hover {{
    background: {BG_RAISED};
    color: {TEXT};
}}
QPushButton#sidebarItem:checked {{
    background: {ACCENT};
    border-left-color: {ACCENT};
    color: {BG_DEEP};
    font-weight: 900;
}}

/* ── Panels ─────────────────────────────────────────── */
QStackedWidget#panelContainer {{
    background: {BG_DEEP};
}}
QWidget#panel {{
    background: {BG_DEEP};
}}
QLabel#sectionTitle {{
    font-size: 21px;
    font-weight: 900;
    color: {TEXT};
    letter-spacing: 0.5px;
}}
QLabel#sectionSub {{
    color: {TEXT_MUTED};
    font-size: 13px;
}}
QLabel#sectionTitle span, QLabel#sectionSub span {{
    color: {ACCENT};
}}

/* ── Cards & surfaces ───────────────────────────────── */
QFrame#card {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;           /* grandMA3: radius kecil */
}}
QLabel#cardTitle {{
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 1px;
    color: {ACCENT};
}}
QLabel#cardSub {{
    color: {TEXT_MUTED};
    font-size: 11px;
}}
QLabel#value {{
    font-size: 15px;
    font-weight: 900;
    color: {ACCENT};
}}
QLabel#valueBig {{
    font-size: 34px;
    font-weight: 900;
    color: {ACCENT};
}}
QLabel#hintLabel {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-style: italic;
}}

/* ── Statusbar ──────────────────────────────────────── */
QStatusBar {{
    background: {BG_SURFACE};
    border-top: 1px solid {BORDER};
    color: {TEXT_MUTED};
    font-size: 11px;
}}
QStatusBar QLabel#statusLabel {{
    color: {TEXT_MUTED};
}}
QStatusBar QLabel#statusLabel[state="ok"] {{
    color: {OK};
}}
QStatusBar QLabel#statusLabel[state="err"] {{
    color: {ERR};
}}

/* ── Forms ──────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {{
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: {BG_DEEP};
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: {BG_DEEP};
}}

/* ── Lists & trees ──────────────────────────────────── */
QListWidget, QTreeWidget, QTableWidget {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 2px;
    alternate-background-color: {BG_RAISED};
}}
QListWidget::item, QTreeWidget::item {{
    padding: 5px 8px;
    border-radius: 2px;
    color: {TEXT};
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background: {BG_RAISED};
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {ACCENT};
    color: {BG_DEEP};
    font-weight: 800;
}}
QHeaderView::section {{
    background: {BG_ACTIVE};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 5px 8px;
    font-weight: 800;
    color: {ACCENT};
}}

/* ── Sliders (grandMA3 fader) ──────────────────────── */
QSlider::groove:horizontal {{
    height: 6px;
    background: {BG_ACTIVE};
    border: 1px solid {BORDER};
    border-radius: 1px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
}}
QSlider::handle:horizontal {{
    width: 18px;
    height: 20px;
    margin: -8px 0;
    border-radius: 2px;
    background: {ACCENT};
    border: 1px solid {ACCENT_HOVER};
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_HOVER};
}}
/* Vertical (fader) — channel level */
QSlider::groove:vertical {{
    width: 6px;
    background: {BG_ACTIVE};
    border: 1px solid {BORDER};
}}
QSlider::add-page:vertical {{
    background: {ACCENT};
}}
QSlider::handle:vertical {{
    width: 22px;
    height: 16px;
    margin: 0 -8px;
    border-radius: 2px;
    background: {ACCENT};
    border: 1px solid {ACCENT_HOVER};
}}
QSlider::handle:vertical:hover {{
    background: {ACCENT_HOVER};
}}
QProgressBar {{
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    border-radius: 1px;
    height: 12px;
    text-align: center;
    color: {TEXT};
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 1px;
}}

/* ── Dial / encoder (grandMA3 wheel) ──────────────── */
QDial {{
    background: {BG_SURFACE};
    border: 2px solid {BORDER};
    border-radius: 26px;
}}
QDial::handle {{
    background: {ACCENT};
    border: 2px solid {BG_DEEP};
    border-radius: 8px;
    width: 14px;
    height: 14px;
}}

/* ── Group box ─────────────────────────────────────── */
QGroupBox {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 2px;
    margin-top: 14px;
    padding-top: 8px;
    font-weight: 900;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 2px 8px;
    color: {ACCENT};
    background: {BG_SURFACE};
}}

/* ── LED display (canal-style) ─────────────────────── */
QLabel#ledDisplay, QLabel#valueBig {{
    background: {BG_DEEP};
    border: 1px solid {BORDER};
    border-radius: 2px;
    padding: 6px 10px;
    color: {ACCENT};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 24px;
    font-weight: 900;
}}

/* ── Scrollbars ─────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG_DEEP};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}

/* ── Menubar ────────────────────────────────────────── */
QMenuBar {{
    background: {BG_HEADER};
    border-bottom: 1px solid {BG_ACTIVE};
    color: {BG_DEEP};
}}
QMenuBar::item {{
    padding: 5px 12px;
    background: transparent;
    font-weight: 700;
}}
QMenuBar::item:selected {{
    background: {ACCENT};
    color: {BG_DEEP};
}}
QMenu {{
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 28px 6px 14px;
    border-radius: 2px;
}}
QMenu::item:selected {{
    background: {ACCENT};
    color: {BG_DEEP};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 5px 10px;
}}

/* ── Tabs ───────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {BG_SURFACE};
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 8px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 700;
}}
QTabBar::tab:selected {{
    color: {ACCENT};
    border-bottom-color: {ACCENT};
}}
QTabBar::tab:hover {{
    color: {TEXT};
}}

/* ── Misc ───────────────────────────────────────────── */
QToolTip {{
    background: {BG_RAISED};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 5px 8px;
    border-radius: 4px;
}}
QFrame#separator {{
    background: {BORDER};
    max-height: 1px;
}}
QCheckBox {{
    spacing: 8px;
    color: {TEXT};
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 2px;
    border: 1px solid {BORDER};
    background: {BG_RAISED};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QLabel#toast {{
    background: {BG_RAISED};
    border: 1px solid {ACCENT};
    color: {ACCENT};
    border-radius: 4px;
    padding: 10px 18px;
    font-weight: 800;
}}
"""
