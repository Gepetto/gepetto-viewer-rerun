from src.gepetto_viewer_rerun.client import Client
import logging

logging.basicConfig(filename='basic_geometries.log', filemode='w', level=logging.DEBUG)

rec = Client()
rec.gui.createWindow("w1")
rec.gui.createScene("s1")
rec.gui.addSceneToWindow("s1", "w1")

rec.gui.addBox("s1/box", 2, 2, 2, [255, 0, 0, 255])

rec.gui.addArrow("arrow", 0.5, -5, [100, 0, 50, 255])
rec.gui.addToGroup("arrow", "s1")

rec.gui.addCapsule("capsule", 0.5, 5, [100, 0,155, 255])
rec.gui.addToGroup("capsule", "s1")

rec.gui.addLine("s1/line", (-5, -2, -4), (9, 4, -5), [100, 0,155, 255])

rec.gui.addSquareFace("square", (-4, 0, 1), (2, 6, 2), (3, 2, 3), (5, 4, 4), [25, 50, 130, 255])
rec.gui.addTriangleFace("triangle", (5, 3, 1), (8, 6, -2), (5, 2, 3), [70, 30, 130, 255])
rec.gui.addToGroup("square", "s1")
rec.gui.addToGroup("triangle", "s1")

rec.gui.addSphere("s1/sphere", 2, [62, 255, 20, 255])
