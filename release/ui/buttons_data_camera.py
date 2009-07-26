
import bpy

class DataButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "data"

	def poll(self, context):
		return (context.camera != None)
		
class DATA_PT_context_camera(DataButtonsPanel):
	__show_header__ = False
	
	def draw(self, context):
		layout = self.layout
		
		ob = context.object
		cam = context.camera
		space = context.space_data

		split = layout.split(percentage=0.65)

		if ob:
			split.template_ID(ob, "data")
			split.itemS()
		elif cam:
			split.template_ID(space, "pin_id")
			split.itemS()

class DATA_PT_camera(DataButtonsPanel):
	__label__ = "Lens"

	def draw(self, context):
		layout = self.layout
		
		cam = context.camera

		layout.itemR(cam, "type", expand=True)
			
		row = layout.row(align=True)
		if cam.type == 'PERSP':
			row.itemR(cam, "lens_unit", text="")
			if cam.lens_unit == 'MILLIMETERS':
				row.itemR(cam, "lens", text="Angle")
			elif cam.lens_unit == 'DEGREES':
				row.itemR(cam, "angle")

		elif cam.type == 'ORTHO':
			row.itemR(cam, "ortho_scale")

		split = layout.split()
		split.itemR(cam, "panorama");
		split.itemL()
				
		split = layout.split()
			
		sub = split.column(align=True)
		sub.itemL(text="Shift:")
		sub.itemR(cam, "shift_x", text="X")
		sub.itemR(cam, "shift_y", text="Y")
			
		sub = split.column(align=True)
		sub.itemL(text="Clipping:")
		sub.itemR(cam, "clip_start", text="Start")
		sub.itemR(cam, "clip_end", text="End")
			
		split = layout.split()
		col = split.column()
		col.itemL(text="Depth of Field:")
		col.itemR(cam, "dof_object", text="")
		col = split.column()
		col.itemL()
		col.itemR(cam, "dof_distance", text="Distance")
		
class DATA_PT_camera_display(DataButtonsPanel):
	__label__ = "Display"

	def draw(self, context):
		cam = context.camera
		layout = self.layout

		split = layout.split()
		
		sub = split.column()
		sub.itemR(cam, "show_limits", text="Limits")
		sub.itemR(cam, "show_mist", text="Mist")
		sub.itemR(cam, "show_title_safe", text="Title Safe")
		sub.itemR(cam, "show_name", text="Name")
			
		col = split.column()
		col.itemR(cam, "show_passepartout", text="Passepartout")
		colsub = col.column()
		colsub.active = cam.show_passepartout
		colsub.itemR(cam, "passepartout_alpha", text="Alpha", slider=True)
		col.itemR(cam, "draw_size", text="Size")
		
bpy.types.register(DATA_PT_context_camera)
bpy.types.register(DATA_PT_camera)
bpy.types.register(DATA_PT_camera_display)

