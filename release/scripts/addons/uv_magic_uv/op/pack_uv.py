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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.1"
__date__ = "24 Feb 2018"

from math import fabs

import bpy
import bmesh
import mathutils
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
)
from mathutils import Vector

from .. import common


class MUV_PackUV(bpy.types.Operator):
    """
    Operation class: Pack UV with same UV islands are integrated
    Island matching algorithm
     - Same center of UV island
     - Same size of UV island
     - Same number of UV
    """

    bl_idname = "uv.muv_packuv"
    bl_label = "Pack UV"
    bl_description = "Pack UV (Same UV Islands are integrated)"
    bl_options = {'REGISTER', 'UNDO'}

    rotate = BoolProperty(
        name="Rotate",
        description="Rotate option used by default pack UV function",
        default=False)
    margin = FloatProperty(
        name="Margin",
        description="Margin used by default pack UV function",
        min=0,
        max=1,
        default=0.001)
    allowable_center_deviation = FloatVectorProperty(
        name="Allowable Center Deviation",
        description="Allowable center deviation to judge same UV island",
        min=0.000001,
        max=0.1,
        default=(0.001, 0.001),
        size=2
    )
    allowable_size_deviation = FloatVectorProperty(
        name="Allowable Size Deviation",
        description="Allowable sizse deviation to judge same UV island",
        min=0.000001,
        max=0.1,
        default=(0.001, 0.001),
        size=2
    )

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        if not bm.loops.layers.uv:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        selected_faces = [f for f in bm.faces if f.select]
        island_info = common.get_island_info(obj)
        num_group = self.__group_island(island_info)

        loop_lists = [l for f in bm.faces for l in f.loops]
        bpy.ops.mesh.select_all(action='DESELECT')

        # pack UV
        for gidx in range(num_group):
            group = list(filter(
                lambda i, idx=gidx: i['group'] == idx, island_info))
            for f in group[0]['faces']:
                f['face'].select = True
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=self.rotate, margin=self.margin)

        # copy/paste UV among same islands
        for gidx in range(num_group):
            group = list(filter(
                lambda i, idx=gidx: i['group'] == idx, island_info))
            if len(group) <= 1:
                continue
            for g in group[1:]:
                for (src_face, dest_face) in zip(
                        group[0]['sorted'], g['sorted']):
                    for (src_loop, dest_loop) in zip(
                            src_face['face'].loops, dest_face['face'].loops):
                        loop_lists[dest_loop.index][uv_layer].uv = loop_lists[
                            src_loop.index][uv_layer].uv

        # restore face/UV selection
        bpy.ops.uv.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='DESELECT')
        for f in selected_faces:
            f.select = True
        bpy.ops.uv.select_all(action='SELECT')

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}

    def __sort_island_faces(self, kd, uvs, isl1, isl2):
        """
        Sort faces in island
        """

        sorted_faces = []
        for f in isl1['sorted']:
            _, idx, _ = kd.find(
                Vector((f['ave_uv'].x, f['ave_uv'].y, 0.0)))
            sorted_faces.append(isl2['faces'][uvs[idx]['face_idx']])
        return sorted_faces

    def __group_island(self, island_info):
        """
        Group island
        """

        num_group = 0
        while True:
            # search islands which is not parsed yet
            isl_1 = None
            for isl_1 in island_info:
                if isl_1['group'] == -1:
                    break
            else:
                break   # all faces are parsed
            if isl_1 is None:
                break
            isl_1['group'] = num_group
            isl_1['sorted'] = isl_1['faces']

            # search same island
            for isl_2 in island_info:
                if isl_2['group'] == -1:
                    dcx = isl_2['center'].x - isl_1['center'].x
                    dcy = isl_2['center'].y - isl_1['center'].y
                    dsx = isl_2['size'].x - isl_1['size'].x
                    dsy = isl_2['size'].y - isl_1['size'].y
                    center_x_matched = (
                        fabs(dcx) < self.allowable_center_deviation[0]
                    )
                    center_y_matched = (
                        fabs(dcy) < self.allowable_center_deviation[1]
                    )
                    size_x_matched = (
                        fabs(dsx) < self.allowable_size_deviation[0]
                    )
                    size_y_matched = (
                        fabs(dsy) < self.allowable_size_deviation[1]
                    )
                    center_matched = center_x_matched and center_y_matched
                    size_matched = size_x_matched and size_y_matched
                    num_uv_matched = (isl_2['num_uv'] == isl_1['num_uv'])
                    # are islands have same?
                    if center_matched and size_matched and num_uv_matched:
                        isl_2['group'] = num_group
                        kd = mathutils.kdtree.KDTree(len(isl_2['faces']))
                        uvs = [
                            {
                                'uv': Vector(
                                    (f['ave_uv'].x, f['ave_uv'].y, 0.0)
                                ),
                                'face_idx': fidx
                            } for fidx, f in enumerate(isl_2['faces'])
                        ]
                        for i, uv in enumerate(uvs):
                            kd.insert(uv['uv'], i)
                        kd.balance()
                        # sort faces for copy/paste UV
                        isl_2['sorted'] = self.__sort_island_faces(
                            kd, uvs, isl_1, isl_2)
            num_group = num_group + 1

        return num_group
