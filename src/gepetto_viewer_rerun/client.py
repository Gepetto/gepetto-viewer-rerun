import logging
from enum import Enum
from math import tau
from typing import List, Union, Callable

import numpy as np
import rerun as rr
import rerun.blueprint as rrb

from .entity import Entity, Group
from .scene import Scene

logger = logging.getLogger(__name__)


class Archetype(Enum):
    ARROWS3D = 0
    BOXES3D = 1
    CAPSULES3D = 2
    LINESTRIPS3D = 3
    MESH3D = 4
    MESH_FROM_PATH = 5
    POINTS3D = 6


class Client:
    def __init__(self):
        self.gui = Gui()

    def __repr__(self):
        return f"Client({self.gui})"


class Gui:
    def __init__(self):
        """
        scene_list : List of `Scene` class (name and associated recording)
        window_list : List of all window names
        entity_list : List containing every Rerun archetypes,
                    each archetypes contain a list of `Entity` class.
                    Use `Enum Archetype` to get indices.
        """

        self.scene_list = []
        self.window_list = []
        self.entity_list = []
        self.group_list = []

    def __repr__(self):
        return (
            f"Gui(window_list={self.window_list}\n"
            f"scene_list (size: {len(self.scene_list)}) = {self.scene_list}\n"
            f"entity_list (size: {len(self.entity_list)}) = {self.entity_list})\n"
            f"group_list (size: {len(self.group_list)}) = {self.group_list})"
        )

    def createWindow(self, name: str) -> str:
        assert isinstance(name, str), "Parameter 'name' must be a string"

        self.window_list.append(name)
        msg = (
            "createWindow() does not create any window, "
            "Rerun create both window and scene at the same time. "
            "Window will be created after calling addSceneToWindow()."
        )
        logger.info(msg)
        return name

    def createScene(self, sceneName: str):
        assert isinstance(sceneName, str), "Parameter 'sceneName' must be a string"

        self.scene_list.append(Scene(sceneName))
        msg = (
            "createScene() does not create any scene yet, "
            "Rerun create both window and scene at the same time. "
            "Window will be created after calling addSceneToWindow()."
        )
        logger.info(msg)

    def _get_scene_index(self, sceneName: str) -> int:
        for index, scene in enumerate(self.scene_list):
            if scene.name == sceneName:
                return index
        return -1

    def addSceneToWindow(self, sceneName: str, wid: str) -> bool:
        assert all(
            isinstance(name, str) for name in [sceneName, wid]
        ), "Parameters 'sceneName' and 'wid' must be strings"

        index = self._get_scene_index(sceneName)
        if index == -1:
            logger.error(f"addSceneToWindow(): Unknown sceneName '{sceneName}'.")
            return False
        elif wid not in self.window_list:
            logger.error(f"addSceneToWindow(): Unknown windowName '{wid}'.")
            return False

        rec = rr.new_recording(application_id=wid, recording_id=sceneName, spawn=True)
        self.scene_list[index].set_rec(rec)
        return True

    def _parse_entity(
        self, archetypeName: str, archetype: rr.archetypes, archetypeType: Archetype
    ):
        """
        Parse archetype name and log (or not) archetype :
            - if there is a scene specified in archetypeName :  <scene>/name
                it will log directly the archetype into the scene
            - if there is a '/' : <not a scene>/name
                it will need addToGroup() to be log in a scene
                every '/' will interpreted as a tree
            - if there is no '/', archetype will require addToGroup() to be logged
        """
        assert archetype is not None, "_parse_entity(): 'entity' must not be None"
        assert isinstance(
            archetypeType, Archetype
        ), "_parse_entity(): 'archetypeType' must be of type `enum Archetype`"

        char_index = archetypeName.find("/")
        # If archetypeName contains '/' then search for the scene in self.scene_list
        if char_index != -1 and char_index != len(archetypeName) - 1:
            scene_name = archetypeName[:char_index]
            scene_index = self._get_scene_index(scene_name)

            if scene_index != -1:
                entity_name = archetypeName[char_index + 1 :]
                entity = Entity(entity_name, archetype, self.scene_list[scene_index])
                self.entity_list.append(entity)

                if archetypeType == Archetype.MESH_FROM_PATH:
                    # There is a bug with `log_file_from_path` and recordings.
                    # That's why we call `rec.to_native()`.
                    # 19/11/2024 - Issue : https://github.com/rerun-io/rerun/issues/8167
                    rr.log_file_from_path(
                        file_path=entity.archetype.path,
                        recording=self.scene_list[scene_index].rec.to_native(),
                    )
                else:
                    entity.add_log_name(entity_name)
                    rr.log(
                        entity_name,
                        entity.archetype,
                        recording=self.scene_list[scene_index].rec,
                    )
                msg = (
                    f"_parse_entity(): Creates entity {archetypeName} of type {archetypeType.name}, "
                    f"and logs it directly to '{self.scene_list[scene_index].name}' scene."
                )
                logger.info(msg)
                return
        # Put entity to entity_list, wait for addToGroup() to be logged
        entity = Entity(archetypeName, archetype)
        self.entity_list.append(entity)
        logger.info(f"_parseEntity(): Creating entity '{archetypeName}'.")

    def _get_entity(self, entityName: str) -> Entity | None:
        for entity in self.entity_list:
            if entity.name == entityName:
                return entity
        return None

    def _is_entity_in_scene(self, entity: Entity, scene: Scene) -> bool:
        if entity and entity.scenes:
            return scene in entity.scenes
        return False

    def addFloor(self, floorName: str) -> bool:
        assert isinstance(floorName, str), "Parameter 'floorName' must be a string"

        floor = rr.Boxes3D(
            sizes=[[200, 200, 0.5]],
            colors=[(125, 125, 125)],
            fill_mode="Solid",
        )
        self._parse_entity(floorName, floor, Archetype.BOXES3D)
        return True

    def addBox(
        self,
        boxName: str,
        boxSize1: List[Union[int, float]],
        boxSize2: List[Union[int, float]],
        boxSize3: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(boxName, str), "Parameter 'boxName' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [boxSize1, boxSize2, boxSize3]
        ), "Parameters 'boxSize' must be a numbers"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        box = rr.Boxes3D(
            sizes=[[boxSize1, boxSize2, boxSize3]],
            colors=[RGBAcolor],
            fill_mode="Solid",
            labels=[boxName],
        )
        self._parse_entity(boxName, box, Archetype.BOXES3D)
        return True

    def addArrow(
        self,
        name: str,
        radius: Union[int, float],
        length: Union[int, float],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(name, str), "Parameter 'name' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, length]
        ), "Parameters 'radius' and 'length' must be a numbers"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        angle = np.arange(start=0, stop=tau, step=tau)
        arrow = rr.Arrows3D(
            radii=[[radius]],
            vectors=np.column_stack(
                [np.sin(angle) * length, np.zeros(1), np.cos(angle) * length]
            ),
            colors=[RGBAcolor],
            labels=[name],
        )
        self._parse_entity(name, arrow, Archetype.ARROWS3D)
        return True

    def _resize_entity(
        self,
        entity_name: str,
        radius: int | float,
        length: int | float,
        create_entity: Callable[
            [str, int | float, int | float, List[int | float]],
            rr.archetypes.arrows3d.Arrows3D | rr.archetypes.capsules3d.Capsules3D,
        ],
        entity_type: Archetype,
    ) -> bool:
        """Resize an entity (Arrow, Capsule)"""
        char_index = entity_name.find("/")
        # If entity_name contains '/' then search for the scene
        if char_index != -1 and char_index != len(entity_name) - 1:
            scene_name = entity_name[:char_index]
            scene_index = self._get_scene_index(scene_name)
            # Check if scene exists
            if scene_index != -1:
                entity_name = entity_name[char_index + 1 :]
                entity = self._get_entity(entity_name)
                scene = self.scene_list[scene_index]
                # if `entity` exists in `scene` then log it
                if entity and self._is_entity_in_scene(entity, scene):
                    new_archetype = create_entity(
                        entity_name, radius, length, entity.archetype.colors.pa_array
                    )
                    entity.archetype = new_archetype
                    rr.log(entity.name, entity.archetype, recording=scene.rec)

                    logger.info(
                        f"_resize_entity(): Logging a new {entity_type.name} "
                        f"named '{entity_name}' in '{scene_name}' scene."
                    )
                    return True
                else:
                    logger.error(
                        f"_resize_entity(): {entity_type.name} '{entity_name}' "
                        f"does not exists in '{scene_name}' scene."
                    )
                    return False

        entity = self._get_entity(entity_name)
        if not entity:
            logger.error(
                f"_resize_entity(): {entity_type.name} '{entity_name}' does not exists."
            )
            return False
        new_archetype = create_entity(
            entity_name, radius, length, entity.archetype.colors.pa_array
        )
        entity.archetype = new_archetype
        self._log_entity(entity)
        return True

    def resizeArrow(
        self, arrowName: str, radius: Union[int, float], length: Union[int, float]
    ) -> bool:
        assert isinstance(arrowName, str), "Parameter 'arrowName' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, length]
        ), "Parameters 'radius' and 'length' must be a numbers"

        def create_arrow(
            arrowName: str,
            radius: Union[int, float],
            length: Union[int, float],
            colors: List[Union[int, float]],
        ) -> rr.archetypes.arrows3d.Arrows3D:
            angle = np.arange(start=0, stop=tau, step=tau)
            vectors = np.column_stack(
                [np.sin(angle) * length, np.zeros(1), np.cos(angle) * length]
            )
            arrow = rr.Arrows3D(
                radii=[[radius]],
                vectors=vectors,
                colors=colors,
                labels=[arrowName],
            )
            return arrow

        logger.info("resizeArrow(): Call to _resize_entity().")
        return self._resize_entity(
            arrowName, radius, length, create_arrow, Archetype.ARROWS3D
        )

    def addCapsule(
        self,
        name: str,
        radius: Union[int, float],
        height: Union[int, float],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(name, str), "Parameter 'name' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, height]
        ), "Parameters 'radius' and 'height must be a numbers"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        capsule = rr.Capsules3D(
            lengths=[height],
            radii=[radius],
            colors=[RGBAcolor],
            labels=[name],
        )
        self._parse_entity(name, capsule, Archetype.CAPSULES3D)
        return True

    def resizeCapsule(
        self, capsuleName: str, radius: Union[int, float], length: Union[int, float]
    ) -> bool:
        assert isinstance(capsuleName, str), "Parameter 'capsuleName' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, length]
        ), "Parameters 'radius' and 'length' must be a numbers"

        def create_capsule(
            capsuleName: str,
            radius: Union[int, float],
            length: Union[int, float],
            colors: List[Union[int, float]],
        ) -> rr.archetypes.capsules3d.Capsules3D:
            capsule = rr.Capsules3D(
                radii=[radius],
                lengths=length,
                colors=colors,
                labels=[capsuleName],
            )
            return capsule

        logger.info("resizeCapsule(): Call to _resize_entity().")
        return self._resize_entity(
            capsuleName, radius, length, create_capsule, Archetype.CAPSULES3D
        )

    def addLine(
        self,
        lineName: str,
        pos1: List[Union[int, float]],
        pos2: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(lineName, str), "Parameter 'lineName' must be a string"
        assert all(
            isinstance(x, (list, tuple)) for x in [pos1, pos2]
        ), "Parameters 'pos1' and 'pos2' must be a list or tuple of numbers"
        assert all(
            isinstance(nb, (int, float)) for x in [pos1, pos2] for nb in x
        ), "Parameters 'pos1' and 'pos2' must be a list or tuple of numbers"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        line = rr.LineStrips3D(
            [[pos1, pos2]],
            radii=[0.1],
            colors=[RGBAcolor],
            labels=[lineName],
        )
        self._parse_entity(lineName, line, Archetype.LINESTRIPS3D)
        return True

    def addSquareFace(
        self,
        faceName: str,
        pos1: List[Union[int, float]],
        pos2: List[Union[int, float]],
        pos3: List[Union[int, float]],
        pos4: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(faceName, str), "Parameter 'faceName' must be a string"
        assert all(
            isinstance(x, (list, tuple)) for x in [pos1, pos2, pos3, pos4]
        ), "Parameters 'pos' must be a list or tuple of numbers"
        assert all(
            isinstance(nb, (int, float)) for x in [pos1, pos2, pos3, pos4] for nb in x
        ), "Parameters 'pos' must be a list or tuple of numbers"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        mesh = rr.Mesh3D(
            vertex_positions=[pos1, pos2, pos3, pos4],
            triangle_indices=[[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
            vertex_colors=[RGBAcolor],
        )
        self._parse_entity(faceName, mesh, Archetype.MESH3D)
        return True

    def addTriangleFace(
        self,
        faceName: str,
        pos1: List[Union[int, float]],
        pos2: List[Union[int, float]],
        pos3: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(faceName, str), "Parameter 'faceName' must be a string"
        assert all(
            isinstance(x, (list, tuple)) for x in [pos1, pos2, pos3]
        ), "Parameters 'pos' must be a list or tuple of numbers"
        assert all(
            isinstance(nb, (int, float)) for x in [pos1, pos2, pos3] for nb in x
        ), "Parameters 'pos' must be a list or tuple of numbers"
        assert all(
            len(x) == 3 for x in [pos1, pos2, pos3]
        ), "Parameter 'pos' must be of length 3"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        mesh = rr.Mesh3D(
            vertex_positions=[pos1, pos2, pos3],
            vertex_colors=[RGBAcolor],
        )

        self._parse_entity(faceName, mesh, Archetype.MESH3D)
        return True

    def addSphere(
        self,
        sphereName: str,
        radius: Union[int, float],
        RGBAcolor: List[Union[int, float]],
    ) -> bool:
        assert isinstance(sphereName, str), "Parameter 'sphereName' must be a string"
        assert isinstance(
            radius, (int, float)
        ), "Parameters 'radius' and 'length' must be a numbers"
        assert isinstance(
            RGBAcolor, (list, tuple)
        ), "Parameter 'RGBAcolor' must be a list or tuple"

        sphere = rr.Points3D(
            positions=[[0.0, 0.0, 0.0]],
            radii=[[radius]],
            colors=[RGBAcolor],
            labels=[sphereName],
        )
        self._parse_entity(sphereName, sphere, Archetype.POINTS3D)
        return True

    def _get_recording(self, recName: str) -> rr.RecordingStream | None:
        return next(
            (scene.rec for scene in self.scene_list if scene.name == recName), None
        )

    def _log_entity(self, entity: Entity):
        """Draw a group entity in the Viewer."""
        if entity.scenes is not None:  # TODO: Remove None by default
            for scene in entity.scenes:
                for log_name in entity.log_name:
                    rr.log(
                        log_name,
                        entity.archetype,
                        recording=scene.rec,
                    )
                logger.info(
                    f"_log_entity(): Logging entity '{entity.name}' in '{scene.name}' scene."
                )
            return True
        logger.info(
            f"_log_entity(): Logging entity '{entity.name}' don't have any scenes to be displayed in."
        )
        return False

    def _get_group_list(self, group_name: str) -> List[Group] | None:
        """Get groups inside `self.group_List`"""
        group_list = []
        for group in self.group_list:
            if group.name.strip("/").endswith(group_name):
                group_list.append(group)
        return group_list

    def _format_string(self, first: str, second: str) -> str:
        """Add '/' between `first` and `second`."""
        return first.strip("/") + "/" + second.strip("/")

    def _get_added_groups(self, groupName: str) -> List[Group]:
        """
        Get all the nodes named 'groupName',
            return the list of nodes that are childrens of other nodes.
        Eg: in this list ["test", "world/test", "map/test"]
        _choose_group will return ["world/test", "map/test"]
        """

        g_list = self._get_group_list(groupName)
        new_g_list = []
        if len(g_list) == 1:
            return [g_list[0]]
        for group in g_list:
            if "/" in group.name.strip("/"):
                new_g_list.append(group)
        return new_g_list

    def _get_group_entities_children(self, group_name: str) -> List[Entity]:
        """Return all the entities children of a group"""

        children = []
        for entity in self.entity_list:
            for log_name in entity.log_name:
                if group_name in log_name:
                    children.append(entity)
        return children

    def _add_entity_to_scene(self, entity: Entity, scene_index: int) -> bool:
        """Add Entity to Scene"""
        scene = self.scene_list[scene_index]
        if scene in entity.scenes:
            logger.error(
                f"addToGroup(): Entity '{entity.name}' already in scene '{scene.name}'."
            )
            return False
        entity.add_scene(scene)
        entity.add_log_name(entity.name)
        logger.info(
            f"addToGroup(): Add entity '{entity.name}' to '{scene.name}' scene."
        )
        self._log_entity(entity)
        return True

    def _add_entity_to_group(self, entity: Entity, groupName: str) -> bool:
        """Add Entity to Group"""
        group_name_list = self._get_added_groups(groupName)
        for group in group_name_list:
            for scene in group.scenes:
                entity.add_scene(scene)
            log_name = self._format_string(group.name, entity.name)
            if log_name in entity.log_name:
                logger.error(
                    f"addToGroup(): Entity '{entity.name}' already in group '{group.name}'."
                )
                return False
            entity.add_log_name(log_name)
            self._log_entity(entity)
        logger.info(
            f"addToGroup(): Added entity '{entity.name}' to '{groupName}' group."
        )
        return True

    def _add_group_to_scene(
        self, node_name_list: List[Group], scene_index: int, group_name: str
    ) -> bool:
        """Add Group to a Scene"""
        scene = self.scene_list[scene_index]
        for group in node_name_list:
            if scene in group.scenes:
                logger.error(
                    f"addToGroup(): Group '{group.name}' already in scene '{scene.name}'."
                )
                return False
            group.add_scene(scene)
            # Add scene for all children of the group
            children = self._get_group_entities_children(group_name)
            for child in children:
                child.add_scene(self.scene_list[scene_index])
                self._log_entity(child)
        logger.info(f"addToGroup(): Add group '{group_name}' to '{scene.name}' scene.")
        return True

    def _add_group_to_group(
        self,
        group_name_list: List[Group],
        node_name_list: List[Group],
        node_name: str,
        group_name: str,
    ) -> bool:
        """
        Add Group to Group.
        If the 'group_name' is already added to other group,
        we have to make child nodes accordingly :
            If we have this list of node ["world", "scene/world", "hello/world"],
            and we want to add the node "test" to "world".
            We need to create all child nodes : "world/test", "scene/world/test", ...
        So, we iterate over all nodes that ends with 'group_name' to creates nodes like :
            'group_name'/'node_name'.
        """
        added_group_list = self._get_added_groups(group_name)
        for added_group in added_group_list:
            new_group = Group(self._format_string(added_group.name, node_name))
            for group in group_name_list:
                for scene in group.scenes:
                    new_group.add_scene(scene)
                    # Ensure that the added group 'nodeName' has its `scenes` filled
                    for group1 in node_name_list:
                        if group1.name == new_group.name:
                            logger.error(
                                f"addToGroup(): Group '{node_name}' already in group '{group_name}'."
                            )
                            return False
                        group1.add_scene(scene)
            self.group_list.append(new_group)
        logger.info(f"addToGroup(): Add group '{node_name}' to '{group_name}' group.")
        return True

    def addToGroup(self, nodeName: str, groupName: str) -> bool:
        """
        Actual log of entities.
        Add group1 to a group2 will create another group 'group1/group2'
        """
        assert all(
            isinstance(name, str) for name in [nodeName, groupName]
        ), "Parameters 'nodeName' and 'groupName' must be strings"

        entity = self._get_entity(nodeName)
        node_name_list = self._get_group_list(nodeName)
        if entity is None and not node_name_list:
            logger.error(f"addToGroup(): Node '{nodeName}' does not exists.")
            return False

        scene_index = self._get_scene_index(groupName)
        group_name_list = self._get_group_list(groupName)
        if not group_name_list and scene_index == -1:
            logger.error(f"addToGroup(): Group '{groupName}' does not exists.")
            return False
        ret = True
        if entity:
            if scene_index != -1:
                ret = self._add_entity_to_scene(entity, scene_index)
            elif group_name_list:
                ret = self._add_entity_to_group(entity, groupName)
            else:
                return False
        elif node_name_list:
            if scene_index != -1:
                ret = self._add_group_to_scene(node_name_list, scene_index, nodeName)
            elif group_name_list:
                ret = self._add_group_to_group(
                    group_name_list, node_name_list, nodeName, groupName
                )
            else:
                return False
        self._draw_spacial_view_content()
        return ret

    def createGroup(self, groupName: str) -> bool:
        assert isinstance(groupName, str), "Paramter 'groupName' must be a string"

        self.group_list.append(Group(groupName))
        logger.info(f"createGroup(): create group '{groupName}'.")
        return True

    def _draw_spacial_view_content(self):
        """
        Each `Spatial3DView` has its own content,
        after logging entity (rerun archetype or group),
        you can choose which object you want to display/hide.
        See [`Spatial3DView`](https://ref.rerun.io/docs/python/0.20.3/common/blueprint_views/#rerun.blueprint.views.Spatial3DView)
        and [`SpaceViewContents`](https://ref.rerun.io/docs/python/0.20.3/common/blueprint_archetypes/#rerun.blueprint.archetypes.SpaceViewContents).
        """

        def make_space_view_content(scene: Scene) -> List[str]:
            """Make the SpaceViewContens for a given Scene."""
            content = []
            for entity in self.entity_list:
                if scene in entity.scenes:
                    for log_name in entity.log_name:
                        content.append("+ " + log_name)
            for group in self.group_list:
                content.append("+ " + group.name)
            return content

        # There is a bug with rerun 0.20 : when sending
        # different blueprints to recordings that are
        # in the same application - 03/12/2024
        # Linked issue : https://github.com/rerun-io/rerun/issues/8287
        for scene in self.scene_list:
            content = make_space_view_content(scene)
            rr.send_blueprint(
                rrb.Spatial3DView(contents=content),
                recording=scene.rec,
            )

    def deleteNode(self, nodeName: str, all: bool) -> bool:
        assert isinstance(nodeName, str), "Parameter 'nodeName' must be a string"
        assert isinstance(all, bool), "Parameter 'all' must be a boolean"

        groups = self._get_group_list(nodeName)
        entity = self._get_entity(nodeName)
        if not groups and entity is None:
            logger.error(f"deleteNode(): Node '{nodeName}' does not exists.")
            return False
        for group in groups:
            if group in self.group_list:
                self.group_list.remove(group)
                # Remove all chidren of group
                children = self._get_group_entities_children(group.name)
                if all:
                    for child in children:
                        if child in self.entity_list:
                            self.entity_list.remove(child)
                else:
                    for child in children:
                        for log_name in child.log_name:
                            if group.name in log_name:
                                child.log_name.remove(log_name)
                logger.info(
                    f"deleteNode(): Successfully removed node group '{nodeName}'."
                )
        if entity is not None:
            self.entity_list.remove(entity)
            logger.info(f"deleteNode(): Successfully removed node entity '{nodeName}'.")
        self._draw_spacial_view_content()
        return True
