import rerun as rr
from dataclasses import dataclass, field
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
    log_name: str = ""
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

        if scene not in self.scenes:
            self.scenes.append(scene)

    def set_log_name(self, name: str):
        """Set log_name"""
        self.log_name = name


@dataclass
class MeshFromPath:
    path: Union[str, pathlib.Path]


@dataclass
class Group:
    name: str
    scenes: List[Scene] = field(default_factory=list)

    def add_scene(self, scene: Scene):
        """Add `scene` to self.scenes."""
        assert isinstance(
            scene, Scene
        ), "Group.add_scene(): Parameter 'scene' must be a `Scene`"

        if scene not in self.scenes:
            self.scenes.append(scene)
