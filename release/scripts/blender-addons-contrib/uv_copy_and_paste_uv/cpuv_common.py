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
import bmesh
from collections import namedtuple
from . import cpuv_properties

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "3.2"
__date__ = "20 Jun 2015"

SelectedFaceInfo = namedtuple('SelectedFaceInfo', 'normal indices center')


def debug_print(*s):
    if cpuv_properties.DEBUG:
        print(s)


class View3DModeMemory():
    __mode_orig = None

    def __init__(self, context):
        self.__mode_orig = bpy.context.object.mode

    def change_mode(self, mode):
        bpy.ops.object.mode_set(mode=mode)

    def __del__(self):
        bpy.ops.object.mode_set(mode=self.__mode_orig)


def memorize_view_3d_mode(fn):
    def __memorize_view_3d_mode(*args, **kwargs):
        mode_orig = bpy.context.object.mode
        result = fn(*args, **kwargs)
        bpy.ops.object.mode_set(mode=mode_orig)
        return result
    return __memorize_view_3d_mode


def check_version(major, minor, unused):
    if bpy.app.version[0] == major and bpy.app.version[1] == minor:
        return 0
    if bpy.app.version[0] > major:
        return 1
    else:
        if bpy.app.version[1] > minor:
            return 1
        else:
            return -1


def change_active_object(context, fm, to):
    mode_orig = context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    fm.select = False
    context.scene.objects.active = to
    to.select = True
    bpy.ops.object.mode_set(mode=mode_orig)


def update_mesh():
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()


def prep_copy(context, self):
    """
    parepare for copy operation.
    @return (code, active object)
    """
    # get active (source) object to be copied from
    obj = context.active_object
    # check if active object has more than one UV map
    if len(obj.data.uv_textures.keys()) == 0:
        self.report({'WARNING'}, "Object must have more than one UV map.")
        return (1, None)

    return (0, obj)


# finish copy operation
def fini_copy():
    """
    finish copy operation.
    """
    pass


# prepare for paste operation
def prep_paste(context, self, src_obj, src_sel_face_info):
    """
    prepare for paste operation.
    @param  src_obj object that is copied from
    @param  src_sel_face_info information about faces will be copied
    @return (code, active object)
    """
    # check if copy operation was executed
    if src_sel_face_info is None or src_obj is None:
        self.report({'WARNING'}, "Do copy operation at first.")
        return (1, None)
    # get active (source) object to be pasted to
    obj = context.active_object
    # check if active object has more than one UV map
    if len(obj.data.uv_textures.keys()) == 0:
        self.report({'WARNING'}, "Object must have more than one UV map.")
        return (2, None)

    return (0, obj)


# finish paste operation
def fini_paste():
    """
    finish paste operation.
    """
    pass


def get_selected_faces(context, obj):
    """
    get information about selected faces.
    @param  obj object
    @return information about selected faces (list of SelectedFaceInfo)
    """
    return get_faces_from_indices(obj, get_selected_face_indices(context, obj))


@memorize_view_3d_mode
def get_selected_face_indices(context, obj):
    bpy.ops.object.mode_set(mode='OBJECT')
    polys = obj.data.polygons
    return [i for i, p in enumerate(polys) if p.select is True]


def get_faces_from_indices(obj, indices):
    polys = obj.data.polygons
    return [
        SelectedFaceInfo(
            polys[i].normal.copy(),
            list(polys[i].loop_indices),
            polys[i].center.copy())
        for i in indices]


@memorize_view_3d_mode
def select_faces_by_indices(context, obj, indices):
    bpy.ops.object.mode_set(mode='OBJECT')
    # clear
    for p in obj.data.polygons:
        p.select = False
    # select
    for i in indices:
        obj.data.polygons[i].select = True


def get_selected_faces_by_sel_seq(obj):
    """
    get information about selected indices.
    @param  obj object
    @return information about selected faces (list of SelectedFaceInfo)
    """
    # get indices by selection sequence
    bm = bmesh.from_edit_mesh(obj.data)
    if check_version(2, 73, 0) >= 0:
        bm.faces.ensure_lookup_table()
    indices = [
        e.loops[0].face.index
        for e in bm.select_history
        if isinstance(e, bmesh.types.BMFace) and e.select]

    # get selected faces by selection sequence
    return get_faces_from_indices(obj, indices)


def copy_opt(self, uv_map, src_obj, src_sel_face_info):
    """
    copy operation.
    @param  self operation object
    @param  uv_map UV Map to be copied. (current map when null str)
    @param  src_obj source object
    @param  src_sel_face_info source information about selected faces
    @return (code, UV map)
    """

    # confirm that there was no problem in copy operation
    if len(src_sel_face_info) == 0:
        self.report({'WARNING'}, "No faces are selected.")
        return (1, None)
    else:
        self.report(
            {'INFO'}, "%d face(s) are selected." % len(src_sel_face_info))

    # get UV map name
    if uv_map == "":
        uv_map = src_obj.data.uv_layers.active.name
    else:
        uv_map = uv_map

    return (0, uv_map)


@memorize_view_3d_mode
def paste_opt(context, self, uv_map, src_obj, src_sel_face_info,
              src_uv_map, dest_obj, dest_sel_face_info):
    """
    paste operation.
    @param  self operation object
    @param  uv_map UV Map to be pasted. (current map when null str)
    @param  src_obj source object
    @param  src_sel_face_info source information about selected faces
    @param  src_uv_map source UV map
    @param  dest_obj destination object
    @param  dest_sel_face_info destination information about selected faces
    """
    bpy.ops.object.mode_set(mode='OBJECT')

    # confirm that there was no problem between copy and paste operation
    if len(dest_sel_face_info) == 0:
        self.report({'WARNING'}, "No faces are selected.")
        return 1
    if len(dest_sel_face_info) != len(src_sel_face_info):
        self.report(
            {'WARNING'},
            "Number of selected faces is different from copied faces." +
            "(src:%d, dest:%d)" %
            (len(src_sel_face_info), len(dest_sel_face_info)))
        return 2
    for sinfo, dinfo in zip(src_sel_face_info, dest_sel_face_info):
        if len(sinfo.indices) != len(dinfo.indices):
            self.report({'WARNING'}, "Some faces are different size.")
            return 3

    # get UV map name
    if uv_map == "":
        dest_uv_map = dest_obj.data.uv_layers.active.name
    else:
        dest_uv_map = uv_map

    # update UV data
    src_uv = src_obj.data.uv_layers[src_uv_map]
    dest_uv = dest_obj.data.uv_layers[dest_uv_map]
    for sinfo, dinfo in zip(src_sel_face_info, dest_sel_face_info):
        dest_indices = dinfo.indices
        src_indices = sinfo.indices
        # flip/rotate UVs
        dest_indices = flip_rotate_uvs(
            list(dest_indices), self.flip_copied_uv, self.rotate_copied_uv)
        # update
        for si, di in zip(src_indices, dest_indices):
            dest_data = dest_uv.data[di]
            src_data = src_uv.data[si]
            dest_data.uv = src_data.uv

    self.report({'INFO'}, "%d faces are copied." % len(dest_sel_face_info))
    return 0


def flip_rotate_uvs(indices, flip, num_rotate):
    # flip UVs
    if flip is True:
        indices.reverse()
    # rotate UVs
    for n in range(num_rotate):
        idx = indices.pop()
        indices.insert(0, idx)
    return indices
