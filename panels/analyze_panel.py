"""
panels/analyze_panel.py — Analyze: audio upload → pipeline → scenes → save.

Alur:
  1. Pilih file audio (mp3/wav/ogg/flac, max 100MB)
  2. AudioWorker QThread jalankan engines.analyze_pipeline.run
  3. Tampilkan hasil (V, A, quadrant, HSV, chase timing, scene count)
  4. Simpan ke ctx.songs (SongStore) + generate chase otomatis
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout,
)

from engines.chase import chase_from_song_scenes, save_chase
from widgets.panel_base import BasePanel, Card
from widgets.toast import show_toast
from workers.audio_worker import AudioWorker

ALLOWED_EXT = (".mp3", ".wav", ".ogg", ".flac")
MAX_SIZE = 100 * 1024 * 1024  # 100 MB


class AnalyzePanel(BasePanel):
    def __init__(self, ctx) -> None:
        super().__init__(ctx, "Analyze", "Analisis audio → scene generator")
        self.worker: AudioWorker | None = None
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # ── Upload card ───────────────────────────────
        card = Card()
        lay = card.body()
        lay.addWidget(self._label("Audio Source", "cardTitle"))

        row = QHBoxLayout()
        self.file_lbl = QLabel("Belum ada file dipilih")
        self.file_lbl.setObjectName("hintLabel")
        row.addWidget(self.file_lbl, 1)
        self.browse_btn = QPushButton("Pilih Audio…")
        self.browse_btn.clicked.connect(self._on_browse)
        row.addWidget(self.browse_btn)
        lay.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        lay.addWidget(self.progress)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setObjectName("primaryButton")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self._on_analyze)
        lay.addWidget(self.analyze_btn)
        self.add_widget(card)

        # ── Result card ───────────────────────────────
        self.result_card = Card()
        rlay = self.result_card.body()
        rlay.addWidget(self._label("Hasil Analisis", "cardTitle"))
        self.result_lbl = QLabel("—")
        self.result_lbl.setWordWrap(True)
        self.result_lbl.setObjectName("value")
        rlay.addWidget(self.result_lbl)
        self.save_btn = QPushButton("Simpan ke Songs + buat Chase")
        self.save_btn.setObjectName("successButton")
        self.save_btn.setVisible(False)
        self.save_btn.clicked.connect(self._on_save)
        rlay.addWidget(self.save_btn)
        self.add_widget(self.result_card)

        self.add_stretch()

    # ── Handlers ───────────────────────────────────────
    def _on_browse(self) -> None:
        start = self.ctx.cfg.last_audio_dir or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Audio", start,
            "Audio Files (*.mp3 *.wav *.ogg *.flac)")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in ALLOWED_EXT:
            show_toast(self, "Format tidak didukung (mp3/wav/ogg/flac)", kind="err")
            return
        try:
            if os.path.getsize(path) > MAX_SIZE:
                show_toast(self, "File terlalu besar (max 100MB)", kind="err")
                return
        except OSError:
            show_toast(self, "File tidak dapat diakses", kind="err")
            return
        self.ctx.cfg.last_audio_dir = os.path.dirname(path)
        self._audio_path = path
        self.file_lbl.setText(os.path.basename(path))
        self.analyze_btn.setEnabled(True)

    def _on_analyze(self) -> None:
        if not getattr(self, "_audio_path", None):
            return
        self.analyze_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.result_lbl.setText("Menganalisis…")
        self.save_btn.setVisible(False)

        self.worker = AudioWorker(self._audio_path, self)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_done(self, result: dict) -> None:
        self.progress.setValue(100)
        self.analyze_btn.setEnabled(True)
        self._last_result = result

        va = result.get("va", {})
        hsv = result.get("hsv", {})
        scenes = result.get("scenes", [])
        text = (
            f"File: {os.path.basename(result.get('audio_path', '?'))}\n"
            f"BPM: {result.get('bpm', '?')}  ·  "
            f"Arousal: {va.get('arousal', 0):.3f}  ·  "
            f"Valence: {va.get('valence', 0):.3f}\n"
            f"Quadrant: {va.get('quadrant', '?')} ({va.get('quadrant_name', '?')})\n"
            f"HSV: H={hsv.get('h', 0):.1f}° S={hsv.get('s', 0):.3f} "
            f"V={hsv.get('v', 0):.3f}\n"
            f"Chase timing: {result.get('chase_timing_ms', 0)}ms  ·  "
            f"Scenes: {len(scenes)}"
        )
        self.result_lbl.setText(text)
        self.save_btn.setVisible(True)
        show_toast(self, "Analisis selesai", kind="ok")

    def _on_failed(self, err: str) -> None:
        self.progress.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.result_lbl.setText(f"Gagal: {err.splitlines()[0] if err else 'unknown'}")
        show_toast(self, "Analisis gagal", kind="err")

    def _on_save(self) -> None:
        result = getattr(self, "_last_result", None)
        if not result:
            return
        # Simpan ke song store
        song = {
            "filepath": result.get("audio_path", ""),
            "filename": os.path.basename(result.get("audio_path", "")),
            "features": result.get("features", {}),
            "segments": result.get("segments", []),
            "scenes": result.get("scenes", []),
            "global_color": {
                "hsv": result.get("hsv", {}),
                "drgbw": result.get("drgbw", {}),
            },
            "va": result.get("va", {}),
        }
        song_id = self.ctx.songs.add(song)

        # Auto-generate chase
        chase = chase_from_song_scenes(
            song_id, result, chase_name=f"{song['filename']} (chase)")
        save_chase(chase)
        # Load ke artnet untuk playback header
        self.ctx.artnet.chase_frames = self._scenes_to_frames(result.get("scenes", []))

        self.save_btn.setVisible(False)
        self.refresh()
        show_toast(self, f"Song + chase disimpan ({song['filename']})", kind="ok")

    @staticmethod
    def _scenes_to_frames(scenes: list) -> list[dict]:
        """Convert scenes → chase frames {dmx, hold_ms, fade_ms}."""
        frames = []
        for sc in scenes:
            dmx = [0] * 512
            color = sc.get("dmx", {})
            # Isi channel 1-5 (PAR pertama) dengan warna scene
            dmx[0] = int(color.get("d", 0))
            dmx[1] = int(color.get("r", 0))
            dmx[2] = int(color.get("g", 0))
            dmx[3] = int(color.get("b", 0))
            dmx[4] = int(color.get("w", 0))
            start = float(sc.get("start", 0))
            end = float(sc.get("end", start + 1))
            hold = int(max(0.05, end - start) * 1000)
            frames.append({"dmx": dmx, "hold_ms": hold, "fade_ms": 500})
        return frames

    # ── Refresh ────────────────────────────────────────
    def refresh(self) -> None:
        # Tampilkan jumlah song tersimpan
        n = len(self.ctx.songs)
        if n:
            self.result_lbl.setText(f"{n} song tersimpan di library")
        self.progress.setVisible(False)

    @staticmethod
    def _label(text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l
