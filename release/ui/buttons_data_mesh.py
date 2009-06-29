
import bpy

class DataButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "data"
	
	def poll(self, context):
		return (context.mesh != None)

class DATA_PT_mesh(DataButtonsPanel):
	__idname__ = "DATA_PT_mesh"
	__label__ = "Mesh"
	
	def poll(self, context):
		return (context.object and context.object.type == 'MESH')

	def draw(self, context):
		layout = self.layout
		
		ob = context.object
		mesh = context.mesh
		space = context.space_data

		split = layout.split(percentage=0.65)

		if ob:
			split.template_ID(ob, "data")
			split.itemS()
		elif mesh:
			split.template_ID(space, "pin_id")
			split.itemS()

		if mesh:
			layout.itemS()

			split = layout.split()
		
			col = split.column()
			col.itemR(mesh, "autosmooth")
			colsub = col.column()
			colsub.active = mesh.autosmooth
			colsub.itemR(mesh, "autosmooth_angle", text="Angle")
			sub = split.column()
			sub.itemR(mesh, "vertex_normal_flip")
			sub.itemR(mesh, "double_sided")
			
			layout.itemR(mesh, "texco_mesh")


class DATA_PT_materials(DataButtonsPanel):
	__idname__ = "DATA_PT_materials"
	__label__ = "Materials"
	
	def poll(self, context):
		return (context.object and context.object.type in ('MESH', 'CURVE', 'FONT', 'SURFACE'))

	def draw(self, context):
		layout = self.layout
		ob = context.object

		row = layout.row()

		row.template_list(ob, "materials", "active_material_index")

		col = row.column(align=True)
		col.itemO("OBJECT_OT_material_slot_add", icon="ICON_ZOOMIN", text="")
		col.itemO("OBJECT_OT_material_slot_remove", icon="ICON_ZOOMOUT", text="")

		row = layout.row(align=True)

		row.itemO("OBJECT_OT_material_slot_assign", text="Assign");
		row.itemO("OBJECT_OT_material_slot_select", text="Select");
		row.itemO("OBJECT_OT_material_slot_deselect", text="Deselect");

		layout.itemS()

		box= layout.box()

		row = box.row()
		row.template_list(ob, "materials", "active_material_index", compact=True)

		subrow = row.row(align=True)
		subrow.itemO("OBJECT_OT_material_slot_add", icon="ICON_ZOOMIN", text="")
		subrow.itemO("OBJECT_OT_material_slot_remove", icon="ICON_ZOOMOUT", text="")


bpy.types.register(DATA_PT_mesh)
bpy.types.register(DATA_PT_materials)

