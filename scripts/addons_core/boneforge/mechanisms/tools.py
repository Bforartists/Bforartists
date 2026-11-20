"""Build Mechanism: the guided joint/link build as a 3D Viewport tool (UI critique, 2026-10-10).

Gesture first: with the tool active, a click on a part starts a joint or link of the type chosen in the
tool header, and that click is its first pick; the guided build then asks for the rest in the viewport.
The sidebar's Add Joint / Add Link menus still work.
"""
import bpy

from boneforge.i18n import T
from boneforge.mechanisms import records


class BC_WT_build_mechanism(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "boneforge.build_mechanism"
    bl_label = "Build Mechanism"
    bl_description = "Click a part to start a joint or link of the type chosen in the tool header"
    bl_icon = "ops.armature.extrude_cursor"
    bl_keymap = (
        ("boneforge.mech_guide", {"type": 'LEFTMOUSE', "value": 'PRESS'},
         {"properties": [("from_tool", True)]}),                   # the type comes from the tool header
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties("boneforge.mech_guide")
        layout.prop(props, "type", text="")
        if records.active_rig(context) is None:
            layout.label(text=T("Select a mechanism rig or one of its parts"))


class BC_WT_build_mechanism_pose(BC_WT_build_mechanism):
    bl_context_mode = 'POSE'


TOOLS = (BC_WT_build_mechanism, BC_WT_build_mechanism_pose)


def register():
    from boneforge.core import toolbar
    for tool in TOOLS:
        # Keep the separator outside native groups so their tools remain safe to cycle.
        toolbar.register(tool, separator=True, group=False)


def unregister():
    from boneforge.core import toolbar
    for tool in reversed(TOOLS):
        toolbar.unregister(tool)
