import bpy


#### ------------------------------ /toolbar/ ------------------------------ ####

def carver_ui_common(context, layout, props):
    """Common tool properties for all Carver tools"""

    if context.region.type == 'TOOL_HEADER':
        layout.prop(props, "mode", text="")
        layout.prop(props, "alignment", text="")
        layout.prop(props, "depth", text="")
        layout.prop(props, "solver", expand=True)

    else:
        # NOTE: Use labels for Properties editor/sidebar.
        layout.prop(props, "mode", text="Mode")
        layout.prop(props, "alignment", text="Alignment")
        layout.prop(props, "depth", text="Depth")
        row = layout.row()
        row.prop(props, "solver", expand=True)
        layout.separator()

    # Popovers
    layout.popover("TOPBAR_PT_carver_shape", text="Shape")
    layout.popover("TOPBAR_PT_carver_effects", text="Effects")
    layout.popover("TOPBAR_PT_carver_cutter", text="Cutter")



#### ------------------------------ /popovers/ ------------------------------ ####

class TOPBAR_PT_carver_shape(bpy.types.Panel):
    bl_label = "Cutter Shape"
    bl_idname = "TOPBAR_PT_carver_shape"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mode = 'OBJECT' if context.mode == 'OBJECT' else 'EDIT_MESH'
        tool = context.workspace.tools.from_space_view3d_mode(mode)
        props = tool.operator_properties(tool.idname)

        # Box & Circle
        if tool.idname == "object.carve_box" or tool.idname == "object.carve_circle":
            if tool.idname == "object.carve_circle":
                layout.prop(props, "subdivision", text="Vertices")
            layout.prop(props, "rotation")
            layout.prop(props, "origin", expand=True)
            layout.prop(props, "aspect", expand=True)

            if props.alignment == 'SURFACE':
                layout.prop(props, "orientation")
                layout.prop(props, "offset", text="Offset")
                layout.prop(props, "align_to_all")
            if props.alignment == 'CURSOR':
                layout.prop(props, "alignment_axis", text="Align to", expand=True)

        # Polyline
        elif tool.idname == "object.carve_polyline":
            if props.alignment == 'SURFACE':
                layout.prop(props, "offset", text="Offset")
                layout.prop(props, "align_to_all")


class TOPBAR_PT_carver_effects(bpy.types.Panel):
    bl_label = "Cutter Effects"
    bl_idname = "TOPBAR_PT_carver_effects"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mode = 'OBJECT' if context.mode == 'OBJECT' else 'EDIT_MESH'
        tool = context.workspace.tools.from_space_view3d_mode(mode)
        props = tool.operator_properties(tool.idname)

        # Bevel
        if tool.idname == 'object.carve_box':
            header, panel = layout.panel("OBJECT_OT_carver_effects_bevel", default_closed=False)
            header.label(text="Bevel")
            if panel:
                panel.prop(props, "use_bevel", text="Side Bevel")
                col = panel.column(align=True)
                col.prop(props, "bevel_segments", text="Segments")
                col.prop(props, "bevel_width", text="Radius")
                col.prop(props, "bevel_profile", text="Profile", slider=True)

                if props.use_bevel == False:
                    col.enabled = False

        # Array
        header, panel = layout.panel("OBJECT_OT_carver_effects_array", default_closed=False)
        header.label(text="Array")
        if panel:
            col = panel.column(align=True)
            col.prop(props, "columns")
            col.prop(props, "rows")
            col.prop(props, "gap")


class TOPBAR_PT_carver_cutter(bpy.types.Panel):
    bl_label = "Carver Cutter"
    bl_idname = "TOPBAR_PT_carver_cutter"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mode = 'OBJECT' if context.mode == 'OBJECT' else 'EDIT_MESH'
        tool = context.workspace.tools.from_space_view3d_mode(mode)
        props = tool.operator_properties(tool.idname)

        # Modifier properties.
        col = layout.column()
        col.prop(props, "pin", text="Pin Modifier")
        col.separator()

        # Cutter object properties.
        col = layout.column()
        row = col.row()
        row.prop(props, "display", text="Display", expand=True)
        if props.mode == 'MODIFIER':
            col.prop(props, "parent")
            col.prop(props, "hide")
            col.prop(props, "cutter_origin", text="Origin")

        # Auto Smooth.
        layout.separator()
        col = layout.column(align=True)
        col.prop(props, "auto_smooth", text="Auto Smooth")
        col1 = layout.column()
        col1.prop(props, "sharp_angle")
        if not props.auto_smooth:
            col1.enabled = False



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = (
    TOPBAR_PT_carver_shape,
    TOPBAR_PT_carver_effects,
    TOPBAR_PT_carver_cutter,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
