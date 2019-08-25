# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )


# View Menu's #
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

        layout.separator()
        layout.prop(context.space_data.fx_settings, "use_ssao",
                    text="Ambient Occlusion", icon="GROUP")
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
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_view.append(menu_func)

# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_view.remove(menu_func)

if __name__ == "__main__":
    register()
