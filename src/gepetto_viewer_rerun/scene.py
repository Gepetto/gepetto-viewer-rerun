import rerun as rr
from dataclasses import dataclass
from typing import List


@dataclass
class Scene:
    name: str
    rec: rr.RecordingStream = None

    def set_rec(self, rec: rr.RecordingStream):
        self.rec = rec


@dataclass
class Window:
    name: str
    scenes: List[Scene] | None = None
