# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# Contributed to by
# meta-androcto #

bl_info = {
	"name": "EWOCprojects tools",
	"author": "Gert De Roost - paleajed",
	"version": (1, 4, 2),
	"blender": (2, 65, 0),
	"location": "View3D > Toolbar and View3D > Specials (W-key)",
	"description": "Edit mode tools - contrib version",
	"warning": "",
	"wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
	"category": "Mesh"}


if "bpy" in locals():
	import imp
	imp.reload(mesh_edgetune)
	imp.reload(mesh_quadder)
	imp.reload(mesh_paredge)
	imp.reload(mesh_edgegrow)
	imp.reload(mesh_fanconnect)
	imp.reload(object_fastorigin)
	imp.reload(mesh_laprelax)
	imp.reload(mesh_polyredux)
	imp.reload(mesh_filletplus)
	imp.reload(mesh_innerweld)
	imp.reload(mesh_straightenplus)
	imp.reload(mesh_floodsel)
	imp.reload(mesh_deathguppie)
	imp.reload(mesh_selproject)
	imp.reload(object_creaprim)
	imp.reload(object_decouple)
	imp.reload(object_keeptrans)

else:
	from . import mesh_edgetune
	from . import mesh_quadder
	from . import mesh_paredge
	from . import mesh_edgegrow
	from . import mesh_fanconnect
	from . import object_fastorigin
	from . import mesh_laprelax
	from . import mesh_polyredux
	from . import mesh_filletplus
	from . import mesh_innerweld
	from . import mesh_straightenplus
	from . import mesh_floodsel
	from . import mesh_deathguppie
	from . import mesh_selproject
	from . import object_creaprim
	from . import object_decouple
	from . import object_keeptrans

import bpy
from bpy.app.handlers import persistent



class VIEW3D_MT_edit_mesh_paleajed(bpy.types.Menu):
	# Define the "Extras" menu
	bl_idname = "VIEW3D_MT_edit_mesh_paleajed"
	bl_label = "EWOCprojects tools"

	def draw(self, context):
		layout = self.layout
		layout.operator_context = "INVOKE_REGION_WIN"
		layout.operator("mesh.edgetune",
			text="EdgeTune")
		layout.operator("mesh.quadder",
			text="Quadder")
		layout.operator("mesh.paredge",
			text="ParEdge")
		layout.operator("mesh.edgegrow",
			text="EdgeGrow")
		layout.operator("mesh.fanconnect",
			text="FanConnect")
		layout.operator("object.fastorigin",
			text="FastOrigin")
		layout.operator("mesh.laprelax",
			text="LapRelax")
		layout.operator("mesh.polyredux",
			text="PolyRedux")
		layout.operator("mesh.filletplus",
			text="FilletPlus")
		layout.operator("mesh.innerweld",
			text="InnerWeld")
		layout.operator("mesh.straightenplus",
			text="StraightenPlus")
		layout.operator("mesh.floodsel",
			text="FloodSel")
		layout.operator("mesh.deathguppie",
			text="DeathGuppie")
		layout.operator("mesh.selproject",
			text="SelProject")


class PaleajedPanel(bpy.types.Panel):
	bl_label = "EWOCprojects tools"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_category = 'Tools'

	def draw(self, context):
		scn = bpy.context.scene
		layout = self.layout
		layout.operator("mesh.edgetune")
		layout.operator("mesh.quadder")

		layout.operator("mesh.paredge")
		if mesh_paredge.started:
			layout.prop(mesh_paredge.mainop, "Distance")
			layout.prop(mesh_paredge.mainop, "Both")
			if mesh_paredge.mainop.Both:
				layout.prop(mesh_paredge.mainop, "Cap")

		layout.operator("mesh.edgegrow")
		layout.operator("mesh.fanconnect")
		layout.operator("object.fastorigin")
		layout.operator("mesh.laprelax")
		layout.operator("mesh.polyredux")
		layout.operator("mesh.filletplus")
		layout.operator("mesh.innerweld")

		if not(mesh_straightenplus.started):
			layout.operator("mesh.straightenplus")
		else:
			layout.operator("mesh.straightenplus")
			msop = mesh_straightenplus.mainop
			layout.prop(msop, "Percentage")
			if mesh_straightenplus.started and msop.Percentage != msop.oldperc:
				msop.do_straighten()
				msop.oldperc = msop.Percentage
			layout.prop(msop, "CancelAxis")

		layout.operator("mesh.floodsel", text="Flood Sel")
		if mesh_floodsel.started:
			layout.prop(mesh_floodsel.mainop, "SelectMode")
			layout.prop(mesh_floodsel.mainop, "Multiple")
			layout.prop(mesh_floodsel.mainop, "Preselection")
			layout.prop(mesh_floodsel.mainop, "Diagonal")

		layout.operator("mesh.deathguppie")
		layout.prop(scn, "Smooth")
		layout.prop(scn, "Inner")

		if not(mesh_selproject.started):
			self.layout.operator("mesh.selproject", text="SelProject")
			if context.mode == 'EDIT_MESH':
				self.layout.prop(scn, "UseSel")
				if not(scn.UseSel):
					self.layout.prop(scn, "FromObject")
				else:
					scn.FromObject = bpy.context.active_object.name
					context.region.tag_redraw()
			else:
				self.layout.prop(scn, "FromObject")
			self.layout.prop(scn, "ToObject")
		else:
			self.layout.label(text="ENTER to confirm")

		self.layout.operator("object.creaprim")
		self.layout.prop(scn, "Name")
		self.layout.prop(scn, "Apply")
		
		if not(object_decouple.unparented):
			layout.operator("object.decouple",
				text="DeCouple")
		else:
			layout.operator("object.recouple",
				text="ReCouple")

		layout.operator("object.keeptrans")

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
	self.layout.menu("VIEW3D_MT_edit_mesh_paleajed", icon='PLUGIN')


def register():

	bpy.app.handlers.scene_update_post.append(sceneupdate_handler)

	bpy.utils.register_module(__name__)

	# Add "Extras" menu to the "Add Mesh" menu
	bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)


def unregister():
	bpy.app.handlers.scene_update_post.remove(sceneupdate_handler)

	bpy.utils.unregister_module(__name__)

	# Remove "Extras" menu from the "Add Mesh" menu.
	bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
	register()




@persistent
def sceneupdate_handler(dummy):

	scn = bpy.context.scene

	if not(list(scn.objects) == mesh_selproject.oldobjs):
		itemlist = []
		objs = list(scn.objects)
		for ob in objs:
			if ob.type == 'MESH':
				itemlist.append((ob.name, ob.name, "Set From:"))
		bpy.types.Scene.FromObject = bpy.props.EnumProperty(
				items = itemlist,
				name = "From",
				description = "Object to project")
		bpy.types.Scene.ToObject = bpy.props.EnumProperty(
				items = itemlist,
				name = "To",
				description = "Object to project onto")
		mesh_selproject.oldobjs = list(scn.objects)

