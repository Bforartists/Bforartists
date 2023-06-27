# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Vertex Chamfer",
    "author": "Andrew Hale (TrumanBlending)",
    "version": (0, 1),
    "blender": (2, 63, 0),
    "location": "Spacebar Menu",
    "description": "Chamfer vertex",
    "doc_url": "",
    "category": "Mesh",
}


import bpy
import bmesh
from bpy.types import Operator
from bpy.props import (
        BoolProperty,
        FloatProperty,
        )


class VertexChamfer(Operator):
    bl_idname = "mesh.vertex_chamfer"
    bl_label = "Chamfer Vertex"
    bl_description = "Tri chamfer selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    factor: FloatProperty(
            name="Factor",
            description="Size of the Champfer",
            default=0.1,
            min=0.0,
            soft_max=1.0
            )
    relative: BoolProperty(
            name="Relative",
            description="If Relative, Champfer size is relative to the edge length",
            default=True
            )
    dissolve: BoolProperty(
            name="Remove",
            description="Remove/keep the original selected vertices\n"
                        "Remove creates a new triangle face between the Champfer edges,\n"
                        "similar to the Dissolve Vertices operator",
            default=True
            )
    displace: FloatProperty(
            name="Displace",
            description="Active only if Remove option is disabled\n"
                        "Displaces the original selected vertices along the normals\n"
                        "defined by the Champfer edges",
            soft_min=-5.0,
            soft_max=5.0
            )

    @classmethod
    def poll(self, context):
        return (context.active_object.type == 'MESH' and
                context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "factor", text="Distance" if self.relative else "Factor")
        sub = layout.row()
        sub.prop(self, "relative")
        sub.prop(self, "dissolve")
        if not self.dissolve:
            layout.prop(self, "displace")

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        bm.select_flush(True)

        fac = self.factor
        rel = self.relative
        dissolve = self.dissolve
        displace = self.displace

        for v in bm.verts:
            v.tag = False

        # Loop over edges to find those with both verts selected
        for e in bm.edges[:]:
            e.tag = e.select
            if not e.select:
                continue
            elen = e.calc_length()
            val = fac if rel else fac / elen
            val = min(val, 0.5)
            # Loop over the verts of the edge to split
            for v in e.verts:
                # if val == 0.5 and e.other_vert(v).tag:
                #    continue
                en, vn = bmesh.utils.edge_split(e, v, val)
                en.tag = vn.tag = True
                val = 1.0 if val == 1.0 else val / (1.0 - val)

        # Get all verts which are selected but not created previously
        verts = [v for v in bm.verts if v.select and not v.tag]

        # Loop over all verts to split their linked edges
        for v in verts:
            for e in v.link_edges[:]:
                if e.tag:
                    continue
                elen = e.calc_length()
                val = fac if rel else fac / elen
                bmesh.utils.edge_split(e, v, val)

            # Loop over all the loops of the vert
            for l in v.link_loops:
                # Split the face
                bmesh.utils.face_split(
                            l.face,
                            l.link_loop_next.vert,
                            l.link_loop_prev.vert
                            )

            # Remove the vert or displace otherwise
            if dissolve:
                bmesh.utils.vert_dissolve(v)
            else:
                v.co += displace * v.normal

        me.calc_loop_triangles()

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


def register():
    bpy.utils.register_class(VertexChamfer)


def unregister():
    bpy.utils.unregister_class(VertexChamfer)


if __name__ == "__main__":
    register()
