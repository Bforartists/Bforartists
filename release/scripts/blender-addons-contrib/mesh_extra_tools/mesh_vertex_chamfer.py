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

bl_info = {
    "name": "Vertex Chamfer",
    "author": "Andrew Hale (TrumanBlending)",
    "version": (0, 1),
    "blender": (2, 63, 0),
    "location": "Spacebar Menu",
    "description": "Chamfer vertex",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}


import bpy
import bmesh


class VertexChamfer(bpy.types.Operator):
    bl_idname = "mesh.vertex_chamfer"
    bl_label = "Chamfer Vertex"
    bl_description = "Tri chamfer selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    factor = bpy.props.FloatProperty(name="Factor",
                                     default=0.1,
                                     min=0.0,
                                     soft_max=1.0)
    relative = bpy.props.BoolProperty(name="Relative", default=True)
    dissolve = bpy.props.BoolProperty(name="Remove", default=True)
    displace = bpy.props.FloatProperty(name="Displace",
                                       soft_min=-5.0,
                                       soft_max=5.0)

    @classmethod
    def poll(self, context):
        return (context.active_object.type == 'MESH' and
                context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "factor", text="Fac" if self.relative else "Dist")
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
                #if val == 0.5 and e.other_vert(v).tag:
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
                bmesh.utils.face_split(l.face,
                                       l.link_loop_next.vert,
                                       l.link_loop_prev.vert)

            # Remove the vert or displace otherwise
            if dissolve:
                bmesh.utils.vert_dissolve(v)
            else:
                v.co += displace * v.normal

        me.calc_tessface()

        return {'FINISHED'}

class chamfer_help(bpy.types.Operator):
	bl_idname = 'help.vertexchamfer'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Make a selection or selection of verts ')
		layout.label('Result is triangle chamfer, works on single vert.')
		layout.label('To Help:')
		layout.label('In some cases may need to press F to fill result.')
	
	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 300)

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
