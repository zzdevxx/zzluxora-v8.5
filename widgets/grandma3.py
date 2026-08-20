"""
widgets/grandma3.py — komponen UI khas konsol grandMA3.

  Fader   — vertical slider + LED value display (0-255) + label
  Encoder — QDial encoder wheel + value label (0-255)
  DMXBar  — horizontal bar (channel level display)
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDial, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget,
)


class Fader(QWidget):
    """Vertical grandMA3 fader: label → fader → LED value."""

    value_changed = Signal(int)

    def __init__(self, label: str = "", default: int = 0,
                 minimum: int = 0, maximum: int = 255,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(64)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(3)

        # LED value display (atas)
        self._led = QLabel(str(default))
        self._led.setObjectName("ledDisplay")
        self._led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._led.setFixedHeight(26)
        lay.addWidget(self._led)

        # Vertical fader
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(default)
        self._slider.setFixedHeight(140)
        self._slider.valueChanged.connect(self._on_value)
        lay.addWidget(self._slider, 1)

        # Label (bawah)
        if label:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("cardSub")
            lay.addWidget(lbl)

    def _on_value(self, v: int) -> None:
        self._led.setText(str(v))
        self.value_changed.emit(v)

    # ── API ────────────────────────────────────────────
    def value(self) -> int:
        return self._slider.value()

    def set_value(self, v: int) -> None:
        self._slider.setValue(int(v))

    def set_enabled(self, en: bool) -> None:
        self._slider.setEnabled(en)
        self._led.setEnabled(en)


class Encoder(QWidget):
    """GrandMA3 encoder wheel (dial) + value label."""

    value_changed = Signal(int)

    def __init__(self, label: str = "", default: int = 0,
                 minimum: int = 0, maximum: int = 255,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(96)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(3)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setObjectName("cardSub")
        lay.addWidget(lbl)

        self._dial = QDial()
        self._dial.setRange(minimum, maximum)
        self._dial.setValue(default)
        self._dial.setNotchesVisible(True)
        self._dial.setFixedSize(64, 64)
        self._dial.valueChanged.connect(self._on_value)
        lay.addWidget(self._dial, alignment=Qt.AlignmentFlag.AlignCenter)

        self._led = QLabel(str(default))
        self._led.setObjectName("ledDisplay")
        self._led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._led.setFixedHeight(24)
        lay.addWidget(self._led)

    def _on_value(self, v: int) -> None:
        self._led.setText(str(v))
        self.value_changed.emit(v)

    # ── API ────────────────────────────────────────────
    def value(self) -> int:
        return self._dial.value()

    def set_value(self, v: int) -> None:
        self._dial.setValue(int(v))


class DMXBar(QWidget):
    """Horizontal channel level bar (grandMA3 canal bar)."""

    def __init__(self, label: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)

        if label:
            lbl = QLabel(label)
            lbl.setObjectName("cardSub")
            lbl.setFixedWidth(56)
            lay.addWidget(lbl)

        bar = QSlider(Qt.Orientation.Horizontal)
        bar.setRange(0, 255)
        bar.setValue(0)
        lay.addWidget(bar, 1)

        self._led = QLabel("0")
        self._led.setObjectName("ledDisplay")
        self._led.setFixedWidth(36)
        self._led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._led)

        self._bar = bar
        bar.valueChanged.connect(lambda v: self._led.setText(str(v)))

    # ── API ────────────────────────────────────────────
    def set_value(self, v: int) -> None:
        self._bar.setValue(int(v))
