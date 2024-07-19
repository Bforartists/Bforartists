import bpy
from .functions.poll import is_canvas
from .functions.list import list_canvas_cutters


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_sidebar_category(self, context):
    try:
        bpy.utils.unregister_class(VIEW3D_PT_boolean)
        bpy.utils.unregister_class(VIEW3D_PT_boolean_properties)
        bpy.utils.unregister_class(VIEW3D_PT_boolean_cutters)
    except:
        pass

    VIEW3D_PT_boolean.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean)

    VIEW3D_PT_boolean_properties.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean_properties)

    VIEW3D_PT_boolean_cutters.bl_category = self.sidebar_category
    bpy.utils.register_class(VIEW3D_PT_boolean_cutters)



#### ------------------------------ /ui/ ------------------------------ ####

def boolean_operators_menu(self, context):
    layout = self.layout
    col = layout.column(align=True)

    col.label(text="Auto Boolean")
    col.operator("object.boolean_auto_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.boolean_auto_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.boolean_auto_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.boolean_auto_slice", text="Slice", icon='SELECT_DIFFERENCE')

    col.separator()
    col.label(text="Brush Boolean")
    col.operator("object.boolean_brush_difference", text="Difference", icon='SELECT_SUBTRACT')
    col.operator("object.boolean_brush_union", text="Union", icon='SELECT_EXTEND')
    col.operator("object.boolean_brush_intersect", text="Intersect", icon='SELECT_INTERSECT')
    col.operator("object.boolean_brush_slice", text="Slice", icon='SELECT_DIFFERENCE')


def boolean_extras_menu(self, context):
    layout = self.layout
    col = layout.column(align=True)

    # canvas_operators
    active_object = context.active_object
    if active_object.booleans.canvas == True and any(modifier.name.startswith("boolean_") for modifier in active_object.modifiers):
        col.separator()
        col.operator("object.boolean_toggle_all", text="Toggle All Cuters")
        col.operator("object.boolean_apply_all", text="Apply All Cutters")
        col.operator("object.boolean_remove_all", text="Remove All Cutters")

    # cutter_operators
    if active_object.booleans.cutter:
        col.separator()
        col.operator("object.boolean_toggle_cutter", text="Toggle Cutter").method='ALL'
        col.operator("object.boolean_apply_cutter", text="Apply Cutter").method='ALL'
        col.operator("object.boolean_remove_cutter", text="Remove Cutter").method='ALL'



#### ------------------------------ /panels/ ------------------------------ ####

# Boolean Operators Panel
class VIEW3D_PT_boolean(bpy.types.Panel):
    bl_label = "Boolean"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.show_in_sidebar

    def draw(self, context):
        boolean_operators_menu(self, context)


# Properties Panel
class VIEW3D_PT_boolean_properties(bpy.types.Panel):
    bl_label = "Properties"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return (prefs.show_in_sidebar and context.active_object
                    and (is_canvas(context.active_object) or context.active_object.booleans.cutter))

    def draw(self, context):
        boolean_extras_menu(self, context)


# Cutters Panel
class VIEW3D_PT_boolean_cutters(bpy.types.Panel):
    bl_label = "Cutters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_boolean"

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.show_in_sidebar and context.active_object and is_canvas(context.active_object)

    def draw(self, context):
        layout = self.layout
        canvas = context.active_object
        __, modifiers = list_canvas_cutters([canvas])

        for mod in modifiers:
            col = layout.column(align=True)
            row = col.row(align=True)

            # icon
            if mod.operation == 'DIFFERENCE':
                icon = 'SELECT_SUBTRACT'
            elif mod.operation == 'UNION':
                icon = 'SELECT_EXTEND'
            elif mod.operation == 'INTERSECT':
                icon = 'SELECT_INTERSECT'

            row.prop(mod.object, "name", text="", icon=icon)

            # Toggle
            op_toggle = row.operator("object.boolean_toggle_cutter", text="", icon='HIDE_OFF' if mod.show_viewport else 'HIDE_ON')
            op_toggle.method = 'SPECIFIED'
            op_toggle.specified_cutter = mod.object.name
            op_toggle.specified_canvas = canvas.name

            # Apply
            op_apply = row.operator("object.boolean_apply_cutter", text="", icon='CHECKMARK')
            op_apply.method = 'SPECIFIED'
            op_apply.specified_cutter = mod.object.name
            op_apply.specified_canvas = canvas.name

            # Remove
            op_remove = row.operator("object.boolean_remove_cutter", text="", icon='X')
            op_remove.method = 'SPECIFIED'
            op_remove.specified_cutter = mod.object.name
            op_remove.specified_canvas = canvas.name



#### ------------------------------ /menus/ ------------------------------ ####

# Object Mode Menu
class VIEW3D_MT_boolean(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean"

    def draw(self, context):
        boolean_operators_menu(self, context)
        boolean_extras_menu(self, context)


def bool_tool_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_boolean")


def boolean_select_menu(self, context):
    layout = self.layout
    active_obj = context.active_object
    if active_obj:
        if active_obj.booleans.canvas == True or active_obj.booleans.cutter:
            layout.separator()

        if active_obj.booleans.canvas == True:
            layout.operator("object.boolean_select_all", text="Boolean Cutters")
        if active_obj.booleans.cutter:
            layout.operator("object.select_cutter_canvas", text="Boolean Canvases")



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    VIEW3D_MT_boolean,
    VIEW3D_PT_boolean,
    VIEW3D_PT_boolean_properties,
    VIEW3D_PT_boolean_cutters,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    prefs = bpy.context.preferences.addons[__package__].preferences
    update_sidebar_category(prefs, bpy.context)

    # MENU
    bpy.types.VIEW3D_MT_object.append(bool_tool_menu)
    bpy.types.VIEW3D_MT_select_object.append(boolean_select_menu)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")
    kmi = km.keymap_items.new("wm.call_menu", 'B', 'PRESS', ctrl=True, shift=True)
    kmi.properties.name = "VIEW3D_MT_boolean"
    kmi.active = True
    addon_keymaps.append(km)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # MENU
    bpy.types.VIEW3D_MT_object.remove(bool_tool_menu)
    bpy.types.VIEW3D_MT_select_object.remove(boolean_select_menu)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()
