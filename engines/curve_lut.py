"""
engines/curve_lut.py — 1D piecewise-linear LUT (pure logic, no Qt).

Used for Saturation (S) and Brightness (V) curve shaping.
Default = identity line (y = x).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from core import paths

Point = tuple[float, float]


def identity_points(n: int = 11) -> list[Point]:
    """Default identity LUT with N points (x = y evenly spaced)."""
    return [(i / (n - 1), i / (n - 1)) for i in range(n)]


@dataclass
class CurveLUT:
    name: str = "Identity"
    points: list[Point] = field(default_factory=lambda: identity_points(11))

    def evaluate(self, x: float) -> float:
        """Piecewise-linear evaluation. x clamped to [0, 1]."""
        if not self.points:
            return x
        x = max(0.0, min(1.0, x))
        pts = self.points
        if x <= pts[0][0]:
            return pts[0][1]
        if x >= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= x <= x1:
                if x1 == x0:
                    return y0
                t = (x - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    def to_dict(self) -> dict:
        return {"name": self.name, "points": [list(p) for p in self.points]}

    @classmethod
    def from_dict(cls, d: dict) -> "CurveLUT":
        pts = [tuple(p) for p in d.get("points", identity_points(11))]
        return cls(name=d.get("name", "Identity"), points=pts)


def build_curve(kind: str, n: int = 256) -> list[float]:
    """Build a normalized curve LUT. kind: linear | exp | log."""
    xs = [i / (n - 1) for i in range(n)]
    if kind == "exp":
        return [x * x for x in xs]
    if kind == "log":
        return [x ** 0.5 for x in xs]
    return xs  # linear


def apply_curve(values: list[float], curve: list[float]) -> list[float]:
    """Apply LUT to values in [0,1] via nearest index."""
    if not curve:
        return values
    n = len(curve)
    return [curve[max(0, min(n - 1, int(round(v * (n - 1)))))] for v in values]


# ── Storage (curves/) ──────────────────────────────────
def _curves_dir() -> str:
    return str(paths.get_data_dir("presets/curves"))


def list_curves() -> list[str]:
    d = _curves_dir()
    if not os.path.isdir(d):
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".json"))


def save_curve(curve: CurveLUT) -> None:
    path = os.path.join(_curves_dir(), f"{curve.name}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(curve.to_dict(), fh, indent=2)


def load_curve(name: str) -> CurveLUT | None:
    path = os.path.join(_curves_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return CurveLUT.from_dict(json.load(fh))


def delete_curve(name: str) -> bool:
    if name == "Identity":
        return False  # protect default
    path = os.path.join(_curves_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True
