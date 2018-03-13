# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

__all__ = (
    "SnapContext",
    )

import bgl
from mathutils import Vector

VERT = 1
EDGE = 2
FACE = 4


class _Internal:
    from .mesh_drawing import (
        gpu_Indices_enable_state,
        gpu_Indices_restore_state,
        gpu_Indices_use_clip_planes,
        gpu_Indices_set_ProjectionMatrix,
        )

    from .utils_projection import (
        region_2d_to_orig_and_view_vector,
        intersect_boundbox_threshold,
        intersect_ray_segment_fac,
        project_co_v3,
        )

    from mathutils.geometry import intersect_line_plane


class _SnapObjectData():
    __slots__ = ('data', 'mat')
    def __init__(self, data, omat):
        self.data = data
        self.mat = omat


class SnapContext():
    """
    Initializes the snap context with the region and space where the snap objects will be added.

    .. note::
        After the context has been created, add the objects with the `add_obj` method.

    :arg region: region of the 3D viewport, typically bpy.context.region.
    :type region: :class:`bpy.types.Region`
    :arg space: 3D region data, typically bpy.context.space_data.
    :type space: :class:`bpy.types.SpaceView3D`
    """

    def __init__(self, region, space):
        import gpu
        import ctypes

        self.freed = False
        self.snap_objects = []
        self.drawn_count = 0
        self._offset_cur = 1 # Starts with index 1
        self.region = region
        self.rv3d = space.region_3d

        if self.rv3d.is_perspective:
            self.depth_range = Vector((space.clip_start, space.clip_end))
        else:
            self.depth_range = Vector((-space.clip_end, space.clip_end))

        self.proj_mat = None
        self.mval = Vector((0, 0))
        self._snap_mode = VERT | EDGE | FACE

        self.set_pixel_dist(12)

        self._offscreen = gpu.offscreen.new(self.region.width, self.region.height)

        self._texture = self._offscreen.color_texture
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self._texture)

        NULL = bgl.Buffer(bgl.GL_INT, 1, (ctypes.c_int32 * 1).from_address(0))
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_R32UI, self.region.width, self.region.height, 0, bgl.GL_RED_INTEGER, bgl.GL_UNSIGNED_INT, NULL)
        del NULL

        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)

        self.winsize = Vector((self._offscreen.width, self._offscreen.height))

    ## PRIVATE ##

    def _get_snap_obj_by_index(self, index):
        for snap_obj in self.snap_objects[:self.drawn_count]:
            data = snap_obj.data[1]
            if index < data.first_index + data.get_tot_elems():
                return snap_obj
        return None

    def _get_nearest_index(self):
        loc = [self._dist_px, self._dist_px]
        d = 1
        m = self.threshold
        max = 2 * m - 1
        offset = 1
        last_snap_obj = None
        r_value = 0
        while m < max:
            for i in range(2):
                while 2 * loc[i] * d < m:
                    value = int(self._snap_buffer[loc[0]][loc[1]])
                    loc[i] += d
                    if value >= offset:
                        r_value = value
                        snap_obj = self._get_snap_obj_by_index(r_value)

                        if self._snap_mode & FACE and self._snap_mode & (VERT | EDGE) and last_snap_obj != snap_obj:
                            data = snap_obj.data[1]
                            offset = data.first_index + data.num_tris
                            last_snap_obj = snap_obj
                            continue
                        return snap_obj, r_value
            d = -d
            m += 4 * self._dist_px * d + 1

        return last_snap_obj, r_value

    def _get_loc(self, snap_obj, index):
        index -= snap_obj.data[1].first_index
        gpu_data = snap_obj.data[1]

        if gpu_data.draw_tris:
            if index < snap_obj.data[1].num_tris:
                tri_verts = gpu_data.get_tri_verts(index)
                tri_co = [snap_obj.mat * Vector(v) for v in gpu_data.get_tri_co(index)]
                nor = (tri_co[1] - tri_co[0]).cross(tri_co[2] - tri_co[0])
                return _Internal.intersect_line_plane(self.last_ray[1], self.last_ray[1] + self.last_ray[0], tri_co[0], nor), tri_verts

            index -= gpu_data.num_tris

        if gpu_data.draw_edges:
            if index < snap_obj.data[1].num_edges:
                edge_verts = gpu_data.get_edge_verts(index)
                edge_co = [snap_obj.mat * Vector(v) for v in gpu_data.get_edge_co(index)]
                fac = _Internal.intersect_ray_segment_fac(*edge_co, *self.last_ray)

                if (self._snap_mode) & VERT and (fac < 0.25 or fac > 0.75):
                    co = edge_co[0] if fac < 0.5 else edge_co[1]
                    proj_co = _Internal.project_co_v3(self, co)
                    dist = self.mval - proj_co
                    if abs(dist.x) < self._dist_px and abs(dist.y) < self._dist_px:
                        return co, (edge_verts[0] if fac < 0.5 else edge_verts[1],)

                if fac <= 0.0:
                    co = edge_co[0]
                elif fac >= 1.0:
                    co = edge_co[1]
                else:
                    co = edge_co[0] + fac * (edge_co[1] - edge_co[0])

                return co, edge_verts

            index -= gpu_data.num_edges

        if gpu_data.draw_verts:
            if index < snap_obj.data[1].num_verts:
                return snap_obj.mat * Vector(gpu_data.get_loosevert_co(index)), (gpu_data.get_loosevert_index(index),)

        return None, None


    def _get_snap_obj_by_obj(self, obj):
        for snap_obj in self.snap_objects:
            if obj == snap_obj.data[0]:
                return snap_obj

    def __del__(self):
        if not self.freed:
            self._offscreen.free()
            # Some objects may still be being referenced
            for snap_obj in self.snap_objects:
                del snap_obj.data
                del snap_obj.mat
                del snap_obj
            del self.snap_objects

    ## PUBLIC ##

    def update_all(self):
        self.drawn_count = 0
        self._offset_cur = 1

        bgl.glClearColor(0.0, 0.0, 0.0, 0.0)
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)

    def update_drawn_snap_object(self, snap_obj):
        if len(snap_obj.data) > 1:
            del snap_obj.data[1:]
            #self.update_all()
            # Update on next snap_get call #
            self.proj_mat = None

    def use_clip_planes(self, value):
        _Internal.gpu_Indices_use_clip_planes(self.rv3d, value)

    def set_pixel_dist(self, dist_px):
        self._dist_px = int(dist_px)
        self._dist_px_sq = self._dist_px ** 2
        self.threshold = 2 * self._dist_px + 1
        self._snap_buffer = bgl.Buffer(bgl.GL_FLOAT, (self.threshold, self.threshold))

    def set_snap_mode(self, snap_to_vert, snap_to_edge, snap_to_face):
        snap_mode = 0
        if snap_to_vert:
            snap_mode |= VERT
        if snap_to_edge:
            snap_mode |= EDGE
        if snap_to_face:
            snap_mode |= FACE

        if snap_mode != self._snap_mode:
            self._snap_mode = snap_mode
            self.update_all()

    def add_obj(self, obj, matrix):
        matrix = matrix.copy()
        snap_obj = self._get_snap_obj_by_obj(obj)
        if not snap_obj:
            self.snap_objects.append(_SnapObjectData([obj], matrix))
        else:
            self.snap_objects.append(_SnapObjectData(snap_obj.data, matrix))

        return self.snap_objects[-1]

    def get_ray(self, mval):
        self.last_ray = _Internal.region_2d_to_orig_and_view_vector(self.region, self.rv3d, mval)
        return self.last_ray

    def snap_get(self, mval):
        ret = None, None
        self.mval[:] = mval
        snap_vert = self._snap_mode & VERT != 0
        snap_edge = self._snap_mode & EDGE != 0
        snap_face = self._snap_mode & FACE != 0

        _Internal.gpu_Indices_enable_state()
        self._offscreen.bind()

        #bgl.glDisable(bgl.GL_DITHER) # dithering and AA break color coding, so disable #
        #multisample_enabled = bgl.glIsEnabled(bgl.GL_MULTISAMPLE)
        #bgl.glDisable(bgl.GL_MULTISAMPLE)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        proj_mat = self.rv3d.perspective_matrix.copy()
        if self.proj_mat != proj_mat:
            self.proj_mat = proj_mat
            _Internal.gpu_Indices_set_ProjectionMatrix(self.proj_mat)
            self.update_all()

        ray_dir, ray_orig = self.get_ray(mval)
        for i, snap_obj in enumerate(self.snap_objects[self.drawn_count:], self.drawn_count):
            obj = snap_obj.data[0]
            bbmin = Vector(obj.bound_box[0])
            bbmax = Vector(obj.bound_box[6])

            if bbmin != bbmax:
                MVP = proj_mat * snap_obj.mat
                mat_inv = snap_obj.mat.inverted()
                ray_orig_local = mat_inv * ray_orig
                ray_dir_local = mat_inv.to_3x3() * ray_dir
                in_threshold = _Internal.intersect_boundbox_threshold(self, MVP, ray_orig_local, ray_dir_local, bbmin, bbmax)
            else:
                proj_co = _Internal.project_co_v3(self, snap_obj.mat.translation)
                dist = self.mval - proj_co
                in_threshold = abs(dist.x) < self._dist_px and abs(dist.y) < self._dist_px
                #snap_obj.data[1] = primitive_point

            if in_threshold:
                if len(snap_obj.data) == 1:
                    from .mesh_drawing import GPU_Indices_Mesh
                    snap_obj.data.append(GPU_Indices_Mesh(obj, snap_face, snap_edge, snap_vert))
                snap_obj.data[1].set_draw_mode(snap_face, snap_edge, snap_vert)
                snap_obj.data[1].set_ModelViewMatrix(snap_obj.mat)
                snap_obj.data[1].Draw(self._offset_cur)
                self._offset_cur += snap_obj.data[1].get_tot_elems()

                self.snap_objects[self.drawn_count], self.snap_objects[i] = self.snap_objects[i], self.snap_objects[self.drawn_count]
                self.drawn_count += 1

        bgl.glReadBuffer(bgl.GL_COLOR_ATTACHMENT0)
        bgl.glReadPixels(
                int(self.mval[0]) - self._dist_px, int(self.mval[1]) - self._dist_px,
                self.threshold, self.threshold, bgl.GL_RED_INTEGER, bgl.GL_UNSIGNED_INT, self._snap_buffer)
        bgl.glReadBuffer(bgl.GL_BACK)

        snap_obj, index = self._get_nearest_index()
        #print(index)
        if snap_obj:
            ret = self._get_loc(snap_obj, index)

        self._offscreen.unbind()
        _Internal.gpu_Indices_restore_state()

        return snap_obj, ret[0], ret[1]

    def free(self):
        self.__del__()
        self.freed = True
