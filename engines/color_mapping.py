"""
engines/color_mapping.py — color mapping pipeline (pure logic, no Qt).

Math model (skripsi BAB 3, script_math_model.md):
  §[3] V-A computation (rule-based weighted sum)
  §[4] V-A → HSV (4 quadrants + chroma correction)
  §[5] HSV → RGB (Foley & van Dam)
  §[6] RGB → RGBW (W = min extraction)
"""
from __future__ import annotations

from dataclasses import dataclass

# Tunable parameters (math model §[10])
W_AROUSAL = (0.40, 0.35, 0.25)   # bpm_n, rms_n, onset_n
W_VALENCE = (0.50, 0.30, 0.20)   # chroma_n, sc_n, mfcc1_n
ALPHA_SAT = 0.60                 # S blend (A weight)
BETA_VAL = 0.50                  # V_hsv blend (rms weight)
V_HSV_MIN = 0.10                 # minimum brightness


@dataclass
class HSV:
    """HSV color (math model §[4] output)."""
    h: float
    s: float
    v: float


@dataclass
class DRGBW:
    """8-bit RGBW + dimmer (math model §[5-6] output)."""
    d: int
    r: int
    g: int
    b: int
    w: int


def compute_va(bpm_n: float, rms_n: float, onset_n: float,
               chroma_n: float, sc_n: float, mfcc1_n: float) -> tuple[float, float]:
    """Compute Valence & Arousal from normalized features (math model §[3]).

    Returns:
        (V, A) each in [0, 1].
    """
    w1, w2, w3 = W_AROUSAL
    A = w1 * bpm_n + w2 * rms_n + w3 * onset_n

    w4, w5, w6 = W_VALENCE
    V = w4 * chroma_n + w5 * sc_n + w6 * (1.0 - abs(mfcc1_n - 0.5) * 2.0)

    V = max(0.0, min(1.0, V))
    A = max(0.0, min(1.0, A))
    return V, A


def get_quadrant(V: float, A: float) -> str:
    """Quadrant detection (math model §[3]):
        Q1: V>0.5, A>0.5 → Praise (warm)
        Q2: V<=0.5, A>0.5 → Intens (purple)
        Q3: V<=0.5, A<=0.5 → Kontemplatif (blue)
        Q4: V>0.5, A<=0.5 → Damai (cyan/green)
    """
    if V > 0.5 and A > 0.5:
        return "Q1"
    if V <= 0.5 and A > 0.5:
        return "Q2"
    if V <= 0.5 and A <= 0.5:
        return "Q3"
    return "Q4"


QUADRANT_NAMES = {"Q1": "Praise", "Q2": "Intens", "Q3": "Kontemplatif", "Q4": "Damai"}


def get_quadrant_name(q: str) -> str:
    return QUADRANT_NAMES.get(q, "Unknown")


def va_to_hsv(V: float, A: float, chroma_peak: int = 6,
              rms_norm: float = 0.5) -> tuple[float, float, float]:
    """Map V-A to HSV (math model §[4]).

    Returns:
        (H, S, V_hsv) — H in [0, 360), S and V_hsv in [0, 1].
    """
    if V > 0.5 and A > 0.5:                # Q1 Praise → warm
        H_base = 30 + (V - 0.5) * 60
    elif V <= 0.5 and A > 0.5:              # Q2 Intens → purple
        H_base = 270 + (0.5 - V) * 120
    elif V <= 0.5 and A <= 0.5:             # Q3 Kontemplatif → blue
        H_base = 200 + (0.5 - V) * 120
    else:                                   # Q4 Damai → cyan/green
        H_base = 150 + (V - 0.5) * 100

    H = (H_base + (chroma_peak - 6) * 5) % 360

    S = ALPHA_SAT * A + (1.0 - ALPHA_SAT) * abs(2 * V - 1)
    S = max(0.0, min(1.0, S))

    V_hsv = BETA_VAL * rms_norm + (1.0 - BETA_VAL) * A
    V_hsv = max(V_HSV_MIN, min(1.0, V_hsv))

    return round(H, 2), round(S, 4), round(V_hsv, 4)


def hsv_to_rgb(H: float, S: float, V: float) -> tuple[float, float, float]:
    """Convert HSV → RGB (Foley & van Dam, math model §[5]).

    Returns:
        (R, G, B) each in [0, 1].
    """
    C = V * S
    Hp = H / 60.0
    X = C * (1 - abs(Hp % 2 - 1))
    m = V - C

    if Hp < 1:
        R1, G1, B1 = C, X, 0
    elif Hp < 2:
        R1, G1, B1 = X, C, 0
    elif Hp < 3:
        R1, G1, B1 = 0, C, X
    elif Hp < 4:
        R1, G1, B1 = 0, X, C
    elif Hp < 5:
        R1, G1, B1 = X, 0, C
    else:
        R1, G1, B1 = C, 0, X

    return R1 + m, G1 + m, B1 + m


def rgb_to_rgbw(R: float, G: float, B: float) -> tuple[float, float, float, float]:
    """Extract white channel (math model §[6]): W = min(R,G,B)."""
    W = min(R, G, B)
    return R - W, G - W, B - W, W


def hsv_to_drgbw(H: float, S: float, V: float, dimmer: int | None = None) -> DRGBW:
    """Full pipeline: HSV → RGB → RGBW → 8-bit DRGBW.

    dimmer defaults to round(V * 255) (math model §[9]: V=0.135 → D=34).
    """
    R, G, B = hsv_to_rgb(H, S, V)
    Rp, Gp, Bp, W = rgb_to_rgbw(R, G, B)
    if dimmer is None:
        dimmer = int(round(V * 255))
    return DRGBW(
        d=dimmer,
        r=int(round(Rp * 255)),
        g=int(round(Gp * 255)),
        b=int(round(Bp * 255)),
        w=int(round(W * 255)),
    )


def va_to_drgbw(V: float, A: float, chroma_peak: int = 6,
                rms_norm: float = 0.5, dimmer: int | None = None) -> dict:
    """Convenience: V-A → HSV → DRGBW with metadata.

    dimmer default: round(V_hsv * 255) (math model §[6] & §[9], konsisten
    dengan hsv_to_drgbw). Sebelumnya default 255 — salah & tidak dipakai.
    """
    H, S, V_hsv = va_to_hsv(V, A, chroma_peak, rms_norm)
    drgbw = hsv_to_drgbw(H, S, V_hsv, dimmer=dimmer)
    return {
        **drgbw.__dict__,
        "hue": H,
        "saturation": S,
        "value_hsv": V_hsv,
        "quadrant": get_quadrant(V, A),
    }
