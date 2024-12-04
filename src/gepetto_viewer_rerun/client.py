import logging
from enum import Enum
from math import tau
from typing import List, Union

import numpy as np
import rerun as rr

from .entity import Entity, MeshFromPath, Group
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
        self.entity_list = [[] for _ in range(len(Archetype))]
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
        self, archetypeName: str, archetype: rr.archetypes, entityType: Archetype
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
            entityType, Archetype
        ), "_parse_entity(): 'entityType' must be of type `enum Archetype`"

        char_index = archetypeName.find("/")
        # If archetypeName contains '/' then search for the scene in self.scene_list
        if char_index != -1 and char_index != len(archetypeName) - 1:
            scene_name = archetypeName[:char_index]
            scene_index = self._get_scene_index(scene_name)

            if scene_index != -1:
                entity_name = archetypeName[char_index + 1 :]
                entity = Entity(entity_name, archetype, self.scene_list[scene_index])
                self.entity_list[entityType.value].append(entity)

                if entityType == Archetype.MESH_FROM_PATH:
                    # There is a bug with `log_file_from_path` and recordings.
                    # That's why we call `rec.to_native()`.
                    # 19/11/2024 - Issue : https://github.com/rerun-io/rerun/issues/8167
                    rr.log_file_from_path(
                        file_path=entity.archetype.path,
                        recording=self.scene_list[scene_index].rec.to_native(),
                    )
                else:
                    rr.log(
                        entity_name,
                        entity.archetype,
                        recording=self.scene_list[scene_index].rec,
                    )
                msg = (
                    f"_parse_entity() creates a {entityType.name} for '{archetypeName}', "
                    f"and logs it directly to '{self.scene_list[scene_index].name}' scene."
                )
                logger.info(msg)
                return
        # Put entity to entity_list, wait for addToGroup() to be logged
        entity = Entity(archetypeName, archetype)
        self.entity_list[entityType.value].append(entity)
        msg = (
            f"_parse_entity() does not create a {entityType.name} for '{archetypeName}', "
            "it will be created when added to a group with addToGroup()."
        )
        logger.info(msg)

    def _get_entity(self, entityName: str) -> Entity | None:
        for entity_list in self.entity_list:
            for entity in entity_list:
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

    def resizeArrow(
        self, arrowName: str, radius: Union[int, float], length: Union[int, float]
    ) -> bool:
        assert isinstance(arrowName, str), "Parameter 'arrowName' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, length]
        ), "Parameters 'radius' and 'length' must be a numbers"

        def createArrow(
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

        char_index = arrowName.find("/")
        # If arrowName contains '/' then search for the scene
        if char_index != -1 and char_index != len(arrowName) - 1:
            scene_name = arrowName[:char_index]
            scene_index = self._get_scene_index(scene_name)
            # Check if scene exists
            if scene_index != -1:
                entity_name = arrowName[char_index + 1 :]
                entity = self._get_entity(entity_name)
                scene = self.scene_list[scene_index]
                # if `entity` exists in `scene` then log it
                if entity and self._is_entity_in_scene(entity, scene):
                    new_arrow = createArrow(
                        arrowName, radius, length, entity.archetype.colors.pa_array
                    )
                    entity.archetype = new_arrow
                    rr.log(entity.name, entity.archetype, recording=scene.rec)

                    msg = (
                        f"resizeArrow('{arrowName}'): Logging new arrow "
                        f"'{entity_name}' in '{scene_name}' scene."
                    )
                    logger.info(msg)
                    return True
                else:
                    msg = (
                        f"resizeArrow({arrowName}): Arrow '{entity_name}' "
                        f"does not exists in '{scene_name}' scene."
                    )
                    logger.error(msg)
                    return False

        entity = self._get_entity(arrowName)
        if not entity:
            logger.error(f"resizeArrow(): Arrow '{arrowName}' does not exists.")
            return False

        new_arrow = createArrow(
            arrowName, radius, length, entity.archetype.colors.pa_array
        )
        entity.archetype = new_arrow
        if entity.scenes:
            for scene in entity.scenes:
                rr.log(entity.name, entity.archetype, recording=scene.rec)
                msg = (
                    f"resizeArrow(): Logging a new Arrow3D named '{entity.name}' "
                    f"in '{scene.name}' scene."
                )
                logger.info(msg)
        else:
            msg = f"resizeArrow(): Resizing an Arrow3D named '{entity.name}'."
            logger.info(msg)
        return True

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

        def createCapsule(
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

        char_index = capsuleName.find("/")
        # If capsuleName contains '/' then search for the scene
        if char_index != -1 and char_index != len(capsuleName) - 1:
            scene_name = capsuleName[:char_index]
            scene_index = self._get_scene_index(scene_name)
            # Check if scene exists
            if scene_index != -1:
                entity_name = capsuleName[char_index + 1 :]
                entity = self._get_entity(entity_name)
                scene = self.scene_list[scene_index]
                # if `entity` exists in `scene` then log it
                if entity and self._is_entity_in_scene(entity, scene):
                    new_capsule = createCapsule(
                        capsuleName, radius, length, entity.archetype.colors.pa_array
                    )
                    entity.archetype = new_capsule
                    rr.log(entity.name, entity.archetype, recording=scene.rec)

                    msg = (
                        f"resizeCapsule('{capsuleName}'): Logging new Capsules3D "
                        f"'{entity_name}' in '{scene_name}' scene."
                    )
                    logger.info(msg)
                    return True
                else:
                    msg = (
                        f"resizeCapsule({capsuleName}): Capsules3D '{entity_name}' "
                        f"does not exists in '{scene_name}' scene."
                    )
                    logger.error(msg)
                    return False

        entity = self._get_entity(capsuleName)
        if not entity:
            logger.error(
                f"resizeCapsule(): Capsules3D '{capsuleName}' does not exists."
            )
            return False

        new_capsule = createCapsule(
            capsuleName, radius, length, entity.archetype.colors.pa_array
        )
        entity.archetype = new_capsule
        if entity.scenes:
            for scene in entity.scenes:
                rr.log(entity.name, entity.archetype, recording=scene.rec)
                msg = (
                    f"resizeCapsule(): Logging a new Capsules3D named '{entity.name}' "
                    f"in '{scene.name}' scene."
                )
                logger.info(msg)
        else:
            msg = f"resizeCapsule(): Resizing an Capsules3D named '{entity.name}'."
            logger.info(msg)
        return True

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

    def _log_archetype(self, entityName: str, groupName: str) -> bool:
        entity = self._get_entity(entityName)
        rec = self._get_recording(groupName)
        scene_index = self._get_scene_index(groupName)

        if isinstance(entity.archetype, MeshFromPath):
            # There is a bug with `log_file_from_path` and recordings.
            # That's why we call `rec.to_native()`.
            # 19/11/2024 - Issue : https://github.com/rerun-io/rerun/issues/8167
            rr.log_file_from_path(
                file_path=entity.archetype.path, recording=rec.to_native()
            )
            logger.info(f"Logging Mesh from file named '{entity.name}'.")
            return True
        elif isinstance(entity.archetype, rr.archetypes.arrows3d.Arrows3D):
            logger.info(f"Logging Arrows3D named '{entity.name}'.")
        elif isinstance(entity.archetype, rr.archetypes.boxes3d.Boxes3D):
            logger.info(f"Logging Boxes3D named '{entity.name}'.")
        elif isinstance(entity.archetype, rr.archetypes.capsules3d.Capsules3D):
            logger.info(f"Logging Capsules3D named '{entity.name}'.")
        elif isinstance(entity.archetype, rr.archetypes.line_strips3d.LineStrips3D):
            logger.info(f"Logging LineStrip3D named '{entity.name}'.")
        elif isinstance(entity.archetype, rr.archetypes.mesh3d.Mesh3D):
            logger.info(f"Logging Mesh3D named '{entity.name}'.")
        elif isinstance(entity.archetype, rr.archetypes.points3d.Points3D):
            logger.info(f"Logging Points3D named '{entity.name}'.")
        else:
            return False
        entity.addScene(self.scene_list[scene_index])
        rr.log(
            entity.name,
            entity.archetype,
            recording=rec,
        )
        return True

    def _log_entity(self, entity: Entity):
        """Draw a group entity in the Viewer."""
        if entity.scenes is not None:  # TODO: Remove None by default
            for scene in entity.scenes:
                rr.log(
                    entity.log_name,
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
        """Get group inside `self.group_List`"""
        group_list = []
        for group in self.group_list:
            if group.name.strip("/").endswith(group_name):
                group_list.append(group)
        return group_list

    def _format_string(self, first: str, second: str) -> str:
        """Add '/' between `first` and `second`."""
        return first.strip("/") + "/" + second.strip("/")

    def _get_added_group(self, groupName: str) -> List[Group]:
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

    def _get_children_entity_in_group(self, group_name: str) -> List[Entity]:
        """Return all the children entity of a group"""

        children = []
        for archetype in self.entity_list:
            for entity in archetype:
                if group_name in entity.log_name:
                    children.append(entity)
        return children

    def _add_entity_to_scene(self, entity: Entity, scene_index: int):
        """Add Entity to Scene"""
        scene = self.scene_list[scene_index]
        entity.addScene(scene)
        entity.set_log_name(entity.name)
        logger.info(
            f"addToGroup(): Add entity '{entity.name}' to '{scene.name}' scene."
        )
        self._log_entity(entity)

    def _add_entity_to_group(
        self, entity: Entity, group_name_list: List[Group], groupName: str
    ):
        """Add Entity to Group"""
        group_name_list = self._get_added_group(groupName)
        for group in group_name_list:
            for scene in group.scenes:
                entity.addScene(scene)

            entity.set_log_name(self._format_string(group.name, entity.name))
            self._log_entity(entity)
        logger.info(f"addToGroup(): Add entity '{entity.name}' to '{groupName}' group.")

    def _add_group_to_scene(
        self, node_name_list: List[Group], scene_index: int, group_name: str
    ):
        """Add Group to a Scene"""
        scene = self.scene_list[scene_index]
        for group in node_name_list:
            group.add_scene(scene)

            # Add scene for all children of the group
            children = self._get_children_entity_in_group(group_name)
            for child in children:
                child.addScene(self.scene_list[scene_index])
                self._log_entity(child)
        logger.info(f"addToGroup(): Add group '{group_name}' to '{scene.name}' scene.")

    def _add_group_to_group(
        self,
        group_name_list: List[Group],
        node_name_list: List[Group],
        group1_name: str,
        group2_name: str,
    ):
        """Add Group to Group"""
        new_group = Group(self._format_string(group2_name, group1_name))
        for group in group_name_list:
            for scene in group.scenes:
                new_group.add_scene(scene)
                # Ensure that the added group 'nodeName' has its `scenes` filled
                for group1 in node_name_list:
                    group1.add_scene(scene)
        self.group_list.append(new_group)
        logger.info(
            f"addToGroup(): Add group '{group1_name}' to '{group2_name}' group."
        )

    def addToGroup(self, nodeName: str, groupName: str) -> bool:
        """
        Actual log of an entity
        add group1 to a group2 will create another group 'group1/group2'
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

        if entity:
            if scene_index != -1:
                self._add_entity_to_scene(entity, scene_index)
            elif group_name_list:
                self._add_entity_to_group(entity, group_name_list, groupName)
            else:
                return False
        elif node_name_list:
            if scene_index != -1:
                self._add_group_to_scene(node_name_list, scene_index, nodeName)
            elif group_name_list:
                self._add_group_to_group(
                    group_name_list, node_name_list, nodeName, groupName
                )
            else:
                return False
        return True

    def createGroup(self, groupName: str) -> bool:
        assert isinstance(groupName, str), "Paramter 'groupName' must be a string"

        self.group_list.append(Group(groupName))
        logger.info(f"createGroup(): create group '{groupName}'.")
        return True
