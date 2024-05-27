# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__all__ = ("SnapContext",)

import gpu
from mathutils import Vector

VERT = 1
EDGE = 2
FACE = 4


class _Internal:
    global_snap_context = None

    @classmethod
    def snap_context_free(cls):
        if cls.global_snap_context is not None:
            cls.global_snap_context.free()
            del cls

    from .mesh_drawing import (
        gpu_Indices_enable_state,
        gpu_Indices_restore_state,
        gpu_Indices_use_clip_planes,
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
        self._fbo = None

        self.width = width
        self.height = height

        self._framebuffer_config()

    def _framebuffer_config(self):
        self._framebuffer_free()

        self._tex_color = gpu.types.GPUTexture((self.width, self.height), format='R32UI')
        self._tex_depth = gpu.types.GPUTexture((self.width, self.height), format='DEPTH_COMPONENT32F')
        self._fbo = gpu.types.GPUFrameBuffer(depth_slot=self._tex_depth, color_slots=self._tex_color)

    def _framebuffer_free(self):
        self._fbo = self._tex_color = self._tex_depth = None

    def bind(self):
        return self._fbo.bind()

    def clear(self):
        # self._fbo.clear(color=(0.0, 0.0, 0.0, 0.0), depth=1.0)
        self._tex_color.clear(format='UINT', value=(0,))
        self._tex_depth.clear(format='FLOAT', value=(1.0,))

    def resize(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self._framebuffer_config()

    def __del__(self):
        self._framebuffer_free()

    def free(self):
        self._framebuffer_free()


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

    __slots__ = (
        '_dist_px',
        '_dist_px_sq',
        '_offscreen',
        '_offset_cur',
        '_snap_buffer',
        '_snap_mode',
        'depsgraph',
        'depth_range',
        'drawn_count',
        'freed',
        'last_ray',
        'mval',
        'proj_mat',
        'region',
        'rv3d',
        'snap_objects',
        'threshold',
        'winsize',)

    def __init__(self, depsgraph, region, space):
        self.freed = False
        self.snap_objects = []
        self.drawn_count = 0
        self._offset_cur = 1  # Starts with index 1

        self.proj_mat = None
        self.mval = Vector((0.0, 0.0))
        self.last_ray = Vector((1.0, 0.0, 0.0))
        self._snap_mode = VERT | EDGE | FACE

        self.set_pixel_dist(12)

        self.region = region
        self.depsgraph = depsgraph

        if not (depsgraph or region or space):
            self.rv3d = None
            self.depth_range = Vector((-1.0, 1.0))
            self._offscreen = _SnapOffscreen(1, 1)
        else:
            self.rv3d = space.region_3d

            if self.rv3d.is_perspective:
                self.depth_range = Vector((space.clip_start, space.clip_end))
            else:
                self.depth_range = Vector((-space.clip_end, space.clip_end))

            self._offscreen = _SnapOffscreen(self.region.width, self.region.height)
            self._offscreen.clear()

        self.winsize = Vector((self._offscreen.width, self._offscreen.height))

    ## PRIVATE ##

    def _get_snap_obj_by_index(self, index):
        if index:
            for snap_obj in self.snap_objects[:self.drawn_count]:
                data = snap_obj.data[1]
                if index < data.first_index + data.get_tot_elems():
                    return snap_obj
        return None

    def _read_buffer(self):
        self._snap_buffer = self._offscreen._tex_color.read()

    def _get_nearest_index(self, mval):
        r_snap_obj = None
        r_value = 0

        loc_curr = [int(mval[1]), int(mval[0])]
        rect = ((
                max(0, loc_curr[0] - self.threshold),
                min(self._snap_buffer.dimensions[0], loc_curr[0] + self.threshold)
                ), (
                max(0, loc_curr[1] - self.threshold),
                min(self._snap_buffer.dimensions[1], loc_curr[1] + self.threshold)
                ))

        if loc_curr[0] < rect[0][0] or loc_curr[0] >= rect[0][1] or loc_curr[1] < rect[1][0] or loc_curr[1] >= rect[1][1]:
            return r_snap_obj, r_value

        find_next_index = self._snap_mode & FACE and self._snap_mode & (VERT | EDGE)
        last_value = -1 if find_next_index else 0
        spiral_direction = 0
        for nr in range(1, 2 * self.threshold):
            for a in range(2):
                for b in range(0, nr):
                    # TODO: Make the buffer flat.
                    value = int(self._snap_buffer[loc_curr[0]][loc_curr[1]])
                    if value != last_value:
                        r_value = value
                        if find_next_index:
                            last_value = value
                            r_snap_obj = self._get_snap_obj_by_index(value)
                            if r_snap_obj is not None:
                                snap_data = r_snap_obj.data[1]
                                if value < (snap_data.first_index + len(snap_data.tri_verts)):
                                    # snap to a triangle
                                    find_next_index = False
                                else:
                                    return r_snap_obj, r_value
                        else:
                            if (r_snap_obj is None) or \
                               (value < r_snap_obj.data[1].first_index) or \
                               (value >= (r_snap_obj.data[1].first_index + r_snap_obj.data[1].get_tot_elems())):
                                r_snap_obj = self._get_snap_obj_by_index(value)

                            return r_snap_obj, r_value

                    # Next spiral step.
                    if (spiral_direction == 0):
                        loc_curr[1] += 1  # right
                    elif (spiral_direction == 1):
                        loc_curr[0] -= 1  # down
                    elif (spiral_direction == 2):
                        loc_curr[1] -= 1  # left
                    else:
                        loc_curr[0] += 1  # up

                    if (loc_curr[not a] < rect[not a][0] or loc_curr[not a] >= rect[not a][1]):
                        return r_snap_obj, r_value

                spiral_direction = (spiral_direction + 1) % 4
        return r_snap_obj, r_value

    def _get_loc(self, snap_obj, index):
        index -= snap_obj.data[1].first_index
        gpu_data = snap_obj.data[1]

        if gpu_data.draw_tris:
            num_tris = len(snap_obj.data[1].tri_verts)
            if index < num_tris:
                tri_verts = gpu_data.get_tri_verts(index)
                tri_co = [snap_obj.mat @ Vector(v) for v in gpu_data.get_tri_co(index)]
                # loc = _Internal.intersect_ray_tri(*tri_co, self.last_ray[0],
                # self.last_ray[1], False)
                nor = (tri_co[1] - tri_co[0]).cross(tri_co[2] - tri_co[0]).normalized()
                loc = _Internal.intersect_line_plane(
                    self.last_ray[1], self.last_ray[1] + self.last_ray[0], tri_co[0], nor)
                return loc, tri_verts, tri_co

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
            self._snap_buffer = None
            # Some objects may still be being referenced
            for snap_obj in self.snap_objects:
                if len(snap_obj.data) == 2:
                    snap_obj.data[1].free()
                    del snap_obj.data[1:]

                del snap_obj.data
                del snap_obj.mat
                del snap_obj
            del self.snap_objects

    ## PUBLIC ##

    def update_viewport_context(self, depsgraph, region, space, resize=False):
        rv3d = space.region_3d

        if not resize and self.rv3d == rv3d and self.region == region:
            return

        self.depsgraph = depsgraph
        self.region = region
        self.rv3d = rv3d

        if self.rv3d.is_perspective:
            self.depth_range = Vector((space.clip_start, space.clip_end))
        else:
            self.depth_range = Vector((-space.clip_end, space.clip_end))

        winsize = Vector((self.region.width, self.region.height))

        if winsize != self.winsize:
            self.winsize = winsize
            self._offscreen.resize(*self.winsize)

    def clear_snap_objects(self, clear_offscreen=False):
        for snap_obj in self.snap_objects:
            if len(snap_obj.data) == 2:
                snap_obj.data[1].free()
                del snap_obj.data[1:]

        self.update_drawing(clear_offscreen)

        self.snap_objects.clear()
        _Internal.gpu_Indices_mesh_cache_clear()

    def update_all(self):
        for snap_obj in self.snap_objects:
            if len(snap_obj.data) == 2:
                snap_obj.data[1].free()
                del snap_obj.data[1:]

        self.update_drawing()

    def update_drawing(self, clear_offscreen=True):
        self.drawn_count = 0
        self._offset_cur = 1
        if clear_offscreen:
            self._offscreen.clear()

        _Internal.gpu_Indices_use_clip_planes(self.rv3d, True)

    def tag_update_drawn_snap_object(self, snap_obj):
        if len(snap_obj.data) > 1:
            snap_obj.data[1].free()
            del snap_obj.data[1:]
            # self.update_drawing()
            # Update on next snap_get call #
            self.proj_mat = None

    def update_drawn_snap_object(self, snap_obj):
        _Internal.gpu_Indices_enable_state(self.rv3d.window_matrix, self.rv3d.view_matrix)

        from .mesh_drawing import GPU_Indices_Mesh
        snap_vert = self._snap_mode & VERT != 0
        snap_edge = self._snap_mode & EDGE != 0
        snap_face = self._snap_mode & FACE != 0

        if len(snap_obj.data) > 1:
            snap_obj.data[1].free()
            del snap_obj.data[1:]

        data = GPU_Indices_Mesh(self.depsgraph, snap_obj.data[0], snap_face, snap_edge, snap_vert)
        snap_obj.data.append(data)

        _Internal.gpu_Indices_restore_state()

    def set_pixel_dist(self, dist_px):
        self._dist_px = int(dist_px)
        self._dist_px_sq = self._dist_px ** 2
        self.threshold = 2 * self._dist_px + 1

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
        self.snap_objects.append(_SnapObjectData([obj], matrix.copy()))

        return self.snap_objects[-1]

    def get_ray(self, mval):
        self.last_ray = _Internal.region_2d_to_orig_and_view_vector(self.region, self.rv3d, mval)
        return self.last_ray

    def snap_get(self, mval, main_snap_obj=None):
        ret = None, None, None
        self.mval[:] = mval
        snap_vert = self._snap_mode & VERT != 0
        snap_edge = self._snap_mode & EDGE != 0
        snap_face = self._snap_mode & FACE != 0

        _Internal.gpu_Indices_enable_state(self.rv3d.window_matrix, self.rv3d.view_matrix)
        gpu.state.depth_mask_set(True)
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.program_point_size_set(True)

        with self._offscreen.bind():
            update_buffer = False
            proj_mat = self.rv3d.perspective_matrix.copy()
            if self.proj_mat != proj_mat:
                self.proj_mat = proj_mat
                self.update_drawing()
                update_buffer = True

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
                    mat_inv = snap_obj.mat.inverted_safe()
                    ray_orig_local = mat_inv @ ray_orig
                    ray_dir_local = mat_inv.to_3x3() @ ray_dir
                    in_threshold = _Internal.intersect_boundbox_threshold(
                        self, MVP, ray_orig_local, ray_dir_local, bbmin, bbmax)
                else:
                    proj_co = _Internal.project_co_v3(self, snap_obj.mat.translation)
                    dist = self.mval - proj_co
                    in_threshold = abs(dist.x) < self._dist_px and abs(dist.y) < self._dist_px
                    # snap_obj.data[1] = primitive_point

                if in_threshold:
                    if len(snap_obj.data) == 1:
                        from .mesh_drawing import GPU_Indices_Mesh
                        is_bound = obj.display_type == 'BOUNDS'
                        draw_face = snap_face and not is_bound and obj.display_type != 'WIRE'
                        draw_edge = snap_edge and not is_bound
                        draw_vert = snap_vert and not is_bound
                        snap_obj.data.append(GPU_Indices_Mesh(self.depsgraph, obj, draw_face, draw_edge, draw_vert))

                    snap_obj.data[1].set_draw_mode(snap_face, snap_edge, snap_vert)

                    if snap_obj == main_snap_obj:
                        snap_obj.data[1].Draw(self._offset_cur, snap_obj.mat, 0.0001)
                    else:
                        snap_obj.data[1].Draw(self._offset_cur, snap_obj.mat)
                    self._offset_cur += snap_obj.data[1].get_tot_elems()

                    tmp = self.snap_objects[self.drawn_count]
                    self.snap_objects[self.drawn_count] = self.snap_objects[i]
                    self.snap_objects[i] = tmp

                    self.drawn_count += 1
                    update_buffer = True

            if update_buffer:
                self._read_buffer()
                # import numpy as np
                # a = np.array(self._snap_buffer)
                # print(a)

            snap_obj, index = self._get_nearest_index(mval)
            # print("index:", index)
            if snap_obj:
                ret = self._get_loc(snap_obj, index)

        gpu.state.program_point_size_set(False)
        gpu.state.depth_mask_set(False)
        gpu.state.depth_test_set('NONE')
        _Internal.gpu_Indices_restore_state()

        return (snap_obj, *ret)

    def free(self):
        self.__del__()
        self.freed = True


def global_snap_context_get(depsgraph, region, space):
    if _Internal.global_snap_context is None:
        import atexit

        _Internal.global_snap_context = SnapContext(depsgraph, region, space)

        # Make sure we only registered the callback once.
        atexit.unregister(_Internal.snap_context_free)
        atexit.register(_Internal.snap_context_free)

    elif (depsgraph and region and space):
        _Internal.global_snap_context.update_viewport_context(depsgraph, region, space, True)

    return _Internal.global_snap_context
