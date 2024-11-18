from src.client import Client
import rerun as rr
import logging


def main():
    logging.basicConfig(filename='client.log', level=logging.DEBUG, filemode="w")
    rec = Client()
    rec.gui.createWindow("w1")
    rec.gui.createScene("s1")
    rec.gui.addSceneToWindow("sb1", "w1")
    
    # rec.gui.createWindow("w2")
    # rec.gui.createScene("s2")
    # rec.gui.addSceneToWindow("s2", "w2")
    
    rec.gui.addArrow("arr", 0.5, 5, [100, 0, 50, 255])
    rec.gui.addToGroup("arr", "s1")
    # rec.gui.addBox("s1/box", 2, 2, 2, [255, 0, 0, 255])
    # rec.gui.addCapsule("cap", 0.5, 5, [100, 0,155, 255])
    # rec.gui.addLine("line", (0.5, 1, 1), (1, 4, 5), [100, 0,155, 255])
    # rec.gui.addSquareFace("sq", (1,1,1), (2,6,2), (3,2,3), (5,4,4), [25, 50, 130, 255])
    # rec.gui.addTriangleFace("sq", (1,1,1), (2,6,2), (3,2,3), [25, 50, 130, 255])
    
    # rec.gui.addMesh("s1/mesh", "/home/kgoddard/rerun_models/cube.stl")
    
    # rec.gui.addFloor("ok/floor")
    # rec.gui.addSphere("sp", 2, [62, 255, 20, 255])
    # rec.gui.addToGroup("sp", "s1")
    # rec.gui.addToGroup("sp", "s1")
    


if __name__ == "__main__":
    main()

# rec = rr.new_recording(application_id="My window", recording_id="My rec", spawn=True)
# rr.log_file_from_path(file_path="/home/kgoddard/rerun_models/cube.stl", recording=rec)
