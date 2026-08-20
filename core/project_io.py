"""
core/project_io.py — save/load .zlx project files (schema v4.0, pure logic).

Schema v4.0 — NEW format, NO migration from v3.x (per ADR-0x, Opsi B).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

SCHEMA_VERSION = "4.0"

_REQUIRED_TOP_KEYS = {"schema_version", "project_name", "fixtures", "artnet"}


def serialize_project(ctx) -> dict:
    """Collect all service state into a dict (schema v4.0)."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cfg = getattr(ctx, "cfg", None)
    artnet = getattr(ctx, "artnet", None)

    fixtures = getattr(ctx, "fixtures", None)
    songs = getattr(ctx, "songs", None)
    song_dicts = {}
    if songs is not None:
        for sid in songs.ids():
            song = songs.get(sid)
            if isinstance(song, dict):
                song_dicts[sid] = song
            elif hasattr(song, "to_dict"):
                song_dicts[sid] = song.to_dict()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_name": getattr(ctx, "project_name", "Untitled.zlx"),
        "created_at": getattr(ctx, "project_created_at", now),
        "updated_at": now,
        "fixtures": {f["name"]: f for f in (fixtures.list() if fixtures else [])},
        "address_map": (fixtures.get_address_map() if fixtures else {}) or {},
        "songs": song_dicts,
        "artnet": {
            "target_ip": getattr(artnet, "target_ip", "127.0.0.1"),
            "universe": getattr(artnet, "universe", 0),
            "fps": getattr(artnet, "fps", 30),
        },
        "chases": [c.to_dict() for c in getattr(ctx, "chases", [])],
        "programs": [p.to_dict() for p in getattr(ctx, "programs", [])],
        "pages": getattr(ctx, "pages", []),
    }


def save_project(ctx, filepath: str) -> bool:
    """Save service state to a .zlx file. Returns True on success."""
    try:
        data = serialize_project(ctx)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        ctx.project_filepath = filepath
        ctx.project_name = os.path.basename(filepath)
        ctx.project_created_at = data["created_at"]
        return True
    except Exception as e:
        print(f"save_project failed: {e}")
        return False


def load_project(ctx, filepath: str) -> bool:
    """Load service state from a .zlx file (v4.0 only). Returns True on success."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # Schema validation (minimum fields) — JSON injection guard
        if not isinstance(data, dict):
            print("load_project failed: root bukan object JSON")
            return False
        if data.get("schema_version") != SCHEMA_VERSION:
            print(f"load_project failed: schema {data.get('schema_version')} != {SCHEMA_VERSION}")
            return False
        missing = _REQUIRED_TOP_KEYS - set(data.keys())
        if missing:
            print(f"load_project failed: missing keys {sorted(missing)}")
            return False

        ctx.project_name = data.get("project_name", "Untitled.zlx")
        ctx.project_filepath = filepath
        ctx.project_created_at = data.get("created_at", "")

        # Restore fixtures + address map (best-effort, each fixture validated)
        fixture_manager = getattr(ctx, "fixtures", None)
        if fixture_manager is not None:
            fixture_manager.clear_fixtures()
            for raw in data.get("fixtures", {}).values():
                try:
                    fixture_manager.save_fixture(raw)
                except Exception as e:
                    print(f"load_project: skip fixture {raw.get('name', '?')}: {e}")
            for addr, raw in data.get("address_map", {}).items():
                try:
                    fixture_manager.patch(
                        int(raw.get("start_address", addr)),
                        raw["fixture_name"],
                    )
                except Exception as e:
                    print(f"load_project: skip address {addr}: {e}")

        # Songs
        song_store = getattr(ctx, "songs", None)
        if song_store is not None:
            song_store.clear()
            for raw in data.get("songs", {}).values():
                try:
                    song_store.add(raw)
                except Exception as e:
                    print(f"load_project: skip song {raw.get('filename', '?')}: {e}")

        # Art-Net
        artnet = getattr(ctx, "artnet", None)
        if artnet is not None:
            a = data.get("artnet", {})
            artnet.target_ip = a.get("target_ip", "127.0.0.1")
            artnet.universe = a.get("universe", 0)
            artnet.fps = a.get("fps", 30)

        # Chases / Programs / Pages
        ctx.chases = data.get("chases", [])
        ctx.programs = data.get("programs", [])
        ctx.pages = data.get("pages", [])

        return True
    except Exception as e:
        print(f"load_project failed: {e}")
        return False
