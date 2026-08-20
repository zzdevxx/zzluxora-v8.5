"""
engines/scene_generator.py — segment → Scene generation (pure logic, no Qt).

STAGE 5-6 of the 8-stage pipeline:
  - segment_song: SSM + novelty peak detection (librosa)
  - generate_scenes: per-segment V-A → DRGBW → Scene objects

NOTE (skripsi decision): changes are driven by beat/onset strength, NOT by
automatic verse/chorus/bridge segmentation of the song structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import librosa
import numpy as np

from engines import color_mapping as cm
from engines.va_presets import VAPreset, apply_preset


@dataclass
class Segment:
    """Song segment (STAGE 5 output)."""
    index: int
    label: str
    start: float
    end: float
    duration: float
    rms: float = 0.0
    sc: float = 0.0
    va: dict = field(default_factory=dict)
    drgbw: dict = field(default_factory=dict)


@dataclass
class Scene:
    """One lighting scene (STAGE 6 output)."""
    index: int
    start: float
    end: float
    type: str = "auto"
    label: str = ""
    dmx: dict = field(default_factory=dict)
    intensity: int = 200
    pattern: str = "all_on"


def segment_song(audio_path: str, sr: int = 22050) -> list[Segment]:
    """Segment song using SSM + novelty heuristic. Returns list of Segment."""
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    ssm = librosa.segment.recurrence_matrix(chroma, mode="affinity", sym=True)
    novelty = librosa.segment.novelty(ssm)

    peaks = []
    threshold = float(np.mean(novelty) + 0.5 * np.std(novelty))
    for i in range(1, len(novelty) - 1):
        if novelty[i] > threshold and novelty[i] > novelty[i - 1] and novelty[i] > novelty[i + 1]:
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

    overall_rms = float(np.mean(librosa.feature.rms(y=y)[0]))
    segments: list[Segment] = []
    total_segs = len(boundary_times) - 1
    for i in range(total_segs):
        start = boundary_times[i]
        end = boundary_times[i + 1]
        seg_duration = end - start
        if seg_duration < 0.5:
            continue

        start_sample = int(start * sr)
        end_sample = min(int(end * sr), len(y))
        y_seg = y[start_sample:end_sample]
        if len(y_seg) < sr * 0.5:
            continue

        seg_rms = float(np.mean(librosa.feature.rms(y=y_seg)[0]))
        seg_sc = float(np.mean(librosa.feature.spectral_centroid(y=y_seg, sr=sr)[0]))

        rel_pos = (start + end) / 2 / duration if duration > 0 else 0.5
        if i == 0 and seg_duration < duration * 0.15:
            label = "intro"
        elif i == total_segs - 1 and seg_duration < duration * 0.15:
            label = "outro"
        elif seg_rms > overall_rms * 1.15:
            label = "chorus"
        elif 0.3 < rel_pos < 0.7 and seg_rms < overall_rms * 0.9:
            label = "bridge"
        else:
            label = "verse"

        segments.append(Segment(
            index=i,
            label=label,
            start=round(start, 2),
            end=round(end, 2),
            duration=round(seg_duration, 2),
            rms=round(seg_rms, 4),
            sc=round(seg_sc, 1),
        ))
    return segments


def _segment_va(seg: Segment, sr: int = 22050, y: np.ndarray | None = None) -> tuple[float, float]:
    """Compute V-A for a segment from its RMS/SC (caller provides sr + optional audio)."""
    # Derive normalized features from segment stats using standard RANGES
    from engines.audio_engine import normalize
    bpm_n = 0.5   # segment-level tempo unknown → neutral
    rms_n = normalize(seg.rms, "rms_mean")
    sc_n = normalize(seg.sc, "sc_mean")
    onset_n = 0.5
    chroma_n = 0.5
    mfcc1_n = 0.5
    return cm.compute_va(bpm_n, rms_n, onset_n, chroma_n, sc_n, mfcc1_n)


def generate_scenes(segments: list[Segment], preset: VAPreset) -> list[Scene]:
    """Generate Scene objects from segments. Fallback: 1 default scene."""
    scenes: list[Scene] = []
    if not segments:
        scenes.append(Scene(
            index=0, start=0.0, end=1.0, label="default",
            dmx={"d": 200, "r": 255, "g": 255, "b": 255, "w": 0},
            intensity=200,
        ))
        return scenes

    for seg in segments:
        V, A = _segment_va(seg)
        H, S, V_hsv = apply_preset(preset, V, A)
        drgbw = cm.hsv_to_drgbw(H, S, V_hsv)
        scenes.append(Scene(
            index=seg.index,
            start=seg.start,
            end=seg.end,
            type="auto",
            label=seg.label,
            dmx=drgbw.__dict__,
            intensity=drgbw.d,
            pattern="all_on",
        ))
    return scenes
