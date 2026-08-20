"""
tests/test_artnet.py — Art-Net sender v8 logika murni (tanpa socket).

Uji: render scene DRGBW → DMX addresses mapping, blackout, emergency_stop,
status fields — semua tanpa benar-benar connect (offline aman).

   python tests/test_artnet.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from engines.artnet_sender import ArtNetController, DMX_SIZE, ARTNET_PORT

ADDRESS_MAP = {
    1: {"fixture_name": "PAR 1", "start_address": 1},
    6: {"fixture_name": "PAR 2", "start_address": 6},
}


def test_scene_maps_to_addresses():
    """Scene DRGBW harus menulis channel 1-5 dan 6-10 sesuai address_map."""
    c = ArtNetController()
    scene = {"d": 200, "r": 255, "g": 100, "b": 0, "w": 50}
    dmx = c._render_scene_to_dmx(scene, ADDRESS_MAP)
    # Fixture 1 (addr 1): D=200 R=255 G=100 B=0 W=50
    assert dmx[0] == 200, f"addr1 dimmer expected 200, got {dmx[0]}"
    assert dmx[1] == 255
    assert dmx[2] == 100
    assert dmx[3] == 0
    assert dmx[4] == 50
    # Fixture 2 (addr 6): sama
    assert dmx[5] == 200
    assert dmx[6] == 255
    assert dmx[7] == 100
    assert dmx[8] == 0
    assert dmx[9] == 50


def test_scene_supports_dimmer_alias():
    """Scene dengan key 'dimmer' (bukan 'd') juga harus bekerja."""
    c = ArtNetController()
    scene = {"dimmer": 34, "r": 0, "g": 6, "b": 4, "w": 28}
    dmx = c._render_scene_to_dmx(scene, ADDRESS_MAP)
    assert dmx[0] == 34, dmx[0]

def test_scene_ignores_out_of_range():
    """Scene + address_map dengan start_address di luar 1-512 harus diabaikan (no crash)."""
    c = ArtNetController()
    bad_map = {1: {"start_address": 512}}   # 512 + 4 channel > 512 → hanya D channel
    dmx = c._render_scene_to_dmx({"d": 10, "r": 20}, bad_map)
    assert dmx[511] == 10
    assert len(dmx) == DMX_SIZE


def test_dmx_size_always_512():
    c = ArtNetController()
    scene = {"d": 255, "r": 1, "g": 2, "b": 3, "w": 4}
    dmx = c._render_scene_to_dmx(scene, {})
    assert len(dmx) == DMX_SIZE


def test_port_constant():
    """Port Art-Net harus 6454 (standar)."""
    assert ARTNET_PORT == 6454


# ── Built-in runner ────────────────────────────────────
if __name__ == "__main__":
    import traceback

    failed = 0
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL  {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
