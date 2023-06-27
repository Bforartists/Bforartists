# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name" : "Cut Faces",
    "author" : "Stanislav Blinov",
    "version" : (1, 0, 0),
    "blender" : (2, 80, 0),
    "description" : "Cut Faces and Deselect Boundary operators",
    "category" : "Mesh",
}

import bpy
import bmesh

def bmesh_from_object(object):
    mesh = object.data
    if object.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(mesh)
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)
    return bm

def bmesh_release(bm, object):
    mesh = object.data
    bm.select_flush_mode()
    if object.mode == 'EDIT':
        bmesh.update_edit_mesh(mesh, loop_triangles=True)
    else:
        bm.to_mesh(mesh)
        bm.free()

def calc_face(face, keep_caps=True):

    assert face.tag

    def radial_loops(loop):
        next = loop.link_loop_radial_next
        while next != loop:
            result, next = next, next.link_loop_radial_next
            yield result

    result = []

    face.tag = False
    selected = []
    to_select = []
    for loop in face.loops:
        self_selected = False
        # Iterate over selected adjacent faces
        for radial_loop in filter(lambda l: l.face.select, radial_loops(loop)):
            # Tag the edge if no other face done so already
            if not loop.edge.tag:
                loop.edge.tag = True
                self_selected = True

            adjacent_face = radial_loop.face
            # Only walk adjacent face if current face tagged the edge
            if adjacent_face.tag and self_selected:
                result += calc_face(adjacent_face, keep_caps)

        if loop.edge.tag:
            (selected, to_select)[self_selected].append(loop)

    for loop in to_select:
        result.append(loop.edge)
        selected.append(loop)

    # Select opposite edge in quads
    if keep_caps and len(selected) == 1 and len(face.verts) == 4:
        result.append(selected[0].link_loop_next.link_loop_next.edge)

    return result

def get_edge_rings(bm, keep_caps=True):

    def tag_face(face):
        if face.select:
            face.tag = True
            for edge in face.edges: edge.tag = False
        return face.select

    # fetch selected faces while setting up tags
    selected_faces = [ f for f in bm.faces if tag_face(f) ]

    edges = []

    try:
        # generate a list of edges to select:
        # traversing only tagged faces, since calc_face can walk and untag islands
        for face in filter(lambda f: f.tag, selected_faces): edges += calc_face(face, keep_caps)
    finally:
        # housekeeping: clear tags
        for face in selected_faces:
            face.tag = False
            for edge in face.edges: edge.tag = False

    return edges

class MESH_xOT_deselect_boundary(bpy.types.Operator):
    """Deselect boundary edges of selected faces"""
    bl_idname = "mesh.ext_deselect_boundary"
    bl_label = "Deselect Boundary"
    bl_options = {'REGISTER', 'UNDO'}

    keep_cap_edges: bpy.props.BoolProperty(
        name        = "Keep Cap Edges",
        description = "Keep quad strip cap edges selected",
        default     = False)

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object and active_object.type == 'MESH' and active_object.mode == 'EDIT'

    def execute(self, context):
        object = context.active_object
        bm = bmesh_from_object(object)

        try:
            edges = get_edge_rings(bm, keep_caps = self.keep_cap_edges)
            if not edges:
                self.report({'WARNING'}, "No suitable selection found")
                return {'CANCELLED'}

            bpy.ops.mesh.select_all(action='DESELECT')
            bm.select_mode = {'EDGE'}

            for edge in edges:
                edge.select = True
            context.tool_settings.mesh_select_mode[:] = False, True, False

        finally:
            bmesh_release(bm, object)

        return {'FINISHED'}

class MESH_xOT_cut_faces(bpy.types.Operator):
    """Cut selected faces, connecting through their adjacent edges"""
    bl_idname = "mesh.ext_cut_faces"
    bl_label = "Cut Faces"
    bl_options = {'REGISTER', 'UNDO'}

    # from bmesh_operators.h
    INNERVERT    = 0
    PATH         = 1
    FAN          = 2
    STRAIGHT_CUT = 3

    num_cuts: bpy.props.IntProperty(
        name    = "Number of Cuts",
        default = 1,
        min     = 1,
        max     = 100,
        subtype = 'UNSIGNED')

    use_single_edge: bpy.props.BoolProperty(
        name        = "Quad/Tri Mode",
        description = "Cut boundary faces",
        default     = False)

    corner_type: bpy.props.EnumProperty(
        items = [('INNER_VERT', "Inner Vert", ""),
                 ('PATH', "Path", ""),
                 ('FAN', "Fan", ""),
                 ('STRAIGHT_CUT', "Straight Cut", ""),],
        name = "Quad Corner Type",
        description = "How to subdivide quad corners",
        default = 'STRAIGHT_CUT')

    use_grid_fill: bpy.props.BoolProperty(
        name        = "Use Grid Fill",
        description = "Fill fully enclosed faces with a grid",
        default     = True)

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object and active_object.type == 'MESH' and active_object.mode == 'EDIT'

    def cut_edges(self, context):
        object = context.active_object
        bm = bmesh_from_object(object)

        try:
            edges = get_edge_rings(bm, keep_caps = True)
            if not edges:
                self.report({'WARNING'}, "No suitable selection found")
                return False

            result = bmesh.ops.subdivide_edges(
                bm,
                edges = edges,
                cuts = int(self.num_cuts),
                use_grid_fill = bool(self.use_grid_fill),
                use_single_edge = bool(self.use_single_edge),
                quad_corner_type = str(self.corner_type))

            bpy.ops.mesh.select_all(action='DESELECT')
            bm.select_mode = {'EDGE'}

            inner = result['geom_inner']
            for edge in filter(lambda e: isinstance(e, bmesh.types.BMEdge), inner):
                edge.select = True

        finally:
            bmesh_release(bm, object)

        return True

    def execute(self, context):

        if not self.cut_edges(context):
            return {'CANCELLED'}

        context.tool_settings.mesh_select_mode[:] = False, True, False
        # Try to select all possible loops
        bpy.ops.mesh.loop_multi_select(ring=False)
        return {'FINISHED'}

def menu_deselect_boundary(self, context):
    self.layout.operator(MESH_xOT_deselect_boundary.bl_idname)

def menu_cut_faces(self, context):
    self.layout.operator(MESH_xOT_cut_faces.bl_idname)

def register():
    bpy.utils.register_class(MESH_xOT_deselect_boundary)
    bpy.utils.register_class(MESH_xOT_cut_faces)

    if __name__ != "__main__":
        bpy.types.VIEW3D_MT_select_edit_mesh.append(menu_deselect_boundary)
        bpy.types.VIEW3D_MT_edit_mesh_faces.append(menu_cut_faces)

def unregister():
    bpy.utils.unregister_class(MESH_xOT_deselect_boundary)
    bpy.utils.unregister_class(MESH_xOT_cut_faces)

    if __name__ != "__main__":
        bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_deselect_boundary)
        bpy.types.VIEW3D_MT_edit_mesh_faces.remove(menu_cut_faces)

if __name__ == "__main__":
    register()
