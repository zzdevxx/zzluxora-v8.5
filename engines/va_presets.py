"""
engines/va_presets.py — VAPreset: per-quadrant V-A → HSV override (pure logic).

Default preset is implicit (VAPreset() defaults) and never written to disk.
Custom presets persist as JSON in the writable data dir.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from core import paths

DEFAULT_PRESET_NAME = "Default Praise"


@dataclass
class VAPreset:
    """Custom V-A → HSV mapping (per-quadrant hue + blend weights)."""
    name: str = DEFAULT_PRESET_NAME
    q1_hue_base: float = 30.0    # Q1 Praise warm (orange-amber)
    q2_hue_base: float = 270.0   # Q2 Intens purple
    q3_hue_base: float = 200.0   # Q3 Kontemplatif blue
    q4_hue_base: float = 150.0   # Q4 Damai cyan/green
    q1_hue_range: float = 60.0
    q2_hue_range: float = 120.0
    q3_hue_range: float = 120.0
    q4_hue_range: float = 100.0
    chroma_offset_deg: float = 5.0
    alpha_sat: float = 0.60
    beta_val: float = 0.50
    v_min: float = 0.10


def _presets_dir() -> str:
    return str(paths.get_data_dir("presets"))


def list_presets() -> list[str]:
    """Return saved preset names (excluding implicit default)."""
    import os
    d = _presets_dir()
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def load_preset(name: str) -> VAPreset:
    """Load preset by name. Returns defaults for default/unknown names."""
    if not name or name == DEFAULT_PRESET_NAME:
        return VAPreset()
    import os
    path = os.path.join(_presets_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return VAPreset(name=name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["name"] = name
        return VAPreset(**data)
    except (OSError, json.JSONDecodeError, TypeError):
        return VAPreset(name=name)


def save_preset(preset: VAPreset) -> None:
    """Save preset. Default preset is implicit (not saved)."""
    if preset.name == DEFAULT_PRESET_NAME:
        return
    import os
    path = os.path.join(_presets_dir(), f"{preset.name}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(preset), fh, indent=2)


def delete_preset(name: str) -> bool:
    """Delete preset file. Returns True if removed."""
    import os
    if name == DEFAULT_PRESET_NAME:
        return False
    path = os.path.join(_presets_dir(), f"{name}.json")
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def apply_preset(preset: VAPreset, V: float, A: float,
                 chroma_peak: int = 6, rms_norm: float = 0.5) -> tuple[float, float, float]:
    """Apply VAPreset to compute HSV. Returns (H, S, V_hsv)."""
    if V > 0.5 and A > 0.5:                # Q1
        H_base = preset.q1_hue_base + (V - 0.5) * preset.q1_hue_range
    elif V <= 0.5 and A > 0.5:              # Q2
        H_base = preset.q2_hue_base + (0.5 - V) * preset.q2_hue_range
    elif V <= 0.5 and A <= 0.5:             # Q3
        H_base = preset.q3_hue_base + (0.5 - V) * preset.q3_hue_range
    else:                                   # Q4
        H_base = preset.q4_hue_base + (V - 0.5) * preset.q4_hue_range

    H = (H_base + (chroma_peak - 6) * preset.chroma_offset_deg) % 360

    S = preset.alpha_sat * A + (1.0 - preset.alpha_sat) * abs(2 * V - 1)
    S = max(0.0, min(1.0, S))

    V_hsv = preset.beta_val * rms_norm + (1.0 - preset.beta_val) * A
    V_hsv = max(preset.v_min, min(1.0, V_hsv))

    return round(H, 2), round(S, 4), round(V_hsv, 4)
