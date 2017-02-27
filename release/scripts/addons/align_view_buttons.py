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

# This is the Bforartists version of the script that uses the internal Bforartists icons. 
#It will not work in Blender since the icons doesn't exist there.

import bpy


bl_info = {
    "name": "Align View Buttons",
    "author": "Reiner 'Tiles' Prokein",
    "version": (1, 0, 0),
    "blender": (2, 76, 0),
    "location": "Header of the 3D View",
    "description": "Adds a tab button row in the header of the 3D View to switch between views",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"}
    
class VIEW3D_MT_switchactivecamto(bpy.types.Operator):
    """Set Active Camera\nSets the current selected camera as the active camera to render from\nYou need to have a camera object selected"""
    bl_idname = "view3d.switchactivecamto"
    bl_label = "Set active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 

        context = bpy.context
        scene = context.scene
        if context.active_object is not None:
            currentCameraObj = bpy.data.objects[bpy.context.active_object.name]
            scene.camera = currentCameraObj     
        return {'FINISHED'} 


def align_view_buttons(self, context):
    layout = self.layout

    obj = context.active_object
    row = layout.row(align=True)
    
    row = layout.row(align=True)          
    
    row.operator("view3d.viewnumpad", text="", icon ="VIEW_FRONT").type = 'FRONT'
    row.operator("view3d.viewnumpad", text="", icon ="VIEW_BACK").type = 'BACK'
    row.operator("view3d.viewnumpad", text="", icon ="VIEW_RIGHT").type = 'RIGHT'
    row.operator("view3d.viewnumpad", text="", icon ="VIEW_LEFT").type = 'LEFT'
    row.operator("view3d.viewnumpad", text="", icon ="VIEW_TOP").type = 'TOP'
    row.operator("view3d.viewnumpad", text="", icon ="VIEW_BOTTOM").type = 'BOTTOM'
    
    row = layout.row(align=True)
    
    row.operator("view3d.viewnumpad", text="", icon = 'VIEW_SWITCHTOCAM').type = 'CAMERA'

    row = layout.row(align=True)

    # Set active camera. Just enabled when a camera object is selected.
    if obj is not None:

        obj_type = obj.type

        if obj_type == 'CAMERA':

            row.operator("view3d.switchactivecamto", text="", icon ="VIEW_SWITCHACTIVECAM")
   
        else:
                    
            row.enabled = False
            row.operator("view3d.switchactivecamto", text="", icon ="VIEW_SWITCHACTIVECAM")

    else:
        row.enabled = False
        row.operator("view3d.switchactivecamto", text="", icon ="VIEW_SWITCHACTIVECAM")


def register():

    bpy.types.VIEW3D_HT_header.append(align_view_buttons) # Here we add our button in the View 3D header. 
    
    bpy.utils.register_class(VIEW3D_MT_switchactivecamto)
    
def unregister():

    bpy.utils.unregister_class(VIEW3D_MT_switchactivecamto)

     
# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.

if __name__ == "__main__":
    register()