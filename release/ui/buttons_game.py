
import bpy
 
class PhysicsButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "physics"

	def poll(self, context):
		ob = context.active_object
		rd = context.scene.render_data
		return ob and ob.game and (rd.engine == 'BLENDER_GAME')

class PHYSICS_PT_game_physics(PhysicsButtonsPanel):
	__idname__ = "PHYSICS_PT_game_physics"
	__label__ = "Physics"

	def draw(self, context):
		layout = self.layout
		ob = context.active_object
		
		game = ob.game

		layout.itemR(game, "physics_type")
		layout.itemS()
		
		split = layout.split()
		col = split.column()
		
		col.itemR(game, "actor")
		
		col.itemR(game, "ghost")
		col.itemR(ob, "restrict_render", text="Invisible") # out of place but useful
		col = split.column()
		col.itemR(game, "do_fh", text="Use Material Physics")
		col.itemR(game, "rotation_fh", text="Rotate From Normal")
		col.itemR(game, "no_sleeping")
		
		layout.itemS()
		split = layout.split()
		col = split.column()
		col.itemL(text="Attributes:")
		colsub = col.column(align=True)
		colsub.itemR(game, "mass")
		colsub.itemR(game, "radius")
		colsub.itemR(game, "form_factor")
		col.itemS()
		col.itemL(text="Damping:")
		colsub = col.column(align=True)
		colsub.itemR(game, "damping", text="Translation", slider=True)
		colsub.itemR(game, "rotation_damping", text="Rotation", slider=True)
		
		col = split.column()
		
		col.itemL(text="Velocity:")
		colsub = col.column(align=True)
		colsub.itemR(game, "minimum_velocity", text="Minimum")
		colsub.itemR(game, "maximum_velocity", text="Maximum")
		col.itemS()
		col.itemR(game, "anisotropic_friction")
		
		colsub = col.column()
		colsub.active = game.anisotropic_friction
		colsub.itemR(game, "friction_coefficients", text="", slider=True)
		
		layout.itemS()
		split = layout.split()
		sub = split.column()
		sub.itemL(text="Lock Translation:")
		sub.itemR(game, "lock_x_axis", text="X")
		sub.itemR(game, "lock_y_axis", text="Y")
		sub.itemR(game, "lock_z_axis", text="Z")
		sub = split.column()
		sub.itemL(text="Lock Rotation:")
		sub.itemR(game, "lock_x_rot_axis", text="X")
		sub.itemR(game, "lock_y_rot_axis", text="Y")
		sub.itemR(game, "lock_z_rot_axis", text="Z")

class PHYSICS_PT_game_collision_bounds(PhysicsButtonsPanel):
	__idname__ = "PHYSICS_PT_game_collision_bounds"
	__label__ = "Collision Bounds"

	def draw_header(self, context):
		layout = self.layout
		ob = context.active_object
		game = ob.game

		layout.itemR(game, "use_collision_bounds", text="")
	
	def draw(self, context):
		layout = self.layout
		
		ob = context.scene.objects[0]
		game = ob.game
		layout.active = game.use_collision_bounds
		
		
		
		layout.itemR(game, "collision_bounds", text="Bounds")
		
		split = layout.split()
		sub = split.column()
		sub.itemR(game, "collision_compound", text="Compound")
		sub = split.column()
		sub.itemR(game, "collision_margin", text="Margin", slider=True)

bpy.types.register(PHYSICS_PT_game_physics)
bpy.types.register(PHYSICS_PT_game_collision_bounds)

class SceneButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "scene"

	def poll(self, context):
		rd = context.scene.render_data
		return (rd.engine == 'BLENDER_GAME')

class SCENE_PT_game(SceneButtonsPanel):
	__label__ = "Game"

	def draw(self, context):
		layout = self.layout
		rd = context.scene.render_data

		row = layout.row()
		row.itemO("view3d.game_start", text="Start")
		row.itemL()

class SCENE_PT_game_player(SceneButtonsPanel):
	__label__ = "Player"

	def draw(self, context):
		layout = self.layout
		gs = context.scene.game_data
		row = layout.row()
		row.itemR(gs, "fullscreen")

		split = layout.split()
		col = split.column()
		col.itemL(text="Resolution:")
		colsub = col.column(align=True)
		colsub.itemR(gs, "resolution_x", slider=False, text="X")
		colsub.itemR(gs, "resolution_y", slider=False, text="Y")

		col = split.column()
		col.itemL(text="Quality:")
		colsub = col.column(align=True)
		colsub.itemR(gs, "depth", text="Bit Depth", slider=False)
		colsub.itemR(gs, "frequency", text="FPS", slider=False)

		# framing:
		col = layout.column()
		col.itemL(text="Framing:")
		col.row().itemR(gs, "framing_type", expand=True)

		colsub = col.column()
		colsub.itemR(gs, "framing_color", text="")

class SCENE_PT_game_stereo(SceneButtonsPanel):
	__label__ = "Stereo"

	def draw(self, context):
		layout = self.layout
		gs = context.scene.game_data

		# stereo options:
		col= layout.column()
		row = col.row()
		row.itemR(gs, "stereo", expand=True)
 
		stereo_mode = gs.stereo

		# stereo:
		if stereo_mode == 'STEREO':
			row = layout.row()
			row.itemR(gs, "stereo_mode")

		# dome:
		if stereo_mode == 'DOME':
			row = layout.row()
			row.itemR(gs, "dome_mode", text="Dome Type")

			split=layout.split()
			col=split.column()
			col.itemR(gs, "dome_angle", slider=True)
			col.itemR(gs, "dome_tesselation", text="Tesselation")
			col=split.column()
			col.itemR(gs, "dome_tilt")
			col.itemR(gs, "dome_buffer_resolution", text="Resolution", slider=True)
			col=layout.column()
			col.itemR(gs, "dome_text")

bpy.types.register(SCENE_PT_game)
bpy.types.register(SCENE_PT_game_player)
bpy.types.register(SCENE_PT_game_stereo)

class WorldButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "world"

	def poll(self, context):
		rd = context.scene.render_data
		return (rd.engine == 'BLENDER_GAME')

class WORLD_PT_game_context_world(WorldButtonsPanel):
	__show_header__ = False

	def poll(self, context):
		rd = context.scene.render_data
		return (context.scene != None) and (rd.use_game_engine)

	def draw(self, context):
		layout = self.layout
		
		scene = context.scene
		world = context.world
		space = context.space_data

		split = layout.split(percentage=0.65)

		if scene:
			split.template_ID(scene, "world", new="world.new")
		elif world:
			split.template_ID(space, "pin_id")

class WORLD_PT_game_world(WorldButtonsPanel):
	__label__ = "World"

	def draw(self, context):
		layout = self.layout
		world = context.world

		row = layout.row()
		row.column().itemR(world, "horizon_color")
		row.column().itemR(world, "ambient_color")

		layout.itemR(world.mist, "enabled", text="Mist")

		row = layout.column_flow()
		row.active = world.mist.enabled
		row.itemR(world.mist, "start")
		row.itemR(world.mist, "depth")


"""
class WORLD_PT_game(WorldButtonsPanel):
	__space_type__ = "LOGIC_EDITOR"
	__region_type__ = "UI"
	__label__ = "Game Settings"

	def draw(self, context):
		layout = self.layout
		world = context.world
		
		flow = layout.column_flow()
		flow.itemR(world, "physics_engine")
		flow.itemR(world, "physics_gravity")
		
		flow.itemR(world, "game_fps")
		flow.itemR(world, "game_logic_step_max")
		flow.itemR(world, "game_physics_substep")
		flow.itemR(world, "game_physics_step_max")
		
		flow.itemR(world, "game_use_occlusion_culling", text="Enable Occlusion Culling")
		flow.itemR(world, "game_occlusion_culling_resolution")
"""

class WORLD_PT_game_physics(WorldButtonsPanel):
	__label__ = "Physics"
 
	def draw(self, context):
		layout = self.layout
		gs = context.scene.game_data
		flow = layout.column_flow()
		flow.itemR(gs, "physics_engine")
		if gs.physics_engine != "NONE":
			flow.itemR(gs, "physics_gravity", text="Gravity")
 
			split = layout.split()
			col = split.column()
			col.itemL(text="Physics Steps:")
			colsub = col.column(align=True)
			colsub.itemR(gs, "physics_step_max", text="Max")
			colsub.itemR(gs, "physics_step_sub", text="Substeps")
			col.itemR(gs, "fps", text="FPS")
			
			col = split.column()
			col.itemL(text="Logic Steps:")
			col.itemR(gs, "logic_step_max", text="Max")
			col.itemS()
			col.itemR(gs, "use_occlusion_culling", text="Occlusion Culling")
			colsub = col.column()
			colsub.active = gs.use_occlusion_culling
			colsub.itemR(gs, "occlusion_culling_resolution", text="Resolution")
			

		else:
			split = layout.split()
			col = split.column()
			col.itemL(text="Physics Steps:")
			col.itemR(gs, "fps", text="FPS")
			col = split.column()
			col.itemL(text="Logic Steps:")
			col.itemR(gs, "logic_step_max", text="Max")

bpy.types.register(WORLD_PT_game_context_world)
bpy.types.register(WORLD_PT_game_world)
bpy.types.register(WORLD_PT_game_physics)

