import bpy
from .list import list_canvas_cutters


#### ------------------------------ FUNCTIONS ------------------------------ ####

def basic_poll(context):
    if context.mode == 'OBJECT':
        if context.active_object is not None:
            if context.active_object.type == 'MESH':
                return True


def is_canvas(obj):
    if obj.booleans.canvas == False:
        return False
    else:
        cutters, __ = list_canvas_cutters([obj])
        if len(cutters) != 0:
            return True
        else:
            return False
