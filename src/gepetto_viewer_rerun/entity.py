import rerun as rr
from dataclasses import dataclass


@dataclass
class Entity:
    name: str
    archetype: rr.archetypes

@dataclass
class MeshFromPath:
    def __init__(self, path: str):
        self.path = path