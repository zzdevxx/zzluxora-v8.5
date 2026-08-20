"""
engines/audio_engine.py — audio feature extraction (pure logic, no Qt).

STAGE 1-2 of the 8-stage pipeline: load audio + extract features.
Feature set (skripsi math model §[2]):
  tempo, RMS energy, spectral centroid, MFCC1, chroma (major + peak),
  onset rate, beat times, spectral bandwidth.

Custom exceptions so UI can map to user-friendly messages.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import librosa
import numpy as np

SAMPLE_RATE = 22050
MAJOR_INDICES = (0, 2, 4, 5, 7, 9, 11)  # C, D, E, F, G, A, B


class AudioDecodeError(Exception):
    """Raised when librosa cannot decode the audio file."""


class UnsupportedFormatError(AudioDecodeError):
    """Raised when the file format is not supported."""


@dataclass
class AudioFeatures:
    """Raw audio features (STAGE 2 output)."""
    duration: float
    tempo: float
    rms_mean: float
    sc_mean: float
    mfcc1_mean: float
    chroma_major: float
    chroma_peak: int
    onset_rate: float
    beat_times: list[float] = field(default_factory=list)
    rms_times: list[float] = field(default_factory=list)
    rms_values: list[float] = field(default_factory=list)
    sc_times: list[float] = field(default_factory=list)
    sc_values: list[float] = field(default_factory=list)
    sb_mean: float = 0.0
    chroma_mean: list[float] = field(default_factory=list)


ProgressCallback = Optional[Callable[[int, str], None]]


def _report(progress: ProgressCallback, pct: int, msg: str) -> None:
    if progress:
        progress(pct, msg)


def load_audio(path: str, sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """Load audio file. Raises AudioDecodeError on failure."""
    try:
        y, sr = librosa.load(path, sr=sr, mono=True)
    except FileNotFoundError:
        raise FileNotFoundError(path)
    except Exception as exc:
        raise AudioDecodeError(f"Cannot decode audio: {exc}") from exc
    if y is None or len(y) == 0:
        raise AudioDecodeError("Audio file is empty")
    return y, sr


def extract_features(audio_path: str, sr: int = SAMPLE_RATE,
                     progress: ProgressCallback = None) -> AudioFeatures:
    """Extract all audio features. Returns AudioFeatures dataclass."""
    _report(progress, 5, "Loading audio…")
    y, sr = load_audio(audio_path, sr)
    duration = float(librosa.get_duration(y=y, sr=sr))

    _report(progress, 20, "Tracking beat…")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, "__len__"):
        tempo = float(tempo[0])
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    _report(progress, 35, "Computing RMS energy…")
    rms = librosa.feature.rms(y=y)[0]
    rms_mean = float(np.mean(rms))
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr).tolist()

    _report(progress, 50, "Computing spectral centroid…")
    sc = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    sc_mean = float(np.mean(sc))
    sc_times = librosa.frames_to_time(np.arange(len(sc)), sr=sr).tolist()

    _report(progress, 65, "Computing MFCC…")
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc1_mean = float(np.mean(mfcc[0]))

    _report(progress, 80, "Computing chroma…")
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    major_energy = float(np.sum(chroma_mean[list(MAJOR_INDICES)]))
    total_energy = float(np.sum(chroma_mean))
    chroma_major = major_energy / total_energy if total_energy > 0 else 0.5
    chroma_peak = int(np.argmax(chroma_mean))

    _report(progress, 90, "Detecting onsets…")
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_rate = float(len(onset_frames) / duration) if duration > 0 else 0.0

    sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    sb_mean = float(np.mean(sb))

    _report(progress, 100, "Done")
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
        rms_times=rms_times,
        rms_values=rms_values,
        sc_times=sc_times,
        sc_values=sc_values,
        sb_mean=round(sb_mean, 1),
        chroma_mean=chroma_mean.tolist(),
    )


# ── Normalization ──────────────────────────────────────
RANGES: dict[str, tuple[float, float]] = {
    "tempo": (60, 180),
    "rms_mean": (0.01, 0.50),
    "sc_mean": (500, 5000),
    "mfcc1_mean": (-300, 100),
    "onset_rate": (0.5, 8.0),
    "chroma_major": (0.0, 1.0),
}


def normalize(value: float, key: str) -> float:
    """Min-max normalize a value to [0, 1] using RANGES table."""
    lo, hi = RANGES.get(key, (0.0, 1.0))
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))
