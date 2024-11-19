import rerun as rr
from dataclasses import dataclass


@dataclass
class Scene:
    def __init__(self, name: str):
        self.name = name
        self.rec = None
    
    def setRec(self, rec: rr.RecordingStream):
        self.rec = rec