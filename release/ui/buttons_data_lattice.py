
import bpy

class DataButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "data"
	
	def poll(self, context):
		return (context.lattice != None)
	
class DATA_PT_context(DataButtonsPanel):
	__idname__ = "DATA_PT_context"
	__label__ = " "
	
	def poll(self, context):
		return (context.object and context.object.type == 'LATTICE')

	def draw(self, context):
		layout = self.layout
		
		ob = context.object
		lat = context.lattice
		space = context.space_data

		split = layout.split(percentage=0.65)

		if ob:
			split.template_ID(ob, "data")
			split.itemS()
		elif lat:
			split.template_ID(space, "pin_id")
			split.itemS()


class DATA_PT_lattice(DataButtonsPanel):
	__idname__ = "DATA_PT_lattice"
	__label__ = "Lattice"
	
	def poll(self, context):
		return (context.object and context.object.type == 'LATTICE')

	def draw(self, context):
		layout = self.layout
		
		ob = context.object
		lat = context.lattice
		space = context.space_data

		if lat:
			row = layout.row()
			row.itemR(lat, "points_u")
			row.itemR(lat, "interpolation_type_u", expand=True)
			
			row = layout.row()
			row.itemR(lat, "points_v")
			row.itemR(lat, "interpolation_type_v", expand=True)
			
			row = layout.row()
			row.itemR(lat, "points_w")
			row.itemR(lat, "interpolation_type_w", expand=True)
			
			row = layout.row()
			row.itemO("LATTICE_OT_make_regular")
			row.itemR(lat, "outside")

bpy.types.register(DATA_PT_context)
bpy.types.register(DATA_PT_lattice)
