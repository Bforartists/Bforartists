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

from bl_ui.properties_paint_common import UnifiedPaintPanel
from .object_menus import *

# Brushes Menu's #
# Thanks to CoDEmanX for the code
class VIEW3D_MT_Brush_Selection(Menu):
    bl_label = "Brush Tool"

    def draw(self, context):
        layout = self.layout
        settings = UnifiedPaintPanel.paint_settings(context)

        # check if brush exists (for instance, in paint mode before adding a slot)
        if hasattr(settings, 'brush'):
            brush = settings.brush
        else:
            brush = None

        if not brush:
            layout.label(text="No Brushes currently available", icon="INFO")
            return

        if not context.particle_edit_object:
            if UseBrushesLists():
                flow = layout.column_flow(columns=3)

                for brsh in bpy.data.brushes:
                    if (context.sculpt_object and brsh.use_paint_sculpt):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.sculpt.brush"
                        props.value = brsh.name
                    elif (context.image_paint_object and brsh.use_paint_image):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.image_paint.brush"
                        props.value = brsh.name
                    elif (context.vertex_paint_object and brsh.use_paint_vertex):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.vertex_paint.brush"
                        props.value = brsh.name
                    elif (context.weight_paint_object and brsh.use_paint_weight):
                        props = flow.operator("wm.context_set_id", text=brsh.name,
                                              icon_value=layout.icon(brsh))
                        props.data_path = "tool_settings.weight_paint.brush"
                        props.value = brsh.name
            else:
                layout.template_ID_preview(settings, "brush", new="brush.add", rows=3, cols=8)


class VIEW3D_MT_Brush_Settings(Menu):
    bl_label = "Brush Settings"

    def draw(self, context):
        layout = self.layout
        settings = UnifiedPaintPanel.paint_settings(context)
        brush = getattr(settings, "brush", None)

        ups = context.tool_settings.unified_paint_settings
        layout.prop(ups, "use_unified_size", text="Unified Size")
        layout.prop(ups, "use_unified_strength", text="Unified Strength")
        if context.image_paint_object or context.vertex_paint_object:
            layout.prop(ups, "use_unified_color", text="Unified Color")
        layout.separator()

        if not brush:
            layout.label(text="No Brushes currently available", icon="INFO")
            return

        layout.menu("VIEW3D_MT_brush_paint_modes")

        if context.sculpt_object:
            sculpt_tool = brush.sculpt_tool

            layout.separator()
            layout.operator_menu_enum("brush.curve_preset", "shape", text="Curve Preset")
            layout.separator()

            if sculpt_tool != 'GRAB':
                layout.prop_menu_enum(brush, "stroke_method")

                if sculpt_tool in {'DRAW', 'PINCH', 'INFLATE', 'LAYER', 'CLAY'}:
                    layout.prop_menu_enum(brush, "direction")

                if sculpt_tool == 'LAYER':
                    layout.prop(brush, "use_persistent")
                    layout.operator("sculpt.set_persistent_base")


# Sculpt Menu's #
class VIEW3D_MT_Sculpts(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings
        sculpt = toolsettings.sculpt

        layout.prop(sculpt, "use_symmetry_x")
        layout.prop(sculpt, "use_symmetry_y")
        layout.prop(sculpt, "use_symmetry_z")

        layout.separator()
        layout.prop(sculpt, "lock_x")
        layout.prop(sculpt, "lock_y")
        layout.prop(sculpt, "lock_z")

        layout.separator()
        layout.prop(sculpt, "use_threaded", text="Threaded Sculpt")
        layout.prop(sculpt, "show_low_resolution")
        layout.prop(sculpt, "use_deform_only")

        layout.separator()
        layout.prop(sculpt, "show_brush")


class VIEW3D_MT_Hide_Masks(Menu):
    bl_label = "Hide/Mask"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("paint.mask_lasso_gesture", text="Lasso Mask")
        layout.separator()
        props = layout.operator("view3d.select_box", text="Box Mask")
        props = layout.operator("paint.hide_show", text="Box Hide")
        props.action = 'HIDE'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Box Show")
        props.action = 'SHOW'
        props.area = 'INSIDE'
        layout.separator()

        props = layout.operator("paint.mask_flood_fill", text="Fill Mask")
        props.mode = 'VALUE'
        props.value = 1

        props = layout.operator("paint.mask_flood_fill", text="Clear Mask")
        props.mode = 'VALUE'
        props.value = 0

        layout.operator("paint.mask_flood_fill", text="Invert Mask").mode = 'INVERT'
        layout.separator()

        props = layout.operator("paint.hide_show", text="Show All", icon="RESTRICT_VIEW_OFF")
        props.action = 'SHOW'
        props.area = 'ALL'

        props = layout.operator("paint.hide_show", text="Hide Masked", icon="RESTRICT_VIEW_ON")
        props.area = 'MASKED'
        props.action = 'HIDE'


# Sculpt Specials Menu (Thanks to marvin.k.breuer) #
class VIEW3D_MT_Sculpt_Specials(Menu):
    bl_label = "Sculpt Specials"

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings

        if context.sculpt_object.use_dynamic_topology_sculpting:
            layout.operator("sculpt.dynamic_topology_toggle",
                            icon='X', text="Disable Dyntopo")
            layout.separator()

            if (settings.sculpt.detail_type_method == 'CONSTANT'):
                layout.prop(settings.sculpt, "constant_detail", text="Const.")
                layout.operator("sculpt.sample_detail_size", text="", icon='EYEDROPPER')
            else:
                layout.prop(settings.sculpt, "detail_size", text="Detail")
            layout.separator()

            layout.operator("sculpt.symmetrize", icon='ARROW_LEFTRIGHT')
            layout.prop(settings.sculpt, "symmetrize_direction", "")
            layout.separator()

            layout.operator("sculpt.optimize")
            if (settings.sculpt.detail_type_method == 'CONSTANT'):
                layout.operator("sculpt.detail_flood_fill")
            layout.separator()

            layout.prop(settings.sculpt, "detail_refine_method", text="")
            layout.prop(settings.sculpt, "detail_type_method", text="")
            layout.separator()
            layout.prop(settings.sculpt, "use_smooth_shading", "Smooth")
        else:
            layout.operator("sculpt.dynamic_topology_toggle", text="Enable Dyntopo")


# Vertex Color Menu #
class VIEW3D_MT_Vertex_Colors(Menu):
    bl_label = "Vertex Colors"

    def draw(self, context):
        layout = self.layout
        layout.operator("paint.vertex_color_set")
        layout.separator()

        layout.operator("paint.vertex_color_smooth")
        layout.operator("paint.vertex_color_dirt")


# Weight Paint Menu #
class VIEW3D_MT_Paint_Weights(Menu):
    bl_label = "Weights"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.weight_from_bones",
                        text="Assign Automatic From Bones").type = 'AUTOMATIC'
        layout.operator("paint.weight_from_bones",
                        text="Assign From Bone Envelopes").type = 'ENVELOPES'
        layout.separator()

        layout.operator("object.vertex_group_normalize_all", text="Normalize All")
        layout.operator("object.vertex_group_normalize", text="Normalize")
        layout.separator()

        layout.operator("object.vertex_group_mirror", text="Mirror")
        layout.operator("object.vertex_group_invert", text="Invert")
        layout.separator()

        layout.operator("object.vertex_group_clean", text="Clean")
        layout.operator("object.vertex_group_quantize", text="Quantize")
        layout.separator()

        layout.operator("object.vertex_group_levels", text="Levels")
        layout.operator("object.vertex_group_smooth", text="Smooth")
        layout.separator()

        props = layout.operator("object.data_transfer", text="Transfer Weights")
        props.use_reverse_transfer = True
        props.data_type = 'VGROUP_WEIGHTS'
        layout.separator()

        layout.operator("object.vertex_group_limit_total", text="Limit Total")
        layout.operator("object.vertex_group_fix", text="Fix Deforms")
        layout.separator()

        layout.operator("paint.weight_set")


class VIEW3D_MT_Angle_Control(Menu):
    bl_label = "Angle Control"

    @classmethod
    def poll(cls, context):
        settings = UnifiedPaintPanel.paint_settings(context)
        if not settings:
            return False

        brush = settings.brush
        tex_slot = brush.texture_slot

        return tex_slot.has_texture_angle and tex_slot.has_texture_angle_source

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        sculpt = (context.sculpt_object is not None)

        tex_slot = brush.texture_slot

        layout.prop(tex_slot, "use_rake", text="Rake")

        if brush.brush_capabilities.has_random_texture_angle and tex_slot.has_random_texture_angle:
            if sculpt:
                if brush.sculpt_capabilities.has_random_texture_angle:
                    layout.prop(tex_slot, "use_random", text="Random")
            else:
                layout.prop(tex_slot, "use_random", text="Random")


# List The Classes #

classes = (
    VIEW3D_MT_Angle_Control,
    VIEW3D_MT_Sculpt_Specials,
    VIEW3D_MT_Brush_Settings,
    VIEW3D_MT_Brush_Selection,
    VIEW3D_MT_Sculpts,
    VIEW3D_MT_Hide_Masks,
    VIEW3D_MT_Vertex_Colors,
    VIEW3D_MT_Paint_Weights,
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
