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

from _bpy import types as bpy_types
import _bpy
from mathutils import Vector

StructRNA = bpy_types.Struct.__bases__[0]
StructMetaIDProp = _bpy.StructMetaIDProp
# StructRNA = bpy_types.Struct


class Context(StructRNA):
    __slots__ = ()

    def copy(self):
        from types import BuiltinMethodType
        new_context = {}
        generic_attrs = list(StructRNA.__dict__.keys()) + ["bl_rna", "rna_type", "copy"]
        for attr in dir(self):
            if not (attr.startswith("_") or attr in generic_attrs):
                value = getattr(self, attr)
                if type(value) != BuiltinMethodType:
                    new_context[attr] = value

        return new_context


class Library(bpy_types.ID):
    __slots__ = ()

    @property
    def users_id(self):
        """ID datablocks which use this library"""
        import bpy

        # See: readblenentry.c, IDTYPE_FLAGS_ISLINKABLE, we could make this an attribute in rna.
        attr_links = "actions", "armatures", "brushes", "cameras", \
                "curves", "grease_pencil", "groups", "images", \
                "lamps", "lattices", "materials", "metaballs", \
                "meshes", "node_groups", "objects", "scenes", \
                "sounds", "textures", "texts", "fonts", "worlds"

        return tuple(id_block for attr in attr_links for id_block in getattr(bpy.data, attr) if id_block.library == self)


class Texture(bpy_types.ID):
    __slots__ = ()

    @property
    def users_material(self):
        """Materials that use this texture"""
        import bpy
        return tuple(mat for mat in bpy.data.materials if self in [slot.texture for slot in mat.texture_slots if slot])

    @property
    def users_object_modifier(self):
        """Object modifiers that use this texture"""
        import bpy
        return tuple(obj for obj in bpy.data.objects if self in [mod.texture for mod in obj.modifiers if mod.type == 'DISPLACE'])


class Group(bpy_types.ID):
    __slots__ = ()

    @property
    def users_dupli_group(self):
        """The dupli group this group is used in"""
        import bpy
        return tuple(obj for obj in bpy.data.objects if self == obj.dupli_group)


class Object(bpy_types.ID):
    __slots__ = ()

    @property
    def children(self):
        """All the children of this object"""
        import bpy
        return tuple(child for child in bpy.data.objects if child.parent == self)

    @property
    def users_group(self):
        """The groups this object is in"""
        import bpy
        return tuple(group for group in bpy.data.groups if self in group.objects[:])

    @property
    def users_scene(self):
        """The scenes this object is in"""
        import bpy
        return tuple(scene for scene in bpy.data.scenes if self in scene.objects[:])


class _GenericBone:
    """
    functions for bones, common between Armature/Pose/Edit bones.
    internal subclassing use only.
    """
    __slots__ = ()

    def translate(self, vec):
        """Utility function to add *vec* to the head and tail of this bone."""
        self.head += vec
        self.tail += vec

    def parent_index(self, parent_test):
        """
        The same as 'bone in other_bone.parent_recursive' but saved generating a list.
        """
        # use the name so different types can be tested.
        name = parent_test.name

        parent = self.parent
        i = 1
        while parent:
            if parent.name == name:
                return i
            parent = parent.parent
            i += 1

        return 0

    @property
    def x_axis(self):
        """ Vector pointing down the x-axis of the bone.
        """
        return Vector((1.0, 0.0, 0.0)) * self.matrix.to_3x3()

    @property
    def y_axis(self):
        """ Vector pointing down the x-axis of the bone.
        """
        return Vector((0.0, 1.0, 0.0)) * self.matrix.to_3x3()

    @property
    def z_axis(self):
        """ Vector pointing down the x-axis of the bone.
        """
        return Vector((0.0, 0.0, 1.0)) * self.matrix.to_3x3()

    @property
    def basename(self):
        """The name of this bone before any '.' character"""
        #return self.name.rsplit(".", 1)[0]
        return self.name.split(".")[0]

    @property
    def parent_recursive(self):
        """A list of parents, starting with the immediate parent"""
        parent_list = []
        parent = self.parent

        while parent:
            if parent:
                parent_list.append(parent)

            parent = parent.parent

        return parent_list

    @property
    def center(self):
        """The midpoint between the head and the tail."""
        return (self.head + self.tail) * 0.5

    @property
    def length(self):
        """The distance from head to tail, when set the head is moved to fit the length."""
        return self.vector.length

    @length.setter
    def length(self, value):
        self.tail = self.head + ((self.tail - self.head).normalize() * value)

    @property
    def vector(self):
        """The direction this bone is pointing. Utility function for (tail - head)"""
        return (self.tail - self.head)

    @property
    def children(self):
        """A list of all the bones children."""
        return [child for child in self._other_bones if child.parent == self]

    @property
    def children_recursive(self):
        """a list of all children from this bone."""
        bones_children = []
        for bone in self._other_bones:
            index = bone.parent_index(self)
            if index:
                bones_children.append((index, bone))

        # sort by distance to parent
        bones_children.sort(key=lambda bone_pair: bone_pair[0])
        return [bone for index, bone in bones_children]

    @property
    def children_recursive_basename(self):
        """
        Returns a chain of children with the same base name as this bone
        Only direct chains are supported, forks caused by multiple children with matching basenames will
        terminate the function and not be returned.
        """
        basename = self.basename
        chain = []

        child = self
        while True:
            children = child.children
            children_basename = []

            for child in children:
                if basename == child.basename:
                    children_basename.append(child)

            if len(children_basename) == 1:
                child = children_basename[0]
                chain.append(child)
            else:
                if len(children_basename):
                    print("multiple basenames found, this is probably not what you want!", bone.name, children_basename)

                break

        return chain

    @property
    def _other_bones(self):
        id_data = self.id_data
        id_data_type = type(id_data)

        if id_data_type == bpy_types.Object:
            bones = id_data.pose.bones
        elif id_data_type == bpy_types.Armature:
            bones = id_data.edit_bones
            if not bones:  # not in editmode
                bones = id_data.bones

        return bones


class PoseBone(StructRNA, _GenericBone, metaclass=StructMetaIDProp):
    __slots__ = ()


class Bone(StructRNA, _GenericBone, metaclass=StructMetaIDProp):
    __slots__ = ()


class EditBone(StructRNA, _GenericBone, metaclass=StructMetaIDProp):
    __slots__ = ()

    def align_orientation(self, other):
        """
        Align this bone to another by moving its tail and settings its roll
        the length of the other bone is not used.
        """
        vec = other.vector.normalize() * self.length
        self.tail = self.head + vec
        self.roll = other.roll

    def transform(self, matrix):
        """
        Transform the the bones head, tail, roll and envalope (when the matrix has a scale component).
        Expects a 4x4 or 3x3 matrix.
        """
        from mathutils import Vector
        z_vec = Vector((0.0, 0.0, 1.0)) * self.matrix.to_3x3()
        self.tail = self.tail * matrix
        self.head = self.head * matrix
        scalar = matrix.median_scale
        self.head_radius *= scalar
        self.tail_radius *= scalar
        self.align_roll(z_vec * matrix)


def ord_ind(i1, i2):
    if i1 < i2:
        return i1, i2
    return i2, i1


class Mesh(bpy_types.ID):
    __slots__ = ()

    def from_pydata(self, vertices, edges, faces):
        """
        Make a mesh from a list of verts/edges/faces
        Until we have a nicer way to make geometry, use this.

        :arg vertices: float triplets each representing (X, Y, Z) eg: [(0.0, 1.0, 0.5), ...].
        :type vertices: iterable object
        :arg edges: int pairs, each pair contains two indices to the *vertices* argument. eg: [(1, 2), ...]
        :type edges: iterable object
        :arg faces: iterator of faces, each faces contains three or four indices to the *vertices* argument. eg: [(5, 6, 8, 9), (1, 2, 3), ...]
        :type faces: iterable object
        """
        self.vertices.add(len(vertices))
        self.edges.add(len(edges))
        self.faces.add(len(faces))

        vertices_flat = [f for v in vertices for f in v]
        self.vertices.foreach_set("co", vertices_flat)
        del vertices_flat

        edges_flat = [i for e in edges for i in e]
        self.edges.foreach_set("vertices", edges_flat)
        del edges_flat

        def treat_face(f):
            if len(f) == 3:
                if f[2] == 0:
                    return f[2], f[0], f[1], 0
                else:
                    return f[0], f[1], f[2], 0
            elif f[2] == 0 or f[3] == 0:
                return f[2], f[3], f[0], f[1]
            return f

        faces_flat = [v for f in faces for v in treat_face(f)]
        self.faces.foreach_set("vertices_raw", faces_flat)
        del faces_flat

    @property
    def edge_keys(self):
        return [edge_key for face in self.faces for edge_key in face.edge_keys]

    @property
    def edge_face_count_dict(self):
        face_edge_keys = [face.edge_keys for face in self.faces]
        face_edge_count = {}
        for face_keys in face_edge_keys:
            for key in face_keys:
                try:
                    face_edge_count[key] += 1
                except:
                    face_edge_count[key] = 1

        return face_edge_count

    @property
    def edge_face_count(self):
        edge_face_count_dict = self.edge_face_count_dict
        return [edge_face_count_dict.get(ed.key, 0) for ed in self.edges]

    def edge_loops_from_faces(self, faces=None, seams=()):
        """
        Edge loops defined by faces

        Takes me.faces or a list of faces and returns the edge loops
        These edge loops are the edges that sit between quads, so they dont touch
        1 quad, note: not connected will make 2 edge loops, both only containing 2 edges.

        return a list of edge key lists
        [ [(0,1), (4, 8), (3,8)], ...]

        return a list of edge vertex index lists
        """

        OTHER_INDEX = 2, 3, 0, 1  # opposite face index

        if faces is None:
            faces = self.faces

        edges = {}

        for f in faces:
#            if len(f) == 4:
            if f.vertices_raw[3] != 0:
                edge_keys = f.edge_keys
                for i, edkey in enumerate(f.edge_keys):
                    edges.setdefault(edkey, []).append(edge_keys[OTHER_INDEX[i]])

        for edkey in seams:
            edges[edkey] = []

        # Collect edge loops here
        edge_loops = []

        for edkey, ed_adj in edges.items():
            if 0 < len(ed_adj) < 3:  # 1 or 2
                # Seek the first edge
                context_loop = [edkey, ed_adj[0]]
                edge_loops.append(context_loop)
                if len(ed_adj) == 2:
                    other_dir = ed_adj[1]
                else:
                    other_dir = None

                ed_adj[:] = []

                flipped = False

                while 1:
                    # from knowing the last 2, look for th next.
                    ed_adj = edges[context_loop[-1]]
                    if len(ed_adj) != 2:

                        if other_dir and flipped == False:  # the original edge had 2 other edges
                            flipped = True  # only flip the list once
                            context_loop.reverse()
                            ed_adj[:] = []
                            context_loop.append(other_dir)  # save 1 lookiup

                            ed_adj = edges[context_loop[-1]]
                            if len(ed_adj) != 2:
                                ed_adj[:] = []
                                break
                        else:
                            ed_adj[:] = []
                            break

                    i = ed_adj.index(context_loop[-2])
                    context_loop.append(ed_adj[not  i])

                    # Dont look at this again
                    ed_adj[:] = []

        return edge_loops

    def edge_loops_from_edges(self, edges=None):
        """
        Edge loops defined by edges

        Takes me.edges or a list of edges and returns the edge loops

        return a list of vertex indices.
        [ [1, 6, 7, 2], ...]

        closed loops have matching start and end values.
        """
        line_polys = []

        # Get edges not used by a face
        if edges is None:
            edges = self.edges

        if not hasattr(edges, "pop"):
            edges = edges[:]

        edge_dict = {ed.key: ed for ed in self.edges if ed.select}

        while edges:
            current_edge = edges.pop()
            vert_end, vert_start = current_edge.vertices[:]
            line_poly = [vert_start, vert_end]

            ok = True
            while ok:
                ok = False
                #for i, ed in enumerate(edges):
                i = len(edges)
                while i:
                    i -= 1
                    ed = edges[i]
                    v1, v2 = ed.vertices
                    if v1 == vert_end:
                        line_poly.append(v2)
                        vert_end = line_poly[-1]
                        ok = 1
                        del edges[i]
                        # break
                    elif v2 == vert_end:
                        line_poly.append(v1)
                        vert_end = line_poly[-1]
                        ok = 1
                        del edges[i]
                        #break
                    elif v1 == vert_start:
                        line_poly.insert(0, v2)
                        vert_start = line_poly[0]
                        ok = 1
                        del edges[i]
                        # break
                    elif v2 == vert_start:
                        line_poly.insert(0, v1)
                        vert_start = line_poly[0]
                        ok = 1
                        del edges[i]
                        #break
            line_polys.append(line_poly)

        return line_polys


class MeshEdge(StructRNA):
    __slots__ = ()

    @property
    def key(self):
        return ord_ind(*tuple(self.vertices))


class MeshFace(StructRNA):
    __slots__ = ()

    @property
    def center(self):
        """The midpoint of the face."""
        face_verts = self.vertices[:]
        mesh_verts = self.id_data.vertices
        if len(face_verts) == 3:
            return (mesh_verts[face_verts[0]].co + mesh_verts[face_verts[1]].co + mesh_verts[face_verts[2]].co) / 3.0
        else:
            return (mesh_verts[face_verts[0]].co + mesh_verts[face_verts[1]].co + mesh_verts[face_verts[2]].co + mesh_verts[face_verts[3]].co) / 4.0

    @property
    def edge_keys(self):
        verts = self.vertices[:]
        if len(verts) == 3:
            return ord_ind(verts[0], verts[1]), ord_ind(verts[1], verts[2]), ord_ind(verts[2], verts[0])

        return ord_ind(verts[0], verts[1]), ord_ind(verts[1], verts[2]), ord_ind(verts[2], verts[3]), ord_ind(verts[3], verts[0])


class Text(bpy_types.ID):
    __slots__ = ()

    def as_string(self):
        """Return the text as a string."""
        return "\n".join(line.body for line in self.lines)

    def from_string(self, string):
        """Replace text with this string."""
        self.clear()
        self.write(string)

    @property
    def users_logic(self):
        """Logic bricks that use this text"""
        import bpy
        return tuple(obj for obj in bpy.data.objects if self in [cont.text for cont in obj.game.controllers if cont.type == 'PYTHON'])

# values are module: [(cls, path, line), ...]
TypeMap = {}


class RNAMeta(type):
    def __new__(cls, name, bases, classdict, **args):
        result = type.__new__(cls, name, bases, classdict)
        if bases and bases[0] != StructRNA:
            import traceback
            import weakref
            module = result.__module__

            # first part of packages only
            if "." in module:
                module = module[:module.index(".")]

            sf = traceback.extract_stack(limit=2)[0]

            TypeMap.setdefault(module, []).append((weakref.ref(result), sf[0], sf[1]))

        return result


import collections


class RNAMetaIDProp(RNAMeta, StructMetaIDProp):
    pass


class OrderedMeta(RNAMeta):

    def __init__(cls, name, bases, attributes):
        super(OrderedMeta, cls).__init__(name, bases, attributes)
        cls.order = list(attributes.keys())

    def __prepare__(name, bases, **kwargs):
        return collections.OrderedDict()


# Only defined so operators members can be used by accessing self.order
# with doc generation 'self.properties.bl_rna.properties' can fail
class Operator(StructRNA, metaclass=OrderedMeta):
    __slots__ = ()

    def __getattribute__(self, attr):
        properties = StructRNA.path_resolve(self, "properties")
        bl_rna = getattr(properties, "bl_rna", None)
        if bl_rna and attr in bl_rna.properties:
            return getattr(properties, attr)
        return super().__getattribute__(attr)

    def __setattr__(self, attr, value):
        properties = StructRNA.path_resolve(self, "properties")
        bl_rna = getattr(properties, "bl_rna", None)
        if bl_rna and attr in bl_rna.properties:
            return setattr(properties, attr, value)
        return super().__setattr__(attr, value)

    def __delattr__(self, attr):
        properties = StructRNA.path_resolve(self, "properties")
        bl_rna = getattr(properties, "bl_rna", None)
        if bl_rna and attr in bl_rna.properties:
            return delattr(properties, attr)
        return super().__delattr__(attr)

    def as_keywords(self, ignore=()):
        """ Return a copy of the properties as a dictionary.
        """
        ignore = ignore + ("rna_type",)
        return {attr: getattr(self, attr) for attr in self.properties.rna_type.properties.keys() if attr not in ignore}


class Macro(StructRNA, metaclass=OrderedMeta):
    # bpy_types is imported before ops is defined
    # so we have to do a local import on each run
    __slots__ = ()

    @classmethod
    def define(self, opname):
        from _bpy import ops
        return ops.macro_define(self, opname)


class IDPropertyGroup(StructRNA, metaclass=RNAMetaIDProp):
        __slots__ = ()


class RenderEngine(StructRNA, metaclass=RNAMeta):
    __slots__ = ()


class KeyingSetInfo(StructRNA, metaclass=RNAMeta):
    __slots__ = ()


class _GenericUI:
    __slots__ = ()

    @classmethod
    def _dyn_ui_initialize(cls):
        draw_funcs = getattr(cls.draw, "_draw_funcs", None)

        if draw_funcs is None:

            def draw_ls(self, context):
                for func in draw_ls._draw_funcs:
                    func(self, context)

            draw_funcs = draw_ls._draw_funcs = [cls.draw]
            cls.draw = draw_ls

        return draw_funcs

    @classmethod
    def append(cls, draw_func):
        """Prepend an draw function to this menu, takes the same arguments as the menus draw function."""
        draw_funcs = cls._dyn_ui_initialize()
        draw_funcs.append(draw_func)

    @classmethod
    def prepend(cls, draw_func):
        """Prepend a draw function to this menu, takes the same arguments as the menus draw function."""
        draw_funcs = cls._dyn_ui_initialize()
        draw_funcs.insert(0, draw_func)

    @classmethod
    def remove(cls, draw_func):
        """Remove a draw function that has been added to this menu"""
        draw_funcs = cls._dyn_ui_initialize()
        try:
            draw_funcs.remove(draw_func)
        except:
            pass


class Panel(StructRNA, _GenericUI, metaclass=RNAMeta):
    __slots__ = ()


class Header(StructRNA, _GenericUI, metaclass=RNAMeta):
    __slots__ = ()


class Menu(StructRNA, _GenericUI, metaclass=RNAMeta):
    __slots__ = ()

    def path_menu(self, searchpaths, operator, props_default={}):
        layout = self.layout
        # hard coded to set the operators 'filepath' to the filename.

        import os
        import bpy.utils

        layout = self.layout

        if not searchpaths:
            layout.label("* Missing Paths *")

        # collect paths
        files = []
        for directory in searchpaths:
            files.extend([(f, os.path.join(directory, f)) for f in os.listdir(directory)])

        files.sort()

        for f, filepath in files:

            if f.startswith("."):
                continue

            preset_name = bpy.path.display_name(f)
            props = layout.operator(operator, text=preset_name)

            for attr, value in props_default.items():
                setattr(props, attr, value)

            props.filepath = filepath
            if operator == "script.execute_preset":
                props.menu_idname = self.bl_idname

    def draw_preset(self, context):
        """Define these on the subclass
         - preset_operator
         - preset_subdir
        """
        import bpy
        self.path_menu(bpy.utils.preset_paths(self.preset_subdir), self.preset_operator)
