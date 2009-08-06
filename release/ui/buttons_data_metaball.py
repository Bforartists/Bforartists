import bpy

class DataButtonsPanel(bpy.types.Panel):
	__space_type__ = "BUTTONS_WINDOW"
	__region_type__ = "WINDOW"
	__context__ = "data"
	
	def poll(self, context):
		return (context.meta_ball)

class DATA_PT_context_metaball(DataButtonsPanel):
	__show_header__ = False
	
	def draw(self, context):
		layout = self.layout
		
		ob = context.object
		mball = context.meta_ball
		space = context.space_data

		split = layout.split(percentage=0.65)

		if ob:
			split.template_ID(ob, "data")
			split.itemS()
		elif mball:
			split.template_ID(space, "pin_id")
			split.itemS()

class DATA_PT_metaball(DataButtonsPanel):
	__label__ = "Metaball"

	def draw(self, context):
		layout = self.layout
		
		mball = context.meta_ball
		
		split = layout.split()
		
		col = split.column()
		col.itemL(text="Resolution:")
		sub = col.column(align=True)
		sub.itemR(mball, "wire_size", text="View")
		sub.itemR(mball, "render_size", text="Render")	
		
		col = split.column()
		col.itemL(text="Settings:")
		col.itemR(mball, "threshold", text="Threshold")

		layout.itemL(text="Update:")
		layout.itemR(mball, "flag", expand=True)

class DATA_PT_metaball_element(DataButtonsPanel):
	__label__ = "Active Element"
	
	def poll(self, context):
		return (context.meta_ball and context.meta_ball.last_selected_element)

	def draw(self, context):
		layout = self.layout
		
		metaelem = context.meta_ball.last_selected_element
		
		split = layout.split(percentage=0.3)
		split.itemL(text="Type:")	
		split.itemR(metaelem, "type", text="")
		
		split = layout.split()
			
		col = split.column()
		col.itemL(text="Settings:")
		col.itemR(metaelem, "stiffness", text="Stiffness")
		col.itemR(metaelem, "negative", text="Negative")
		col.itemR(metaelem, "hide", text="Hide")
		
		if metaelem.type == 'BALL':
		
			col = split.column(align=True)
			
		elif metaelem.type == 'CUBE':
		
			col = split.column(align=True)
			col.itemL(text="Size:")	
			col.itemR(metaelem, "sizex", text="X")
			col.itemR(metaelem, "sizey", text="Y")
			col.itemR(metaelem, "sizez", text="Z")
			
		elif metaelem.type == 'TUBE':
		
			col = split.column(align=True)
			col.itemL(text="Size:")	
			col.itemR(metaelem, "sizex", text="X")
			
		elif metaelem.type == 'PLANE':
			
			col = split.column(align=True)
			col.itemL(text="Size:")	
			col.itemR(metaelem, "sizex", text="X")
			col.itemR(metaelem, "sizey", text="Y")
			
		elif metaelem.type == 'ELLIPSOID':
			
			col = split.column(align=True)
			col.itemL(text="Size:")	
			col.itemR(metaelem, "sizex", text="X")
			col.itemR(metaelem, "sizey", text="Y")
			col.itemR(metaelem, "sizez", text="Z")
		

bpy.types.register(DATA_PT_context_metaball)
bpy.types.register(DATA_PT_metaball)
bpy.types.register(DATA_PT_metaball_element)
