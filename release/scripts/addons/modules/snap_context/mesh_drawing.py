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


import bgl
import bmesh
import numpy as np
from mathutils import Matrix

from .utils_shader import Shader


def load_shader(shadername):
    from os import path
    with open(path.join(path.dirname(__file__), 'resources', shadername), 'r') as f:
        return f.read()

def gl_buffer_void_as_long(value):
    import ctypes
    a = (ctypes.c_byte * 1).from_address(value)
    return bgl.Buffer(bgl.GL_BYTE, 1, a)

def get_mesh_vert_co_array(me):
    tot_vco = len(me.vertices)
    if tot_vco:
        verts_co = np.empty(len(me.vertices) * 3, 'f4')
        me.vertices.foreach_get("co", verts_co)
        verts_co.shape = (-1, 3)
        return verts_co
    return None


def get_bmesh_vert_co_array(bm):
    tot_vco = len(bm.verts)
    if tot_vco:
        return np.array([v.co for v in bm.verts], 'f4')
    return None


def get_mesh_tri_verts_array(me):
    me.calc_tessface()
    len_tessfaces = len(me.tessfaces)
    if len_tessfaces:
        tessfaces = np.empty(len_tessfaces * 4, 'i4')
        me.tessfaces.foreach_get("vertices_raw", tessfaces)
        tessfaces.shape = (-1, 4)

        quad_indices = tessfaces[:, 3].nonzero()[0]
        tris = np.empty(((len_tessfaces + len(quad_indices)), 3), 'i4')

        tris[:len_tessfaces] = tessfaces[:, :3]
        tris[len_tessfaces:] = tessfaces[quad_indices][:, (0, 2, 3)]

        del tessfaces
        return tris
    return None


def get_bmesh_tri_verts_array(bm):
    ltris = bm.calc_tessface()
    tris = [[ltri[0].vert.index, ltri[1].vert.index, ltri[2].vert.index] for ltri in ltris if not ltri[0].face.hide]
    if tris:
        return np.array(tris, 'i4')
    return None


def get_mesh_edge_verts_array(me):
    tot_edges = len(me.edges)
    if tot_edges:
        edge_verts = np.empty(tot_edges * 2, 'i4')
        me.edges.foreach_get("vertices", edge_verts)
        edge_verts.shape = tot_edges, 2
        return edge_verts
    return None


def get_bmesh_edge_verts_array(bm):
    bm.edges.ensure_lookup_table()
    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges if not e.hide]
    if edges:
        return np.array(edges, 'i4')
    return None


def get_mesh_loosevert_array(me, edges):
    verts = np.arange(len(me.vertices))

    mask = np.in1d(verts, edges, invert=True)

    verts = verts[mask]
    if len(verts):
        return verts
    return None


def get_bmesh_loosevert_array(bm):
    looseverts = [v.index for v in bm.verts if not (v.link_edges or v.hide)]
    if looseverts:
        return np.array(looseverts, 'i4')
    return None


class _Mesh_Arrays():
    def __init__(self, obj, create_tris, create_edges, create_looseverts):
        self.tri_verts = self.edge_verts = self.looseverts = None
        self.tris_co = self.edges_co = self.looseverts_co = None
        if obj.type == 'MESH':
            me = obj.data
            if me.is_editmode:
                bm = bmesh.from_edit_mesh(me)
                bm.verts.ensure_lookup_table()

                self.verts_co = get_bmesh_vert_co_array(bm)

                if create_tris:
                    self.tri_verts = get_bmesh_tri_verts_array(bm)
                if create_edges:
                    self.edge_verts = get_bmesh_edge_verts_array(bm)
                if create_looseverts:
                    self.looseverts = get_bmesh_loosevert_array(bm)
            else:
                self.verts_co = get_mesh_vert_co_array(me)

                if create_tris:
                    self.tri_verts = get_mesh_tri_verts_array(me)
                if create_edges:
                    self.edge_verts = get_mesh_edge_verts_array(me)
                if create_looseverts:
                    edge_verts = self.edge_verts
                    if edge_verts is None:
                        edge_verts = get_mesh_edge_verts_array(me)
                    self.looseverts = get_mesh_loosevert_array(me, edge_verts)
                    del edge_verts

        else: #TODO
            self.verts_co = np.zeros((1,3), 'f4')
            self.looseverts = np.zeros(1, 'i4')

    def __del__(self):
        del self.tri_verts, self.edge_verts, self.looseverts
        del self.verts_co


class GPU_Indices_Mesh():
    shader = None

    @classmethod
    def end_opengl(cls):
        del cls.shader
        del cls._NULL
        del cls.P
        del cls.MV
        del cls.MVP
        del cls.vert_index
        del cls.tri_co
        del cls.edge_co
        del cls.vert_co

        del cls

    @classmethod
    def init_opengl(cls):
        # OpenGL was already initialized, nothing to do here.
        if cls.shader is not None:
            return

        import atexit

        # Make sure we only registered the callback once.
        atexit.unregister(cls.end_opengl)
        atexit.register(cls.end_opengl)

        cls.shader = Shader(
            load_shader('3D_vert.glsl'),
            None,
            load_shader('primitive_id_frag.glsl'),
        )

        cls.unif_use_clip_planes = bgl.glGetUniformLocation(cls.shader.program, 'use_clip_planes')
        cls.unif_clip_plane = bgl.glGetUniformLocation(cls.shader.program, 'clip_plane')

        cls._NULL = gl_buffer_void_as_long(0)

        cls.unif_MVP = bgl.glGetUniformLocation(cls.shader.program, 'MVP')
        cls.unif_MV = bgl.glGetUniformLocation(cls.shader.program, 'MV')
        cls.unif_offset = bgl.glGetUniformLocation(cls.shader.program, 'offset')

        cls.attr_pos = bgl.glGetAttribLocation(cls.shader.program, 'pos')
        cls.attr_primitive_id = bgl.glGetAttribLocation(cls.shader.program, 'primitive_id')

        cls.P = bgl.Buffer(bgl.GL_FLOAT, (4, 4))
        cls.MV = bgl.Buffer(bgl.GL_FLOAT, (4, 4))
        cls.MVP = bgl.Buffer(bgl.GL_FLOAT, (4, 4))

        # returns of public API #
        cls.vert_index = bgl.Buffer(bgl.GL_INT, 1)

        cls.tri_co = bgl.Buffer(bgl.GL_FLOAT, (3, 3))
        cls.edge_co = bgl.Buffer(bgl.GL_FLOAT, (2, 3))
        cls.vert_co = bgl.Buffer(bgl.GL_FLOAT, 3)

    def __init__(self, obj, draw_tris, draw_edges, draw_verts):
        GPU_Indices_Mesh.init_opengl()

        self.obj = obj
        self.draw_tris = draw_tris
        self.draw_edges = draw_edges
        self.draw_verts = draw_verts

        self.vbo = None
        self.vbo_tris = None
        self.vbo_edges = None
        self.vbo_verts = None

        ## Create VAO ##
        self.vao = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenVertexArrays(1, self.vao)
        bgl.glBindVertexArray(self.vao[0])

        ## Init Array ##
        mesh_arrays = _Mesh_Arrays(obj, draw_tris, draw_edges, draw_verts)

        ## Create VBO for vertices ##
        if mesh_arrays.verts_co is None:
            self.draw_tris = False
            self.draw_edges = False
            self.draw_verts = False
            return

        if False:  # Blender 2.8
            self.vbo_len = len(mesh_arrays.verts_co)

            self.vbo = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo[0])
            verts_co = bgl.Buffer(bgl.GL_FLOAT, mesh_arrays.verts_co.shape, mesh_arrays.verts_co)
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.vbo_len * 12, verts_co, bgl.GL_STATIC_DRAW)

        ## Create VBO for Tris ##
        if mesh_arrays.tri_verts is not None:
            self.tri_verts = mesh_arrays.tri_verts
            self.num_tris = len(self.tri_verts)

            np_tris_co = mesh_arrays.verts_co[mesh_arrays.tri_verts]
            np_tris_co = bgl.Buffer(bgl.GL_FLOAT, np_tris_co.shape, np_tris_co)
            self.vbo_tris = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_tris)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tris[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_tris * 36, np_tris_co, bgl.GL_STATIC_DRAW)
            del np_tris_co

            tri_indices = np.repeat(np.arange(self.num_tris, dtype = 'f4'), 3)
            tri_indices = bgl.Buffer(bgl.GL_FLOAT, tri_indices.shape, tri_indices)
            self.vbo_tri_indices = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_tri_indices)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tri_indices[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_tris * 12, tri_indices, bgl.GL_STATIC_DRAW)
            del tri_indices

        else:
            self.num_tris = 0
            self.draw_tris = False

        ## Create VBO for Edges ##
        if mesh_arrays.edge_verts is not None:
            self.edge_verts = mesh_arrays.edge_verts
            self.num_edges = len(self.edge_verts)

            np_edges_co = mesh_arrays.verts_co[mesh_arrays.edge_verts]
            np_edges_co = bgl.Buffer(bgl.GL_FLOAT, np_edges_co.shape, np_edges_co)
            self.vbo_edges = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_edges)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edges[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_edges * 24, np_edges_co, bgl.GL_STATIC_DRAW)
            del np_edges_co

            edge_indices = np.repeat(np.arange(self.num_edges, dtype = 'f4'), 2)
            edge_indices = bgl.Buffer(bgl.GL_FLOAT, edge_indices.shape, edge_indices)
            self.vbo_edge_indices = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_edge_indices)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edge_indices[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_edges * 8, edge_indices, bgl.GL_STATIC_DRAW)
            del edge_indices
        else:
            self.num_edges = 0
            self.draw_edges = False

        ## Create EBO for Loose Verts ##
        if mesh_arrays.looseverts is not None:
            self.looseverts = mesh_arrays.looseverts
            self.num_verts = len(mesh_arrays.looseverts)

            np_lverts_co = mesh_arrays.verts_co[mesh_arrays.looseverts]
            np_lverts_co = bgl.Buffer(bgl.GL_FLOAT, np_lverts_co.shape, np_lverts_co)
            self.vbo_verts = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_verts)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_verts[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_verts * 12, np_lverts_co, bgl.GL_STATIC_DRAW)
            del np_lverts_co

            looseverts_indices = np.arange(self.num_verts, dtype = 'f4')
            looseverts_indices = bgl.Buffer(bgl.GL_FLOAT, looseverts_indices.shape, looseverts_indices)
            self.vbo_looseverts_indices = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenBuffers(1, self.vbo_looseverts_indices)
            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_looseverts_indices[0])
            bgl.glBufferData(bgl.GL_ARRAY_BUFFER, self.num_verts * 4, looseverts_indices, bgl.GL_STATIC_DRAW)
            del looseverts_indices
        else:
            self.num_verts = 0
            self.draw_verts = False

        del mesh_arrays

        bgl.glBindVertexArray(0)


    def get_tot_elems(self):
        tot = 0

        if self.draw_tris:
            tot += self.num_tris

        if self.draw_edges:
            tot += self.num_edges

        if self.draw_verts:
            tot += self.num_verts

        return tot


    def set_draw_mode(self, draw_tris, draw_edges, draw_verts):
        self.draw_tris = draw_tris and self.vbo_tris
        self.draw_edges = draw_edges and self.vbo_edges
        self.draw_verts = draw_verts and self.vbo_verts


    def set_ModelViewMatrix(self, MV):
        self.MV[:] = MV[:]
        self.MVP[:] = Matrix(self.P) * MV


    def Draw(self, index_offset):
        self.first_index = index_offset
        bgl.glUseProgram(self.shader.program)
        bgl.glBindVertexArray(self.vao[0])

        bgl.glUniformMatrix4fv(self.unif_MV, 1, bgl.GL_TRUE, self.MV)
        bgl.glUniformMatrix4fv(self.unif_MVP, 1, bgl.GL_TRUE, self.MVP)

        if self.draw_tris:
            bgl.glUniform1f(self.unif_offset, float(index_offset)) # bgl has no glUniform1ui :\

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tris[0])
            bgl.glEnableVertexAttribArray(self.attr_pos)
            bgl.glVertexAttribPointer(self.attr_pos, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL)

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tri_indices[0])
            bgl.glEnableVertexAttribArray(self.attr_primitive_id)
            bgl.glVertexAttribPointer(self.attr_primitive_id, 1, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL)

            bgl.glDrawArrays(bgl.GL_TRIANGLES, 0, self.num_tris * 3)

            index_offset += self.num_tris
            bgl.glDepthRange(-0.00005, 0.99995)

        if self.draw_edges:
            bgl.glUniform1f(self.unif_offset, float(index_offset)) #TODO: use glUniform1ui

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edges[0])
            bgl.glVertexAttribPointer(self.attr_pos, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL)
            bgl.glEnableVertexAttribArray(self.attr_pos)

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edge_indices[0])
            bgl.glVertexAttribPointer(self.attr_primitive_id, 1, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL)
            bgl.glEnableVertexAttribArray(self.attr_primitive_id)

            bgl.glDrawArrays(bgl.GL_LINES, 0, self.num_edges * 2)

            index_offset += self.num_edges

        if self.draw_verts:
            bgl.glUniform1f(self.unif_offset, float(index_offset)) #TODO: use glUniform1ui

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_verts[0])
            bgl.glVertexAttribPointer(self.attr_pos, 3, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL)
            bgl.glEnableVertexAttribArray(self.attr_pos)

            bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_looseverts_indices[0])
            bgl.glVertexAttribPointer(self.attr_primitive_id, 1, bgl.GL_FLOAT, bgl.GL_FALSE, 0, self._NULL)
            bgl.glEnableVertexAttribArray(self.attr_primitive_id)

            bgl.glDrawArrays(bgl.GL_POINTS, 0, self.num_verts)

        bgl.glDepthRange(0.0, 1.0)


    def get_tri_co(self, index):
        bgl.glBindVertexArray(self.vao[0])
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_tris[0])
        bgl.glGetBufferSubData(bgl.GL_ARRAY_BUFFER, index * 36, 36, self.tri_co)
        bgl.glBindVertexArray(0)
        return self.tri_co


    def get_edge_co(self, index):
        bgl.glBindVertexArray(self.vao[0])
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_edges[0])
        bgl.glGetBufferSubData(bgl.GL_ARRAY_BUFFER, index * 24, 24, self.edge_co)
        bgl.glBindVertexArray(0)
        return self.edge_co


    def get_loosevert_co(self, index):
        bgl.glBindVertexArray(self.vao[0])
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vbo_verts[0])
        bgl.glGetBufferSubData(bgl.GL_ARRAY_BUFFER, index * 12, 12, self.vert_co)
        bgl.glBindVertexArray(0)
        return self.vert_co


    def get_tri_verts(self, index):
        return self.tri_verts[index]


    def get_edge_verts(self, index):
        return self.edge_verts[index]


    def get_loosevert_index(self, index):
        return self.looseverts[index]


    def __del__(self):
        if self.vbo_tris:
            bgl.glDeleteBuffers(1, self.vbo_tris)
            bgl.glDeleteBuffers(1, self.vbo_tri_indices)
            del self.tri_verts

        if self.vbo_edges:
            bgl.glDeleteBuffers(1, self.vbo_edges)
            bgl.glDeleteBuffers(1, self.vbo_edge_indices)
            del self.edge_verts

        if self.vbo_verts:
            bgl.glDeleteBuffers(1, self.vbo_verts)
            bgl.glDeleteBuffers(1, self.vbo_looseverts_indices)
            del self.looseverts

        bgl.glDeleteVertexArrays(1, self.vao)
        #print('mesh_del', self.obj.name)


class PreviousGLState:
    buf = bgl.Buffer(bgl.GL_INT, (4, 1))
    cur_program = buf[0]
    cur_vao = buf[1]
    cur_vbo = buf[2]
    cur_ebo = buf[3]


def _store_current_shader_state(cls):
    bgl.glGetIntegerv(bgl.GL_CURRENT_PROGRAM, cls.cur_program)
    bgl.glGetIntegerv(bgl.GL_VERTEX_ARRAY_BINDING, cls.cur_vao)
    bgl.glGetIntegerv(bgl.GL_ARRAY_BUFFER_BINDING, cls.cur_vbo)
    bgl.glGetIntegerv(bgl.GL_ELEMENT_ARRAY_BUFFER_BINDING, cls.cur_ebo)


def _restore_shader_state(cls):
    bgl.glUseProgram(cls.cur_program[0])
    bgl.glBindVertexArray(cls.cur_vao[0])
    bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, cls.cur_vbo[0])
    bgl.glBindBuffer(bgl.GL_ELEMENT_ARRAY_BUFFER, cls.cur_ebo[0])


def gpu_Indices_enable_state():
    _store_current_shader_state(PreviousGLState)

    GPU_Indices_Mesh.init_opengl()
    bgl.glUseProgram(GPU_Indices_Mesh.shader.program)
    #bgl.glBindVertexArray(GPU_Indices_Mesh.vao[0])


def gpu_Indices_restore_state():
    bgl.glBindVertexArray(0)
    _restore_shader_state(PreviousGLState)


def gpu_Indices_use_clip_planes(rv3d, value):
    if rv3d.use_clip_planes:
        planes = bgl.Buffer(bgl.GL_FLOAT, (6, 4), rv3d.clip_planes)

        _store_current_shader_state(PreviousGLState)
        GPU_Indices_Mesh.init_opengl()
        bgl.glUseProgram(GPU_Indices_Mesh.shader.program)
        bgl.glUniform1i(GPU_Indices_Mesh.unif_use_clip_planes, value)

        bgl.glUniform4fv(GPU_Indices_Mesh.unif_clip_plane, 4, planes)

        _restore_shader_state(PreviousGLState)


def gpu_Indices_set_ProjectionMatrix(P):
    GPU_Indices_Mesh.P[:] = P
