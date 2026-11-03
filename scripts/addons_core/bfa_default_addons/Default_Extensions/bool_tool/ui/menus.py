import bpy

from ..functions.canvas import (
    is_canvas,
)

from .common import (
    boolean_operators_menu,
    boolean_extras_menu,
)


#### ------------------------------ /boolean_menu/ ------------------------------ ####

# 3D Viewport (Object Mode) -> Object
class VIEW3D_MT_boolean(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_carve")
        layout.separator()
        boolean_operators_menu(self, context)
        boolean_extras_menu(self, context)


def object_mode_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_boolean")



#### ------------------------------ /popup_menu/ ------------------------------ ####

# Shift-Ctrl-B Menu
class VIEW3D_MT_boolean_popup(bpy.types.Menu):
    bl_label = "Boolean"
    bl_idname = "VIEW3D_MT_boolean_popup"

    def draw(self, context):
        boolean_operators_menu(self, context)
        boolean_extras_menu(self, context)



#### ------------------------------ /carve_menu/ ------------------------------ ####

class VIEW3D_MT_carve(bpy.types.Menu):
    bl_label = "Carve"
    bl_idname = "VIEW3D_MT_carve"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.carve_box", text="Box Carve")
        layout.operator("object.carve_circle", text="Circle Carve")
        layout.operator("object.carve_polyline", text="Polyline Carve")


# Separate "Carve" menu in Edit Mode (where we don't have "Boolean" menu).
def edit_mode_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_carve")



#### ------------------------------ /select_menu/ ------------------------------ ####

def select_menu(self, context):
    layout = self.layout
    obj = context.active_object

    if not obj:
        return

    if is_canvas(obj) or obj.booleans.cutter:
        layout.separator()

    if is_canvas(obj):
        layout.operator("object.boolean_select_all", text="Boolean Cutters")
    if obj.booleans.cutter:
        layout.operator("object.select_cutter_canvas", text="Boolean Canvases")



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = (
    VIEW3D_MT_boolean,
    VIEW3D_MT_boolean_popup,
    VIEW3D_MT_carve,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # MENU
    bpy.types.VIEW3D_MT_object.append(object_mode_menu)
    bpy.types.VIEW3D_MT_edit_mesh.append(edit_mode_menu)
    bpy.types.VIEW3D_MT_select_object.append(select_menu)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Object Mode")

    kmi = km.keymap_items.new("wm.call_menu", 'B', 'PRESS', ctrl=True, shift=True)
    kmi.properties.name = "VIEW3D_MT_boolean_popup"
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # MENU
    bpy.types.VIEW3D_MT_object.remove(object_mode_menu)
    bpy.types.VIEW3D_MT_edit_mesh.remove(edit_mode_menu)
    bpy.types.VIEW3D_MT_select_object.remove(select_menu)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
