class Scene:
    def __init__(self, name, rec=None):
        self.name = name
        self.rec = rec
    
    def setRec(self, rec):
        self.rec = rec