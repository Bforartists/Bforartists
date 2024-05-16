import bpy



def draw_subpanel(layout, label, source, property):

    state = getattr(source, property)
    
    if state:
        icon = "TRIA_DOWN"    
    else:
        icon = "TRIA_RIGHT"

    row = layout.row(align=True)
    row.alignment = "LEFT"
    row.prop(source, property, text=label, icon=icon, emboss=False)

    return state 








class SIMPLETWEAK_PT_Weight_Paint_Brush_Panel(bpy.types.Panel):
    bl_label = "Weight Paint Brush Menu"
    bl_idname = "SIMPLETWEAK_PT_Weight_Paint_Brush_Menu"
    bl_options = {'HIDE_HEADER'}
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'

    def draw(self, context):

        layout = self.layout

        brush = context.tool_settings.weight_paint.brush
        simple_tweak_data = brush.SimpleTweakData


        col = layout.column()
        col.prop(simple_tweak_data, "Paint_Through", text="Paint Through", icon="XRAY")



        box = col
        

        box.label(text="Actual Property")
        box.prop(brush, "use_frontface", text="Front-Face Only")
        box.prop(brush, "use_frontface_falloff", text="Use Front-Face Falloff")
        row = box.row()
        row.prop(brush, "falloff_shape", text="Falloff Shape", expand=True, emboss=True)


        subox = box

        if draw_subpanel(subox, "Saved Off Settings", simple_tweak_data, "Show_Off_Settings"):

            subox.prop(simple_tweak_data, "off_use_frontface", text="Front-Face Only")
            row = subox.row()
            row.prop(simple_tweak_data, "off_falloff_shape", text="Falloff Shape", expand=True, emboss=True)



        if draw_subpanel(subox, "Saved On Settings", simple_tweak_data, "Show_On_Settings"):

            subox.prop(simple_tweak_data, "on_use_frontface", text="Front-Face Only")
            row = subox.row()
            row.prop(simple_tweak_data, "on_falloff_shape", text="Falloff Shape", expand=True, emboss=True)


def draw_item(self, context):

    if context.mode == "PAINT_WEIGHT":
        layout = self.layout

        try:
            brush = context.tool_settings.weight_paint.brush
            simple_tweak_data = brush.SimpleTweakData

            row = layout.row(align=True)
            row.prop(simple_tweak_data, "Paint_Through", icon="XRAY", text="")
            row.popover(SIMPLETWEAK_PT_Weight_Paint_Brush_Panel.bl_idname, text="")

        except:
            print("Brush not Found")


ENUM_Falloff_Shape = [("SPHERE","Sphere","SPHERE") , ("PROJECTED","Projected","PROJECTED")]

def update_paint_through(self, context):

    brush = self.id_data


    if self.Paint_Through:


        brush.use_frontface = self.on_use_frontface 
        brush.falloff_shape = self.on_falloff_shape 
    else:
        brush.use_frontface = self.off_use_frontface
        brush.falloff_shape = self.off_falloff_shape



class SIMPLETWEAK_Data(bpy.types.PropertyGroup):

    Paint_Through: bpy.props.BoolProperty(update=update_paint_through) 
    
    Show_Settings: bpy.props.BoolProperty()

    Show_Off_Settings: bpy.props.BoolProperty()
    off_use_frontface: bpy.props.BoolProperty(default=True)
    off_falloff_shape: bpy.props.EnumProperty(items=ENUM_Falloff_Shape, default="SPHERE")


    Show_On_Settings: bpy.props.BoolProperty()
    on_use_frontface: bpy.props.BoolProperty(default=False)
    on_falloff_shape: bpy.props.EnumProperty(items=ENUM_Falloff_Shape, default="PROJECTED")



classes = [SIMPLETWEAK_PT_Weight_Paint_Brush_Panel, SIMPLETWEAK_Data]



def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # bpy.types.VIEW3D_HT_header.append(draw_item)
    bpy.types.VIEW3D_HT_tool_header.append(draw_item)

    bpy.types.Brush.SimpleTweakData = bpy.props.PointerProperty(type=SIMPLETWEAK_Data)


def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)

    # bpy.types.VIEW3D_HT_header.remove(draw_item)
    bpy.types.VIEW3D_HT_tool_header.remove(draw_item)

    del bpy.types.Brush.SimpleTweakData

if __name__ == "__main__":
    register()

