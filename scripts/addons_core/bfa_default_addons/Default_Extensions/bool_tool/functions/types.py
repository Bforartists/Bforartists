import bpy
from mathutils import Vector, Matrix


#### ------------------------------ CLASSES ------------------------------ ####

class Ray:
    """Class object for storing raycast results."""

    def __init__(self,
                 hit: bool,
                 location: Vector,
                 normal: Vector,
                 index: int,
                 obj,
                 matrix: Matrix):
        self.hit = hit
        self.location = location
        self.normal = normal
        self.index = index
        self.obj = obj
        self.matrix = matrix
