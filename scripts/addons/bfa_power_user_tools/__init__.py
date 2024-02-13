# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
        "name": "BFA - Power User Tools",
        "description": "Additional set of user experience tools and operators to assist with every day use.",
        "author": "Andres Stephens (Draise)",
        "version": (0, 2),
        "blender": (4, 00, 0),
        "location": "Varios locations, customize as you need",
        "warning": "This is a Bforartists exclusive addon for the time being", # used for warning icon and text in add-ons panel
        "wiki_url": "",
        "tracker_url": "https://github.com/Draise14/bfa_power_user_tools",
        "support": "COMMUNITY",
        "category": "UI"
        }

import bpy
from . import operators
from . import ui
from . import properties
from . import preferences


op_list = [
    operators.BFA_OT_insertframe_right,
    operators.BFA_OT_insertframe_left,
    # Add more operators as needed
]


def register():
    # Register operators before adding them to the menus
    for operator in op_list:
        bpy.utils.register_class(operator)

    # Register custom menus, do this before filling in operators
    bpy.utils.register_class(ui.BFA_MT_timeline_key)
    bpy.types.TIME_MT_editor_menus.append(ui.BFA_MT_timeline_key.menu_func)

    ## 3D View Editor
    bpy.types.VIEW3D_MT_object_animation.append(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.append(operators.BFA_OT_insertframe_right.menu_func)

    ## Dopesheet Editor
    bpy.types.DOPESHEET_MT_key.append(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.DOPESHEET_MT_key.append(operators.BFA_OT_insertframe_right.menu_func)

    ## Graph Editor
    bpy.types.GRAPH_MT_key.append(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.GRAPH_MT_key.append(operators.BFA_OT_insertframe_right.menu_func)

    ## Timeline Editor
    bpy.types.BFA_MT_timeline_key.append(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.BFA_MT_timeline_key.append(operators.BFA_OT_insertframe_right.menu_func)


    # Register other classes and properties...
    bpy.utils.register_class(preferences.BFA_UI_preferences)
    bpy.utils.register_class(properties.BFA_UI_toggles)

    # Register the toggles
    bpy.types.WindowManager.BFA_UI_addon_props = bpy.props.PointerProperty(type=properties.BFA_UI_toggles)

def unregister():
    # Unregister operators
    for operator in op_list:
        bpy.utils.unregister_class(operator)

    ## 3D View Editor
    bpy.types.VIEW3D_MT_object_animation.remove(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.VIEW3D_MT_object_animation.remove(operators.BFA_OT_insertframe_right.menu_func)

    ## Dopesheet Editor
    bpy.types.DOPESHEET_MT_key.remove(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.DOPESHEET_MT_key.remove(operators.BFA_OT_insertframe_right.menu_func)

    ## Graph Editor
    bpy.types.GRAPH_MT_key.remove(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.GRAPH_MT_key.remove(operators.BFA_OT_insertframe_right.menu_func)

    ## Timeline Editor
    bpy.types.BFA_MT_timeline_key.remove(operators.BFA_OT_insertframe_left.menu_func)
    bpy.types.BFA_MT_timeline_key.remove(operators.BFA_OT_insertframe_right.menu_func)

    # Unregister other classes and properties...
    bpy.utils.unregister_class(preferences.BFA_UI_preferences)
    bpy.utils.unregister_class(properties.BFA_UI_toggles)

    # Unregister custom menus, notice this comes last. First unregister operators, then menus
    bpy.utils.unregister_class(ui.BFA_MT_timeline_key)
    bpy.types.TIME_MT_editor_menus.remove(ui.BFA_MT_timeline_key.menu_func)

    # Unregister the toggles
    del bpy.types.WindowManager.BFA_UI_addon_props

if __name__ == "__main__":
    register()
