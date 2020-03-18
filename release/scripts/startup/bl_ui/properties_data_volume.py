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
from bpy.types import Panel, UIList
from rna_prop_ui import PropertyPanel


class DataButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.volume and (engine in cls.COMPAT_ENGINES)


class DATA_PT_context_volume(DataButtonsPanel, Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout

        ob = context.object
        volume = context.volume
        space = context.space_data

        if ob:
            layout.template_ID(ob, "data")
        elif volume:
            layout.template_ID(space, "pin_id")


class DATA_PT_volume_file(DataButtonsPanel, Panel):
    bl_label = "OpenVDB File"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout

        volume = context.volume
        volume.grids.load()

        layout.prop(volume, "filepath", text="")

        if len(volume.filepath):
            layout.use_property_split = True
            layout.use_property_decorate = False

            col = layout.column(align=True)
            col.prop(volume, "is_sequence")
            if volume.is_sequence:
                col.prop(volume, "frame_duration", text="Frames")
                col.prop(volume, "frame_start", text="Start")
                col.prop(volume, "frame_offset", text="Offset")
                col.prop(volume, "sequence_mode", text="Mode")

        error_msg = volume.grids.error_message
        if len(error_msg):
          layout.separator()
          col = layout.column(align=True)
          col.label(text="Failed to load volume:")
          col.label(text=error_msg)


class VOLUME_UL_grids(UIList):
    def draw_item(self, context, layout, data, grid, icon, active_data, active_propname, index):
        name = grid.name
        data_type = grid.bl_rna.properties['data_type'].enum_items[grid.data_type]

        layout.label(text=name)
        row = layout.row()
        row.alignment = 'RIGHT'
        row.active = False
        row.label(text=data_type.name)


class DATA_PT_volume_grids(DataButtonsPanel, Panel):
    bl_label = "Grids"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout

        volume = context.volume
        volume.grids.load()

        layout.template_list("VOLUME_UL_grids", "grids", volume, "grids", volume.grids, "active_index", rows=3)


class DATA_PT_volume_render(DataButtonsPanel, Panel):
    bl_label = "Render"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        volume = context.volume
        render = volume.render

        col = layout.column(align=True)
        col.prop(render, "space")

        if scene.render.engine == 'CYCLES':
            col.prop(render, "step_size")

            col = layout.column(align=True)
            col.prop(render, "clipping")


class DATA_PT_volume_viewport_display(DataButtonsPanel, Panel):
    bl_label = "Viewport Display"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        volume = context.volume
        display = volume.display

        col = layout.column(align=True)
        col.prop(display, "wireframe_type")
        sub = col.row()
        sub.active = display.wireframe_type in {'BOXES', 'POINTS'}
        sub.prop(display, "wireframe_detail", text="Detail")

        layout.prop(display, "density")


class DATA_PT_custom_props_volume(DataButtonsPanel, PropertyPanel, Panel):
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    _context_path = "object.data"
    _property_type = bpy.types.Volume


classes = (
    DATA_PT_context_volume,
    DATA_PT_volume_grids,
    DATA_PT_volume_file,
    DATA_PT_volume_viewport_display,
    DATA_PT_volume_render,
    DATA_PT_custom_props_volume,
    VOLUME_UL_grids,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
