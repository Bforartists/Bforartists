# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

class AMTH_VIEW3D_PT_wire_toggle(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Wireframes "
    bl_parent_id = "VIEW3D_PT_view3d_properties"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        scene = context.scene

        row = layout.row(align=True)
        row.operator(AMTH_OBJECT_OT_wire_toggle.bl_idname,
                    icon="MOD_WIREFRAME", text="Display").clear = False
        row.operator(AMTH_OBJECT_OT_wire_toggle.bl_idname,
                    icon="X", text="Clear").clear = True

        layout.separator()

        col = layout.column(heading="Display", align=True)
        col.prop(scene, "amth_wire_toggle_edges_all")
        col.prop(scene, "amth_wire_toggle_optimal")

        col = layout.column(heading="Apply to", align=True)
        sub = col.row(align=True)
        sub.active = not scene.amth_wire_toggle_scene_all
        sub.prop(scene, "amth_wire_toggle_is_selected")
        sub = col.row(align=True)
        sub.active = not scene.amth_wire_toggle_is_selected
        sub.prop(scene, "amth_wire_toggle_scene_all")


# FEATURE: Toggle Wire Display
class AMTH_OBJECT_OT_wire_toggle(bpy.types.Operator):

    """Turn on/off wire display on mesh objects"""
    bl_idname = "object.amth_wire_toggle"
    bl_label = "Display Wireframe"
    bl_options = {"REGISTER", "UNDO"}

    clear: bpy.props.BoolProperty(
        default=False, name="Clear Wireframe",
        description="Clear Wireframe Display")

    def execute(self, context):

        scene = context.scene
        is_all_scenes = scene.amth_wire_toggle_scene_all
        is_selected = scene.amth_wire_toggle_is_selected
        is_all_edges = scene.amth_wire_toggle_edges_all
        is_optimal = scene.amth_wire_toggle_optimal
        clear = self.clear

        if is_all_scenes:
            which = bpy.data.objects
        elif is_selected:
            if not context.selected_objects:
                self.report({"INFO"}, "No selected objects")
            which = context.selected_objects
        else:
            which = scene.objects

        if which:
            for ob in which:
                if ob and ob.type in {
                        "MESH", "EMPTY", "CURVE",
                        "META", "SURFACE", "FONT"}:

                    ob.show_wire = False if clear else True
                    ob.show_all_edges = is_all_edges

                    for mo in ob.modifiers:
                        if mo and mo.type == "SUBSURF":
                            mo.show_only_control_edges = is_optimal

        return {"FINISHED"}


def init_properties():
    scene = bpy.types.Scene
    scene.amth_wire_toggle_scene_all = bpy.props.BoolProperty(
        default=False,
        name="All Scenes",
        description="Toggle wire on objects in all scenes")
    scene.amth_wire_toggle_is_selected = bpy.props.BoolProperty(
        default=False,
        name="Only Selected Objects",
        description="Only toggle wire on selected objects")
    scene.amth_wire_toggle_edges_all = bpy.props.BoolProperty(
        default=True,
        name="Draw All Edges",
        description="Draw all the edges even on coplanar faces")
    scene.amth_wire_toggle_optimal = bpy.props.BoolProperty(
        default=False,
        name="Optimal Display Subdivision",
        description="Skip drawing/rendering of interior subdivided edges "
                    "on meshes with Subdivision Surface modifier")


def clear_properties():
    props = (
        'amth_wire_toggle_is_selected',
        'amth_wire_toggle_scene_all',
        "amth_wire_toggle_edges_all",
        "amth_wire_toggle_optimal"
    )
    wm = bpy.context.window_manager
    for p in props:
        if p in wm:
            del wm[p]

# //FEATURE: Toggle Wire Display

classes = (
    AMTH_VIEW3D_PT_wire_toggle,
    AMTH_OBJECT_OT_wire_toggle
)

def register():
    init_properties()

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    clear_properties()

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
