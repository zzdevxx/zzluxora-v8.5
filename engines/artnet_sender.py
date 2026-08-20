"""
engines/artnet_sender.py — Art-Net output (entity: ArtNetController).

Wraps stupidArtnet for DMX over Art-Net UDP. Only module in engines/ with
external IO — everything else is pure logic. Import guard so the app boots
even when stupidArtnet is missing (HAS_ARTNET=False, connect returns error).
"""
from __future__ import annotations

import socket
import struct
import threading
import time

try:
    from stupidArtnet import StupidArtnet
    HAS_ARTNET = True
except ImportError:  # pragma: no cover
    HAS_ARTNET = False

ARTNET_PORT = 6454
DMX_SIZE = 512


class ArtNetController:
    """Controls Art-Net output to a target IP (QLC+ virtual adapter or ESP32)."""

    def __init__(self) -> None:
        self.artnet = None
        self.target_ip = "127.0.0.1"
        self.universe = 0
        self.fps = 30
        self.is_running = False
        self.is_playing = False
        self.play_thread: threading.Thread | None = None
        self.current_dmx = [0] * DMX_SIZE
        self.chase_frames: list[dict] = []
        self.chase_index = 0
        self.stop_event = threading.Event()
        self.frames_sent = 0
        self.last_frame_time = 0.0
        self._keepalive_thread: threading.Thread | None = None
        self._keepalive_stop = threading.Event()
        self.last_error: str | None = None
        self._last_err_log = 0.0

    # ── Idle keepalive ────────────────────────────────
    # ESP32 firmware mem-blackout semua channel jika tidak ada paket
    # Art-Net selama >10 detik (artnet_dmx_final.ino L283). Jadi saat idle
    # kita harus tetap mengirim frame terakhir secara berkala.
    def _start_keepalive(self) -> None:
        self._keepalive_stop.clear()
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            return
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop, daemon=True
        )
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        while not self._keepalive_stop.is_set():
            if self.is_running and not self.is_playing:
                # Kirim ulang frame terakhir setiap 2.5s (jauh di bawah 10s)
                # agar module ESP32 tidak masuk blackout.
                if self.current_dmx:
                    self._send(self.current_dmx)
            self._keepalive_stop.wait(2.5)

    def _stop_keepalive(self) -> None:
        self._keepalive_stop.set()
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            self._keepalive_thread.join(timeout=2)
        self._keepalive_thread = None

    # ── Connection ─────────────────────────────────────
    def connect(self, target_ip: str = "127.0.0.1", universe: int = 0,
                fps: int = 30) -> dict:
        if not HAS_ARTNET:
            return {"ok": False, "error": "stupidArtnet not installed"}
        self.target_ip = target_ip
        self.universe = universe
        self.fps = fps
        try:
            if self.artnet:
                self.artnet.stop()
            self.artnet = StupidArtnet(target_ip, universe, DMX_SIZE, fps, True, True)
            self.artnet.start()
            self.is_running = True
            self._start_keepalive()
            return {"ok": True, "ip": target_ip, "universe": universe}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def disconnect(self) -> None:
        self.stop_chase()
        self._stop_keepalive()
        if self.artnet:
            self.blackout()
            time.sleep(0.1)
            self.artnet.stop()
            self.artnet = None
        self.is_running = False

    # ── Frames ─────────────────────────────────────────
    def _send(self, dmx_data: list[int]) -> bool:
        if not self.artnet or not self.is_running:
            return False
        try:
            packet = bytearray(dmx_data[:DMX_SIZE])
            self.artnet.set(packet)
            self.frames_sent += 1
            self.last_frame_time = time.time()
            return True
        except Exception as exc:
            self.last_error = str(exc)
            now = time.time()
            if now - self._last_err_log > 1.0:
                print(f"[artnet] send failed: {exc}")
                self._last_err_log = now
            return False

    def send_frame(self, dmx_data: list[int]) -> bool:
        """Kirim frame DMX 512 channel."""
        ok = self._send(dmx_data)
        if ok:
            self.current_dmx = list(dmx_data[:DMX_SIZE])
        return ok

    def _render_scene_to_dmx(self, drgbw: dict, address_map: dict) -> list[int]:
        """Render scene DRGBW → DMX 512 (pure, no IO).

        address_map: {dmx_address: {"fixture_name", "start_address"}} dari
        FixtureManager; setiap fixture dipetakan channel 0=Dimmer, 1=R, 2=G,
        3=B, 4=W (PAR 5ch DRGBW). Di luar 1-512 diabaikan.
        """
        dmx = [0] * DMX_SIZE
        for addr, info in address_map.items():
            try:
                start = int(info["start_address"])
                d = int(drgbw.get("d", drgbw.get("dimmer", 0)))
                r = int(drgbw.get("r", 0))
                g = int(drgbw.get("g", 0))
                b = int(drgbw.get("b", 0))
                w = int(drgbw.get("w", 0))
                if start < 1 or start > 512:
                    continue
                dmx[start - 1] = d
                if start < 512: dmx[start] = r
                if start < 511: dmx[start + 1] = g
                if start < 510: dmx[start + 2] = b
                if start < 509: dmx[start + 3] = w
            except (KeyError, TypeError, ValueError):
                continue
        return dmx

    def send_frame_from_scene(self, drgbw: dict, address_map: dict) -> bool:
        """Render scene DRGBW ke DMX via address_map → kirim frame."""
        dmx = self._render_scene_to_dmx(drgbw, address_map)
        return self.send_frame(dmx)

    def blackout(self) -> None:
        self.send_frame([0] * DMX_SIZE)

    def reset_counter(self) -> None:
        self.frames_sent = 0

    def emergency_stop(self) -> None:
        """Stop chase + blackout semua channel (shortcut E)."""
        self.stop_chase()
        self.blackout()

    # ── Chase playback ─────────────────────────────────
    def play_chase(self, frames: list[dict]) -> None:
        """Play chase in background thread.

        frames: list of {"dmx": [512 ints], "hold_ms": int, "fade_ms": int}
        """
        self.stop_chase()
        self.chase_frames = frames
        self.chase_index = 0
        self.stop_event.clear()
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._chase_loop, daemon=True)
        self.play_thread.start()

    def _chase_loop(self) -> None:
        while not self.stop_event.is_set() and self.chase_frames:
            frame = self.chase_frames[self.chase_index]
            dmx = frame["dmx"]
            hold_ms = frame.get("hold_ms", 1000)
            fade_ms = frame.get("fade_ms", 500)

            start_dmx = list(self.current_dmx)
            target_dmx = list(dmx)
            fade_steps = max(1, fade_ms // 33)

            for step in range(fade_steps):
                if self.stop_event.is_set():
                    return
                t = (step + 1) / fade_steps
                interp = [
                    int(start_dmx[i] + (target_dmx[i] - start_dmx[i]) * t)
                    for i in range(DMX_SIZE)
                ]
                self.send_frame(interp)
                time.sleep(0.033)

            self.send_frame(target_dmx)
            hold_until = time.monotonic() + hold_ms / 1000
            while time.monotonic() < hold_until and not self.stop_event.is_set():
                time.sleep(0.05)

            self.chase_index = (self.chase_index + 1) % len(self.chase_frames)
        self.is_playing = False

    def stop_chase(self) -> None:
        self.stop_event.set()
        self.is_playing = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=2)
        self.play_thread = None

    # ── Status & scan ──────────────────────────────────
    def get_status(self) -> dict:
        return {
            "connected": self.is_running,
            "playing": self.is_playing,
            "target_ip": self.target_ip,
            "universe": self.universe,
            "fps": self.fps,
            "frames_sent": self.frames_sent,
            "chase_index": self.chase_index,
            "chase_total": len(self.chase_frames),
            "last_frame_age": round(time.time() - self.last_frame_time, 1) if self.last_frame_time else None,
            "last_error": self.last_error,
        }

    def scan(self, timeout_s: float = 3.0) -> list[dict]:
        """ArtPoll broadcast scan → list of {ip, name} nodes."""
        sock: socket.socket | None = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.3)
            poll = struct.pack("<8sHBB", b"Art-Net\x00", 0x2000, 0, 0) + b"\x00" * 6
            try:
                sock.sendto(poll, ("<broadcast>", ARTNET_PORT))
            except OSError:
                return []
            nodes: dict[str, dict] = {}
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                try:
                    data, _addr = sock.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if len(data) < 18:
                    continue
                if data[:8] != b"Art-Net\x00" or data[8:10] != b"\x00\x21":
                    continue
                ip = f"{data[10]}.{data[11]}.{data[12]}.{data[13]}"
                try:
                    name = data[18:34].split(b"\x00", 1)[0].decode("ascii", "ignore") or ip
                except UnicodeDecodeError:
                    name = ip
                if ip not in nodes:
                    nodes[ip] = {"ip": ip, "name": name}
            return list(nodes.values())
        except Exception:
            return []
        finally:
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
