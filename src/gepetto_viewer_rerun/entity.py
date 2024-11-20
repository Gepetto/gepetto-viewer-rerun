import rerun as rr
from dataclasses import dataclass
from typing import Union
import pathlib


@dataclass
class Entity:
    name: str
    archetype: rr.archetypes

@dataclass
class MeshFromPath:
    path: Union[str, pathlib.Path]