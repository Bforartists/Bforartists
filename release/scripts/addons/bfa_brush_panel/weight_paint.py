import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Union

import bpy
import bpy.utils.previews

from .common import DEFAULT_ICON_FOR_BLEND_MODE, DEFAULT_ICON_FOR_IDNAME, _icon_value_from_icon_name, column_count


def get_weight_brush_icon(weight_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_weight."
    idname = weight_brush.weight_tool
    icon_name = icon_prefix + idname.lower()
    print("Loading brush icon", weight_brush, idname)
    return _icon_value_from_icon_name(icon_name)


@dataclass
class WeightBrushButton:
    brush_name: str
    icon_name: str
    icon_value: int

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout, icon_only=False):
        active_brush = context.tool_settings.weight_paint.brush
        is_active = False
        if active_brush is not None:
            is_active = active_brush.name == self.brush_name

        op = layout.operator(
            "bfa.set_brush",
            text="" if icon_only else self.brush_name,
            icon=self.icon_name,
            icon_value=self.icon_value,
            depress=is_active,
        )
        op.paint_settings_attr_name = "weight_paint"
        op.brush_name = self.brush_name


def get_weight_brush_buttons():
    """Get list of weight brush buttons from brushes in the blend file"""
    buttons: Dict[str, List[WeightBrushButton]] = defaultdict(list)
    brush: bpy.types.Brush
    for brush in sorted(bpy.data.brushes, key=lambda b: b.name):
        if not brush.use_paint_weight:
            continue
        if brush.use_custom_icon and brush.icon_filepath:
            pcoll = preview_collections["main"]
            filepath = os.path.abspath(bpy.path.abspath(brush.icon_filepath))
            try:
                preview = pcoll.load(filepath, filepath, "IMAGE")
            except KeyError:
                # Blender API raises KeyError if image is already in the collection
                preview = pcoll[filepath]

            icon_value = preview.icon_id
            icon_name = "NONE"
        else:
            # TODO: refactor
            icon_value = 0
            if brush.blend == "MIX":
                icon_name = DEFAULT_ICON_FOR_IDNAME.get(brush.weight_tool, None)
            else:
                icon_name = DEFAULT_ICON_FOR_BLEND_MODE.get(brush.blend, None)
            if icon_name is None:
                icon_name = "NONE"
                icon_value = get_weight_brush_icon(brush)
        buttons[brush.weight_tool].append(WeightBrushButton(brush.name, icon_name, icon_value))
        # TODO: support linked brushes
    return buttons


# From BFA space_toolbar_tabs


# TODO: create brush panels dynamically, instead of repeating code
# Weight Draw Brush panel
class BFA_PT_brush_weight(bpy.types.Panel):
    bl_label = "Draw"
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        buttons = get_weight_brush_buttons()

        num_cols = column_count(context.region)

        # TODO: fix icon_value icons not centered

        if num_cols == 4:
            col = layout.column(align=True)
            for but in buttons["DRAW"]:
                but.draw(context, col)

        else:
            col = layout.column_flow(columns=num_cols, align=True)
            for but in buttons["DRAW"]:
                but.draw(context, col, icon_only=True)


# Weight Smear Brush panel
class BFA_PT_brush_weight_smear(bpy.types.Panel):
    bl_label = "Smear"
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        buttons = get_weight_brush_buttons()

        num_cols = column_count(context.region)

        # TODO: fix icon_value icons not centered

        if num_cols == 4:
            col = layout.column(align=True)
            for but in buttons["SMEAR"]:
                but.draw(context, col)
        else:
            col = layout.column_flow(columns=num_cols, align=True)
            for but in buttons["SMEAR"]:
                but.draw(context, col, icon_only=True)


# Weight Average brush panel
class BFA_PT_brush_weight_average(bpy.types.Panel):
    bl_label = "Average"
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        buttons = get_weight_brush_buttons()

        num_cols = column_count(context.region)

        # TODO: fix icon_value icons not centered

        if num_cols == 4:
            col = layout.column(align=True)
            for but in buttons["AVERAGE"]:
                but.draw(context, col)

        else:

            col = layout.column_flow(columns=num_cols, align=True)
            for but in buttons["AVERAGE"]:
                but.draw(context, col, icon_only=True)


# Weight Blur Brush panel
class BFA_PT_brush_weight_blur(bpy.types.Panel):
    bl_label = "Blur"
    bl_region_type = "TOOLS"
    bl_space_type = "VIEW_3D"
    bl_category = "Brushes"
    bl_options = {"HIDE_BG"}

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.scale_y = 2
        buttons = get_weight_brush_buttons()

        num_cols = column_count(context.region)

        # TODO: fix icon_value icons not centered

        if num_cols == 4:
            col = layout.column(align=True)
            for but in buttons["BLUR"]:
                but.draw(context, col)

        else:
            col = layout.column_flow(columns=num_cols, align=True)
            for but in buttons["BLUR"]:
                but.draw(context, col, icon_only=True)


# Custom Image Previews
preview_collections: Dict[
    str,
    Union[bpy.utils.previews.ImagePreviewCollection, Dict[str, bpy.types.ImagePreview]],
] = {}

# Register and unregister


def register():
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    bpy.utils.register_class(BFA_PT_brush_weight)
    bpy.utils.register_class(BFA_PT_brush_weight_smear)
    bpy.utils.register_class(BFA_PT_brush_weight_average)
    bpy.utils.register_class(BFA_PT_brush_weight_blur)


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    bpy.utils.unregister_class(BFA_PT_brush_weight)
    bpy.utils.unregister_class(BFA_PT_brush_weight_smear)
    bpy.utils.unregister_class(BFA_PT_brush_weight_average)
    bpy.utils.unregister_class(BFA_PT_brush_weight_blur)
