#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import bpy


# FEATURE: Toggle Wire Display
class AMTH_OBJECT_OT_wire_toggle(bpy.types.Operator):

    """Turn on/off wire display on mesh objects"""
    bl_idname = "object.amth_wire_toggle"
    bl_label = "Display Wireframe"
    bl_options = {"REGISTER", "UNDO"}

    clear = bpy.props.BoolProperty(
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


def ui_object_wire_toggle(self, context):

    scene = context.scene

    self.layout.separator()
    col = self.layout.column(align=True)
    col.label(text="Wireframes:")
    row = col.row(align=True)
    row.operator(AMTH_OBJECT_OT_wire_toggle.bl_idname,
                 icon="MOD_WIREFRAME", text="Display").clear = False
    row.operator(AMTH_OBJECT_OT_wire_toggle.bl_idname,
                 icon="X", text="Clear").clear = True
    col.separator()
    row = col.row(align=True)
    row.prop(scene, "amth_wire_toggle_edges_all")
    row.prop(scene, "amth_wire_toggle_optimal")
    row = col.row(align=True)
    sub = row.row(align=True)
    sub.active = not scene.amth_wire_toggle_scene_all
    sub.prop(scene, "amth_wire_toggle_is_selected")
    sub = row.row(align=True)
    sub.active = not scene.amth_wire_toggle_is_selected
    sub.prop(scene, "amth_wire_toggle_scene_all")


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
        name="Subsurf Optimal Display",
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


def register():
    init_properties()
    bpy.utils.register_class(AMTH_OBJECT_OT_wire_toggle)
    bpy.types.VIEW3D_PT_view3d_display.append(ui_object_wire_toggle)


def unregister():
    bpy.utils.unregister_class(AMTH_OBJECT_OT_wire_toggle)
    bpy.types.VIEW3D_PT_view3d_display.remove(ui_object_wire_toggle)
    clear_properties()
