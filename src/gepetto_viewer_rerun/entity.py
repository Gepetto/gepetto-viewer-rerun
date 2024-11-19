import rerun as rr
from dataclasses import dataclass


@dataclass
class Entity:
    def __init__(self, name: str, archetype: rr.archetypes):
        self.name = name
        self.archetype = archetype

@dataclass
class MeshFromPath:
    def __init__(self, path: str):
        self.path = path