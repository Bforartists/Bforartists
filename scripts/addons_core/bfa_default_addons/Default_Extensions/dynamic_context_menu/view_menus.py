# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )

from . edit_mesh import *

# View Menu's #
class VIEW3D_MT_View_Menu(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        layout.menu("VIEW3D_MT_view_viewpoint")
        layout.menu("VIEW3D_MT_view_align")
        layout.menu("VIEW3D_MT_view_navigation")
        layout.menu("INFO_MT_area")
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_view_regions", text="View Regions")
        layout.menu("VIEW3D_MT_Shade")
        layout.separator()

        layout.operator("view3d.view_selected", text="Frame Selected").use_all_regions = False
        if view.region_quadviews:
            layout.operator("view3d.view_selected", text="Frame Selected (Quad View)").use_all_regions = True
        layout.operator("view3d.view_all").center = False
        layout.separator()

        layout.operator("view3d.view_persportho", text="Perspective/Orthographic")
        layout.menu("VIEW3D_MT_view_local")
        layout.separator()

        layout.operator("render.opengl", text="Viewport Render Image", icon='RENDER_STILL')
        layout.operator("render.opengl", text="Viewport Render Animation", icon='RENDER_ANIMATION').animation = True
        layout.separator()

        layout.prop(view, "show_region_toolbar")
        layout.prop(view, "show_region_ui")
        layout.prop(view, "show_region_tool_header")
        layout.prop(view, "show_region_hud")



# Display Wire (Thanks to marvin.k.breuer) #
class VIEW3D_OT_Display_Wire_All(Operator):
    bl_label = "Wire on All Objects"
    bl_idname = "view3d.display_wire_all"
    bl_description = "Enable/Disable Display Wire on All Objects"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        is_error = False
        for obj in bpy.data.objects:
            try:
                if obj.show_wire:
                    obj.show_all_edges = False
                    obj.show_wire = False
                else:
                    obj.show_all_edges = True
                    obj.show_wire = True
            except:
                is_error = True
                pass

        if is_error:
            self.report({'WARNING'},
                        "Wire on All Objects could not be completed for some objects")

        return {'FINISHED'}


# Matcap and AO, Wire all and X-Ray entries thanks to marvin.k.breuer
class VIEW3D_MT_Shade(Menu):
    bl_label = "Shade"

    def draw(self, context):
        layout = self.layout

#        layout.prop(context.space_data, "viewport_shade", expand=True)

        if context.active_object:
            if(context.mode == 'EDIT_MESH'):
                layout.operator("MESH_OT_faces_shade_smooth", icon='SHADING_RENDERED')
                layout.operator("MESH_OT_faces_shade_flat", icon='SHADING_SOLID')
            else:
                layout.operator("OBJECT_OT_shade_smooth", icon='SHADING_RENDERED')
                layout.operator("OBJECT_OT_shade_flat", icon='SHADING_SOLID')

        layout.separator()
        layout.operator("view3d.display_wire_all", text="Wire all", icon='SHADING_WIRE')

#        layout.prop(context.space_data, "use_matcap", icon="MATCAP_01")

#        if context.space_data.use_matcap:
#            row = layout.column(1)
#            row.scale_y = 0.3
#            row.scale_x = 0.5
#            row.template_icon_view(context.space_data, "matcap_icon")

def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_Shade")

# List The Classes #

classes = (
    VIEW3D_MT_Shade,
    VIEW3D_OT_Display_Wire_All,
    VIEW3D_MT_View_Menu
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
