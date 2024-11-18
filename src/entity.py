class Entity:
    def __init__(self, name, archetype):
        self.name = name
        self.archetype = archetype

class MeshFromPath:
    def __init__(self, path):
        self.path = path