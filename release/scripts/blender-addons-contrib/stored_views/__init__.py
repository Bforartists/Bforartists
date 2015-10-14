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
    "name": "Stored Views",
    "description": "Save and restore User defined views, pov, layers and display configs.",
    "author": "nfloyd",
    "version": (0, 3, 3, 'beta'),
    "blender": (2, 71, 0),
    "location": "View3D > Properties > Stored Views",
    "warning": 'beta release, single view only',
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/3D_interaction/stored_views",
    "tracker_url": "https://developer.blender.org/T27476",
    "category": "3D View"}

# ACKNOWLEDGMENT
# ==============
# import/export functionality is mostly based
#   on Bart Crouch's Theme Manager Addon

# TODO: check against 2.63
# TODO: quadview complete support : investigate. Where's the data?
# TODO: lock_camera_and_layers. investigate usage
# TODO: list reordering

# logging setup
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
hdlr = logging.StreamHandler()
fmtr = logging.Formatter('%(asctime)s %(levelname)s %(name)s : %(funcName)s - %(message)s')
hdlr.setFormatter(fmtr)
logger.addHandler(hdlr)


if "bpy" in locals():
    import imp
    imp.reload(ui)
    imp.reload(properties)
    imp.reload(core)
    imp.reload(operators)
    imp.reload(io)
else:
    #from . import properties, core
    from . import ui, properties, core, operators, io

import bpy
from bpy.props import PointerProperty


class VIEW3D_stored_views_initialize(bpy.types.Operator):
    bl_idname = "view3d.stored_views_initialize"
    bl_label = "Initilize"

    @classmethod
    def poll(cls, context):
        return not hasattr(bpy.types.Scene, 'stored_views')

    def execute(self, context):
        bpy.types.Scene.stored_views = PointerProperty(type=properties.StoredViewsData)
        scenes = bpy.data.scenes
        for scene in scenes:
            core.DataStore.sanitize_data(scene)
        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)
    # Context restricted, need to initialize different (button to be clicked by user)
    #initialize()

def unregister():
    ui.VIEW3D_stored_views_draw.handle_remove(bpy.context)
    bpy.utils.unregister_module(__name__)
    if hasattr(bpy.types.Scene, "stored_views"):
        del bpy.types.Scene.stored_views

if __name__ == "__main__":
    register()
