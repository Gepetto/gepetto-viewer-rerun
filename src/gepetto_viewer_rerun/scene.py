import rerun as rr
from dataclasses import dataclass
from typing import List


@dataclass
class Scene:
    """Scenes and their associated recording"""

    name: str
    rec: rr.RecordingStream = None

    def set_rec(self, rec: rr.RecordingStream):
        self.rec = rec


@dataclass
class Window:
    """Windows and their associated scenes"""

    name: str
    scenes: List[Scene] | None = None
