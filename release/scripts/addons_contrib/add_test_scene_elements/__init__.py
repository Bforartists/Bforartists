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
# by meta-androcto #

bl_info = {
    "name": "Test Scene, Light, Camera",
    "author": "Meta Androcto",
    "version": (0, 2),
    "blender": (2, 77, 0),
    "location": "View3D > Add > Scene Elements",
    "description": "Add Scenes & Lights, Objects.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6"
    "/Py/Scripts",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object"}


if "bpy" in locals():
    import importlib
    importlib.reload(scene_camera)
    importlib.reload(scene_materials)
    importlib.reload(scene_objects)
    importlib.reload(scene_objects_cycles)
    importlib.reload(scene_texture_render)
    importlib.reload(add_light_template)
    importlib.reload(trilighting)
    importlib.reload(camera_turnaround)

else:
    from . import scene_camera
    from . import scene_materials
    from . import scene_objects
    from . import scene_objects_cycles
    from . import scene_texture_render
    from . import add_light_template
    from . import trilighting
    from . import camera_turnaround

import bpy


class INFO_MT_scene_elements_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_scene_elements"
    bl_label = "Test scenes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("camera.add_scene",
                        text="Scene_Camera")
        layout.operator("materials.add_scene",
                        text="Scene_Objects_BI")
        layout.operator("plane.add_scene",
                        text="Scene_Plane")
        layout.operator("objects_cycles.add_scene",
                        text="Scene_Objects_Cycles")
        layout.operator("objects_texture.add_scene",
                        text="Scene_Textures_Cycles")

class INFO_MT_mesh_lamps_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_scene_lamps"
    bl_label = "Lighting Sets"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.add_light_template",
                        text="Add Light Template")
        layout.operator("object.trilighting",
                        text="Add Tri Lighting")

class INFO_MT_mesh_cameras_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_scene_cameras"
    bl_label = "Camera Sets"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.rotate_around",
                        text="Turnaround Camera")

# Define menu
def menu(self, context):

    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'
    self.layout.separator()
    self.layout.menu("INFO_MT_scene_elements", icon="SCENE_DATA")
    self.layout.menu("INFO_MT_scene_lamps", icon="LAMP_SPOT")
    self.layout.menu("INFO_MT_scene_cameras", icon="OUTLINER_DATA_CAMERA")

# Addons Preferences


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.label(text="Lighting Sets:")
        layout.label(text="Spots, Points & Tri Lights")
        layout.label(text="Test Scenes:")
        layout.label(text="Basic pre-built test scenes Cycles & BI")


def register():
    camera_turnaround.register()
    bpy.utils.register_module(__name__)
    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_add.append(menu)
    try:
        bpy.types.VIEW3D_MT_AddMenu.prepend(menu)
    except:
        pass

def unregister():
    camera_turnaround.unregister()
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_add.remove(menu)
    try:
        bpy.types.VIEW3D_MT_AddMenu.remove(menu)
    except:
        pass
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
