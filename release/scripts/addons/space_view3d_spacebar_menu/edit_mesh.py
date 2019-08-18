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
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


import bpy
from bpy.types import (
		Operator,
		Menu,
		)
from bpy.props import (
		BoolProperty,
		StringProperty,
		)

from .object_menus import *
from .snap_origin_cursor import *


# ********** Edit Mirror **********
class VIEW3D_MT_MirrorMenuEM(Menu):
	bl_label = "Mirror"

	def draw(self, context):
		layout = self.layout

		props = layout.operator("transform.mirror", text="X Local")
		props.constraint_axis = (True, False, False)
		props.orient_type = 'LOCAL'
		props = layout.operator("transform.mirror", text="Y Local")
		props.constraint_axis = (False, True, False)
		props.orient_type = 'LOCAL'
		props = layout.operator("transform.mirror", text="Z Local")
		props.constraint_axis = (False, False, True)
		props.orient_type = 'LOCAL'
		layout.separator()
		layout.operator("object.vertex_group_mirror")


# ********** Normals / Auto Smooth Menu **********
# Thanks to marvin.k.breuer for the Autosmooth part of the menu
class VIEW3D_MT_AutoSmooth(Menu):
	bl_label = "Normals / Auto Smooth"

	def draw(self, context):
		layout = self.layout
		obj = context.object
		obj_data = context.active_object.data

		# moved the VIEW3D_MT_edit_mesh_normals contents here under an Edit mode check
		if obj and obj.type == 'MESH' and obj.mode in {'EDIT'}:
			layout.operator("mesh.normals_make_consistent",
							text="Recalculate Outside").inside = False
			layout.operator("mesh.normals_make_consistent",
							text="Recalculate Inside").inside = True
			layout.operator("mesh.flip_normals")
			layout.separator()

		layout.separator()
		layout.prop(obj_data, "use_auto_smooth", text="Normals: Auto Smooth")

		# Auto Smooth Angle - two tab spaces to align it with the rest of the menu
		layout.prop(obj_data, "auto_smooth_angle",
					text="       Auto Smooth Angle")


# Edit Mode Menu's #

# ********** Edit Mesh **********
class VIEW3D_MT_Edit_Mesh(Menu):
	bl_label = "Mesh"

	def draw(self, context):
		layout = self.layout
		toolsettings = context.tool_settings
		view = context.space_data

		layout.menu("VIEW3D_MT_edit_mesh_vertices", icon='VERTEXSEL')
		layout.menu("VIEW3D_MT_edit_mesh_edges", icon='EDGESEL')
		layout.menu("VIEW3D_MT_edit_mesh_faces", icon='FACESEL')
		layout.separator()
		layout.operator("mesh.duplicate_move")
		layout.separator()
		layout.menu("VIEW3D_MT_edit_mesh_clean", icon='AUTO')
#        layout.prop(view, "use_occlude_geometry")
		layout.separator()
		layout.menu("VIEW3D_MT_AutoSmooth", icon='META_DATA')
		layout.operator("mesh.loopcut_slide",
						text="Loopcut", icon='UV_EDGESEL')
		layout.separator()
		layout.operator("mesh.symmetrize")
		layout.operator("mesh.symmetry_snap")
		layout.separator()
		layout.operator("mesh.bisect")
		layout.operator_menu_enum("mesh.sort_elements", "type", text="Sort Elements...")
		layout.separator()
#		layout.prop_menu_enum(toolsettings, "proportional_edit")
		layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")
		layout.separator()

		layout.prop(toolsettings, "use_mesh_automerge")
		# Double Threshold - two tab spaces to align it with the rest of the menu
		layout.prop(toolsettings, "double_threshold", text="Double Threshold")

		layout.separator()
		layout.menu("VIEW3D_MT_edit_mesh_showhide")


# ********** Edit Multiselect **********
class VIEW3D_MT_Edit_Multi(Menu):
	bl_label = "Mode Select"

	def draw(self, context):
		layout = self.layout

		layout.operator("selectedit.vertex", text="Vertex", icon='VERTEXSEL')
		layout.operator("selectedit.edge", text="Edge", icon='EDGESEL')
		layout.operator("selectedit.face", text="Face", icon='FACESEL')
		layout.operator("selectedit.vertsfaces", text="Vertex/Faces", icon='VERTEXSEL')
		layout.operator("selectedit.vertsedges", text="Vertex/Edges", icon='EDGESEL')
		layout.operator("selectedit.edgesfaces", text="Edges/Faces", icon='FACESEL')
		layout.operator("selectedit.vertsedgesfaces", text="Vertex/Edges/Faces", icon='OBJECT_DATAMODE')


# ********** Edit Mesh Edge **********
class VIEW3D_MT_EditM_Edge(Menu):
	bl_label = "Edges"

	def draw(self, context):
		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'

		layout.operator("mesh.mark_seam")
		layout.operator("mesh.mark_seam", text="Clear Seam").clear = True
		layout.separator()

		layout.operator("mesh.mark_sharp")
		layout.operator("mesh.mark_sharp", text="Clear Sharp").clear = True
		layout.operator("mesh.extrude_move_along_normals", text="Extrude")
		layout.separator()

		layout.operator("mesh.edge_rotate",
						text="Rotate Edge CW").direction = 'CW'
		layout.operator("mesh.edge_rotate",
						text="Rotate Edge CCW").direction = 'CCW'
		layout.separator()

		layout.operator("TFM_OT_edge_slide", text="Edge Slide")
		layout.operator("mesh.loop_multi_select", text="Edge Loop")
		layout.operator("mesh.loop_multi_select", text="Edge Ring").ring = True
		layout.operator("mesh.loop_to_region")
		layout.operator("mesh.region_to_loop")


# ********** Edit Mesh Cursor **********
class VIEW3D_MT_EditCursorMenu(Menu):
	bl_label = "Snap Cursor"

	def draw(self, context):
		layout = self.layout
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.operator("object.setorigintoselected",
						text="Origin to Selected V/F/E")
		layout.separator()
		layout.menu("VIEW3D_MT_Snap_Origin")
		layout.menu("VIEW3D_MT_Snap_Context")
		layout.separator()
		layout.operator("view3d.snap_cursor_to_selected",
						text="Cursor to Selected")
		layout.operator("view3d.snap_cursor_to_center",
						text="Cursor to World Origin")
		layout.operator("view3d.snap_cursor_to_grid",
						text="Cursor to Grid")
		layout.operator("view3d.snap_cursor_to_active",
						text="Cursor to Active")
		layout.operator("view3d.snap_cursor_to_edge_intersection",
						text="Cursor to Edge Intersection")
		layout.separator()
		layout.operator("view3d.snap_selected_to_cursor",
						text="Selection to Cursor").use_offset = False
		layout.operator("view3d.snap_selected_to_cursor",
						text="Selection to Cursor (Keep Offset)").use_offset = True
		layout.operator("view3d.snap_selected_to_grid",
						text="Selection to Grid")


# ********** Edit Mesh UV **********
class VIEW3D_MT_UV_Map(Menu):
	bl_label = "UV Mapping"

	def draw(self, context):
		layout = self.layout
		layout.operator("uv.unwrap")
		layout.separator()
		layout.operator_context = 'INVOKE_DEFAULT'
		layout.operator("uv.smart_project")
		layout.operator("uv.lightmap_pack")
		layout.operator("uv.follow_active_quads")
		layout.operator_context = 'EXEC_REGION_WIN'
		layout.operator("uv.cube_project")
		layout.operator("uv.cylinder_project")
		layout.operator("uv.sphere_project")
		layout.operator_context = 'INVOKE_REGION_WIN'
		layout.separator()
		layout.operator("uv.project_from_view").scale_to_bounds = False
		layout.operator("uv.project_from_view", text="Project from View (Bounds)").scale_to_bounds = True
		layout.separator()
		layout.operator("uv.reset")


# ********** Edit Mesh Transform **********
class VIEW3D_MT_TransformMenuEdit(Menu):
	bl_label = "Transform"

	def draw(self, context):
		layout = self.layout
		layout.operator("transform.translate", text="Move")
		layout.operator("transform.rotate", text="Rotate")
		layout.operator("transform.resize", text="Scale")
		layout.separator()
		layout.operator("transform.tosphere", text="To Sphere")
		layout.operator("transform.shear", text="Shear")
		layout.operator("transform.bend", text="Bend")
		layout.operator("transform.push_pull", text="Push/Pull")
		layout.operator("transform.vertex_warp", text="Warp")
		layout.operator("transform.vertex_random", text="Randomize")
		layout.separator()
		layout.operator("transform.translate", text="Move Texture Space").texture_space = True
		layout.operator("transform.resize", text="Scale Texture Space").texture_space = True
		layout.separator()
		layout.operator_context = 'EXEC_REGION_WIN'
		layout.operator("transform.transform",
						text="Align to Transform Orientation").mode = 'ALIGN'
		layout.operator_context = 'EXEC_AREA'
		layout.operator("object.origin_set",
						text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'


# Edit Select #
class VIEW3D_MT_Select_Edit_Mesh(Menu):
	bl_label = "Select"

	def draw(self, context):
		layout = self.layout
		layout.operator("view3d.select_box")
		layout.operator("view3d.select_circle")
		layout.separator()
		layout.operator("mesh.select_all").action = 'TOGGLE'
		layout.operator("mesh.select_all", text="Inverse").action = 'INVERT'
		layout.operator("mesh.select_linked", text="Linked")
		layout.operator("mesh.faces_select_linked_flat",
						text="Linked Flat Faces")
		layout.operator("mesh.select_random", text="Random")
		layout.operator("mesh.select_nth", text="Every N Number of Verts")
		layout.separator()
		layout.menu("VIEW3D_MT_Edit_Mesh_Select_Trait")
		layout.menu("VIEW3D_MT_Edit_Mesh_Select_Similar")
		layout.menu("VIEW3D_MT_Edit_Mesh_Select_More_Less")
		layout.separator()
		layout.operator("mesh.select_mirror", text="Mirror")
		layout.operator("mesh.edges_select_sharp", text="Sharp Edges")
		layout.operator("mesh.select_axis", text="Side of Active")
		layout.operator("mesh.shortest_path_select", text="Shortest Path")
		layout.separator()
		layout.operator("mesh.loop_multi_select", text="Edge Loops").ring = False
		layout.operator("mesh.loop_multi_select", text="Edge Rings").ring = True
		layout.operator("mesh.loop_to_region")
		layout.operator("mesh.region_to_loop")


class VIEW3D_MT_Edit_Mesh_Select_Similar(Menu):
	bl_label = "Select Similar"

	def draw(self, context):
		layout = self.layout
		layout.operator_enum("mesh.select_similar", "type")
		layout.operator("mesh.select_similar_region", text="Face Regions")


class VIEW3D_MT_Edit_Mesh_Select_Trait(Menu):
	bl_label = "Select All by Trait"

	def draw(self, context):
		layout = self.layout
		if context.scene.tool_settings.mesh_select_mode[2] is False:
			layout.operator("mesh.select_non_manifold", text="Non Manifold")
		layout.operator("mesh.select_loose", text="Loose Geometry")
		layout.operator("mesh.select_interior_faces", text="Interior Faces")
		layout.operator("mesh.select_face_by_sides", text="By Number of Verts")
		layout.operator("mesh.select_ungrouped", text="Ungrouped Verts")


class VIEW3D_MT_Edit_Mesh_Select_More_Less(Menu):
	bl_label = "Select More/Less"

	def draw(self, context):
		layout = self.layout
		layout.operator("mesh.select_more", text="More")
		layout.operator("mesh.select_less", text="Less")
		layout.separator()
		layout.operator("mesh.select_next_item", text="Next Active")
		layout.operator("mesh.select_prev_item", text="Previous Active")


# multiple edit select modes.
class VIEW3D_OT_selecteditVertex(Operator):
	bl_idname = "selectedit.vertex"
	bl_label = "Vertex Mode"
	bl_description = "Vert Select"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
		if bpy.ops.mesh.select_mode != "EDGE, FACE":
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
			return {'FINISHED'}


class VIEW3D_OT_selecteditEdge(Operator):
	bl_idname = "selectedit.edge"
	bl_label = "Edge Mode"
	bl_description = "Edge Select"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
		if bpy.ops.mesh.select_mode != "VERT, FACE":
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
			return {'FINISHED'}


class VIEW3D_OT_selecteditFace(Operator):
	bl_idname = "selectedit.face"
	bl_label = "Multiedit Face"
	bl_description = "Face Mode"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		if bpy.ops.mesh.select_mode != "VERT, EDGE":
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
			return {'FINISHED'}


# Components Multi Selection Mode
class VIEW3D_OT_selecteditVertsEdges(Operator):
	bl_idname = "selectedit.vertsedges"
	bl_label = "Verts Edges Mode"
	bl_description = "Vert/Edge Select"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
		if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
			bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
			return {'FINISHED'}


class VIEW3D_OT_selecteditEdgesFaces(Operator):
	bl_idname = "selectedit.edgesfaces"
	bl_label = "Edges Faces Mode"
	bl_description = "Edge/Face Select"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
		if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
			bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
			return {'FINISHED'}


class VIEW3D_OT_selecteditVertsFaces(Operator):
	bl_idname = "selectedit.vertsfaces"
	bl_label = "Verts Faces Mode"
	bl_description = "Vert/Face Select"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
		if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
			bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
			return {'FINISHED'}


class VIEW3D_OT_selecteditVertsEdgesFaces(Operator):
	bl_idname = "selectedit.vertsedgesfaces"
	bl_label = "Verts Edges Faces Mode"
	bl_description = "Vert/Edge/Face Select"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if context.object.mode != "EDIT":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
		if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
			bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
			bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
			return {'FINISHED'}


# List The Classes #

classes = (
	VIEW3D_MT_MirrorMenuEM,
	VIEW3D_MT_AutoSmooth,
	VIEW3D_MT_Edit_Mesh,
	VIEW3D_MT_Edit_Multi,
	VIEW3D_MT_EditM_Edge,
	VIEW3D_MT_EditCursorMenu,
	VIEW3D_MT_UV_Map,
	VIEW3D_MT_TransformMenuEdit,
	VIEW3D_MT_Select_Edit_Mesh,
	VIEW3D_MT_Edit_Mesh_Select_Similar,
	VIEW3D_MT_Edit_Mesh_Select_Trait,
	VIEW3D_MT_Edit_Mesh_Select_More_Less,
	VIEW3D_OT_selecteditVertex,
	VIEW3D_OT_selecteditEdge,
	VIEW3D_OT_selecteditFace,
	VIEW3D_OT_selecteditVertsEdges,
	VIEW3D_OT_selecteditEdgesFaces,
	VIEW3D_OT_selecteditVertsFaces,
	VIEW3D_OT_selecteditVertsEdgesFaces,
)


# Register Classes & Hotkeys #
def register():
	for cls in classes:
		bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)


if __name__ == "__main__":
	register()
