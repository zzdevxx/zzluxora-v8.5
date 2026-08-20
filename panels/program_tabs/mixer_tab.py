"""
panels/program_tabs/mixer_tab.py — Mixer (feedback §13): 513 slider.

Model referensi QLC+ ConsoleChannel (ui/src/consolechannel.cpp): setiap channel
= QGroupBox berisi label + slider + spinbox (value 0-255), tersusun horizontal
dengan scroll. Header [Master Dimmer][Ch1..Ch512]. Tombol Refresh kanan atas.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSlider,
    QSpinBox, QVBoxLayout, QWidget,
)

# QLC+ model: DMX 512 + master
DMX_SIZE = 512


class ChannelSlider(QGroupBox):
    """Satu slider channel (model ConsoleChannel QLC+)."""

    value_changed = Signal(int, int)  # (channel_index, value)

    def __init__(self, index: int, label: str, parent=None) -> None:
        super().__init__(parent)
        self.index = index
        self.setObjectName("mixerChannel")
        self.setCheckable(False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(3)

        # Label channel
        self.lbl = QLabel(label)
        self.lbl.setObjectName("mixerLabel")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.lbl)

        # Slider vertikal
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 255)
        self.slider.setValue(0)
        self.slider.setObjectName("mixerSlider")
        lay.addWidget(self.slider, 1)

        # Value spinbox (QLC+ style manual input)
        self.spin = QSpinBox()
        self.spin.setRange(0, 255)
        self.spin.setObjectName("mixerSpin")
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.spin)

        # Sync slider ↔ spinbox
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(
            lambda v, i=self.index: self.value_changed.emit(i, v))

    def value(self) -> int:
        return self.slider.value()

    def set_value(self, v: int, notify: bool = False) -> None:
        if notify:
            self.slider.setValue(v)
        else:
            self.spin.blockSignals(True)
            self.slider.blockSignals(True)
            self.spin.setValue(v)
            self.slider.setValue(v)
            self.spin.blockSignals(False)
            self.slider.blockSignals(False)


class MixerTab(QWidget):
    """Mixer 513 slider: [Master][Ch1..Ch512], scroll horizontal."""

    master_changed = Signal(int)
    channel_changed = Signal(int, int)

    def __init__(self, ctx=None, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._channels: list[ChannelSlider] = []
        self._master: ChannelSlider | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Header row: title + refresh
        head = QHBoxLayout()
        title = QLabel("Mixer")
        title.setObjectName("cardTitle")
        head.addWidget(title)
        head.addStretch(1)
        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.setObjectName("toolButton")
        self.refresh_btn.clicked.connect(self.refresh)
        head.addWidget(self.refresh_btn)
        root.addLayout(head)

        # Scroll area horizontal
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("mixerScroll")

        container = QWidget()
        self._sliders_lay = QHBoxLayout(container)
        self._sliders_lay.setContentsMargins(4, 4, 4, 4)
        self._sliders_lay.setSpacing(4)

        # Master
        self._master = ChannelSlider(0, "MASTER")
        self._master.slider.setStyleSheet("""
            QSlider::groove:vertical { background:#FFD600; width:6px; border-radius:3px; }
            QSlider::handle:vertical { background:#0A0A0C; height:14px; width:14px;
                                       margin:0 -4px; border-radius:2px; }
        """)
        self._master.value_changed.connect(self.master_changed.emit)
        self._sliders_lay.addWidget(self._master)

        # 512 channel
        for i in range(1, DMX_SIZE + 1):
            ch = ChannelSlider(i, str(i))
            ch.value_changed.connect(self.channel_changed.emit)
            self._sliders_lay.addWidget(ch)
            self._channels.append(ch)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

    # ── API ────────────────────────────────────────────
    def refresh(self) -> None:
        """Refresh dari DMX aktual (ArtNetController kalau tersedia)."""
        artnet = getattr(self.ctx, "artnet", None) if self.ctx else None
        if artnet is None or not hasattr(artnet, "dmx"):
            return
        dmx = artnet.dmx
        if dmx is not None:
            for i, v in enumerate(dmx[:DMX_SIZE]):
                self.set_channel(i + 1, v)

    def set_ctx(self, ctx) -> None:
        self.ctx = ctx

    def set_channel(self, index: int, value: int) -> None:
        """Set channel 1-512 (atau 0=master) tanpa emit."""
        if index == 0 and self._master:
            self._master.set_value(value)
        elif 1 <= index <= DMX_SIZE:
            self._channels[index - 1].set_value(value)

    def get_values(self) -> dict[int, int]:
        """Baca semua nilai: {0: master, 1..512: channel}."""
        vals: dict[int, int] = {0: self._master.value()}
        for ch in self._channels:
            vals[ch.index] = ch.value()
        return vals

    def master_value(self) -> int:
        return self._master.value() if self._master else 0
