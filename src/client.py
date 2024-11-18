import logging
import numpy as np
from math import tau
from enum import Enum
import rerun as rr

from src.entity import (
    Entity,
    MeshFromPath
)
from src.scene import Scene

logger = logging.getLogger(__name__)

class Archetype(Enum):
    ARROWS3D = 0
    BoxeS3D = 1
    CAPSULES3D = 2
    LINESTRIPS3D = 3
    MESH3D = 4
    MESH_FROM_PATH = 5
    POINTS3D = 6
    

class Client:
    def __init__(self):
        self.gui = Gui()

class Gui:
    def __init__(self, windowName="python-pinocchio", recordingName="world"):
        """
        sceneList : List of `Scene` class (name and associated recording)
        windowList : List of all window names
        entityList : List containing every Rerun archetypes,
                    each archetypes contain a list of `Entity` class.
                    Use `Enum Archetype` to get indices.
        """   
        
        self.sceneList = []
        self.windowList = []
        self.entityList = [[]] * len(Archetype)
    
    def createWindow(self, name):
        assert isinstance(name, str), "Parameter 'name' must be a string"
        
        self.windowList.append(name)
        msg = (
            "createWindow() does not create any window, "
            "Rerun create both window and scene at the same time. "
            "Window will be created after calling addSceneToWindow()."
        )
        logger.info(msg)
        return name
    
    def createScene(self, sceneName):
        assert isinstance(sceneName, str), "Parameter 'sceneName' must be a string"
        
        self.sceneList.append(Scene(sceneName))
        msg = (
            "createScene() does not create any scene yet, "
            "Rerun create both window and scene at the same time. "
            "Window will be created after calling addSceneToWindow()."
        )
        logger.info(msg)
    
    def __getSceneIndex(self, sceneName):
        for index, scene in enumerate(self.sceneList):
            if scene.name == sceneName:
                return index
        return -1
    
    def addSceneToWindow(self, sceneName, wid):
        assert all(isinstance(name, str) for name in [sceneName, wid]), \
            "Parameters 'sceneName' and 'wid' must be strings"
        
        index = self.__getSceneIndex(sceneName)
        if index == -1:
            logger.error(f"addSceneToWindow(): Unknown sceneName '{sceneName}'.")
            return False
        elif wid not in self.windowList:
            logger.error(f"addSceneToWindow(): Unknown windowName '{wid}'.")
            return False
    
        rec = rr.new_recording(application_id=wid, recording_id=sceneName, spawn=True)
        self.sceneList[index].setRec(rec)
        return True
    
    def __parse_entity(self, entityName, entity, entityType):
        """
        Parse entity name and log (or not) entity :
            - if there is a scene specified in entityName :  <scene>/name
                it will log directly the entity into the scene
            - if there is a '/' : <not a scene>/name
                it will need addToGroup() to be log in a scene
                every '/' will interpreted as a tree
            - if there is no '/', entity will require addToGroup() to be logged
        """
        assert entity is not None, "__parse_entity(): 'entity' must not be None"
        assert isinstance(entityType, Archetype), \
            "__parse_entity(): 'entityType' must be of type `enum Archetype`"
        
        charIndex = entityName.find('/')
        # if '/' in entityName then search for the scene in self.sceneList
        if charIndex != -1 and charIndex != len(entityName) - 1:
            sceneIndex = self.__getSceneIndex(entityName[:charIndex])
            if sceneIndex != -1:
                entity = Entity(entityName[charIndex + 1:], entity)
                self.entityList[entityType.value].append(entity)
                if entityType != Archetype.MESH_FROM_PATH:
                    rr.log(entityName[charIndex:], entity.archetype, recording=self.sceneList[sceneIndex].rec)
                else:
                    rr.log_file_from_path(file_path=entity.archetype.path)
                msg = (
                    f"__parse_entity() creates a {entityType.name} for '{entityName}', "
                    f"and logs it directly to '{self.sceneList[sceneIndex].name}' scene."
                )
                logger.info(msg)
                return
        # put entity to entityList, wait for addToGroup() to be logged
        entity = Entity(entityName, entity)
        self.entityList[entityType.value].append(entity)
        msg = (
            f"__parse_entity() does not create a {entityType.name} for '{entityName}', "
                "it will be created when added to a group with addToGroup()."
        )
        logger.info(msg)
    
    def __get_entity(self, entityName):
        for entity_list in self.entityList:
            for entity in entity_list:
                if entity.name == entityName:
                    return entity
        return None
    
    def addFloor(self, floorName):
        assert isinstance(floorName, str), "Parameter 'floorName' must be a string"
        
        floor = rr.Boxes3D(
            sizes=[[200, 200, 0.5]],
            colors=[(125, 125, 125)],
            fill_mode="Solid",
        )
        self.__parse_entity(floorName, floor, Archetype.BoxeS3D)
        return True
    
    def addBox(self, boxName, boxSize1, boxSize2, boxSize3, RGBAcolor):
        assert isinstance(boxName, str), "Parameter 'boxName' must be a string"
        assert all(isinstance(x, (int, float)) for x in [boxSize1, boxSize2, boxSize3]), \
            "Parameters 'boxSize' must be a numbers"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"
        
        box = rr.Boxes3D(
            sizes=[[boxSize1, boxSize2, boxSize3]],
            colors=[RGBAcolor],
            fill_mode="Solid",
            labels=[boxName],
        )
        self.__parse_entity(boxName, box, Archetype.BoxeS3D)
        return True

    def addArrow(self, name, radius, length, RGBAcolor):
        assert isinstance(name, str), "Parameter 'name' must be a string"
        assert all(isinstance(x, (int, float)) for x in [radius, length]), \
            "Parameters 'radius' and 'length' must be a numbers"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"
        
        angle = np.arange(start=0, stop=tau, step=tau)
        arrow = rr.Arrows3D(
            radii=[[radius]],
            vectors  = np.column_stack([np.sin(angle) * length, np.zeros(1), np.cos(angle) * length]),
            colors=[RGBAcolor],
            labels=[name],
        )
        self.__parse_entity(name, arrow, Archetype.ARROWS3D)
        return True
    
    def addCapsule(self, name, radius, height, RGBAcolor):
        assert isinstance(name, str), "Parameter 'name' must be a string"
        assert all(isinstance(x, (int, float)) for x in [radius, height]), \
            "Parameters 'radius' and 'height must be a numbers"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"
        
        capsule = rr.Capsules3D(
            lengths=[height],
            radii=[radius],
            colors=[RGBAcolor]
        )
        self.__parse_entity(name, capsule, Archetype.CAPSULES3D)
        return True
    
    def addLine(self, lineName, pos1, pos2, RGBAcolor):
        assert isinstance(lineName, str), "Parameter 'lineName' must be a string"
        assert all(isinstance(x, (list, tuple)) for x in [pos1, pos2]), \
            "Parameters 'pos1' and 'pos2' must be a list or tuple of numbers"
        assert all(isinstance(nb, (int, float)) for x in [pos1, pos2] for nb in x), \
            "Parameters 'pos1' and 'pos2' must be a list or tuple of numbers"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"
        
        line = rr.LineStrips3D(
            [[pos1, pos2]],
            radii=[0.1],
            colors=[RGBAcolor],
            labels=[lineName],
        )
        self.__parse_entity(lineName, line, Archetype.LINESTRIPS3D)
        return True
    
    def addSquareFace(self, faceName, pos1, pos2, pos3, pos4, RGBAcolor):
        assert isinstance(faceName, str), "Parameter 'faceName' must be a string"
        assert all(isinstance(x, (list, tuple)) for x in [pos1, pos2, pos3, pos4]), \
            "Parameters 'pos' must be a list or tuple of numbers"
        assert all(isinstance(nb, (int, float)) for x in [pos1, pos2, pos3, pos4] for nb in x), \
            "Parameters 'pos' must be a list or tuple of numbers"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"
        
        mesh = rr.Mesh3D(
            vertex_positions=[pos1, pos2, pos3, pos4],
            triangle_indices=[[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
            vertex_colors=[RGBAcolor],
        )
        self.__parse_entity(faceName, mesh, Archetype.MESH3D)
        return True
    
    def addTriangleFace(self, faceName, pos1, pos2, pos3, RGBAcolor):
        assert isinstance(faceName, str), "Parameter 'faceName' must be a string"
        assert all(isinstance(x, (list, tuple)) for x in [pos1, pos2, pos3]), \
            "Parameters 'pos' must be a list or tuple of numbers"
        assert all(isinstance(nb, (int, float)) for x in [pos1, pos2, pos3] for nb in x), \
            "Parameters 'pos' must be a list or tuple of numbers"
        assert all(len(x) == 3 for x in [pos1, pos2, pos3]), "Parameter 'pos' must be of length 3"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"

        mesh = rr.Mesh3D(
            vertex_positions=[pos1, pos2, pos3],
            vertex_colors=[RGBAcolor],
        )
        
        self.__parse_entity(faceName, mesh, Archetype.MESH3D)
        return True
    
    def addSphere(self, sphereName, radius, RGBAcolor):
        assert isinstance(sphereName, str), "Parameter 'sphereName' must be a string"
        assert isinstance(radius, (int, float)), "Parameters 'radius' and 'length' must be a numbers"
        assert isinstance(RGBAcolor, (list, tuple)), "Parameter 'RGBAcolor' must be a list or tuple"
        
        sphere = rr.Points3D(
            positions = [[0.0, 0.0, 0.0]],
            radii=[[radius]],
            colors=[RGBAcolor],
            labels=[sphereName],
        )
        self.__parse_entity(sphereName, sphere, Archetype.POINTS3D)
        return True
    
    def __getRecording(self, recName):
        return next((scene.rec for scene in self.sceneList if scene.name == recName), None)
    
    def __log_archetype(self, entityName, groupName):
        entity = self.__get_entity(entityName)
        rec = self.__getRecording(groupName)
        
        if type(entity.archetype) == MeshFromPath:
            rr.log_file_from_path(file_path=entity.archetype.path)
            logger.info(f"Logging Mesh from file named '{entity.name}'.")
            return True
        elif type(entity.archetype) == rr.archetypes.arrows3d.Arrows3D:
            logger.info(f"Logging Arrows3D named '{entity.name}'.")
        elif type(entity.archetype) == rr.archetypes.boxes3d.Boxes3D:
            logger.info(f"Logging Boxes3D named '{entity.name}'.")
        elif type(entity.archetype) == rr.archetypes.capsules3d.Capsules3D:
            logger.info(f"Logging Capsules3D named '{entity.name}'.")
        elif type(entity.archetype) == rr.archetypes.line_strips3d.LineStrips3D:
            logger.info(f"Logging LineStrip3D named '{entity.name}'.")
        elif type(entity.archetype) == rr.archetypes.mesh3d.Mesh3D:
            logger.info(f"Logging Mesh3D named '{entity.name}'.")
        elif type(entity.archetype) == rr.archetypes.points3d.Points3D:
            logger.info(f"Logging Points3D named '{entity.name}'.")
        else:
            return False
        rr.log(
            entity.name,
            entity.archetype,
            recording=rec,
        )
        return True
    
    def addToGroup(self, nodeName, groupName):
        """
        Actual log of an entity
        """
        assert all(isinstance(name, str) for name in [nodeName, groupName]), \
            "Parameters 'nodeName' and 'groupName' must be strings"
        
        if self.__getSceneIndex(groupName) == -1:
            logger.error(f"addToGroup(): Scene '{groupName}' does not exists.")
            return False
        if not self.__get_entity(nodeName):
            logger.error(f"addToGroup(): Entity '{nodeName}' does not exists.")
            return False
        return self.__log_archetype(nodeName, groupName)
