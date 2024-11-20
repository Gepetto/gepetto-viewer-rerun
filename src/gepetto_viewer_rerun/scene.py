import rerun as rr
from dataclasses import dataclass


@dataclass
class Scene:
    name: str
    rec: rr.RecordingStream = None
    
    def setRec(self, rec: rr.RecordingStream):
        self.rec = rec