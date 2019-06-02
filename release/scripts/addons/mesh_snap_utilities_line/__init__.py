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
    "version": (5, 9, 15),
    "blender": (2, 80, 0),
    "location": "View3D > TOOLS > Line Tool",
    "description": "Extends Blender Snap controls",
    "wiki_url" : "https://blenderartists.org/t/cad-snap-utilities",
    "category": "Mesh"}

if "bpy" in locals():
    import importlib
    importlib.reload(navigation_ops)
    importlib.reload(widgets)
    importlib.reload(preferences)
    importlib.reload(op_line)
    importlib.reload(keys)
else:
    from . import navigation_ops
    from . import widgets
    from . import preferences
    from . import op_line
    from . import keys

import bpy
from bpy.utils.toolsystem import ToolDef

if not __package__:
    __package__ = "mesh_snap_utilities_line"

@ToolDef.from_fn
def tool_line():
    import os
    def draw_settings(context, layout, tool):
        addon_prefs = context.preferences.addons[__package__].preferences

        layout.prop(addon_prefs, "incremental")
        layout.prop(addon_prefs, "increments_grid")
        layout.prop(addon_prefs, "intersect")
        layout.prop(addon_prefs, "create_face")
        if context.mode == 'EDIT_MESH':
            layout.prop(addon_prefs, "outer_verts")
        #props = tool.operator_properties("mesh.snap_utilities_line")
        #layout.prop(props, "radius")

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    return dict(
        idname="snap_utilities.line",
        label="Make Line",
        description=(
            "Make Lines\n"
            "Connect them to split faces"
        ),
        icon=os.path.join(icons_dir, "ops.mesh.snap_utilities_line"),
        widget="MESH_GGT_snap_point",
        #operator="mesh.snap_utilities_line",
        keymap=keys.km_tool_snap_utilities_line,
        draw_settings=draw_settings,
    )


# -----------------------------------------------------------------------------
# Tool Registraion


def get_tool_list(space_type, context_mode):
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
    return cls._tools[context_mode]


def register_snap_tools():
    tools = get_tool_list('VIEW_3D', 'EDIT_MESH')

    for index, tool in enumerate(tools, 1):
        if isinstance(tool, ToolDef) and tool.label == "Measure":
            break

    tools[:index] += None, tool_line

    del tools


def unregister_snap_tools():
    tools = get_tool_list('VIEW_3D', 'EDIT_MESH')

    index = tools.index(tool_line) - 1 #None
    tools.pop(index)
    tools.remove(tool_line)

    del tools
    del index


def register_keymaps():
    keyconfigs = bpy.context.window_manager.keyconfigs
    kc_defaultconf = keyconfigs.default
    kc_addonconf   = keyconfigs.addon

    # TODO: find the user defined tool_mouse.
    from bl_keymap_utils.io import keyconfig_init_from_data
    keyconfig_init_from_data(kc_defaultconf, keys.generate_empty_snap_utilities_tools_keymaps())
    keyconfig_init_from_data(kc_addonconf, keys.generate_snap_utilities_keymaps())

    #snap_modalkeymap = kc_addonconf.keymaps.find(keys.km_snap_utilities_modal_keymap)
    #snap_modalkeymap.assign("MESH_OT_snap_utilities_line")


def unregister_keymaps():
    keyconfigs = bpy.context.window_manager.keyconfigs
    defaultmap = keyconfigs.get("blender").keymaps
    addonmap   = keyconfigs.get("blender addon").keymaps

    for keyconfig_data in keys.generate_snap_utilities_keymaps():
        km_name, km_args, km_content = keyconfig_data
        addonmap.remove(addonmap.find(km_name, **km_args))

    for keyconfig_data in keys.generate_empty_snap_utilities_tools_keymaps():
        km_name, km_args, km_content = keyconfig_data
        defaultmap.remove(defaultmap.find(km_name, **km_args))


# -----------------------------------------------------------------------------
# Addon Registraion

classes = (
    preferences.SnapUtilitiesPreferences,
    op_line.SnapUtilitiesLine,
    navigation_ops.VIEW3D_OT_rotate_custom_pivot,
    navigation_ops.VIEW3D_OT_zoom_custom_target,
    widgets.SnapPointWidget,
    widgets.SnapPointWidgetGroup,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    register_snap_tools()
    register_keymaps()


def unregister():
    unregister_keymaps()
    unregister_snap_tools()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
