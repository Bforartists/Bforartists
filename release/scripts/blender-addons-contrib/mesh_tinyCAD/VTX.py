import bpy
import sys
import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_line_line as LineIntersect
from mathutils.geometry import intersect_point_line as PtLineIntersect

from mesh_tinyCAD import cad_module as cm


def getVTX(self):
    self.idx1, self.idx2 = self.selected_edges
    self.edge1 = cm.coords_tuple_from_edge_idx(self.bm, self.idx1)
    self.edge2 = cm.coords_tuple_from_edge_idx(self.bm, self.idx2)
    self.point = cm.get_intersection(self.edge1, self.edge2)
    self.edges = cm.find_intersecting_edges(
        self.bm, self.point, self.idx1, self.idx2)


def add_edges(self, idxs):

    # precaution?
    if hasattr(self.bm.verts, "ensure_lookup_table"):
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()

    for e in idxs:
        v1 = self.bm.verts[-1]
        v2 = self.bm.verts[e]
        self.bm.edges.new((v1, v2))


def remove_earmarked_edges(self, earmarked):
    edges_select = [e for e in self.bm.edges if e.index in earmarked]
    bmesh.ops.delete(self.bm, geom=edges_select, context=2)


def checkVTX(self, context):
    '''
    - decides VTX automatically.
    - remembers edges attached to current selection, for later.
    '''

    # precaution?
    if hasattr(self.bm.verts, "ensure_lookup_table"):
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()

    # if either of these edges share a vertex, return early.
    indices = cm.vertex_indices_from_edges_tuple(self.bm, self.selected_edges)
    if cm.duplicates(indices):
        msg = "edges share a vertex, degenerate case, returning early"
        self.report({"WARNING"}, msg)
        return False

    # find which edges intersect
    getVTX(self)

    # check coplanar, or parallel.
    if [] == self.edges:
        coplanar = cm.test_coplanar(self.edge1, self.edge2)
        if not coplanar:
            msg = "parallel or not coplanar! returning early"
            self.report({"WARNING"}, msg)
            return False

    return True


def doVTX(self):
    '''
    At this point we know that there is an intersection, and if it
    is V, T or X.
    - If both are None, then both edges are projected towards point. (V)
    - If only one is None, then it's a projection onto a real edge (T)
    - Else, then the intersection lies on both edges (X)
    '''
    print('point:', self.point)
    print('edges selected:', self.idx1, self.idx2)
    print('edges to use:', self.edges)

    self.bm.verts.new((self.point))

    earmarked = self.edges
    pt = self.point

    # V (projection of both edges)
    if [] == earmarked:
        cl_vert1 = cm.closest_idx(pt, self.bm.edges[self.idx1])
        cl_vert2 = cm.closest_idx(pt, self.bm.edges[self.idx2])
        add_edges(self, [cl_vert1, cl_vert2])

    # X (weld intersection)
    elif len(earmarked) == 2:
        vector_indices = cm.vertex_indices_from_edges_tuple(self.bm, earmarked)
        add_edges(self, vector_indices)

    # T (extend towards)
    else:
        to_edge_idx = self.edges[0]
        from_edge_idx = self.idx1 if to_edge_idx == self.idx2 else self.idx2

        # make 3 new edges: 2 on the towards, 1 as extender
        cl_vert = cm.closest_idx(pt, self.bm.edges[from_edge_idx])
        to_vert1, to_vert2 = cm.vert_idxs_from_edge_idx(self.bm, to_edge_idx)
        roto_indices = [cl_vert, to_vert1, to_vert2]
        add_edges(self, roto_indices)

    # final refresh before returning to user.
    if earmarked:
        remove_earmarked_edges(self, earmarked)
    bmesh.update_edit_mesh(self.me, True)


class AutoVTX(bpy.types.Operator):
    bl_idname = 'view3d.autovtx'
    bl_label = 'autoVTX'
    # bl_options = {'REGISTER', 'UNDO'}

    VTX_PRECISION = 1.0e-5  # or 1.0e-6 ..if you need

    @classmethod
    def poll(self, context):
        '''
        - only activate if two selected edges
        - and both are not hidden
        '''
        obj = context.active_object
        self.me = obj.data
        self.bm = bmesh.from_edit_mesh(self.me)

        # self.me.update()
        if hasattr(self.bm.verts, "ensure_lookup_table"):
            self.bm.verts.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()

        if obj is not None and obj.type == 'MESH':
            edges = self.bm.edges
            ok = lambda v: v.select and not v.hide
            idxs = [v.index for v in edges if ok(v)]
            if len(idxs) is 2:
                self.selected_edges = idxs
                return True

    def execute(self, context):

        self.me.update()
        if checkVTX(self, context):
            doVTX(self)

        return {'FINISHED'}
