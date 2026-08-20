"""
core/fixture_manager.py — fixtures + DMX address map CRUD (entity: FixtureDefinition, AddressPatch).

Persists fixtures to JSON in the writable data dir (dev: project root/fixtures,
frozen: %APPDATA%/zzluxora/fixtures). Seeded from bundle on first frozen run.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from core import paths


class FixtureManager:
    """In-memory store for fixture definitions and DMX address map."""

    def __init__(self, fixtures_dir: str | None = None) -> None:
        self.fixtures: dict[str, dict] = {}
        self.address_map: dict[int, dict] = {}
        self._dir = paths.get_data_dir("fixtures") if fixtures_dir is None else Path(fixtures_dir)
        self._seed_from_bundle()
        self.load_all()

    # ── Seed from PyInstaller bundle ───────────────────
    def _seed_from_bundle(self) -> None:
        if any(self._dir.glob("*.json")):
            return
        bundle = paths.get_bundle_base()
        if not bundle:
            return
        src = bundle / "fixtures"
        if not src.exists():
            return
        for f in src.glob("*.json"):
            try:
                shutil.copy(f, self._dir / f.name)
            except OSError:
                pass

    # ── Fixtures ───────────────────────────────────────
    def load_all(self) -> list[str]:
        self.fixtures.clear()
        for path in self._dir.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                name = data.get("name") or path.stem
                data.setdefault("filename", path.name)
                data.setdefault("x", 0.5)
                data.setdefault("y", 0.5)
                self.fixtures[name] = data
            except (OSError, json.JSONDecodeError):
                continue
        return self.list_fixtures()

    def save_fixture(self, data: dict) -> tuple[bool, str]:
        name = str(data.get("name", "")).strip()
        if not name:
            return False, "Name is required"
        if not isinstance(data.get("channels"), int) or data["channels"] < 1:
            return False, "Channels must be a positive integer"
        if not isinstance(data.get("channel_map"), list):
            return False, "channel_map must be a list"

        safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe:
            return False, "Name has no valid filename characters"

        path = self._dir / f"{safe}.json"
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            return False, f"Write failed: {exc}"
        self.fixtures[name] = {**data, "filename": path.name}
        return True, f"Saved: {path.name}"

    def delete_fixture(self, name: str) -> tuple[bool, str]:
        if name not in self.fixtures:
            return False, f"Not found: {name}"
        fname = self.fixtures[name].get("filename")
        if fname:
            path = self._dir / fname
            if path.exists():
                path.unlink()
        del self.fixtures[name]
        self.address_map = {
            k: v for k, v in self.address_map.items()
            if v.get("fixture_name") != name
        }
        return True, f"Deleted: {name}"

    def get_fixture(self, name: str) -> dict | None:
        return self.fixtures.get(name)

    def list_fixtures(self) -> list[str]:
        return sorted(self.fixtures)

    def list(self) -> list[dict]:
        """Return all fixture definitions as dicts (for .zlx serialization)."""
        return [self.fixtures[name] for name in sorted(self.fixtures)]

    def clear_fixtures(self) -> None:
        """Hapus semua fixture in-memory (tanpa hapus file di disk)."""
        self.fixtures.clear()
        self.address_map.clear()

    # ── Address map ────────────────────────────────────
    def patch(self, address: int, fixture_name: str) -> tuple[bool, str]:
        if address < 1 or address > 512:
            return False, "Address must be 1-512"
        if fixture_name not in self.fixtures:
            return False, f"Unknown fixture: {fixture_name}"
        fx = self.fixtures[fixture_name]
        ch_count = fx.get("channels", 1)
        for offset in range(ch_count):
            addr = address + offset
            if addr > 512:
                return False, f"Exceeds 512 at channel {offset + 1}"
            if addr in self.address_map:
                existing = self.address_map[addr]["fixture_name"]
                same_fx_same_start = (
                    existing == fixture_name
                    and self.address_map[addr].get("start_address") == address
                )
                if same_fx_same_start:
                    continue
                return False, f"Address {addr} already patched to '{existing}'"
        for offset in range(ch_count):
            addr = address + offset
            self.address_map[addr] = {
                "fixture_name": fixture_name,
                "start_address": address,
            }
        return True, f"Patched '{fixture_name}' at {address}-{address + ch_count - 1}"

    def unpatch(self, address: int) -> tuple[bool, str]:
        if address not in self.address_map:
            return False, "Address not patched"
        start = self.address_map[address]["start_address"]
        fx_name = self.address_map[address]["fixture_name"]
        ch_count = self.fixtures.get(fx_name, {}).get("channels", 1)
        for offset in range(ch_count):
            self.address_map.pop(start + offset, None)
        return True, f"Unpatched '{fx_name}' from {start}-{start + ch_count - 1}"

    def get_address_map(self) -> dict[int, dict]:
        return self.address_map

    def clear_all(self) -> None:
        self.address_map.clear()
