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

# <pep8 compliant>

import bpy
import os
from bpy.app.handlers import persistent

@persistent
def replaceTokens (dummy):
    global renpath
    tokens = {
    "$Scene":bpy.context.scene.name,
    "$File":os.path.basename(bpy.data.filepath).split(".")[0],
    "$ViewLayer":bpy.context.view_layer.name,
    "$Camera":bpy.context.scene.camera.name}
    
    renpath = bpy.context.scene.render.filepath
    
    bpy.context.scene.render.filepath = renpath.replace("$Scene",tokens["$Scene"]).replace("$File",tokens["$File"]).replace("$ViewLayer",tokens["$ViewLayer"]).replace("$Camera",tokens["$Camera"])
    print(bpy.context.scene.render.filepath)


@persistent
def restoreTokens (dummy):
    global renpath
    bpy.context.scene.render.filepath = renpath


# //RENDER/$Scene/$File/$ViewLayer/$Camera
