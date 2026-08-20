"""
engines/program.py — Program model (multi-track cue sequencer, pure logic, no Qt).

A Program is a whole-song timeline: each step is a color state for the room.
Distinct from Chase (multi-fixture sequence).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from core import paths


@dataclass
class Cue:
    index: int
    start: float          # seconds
    duration: float       # seconds
    drgbw: dict           # {r,g,b,w,dimmer} 0-255
    color: tuple = (0, 0, 0)  # RGB preview color
    label: str = ""

    def end(self) -> float:
        return self.start + self.duration

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": self.start,
            "duration": self.duration,
            "drgbw": dict(self.drgbw),
            "color": list(self.color),
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Cue":
        return cls(
            index=d.get("index", 0),
            start=float(d.get("start", 0)),
            duration=float(d.get("duration", 1.0)),
            drgbw=dict(d.get("drgbw", {"r": 0, "g": 0, "b": 0, "w": 0, "dimmer": 0})),
            color=tuple(d.get("color", [0, 0, 0])),
            label=d.get("label", ""),
        )


@dataclass
class Track:
    name: str
    cues: list[Cue] = field(default_factory=list)

    def total_duration(self) -> float:
        if not self.cues:
            return 0.0
        return max(c.end() for c in self.cues)

    def add_cue(self, start: float, duration: float, drgbw: dict,
                color: tuple = (0, 0, 0), label: str = "") -> Cue:
        cue = Cue(
            index=len(self.cues), start=start, duration=duration,
            drgbw=dict(drgbw), color=color,
            label=label or f"Cue {len(self.cues) + 1}",
        )
        self.cues.append(cue)
        return cue

    def to_dict(self) -> dict:
        return {"name": self.name, "cues": [c.to_dict() for c in self.cues]}

    @classmethod
    def from_dict(cls, d: dict) -> "Track":
        return cls(name=d.get("name", "Track"),
                   cues=[Cue.from_dict(c) for c in d.get("cues", [])])


@dataclass
class Program:
    name: str
    tracks: list[Track] = field(default_factory=list)
    created: str = ""
    modified: str = ""

    def add_track(self, name: str = "Track") -> Track:
        track = Track(name=name)
        self.tracks.append(track)
        self._touch()
        return track

    def total_duration(self) -> float:
        if not self.tracks:
            return 0.0
        return max(t.total_duration() for t in self.tracks)

    def _touch(self) -> None:
        self.modified = time.strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created": self.created,
            "modified": self.modified,
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Program":
        return cls(
            name=d.get("name", "Untitled"),
            tracks=[Track.from_dict(t) for t in d.get("tracks", [])],
            created=d.get("created", ""),
            modified=d.get("modified", ""),
        )


# ── Storage ────────────────────────────────────────────
def _programs_dir() -> str:
    return str(paths.get_data_dir("programs"))


def list_programs() -> list[str]:
    d = _programs_dir()
    if not os.path.isdir(d):
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".json"))


def save_program(program: Program) -> None:
    if not program.created:
        program.created = time.strftime("%Y-%m-%dT%H:%M:%S")
    program._touch()
    path = os.path.join(_programs_dir(), f"{program.name}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(program.to_dict(), fh, indent=2)


def load_program(name: str) -> Program | None:
    path = os.path.join(_programs_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return Program.from_dict(json.load(fh))


def delete_program(name: str) -> bool:
    path = os.path.join(_programs_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True
