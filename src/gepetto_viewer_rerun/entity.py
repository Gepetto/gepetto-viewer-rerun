import rerun as rr
from dataclasses import dataclass, field
from typing import List
import pathlib
from .scene import Scene


@dataclass
class Entity:
    """
    Each entity is defined by its name and log_name, the archetype
        and the list of the scenes in which it is drawn.

    The list of log_name makes the node hierarchy, so that when logging
    the entity, Rerun makes the intermediate group nodes.
    """

    name: str
    archetype: rr.archetypes
    scenes: List[Scene] = field(default_factory=list)
    log_name: List[str] = field(default_factory=list)

    def add_scene(self, scene: Scene):
        assert isinstance(
            scene, Scene
        ), "Entity.add_scene() parameter 'scene' must be of type 'Scene'"

        if scene not in self.scenes:
            self.scenes.append(scene)

    def add_log_name(self, name: str):
        """Add log_name"""
        if name not in self.log_name:
            self.log_name.append(name)


@dataclass
class MeshFromPath:
    path: str | pathlib.Path


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
