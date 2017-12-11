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

"""
    misc_util.py
    Miscellaneous helper methods
"""

import bpy
from mathutils import Vector
from .cursor_utils import CursorAccess


class BlenderFake:

    @classmethod
    def forceUpdate(cls):
        if bpy.context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

    @classmethod
    def forceRedraw(cls):
        CursorAccess.setCursor(CursorAccess.getCursor())


# Converts 3D coordinates in a 3DRegion
# into 2D screen coordinates for that region.
# Borrowed from Buerbaum Martin (Pontiac)
def region3d_get_2d_coordinates(context, loc_3d):
    # Get screen information
    mid_x = context.region.width / 2.0
    mid_y = context.region.height / 2.0
    width = context.region.width
    height = context.region.height

    # Get matrices
    view_mat = context.space_data.region_3d.perspective_matrix
    total_mat = view_mat

    # order is important
    vec = total_mat * Vector((loc_3d[0], loc_3d[1], loc_3d[2], 1.0))

    # dehomogenise
    vec = Vector((
        vec[0] / vec[3],
        vec[1] / vec[3],
        vec[2] / vec[3]))

    x = int(mid_x + vec[0] * width / 2.0)
    y = int(mid_y + vec[1] * height / 2.0)
    z = vec[2]

    return Vector((x, y, z))
