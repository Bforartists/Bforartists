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

bl_info = {
    "name": "Copy UV's from Joined",
    "description": "Copy UV coordinates from the active joined mesh",
    "author": "Sergey Sharybin",
    "version": (0, 1),
    "blender": (2, 63, 0),
    "location": "Object mode 'Make Links' menu",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object"}


import bpy
from bpy.types import Operator
from mathutils import Vector

FLT_MAX = 30000.0
KEY_PRECISION = 1


def MINMAX_INIT():
    return (Vector((+FLT_MAX, +FLT_MAX, +FLT_MAX)),
            Vector((-FLT_MAX, -FLT_MAX, -FLT_MAX)))


def MINMAX_DO(min, max, vec):
    for x in range(3):
        if vec[x] < min[x]:
            min[x] = vec[x]

        if vec[x] > max[x]:
            max[x] = vec[x]


def getObjectAABB(obj):
    min, max = MINMAX_INIT()

    matrix = obj.matrix_world.copy()
    for vec in obj.bound_box:
        v = matrix * Vector(vec)
        MINMAX_DO(min, max, v)

    return min, max


class  OBJECT_OT_copy_uv_from_joined(Operator):
    """
    Copy UVs from joined objects into originals
    """

    bl_idname = "object.copy_uv_from_joined"
    bl_label = "Copy UVs from Joined"

    def _findTranslation(self, obact, objects):
        """
        Find a translation from original objects to joined
        """

        bb_joined = getObjectAABB(obact)
        bb_orig = MINMAX_INIT()

        for ob in objects:
            if ob != obact:
                bb = getObjectAABB(ob)
                MINMAX_DO(bb_orig[0], bb_orig[1], bb[0])
                MINMAX_DO(bb_orig[0], bb_orig[1], bb[1])

        return bb_joined[0] - bb_orig[0]

    def _getPolygonMedian(self, me, poly):
        median = Vector()
        verts = me.vertices

        for vert_index in poly.vertices:
            median += verts[vert_index].co

        median /= len(poly.vertices)

        return median

    def _getVertexLookupMap(self, obact, objects):
        """
        Create a vertex lookup map from joined object space to original object
        """

        uv_map = {}

        T = self._findTranslation(obact, objects)

        for obj in objects:
            if obj != obact:
                me = obj.data
                mat = obj.matrix_world.copy()
                uv_layer = me.uv_layers.active

                for poly in me.polygons:
                    center = mat * self._getPolygonMedian(me, poly) + T
                    center_key = center.to_tuple(KEY_PRECISION)

                    for loop_index in poly.loop_indices:
                        loop = me.loops[loop_index]
                        vert = me.vertices[loop.vertex_index]
                        vec = mat * vert.co + T

                        key = (center_key, vec.to_tuple(KEY_PRECISION))

                        uv_map.setdefault(key, []).append((center, vec, (uv_layer, loop_index)))

        return uv_map

    def execute(self, context):
        obact = context.object

        # Check wether we're working with meshes
        # other object types are not supported
        if obact.type != 'MESH':
            self.report({'ERROR'}, "Only meshes are supported")
            return {'CANCELLED'}

        objects = context.selected_objects

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                self.report({'ERROR'}, "Only meshes are supported")
                return {'CANCELLED'}

        uv_map = self._getVertexLookupMap(obact, objects)

        me = obact.data
        mat = obact.matrix_world.copy()
        uv_layer = me.uv_layers.active

        for poly in me.polygons:
            center = mat * self._getPolygonMedian(me, poly)
            center_key = center.to_tuple(KEY_PRECISION)

            for loop_index in poly.loop_indices:
                loop = me.loops[loop_index]
                vert = me.vertices[loop.vertex_index]
                vec = mat * vert.co

                key = (center_key, vec.to_tuple(KEY_PRECISION))
                check_list = uv_map.get(key)

                if check_list is not None:
                    new_uv = None
                    closest_data = None

                    dist = FLT_MAX
                    for x in check_list:
                        cur_center, cur_vec, data = x

                        d1 = Vector(cur_center) - Vector(center)
                        d2 = Vector(cur_vec) - Vector(vec)

                        d = d1.length_squared + d2.length_squared

                        if d < dist:
                            closest_data = data
                            dist = d

                    if closest_data is not None:
                        orig_uv_layer, orig_loop_index = closest_data
                        new_uv = uv_layer.data[loop_index].uv
                        orig_uv_layer.data[orig_loop_index].uv = new_uv
                else:
                    print("Failed to lookup %r" % (key,))

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator("OBJECT_OT_copy_uv_from_joined",
                         text="Join as UVs (active to other selected)",
                         icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)
    
    bpy.types.VIEW3D_MT_make_links.append(menu_func)
    

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.VIEW3D_MT_make_links.remove(menu_func)


if __name__ == "__main__":
    register()
