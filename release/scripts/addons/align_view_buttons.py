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

# This is the Bforartists 2 version of the script that uses the internal Bforartists icons. 
#It will not work in Blender since the icons doesn't exist there.

import bpy

bl_info = {
    "name": "Align View Buttons",
    "author": "Reiner 'Tiles' Prokein",
    "version": (1, 1, 0),
    "blender": (2, 80, 0),
    "location": "Header of the 3D View",
    "description": "Adds a tab button row in the header of the 3D View to switch between views",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"}

def align_view_buttons(self, context):
    layout = self.layout
    
    row = layout.row(align=True)          
    
    row.operator("view3d.view_axis", text="", icon ="VIEW_FRONT").type = 'FRONT'
    row.operator("view3d.view_axis", text="", icon ="VIEW_BACK").type = 'BACK'
    row.operator("view3d.view_axis", text="", icon ="VIEW_RIGHT").type = 'RIGHT'
    row.operator("view3d.view_axis", text="", icon ="VIEW_LEFT").type = 'LEFT'
    row.operator("view3d.view_axis", text="", icon ="VIEW_TOP").type = 'TOP'
    row.operator("view3d.view_axis", text="", icon ="VIEW_BOTTOM").type = 'BOTTOM'


def register():

    bpy.types.VIEW3D_HT_header.append(align_view_buttons) # Here we add our button in the View 3D header. 

def unregister():

    bpy.types.VIEW3D_HT_header.remove(align_view_buttons)
     
# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.

if __name__ == "__main__":
    register()