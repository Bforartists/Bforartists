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
        gpu_Indices_mesh_cache_clear,
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


class _SnapOffscreen():
    bound = None
    def __init__(self, width, height):
        import ctypes

        self.freed = False
        self.is_bound = False

        self.width = width
        self.height = height

        self.fbo = bgl.Buffer(bgl.GL_INT, 1)
        self.buf_color = bgl.Buffer(bgl.GL_INT, 1)
        self.buf_depth = bgl.Buffer(bgl.GL_INT, 1)

        self.cur_fbo = bgl.Buffer(bgl.GL_INT, 1)
        self.cur_viewport = bgl.Buffer(bgl.GL_INT, 4)

        bgl.glGenRenderbuffers(1, self.buf_depth)
        bgl.glBindRenderbuffer(bgl.GL_RENDERBUFFER, self.buf_depth[0])
        bgl.glRenderbufferStorage(bgl.GL_RENDERBUFFER, bgl.GL_DEPTH_COMPONENT, width, height)

        bgl.glGenTextures(1, self.buf_color)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.buf_color[0])
        NULL = bgl.Buffer(bgl.GL_INT, 1, (ctypes.c_int32 * 1).from_address(0))
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_R32UI, width, height, 0, bgl.GL_RED_INTEGER, bgl.GL_UNSIGNED_INT, NULL)
        del NULL
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

        bgl.glGetIntegerv(bgl.GL_FRAMEBUFFER_BINDING, self.cur_fbo)

        bgl.glGenFramebuffers(1, self.fbo)
        bgl.glBindFramebuffer(bgl.GL_FRAMEBUFFER, self.fbo[0])
        bgl.glFramebufferRenderbuffer(bgl.GL_FRAMEBUFFER, bgl.GL_DEPTH_ATTACHMENT, bgl.GL_RENDERBUFFER, self.buf_depth[0])
        bgl.glFramebufferTexture(bgl.GL_FRAMEBUFFER, bgl.GL_COLOR_ATTACHMENT0, self.buf_color[0], 0)

        bgl.glDrawBuffers(1, bgl.Buffer(bgl.GL_INT, 1, [bgl.GL_COLOR_ATTACHMENT0]))

        status = bgl.glCheckFramebufferStatus(bgl.GL_FRAMEBUFFER)
        if status != bgl.GL_FRAMEBUFFER_COMPLETE:
            print("Framebuffer Invalid", status)

        bgl.glBindFramebuffer(bgl.GL_FRAMEBUFFER, self.cur_fbo[0])

    def bind(self):
        if self is not _SnapOffscreen.bound:
            if _SnapOffscreen.bound is None:
                bgl.glGetIntegerv(bgl.GL_FRAMEBUFFER_BINDING, self.cur_fbo)
                bgl.glGetIntegerv(bgl.GL_VIEWPORT, self.cur_viewport)

            bgl.glBindFramebuffer(bgl.GL_FRAMEBUFFER, self.fbo[0])
            bgl.glViewport(0, 0, self.width, self.height)
            _SnapOffscreen.bound = self

    def unbind(self):
        if self is _SnapOffscreen.bound:
            bgl.glBindFramebuffer(bgl.GL_FRAMEBUFFER, self.cur_fbo[0])
            bgl.glViewport(*self.cur_viewport)
            _SnapOffscreen.bound = None

    def clear(self):
        is_bound =  self is _SnapOffscreen.bound
        if not is_bound:
            self.bind()

        bgl.glColorMask(bgl.GL_TRUE, bgl.GL_TRUE, bgl.GL_TRUE, bgl.GL_TRUE)
        bgl.glClearColor(0.0, 0.0, 0.0, 0.0)

        bgl.glDepthMask(bgl.GL_TRUE)
        bgl.glClearDepth(1.0);

        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)

        if not is_bound:
            self.unbind()

    def __del__(self):
        if not self.freed:
            bgl.glDeleteFramebuffers(1, self.fbo)
            bgl.glDeleteRenderbuffers(1, self.buf_depth)
            bgl.glDeleteTextures(1, self.buf_color)
            del self.fbo
            del self.buf_color
            del self.buf_depth

            del self.cur_fbo
            del self.cur_viewport

    def free(self):
        self.__del__()
        self.freed = True


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
        #print('Render:', bgl.glGetString(bgl.GL_RENDERER))
        #print('OpenGL Version:', bgl.glGetString(bgl.GL_VERSION))

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

        self._offscreen = _SnapOffscreen(self.region.width, self.region.height)

        self.winsize = Vector((self._offscreen.width, self._offscreen.height))

        self._offscreen.clear()

    ## PRIVATE ##

    def _get_snap_obj_by_index(self, index):
        if index:
            for snap_obj in self.snap_objects[:self.drawn_count]:
                data = snap_obj.data[1]
                if index < data.first_index + data.get_tot_elems():
                    return snap_obj
        return None

    def _get_nearest_index(self):
        r_snap_obj = None
        r_value = 0

        loc = [self._dist_px, self._dist_px]
        d = 1
        m = self.threshold
        max_val = 2 * m - 1
        last_value = -1
        find_next_index = self._snap_mode & FACE and self._snap_mode & (VERT | EDGE)
        while m < max_val:
            for i in range(2):
                while 2 * loc[i] * d < m:
                    value = int(self._snap_buffer[loc[0]][loc[1]])
                    loc[i] += d
                    if value != last_value:
                        r_value = value
                        if find_next_index:
                            last_value = value
                            r_snap_obj = self._get_snap_obj_by_index(value)
                            if (r_snap_obj is None) or value < (r_snap_obj.data[1].first_index + len(r_snap_obj.data[1].tri_verts)):
                                continue
                            find_next_index = False
                        elif (r_snap_obj is None) or\
                            (value < r_snap_obj.data[1].first_index) or\
                            (value >= (r_snap_obj.data[1].first_index + r_snap_obj.data[1].get_tot_elems())):
                                r_snap_obj = self._get_snap_obj_by_index(value)
                        return r_snap_obj, r_value
            d = -d
            m += 4 * self._dist_px * d + 1

        return r_snap_obj, r_value

    def _get_loc(self, snap_obj, index):
        index -= snap_obj.data[1].first_index
        gpu_data = snap_obj.data[1]

        if gpu_data.draw_tris:
            num_tris = len(snap_obj.data[1].tri_verts)
            if index < num_tris:
                tri_verts = gpu_data.get_tri_verts(index)
                tri_co = [snap_obj.mat @ Vector(v) for v in gpu_data.get_tri_co(index)]
                nor = (tri_co[1] - tri_co[0]).cross(tri_co[2] - tri_co[0])
                return _Internal.intersect_line_plane(self.last_ray[1], self.last_ray[1] + self.last_ray[0], tri_co[0], nor), tri_verts, tri_co

            index -= num_tris

        if gpu_data.draw_edges:
            num_edges = len(snap_obj.data[1].edge_verts)
            if index < num_edges:
                edge_verts = gpu_data.get_edge_verts(index)
                edge_co = [snap_obj.mat @ Vector(v) for v in gpu_data.get_edge_co(index)]
                fac = _Internal.intersect_ray_segment_fac(*edge_co, *self.last_ray)

                if (self._snap_mode) & VERT and (fac < 0.25 or fac > 0.75):
                    co = edge_co[0] if fac < 0.5 else edge_co[1]
                    proj_co = _Internal.project_co_v3(self, co)
                    dist = self.mval - proj_co
                    if abs(dist.x) < self._dist_px and abs(dist.y) < self._dist_px:
                        return co, (edge_verts[0] if fac < 0.5 else edge_verts[1],), co

                if fac <= 0.0:
                    co = edge_co[0]
                elif fac >= 1.0:
                    co = edge_co[1]
                else:
                    co = edge_co[0] + fac * (edge_co[1] - edge_co[0])

                return co, edge_verts, edge_co

            index -= num_edges

        if gpu_data.draw_verts:
            if index < len(snap_obj.data[1].looseverts):
                co = snap_obj.mat @ Vector(gpu_data.get_loosevert_co(index))
                return co, (gpu_data.get_loosevert_index(index),), co

        return None, None, None


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

    def clear_snap_objects(self):
        self.snap_objects.clear()
        _Internal.gpu_Indices_mesh_cache_clear()

    def update_all(self):
        self.drawn_count = 0
        self._offset_cur = 1
        self._offscreen.clear()

    def tag_update_drawn_snap_object(self, snap_obj):
        if len(snap_obj.data) > 1:
            del snap_obj.data[1:]
            #self.update_all()
            # Update on next snap_get call #
            self.proj_mat = None

    def update_drawn_snap_object(self, snap_obj):
        if len(snap_obj.data) > 1:
            _Internal.gpu_Indices_enable_state()

            from .mesh_drawing import GPU_Indices_Mesh
            snap_vert = self._snap_mode & VERT != 0
            snap_edge = self._snap_mode & EDGE != 0
            snap_face = self._snap_mode & FACE != 0
            snap_obj.data[1] = GPU_Indices_Mesh(snap_obj.data[0], snap_face, snap_edge, snap_vert)

            _Internal.gpu_Indices_restore_state()

    def use_clip_planes(self, value):
        _Internal.gpu_Indices_use_clip_planes(self.rv3d, value)

    def set_pixel_dist(self, dist_px):
        self._dist_px = int(dist_px)
        self._dist_px_sq = self._dist_px ** 2
        self.threshold = 2 * self._dist_px + 1
        self._snap_buffer = bgl.Buffer(bgl.GL_INT, (self.threshold, self.threshold))

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

    def snap_get(self, mval, main_snap_obj = None):
        ret = None, None, None
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
            try:
                bbmin = Vector(obj.bound_box[0])
                bbmax = Vector(obj.bound_box[6])
            except ReferenceError:
                self.snap_objects.remove(snap_obj)
                continue

            if bbmin != bbmax:
                MVP = proj_mat @ snap_obj.mat
                mat_inv = snap_obj.mat.inverted()
                ray_orig_local = mat_inv @ ray_orig
                ray_dir_local = mat_inv.to_3x3() @ ray_dir
                in_threshold = _Internal.intersect_boundbox_threshold(
                        self, MVP, ray_orig_local, ray_dir_local, bbmin, bbmax)
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

                if snap_obj == main_snap_obj:
                    snap_obj.data[1].Draw(self._offset_cur, -0.0001)
                else:
                    snap_obj.data[1].Draw(self._offset_cur)
                self._offset_cur += snap_obj.data[1].get_tot_elems()

                tmp = self.snap_objects[self.drawn_count]
                self.snap_objects[self.drawn_count] = self.snap_objects[i]
                self.snap_objects[i] = tmp

                self.drawn_count += 1

        bgl.glReadBuffer(bgl.GL_COLOR_ATTACHMENT0)
        bgl.glReadPixels(
                int(self.mval[0]) - self._dist_px, int(self.mval[1]) - self._dist_px,
                self.threshold, self.threshold, bgl.GL_RED_INTEGER, bgl.GL_UNSIGNED_INT, self._snap_buffer)
        #bgl.glReadBuffer(bgl.GL_BACK)
        #import numpy as np
        #a = np.array(self._snap_buffer)
        #print(a)

        snap_obj, index = self._get_nearest_index()
        #print("index:", index)
        if snap_obj:
            ret = self._get_loc(snap_obj, index)

        bgl.glDisable(bgl.GL_DEPTH_TEST)
        self._offscreen.unbind()
        _Internal.gpu_Indices_restore_state()

        return (snap_obj, *ret)

    def free(self):
        self.__del__()
        self.freed = True
