# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
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
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Cursor Control",
    "author": "Morgan Mörtsell (Seminumerical)",
    "version": (0, 7, 3),
    "blender": (2, 65, 4),
    "location": "View3D > Properties > Cursor",
    "description": "Control the Cursor",
    "warning": "Buggy, may crash other add-ons",
    "wiki_url": "http://blenderpythonscripts.wordpress.com/",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "3D View"}


if "bpy" in locals():
    import importlib
    importlib.reload(data)
    importlib.reload(ui)
    importlib.reload(operators)
    importlib.reload(history)
    importlib.reload(memory)
else:
    from . import data
    from . import ui
    from . import operators
    from . import history
    from . import memory

import bpy
from bpy.props import PointerProperty

from .data import CursorControlData
from .memory import (
    CursorMemoryData,
    VIEW3D_PT_cursor_memory_init,
    VIEW3D_OT_cursor_memory_hide,
    VIEW3D_OT_cursor_memory_recall,
    VIEW3D_OT_cursor_memory_save,
    VIEW3D_OT_cursor_memory_show,
    VIEW3D_OT_cursor_memory_swap,
    VIEW3D_PT_cursor_memory,
    )
from .history import (
    CursorHistoryData,
    cursor_history_draw,
    VIEW3D_PT_cursor_history_init,
    VIEW3D_OT_cursor_history_hide,
    VIEW3D_OT_cursor_history_show,
    VIEW3D_PT_cursor_history,
    VIEW3D_OT_cursor_next,
    VIEW3D_OT_cursor_previous,
    )
from .operators import (
    VIEW3D_OT_ccdelta_add,
    VIEW3D_OT_ccdelta_invert,
    VIEW3D_OT_ccdelta_normalize,
    VIEW3D_OT_ccdelta_sub,
    VIEW3D_OT_ccdelta_vvdist,
    VIEW3D_OT_cursor_stepval_phi,
    VIEW3D_OT_cursor_stepval_phi2,
    VIEW3D_OT_cursor_stepval_phinv,
    VIEW3D_OT_cursor_stepval_vvdist,
    VIEW3D_OT_cursor_to_active_object_center,
    VIEW3D_OT_cursor_to_cylinderaxis,
    VIEW3D_OT_cursor_to_edge,
    VIEW3D_OT_cursor_to_face,
    VIEW3D_OT_cursor_to_line,
    VIEW3D_OT_cursor_to_linex,
    VIEW3D_OT_cursor_to_origin,
    VIEW3D_OT_cursor_to_perimeter,
    VIEW3D_OT_cursor_to_plane,
    VIEW3D_OT_cursor_to_sl,
    VIEW3D_OT_cursor_to_sl_mirror,
    VIEW3D_OT_cursor_to_spherecenter,
    VIEW3D_OT_cursor_to_vertex,
    VIEW3D_OT_cursor_to_vertex_median,
    )
from .ui import (
    CursorControlMenu,
    VIEW3D_PT_ccDelta,
    VIEW3D_PT_cursor,
    menu_callback,
    )


classes = (
    CursorControlData,
    CursorHistoryData,
    CursorMemoryData,

    VIEW3D_PT_cursor_memory_init,
    VIEW3D_PT_cursor_history_init,

    VIEW3D_OT_cursor_memory_hide,
    VIEW3D_OT_cursor_memory_recall,
    VIEW3D_OT_cursor_memory_save,
    VIEW3D_OT_cursor_memory_show,
    VIEW3D_OT_cursor_memory_swap,
    VIEW3D_PT_cursor_memory,

    VIEW3D_OT_cursor_history_hide,
    VIEW3D_OT_cursor_history_show,
    VIEW3D_OT_cursor_next,
    VIEW3D_OT_cursor_previous,
    VIEW3D_PT_cursor_history,

    VIEW3D_OT_ccdelta_add,
    VIEW3D_OT_ccdelta_invert,
    VIEW3D_OT_ccdelta_normalize,
    VIEW3D_OT_ccdelta_sub,
    VIEW3D_OT_ccdelta_vvdist,
    VIEW3D_OT_cursor_stepval_phi,
    VIEW3D_OT_cursor_stepval_phi2,
    VIEW3D_OT_cursor_stepval_phinv,
    VIEW3D_OT_cursor_stepval_vvdist,
    VIEW3D_OT_cursor_to_active_object_center,
    VIEW3D_OT_cursor_to_cylinderaxis,
    VIEW3D_OT_cursor_to_edge,
    VIEW3D_OT_cursor_to_face,
    VIEW3D_OT_cursor_to_line,
    VIEW3D_OT_cursor_to_linex,
    VIEW3D_OT_cursor_to_origin,
    VIEW3D_OT_cursor_to_perimeter,
    VIEW3D_OT_cursor_to_plane,
    VIEW3D_OT_cursor_to_sl,
    VIEW3D_OT_cursor_to_sl_mirror,
    VIEW3D_OT_cursor_to_spherecenter,
    VIEW3D_OT_cursor_to_vertex,
    VIEW3D_OT_cursor_to_vertex_median,

    CursorControlMenu,
    VIEW3D_PT_ccDelta,
    VIEW3D_PT_cursor,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register Cursor Control Structure
    bpy.types.Scene.cursor_control = PointerProperty(
                                        type=CursorControlData,
                                        name=""
                                        )
    bpy.types.Scene.cursor_history = PointerProperty(
                                        type=CursorHistoryData,
                                        name=""
                                        )
    bpy.types.Scene.cursor_memory = PointerProperty(
                                        type=CursorMemoryData,
                                        name=""
                                        )
    # Register menu
    bpy.types.VIEW3D_MT_snap.append(menu_callback)


def unregister():
    history.VIEW3D_PT_cursor_history_init.handle_remove()
    memory.VIEW3D_PT_cursor_memory_init.handle_remove()
    # reset the panel flags if the add-on is toggled off/on
    history.VIEW3D_PT_cursor_history_init.initDone = False
    memory.VIEW3D_PT_cursor_memory_init.initDone = False
    # Unregister menu
    bpy.types.VIEW3D_MT_snap.remove(menu_callback)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.cursor_control
    del bpy.types.Scene.cursor_history
    del bpy.types.Scene.cursor_memory


if __name__ == "__main__":
    register()
