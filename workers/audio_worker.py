"""
workers/audio_worker.py — QThread wrapper untuk audio analysis.

Memisahkan CPU-heavy analysis (librosa) dari UI thread. Emits:
  progress(int), finished(dict result), failed(str error)
"""
from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal

from engines.analyze_pipeline import run


class AudioWorker(QThread):
    progress = Signal(int)
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, audio_path: str, parent=None) -> None:
        super().__init__(parent)
        self.audio_path = audio_path

    def run(self) -> None:
        try:
            result = run(
                self.audio_path,
                progress=lambda pct: self.progress.emit(int(pct)),
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(f"{exc}\n{traceback.format_exc()}")
