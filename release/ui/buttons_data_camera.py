
import bpy

class DataButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "data"

	def poll(self, context):
		ob = context.active_object
		return (ob and ob.type == 'CAMERA')
		
class DATA_PT_cameralens(DataButtonsPanel):
	__idname__ = "DATA_PT_camera"
	__label__ = "Lens"

	def draw(self, context):
		cam = context.main.cameras[0]
		layout = self.layout

		if not cam:
			return
		
		layout.itemR(cam, "type", expand=True)
		
		row = layout.row(align=True)
		if cam.type == 'PERSP':
			if cam.lens_unit == 'MILLIMETERS':
				row.itemR(cam, "lens", text="Angle")
			elif cam.lens_unit == 'DEGREES':
				row.itemR(cam, "angle")

			row.itemR(cam, "lens_unit", text="")
		elif cam.type == 'ORTHO':
			row.itemR(cam, "ortho_scale")
			
		split = layout.split()
		
		sub = split.column(align=True)
		sub.itemL(text="Shift:")
		sub.itemR(cam, "shift_x", text="X")
		sub.itemR(cam, "shift_y", text="Y")
		
		sub = split.column(align=True)
		sub.itemL(text="Clipping:")
		sub.itemR(cam, "clip_start", text="Start")
		sub.itemR(cam, "clip_end", text="End")
		
		row = layout.row()
		row.itemR(cam, "dof_object")
		row.itemR(cam, "dof_distance")
		
class DATA_PT_cameradisplay(DataButtonsPanel):
	__idname__ = "DATA_PT_cameradisplay"
	__label__ = "Display"
	
	def draw(self, context):
		cam = context.main.cameras[0]
		layout = self.layout

		if not cam:
			return
			
		split = layout.split()
		
		sub = split.column()
		sub.itemR(cam, "show_limits", text="Limits")
		sub.itemR(cam, "show_mist", text="Mist")
		sub.itemR(cam, "show_title_safe", text="Title Safe")
		sub.itemR(cam, "show_name", text="Name")
			
		sub = split.column()
		sub.itemR(cam, "show_passepartout", text="Passepartout")
		if (cam.show_passepartout):
			sub.itemR(cam, "passepartout_alpha", text="Alpha")
		sub.itemR(cam, "draw_size", text="Size")
		
bpy.types.register(DATA_PT_cameralens)
bpy.types.register(DATA_PT_cameradisplay)


