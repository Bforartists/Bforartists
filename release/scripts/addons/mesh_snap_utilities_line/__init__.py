### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Contact for more information about the Addon:
# Email:    germano.costa@ig.com.br
# Twitter:  wii_mano @mano_wii

bl_info = {
    "name": "Snap_Utilities_Line",
    "author": "Germano Cavalcante",
    "version": (5, 8, 24),
    "blender": (0, 0, 0),
    "location": "View3D > TOOLS > Make Line",
    "description": "Extends Blender Snap controls",
    #"wiki_url" : "http://blenderartists.org/forum/showthread.php?363859-Addon-CAD-Snap-Utilities",
    "category": "Mesh"}

if "bpy" in locals():
    import importlib
    importlib.reload(preferences)
    importlib.reload(ops_line)
    importlib.reload(common_classes)
else:
    from . import preferences
    from . import ops_line

import bpy
from bpy.utils.toolsystem import ToolDef

@ToolDef.from_fn
def tool_make_line():
    import os
    def draw_settings(context, layout, tool):
        addon_prefs = context.user_preferences.addons["mesh_snap_utilities_line"].preferences

        layout.prop(addon_prefs, "incremental")
        layout.prop(addon_prefs, "increments_grid")
        if addon_prefs.increments_grid:
            layout.prop(addon_prefs, "relative_scale")
        layout.prop(addon_prefs, "create_face")
        layout.prop(addon_prefs, "outer_verts")
        #props = tool.operator_properties("mesh.snap_utilities_line")
        #layout.prop(props, "radius")

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    return dict(
        text="Make Line",
        description=(
            "Make Lines\n"
            "Connect them to split faces"
        ),
        icon=os.path.join(icons_dir, "ops.mesh.make_line"),
#        widget="MESH_GGT_mouse_point",
        operator="mesh.make_line",
        keymap=(
            ("mesh.make_line", dict(type='LEFTMOUSE', value='PRESS'), None),
        ),
        draw_settings=draw_settings,
    )


def register():
    def get_tool_list(space_type, context_mode):
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
        return cls._tools[context_mode]

    bpy.utils.register_class(preferences.SnapUtilitiesLinePreferences)
    bpy.utils.register_class(common_classes.VIEW3D_OT_rotate_custom_pivot)
    bpy.utils.register_class(common_classes.VIEW3D_OT_zoom_custom_target)
    bpy.utils.register_class(ops_line.SnapUtilitiesLine)
#    bpy.utils.register_class(common_classes.MousePointWidget)
#    bpy.utils.register_class(common_classes.MousePointWidgetGroup)

    bpy.utils.register_tool('VIEW_3D', 'EDIT_MESH', tool_make_line)

    # Move tool to after 'Add Cube'
    tools = get_tool_list('VIEW_3D', 'EDIT_MESH')
    for index, tool in enumerate(tools):
        if isinstance(tool, ToolDef) and tool.text == "Add Cube":
            break
    tools.insert(index + 1, tools.pop(-1))

def unregister():
    bpy.utils.unregister_tool('VIEW_3D', 'EDIT_MESH', tool_make_line)

#    bpy.utils.unregister_class(common_classes.MousePointWidgetGroup)
#    bpy.utils.unregister_class(common_classes.MousePointWidget)
    bpy.utils.unregister_class(ops_line.SnapUtilitiesLine)
    bpy.utils.unregister_class(common_classes.VIEW3D_OT_zoom_custom_target)
    bpy.utils.unregister_class(common_classes.VIEW3D_OT_rotate_custom_pivot)
    bpy.utils.unregister_class(preferences.SnapUtilitiesLinePreferences)

if __name__ == "__main__":
    __name__ = "mesh_snap_utilities_line"
    __package__ = "mesh_snap_utilities_line"
    register()
