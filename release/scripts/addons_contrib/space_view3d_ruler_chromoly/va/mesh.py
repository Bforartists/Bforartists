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
########################################################
#
# Before changing this file please discuss with admins.
#
########################################################
# <pep8 compliant>

import bpy
from bpy.props import *
import math
import mathutils as Math
from mathutils import Matrix, Euler, Vector, Quaternion
from .utils import the_other


def keypath(edge_keys):
    vkdict = {}
    tip = -1
    tip_sub = edge_keys[0][0]
    tipnum = 0
    verts = []
    closed = 1

    for k in edge_keys:
        for v in k:
            if v not in vkdict:
                vkdict[v] = [k]
            else:
                vkdict[v].append(k)

    for v, keys in vkdict.items():
        if len(keys) == 1:
            closed = 0
            tipnum += 1
            for k in keys:
                if k.index(v) == 0:
                    tip = v
                else:
                    tip_sub = v
    if tipnum >= 3:
        return []

    if tip == -1:
        tip = tip_sub

    verts.append(tip)

    while True:
        v = verts[-1]
        keys = vkdict[v]
        for k in keys:
            v2 = the_other(k, v)
            if v2 not in verts:
                verts.append(v2)
                break
        if not closed:
            if len(verts) >= len(edge_keys) + 1:
                break
        else:
            if len(verts) >= len(edge_keys):
                break

    return verts    

def vert_edge_dict(me, sel=0, key=True):
    # -1 <= sel <= 2
    if sel == -1:
        vert_edges = {v.index: [] for v in me.vertices}
    elif sel:
        vert_edges = {v.index: [] for v in me.vertices if \
                      v.select and not v.hide}
    else:
        vert_edges = {v.index: [] for v in me.vertices if not v.hide}
    if sel == -1:
        for ed in me.edges:
            edkey = ed.key
            ei = ed.index
            vert_edges[edkey[0]].append(edkey if key else ei)
            vert_edges[edkey[1]].append(edkey if key else ei)
    else:
        for ed in me.edges:
            if not ed.hide:
                ei = ed.index
                for v in ed.key:
                    if sel == 0:
                        vert_edges[v].append(ed.key if key else ei)
                    elif sel == 1:
                        if v in vert_edges:
                            vert_edges[v].append(ed.key if key else ei)
                    else:  # sel == 2
                        if ed.select:
                            vert_edges[v].append(ed.key if key else ei)
    return vert_edges

def vert_face_dict(me, sel=0):
    # -1 <= sel <= 2
    if sel == -1:
        vert_faces = {v.index: [] for v in me.vertices}
    elif sel:
        vert_faces = {v.index: [] for v in me.vertices if \
                      v.select and not v.hide}
    else:
        vert_faces = {v.index: [] for v in me.vertices if not v.hide}

    if sel == -1:
        for f in me.faces:
            for v in f.vertices:
                vert_faces[v].append(f.index)
    else:
        for f in me.faces:
            if not f.hide:
                for v in f.vertices:
                    if sel == 0:
                        vert_faces[v].append(f.index)
                    elif sel == 1:
                        if v in vert_faces:
                            vert_faces[v].append(f.index)
                    else:  # sel == 2
                        if f.select:
                            vert_faces[v].append(f.index)

    return vert_faces

def edge_face_dict(me, sel=0, key=True):
    # sel==0:all, sel==1:edge.select, sel==2:face&edge.select
    if sel == -1:
        edge_faces = {ed.key: [] for ed in me.edges}
    elif sel:
        edge_faces = {ed.key: [] for ed in me.edges if \
                        ed.select and not ed.hide}
    else:
        edge_faces = {ed.key: [] for ed in me.edges if \
                        not ed.hide}
    if sel == -1:
        for f in me.faces:
            for edkey in f.edge_keys:
                edge_faces[edkey].append(f.index)
    else:
        for f in me.faces:
            if not f.hide:
                for edkey in f.edge_keys:
                    if sel == 0:
                        edge_faces[edkey].append(f.index)
                    elif sel == 1:
                        if edkey in edge_faces:
                            edge_faces[edkey].append(f.index)
                    else:
                        if f.select:
                            edge_faces[edkey].append(f.index)
    if key:
        return edge_faces
    else:
        kedict = key_edge_dict(me, sel=-1)
        edge_faces_i = {}
        for k, i in edge_faces.items():
            edge_faces_i[kedict[k]] = i
        return edge_faces_i

def key_edge_dict(me, sel=0):
    # sel==-1:all, sel==0:notHidden, sel==1or2:edge.select
    if sel == -1:
        key_edges = {ed.key: ed.index for ed in me.edges}
    elif sel == 0:
        key_edges = {ed.key: ed.index for ed in me.edges if not ed.hide}
    elif sel:
        key_edges = {ed.key: ed.index for ed in me.edges if \
                     ed.select and not ed.hide}
    return key_edges

def vert_vert_dict(me, sel=0):
    # -1 <= sel <= 2
    if sel == -1:  # all vertices
        vert_verts = {v.index: [] for v in me.vertices}
    elif sel:
        vert_verts = {v.index: [] for v in me.vertices if \
                      v.select and not v.hide}
    else:
        vert_verts = {v.index: [] for v in me.vertices if not v.hide}
    if sel == -1:
        for ed in me.edges:
            v1 = ed.key[0]
            v2 = ed.key[1]
            vert_verts[v1].append(v2)
            vert_verts[v2].append(v1)
    else:
        for ed in me.edges:
            if not ed.hide:
                for cnt, v in enumerate(ed.key):
                    if sel == 0:
                        vert_verts[v].append(ed.key[cnt - 1])
                    elif sel == 1:
                        if v in vert_verts:
                            vert_verts[v].append(ed.key[cnt - 1])
                    else:  # sel == 2
                        if ed.select:
                            vert_verts[v].append(ed.key[cnt - 1])
    return vert_verts

def vert_edge_dict(me, sel=0, key=True):
    # -1 <= sel <= 2
    if sel == -1:
        vert_edges = {v.index: [] for v in me.vertices}
    elif sel:
        vert_edges = {v.index: [] for v in me.vertices if \
                      v.select and not v.hide}
    else:
        vert_edges = {v.index: [] for v in me.vertices if not v.hide}
    if sel == -1:
        for ed in me.edges:
            edkey = ed.key
            ei = ed.index
            vert_edges[edkey[0]].append(edkey if key else ei)
            vert_edges[edkey[1]].append(edkey if key else ei)
    else:
        for ed in me.edges:
            if not ed.hide:
                ei = ed.index
                for v in ed.key:
                    if sel == 0:
                        vert_edges[v].append(ed.key if key else ei)
                    elif sel == 1:
                        if v in vert_edges:
                            vert_edges[v].append(ed.key if key else ei)
                    else:  # sel == 2
                        if ed.select:
                            vert_edges[v].append(ed.key if key else ei)
    return vert_edges

def vert_face_dict(me, sel=0):
    # -1 <= sel <= 2
    if sel == -1:
        vert_faces = {v.index: [] for v in me.vertices}
    elif sel:
        vert_faces = {v.index: [] for v in me.vertices if \
                      v.select and not v.hide}
    else:
        vert_faces = {v.index: [] for v in me.vertices if not v.hide}

    if sel == -1:
        for f in me.faces:
            for v in f.vertices:
                vert_faces[v].append(f.index)
    else:
        for f in me.faces:
            if not f.hide:
                for v in f.vertices:
                    if sel == 0:
                        vert_faces[v].append(f.index)
                    elif sel == 1:
                        if v in vert_faces:
                            vert_faces[v].append(f.index)
                    else:  # sel == 2
                        if f.select:
                            vert_faces[v].append(f.index)

    return vert_faces

def edge_face_dict(me, sel=0, key=True):
    # sel==0:all, sel==1:edge.select, sel==2:face&edge.select
    if sel == -1:
        edge_faces = {ed.key: [] for ed in me.edges}
    elif sel:
        edge_faces = {ed.key: [] for ed in me.edges if \
                        ed.select and not ed.hide}
    else:
        edge_faces = {ed.key: [] for ed in me.edges if \
                        not ed.hide}
    if sel == -1:
        for f in me.faces:
            for edkey in f.edge_keys:
                edge_faces[edkey].append(f.index)
    else:
        for f in me.faces:
            if not f.hide:
                for edkey in f.edge_keys:
                    if sel == 0:
                        edge_faces[edkey].append(f.index)
                    elif sel == 1:
                        if edkey in edge_faces:
                            edge_faces[edkey].append(f.index)
                    else:
                        if f.select:
                            edge_faces[edkey].append(f.index)
    if key:
        return edge_faces
    else:
        kedict = key_edge_dict(me, sel=-1)
        edge_faces_i = {}
        for k, i in edge_faces.items():
            edge_faces_i[kedict[k]] = i
        return edge_faces_i

def key_edge_dict_old(me, sel=0):
    # sel==-1:all, sel==0:notHidden, sel==1or2:edge.select
    if sel == -1:
        key_edges = {ed.key: ed.index for ed in me.edges}
    elif sel == 0:
        key_edges = {ed.key: ed.index for ed in me.edges if not ed.hide}
    elif sel:
        key_edges = {ed.key: ed.index for ed in me.edges if \
                     ed.select and not ed.hide}
    return key_edges


def keypath(edge_keys):
    vkdict = {}
    tip = -1
    tip_sub = edge_keys[0][0]
    tipnum = 0
    verts = []
    closed = 1

    for k in edge_keys:
        for v in k:
            if v not in vkdict:
                vkdict[v] = [k]
            else:
                vkdict[v].append(k)

    for v, keys in vkdict.items():
        if len(keys) == 1:
            closed = 0
            tipnum += 1
            for k in keys:
                if k.index(v) == 0:
                    tip = v
                else:
                    tip_sub = v
    if tipnum >= 3:
        return []

    if tip == -1:
        tip = tip_sub

    verts.append(tip)

    while True:
        v = verts[-1]
        keys = vkdict[v]
        for k in keys:
            v2 = the_other(k, v)
            if v2 not in verts:
                verts.append(v2)
                break
        if not closed:
            if len(verts) >= len(edge_keys) + 1:
                break
        else:
            if len(verts) >= len(edge_keys):
                break

    return verts    

def vert_verts_dict(me, select=None, hide=None):
    check = lambda item: (select is None or item.select is select) and \
                         (hide is None or item.hide is hide)
    vert_verts = {v.index: [] for v in me.vertices if check(v)}
    for edge in (e for e in me.edges if check(e)):  # edgeで接続判定
        i1, i2 = edge.key
        vert_verts[i1].append(i2)
        vert_verts[i2].append(i1)
    return vert_verts

def key_edge_dict(me, select=None, hide=None):
    check = lambda item: (select is None or item.select is select) and \
                         (hide is None or item.hide is hide)
    key_edge = {e.key: e.index for e in me.edges if check(e)}
    return key_edge

def path_vertices_list(me, select=None, hide=None):
    class Path(list):
        def __init__(self, arg=[], cyclic=False):
            super(Path, self).__init__(arg)
            self.cyclic = cyclic
    vert_verts = vert_verts_dict(me, select=select, hide=hide)
    vert_end = {vi: len(vis) != 2 for vi, vis in vert_verts.items()}
    key_edge = key_edge_dict(me, select=select, hide=hide)
    key_added = {k: False for k in key_edge.keys()}
    paths = []

    # path has end points
    for vibase, vis in vert_verts.items():
        if vert_end[vibase] and len(vis) != 0:  # end point
            for vi in vis:
                if key_added[tuple(sorted((vibase, vi)))]:
                    continue
                path = Path([vibase])
                while True:
                    path.append(vi)
                    if vert_end[vi]:
                        break
                    vi = [i for i in vert_verts[vi] if i != path[-2]][0]
                for i, j in zip(path, path[1:]):
                    key = tuple(sorted((i, j)))
                    key_added[key] = True

                paths.append(path)
        elif len(vis) == 0:
            path = Path([vibase])
            paths.append(path)
    # cyclic path
    for vi in (vi for vi, end in vert_end.items() if end is True):
        del(vert_verts[vi])
    for path in paths:
        for vi in path[1:-1]:
            del(vert_verts[vi])
    while vert_verts:
        for vibase in vert_verts.keys():
            break
        path = Path([vibase], cyclic=True)
        vi = vert_verts[vibase][0]
        del(vert_verts[vibase])
        while vibase != vi:
            path.append(vi)
            vn = [i for i in vert_verts[vi] if i != path[-2]][0]
            del(vert_verts[vi])
            vi = vn
        else:
            path.append(vi)
        paths.append(path)

    return paths


class Vert():
    def __init__(self, vertex=None):
        if vertex:
            self.index = vertex.index
            self.select = vertex.select
            self.hide = vertex.hide
            self.normal = vertex.normal.copy()
            self.co = vertex.co.copy()
        else:
            self.index = 0
            self.select = False
            self.hide = False
            self.normal = Vector()
            self.co = Vector()
        self.vertices = []
        self.edges = []
        self.faces = []
        self.f1 = 0
        self.f2 = 0
        self.wldco = None  # type:Vector. self.co * ob.matrix_world
        self.winco = None  # type:Vector. convert_world_to_window()
        self.viewco = None  # type:Vector self.wldco * viewmat

    def _get_selected(self):
        return self.select and not self.hide

    def _set_selected(self, val):
        if not self.hide:
            self.select = val

    is_selected = property(_get_selected, _set_selected)

    def copy(self, set_original=False):
        vert = Vert(self)
        if set_original:
            vert.original = self
        return vert

    '''
    def get_edge(self, vert):
        key = tuple(sorted((self.index, vert.index)))
        return self.pymesh.key_edge.get(key, None)
    '''


class Edge():
    def __init__(self, edge=None, vertices=None):
        if edge:
            self.index = edge.index
            self.select = edge.select
            self.hide = edge.hide
            self.is_loose = edge.is_loose
            self.use_edge_sharp = edge.use_edge_sharp
            self.use_seam = edge.use_seam
            self.key = edge.key
            if vertices:
                #self.vertices = [vertices[i] for i in edge.vertices]
                self.vertices = [vertices[edge.vertices[0]],
                                 vertices[edge.vertices[1]]]
        else:
            self.index = 0
            self.select = False
            self.hide = False
            self.is_loose = False
            self.use_edge_sharp = False
            self.use_seam = False
            self.key = ()  # (int, int)
            self.vertices = []
        self.faces = []
        self.f1 = 0
        self.f2 = 0

    def _get_selected(self):
        return self.select and not self.hide

    def _set_selected(self, val):
        if not self.hide:
            self.select = val

    is_selected = property(_get_selected, _set_selected)

    def copy(self, set_original=False):
        edge = Edge(self)
        edge.vertices = list(self.vertices)
        if set_original:
            edge.original = self
        return edge

    def vert_another(self, v):
        if v in self.vertices:
            return self.vertices[self.vertices.index(v) - 1]
        else:
            return None


class Face():
    def __init__(self, face=None, vertices=None, key_edge=None):
        if face:
            self.index = face.index
            self.select = face.select
            self.hide = face.hide
            self.material_index = face.material_index
            self.area = face.area
            self.normal = face.normal.copy()
            self.center = face.center.copy()
            self.edge_keys = tuple(face.edge_keys)
            if vertices:
                self.vertices = [vertices[i] for i in face.vertices]
            if key_edge:
                self.edges = [key_edge[key] for key in face.edge_keys]
        else:
            self.index = 0
            self.select = False
            self.hide = False
            self.material_index = 0
            self.area = 0.0
            self.normal = Vector()
            self.center = Vector()
            self.edge_keys = []
            self.vertices = []
            self.edges = []
        self.f1 = 0
        self.f2 = 0

    def _get_selected(self):
        return self.select and not self.hide

    def _set_selected(self, val):
        if not self.hide:
            self.select = val

    is_selected = property(_get_selected, _set_selected)

    def copy(self, set_original=False):
        face = Face(self)
        face.vertices = list(self.vertices)
        face.edges = list(self.edges)
        if set_original:
            face.original = self
        return face

    '''
    def vertices_other(self, vertices, force=False):
        ret_vertices = self.vertices[:]
        if force:
            for v in vertices:
                try:
                    ret_vertices.remove(v)
                except:
                    pass
        else:
            for v in vertices:
                try:
                    ret_vertices.remove(v)
                except:
                    return None
        return ret_vertices

    def shared_edges(self, vertices=[], edges=[]):
        verts = set()
        for edge in edges:
            verts.add(edge.vertices[0])
            verts.add(edge.vertices[1])
        for vert in vertices:
            verts.add(vert)
        return (e for e in self.edges if e.vertices[0] in verts and \
                                         e.vertices[1] in verts and \
                                         e not in edges)
    '''


class PyMesh():
    def __init__(self, me, select=(None, None, None), hide=(None, None, None)):
        key_edge = key_edge_dict(me, select=None, hide=None)

        def select_hide_check(item, select, hide):
            if (select is None or item.select == select) and \
               (hide is None or item.hide == hide):
                return True
            return False
        vertices = [Vert(v) for v in me.vertices]
        #vertices = [Vert(v) for v in me.vertices if select_hide_check(v)]()
        edges = [Edge(e, vertices) for e in me.edges]
        key_edge = {k: edges[ei] for k, ei in key_edge.items()}
        faces = [Face(f, vertices, key_edge) for f in me.faces]

        for f in faces:
            for v in f.vertices:
                v.faces.append(f)
            for key in f.edge_keys:
                key_edge[key].faces.append(f)
        for e in edges:
            for v in e.vertices:
                v.edges.append(e)
        for v in vertices:
            for e in v.edges:
                v.vertices.append(e.vert_another(v))

        self.vertices = vertices
        self.edges = edges
        self.faces = faces
        self.key_edge = key_edge

    def calc_world_coordinate(self, matrix_world):
        for vert in self.vertices:
            vert.wldco = vert.co * matrix_world

    def calc_window_coordinate(self, persmat, sx, sy):
        for vert in self.vertices:
            if vert.wldco:
                vert.winco = convert_world_to_window(vert.wldco, \
                                                     persmat, sx, sy)

    def calc_view_coordinate(self, view_matrix):
        for vert in self.vertices:
            if vert.wldco:
                vert.viewco = vert.wldco * view_matrix

    def calc_same_coordinate(self):
        for vert in self.vertices:
            vert.on_vertices = [v for v in vert.vertices if v.co == vert.co]

    def removed_same_coordinate(verts):
        d = OrderedDict(zip((tuple(v.co) for v in verts), range(len(verts))))
        return [verts[i] for i in d.values()]

    def find_edge(self, v1, v2):
        return self.key_edge.get(tuple(sorted(v1.index, v2.index)), None)
