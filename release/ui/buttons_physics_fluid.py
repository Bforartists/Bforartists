
import bpy

class PhysicButtonsPanel(bpy.types.Panel):
	__space_type__ = "PROPERTIES"
	__region_type__ = "WINDOW"
	__context__ = "physics"

	def poll(self, context):
		ob = context.object
		rd = context.scene.render_data
		return (ob and ob.type == 'MESH') and (not rd.use_game_engine)
		
class PHYSICS_PT_fluid(PhysicButtonsPanel):
	__label__ = "Fluid"

	def draw(self, context):
		layout = self.layout
		
		md = context.fluid
		ob = context.object

		split = layout.split()
		split.operator_context = 'EXEC_DEFAULT'

		if md:
			# remove modifier + settings
			split.set_context_pointer("modifier", md)
			split.itemO("object.modifier_remove", text="Remove")

			row = split.row(align=True)
			row.itemR(md, "render", text="")
			row.itemR(md, "realtime", text="")
			
			fluid = md.settings
			
		else:
			# add modifier
			split.item_enumO("object.modifier_add", "type", 'FLUID_SIMULATION', text="Add")
			split.itemL()
			
			fluid = None
		
		
		if fluid:
			layout.itemR(fluid, "type")

			if fluid.type == 'DOMAIN':
				layout.itemO("fluid.bake", text="BAKE")
				split = layout.split()
				
				col = split.column()
				col.itemL(text="Resolution:")
				col.itemR(fluid, "resolution", text="Final")
				col.itemL(text="Render Display:")
				col.itemR(fluid, "render_display_mode", text="")
				col.itemL(text="Time:")
				sub = col.column(align=True)
				sub.itemR(fluid, "start_time", text="Start")
				sub.itemR(fluid, "end_time", text="End")
				
				col = split.column()
				col.itemL(text="Required Memory: " + fluid.memory_estimate)
				col.itemR(fluid, "preview_resolution", text="Preview")
				col.itemL(text="Viewport Display:")
				col.itemR(fluid, "viewport_display_mode", text="")
				col.itemL()
				col.itemR(fluid, "generate_speed_vectors")
				col.itemR(fluid, "reverse_frames")
				
				layout.itemR(fluid, "path", text="")
				
			elif fluid.type == 'FLUID':
				split = layout.split()
				
				col = split.column()
				col.itemL(text="Volume Initialization:")
				col.itemR(fluid, "volume_initialization", text="")
				col.itemR(fluid, "export_animated_mesh")
				
				col = split.column()
				col.itemL(text="Initial Velocity:")
				col.itemR(fluid, "initial_velocity", text="")
				
			elif fluid.type == 'OBSTACLE':
				split = layout.split()
				
				col = split.column()
				col.itemL(text="Volume Initialization:")
				col.itemR(fluid, "volume_initialization", text="")
				col.itemR(fluid, "export_animated_mesh")
				
				col = split.column()
				col.itemL(text="Slip Type:")
				col.itemR(fluid, "slip_type", text="")
				if fluid.slip_type == 'PARTIALSLIP':
					col.itemR(fluid, "partial_slip_amount", slider=True, text="Amount")
					
				col.itemL(text="Impact:")
				col.itemR(fluid, "impact_factor", text="Factor")
				
			elif fluid.type == 'INFLOW':
				split = layout.split()
				
				col = split.column()
				col.itemL(text="Volume Initialization:")
				col.itemR(fluid, "volume_initialization", text="")
				col.itemR(fluid, "export_animated_mesh")
				col.itemR(fluid, "local_coordinates")
				
				col = split.column()
				col.itemL(text="Inflow Velocity:")
				col.itemR(fluid, "inflow_velocity", text="")
				
			elif fluid.type == 'OUTFLOW':
				split = layout.split()
				
				col = split.column()
				col.itemL(text="Volume Initialization:")
				col.itemR(fluid, "volume_initialization", text="")
				col.itemR(fluid, "export_animated_mesh")
				
				split.column()
				
			elif fluid.type == 'PARTICLE':
				split = layout.split(percentage=0.5)
				
				col = split.column()
				col.itemL(text="Influence:")
				col.itemR(fluid, "particle_influence", text="Size")
				col.itemR(fluid, "alpha_influence", text="Alpha")
				
				col = split.column()
				col.itemL(text="Type:")
				col.itemR(fluid, "drops")
				col.itemR(fluid, "floats")
				col = split.column()
				col.itemL()
				col.itemR(fluid, "tracer")
				
				layout.itemR(fluid, "path", text="")
				
			elif fluid.type == 'CONTROL':
				split = layout.split()
				
				col = split.column()
				col.itemL(text="")
				col.itemR(fluid, "quality", slider=True)
				col.itemR(fluid, "reverse_frames")
				
				col = split.column()
				col.itemL(text="Time:")
				sub = col.column(align=True)
				sub.itemR(fluid, "start_time", text="Start")
				sub.itemR(fluid, "end_time", text="End")
				
				split = layout.split()
				
				col = split.column()
				col.itemL(text="Attraction Force:")
				sub = col.column(align=True)
				sub.itemR(fluid, "attraction_strength", text="Strength")
				sub.itemR(fluid, "attraction_radius", text="Radius")
				
				col = split.column()
				col.itemL(text="Velocity Force:")
				sub = col.column(align=True)
				sub.itemR(fluid, "velocity_strength", text="Strength")
				sub.itemR(fluid, "velocity_radius", text="Radius")

class PHYSICS_PT_domain_gravity(PhysicButtonsPanel):
	__label__ = "Domain World"
	__default_closed__ = True
	
	def poll(self, context):
		md = context.fluid
		if md:
			settings = md.settings
			if settings:
				return (settings.type == 'DOMAIN')
		
		return False

	def draw(self, context):
		layout = self.layout
		
		fluid = context.fluid.settings
		
		split = layout.split()
		
		col = split.column()
		col.itemL(text="Gravity:")
		col.itemR(fluid, "gravity", text="")
		col.itemL(text="Real World Size:")
		col.itemR(fluid, "real_world_size", text="Metres")
		
		col = split.column()
		col.itemL(text="Viscosity Presets:")
		sub = col.column(align=True)
		sub.itemR(fluid, "viscosity_preset", text="")
		
		if fluid.viscosity_preset == 'MANUAL':
			sub.itemR(fluid, "viscosity_base", text="Base")
			sub.itemR(fluid, "viscosity_exponent", text="Exponent", slider=True)
		else:
			sub.itemL()
			sub.itemL()
			
		col.itemL(text="Optimization:")
		sub = col.column(align=True)
		sub.itemR(fluid, "grid_levels", slider=True)
		sub.itemR(fluid, "compressibility", slider=True)
	
class PHYSICS_PT_domain_boundary(PhysicButtonsPanel):
	__label__ = "Domain Boundary"
	__default_closed__ = True
	
	def poll(self, context):
		md = context.fluid
		if md:
			settings = md.settings
			if settings:
				return (settings.type == 'DOMAIN')
		
		return False

	def draw(self, context):
		layout = self.layout
		
		fluid = context.fluid.settings
		
		split = layout.split()
		
		col = split.column()
		col.itemL(text="Slip Type:")
		sub = col.column(align=True)
		sub.itemR(fluid, "slip_type", text="")
		if fluid.slip_type == 'PARTIALSLIP':
			sub.itemR(fluid, "partial_slip_amount", slider=True, text="Amount")

		col = split.column()
		col.itemL(text="Surface:")
		sub = col.column(align=True)
		sub.itemR(fluid, "surface_smoothing", text="Smoothing")
		sub.itemR(fluid, "surface_subdivisions", text="Subdivisions")	
		
class PHYSICS_PT_domain_particles(PhysicButtonsPanel):
	__label__ = "Domain Particles"
	__default_closed__ = True
	
	def poll(self, context):
		md = context.fluid
		if md:
			settings = md.settings
			if settings:
				return (settings.type == 'DOMAIN')
		
		return False

	def draw(self, context):
		layout = self.layout
		
		fluid = context.fluid.settings
		
		col = layout.column(align=True)
		col.itemR(fluid, "tracer_particles")
		col.itemR(fluid, "generate_particles")

bpy.types.register(PHYSICS_PT_fluid)
bpy.types.register(PHYSICS_PT_domain_gravity)
bpy.types.register(PHYSICS_PT_domain_boundary)
bpy.types.register(PHYSICS_PT_domain_particles)
