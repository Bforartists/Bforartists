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

# <pep8 compliant>
import bpy
from rna_prop_ui import PropertyPanel

narrowui = bpy.context.user_preferences.view.properties_width_check


class DataButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"


class DATA_PT_context_camera(DataButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_show_header = False
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        engine = context.scene.render.engine
        return context.camera and (engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        cam = context.camera
        space = context.space_data
        wide_ui = context.region.width > narrowui

        if wide_ui:
            split = layout.split(percentage=0.65)
            if ob:
                split.template_ID(ob, "data")
                split.separator()
            elif cam:
                split.template_ID(space, "pin_id")
                split.separator()
        else:
            if ob:
                layout.template_ID(ob, "data")
            elif cam:
                layout.template_ID(space, "pin_id")


class DATA_PT_custom_props_camera(DataButtonsPanel, PropertyPanel, bpy.types.Panel):
    _context_path = "object.data"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        engine = context.scene.render.engine
        return context.camera and (engine in __class__.COMPAT_ENGINES)


class DATA_PT_camera(DataButtonsPanel, bpy.types.Panel):
    bl_label = "Lens"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        engine = context.scene.render.engine
        return context.camera and (engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        cam = context.camera
        wide_ui = context.region.width > narrowui

        if wide_ui:
            layout.prop(cam, "type", expand=True)
        else:
            layout.prop(cam, "type", text="")

        split = layout.split()

        col = split.column()
        if cam.type == 'PERSP':
            if cam.lens_unit == 'MILLIMETERS':
                col.prop(cam, "lens", text="Angle")
            elif cam.lens_unit == 'DEGREES':
                col.prop(cam, "angle")
            if wide_ui:
                col = split.column()
            col.prop(cam, "lens_unit", text="")

        elif cam.type == 'ORTHO':
            col.prop(cam, "ortho_scale")

        layout.prop(cam, "panorama")

        split = layout.split()

        col = split.column(align=True)
        col.label(text="Shift:")
        col.prop(cam, "shift_x", text="X")
        col.prop(cam, "shift_y", text="Y")

        if wide_ui:
            col = split.column(align=True)
        col.label(text="Clipping:")
        col.prop(cam, "clip_start", text="Start")
        col.prop(cam, "clip_end", text="End")

        layout.label(text="Depth of Field:")

        split = layout.split()

        col = split.column()
        col.prop(cam, "dof_object", text="")

        if wide_ui:
            col = split.column()
        else:
            col = col.column()
        if cam.dof_object != None:
            col.enabled = False
        col.prop(cam, "dof_distance", text="Distance")


class DATA_PT_camera_display(DataButtonsPanel, bpy.types.Panel):
    bl_label = "Display"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}

    @staticmethod
    def poll(context):
        engine = context.scene.render.engine
        return context.camera and (engine in __class__.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        cam = context.camera
        wide_ui = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.prop(cam, "show_limits", text="Limits")
        col.prop(cam, "show_mist", text="Mist")
        col.prop(cam, "show_title_safe", text="Title Safe")
        col.prop(cam, "show_name", text="Name")

        if wide_ui:
            col = split.column()
        col.prop(cam, "draw_size", text="Size")
        col.separator()
        col.prop(cam, "show_passepartout", text="Passepartout")
        sub = col.column()
        sub.active = cam.show_passepartout
        sub.prop(cam, "passepartout_alpha", text="Alpha", slider=True)


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()
