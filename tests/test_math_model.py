"""
tests/test_math_model.py — zzluxora v8.5

RELEASE BLOCKER.
Test case dari `script_math_model.md §[9]`: "10.000 Reasons"

Expected output:
    A = 0.126
    V = 0.627
    Quadrant = Q4 (Damai/tenang)
    H = 162.7° (cyan)
    S = 0.178
    V_hsv = 0.135
    D = 34, R = 0, G = 6, B = 4, W = 28
    Chase timing = 1500ms (BPM < 90)

Run:   python -m pytest tests/test_math_model.py -v
       python tests/test_math_model.py  (built-in runner)
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Windows cp1252 console fix — allow unicode test output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from engines.audio_engine import AudioFeatures
from engines.analyze_pipeline import (
    normalize_features, compute_va, chase_timing, run_with_features,
)
from engines.color_mapping import (
    va_to_hsv, hsv_to_rgb, rgb_to_rgbw, hsv_to_drgbw,
    get_quadrant, get_quadrant_name, compute_va as cm_compute_va,
)


# ── Test case dari math model §[9] "10.000 Reasons" ────
def make_10k_features() -> AudioFeatures:
    """Raw features untuk '10.000 Reasons' test case."""
    return AudioFeatures(
        duration=300.0,
        tempo=73,
        rms_mean=0.08,
        sc_mean=1800.0,
        mfcc1_mean=-120.0,
        chroma_major=0.72,
        chroma_peak=6,
        onset_rate=1.5,
    )


def test_10k_reasons_normalization():
    """STAGE 3: Normalized values harus match math model §[9]."""
    af = make_10k_features()
    n = normalize_features(af)

    assert abs(n.bpm - 0.108) < 0.001, f"BPM_n expected 0.108, got {n.bpm}"
    assert abs(n.rms - 0.143) < 0.001, f"RMS_n expected 0.143, got {n.rms}"
    assert abs(n.sc - 0.289) < 0.001, f"SC_n expected 0.289, got {n.sc}"
    assert abs(n.mfcc1 - 0.450) < 0.001, f"MFCC1_n expected 0.450, got {n.mfcc1}"
    assert abs(n.onset_rate - 0.133) < 0.001, f"Onset_n expected 0.133, got {n.onset_rate}"
    assert abs(n.chroma_major - 0.720) < 0.001, f"ChromaMajor_n expected 0.720, got {n.chroma_major}"
    print("  ✓ test_10k_normalization PASSED")


def test_10k_va():
    """STAGE 4: V-A harus match A=0.126, V=0.627, Q4."""
    af = make_10k_features()
    n = normalize_features(af)
    va = compute_va(n)

    assert abs(va.arousal - 0.126) < 0.001, f"A expected 0.126, got {va.arousal}"
    assert abs(va.valence - 0.627) < 0.001, f"V expected 0.627, got {va.valence}"
    assert va.quadrant == "Q4", f"Expected Q4, got {va.quadrant}"
    assert va.quadrant_name == "Damai", f"Expected 'Damai', got {va.quadrant_name}"
    print("  ✓ test_10k_va PASSED")


def test_10k_hsv():
    """STAGE 6/8: HSV harus match H=162.7°, S=0.178, V_hsv=0.135."""
    af = make_10k_features()
    n = normalize_features(af)
    va = compute_va(n)

    H, S, V_hsv = va_to_hsv(va.valence, va.arousal, af.chroma_peak, n.rms)

    assert abs(H - 162.7) < 0.5, f"H expected 162.7°, got {H}°"
    assert abs(S - 0.178) < 0.005, f"S expected 0.178, got {S}"
    assert abs(V_hsv - 0.135) < 0.005, f"V_hsv expected 0.135, got {V_hsv}"
    print(f"  ✓ test_10k_hsv PASSED (H={H}°, S={S}, V_hsv={V_hsv})")


def test_10k_drgbw():
    """STAGE 6/8: DRGBW harus match D=34 R=0 G=6 B=4 W=28."""
    af = make_10k_features()
    n = normalize_features(af)
    va = compute_va(n)
    H, S, V_hsv = va_to_hsv(va.valence, va.arousal, af.chroma_peak, n.rms)

    result = hsv_to_drgbw(H, S, V_hsv)
    assert getattr(result, "d", None) is not None, "DRGBW harus object (bukan dict)"

    assert result.d == 34, f"D expected 34, got {result.d}"
    assert result.r == 0, f"R expected 0, got {result.r}"
    assert result.g == 6, f"G expected 6, got {result.g}"
    assert result.b == 4, f"B expected 4, got {result.b}"
    assert result.w == 28, f"W expected 28, got {result.w}"
    print(f"  ✓ test_10k_drgbw PASSED (D={result.d} R={result.r} G={result.g} B={result.b} W={result.w})")


def test_10k_chase_timing():
    """STAGE 7: BPM 73 < 90 → 1500ms chase timing."""
    af = make_10k_features()
    timing = chase_timing(af)
    assert timing == 1500, f"BPM 73 expected 1500ms, got {timing}ms"
    print(f"  ✓ test_10k_chase_timing PASSED ({timing}ms)")


# ── V-A quadrant mapping ───────────────────────────────
def test_quadrant_q1():
    assert get_quadrant(0.8, 0.9) == "Q1"
    assert get_quadrant_name("Q1") == "Praise"


def test_quadrant_q2():
    assert get_quadrant(0.3, 0.9) == "Q2"
    assert get_quadrant_name("Q2") == "Intens"


def test_quadrant_q3():
    assert get_quadrant(0.3, 0.2) == "Q3"
    assert get_quadrant_name("Q3") == "Kontemplatif"


def test_quadrant_q4():
    assert get_quadrant(0.8, 0.2) == "Q4"
    assert get_quadrant_name("Q4") == "Damai"


def test_quadrant_boundary():
    """Boundary V=0.5 → Q3 (V ≤ 0.5)."""
    assert get_quadrant(0.5, 0.2) == "Q3"
    assert get_quadrant(0.5, 0.9) == "Q2"


# ── V-A computation (rule-based) ───────────────────────
def test_compute_va_range():
    """V dan A harus dalam [0,1] untuk semua input ekstrem."""
    for v in (0.0, 0.3, 0.5, 0.9, 1.0):
        V, A = cm_compute_va(v, v, v, v, v, v)
        assert 0.0 <= V <= 1.0
        assert 0.0 <= A <= 1.0


def test_compute_va_weights():
    """Pastikan bobot sesuai math model §[3]:
    A = 0.40*bpm + 0.35*rms + 0.25*onset
    V = 0.50*chroma + 0.30*sc + 0.20*(1-|mfcc1-0.5|*2)
    """
    V, A = cm_compute_va(1.0, 1.0, 1.0, 1.0, 1.0, 0.5)
    assert abs(A - 1.0) < 1e-6
    assert abs(V - 1.0) < 1e-6


# ── HSV → RGB conversion ───────────────────────────────
def test_hsv_red():
    R, G, B = hsv_to_rgb(0, 1, 1)
    assert abs(R - 1.0) < 0.001 and abs(G - 0.0) < 0.001 and abs(B - 0.0) < 0.001


def test_hsv_green():
    R, G, B = hsv_to_rgb(120, 1, 1)
    assert abs(R - 0.0) < 0.001 and abs(G - 1.0) < 0.001 and abs(B - 0.0) < 0.001


def test_hsv_blue():
    R, G, B = hsv_to_rgb(240, 1, 1)
    assert abs(R - 0.0) < 0.001 and abs(G - 0.0) < 0.001 and abs(B - 1.0) < 0.001


def test_hsv_white():
    R, G, B = hsv_to_rgb(0, 0, 1)
    assert abs(R - 1.0) < 0.001 and abs(G - 1.0) < 0.001 and abs(B - 1.0) < 0.001


# ── RGB → RGBW ─────────────────────────────────────────
def test_rgbw_extraction():
    Rp, Gp, Bp, W = rgb_to_rgbw(1.0, 0.5, 0.25)
    assert abs(W - 0.25) < 1e-6
    assert abs(Rp - 0.75) < 1e-6
    assert abs(Gp - 0.25) < 1e-6
    assert abs(Bp - 0.0) < 1e-6


def test_rgbw_gray():
    Rp, Gp, Bp, W = rgb_to_rgbw(0.4, 0.4, 0.4)
    assert abs(Rp + Gp + Bp) < 1e-6
    assert abs(W - 0.4) < 1e-6


# ── Chase timing brackets ──────────────────────────────
def test_chase_timing_120():
    af = AudioFeatures(duration=10, tempo=121, rms_mean=0.1, sc_mean=1000,
                       mfcc1_mean=0, chroma_major=0.5, chroma_peak=6, onset_rate=2)
    assert chase_timing(af) == 500


def test_chase_timing_90():
    af = AudioFeatures(duration=10, tempo=91, rms_mean=0.1, sc_mean=1000,
                       mfcc1_mean=0, chroma_major=0.5, chroma_peak=6, onset_rate=2)
    assert chase_timing(af) == 700


# ── Pattern selection ──────────────────────────────────
def test_pattern_all_on():
    from engines.analyze_pipeline import pick_pattern
    assert pick_pattern(0.8, 100) == "all_on"


def test_pattern_running():
    from engines.analyze_pipeline import pick_pattern
    assert pick_pattern(0.5, 130) == "running"


def test_pattern_gradient():
    from engines.analyze_pipeline import pick_pattern
    assert pick_pattern(0.2, 100) == "gradient"


def test_pattern_center_out():
    from engines.analyze_pipeline import pick_pattern
    assert pick_pattern(0.5, 100) == "center_out"


# ── Full pipeline via run_with_features ────────────────
def test_run_with_features_10k():
    """Pipeline lengkap: semua output konsisten dengan math model §[9]."""
    af = make_10k_features()
    result = run_with_features(af)
    assert result.va.quadrant == "Q4"
    assert result.chase_timing_ms == 1500
    assert 0 <= result.hsv.h < 360


# ── V-A preset override ────────────────────────────────
def test_preset_override_different_hue():
    """Preset berbeda → HSV berbeda dari default."""
    from engines.va_presets import VAPreset, apply_preset
    af = make_10k_features()
    n = normalize_features(af)
    va = compute_va(n)

    default_H, _, _ = apply_preset(VAPreset(), va.valence, va.arousal, af.chroma_peak, n.rms)
    custom = VAPreset(name="Custom", q4_hue_base=200.0)
    custom_H, _, _ = apply_preset(custom, va.valence, va.arousal, af.chroma_peak, n.rms)

    assert default_H != custom_H


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
