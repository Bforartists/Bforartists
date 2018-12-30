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
    "version": (5, 8, 27),
    "blender": (2, 80, 0),
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
        addon_prefs = context.preferences.addons["mesh_snap_utilities_line"].preferences

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
        #widget="MESH_GGT_mouse_point",
        operator="mesh.make_line",
        keymap="3D View Tool: Edit Mesh, Make Line",
        draw_settings=draw_settings,
    )


# -----------------------------------------------------------------------------
# Tool Registraion

def km_3d_view_tool_make_line(tool_mouse = 'LEFTMOUSE'):
    return [(
        "3D View Tool: Edit Mesh, Make Line",
        {"space_type": 'VIEW_3D', "region_type": 'WINDOW'},
        {"items": [
            ("mesh.make_line", {"type": tool_mouse, "value": 'CLICK'}, None),
        ]},
    )]


def get_tool_list(space_type, context_mode):
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
    return cls._tools[context_mode]


def register_make_line_tool():
    tools = get_tool_list('VIEW_3D', 'EDIT_MESH')

    for index, tool in enumerate(tools, 1):
        if isinstance(tool, ToolDef) and tool.text == "Add Cube":
            break

    tools.insert(index, tool_make_line)

    keyconfigs = bpy.context.window_manager.keyconfigs
    kc_defaultconf = keyconfigs.get("blender")
    kc_addonconf   = keyconfigs.get("blender addon")

    # TODO: find the user defined tool_mouse.
    keyconfig_data = km_3d_view_tool_make_line()

    from bl_keymap_utils.io import keyconfig_init_from_data
    keyconfig_init_from_data(kc_defaultconf, keyconfig_data)
    keyconfig_init_from_data(kc_addonconf, keyconfig_data)


def unregister_make_line_tool():
    tools = get_tool_list('VIEW_3D', 'EDIT_MESH')
    tools.remove(tool_make_line)

    km_name, km_args, km_content = km_3d_view_tool_make_line()[0]

    keyconfigs = bpy.context.window_manager.keyconfigs
    defaultmap = keyconfigs.get("blender").keymaps
    addonmap   = keyconfigs.get("blender addon").keymaps

    addonmap.remove(addonmap.find(km_name, **km_args))
    defaultmap.remove(defaultmap.find(km_name, **km_args))


# -----------------------------------------------------------------------------
# Addon Registraion

def register():
    bpy.utils.register_class(preferences.SnapUtilitiesLinePreferences)
    bpy.utils.register_class(common_classes.VIEW3D_OT_rotate_custom_pivot)
    bpy.utils.register_class(common_classes.VIEW3D_OT_zoom_custom_target)
    bpy.utils.register_class(ops_line.SnapUtilitiesLine)
    #bpy.utils.register_class(common_classes.MousePointWidget)
    #bpy.utils.register_class(common_classes.MousePointWidgetGroup)

    register_make_line_tool()


def unregister():
    unregister_make_line_tool()

    #bpy.utils.unregister_class(common_classes.MousePointWidgetGroup)
    #bpy.utils.unregister_class(common_classes.MousePointWidget)
    bpy.utils.unregister_class(ops_line.SnapUtilitiesLine)
    bpy.utils.unregister_class(common_classes.VIEW3D_OT_zoom_custom_target)
    bpy.utils.unregister_class(common_classes.VIEW3D_OT_rotate_custom_pivot)
    bpy.utils.unregister_class(preferences.SnapUtilitiesLinePreferences)


if __name__ == "__main__":
    __name__ = "mesh_snap_utilities_line"
    __package__ = "mesh_snap_utilities_line"
    register()
