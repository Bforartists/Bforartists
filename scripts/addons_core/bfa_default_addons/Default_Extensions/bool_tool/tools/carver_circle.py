import bpy
import os

from ..constants import (
    ICONS_PATH,
)

from .common.ui import (
    carver_ui_common,
)
from .carver_box import OBJECT_OT_carve_box


description = "Cut primitive shapes into mesh objects with brush"

#### ------------------------------ TOOLS ------------------------------ ####

class OBJECT_WT_carve_circle(bpy.types.WorkSpaceTool):
    bl_idname = "object.carve_circle"
    bl_label = "Circle Carve"
    bl_description = description

    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_icon = os.path.join(ICONS_PATH, "dat", "ops.object.carver_circle")
    bl_keymap = (
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "alt": True}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "alt": True}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "alt": True}, {"properties": None}),
        ("object.carve_circle", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "ctrl": True, "shift": True, "alt": True}, {"properties": None}),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("object.carve_circle")
        carver_ui_common(context, layout, props)

class MESH_WT_carve_circle(OBJECT_WT_carve_circle):
    bl_context_mode = 'EDIT_MESH'



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_carve_circle(OBJECT_OT_carve_box):
    bl_idname = "object.carve_circle"
    bl_label = "Box Carve"
    bl_description = description

    # SHAPE-properties
    shape = 'CIRCLE'

    # NOTE: There are registered on operator level because they need to be overriden or hidden per-tool.
    subdivision: bpy.props.IntProperty(
        name = "Circle Subdivisions",
        description = "Number of vertices that will make up the circular shape that will be extruded into a cylinder",
        min = 3, soft_max = 128,
        default = 16,
    )
    aspect: bpy.props.EnumProperty(
        name = "Aspect",
        description = "The initial aspect",
        items = (('FREE', "Free", "Use an unconstrained aspect"),
                 ('FIXED', "Fixed", "Use a fixed 1:1 aspect")),
        default = 'FIXED',
    )
    origin: bpy.props.EnumProperty(
        name = "Origin",
        description = "The initial position for placement",
        items = (('EDGE', "Edge", ""),
                 ('CENTER', "Center", "")),
        default = 'CENTER',
    )



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    OBJECT_OT_carve_circle,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
