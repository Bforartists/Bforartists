import bpy
from bpy.types import Menu


class ADD_CAMERA_RIGS_MT_composition_guides_menu(Menu):
    bl_label = "Composition Guides"
    bl_idname = "ADD_CAMERA_RIGS_MT_composition_guides_menu"

    def draw(self, context):
        layout = self.layout

        activeCameraName = bpy.context.active_object.children[0].name
        cam = bpy.data.cameras[bpy.data.objects[activeCameraName].data.name]

        layout.prop(cam, "show_safe_areas")
        layout.row().separator()
        layout.prop(cam, "show_composition_center")
        layout.prop(cam, "show_composition_center_diagonal")
        layout.prop(cam, "show_composition_golden")
        layout.prop(cam, "show_composition_golden_tria_a")
        layout.prop(cam, "show_composition_golden_tria_b")
        layout.prop(cam, "show_composition_harmony_tri_a")
        layout.prop(cam, "show_composition_harmony_tri_b")
        layout.prop(cam, "show_composition_thirds")


def draw_item(self, context):
    layout = self.layout
    layout.menu(CustomMenu.bl_idname)


def register():
    bpy.utils.register_class(ADD_CAMERA_RIGS_MT_composition_guides_menu)


def unregister():
    bpy.utils.unregister_class(ADD_CAMERA_RIGS_MT_composition_guides_menu)


if __name__ == "__main__":
    register()
