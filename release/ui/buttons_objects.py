
import bpy

class ObjectButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "object"

	def poll(self, context):
		return (context.active_object != None)

class OBJECT_PT_transform(ObjectButtonsPanel):
	__idname__ = "OBJECT_PT_transform"
	__label__ = "Transform"

	def draw(self, context):
		ob = context.active_object
		layout = self.layout

		row = layout.row()
		row.column().itemR(ob, "location")
		row.column().itemR(ob, "rotation")
		row.column().itemR(ob, "scale")

class OBJECT_PT_groups(ObjectButtonsPanel):
	__idname__ = "OBJECT_PT_groups"
	__label__ = "Groups"

	def draw(self, context):
		ob = context.active_object
		layout = self.layout

		row = layout.row()
		row.itemR(ob, "pass_index")
		row.itemR(ob, "parent")

		# layout.left_right()
		# layout.itemO("OBJECT_OT_add_group");

		for group in bpy.data.groups:
			if ob in group.objects:
				box = layout.box()

				row = box.row()
				row.itemR(group, "name")
				#row.itemO("OBJECT_OT_remove_group")

				row = box.row()
				row.column().itemR(group, "layer")
				row.column().itemR(group, "dupli_offset")

class OBJECT_PT_display(ObjectButtonsPanel):
	__idname__ = "OBJECT_PT_display"
	__label__ = "Display"

	def draw(self, context):
		ob = context.active_object
		layout = self.layout
			
		row = layout.row()
		row.itemR(ob, "max_draw_type", text="Type")
		row.itemR(ob, "draw_bounds_type", text="Bounds")

		flow = layout.column_flow()
		flow.itemR(ob, "draw_name", text="Name")
		flow.itemR(ob, "draw_axis", text="Axis")
		flow.itemR(ob, "draw_wire", text="Wire")
		flow.itemR(ob, "draw_texture_space", text="Texture Space")
		flow.itemR(ob, "x_ray", text="X-Ray")
		flow.itemR(ob, "draw_transparent", text="Transparency")

class OBJECT_PT_duplication(ObjectButtonsPanel):
	__idname__ = "OBJECT_PT_duplication"
	__label__ = "Duplication"

	def draw(self, context):
		ob = context.active_object
		layout = self.layout

		row = layout.row()
		row.itemR(ob, "dupli_type", text="", expand=True)

		if ob.dupli_type == "FRAMES":
			split = layout.split()
			
			sub = split.column(align=True)
			sub.itemR(ob, "dupli_frames_start", text="Start")
			sub.itemR(ob, "dupli_frames_end", text="End")
			
			sub = split.column(align=True)
			sub.itemR(ob, "dupli_frames_on", text="On")
			sub.itemR(ob, "dupli_frames_off", text="Off")

class OBJECT_PT_animation(ObjectButtonsPanel):
	__idname__ = "OBJECT_PT_animation"
	__label__ = "Animation"

	def draw(self, context):
		ob = context.active_object
		layout = self.layout

		row = layout.row()
		
		sub = row.column()
		sub.itemL(text="Time Offset:")
		sub.itemR(ob, "time_offset_edit", text="Edit")
		sub.itemR(ob, "time_offset_particle", text="Particle")
		sub.itemR(ob, "time_offset_parent", text="Parent")
		sub.itemR(ob, "slow_parent")
		sub.itemR(ob, "time_offset", text="Offset")
		
		sub = row.column()
		sub.itemL(text="Tracking:")
		sub.itemR(ob, "track_axis", text="Axis")
		sub.itemR(ob, "up_axis", text="Up Axis")
		sub.itemR(ob, "track_rotation", text="Rotation")

bpy.types.register(OBJECT_PT_transform)
bpy.types.register(OBJECT_PT_groups)
bpy.types.register(OBJECT_PT_display)
bpy.types.register(OBJECT_PT_duplication)
bpy.types.register(OBJECT_PT_animation)

