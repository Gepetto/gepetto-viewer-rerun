import rerun as rr
from dataclasses import dataclass
from typing import Union, List
import pathlib
from .scene import Scene


@dataclass
class Entity:
    """
    Each entity is defined by its name, the archetype and
        the list of the scenes in which it is drawn.
    """

    name: str
    archetype: rr.archetypes
    scenes: List[Scene] = None

    def __post_init__(self):
        if self.scenes is None:
            self.scenes = []
        else:
            self.scenes = [self.scenes]

    def addScene(self, scene: Scene):
        assert isinstance(
            scene, Scene
        ), "Entity.addScene() parameter 'scene' must be of type 'Scene'"

        self.scenes.append(scene)


@dataclass
class MeshFromPath:
    path: Union[str, pathlib.Path]
