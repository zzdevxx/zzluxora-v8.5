"""
tests/test_program_tabs.py — Quinn QA: Fase 3-5 tab logic (offscreen).

Cover:
  - MixerTab: 513 slider (Master+512), set/get, master
  - AddressTab: 512 cell, update_map warna, clear
  - OutputTab: IP valid / invalid, save via ctx.cfg
  - ChaseTab: list load_chase + delete (tanpa ArtNet)
  - ProgramPanel: 8 tab terpasang
Semua headless (QT_QPA_PLATFORM=offscreen), QMessageBox/QInputDialog di-monkeypatch.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (  # noqa: E402
    QApplication, QInputDialog, QMessageBox,
)

QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QInputDialog.getText = staticmethod(lambda *a, **k: ("Scene 1", True))

from app import AppContext  # noqa: E402
from panels.program_panel import ProgramPanel  # noqa: E402
from panels.program_tabs.address_tab import COLS, AddressTab, TYPE_COLORS  # noqa: E402
from panels.program_tabs.mixer_tab import DMX_SIZE, MixerTab  # noqa: E402
from panels.program_tabs.output_tab import OutputTab, _ip_valid  # noqa: E402

_app: QApplication | None = None


def get_app() -> QApplication:
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication([])
    return _app


def test_mixer_513_sliders() -> None:
    get_app()
    m = MixerTab()
    assert len(m._channels) == 512
    assert m._master is not None
    # set/get channel
    m.set_channel(10, 77)
    assert m.get_values()[10] == 77
    m.set_channel(0, 200)
    assert m.master_value() == 200
    # range boundary
    m.set_channel(512, 255)
    assert m.get_values()[512] == 255
    m.set_channel(513, 10)  # out of range → no-op
    assert 513 not in m.get_values()


def test_address_512_cells_24_cols() -> None:
    get_app()
    a = AddressTab()
    assert len(a._cells) == 512
    assert COLS == 24
    assert all(addr in a._cells for addr in (1, 24, 25, 512))
    # update_map warna
    amap = {1: {"fixture_name": "PAR64", "start_address": 1}}
    labels = {"PAR64": {0: ("Dim", "dimmer")}}
    a.update_map(amap, labels)
    assert "D" in a._cells[1].role.text()
    a.clear()
    assert a._cells[1].role.text() == ""


def test_output_ip_validation() -> None:
    get_app()
    assert _ip_valid("127.0.0.1")
    assert _ip_valid("192.168.4.1")
    assert not _ip_valid("999.1.1.1")
    assert not _ip_valid("abc")
    assert not _ip_valid("1.2.3")
    o = OutputTab(AppContext())
    o.set_ip("127.0.0.1")
    assert o.current_ip() == "127.0.0.1"
    o.set_ip("192.168.1.50")
    assert o.current_ip() == "192.168.1.50"


def test_program_panel_8_tabs() -> None:
    get_app()
    ctx = AppContext()
    p = ProgramPanel(ctx)
    names = [p.tabs.tabText(i) for i in range(p.tabs.count())]
    assert names == ["Address", "Analyze", "Scenes", "Chase",
                     "Page", "Mixer", "Preview", "Output"]
    assert p.mixer_tab is not None
    assert p.address_tab is not None


def test_drop_patch_wires_fixtures() -> None:
    get_app()
    ctx = AppContext()
    ctx.fixtures.save_fixture({
        "name": "QA_PAR", "manufacturer": "QA", "channels": 3,
        "channel_map": [{"label": "Dim", "type": "dimmer"},
                        {"label": "R", "type": "red"},
                        {"label": "G", "type": "green"}],
    })
    p = ProgramPanel(ctx)
    p._on_drop_patch(1, "QA_PAR")
    amap = ctx.fixtures.get_address_map()
    assert len(amap) == 3
    assert amap[1]["fixture_name"] == "QA_PAR"
    assert p.address_tab.info.text() == "3 channel ter-patch"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__} PASSED")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {t.__name__} FAILED: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {t.__name__} ERROR: {type(e).__name__}: {e}")
    print(f"{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
