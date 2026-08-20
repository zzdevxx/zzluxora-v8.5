"""
engines/realtime.py — RealtimePlayer (pure logic, NO Qt): playback audio +
scene sync. Menggunakan soundfile untuk decode & Pyaudio/SoundDevice jika ada.

Mode:
  - virtual: no audio device → hanya timeline (chase frames pakai BPM)
  - device : play audio real (jika sounddevice terpasang)

Updates via callback: on_status(dict) & on_scene(dict, index)
"""
from __future__ import annotations

import threading
import time

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:  # pragma: no cover
    HAS_SOUNDDEVICE = False


class RealtimePlayer:
    def __init__(self) -> None:
        self.playing = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.scenes: list[dict] = []
        self.on_status = None
        self.on_scene = None

    # ── API ────────────────────────────────────────────
    def load_scenes(self, scenes: list[dict]) -> None:
        self.scenes = list(scenes)

    def play(self, sender) -> None:
        """Start playback. sender: callable(dmx[512]) untuk kirim ke Art-Net."""
        self.stop()
        self._stop.clear()
        self.playing = True
        self._thread = threading.Thread(
            target=self._loop, args=(sender,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.playing = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def _loop(self, sender) -> None:
        t0 = time.time()
        idx = 0
        total = max([float(s.get("end", float(s.get("start", 0)) + 1))
                     for s in self.scenes] or [0])
        while not self._stop.is_set() and time.time() - t0 < total:
            now = time.time() - t0
            # Kirim scene jika waktunya tiba
            if idx < len(self.scenes):
                scene = self.scenes[idx]
                start = float(scene.get("start", idx))
                if now >= start:
                    color = scene.get("dmx", {})
                    dmx = [0] * 512
                    dmx[0] = int(color.get("d", 0))
                    dmx[1] = int(color.get("r", 0))
                    dmx[2] = int(color.get("g", 0))
                    dmx[3] = int(color.get("b", 0))
                    dmx[4] = int(color.get("w", 0))
                    try:
                        sender(dmx)
                    except Exception:
                        pass
                    if self.on_scene:
                        self.on_scene(scene, idx)
                    idx += 1

            # Keepalive supaya ESP32 tidak blackout (10s timeout)
            if self.on_status:
                self.on_status({"scene_index": idx, "time": now})
            time.sleep(0.05)

        self.playing = False
