import logging
from math import tau
from typing import List, Union

import numpy as np
import rerun as rr

from .entity import Entity, Group
from .scene import Scene
from .archetype import Archetype

logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.gui = Gui()

    def __repr__(self):
        return f"Client({self.gui})"


class Gui:
    def __init__(self):
        """
        sceneList : List of `Scene` class (name and associated recording)
        windowList : List of all window names
        entityList : List containing every Rerun archetypes,
                    each archetypes contain a list of `Entity` class.
                    Use `Enum Archetype` to get indices.
        """

        self.sceneList = []
        self.windowList = []
        self.entityList = [[] for _ in range(len(Archetype))]
        self.groupList = []
        self.groupTree = Group("/", None, [])

    def __repr__(self):
        return (
            f"Gui(windowList={self.windowList}\n"
            f"sceneList (size: {len(self.sceneList)}) = {self.sceneList}\n"
            f"entityList (size: {len(self.entityList)}) = {self.entityList}\n"
            f"groupTree = {self.groupTree})\n"
            f"groupList (size: {len(self.groupList)}) : {self.groupList}\n"
        )

    def createWindow(self, name: str):
        assert isinstance(name, str), "Parameter 'name' must be a string"

        self.windowList.append(name)
        msg = (
            "createWindow() does not create any window, "
            "Rerun create both window and scene at the same time. "
            "Window will be created after calling addSceneToWindow()."
        )
        logger.info(msg)
        return name

    def createScene(self, sceneName: str):
        assert isinstance(sceneName, str), "Parameter 'sceneName' must be a string"

        self.sceneList.append(Scene(sceneName))
        msg = (
            "createScene() does not create any scene yet, "
            "Rerun create both window and scene at the same time. "
            "Window will be created after calling addSceneToWindow()."
        )
        logger.info(msg)

    def _getSceneIndex(self, sceneName: str):
        for index, scene in enumerate(self.sceneList):
            if scene.name == sceneName:
                return index
        return -1

    def addSceneToWindow(self, sceneName: str, wid: str):
        assert all(
            isinstance(name, str) for name in [sceneName, wid]
        ), "Parameters 'sceneName' and 'wid' must be strings"

        index = self._getSceneIndex(sceneName)
        if index == -1:
            logger.error(f"addSceneToWindow(): Unknown sceneName '{sceneName}'.")
            return False
        elif wid not in self.windowList:
            logger.error(f"addSceneToWindow(): Unknown windowName '{wid}'.")
            return False

        rec = rr.new_recording(application_id=wid, recording_id=sceneName, spawn=True)
        self.sceneList[index].setRec(rec)
        scene = Group(sceneName, self.sceneList[index], [])
        window = Group(wid, None, [scene])
        self.groupTree.add_child(window)
        return True

    def _parseEntity(
        self, archetypeName: str, archetype: rr.archetypes, archetypeType: Archetype
    ):
        """
        Parse archetype name and log (or not) archetype :
            - if there is a group specified in archetypeName :  <group>/name
                it will add the archetype to group, if the group does not exits,
                it will create it in self.groupTree.
            - if there is no '/', archetype will require addToGroup() to be added to
                self.groupTree
        """
        assert archetype is not None, "_parseEntity(): 'entity' must not be None"
        assert isinstance(
            archetypeType, Archetype
        ), "_parseEntity(): 'archetypeType' must be of type `enum Archetype`"

        charIndex = archetypeName.find("/")
        # If entityName contains '/' then create Entity and search for the group
        if charIndex != -1 and charIndex != len(archetypeName) - 1:
            groupName = archetypeName[:charIndex]
            group = self._getNodeInTree(self.groupTree, groupName)
            entityName = archetypeName[charIndex + 1 :]
            entity = Entity(entityName, archetype)
            self.entityList[archetypeType.value].append(entity)

            if group is None:
                logger.info("_parseEntity(): call to createGroup()")
                self.createGroup(groupName)
            logger.info(
                f"_parseEntity(): create entity '{entityName}' of type {archetypeType.name}."
                f"_parseEntity(): call to addToGroup()."
            )
            self.addToGroup(entityName, groupName)
            return
        # Create entity and store it to self.entityList
        entity = Entity(archetypeName, archetype)
        self.entityList[archetypeType.value].append(entity)
        logger.info(f"_parseEntity(): Creating entity '{archetypeName}'.")

    def _getEntity(self, entityName: str):
        for entity_list in self.entityList:
            for entity in entity_list:
                if entity.name == entityName:
                    return entity
        return None

    def _isEntityInScene(self, entity: Entity, scene: Scene):
        if entity and entity.scenes:
            return scene in entity.scenes
        return False

    def addFloor(self, floorName: str):
        assert isinstance(floorName, str), "Parameter 'floorName' must be a string"

        floor = rr.Boxes3D(
            sizes=[[200, 200, 0.5]],
            colors=[(125, 125, 125)],
            fill_mode="Solid",
        )
        self._parseEntity(floorName, floor, Archetype.BOXES3D)
        return True

    def addBox(
        self,
        boxName: str,
        boxSize1: List[Union[int, float]],
        boxSize2: List[Union[int, float]],
        boxSize3: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ):
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
        self._parseEntity(boxName, box, Archetype.BOXES3D)
        return True

    def addArrow(
        self,
        name: str,
        radius: Union[int, float],
        length: Union[int, float],
        RGBAcolor: List[Union[int, float]],
    ):
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
        self._parseEntity(name, arrow, Archetype.ARROWS3D)
        return True

    def resizeArrow(
        self, arrowName: str, radius: Union[int, float], length: Union[int, float]
    ):
        assert isinstance(arrowName, str), "Parameter 'arrowName' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, length]
        ), "Parameters 'radius' and 'length' must be a numbers"

        def createArrow(
            arrowName: str,
            radius: Union[int, float],
            length: Union[int, float],
            colors: List[Union[int, float]],
        ):
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

        charIndex = arrowName.find("/")
        # If arrowName contains '/' then search for the scene
        if charIndex != -1 and charIndex != len(arrowName) - 1:
            sceneName = arrowName[:charIndex]
            sceneIndex = self._getSceneIndex(sceneName)
            # Check if scene exists
            if sceneIndex != -1:
                entityName = arrowName[charIndex + 1 :]
                entity = self._getEntity(entityName)
                scene = self.sceneList[sceneIndex]
                # if `entity` exists in `scene` then log it
                if entity and self._isEntityInScene(entity, scene):
                    newArrow = createArrow(
                        arrowName, radius, length, entity.archetype.colors.pa_array
                    )
                    entity.archetype = newArrow
                    rr.log(entity.name, entity.archetype, recording=scene.rec)

                    msg = (
                        f"resizeArrow('{arrowName}'): Logging new arrow "
                        f"'{entityName}' in '{sceneName}' scene."
                    )
                    logger.info(msg)
                    return True
                else:
                    msg = (
                        f"resizeArrow({arrowName}): Arrow '{entityName}' "
                        f"does not exists in '{sceneName}' scene."
                    )
                    logger.error(msg)
                    return False

        entity = self._getEntity(arrowName)
        if not entity:
            logger.error(f"resizeArrow(): Arrow '{arrowName}' does not exists.")
            return False

        newArrow = createArrow(
            arrowName, radius, length, entity.archetype.colors.pa_array
        )
        entity.archetype = newArrow
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
    ):
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
        self._parseEntity(name, capsule, Archetype.CAPSULES3D)
        return True

    def resizeCapsule(
        self, capsuleName: str, radius: Union[int, float], length: Union[int, float]
    ):
        assert isinstance(capsuleName, str), "Parameter 'capsuleName' must be a string"
        assert all(
            isinstance(x, (int, float)) for x in [radius, length]
        ), "Parameters 'radius' and 'length' must be a numbers"

        def createCapsule(
            capsuleName: str,
            radius: Union[int, float],
            length: Union[int, float],
            colors: List[Union[int, float]],
        ):
            capsule = rr.Capsules3D(
                radii=[radius],
                lengths=length,
                colors=colors,
                labels=[capsuleName],
            )
            return capsule

        charIndex = capsuleName.find("/")
        # If capsuleName contains '/' then search for the scene
        if charIndex != -1 and charIndex != len(capsuleName) - 1:
            sceneName = capsuleName[:charIndex]
            sceneIndex = self._getSceneIndex(sceneName)
            # Check if scene exists
            if sceneIndex != -1:
                entityName = capsuleName[charIndex + 1 :]
                entity = self._getEntity(entityName)
                scene = self.sceneList[sceneIndex]
                # if `entity` exists in `scene` then log it
                if entity and self._isEntityInScene(entity, scene):
                    newCapsule = createCapsule(
                        capsuleName, radius, length, entity.archetype.colors.pa_array
                    )
                    entity.archetype = newCapsule
                    rr.log(entity.name, entity.archetype, recording=scene.rec)

                    msg = (
                        f"resizeCapsule('{capsuleName}'): Logging new Capsules3D "
                        f"'{entityName}' in '{sceneName}' scene."
                    )
                    logger.info(msg)
                    return True
                else:
                    msg = (
                        f"resizeCapsule({capsuleName}): Capsules3D '{entityName}' "
                        f"does not exists in '{sceneName}' scene."
                    )
                    logger.error(msg)
                    return False

        entity = self._getEntity(capsuleName)
        if not entity:
            logger.error(
                f"resizeCapsule(): Capsules3D '{capsuleName}' does not exists."
            )
            return False

        newCapsule = createCapsule(
            capsuleName, radius, length, entity.archetype.colors.pa_array
        )
        entity.archetype = newCapsule
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
    ):
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
        self._parseEntity(lineName, line, Archetype.LINESTRIPS3D)
        return True

    def addSquareFace(
        self,
        faceName: str,
        pos1: List[Union[int, float]],
        pos2: List[Union[int, float]],
        pos3: List[Union[int, float]],
        pos4: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ):
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
        self._parseEntity(faceName, mesh, Archetype.MESH3D)
        return True

    def addTriangleFace(
        self,
        faceName: str,
        pos1: List[Union[int, float]],
        pos2: List[Union[int, float]],
        pos3: List[Union[int, float]],
        RGBAcolor: List[Union[int, float]],
    ):
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

        self._parseEntity(faceName, mesh, Archetype.MESH3D)
        return True

    def addSphere(
        self,
        sphereName: str,
        radius: Union[int, float],
        RGBAcolor: List[Union[int, float]],
    ):
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
        self._parseEntity(sphereName, sphere, Archetype.POINTS3D)
        return True

    def _getRecording(self, recName: str):
        return next(
            (scene.rec for scene in self.sceneList if scene.name == recName), None
        )

    def _logEntity(self, group: Group):
        """Draw a group entity in the Viewer"""
        entity = group.value

        if entity.scenes is not None:
            for scene in entity.scenes:
                split = group.name.split("/")
                # Ensure that we log the group to the right scene.
                if split[0] in scene.name:
                    rr.log(
                        group.name,
                        entity.archetype,
                        recording=scene.rec,
                    )
                    logger.info(
                        f"_logEntity(): Logging entity '{entity.name}' in '{scene.name}' scene."
                    )
            return True
        else:
            logger.info(
                f"_logEntity(): Logging entity '{entity.name}' don't have any scenes to be displayed in."
            )
            return False

    def _getNodeInTree(self, root: Group, groupName: str) -> Group | None:
        """Get a node in self.groupTree, regardless of its type"""
        if root is None:
            return None
        if groupName in root.name:
            return root
        for child in root.children:
            foundNode = self._getNodeInTree(child, groupName)
            if foundNode:
                return foundNode

    def _getNotAddedGroup(self, groupName: str) -> int:
        """Return the index of the groupName in self.groupList"""
        for i in range(len(self.groupList)):
            if self.groupList[i] == groupName:
                return i
        return -1

    def _getSceneInTree(self, root: Group, sceneName: str) -> Scene | None:
        """Get a scene in self.groupTree"""
        if root is None:
            return None
        if root.name == sceneName and isinstance(root.value, Scene):
            return root
        for child in root.children:
            foundNode = self._getSceneInTree(child, sceneName)
            if foundNode:
                return foundNode

    def _getGroupInTree(self, root: Group, groupName: str) -> Group | None:
        """Get a group in self.groupTree"""
        if root is None:
            return None
        if root.name == groupName and root.value is None:
            return root
        for child in root.children:
            foundNode = self._getGroupInTree(child, groupName)
            if foundNode:
                return foundNode

    def _getSceneParent(self, target: Group) -> Group | None:
        """
        Browse tree to find the last Scene parent of the given node
        """

        def dfs(current: Group, targetNode: Group, lastScene: Group = None):
            if current == targetNode:
                return lastScene.value
            if isinstance(current.value, Scene):
                lastScene = current
            for child in current.children:
                result = dfs(child, targetNode, lastScene)
                if result:
                    return result

        return dfs(self.groupTree, target)

    def addToGroup(self, nodeName: str, groupName: str) -> bool:
        """
        Actual log of an entity
        """
        assert all(
            isinstance(name, str) for name in [nodeName, groupName]
        ), "Parameters 'nodeName' and 'groupName' must be strings"

        entity = self._getEntity(nodeName)
        groupIndex = self._getNotAddedGroup(nodeName)
        if entity is None and groupIndex == -1:
            logger.error(f"addToGroup(): node '{nodeName}' does not exists.")
            return False

        group = self._getNodeInTree(self.groupTree, groupName)
        if group is None:
            logger.error(f"addToGroup(): group '{groupName}' does not exists.")
            return False

        if group.name[-1] != "/" and nodeName[0] != "/":
            nodeName = group.name + "/" + nodeName
        else:
            nodeName = group.name + nodeName
        if entity:
            newGroup = Group(nodeName, entity)
            group.add_child(newGroup)
            sceneAncestor = self._getSceneParent(newGroup)
            if sceneAncestor is not None:
                entity.addScene(sceneAncestor)
            logger.info(f"addToGroup(): Creating '{newGroup.name}' entity group.")
            self._logEntity(newGroup)
        elif groupIndex != -1:
            newGroup = self._makeGroup(nodeName)
            newGroup.name = groupName + newGroup.name
            group.add_child(newGroup)
            logger.info(f"addToGroup(): Creating '{newGroup.name}' group.")
        return True

    def _makeGroup(self, groupName: str) -> Group:
        split = groupName.split("/")
        root = Group(split[0])
        current = root
        current_path = split[0]

        for string in split[1:]:
            current_path += "/" + string
            child = Group(current_path)
            current.add_child(child)
            current = child
        return root

    def createGroup(self, groupName: str) -> bool:
        assert isinstance(groupName, str), "Paramter 'groupName' must be a string"

        self.groupList.append(groupName)
        logger.info(
            "createGroup(): does not create the group, group is create when calling addToGroup()."
        )
        return True
