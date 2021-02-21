### BEGIN GPL LICENSE BLOCK #####
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
import gpu
from mathutils import Vector


class SnapDrawn():
    __slots__ = (\
        'out_color',
        'face_color',
        'edge_color',
        'vert_color',
        'center_color',
        'perpendicular_color',
        'constrain_shift_color',
        'axis_x_color',
        'axis_y_color',
        'axis_z_color',
        '_format_pos',
        '_format_pos_and_color',
        '_program_unif_col',
        '_program_smooth_col',
        '_batch_point',)

    def __init__(self, out_color, face_color,
                 edge_color, vert_color, center_color,
                 perpendicular_color, constrain_shift_color,
                 axis_x_color, axis_y_color, axis_z_color):

        import gpu

        self.out_color = out_color
        self.face_color = face_color
        self.edge_color = edge_color
        self.vert_color = vert_color
        self.center_color = center_color
        self.perpendicular_color = perpendicular_color
        self.constrain_shift_color = constrain_shift_color

        self.axis_x_color = axis_x_color
        self.axis_y_color = axis_y_color
        self.axis_z_color = axis_z_color

        self._format_pos = gpu.types.GPUVertFormat()
        self._format_pos.attr_add(id="pos", comp_type='F32', len=3, fetch_mode='FLOAT')

        self._format_pos_and_color = gpu.types.GPUVertFormat()
        self._format_pos_and_color.attr_add(id="pos", comp_type='F32', len=3, fetch_mode='FLOAT')
        self._format_pos_and_color.attr_add(id="color", comp_type='F32', len=4, fetch_mode='FLOAT')

        self._program_unif_col = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
        self._program_smooth_col = gpu.shader.from_builtin("3D_SMOOTH_COLOR")

        self._batch_point = None


    def _gl_state_push(self):
        gpu.state.program_point_size_set(False)
        gpu.state.blend_set('ALPHA')

    def _gl_state_restore(self):
        gpu.state.blend_set('NONE')

    def batch_line_strip_create(self, coords):
        from gpu.types import (
            GPUVertBuf,
            GPUBatch,
        )

        vbo = GPUVertBuf(self._format_pos, len = len(coords))
        vbo.attr_fill(0, data = coords)
        batch_lines = GPUBatch(type = "LINE_STRIP", buf = vbo)
        return batch_lines

    def batch_lines_smooth_color_create(self, coords, colors):
        from gpu.types import (
            GPUVertBuf,
            GPUBatch,
        )

        vbo = GPUVertBuf(self._format_pos_and_color, len = len(coords))
        vbo.attr_fill(0, data = coords)
        vbo.attr_fill(1, data = colors)
        batch_lines = GPUBatch(type = "LINES", buf = vbo)
        return batch_lines

    def batch_triangles_create(self, coords):
        from gpu.types import (
            GPUVertBuf,
            GPUBatch,
        )

        vbo = GPUVertBuf(self._format_pos, len = len(coords))
        vbo.attr_fill(0, data = coords)
        batch_tris = GPUBatch(type = "TRIS", buf = vbo)
        return batch_tris

    def batch_point_get(self):
        if self._batch_point is None:
            from gpu.types import (
                GPUVertBuf,
                GPUBatch,
            )
            vbo = GPUVertBuf(self._format_pos, len = 1)
            vbo.attr_fill(0, ((0.0, 0.0, 0.0),))
            self._batch_point = GPUBatch(type = "POINTS", buf = vbo)
        return self._batch_point

    def draw(self, type, location, list_verts_co, vector_constrain, prevloc):
        import gpu

        self._gl_state_push()
        gpu.matrix.push()
        self._program_unif_col.bind()

        if list_verts_co:
            # draw 3d line OpenGL in the 3D View
            winmat = gpu.matrix.get_projection_matrix()
            winmat[3][2] -= 0.0001
            gpu.matrix.push_projection()
            gpu.matrix.load_projection_matrix(winmat)
            gpu.state.line_width_set(3.0)

            batch = self.batch_line_strip_create([v.to_tuple() for v in list_verts_co] + [location.to_tuple()])

            self._program_unif_col.bind()
            self._program_unif_col.uniform_float("color", (1.0, 0.8, 0.0, 0.5))
            batch.draw(self._program_unif_col)
            gpu.matrix.pop_projection()
            del batch

        gpu.state.depth_test_set('NONE')

        point_batch = self.batch_point_get()
        if vector_constrain:
            if prevloc:
                gpu.state.point_size_set(5.0)
                gpu.matrix.translate(prevloc)

                self._program_unif_col.bind()
                self._program_unif_col.uniform_float("color", (1.0, 1.0, 1.0, 0.5))
                point_batch.draw(self._program_unif_col)
                gpu.matrix.translate(-prevloc)

            if vector_constrain[2] == 'X':
                Color4f = self.axis_x_color
            elif vector_constrain[2] == 'Y':
                Color4f = self.axis_y_color
            elif vector_constrain[2] == 'Z':
                Color4f = self.axis_z_color
            else:
                Color4f = self.constrain_shift_color
        else:
            if type == 'OUT':
                Color4f = self.out_color
            elif type == 'FACE':
                Color4f = self.face_color
            elif type == 'EDGE':
                Color4f = self.edge_color
            elif type == 'VERT':
                Color4f = self.vert_color
            elif type == 'CENTER':
                Color4f = self.center_color
            elif type == 'PERPENDICULAR':
                Color4f = self.perpendicular_color
            else: # type == None
                Color4f = self.out_color

        gpu.state.point_size_set(10.0)

        gpu.matrix.translate(location)
        self._program_unif_col.bind()
        self._program_unif_col.uniform_float("color", Color4f)
        point_batch.draw(self._program_unif_col)

        # restore opengl defaults
        gpu.state.point_size_set(1.0)
        gpu.state.line_width_set(1.0)
        gpu.state.depth_test_set('LESS_EQUAL')

        gpu.matrix.pop()
        self._gl_state_restore()

    def draw_elem(self, snap_obj, bm, elem):
        #TODO: Cache coords (because antialiasing)
        import gpu
        from bmesh.types import(
            BMVert,
            BMEdge,
            BMFace,
        )

        with gpu.matrix.push_pop():
            self._gl_state_push()
            gpu.state.depth_test_set('NONE')

            gpu.matrix.multiply_matrix(snap_obj.mat)

            if isinstance(elem, BMVert):
                if elem.link_edges:
                    import numpy as np

                    color = self.vert_color
                    edges = np.empty((len(elem.link_edges), 2), [("pos", "f4", 3), ("color", "f4", 4)])
                    edges["pos"][:, 0] = elem.co
                    edges["pos"][:, 1] = [e.other_vert(elem).co for e in elem.link_edges]
                    edges["color"][:, 0] = color
                    edges["color"][:, 1] = (color[0], color[1], color[2], 0.0)
                    edges.shape = -1

                    self._program_smooth_col.bind()
                    gpu.state.line_width_set(3.0)
                    batch = self.batch_lines_smooth_color_create(edges["pos"], edges["color"])
                    batch.draw(self._program_smooth_col)
                    gpu.state.line_width_set(1.0)
            else:
                self._program_unif_col.bind()

                if isinstance(elem, BMEdge):
                    self._program_unif_col.bind()
                    self._program_unif_col.uniform_float("color", self.edge_color)

                    gpu.state.line_width_set(3.0)
                    batch = self.batch_line_strip_create([v.co for v in elem.verts])
                    batch.draw(self._program_unif_col)
                    gpu.state.line_width_set(1.0)

                elif isinstance(elem, BMFace):
                    if len(snap_obj.data) == 2:
                        face_color = self.face_color[0], self.face_color[1], self.face_color[2], self.face_color[3] * 0.2
                        self._program_unif_col.bind()
                        self._program_unif_col.uniform_float("color", face_color)

                        tris = snap_obj.data[1].get_loop_tri_co_by_bmface(bm, elem)
                        tris.shape = (-1, 3)
                        batch = self.batch_triangles_create(tris)
                        batch.draw(self._program_unif_col)

            # restore opengl defaults
            gpu.state.depth_test_set('LESS_EQUAL')

        self._gl_state_restore()
