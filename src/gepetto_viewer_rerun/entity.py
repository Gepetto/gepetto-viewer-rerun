import rerun as rr
from dataclasses import dataclass, field
from typing import Union, List
import pathlib
from .scene import Scene
from .archetype import Archetype


@dataclass
class Entity:
    """
    Each entity is defined by its name, the archetype and
        the list of the scenes in which it is drawn.
    """

    name: str
    type: Archetype
    archetype: rr.archetypes
    scenes: List[Scene] | None = None

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


@dataclass
class Group:
    name: str
    value: Scene | Entity | None = None
    children: List["Group"] = field(default_factory=list)

    def add_child(self, child: "Group"):
        assert isinstance(
            child, Group
        ), "Group.add_child(): Parameter 'child' must of type Group"

        self.children.append(child)
