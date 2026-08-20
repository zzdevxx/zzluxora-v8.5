"""
engines/analyze_pipeline.py — 8-stage audio analysis pipeline (pure logic, no Qt).

Stages (skripsi math model / BAB 3):
  STAGE 1: Load Audio            (librosa.load)
  STAGE 2: Extract Features      (7 fitur audio)
  STAGE 3: Normalize             (min-max [0,1])
  STAGE 4: Compute V-A           (rule-based weighted sum)
  STAGE 5: Segment Song          (SSM + novelty peaks)
  STAGE 6: Per-segment V-A+Color (8-bit DRGBW per segment, modulated arousal)
  STAGE 7: Chase Timing Rules    (BPM-based 500/700/1500ms)
  STAGE 8: Build AnalyzeResult   (final orchestrator)

Source of truth: skripsi BAB 3 + script_math_model.md (v7 verified).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from engines import color_mapping as cm
from engines.audio_engine import AudioFeatures, load_audio
from engines.scene_generator import Segment
from engines.va_presets import VAPreset, apply_preset

ProgressCallback = Optional[Callable[[int, str], None]]


@dataclass
class NormalizedFeatures:
    """Min-max normalized features (STAGE 3 output)."""
    bpm: float
    rms: float
    sc: float
    mfcc1: float
    onset_rate: float
    chroma_major: float


@dataclass
class VAResult:
    """Valence & Arousal + quadrant (STAGE 4 output)."""
    valence: float
    arousal: float
    quadrant: str
    quadrant_name: str = ""


@dataclass
class HSV:
    """HSV color (math model §[4] output)."""
    h: float
    s: float
    v: float


@dataclass
class DRGBW:
    """8-bit RGBW + dimmer (math model §[5-6] output)."""
    dimmer: int
    r: int
    g: int
    b: int
    w: int


@dataclass
class AnalyzeResult:
    """Final analyze result (STAGE 8 output)."""
    filepath: str
    filename: str
    features: AudioFeatures
    normalized: NormalizedFeatures
    va: VAResult
    hsv: HSV
    drgbw: DRGBW
    segments: list[Segment] = field(default_factory=list)
    chase_timing_ms: int = 700


# Normalization ranges (math model §[2])
RANGES: dict[str, tuple[float, float]] = {
    "bpm": (60, 180),
    "rms": (0.01, 0.50),
    "sc": (500, 5000),
    "mfcc1": (-300, 100),
    "onset_rate": (0.5, 8.0),
    "chroma_major": (0.0, 1.0),
}

# Chase timing rules (math model §[8])
CHASE_TIMING_BRACKETS: tuple[tuple[float, int], ...] = (
    (120, 500),   # BPM > 120 → 500ms
    (90, 700),    # 90 ≤ BPM ≤ 120 → 700ms
    (0, 1500),    # BPM < 90 → 1500ms
)


def _norm(v: float, key: str) -> float:
    """Min-max normalize sesuai math model §[2]."""
    lo, hi = RANGES.get(key, (0.0, 1.0))
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


def normalize_features(af: AudioFeatures) -> NormalizedFeatures:
    """STAGE 3: Normalize ke [0, 1]."""
    return NormalizedFeatures(
        bpm=_norm(af.tempo, "bpm"),
        rms=_norm(af.rms_mean, "rms"),
        sc=_norm(af.sc_mean, "sc"),
        mfcc1=_norm(af.mfcc1_mean, "mfcc1"),
        onset_rate=_norm(af.onset_rate, "onset_rate"),
        chroma_major=af.chroma_major,  # already 0-1
    )


def compute_va(n: NormalizedFeatures) -> VAResult:
    """STAGE 4: V-A weighted sum. Lihat math model §[3]."""
    V, A = cm.compute_va(n.bpm, n.rms, n.onset_rate, n.chroma_major, n.sc, n.mfcc1)
    q = cm.get_quadrant(V, A)
    return VAResult(
        valence=round(V, 4),
        arousal=round(A, 4),
        quadrant=q,
        quadrant_name=cm.get_quadrant_name(q),
    )


def segment_color(
    segments: list[Segment], af: AudioFeatures,
    va_preset: Optional[VAPreset] = None,
) -> list[Segment]:
    """STAGE 6: Per-segment V-A + HSV + DRGBW (arousal modulated by RMS ratio)."""
    global_rms_norm = _norm(af.rms_mean, "rms")

    for seg in segments:
        seg_rms_norm = _norm(seg.rms, "rms")
        rms_ratio = seg_rms_norm / max(global_rms_norm, 0.01)
        modulated_bpm = min(af.tempo * rms_ratio, 180.0)
        seg_bpm_norm = _norm(modulated_bpm, "bpm")

        seg_n = NormalizedFeatures(
            bpm=seg_bpm_norm,
            rms=seg_rms_norm,
            sc=_norm(seg.sc, "sc"),
            mfcc1=_norm(af.mfcc1_mean, "mfcc1"),
            onset_rate=_norm(af.onset_rate, "onset_rate"),
            chroma_major=af.chroma_major,
        )
        seg_va = compute_va(seg_n)

        if va_preset is not None:
            H, S, V_hsv = apply_preset(va_preset, seg_va.valence, seg_va.arousal,
                                       af.chroma_peak, seg_rms_norm)
        else:
            H, S, V_hsv = cm.va_to_hsv(seg_va.valence, seg_va.arousal,
                                       af.chroma_peak, seg_rms_norm)

        drgbw = cm.hsv_to_drgbw(H, S, V_hsv)
        seg.va = seg_va.__dict__
        seg.drgbw = drgbw.__dict__

    return segments


def chase_timing(af: AudioFeatures) -> int:
    """STAGE 7: BPM-based chase timing (math model §[8])."""
    bpm = af.tempo
    for threshold, ms in CHASE_TIMING_BRACKETS:
        if bpm > threshold:
            return ms
    return 1500


def pick_pattern(arousal: float, bpm: float) -> str:
    """Pilih multi-fixture pattern (math model §[8])."""
    if arousal > 0.7:
        return "all_on"
    if bpm > 120:
        return "running"
    if arousal < 0.3:
        return "gradient"
    return "center_out"


def run(audio_path: str, progress: ProgressCallback = None,
        va_preset: Optional[VAPreset] = None) -> AnalyzeResult:
    """Run full 8-stage pipeline from audio file."""
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if progress:
        progress(5, "Loading audio…")
    y, sr = load_audio(audio_path)

    if progress:
        progress(20, "Extracting features…")
    af = extract_from_audio(y, sr)

    n = normalize_features(af)
    va = compute_va(n)

    if progress:
        progress(65, "Segmenting song…")
    segments = segment_song_from_audio(y, sr, af)

    if progress:
        progress(78, "Mapping V-A to color per segment…")
    segments = segment_color(segments, af, va_preset=va_preset)

    timing = chase_timing(af)

    if va_preset is not None:
        H, S, V_hsv = apply_preset(va_preset, va.valence, va.arousal, af.chroma_peak, n.rms)
    else:
        H, S, V_hsv = cm.va_to_hsv(va.valence, va.arousal, af.chroma_peak, n.rms)

    drgbw = cm.hsv_to_drgbw(H, S, V_hsv)

    if progress:
        progress(100, "Analysis complete")

    return AnalyzeResult(
        filepath=audio_path,
        filename=os.path.basename(audio_path),
        features=af,
        normalized=n,
        va=va,
        hsv=HSV(h=H, s=S, v=V_hsv),
        drgbw=DRGBW(dimmer=drgbw.d, r=drgbw.r, g=drgbw.g, b=drgbw.b, w=drgbw.w),
        segments=segments,
        chase_timing_ms=timing,
    )


def run_with_features(features: AudioFeatures,
                      va_preset: Optional[VAPreset] = None) -> AnalyzeResult:
    """Run pipeline from pre-computed features (for tests / programmatic use)."""
    n = normalize_features(features)
    va = compute_va(n)
    if va_preset is not None:
        H, S, V_hsv = apply_preset(va_preset, va.valence, va.arousal,
                                   features.chroma_peak, n.rms)
    else:
        H, S, V_hsv = cm.va_to_hsv(va.valence, va.arousal, features.chroma_peak, n.rms)
    drgbw = cm.hsv_to_drgbw(H, S, V_hsv)
    return AnalyzeResult(
        filepath="<features>",
        filename="<features>",
        features=features,
        normalized=n,
        va=va,
        hsv=HSV(h=H, s=S, v=V_hsv),
        drgbw=DRGBW(dimmer=drgbw.d, r=drgbw.r, g=drgbw.g, b=drgbw.b, w=drgbw.w),
        segments=[],
        chase_timing_ms=chase_timing(features),
    )


# ── Internal helpers (avoid double audio load in run) ──
def extract_from_audio(y, sr) -> AudioFeatures:
    """STAGE 2 from loaded audio (shared with segment_song)."""
    import librosa
    import numpy as np

    duration = float(librosa.get_duration(y=y, sr=sr))

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    rms = librosa.feature.rms(y=y)[0]
    rms_mean = float(np.mean(rms))

    sc = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    sc_mean = float(np.mean(sc))

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc1_mean = float(np.mean(mfcc[0]))

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    major_indices = list(cm.MAJOR_INDICES) if hasattr(cm, "MAJOR_INDICES") else [0, 2, 4, 5, 7, 9, 11]
    major_energy = float(np.sum(chroma_mean[major_indices]))
    total_energy = float(np.sum(chroma_mean))
    chroma_major = major_energy / total_energy if total_energy > 0 else 0.5
    chroma_peak = int(np.argmax(chroma_mean))

    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_rate = float(len(onset_frames) / duration) if duration > 0 else 0.0

    sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    sb_mean = float(np.mean(sb))

    return AudioFeatures(
        duration=round(duration, 2),
        tempo=round(tempo, 1),
        rms_mean=round(rms_mean, 4),
        sc_mean=round(sc_mean, 1),
        mfcc1_mean=round(mfcc1_mean, 2),
        chroma_major=round(chroma_major, 4),
        chroma_peak=chroma_peak,
        onset_rate=round(onset_rate, 2),
        beat_times=beat_times,
        rms_times=librosa.frames_to_time(np.arange(len(rms)), sr=sr).tolist(),
        rms_values=rms.tolist(),
        sc_times=librosa.frames_to_time(np.arange(len(sc)), sr=sr).tolist(),
        sc_values=sc.tolist(),
        sb_mean=round(sb_mean, 1),
        chroma_mean=chroma_mean.tolist(),
    )


def segment_song_from_audio(y, sr, af: AudioFeatures) -> list[Segment]:
    """STAGE 5 from loaded audio (SSM + novelty peaks)."""
    import librosa
    import numpy as np

    duration = af.duration
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    ssm = librosa.segment.recurrence_matrix(chroma, mode="affinity", sym=True)
    novelty = librosa.segment.novelty(ssm)

    peaks = []
    if len(novelty) > 2:
        threshold = float(np.mean(novelty)) + 0.5 * float(np.std(novelty))
        for i in range(1, len(novelty) - 1):
            if (novelty[i] > threshold and novelty[i] > novelty[i - 1]
                    and novelty[i] > novelty[i + 1]):
                peaks.append(i)

    boundary_times = [0.0] + librosa.frames_to_time(peaks, sr=sr, hop_length=512).tolist() + [duration]
    if len(boundary_times) < 4:
        n = 4
        boundary_times = [duration * i / n for i in range(n + 1)]
    elif len(boundary_times) > 10:
        novelty_at_peaks = [novelty[p] for p in peaks]
        top_indices = np.argsort(novelty_at_peaks)[-7:]
        top_peaks = sorted([peaks[i] for i in top_indices])
        boundary_times = [0.0] + librosa.frames_to_time(top_peaks, sr=sr, hop_length=512).tolist() + [duration]

    segments: list[Segment] = []
    total_segs = len(boundary_times) - 1
    global_rms_mean = float(np.mean(librosa.feature.rms(y=y)[0]))

    for i in range(total_segs):
        start = boundary_times[i]
        end = boundary_times[i + 1]
        seg_duration = end - start
        start_sample = int(start * sr)
        end_sample = min(int(end * sr), len(y))
        y_seg = y[start_sample:end_sample]
        if len(y_seg) < int(sr * 0.5):
            continue

        seg_rms = float(np.mean(librosa.feature.rms(y=y_seg)[0]))
        seg_sc = float(np.mean(librosa.feature.spectral_centroid(y=y_seg, sr=sr)[0]))
        rel_pos = (start + end) / 2 / duration if duration > 0 else 0.5

        if i == 0 and seg_duration < duration * 0.15:
            label = "intro"
        elif i == total_segs - 1 and seg_duration < duration * 0.15:
            label = "outro"
        elif seg_rms > global_rms_mean * 1.15:
            label = "chorus"
        elif 0.3 < rel_pos < 0.7 and seg_rms < global_rms_mean * 0.9:
            label = "bridge"
        else:
            label = "verse"

        segments.append(Segment(
            index=i, label=label,
            start=round(start, 2), end=round(end, 2),
            duration=round(seg_duration, 2),
            rms=round(seg_rms, 4), sc=round(seg_sc, 1),
        ))
    return segments
