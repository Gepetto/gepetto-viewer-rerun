import rerun as rr
from dataclasses import dataclass


@dataclass
class Scene:
    name: str
    rec: rr.RecordingStream = None

    def set_rec(self, rec: rr.RecordingStream):
        """Set self.rec."""
        self.rec = rec
