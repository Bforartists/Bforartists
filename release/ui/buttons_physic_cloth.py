
import bpy

class PhysicButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "physics"

	def poll(self, context):
		return (context.object != None)
		
class PHYSICS_PT_cloth(PhysicButtonsPanel):
	__idname__ = "PHYSICS_PT_cloth"
	__label__ = "Cloth"

	def draw(self, context):
		layout = self.layout
		md = context.cloth
		ob = context.object

		split = layout.split()
		split.operator_context = "EXEC_DEFAULT"

		if md:
			# remove modifier + settings
			split.set_context_pointer("modifier", md)
			split.itemO("OBJECT_OT_modifier_remove", text="Remove")

			row = split.row(align=True)
			row.itemR(md, "render", text="")
			row.itemR(md, "realtime", text="")
		else:
			# add modifier
			split.item_enumO("OBJECT_OT_modifier_add", "type", "CLOTH", text="Add")
			split.itemL()

		if md:
			cloth = md.settings

			split = layout.split()
			
			col = split.column()
			col.itemR(cloth, "quality", slider=True)
			col.itemR(cloth, "gravity")

			subcol = col.column(align=True)
			subcol.itemR(cloth, "mass")
			subcol.item_pointerR(cloth, "mass_vertex_group", ob, "vertex_groups", text="")

			col = split.column()
			col.itemL(text="Stiffness:")
			col.itemR(cloth, "structural_stiffness", text="Structural")
			col.itemR(cloth, "bending_stiffness", text="Bending")
			col.itemL(text="Damping:")
			col.itemR(cloth, "spring_damping", text="Spring")
			col.itemR(cloth, "air_damping", text="Air")
			
			# Disabled for now
			"""
			if cloth.mass_vertex_group:
				layout.itemL(text="Goal:")
			
				col = layout.column_flow()
				col.itemR(cloth, "goal_default", text="Default")
				col.itemR(cloth, "goal_spring", text="Stiffness")
				col.itemR(cloth, "goal_friction", text="Friction")
			"""

class PHYSICS_PT_cloth_cache(PhysicButtonsPanel):
	__idname__= "PHYSICS_PT_cloth_cache"
	__label__ = "Cloth Cache"
	__default_closed__ = True

	def poll(self, context):
		return (context.cloth != None)

	def draw(self, context):
		layout = self.layout

		cache = context.cloth.point_cache
		
		row = layout.row()
		row.itemR(cache, "name")
		
		row = layout.row()
		row.itemR(cache, "start_frame")
		row.itemR(cache, "end_frame")
		
		row = layout.row()
		
		if cache.baked == True:
			row.itemO("PTCACHE_OT_free_bake_cloth", text="Free Bake")
		else:
			row.item_booleanO("PTCACHE_OT_cache_cloth", "bake", True, text="Bake")
		
		subrow = row.row()
		subrow.enabled = cache.frames_skipped or cache.outdated
		subrow.itemO("PTCACHE_OT_cache_cloth", text="Calculate to Current Frame")
			
		row = layout.row()
		#row.enabled = particle_panel_enabled(psys)
		row.itemO("PTCACHE_OT_bake_from_cloth_cache", text="Current Cache to Bake")
		row.itemR(cache, "step");
	
		row = layout.row()
		#row.enabled = particle_panel_enabled(psys)
		row.itemR(cache, "quick_cache")
		row.itemR(cache, "disk_cache")
		
		layout.itemL(text=cache.info)
		
		layout.itemS()
		
		row = layout.row()
		row.itemO("PTCACHE_OT_bake_all", "bake", True, text="Bake All Dynamics")
		row.itemO("PTCACHE_OT_free_bake_all", text="Free All Bakes")
		layout.itemO("PTCACHE_OT_bake_all", text="Update All Dynamics to current frame")
		
class PHYSICS_PT_cloth_collision(PhysicButtonsPanel):
	__idname__ = "PHYSICS_PT_clothcollision"
	__label__ = "Cloth Collision"

	def poll(self, context):
		return (context.cloth != None)
	
	def draw_header(self, context):
		layout = self.layout
		cloth = context.cloth.collision_settings
	
		layout.itemR(cloth, "enable_collision", text="")

	def draw(self, context):
		layout = self.layout
		cloth = context.cloth.collision_settings
		
		layout.active = cloth.enable_collision	
		
		col = layout.column_flow()
		col.itemR(cloth, "collision_quality", slider=True)
		col.itemR(cloth, "friction")
		col.itemR(cloth, "min_distance", text="MinDistance")
		
		
		layout.itemR(cloth, "enable_self_collision", text="Self Collision")
		
		col = layout.column_flow()
		col.active = cloth.enable_self_collision
		col.itemR(cloth, "self_collision_quality", slider=True)
		col.itemR(cloth, "self_min_distance", text="MinDistance")

class PHYSICS_PT_cloth_stiffness(PhysicButtonsPanel):
	__idname__ = "PHYSICS_PT_stiffness"
	__label__ = "Cloth Stiffness Scaling"

	def poll(self, context):
		return (context.cloth != None)
	
	def draw_header(self, context):
		layout = self.layout
		cloth = context.cloth.settings
	
		layout.itemR(cloth, "stiffness_scaling", text="")

	def draw(self, context):
		layout = self.layout
		ob = context.object
		cloth = context.cloth.settings
		
		layout.active = cloth.stiffness_scaling	
		
		split = layout.split()
		
		sub = split.column(align=True)
		sub.itemL(text="Structural Stiffness:")
		sub.item_pointerR(cloth, "structural_stiffness_vertex_group", ob, "vertex_groups", text="")
		sub.itemR(cloth, "structural_stiffness_max", text="Max")
		
		sub = split.column(align=True)
		sub.itemL(text="Bending Stiffness:")
		sub.item_pointerR(cloth, "bending_vertex_group", ob, "vertex_groups", text="")
		sub.itemR(cloth, "bending_stiffness_max", text="Max")
		
bpy.types.register(PHYSICS_PT_cloth)
bpy.types.register(PHYSICS_PT_cloth_cache)
bpy.types.register(PHYSICS_PT_cloth_collision)
bpy.types.register(PHYSICS_PT_cloth_stiffness)

