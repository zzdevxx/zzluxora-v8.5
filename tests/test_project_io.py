"""
tests/test_project_io.py — .zlx schema v4.0 round-trip tests.

Run:   python -m pytest tests/test_project_io.py -v
       python tests/test_project_io.py  (built-in runner)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.fixture_manager import FixtureManager
from core.project_io import save_project, load_project, SCHEMA_VERSION


class FakeArtNet:
    target_ip = "127.0.0.1"
    universe = 0
    fps = 30


class FakeCtx:
    """Minimal AppContext stand-in — fixtures/songs/artnet + project state."""

    def __init__(self) -> None:
        self._tmp = tempfile.mkdtemp()
        self.project_name = "Untitled.zlx"
        self.project_filepath = ""
        self.project_created_at = ""
        self.fixtures = FixtureManager(fixtures_dir=self._tmp)
        self.songs = None  # tidak diuji di sini
        self.artnet = FakeArtNet()
        self.chases = []
        self.programs = []
        self.pages = []


def _make_ctx() -> FakeCtx:
    ctx = FakeCtx()
    ctx.project_name = "Show.zlx"
    ctx.fixtures.save_fixture({
        "name": "PAR 5ch",
        "channels": 5,
        "channel_map": ["Dimmer", "Red", "Green", "Blue", "White"],
        "mode": "drgbw",
        "x": 0.3, "y": 0.7,
    })
    ctx.fixtures.patch(1, "PAR 5ch")
    return ctx


def test_roundtrip_basic():
    """Save → load harus mengembalikan fixtures + address_map sama."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "Show.zlx")

    ctx = _make_ctx()
    assert save_project(ctx, path) is True
    assert os.path.isfile(path)

    ctx2 = FakeCtx()
    assert load_project(ctx2, path) is True
    assert ctx2.project_name == "Show.zlx"
    assert "PAR 5ch" in ctx2.fixtures.list_fixtures()
    assert ctx2.fixtures.get_address_map()[1]["fixture_name"] == "PAR 5ch"


def test_roundtrip_artnet():
    """Art-Net settings harus persist."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "Show.zlx")

    ctx = _make_ctx()
    ctx.artnet.target_ip = "192.168.1.50"
    ctx.artnet.universe = 3
    ctx.artnet.fps = 25
    save_project(ctx, path)

    ctx2 = FakeCtx()
    load_project(ctx2, path)
    assert ctx2.artnet.target_ip == "192.168.1.50"
    assert ctx2.artnet.universe == 3
    assert ctx2.artnet.fps == 25


def test_schema_version_written():
    """File .zlx harus berisi schema_version 4.0."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "Show.zlx")
    save_project(_make_ctx(), path)
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["schema_version"] == "4.0"
    assert set(data.keys()) >= {"fixtures", "address_map", "artnet", "chases", "programs"}


def test_load_rejects_wrong_version():
    """Schema 3.0 harus ditolak (tanpa migrasi — ADR Opsi B)."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "Old.zlx")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"schema_version": "3.0", "project_name": "Old"}, fh)

    ctx = FakeCtx()
    assert load_project(ctx, path) is False


def test_load_rejects_missing_keys():
    """File tanpa field wajib harus ditolak (JSON injection guard)."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "Bad.zlx")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"schema_version": "4.0"}, fh)

    ctx = FakeCtx()
    assert load_project(ctx, path) is False


def test_load_rejects_corrupt_json():
    """File JSON korup harus ditolak, bukan crash."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "Corrupt.zlx")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{ not json !!!")

    ctx = FakeCtx()
    assert load_project(ctx, path) is False


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
