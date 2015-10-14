# <pep8-80 compliant>

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

import bpy
from bpy.props import BoolProperty, IntProperty
from . import cpuv_common

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "3.2"
__date__ = "20 Jun 2015"


# flip/rotate
class CPUVFlipRotate(bpy.types.Operator):
    """FlipRrotate UV."""

    bl_idname = "uv.flip_rotate"
    bl_label = "Flip/Rotate UV"
    bl_description = "Flip/Rotate UV"
    bl_options = {'REGISTER', 'UNDO'}

    flip = BoolProperty(
        name="Flip UV",
        description="Flip UV...",
        default=False)

    rotate = IntProperty(
        default=0,
        name="Rotate UV",
        min=0,
        max=30)

    def execute(self, context):
        self.report({'INFO'}, "Flip/Rotate UVs.")
        mem = cpuv_common.View3DModeMemory(context)

        # get active object to be fliped/rotated
        obj = context.active_object
        # check if active object has more than one UV map
        if len(obj.data.uv_textures.keys()) == 0:
            self.report({'WARNING'}, "Object must have more than one UV map.")
            return {'CANCELLED'}
        sel_face = cpuv_common.get_selected_faces_by_sel_seq(obj)
        uv_map = obj.data.uv_layers.active.name
        # change to 'OBJECT' mode, in order to access internal data
        mem.change_mode('OBJECT')
        # update UV data
        uv = obj.data.uv_layers[uv_map]
        for sf in sel_face:
            indices = sf.indices
            indices_orig = indices.copy()
            indices = cpuv_common.flip_rotate_uvs(
                list(indices), self.flip, self.rotate)
            orig = [uv.data[i].uv.copy() for i in indices_orig]
            # update
            for j in range(len(indices_orig)):
                uv.data[indices[j]].uv = orig[j]

        return {'FINISHED'}
