import logging
from math import tau
from typing import List, Union

import numpy as np
import rerun as rr
import rerun.blueprint as rrb

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
            entity = Entity(entityName, archetypeType, archetype)
            self.entityList[archetypeType.value].append(entity)

            if group is None:
                logger.info(f"_parseEntity(): call to createGroup({groupName})")
                self.createGroup(groupName)
            logger.info(
                f"_parseEntity(): create entity '{entityName}' of type {archetypeType.name}."
                f"_parseEntity(): call to addToGroup({entityName}, {groupName})."
            )
            self.addToGroup(entityName, groupName)
            return
        # Create entity and store it to self.entityList
        entity = Entity(archetypeName, archetypeType, archetype)
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

        group = self._getNodeInTree(self.groupTree, arrowName)
        if group is None:
            entity = self._getEntity(arrowName)
            if entity is None:
                logger.error(f"resizeArrow(): Arrow '{arrowName}' does not exists.")
                return False
            newArrow = createArrow(
                arrowName, radius, length, entity.archetype.colors.pa_array
            )
            entity.archetype = newArrow
            logger.info(
                f"resizeArrow(): Creating a new arrow called '{arrowName}'."
                "resizeArrow() does not log it."
            )
            return True
        else:
            if not isinstance(group.value, Entity):
                logger.error(
                    f"resizeArrow(): group '{group.name}' is not of type Entity"
                )
                return False
            entity = group.value
            newArrow = createArrow(
                arrowName, radius, length, entity.archetype.colors.pa_array
            )
            entity.archetype = newArrow
            logger.info(
                f"resizeArrow(): Creating a new arrow called '{arrowName}' and log it."
            )
            self._logEntity(group)
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

        group = self._getNodeInTree(self.groupTree, capsuleName)
        if group is None:
            entity = self._getEntity(capsuleName)
            if entity is None:
                logger.error(
                    f"resizeCapsule(): Capsule '{capsuleName}' does not exists."
                )
                return False
            newCapsule = createCapsule(
                capsuleName, radius, length, entity.archetype.colors.pa_array
            )
            entity.archetype = newCapsule
            logger.info(
                f"resizeCapsule(): Creating a new capsule called '{capsuleName}'."
                "resizeCapsule() does not log it."
            )
            return True
        else:
            if not isinstance(group.value, Entity):
                logger.error(
                    f"resizeCapsule(): group '{group.name}' is not of type Entity"
                )
                return False
            entity = group.value
            newCapsule = createCapsule(
                capsuleName, radius, length, entity.archetype.colors.pa_array
            )
            entity.archetype = newCapsule
            logger.info(
                f"resizeCapsule(): Creating a new capsule called '{capsuleName}' and log it."
            )
            self._logEntity(group)
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
        if groupName in root.name + "/":
            return root
        for child in root.children:
            foundNode = self._getNodeInTree(child, groupName)
            if foundNode:
                return foundNode

    def _getNodeListInTree(self, root: Group, groupName: str) -> List[Group]:
        """
        Get all the node in self.groupTree,
        regardless of its type, based on its name
        """
        if root is None:
            return []
        nodeList = []
        if groupName in root.name + "/":
            nodeList.append(root)
        for child in root.children:
            nodeList.extend(self._getNodeListInTree(child, groupName))
        return nodeList

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
        """Get a group node in self.groupTree"""
        if root is None:
            return None
        if root.name == groupName and root.value is None:
            return root
        for child in root.children:
            foundNode = self._getGroupInTree(child, groupName)
            if foundNode:
                return foundNode

    def _getSceneParent(self, target: Group) -> Scene | None:
        """
        Browse tree to find the last Scene parent of the given node
        """

        def dfs(current: Group, targetNode: Group, lastScene: Group = None):
            if current == targetNode:
                if lastScene is not None:
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

        def format_string(first: str, second: str) -> str:
            """
            Remove last '/' of `first` and first '/' of `second`.
            Return first + '/' + second
            """

            if first.endswith("/"):
                first = first[:-1]
            if second.startswith("/"):
                second = second[1:]
            return first + "/" + second

        entity = self._getEntity(nodeName)
        groupIndex = self._getNotAddedGroup(nodeName)
        if entity is None and groupIndex == -1:
            logger.error(f"addToGroup(): node '{nodeName}' does not exists.")
            return False

        groupList = self._getNodeListInTree(self.groupTree, groupName)
        if not groupList:
            logger.error(f"addToGroup(): group '{groupName}' does not exists.")
            return False

        for group in groupList:
            if entity:
                nodeName = format_string(group.name, nodeName)
                newGroup = Group(nodeName, entity)
                group.add_child(newGroup)
                sceneAncestor = self._getSceneParent(newGroup)
                if sceneAncestor is not None:
                    entity.addScene(sceneAncestor)
                logger.info(f"addToGroup(): Creating '{newGroup.name}' entity group.")
                self._logEntity(newGroup)
            elif groupIndex != -1:
                newGroup = self._makeGroup(nodeName)
                newGroup.name = format_string(group.name, newGroup.name)
                for child in newGroup.children:
                    child.name = format_string(group.name, child.name)
                group.add_child(newGroup)
                logger.info(f"addToGroup(): Creating '{newGroup.name}' group.")
            self._draw_spacial_view_content()
        return True

    def _makeGroup(self, groupName: str) -> Group:
        """
        Given a groupName, it will create a group
        and its children, with '/' as separator.
        """
        split = groupName.strip("/").split("/")
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

    def _getNodeParentList(
        self, root: Group, nodeName: str, parent: Group = None
    ) -> List[Group]:
        """Get all the parent of the node"""
        if root is None:
            return []
        parents = []
        if nodeName in root.name + "/":
            parents.append(parent)
        for child in root.children:
            parents.extend(self._getNodeParentList(child, nodeName, root))
        return parents

    def _draw_spacial_view_content(self):
        def make_space_view_content(scene: Scene, node: Group) -> List[str]:
            """Make the SpaceViewContens for a given Scene"""

            content = []
            if node is None:
                return content
            if isinstance(node.value, Entity) and scene in node.value.scenes:
                content.append("+ " + node.name)
            elif node.value is None and scene.name in node.name:
                # Ensure the node is a group and it is displayed in the scene parameter
                content.append("+ " + node.name)
            for child in node.children:
                content.extend(make_space_view_content(scene, child))
            return content

        for scene in self.sceneList:
            content = make_space_view_content(scene, self.groupTree)
            rr.send_blueprint(
                rrb.Spatial3DView(contents=content),
                recording=scene.rec,
            )

    def deleteNode(self, nodeName: str, all: bool) -> bool:
        def deleteGroupValue(group: Group):
            """
            Remove group value (and its children) in self.window/scene/entity/groupList
            """
            if group is None:
                return
            for child in group.children:
                deleteGroupValue(child)
            if group.value is None:
                if group.name in self.groupList:
                    self.groupList.remove(group.value)
            elif isinstance(group.value, Scene):
                if group.value in self.sceneList:
                    self.sceneList.remove(group.value)
            elif isinstance(group.value, Entity):
                entity = self._getEntity(node.value.name)
                if entity is not None:
                    self.entityList[entity.type.value].remove(group.value)

        nodeList = self._getNodeListInTree(self.groupTree, nodeName)
        if not nodeList:
            logger.error(f"deleteNode(): Node '{nodeName}' does not exists.")
            return False
        parentList = self._getNodeParentList(self.groupTree, nodeName)
        if not parentList:
            logger.error(f"deleteNode(): No parent found for node '{nodeName}'.")
            return False
        for node, parent in zip(nodeList, parentList):
            scene = self._getSceneParent(node)
            parent.children.remove(node)
            if scene is None:
                logger.info(f"deleteNode(): No parent scene for {node.name}.")
                if all:
                    deleteGroupValue(node)
                continue
            self._draw_spacial_view_content()
            logger.info(f"deleteNode(): Removing node '{node.name}'.")
            if all:
                deleteGroupValue(node)
        return True
