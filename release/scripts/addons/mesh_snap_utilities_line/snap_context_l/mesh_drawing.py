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
from mathutils import Matrix

def load_shader(shadername):
    from os import path
    with open(path.join(path.dirname(__file__), 'shaders', shadername), 'r') as f:
        return f.read()

def get_mesh_vert_co_array(me):
    tot_vco = len(me.vertices)
    if tot_vco:
        import numpy as np

        verts_co = np.empty(len(me.vertices) * 3, 'f4')
        me.vertices.foreach_get("co", verts_co)
        verts_co.shape = (-1, 3)
        return verts_co
    return ()


def get_bmesh_vert_co_array(bm):
    tot_vco = len(bm.verts)
    if tot_vco:
        import numpy as np

        return np.array([v.co for v in bm.verts], 'f4')
    return ()


def get_mesh_tri_verts_array(me):
    me.calc_loop_triangles()
    len_triangles = len(me.loop_triangles)
    if len_triangles:
        import numpy as np

        tris = np.empty(len_triangles * 3, 'i4')
        me.loop_triangles.foreach_get("vertices", tris)
        tris.shape = (-1, 3)
        return tris
    return ()


def get_bmesh_tri_verts_array(bm):
    if bm.faces:
        import numpy as np

        l_tri_layer = bm.faces.layers.int.get("l_tri")
        if l_tri_layer is None:
            l_tri_layer = bm.faces.layers.int.new("l_tri")

        ltris = bm.calc_loop_triangles()
        tris = np.empty((len(ltris), 3), 'i4')
        i = 0

        bm.faces.ensure_lookup_table()
        last_face = bm.faces[-1]
        for ltri in ltris:
            face = ltri[0].face
            if not face.hide:
                tris[i] = ltri[0].vert.index, ltri[1].vert.index, ltri[2].vert.index
                if last_face != face:
                    last_face = face
                    face[l_tri_layer] = i
                i += 1
        if i:
            tris.resize((i, 3), refcheck=False)
            return tris
    return ()


def get_mesh_edge_verts_array(me):
    tot_edges = len(me.edges)
    if tot_edges:
        import numpy as np

        edge_verts = np.empty(tot_edges * 2, 'i4')
        me.edges.foreach_get("vertices", edge_verts)
        edge_verts.shape = tot_edges, 2
        return edge_verts
    return ()


def get_bmesh_edge_verts_array(bm):
    bm.edges.ensure_lookup_table()
    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges if not e.hide]
    if edges:
        import numpy as np
        return np.array(edges, 'i4')
    return ()


def get_mesh_loosevert_array(me, edges):
    import numpy as np

    verts = np.arange(len(me.vertices))

    mask = np.in1d(verts, edges, invert=True)

    verts = verts[mask]
    if len(verts):
        return verts
    return ()


def get_bmesh_loosevert_array(bm):
    looseverts = [v.index for v in bm.verts if not (v.link_edges or v.hide)]
    if looseverts:
        import numpy as np
        return np.array(looseverts, 'i4')
    return ()


class _Mesh_Arrays():
    def __init__(self, obj, create_tris, create_edges, create_looseverts):
        self.tri_verts = self.edge_verts = self.looseverts = ()
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

                del bm
            else:
                import bpy
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
            import numpy as np

            self.verts_co = np.zeros((1,3), 'f4')
            self.looseverts = np.zeros(1, 'i4')

    def __del__(self):
        del self.tri_verts, self.edge_verts, self.looseverts
        del self.verts_co


class GPU_Indices_Mesh():
    __slots__ = (
        "ob_data",
        "draw_tris",
        "draw_edges",
        "draw_verts",
        "batch_tris",
        "batch_edges",
        "batch_lverts",
        "verts_co",
        "tri_verts",
        "edge_verts",
        "looseverts",
        "first_index",
        "users"
    )

    _Hash = {}
    shader = None

    @classmethod
    def end_opengl(cls):
        del cls.shader
        del cls.P

        del cls

    @staticmethod
    def init_opengl():
        cls = GPU_Indices_Mesh
        # OpenGL was already initialized, nothing to do here.
        if cls.shader is not None:
            return

        import atexit
        import gpu

        # Make sure we only registered the callback once.
        atexit.unregister(cls.end_opengl)
        atexit.register(cls.end_opengl)

        cls.shader = gpu.types.GPUShader(
                load_shader("ID_color_vert.glsl"),
                load_shader("ID_color_frag.glsl"),
                )
        #cls.unif_use_clip_planes = cls.shader.uniform_from_name('use_clip_planes')
        #cls.unif_clip_plane = cls.shader.uniform_from_name('clip_plane')
        cls.unif_offset = cls.shader.uniform_from_name('offset')

        cls.P = Matrix()


    @staticmethod
    def set_ModelViewMatrix(MV):
        import gpu
        gpu.matrix.load_matrix(MV)


    def __init__(self, depsgraph, obj, draw_tris, draw_edges, draw_verts):
        self.ob_data = obj.original.data

        if self.ob_data in GPU_Indices_Mesh._Hash:
            src = GPU_Indices_Mesh._Hash[self.ob_data]
            dst = self

            dst.draw_tris    = src.draw_tris
            dst.draw_edges   = src.draw_edges
            dst.draw_verts   = src.draw_verts
            dst.batch_tris   = src.batch_tris
            dst.batch_edges  = src.batch_edges
            dst.batch_lverts = src.batch_lverts
            dst.verts_co     = src.verts_co
            dst.tri_verts    = src.tri_verts
            dst.edge_verts   = src.edge_verts
            dst.looseverts   = src.looseverts
            dst.users        = src.users
            dst.users.append(self)

            update = False

        else:
            GPU_Indices_Mesh._Hash[self.ob_data] = self
            self.users = [self]
            update = True;

        if update:
            import gpu

            self.draw_tris = draw_tris
            self.draw_edges = draw_edges
            self.draw_verts = draw_verts

            GPU_Indices_Mesh.init_opengl()

            ## Init Array ##
            mesh_arrays = _Mesh_Arrays(depsgraph.id_eval_get(obj), draw_tris, draw_edges, draw_verts)

            if mesh_arrays.verts_co is None:
                self.draw_tris = False
                self.draw_edges = False
                self.draw_verts = False
                self.tri_verts = ()
                self.edge_verts = ()
                self.looseverts = ()
                return

            ## Create VBO for vertices ##
            self.verts_co = mesh_arrays.verts_co
            self.tri_verts = mesh_arrays.tri_verts
            self.edge_verts = mesh_arrays.edge_verts
            self.looseverts = mesh_arrays.looseverts
            del mesh_arrays

            format = gpu.types.GPUVertFormat()
            format.attr_add(id="pos", comp_type='F32', len=3, fetch_mode='FLOAT')

            vbo = gpu.types.GPUVertBuf(format, len = len(self.verts_co))

            vbo.attr_fill(0, data = self.verts_co)

            ## Create Batch for Tris ##
            if len(self.tri_verts) > 0:
                ebo = gpu.types.GPUIndexBuf(type = "TRIS", seq = self.tri_verts)
                self.batch_tris = gpu.types.GPUBatch(type = "TRIS", buf = vbo, elem = ebo)
                self.batch_tris.program_set(self.shader)
            else:
                self.draw_tris = False
                self.batch_tris = None

            ## Create Batch for Edges ##
            if len(self.edge_verts) > 0:
                ebo = gpu.types.GPUIndexBuf(type = "LINES", seq = self.edge_verts)
                self.batch_edges = gpu.types.GPUBatch(type = "LINES", buf = vbo, elem = ebo)
                self.batch_edges.program_set(self.shader)
            else:
                self.draw_edges = False
                self.batch_edges = None

            ## Create Batch for Loose Verts ##
            if len(self.looseverts) > 0:
                ebo = gpu.types.GPUIndexBuf(type = "POINTS", seq = self.looseverts)
                self.batch_lverts = gpu.types.GPUBatch(type = "POINTS", buf = vbo, elem = ebo)
                self.batch_lverts.program_set(self.shader)
            else:
                self.draw_verts = False
                self.batch_lverts = None


    def get_tot_elems(self):
        tot = 0
        if self.draw_tris:
            tot += len(self.tri_verts)

        if self.draw_edges:
            tot += len(self.edge_verts)

        if self.draw_verts:
            tot += len(self.looseverts)

        return tot


    def set_draw_mode(self, draw_tris, draw_edges, draw_verts):
        self.draw_tris = draw_tris and len(self.tri_verts) > 0
        self.draw_edges = draw_edges and len(self.edge_verts) > 0
        self.draw_verts = draw_verts and len(self.looseverts) > 0


    def Draw(self, index_offset, depth_offset = -0.00005):
        self.first_index = index_offset
        if self.draw_tris:
            self.shader.uniform_int("offset", (index_offset,))
            self.batch_tris.draw(self.shader)
            index_offset += len(self.tri_verts)
            bgl.glDepthRange(depth_offset, 1 + depth_offset)

        if self.draw_edges:
            self.shader.uniform_int("offset", (index_offset,))
            #bgl.glLineWidth(3.0)
            self.batch_edges.draw(self.shader)
            #bgl.glLineWidth(1.0)
            index_offset += len(self.edge_verts)

        if self.draw_verts:
            self.shader.uniform_int("offset", (index_offset,))
            self.batch_lverts.draw(self.shader)

        bgl.glDepthRange(0.0, 1.0)


    def get_tri_co(self, index):
        return self.verts_co[self.tri_verts[index]]

    def get_edge_co(self, index):
        return self.verts_co[self.edge_verts[index]]

    def get_loosevert_co(self, index):
        return self.verts_co[self.looseverts[index]]

    def get_loop_tri_co_by_bmface(self, bm, bmface):
        l_tri_layer = bm.faces.layers.int["l_tri"]
        tri = bmface[l_tri_layer]
        return self.verts_co[self.tri_verts[tri : tri + len(bmface.verts) - 2]]


    def get_tri_verts(self, index):
        return self.tri_verts[index]

    def get_edge_verts(self, index):
        return self.edge_verts[index]

    def get_loosevert_index(self, index):
        return self.looseverts[index]

    def free(self):
        self.users.remove(self)
        if len(self.users) == 0:
            del self.batch_tris
            del self.batch_edges
            del self.batch_lverts
            del self.verts_co
            del self.tri_verts
            del self.edge_verts
            del self.looseverts
            GPU_Indices_Mesh._Hash.pop(self.ob_data)

        #print('mesh_del', self.obj.name)


def gpu_Indices_enable_state():
    import gpu

    GPU_Indices_Mesh.init_opengl()
    gpu.matrix.push()
    gpu.matrix.push_projection()
    gpu.matrix.load_projection_matrix(GPU_Indices_Mesh.P)
    GPU_Indices_Mesh.shader.bind()


def gpu_Indices_restore_state():
    import gpu

    gpu.matrix.pop()
    gpu.matrix.pop_projection()


def gpu_Indices_use_clip_planes(rv3d, value):
    pass #TODO
    #if rv3d.use_clip_planes:
        #planes = bgl.Buffer(bgl.GL_FLOAT, (6, 4), rv3d.clip_planes)

        #_store_current_shader_state(PreviousGLState)
        #GPU_Indices_Mesh.init_opengl()
        #bgl.glUseProgram(GPU_Indices_Mesh.shader.program)
        #bgl.glUniform1i(GPU_Indices_Mesh.unif_use_clip_planes, value)

        #bgl.glUniform4fv(GPU_Indices_Mesh.unif_clip_plane, 4, planes)

        #_restore_shader_state(PreviousGLState)


def gpu_Indices_set_ProjectionMatrix(P):
    import gpu

    gpu.matrix.load_projection_matrix(P)
    GPU_Indices_Mesh.P[:] = P


def gpu_Indices_mesh_cache_clear():
    GPU_Indices_Mesh._Hash.clear()
