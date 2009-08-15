
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
	__label__ = "Physics"

	def draw(self, context):
		layout = self.layout
		
		ob = context.active_object
		game = ob.game
		soft = ob.game.soft_body

		layout.itemR(game, "physics_type")
		layout.itemS()
		
		#if game.physics_type == 'DYNAMIC':
		if game.physics_type in ('DYNAMIC', 'RIGID_BODY'):

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
			sub = col.column()
			sub.itemR(game, "mass")
			sub.itemR(game, "radius")
			sub.itemR(game, "form_factor")
			
			col.itemS()
			
			col.itemL(text="Damping:")
			sub = col.column(align=True)
			sub.itemR(game, "damping", text="Translation", slider=True)
			sub.itemR(game, "rotation_damping", text="Rotation", slider=True)
			
			col = split.column()
			col.itemL(text="Velocity:")
			sub = col.column(align=True)
			sub.itemR(game, "minimum_velocity", text="Minimum")
			sub.itemR(game, "maximum_velocity", text="Maximum")
			
			col.itemS()
			
			sub = col.column()
			sub.active = (game.physics_type == 'RIGID_BODY')
			sub.itemR(game, "anisotropic_friction")
			subsub = sub.column()
			subsub.active = game.anisotropic_friction
			subsub.itemR(game, "friction_coefficients", text="", slider=True)
			
			layout.itemS()
			
			split = layout.split()
			
			col = split.column()
			col.itemL(text="Lock Translation:")
			col.itemR(game, "lock_x_axis", text="X")
			col.itemR(game, "lock_y_axis", text="Y")
			col.itemR(game, "lock_z_axis", text="Z")
			
			col = split.column()
			col.itemL(text="Lock Rotation:")
			col.itemR(game, "lock_x_rot_axis", text="X")
			col.itemR(game, "lock_y_rot_axis", text="Y")
			col.itemR(game, "lock_z_rot_axis", text="Z")
		
		elif game.physics_type == 'SOFT_BODY':

			col = layout.column()
			col.itemR(game, "actor")
			col.itemR(game, "ghost")
			col.itemR(ob, "restrict_render", text="Invisible")
			
			layout.itemS()
			
			split = layout.split()
			
			col = split.column()
			col.itemL(text="Attributes:")
			col.itemR(game, "mass")
			col.itemR(soft, "welding")
			col.itemR(soft, "position_iterations")
			col.itemR(soft, "linstiff", slider=True)
			col.itemR(soft, "dynamic_friction", slider=True)
			col.itemR(soft, "margin", slider=True)
			col.itemR(soft, "bending_const", text="Bending Constraints")
			
			
			col = split.column()
			col.itemR(soft, "shape_match")
			sub = col.column()
			sub.active = soft.shape_match
			sub.itemR(soft, "threshold", slider=True)
			
			col.itemS()
			
			col.itemL(text="Cluster Collision:")
			col.itemR(soft, "enable_rs_collision", text="Rigid to Soft Body")
			col.itemR(soft, "enable_ss_collision", text="Soft to Soft Body")
			sub  = col.column()
			sub.active = (soft.enable_rs_collision or soft.enable_ss_collision)
			sub.itemR(soft, "cluster_iterations", text="Iterations")
		
		elif game.physics_type == 'STATIC':
			
			col = layout.column()
			col.itemR(game, "actor")
			col.itemR(game, "ghost")
			col.itemR(ob, "restrict_render", text="Invisible")
			
		elif game.physics_type in ('SENSOR', 'INVISIBLE', 'NO_COLLISION', 'OCCLUDE'):
			
			col = layout.column()
			col.itemR(ob, "restrict_render", text="Invisible")
			
class PHYSICS_PT_game_collision_bounds(PhysicsButtonsPanel):
	__label__ = "Collision Bounds"

	def poll(self, context):
		ob = context.active_object
		game = ob.game
		rd = context.scene.render_data
		return (game.physics_type in ('DYNAMIC', 'RIGID_BODY', 'SENSOR', 'SOFT_BODY', 'STATIC')) and (rd.engine == 'BLENDER_GAME')

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
		
		row = layout.row()
		row.itemR(game, "collision_compound", text="Compound")
		row.itemR(game, "collision_margin", text="Margin", slider=True)

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
		
		layout.itemR(gs, "fullscreen")

		split = layout.split()
		
		col = split.column()
		col.itemL(text="Resolution:")
		sub = col.column(align=True)
		sub.itemR(gs, "resolution_x", slider=False, text="X")
		sub.itemR(gs, "resolution_y", slider=False, text="Y")

		col = split.column()
		col.itemL(text="Quality:")
		sub = col.column(align=True)
		sub.itemR(gs, "depth", text="Bit Depth", slider=False)
		sub.itemR(gs, "frequency", text="FPS", slider=False)

		# framing:
		col = layout.column()
		col.itemL(text="Framing:")
		col.row().itemR(gs, "framing_type", expand=True)
		sub = col.column()
		sub.itemR(gs, "framing_color", text="")

class SCENE_PT_game_stereo(SceneButtonsPanel):
	__label__ = "Stereo"

	def draw(self, context):
		layout = self.layout
		
		gs = context.scene.game_data
		stereo_mode = gs.stereo

		# stereo options:
		layout.itemR(gs, "stereo", expand=True)
 
		# stereo:
		if stereo_mode == 'STEREO':
			layout.itemR(gs, "stereo_mode")
			layout.itemL(text="To do: Focal Length")
			layout.itemL(text="To do: Eye Separation")

		# dome:
		elif stereo_mode == 'DOME':
			layout.itemR(gs, "dome_mode", text="Dome Type")

			dome_type = gs.dome_mode

			split=layout.split()

			if dome_type == 'FISHEYE' or \
			   dome_type == 'TRUNCATED_REAR' or \
			   dome_type == 'TRUNCATED_FRONT':
				
				col=split.column()
				col.itemR(gs, "dome_angle", slider=True)
				col.itemR(gs, "dome_tilt")

				col=split.column()
				col.itemR(gs, "dome_tesselation", text="Tesselation")
				col.itemR(gs, "dome_buffer_resolution", text="Resolution", slider=True)

			elif dome_type == 'PANORAM_SPH':
				col=split.column()
				col.itemR(gs, "dome_tesselation", text="Tesselation")
				col.itemR(gs, "dome_buffer_resolution", text="Resolution", slider=True)

			else: # cube map
				col=split.column()
				col.itemR(gs, "dome_buffer_resolution", text="Resolution", slider=True)
		
			layout.itemR(gs, "dome_text")

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
		return (context.scene) and (rd.use_game_engine)

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

class WORLD_PT_game_physics(WorldButtonsPanel):
	__label__ = "Physics"
 
	def draw(self, context):
		layout = self.layout
		
		gs = context.scene.game_data
		
		layout.itemR(gs, "physics_engine")
		if gs.physics_engine != 'NONE':
			layout.itemR(gs, "physics_gravity", text="Gravity")
 
			split = layout.split()
			
			col = split.column()
			col.itemL(text="Physics Steps:")
			sub = col.column(align=True)
			sub.itemR(gs, "physics_step_max", text="Max")
			sub.itemR(gs, "physics_step_sub", text="Substeps")
			col.itemR(gs, "fps", text="FPS")
			
			col = split.column()
			col.itemL(text="Logic Steps:")
			col.itemR(gs, "logic_step_max", text="Max")
			
			col = layout.column()
			col.itemR(gs, "use_occlusion_culling", text="Occlusion Culling")
			sub = col.column()
			sub.active = gs.use_occlusion_culling
			sub.itemR(gs, "occlusion_culling_resolution", text="Resolution")

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
