bl_info = {
    "name": "Bforartists Brush Panel",
    "author": "Iyad Ahmed (@cgonfire), Draise (@trinumedia)",
    "version": (0, 0, 10),
    "blender": (3, 1, 0),
    "location": "3D View > Tools",
    "description": "This is an official Bforartists addon to add top-level brush presets to panels in the toolshelf. Weight Paint mode only (for now)",
    "category": "Weight Paint",
}

## INFO ##
# This version of the addon adds Weight Paint top-level brush presets into a new toolshelf tab and brush panels you can collapse, pin or use.
# The panels update depending on how many brush presets you have per brush group.
# The buttons also highlight when activated, and the list updates when you create and remove brushes.
# The iconography also updates to custom icons when they are defined by the user.
# The panel also is responsive with the standard 1,2,3 and text row format defined by Bforartists.
# In use cases, this has already proven a huge time saver when weighting rigs - very intuitive.

## KNOWN ISSUES ##
# There is a known issue which will require a new patch to Bforartists which is... when making or deleting brushes, the panel will not update till you mouse over it.
# A future patch will intentionally update the panels when you make and delete brushes from the property shelf operators. Coming soon.

## TO DO ##
# - add the other paint modes: Grease Pencil Draw Mode, Vertex Paint Mode, Texture Paint Mode and potentially Sculpt Mode
# - Add the 16px built in icons as the defaults for the brushes instead of the larger ones (breaks layout)

## Updates ##
# - removed icons from panel headers

import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Union

import bpy
import bpy.utils.previews


# This is where you define the default icon per the brush mix mode type, "DELETE" icon indicates icons to be done
DEFAULT_ICON_FOR_BLEND_MODE = {
    #"MIX": "PAINT_DRAW", # This currently overrides all other brush defaults since the other brushes default to "Mix".
    "DARKEN": "PAINT_DARKEN",
    "MUL": "PAINT_MULTIPLY",
    "COLORBURN": "OUTLINER_OB_LIGHT",
    "LINEARBURN": "MESH_LINE",
    "LIGHTEN": "PAINT_LIGHTEN",
    "SCREEN": "SPLITSCREEN",
    "COLORDODGE": "PAINT_MIX",
    "ADD": "PAINT_ADD",
    "OVERLAY": "OVERLAY",
    "SOFTLIGHT": "NODE_LIGHTFALLOFF",
    "VIVIDLIGHT": "LIGHT_SIZE",
    "HARDLIGHT": "LIGHT_POINT",
    "LINEARLIGHT": "LIGHT_STRENGTH",
    "PINLIGHT": "NODE_LIGHTPATH",
    "DIFFERENCE": "MOD_BOOLEAN",
    "EXCLUSION": "BOOLEAN_MATH",
    "SUB": "PAINT_SUBTRACT",
    "HUE": "NODE_HUESATURATION",
    "COLOR": "COLOR",
    "LUMINOSITY": "NODE_LUMINANCE",
    "ERASE_ALPHA": "IMAGE_RGB_ALPHA",
    "ADD_ALPHA": "SEQ_ALPHA_OVER",
    "BLUR": "PAINT_BLUR",
    "SATURATION": "COLOR_SPACE",
}


DEFAULT_ICON_FOR_IDNAME = {
    "AVERAGE": "PAINT_AVERAGE",
    "SMEAR": "PAINT_SMEAR",
    "DRAW": "PAINT_DRAW",
    "BLUR": "PAINT_BLUR",
}

_icon_cache = dict()

# Copied as is from BFA/Blender toolsystem
# release\scripts\startup\bl_ui\space_toolsystem_common.py
def _icon_value_from_icon_handle(icon_name):
    if icon_name is not None:
        assert type(icon_name) is str
        icon_value = _icon_cache.get(icon_name)
        if icon_value is None:
            dirname = bpy.utils.system_resource("DATAFILES", path="icons")
            filename = os.path.join(dirname, icon_name + ".dat")
            try:
                icon_value = bpy.app.icons.new_triangles_from_file(filename)
            except Exception as ex:
                if not os.path.exists(filename):
                    print("Missing icons:", filename, ex)
                else:
                    print("Corrupt icon:", filename, ex)
                # Use none as a fallback (avoids layout issues).
                if icon_name != "none":
                    icon_value = _icon_value_from_icon_handle("none")
                else:
                    icon_value = 0
            _icon_cache[icon_name] = icon_value
        return icon_value
    else:
        return 0


def get_weight_brush_icon(weight_brush: bpy.types.Brush):
    # Values should match toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_toolbar.py
    icon_prefix = "brush.paint_weight."
    idname = weight_brush.weight_tool
    print("Loading brush icon", weight_brush, idname)
    icon = icon_prefix + idname.lower()
    #if idname in DEFAULT_ICON_FOR_IDNAME:
    #        return DEFAULT_ICON_FOR_IDNAME[idname]
    return _icon_value_from_icon_handle(icon)


# Some Brush code
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


# Get the weight brushes and list them with the default icon if it doesn't have custom icons.
def get_weight_brushes_buttons():
    buttons: Dict[str, List[WeightBrushButton]] = defaultdict(list)
    brush: bpy.types.Brush
    for brush in sorted(bpy.data.brushes, key=lambda b: b.name):
        if not brush.use_paint_weight:
            continue
        # brush name, icon
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
            # Assign the icons by dictionary here
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


# Used to set the weight brushes
class BFA_OT_set_brush(bpy.types.Operator):
    bl_label = "Set Brush"
    bl_idname = "bfa.set_brush"
    bl_options = {"UNDO"}

    paint_settings_attr_name: bpy.props.StringProperty()
    brush_name: bpy.props.StringProperty()

    def execute(self, context):
        paint_settings = getattr(context.tool_settings, self.paint_settings_attr_name)
        paint_settings.brush = bpy.data.brushes[self.brush_name]
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        return properties.brush_name


## From BFA space_toolbar_tabs
def column_count(region: bpy.types.Region):
    """
    Choose an appropriate layout for the toolbar.
    """
    # Currently this just checks the width,
    # we could have different layouts as preferences too.
    system = bpy.context.preferences.system
    view2d = region.view2d
    view2d_scale = view2d.region_to_view(1.0, 0.0)[0] - view2d.region_to_view(0.0, 0.0)[0]
    width_scale = region.width * view2d_scale / system.ui_scale

    # how many rows. 4 is text buttons.

    if width_scale > 160.0:
        column_count = 4
    elif width_scale > 120.0:
        column_count = 3
    elif width_scale > 80:
        column_count = 2
    else:
        column_count = 1

    return column_count


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
        buttons = get_weight_brushes_buttons()

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
        buttons = get_weight_brushes_buttons()

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
        buttons = get_weight_brushes_buttons()

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
        buttons = get_weight_brushes_buttons()

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
    bpy.utils.register_class(BFA_OT_set_brush)
    bpy.utils.register_class(BFA_PT_brush_weight)
    bpy.utils.register_class(BFA_PT_brush_weight_smear)
    bpy.utils.register_class(BFA_PT_brush_weight_average)
    bpy.utils.register_class(BFA_PT_brush_weight_blur)


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    bpy.utils.unregister_class(BFA_OT_set_brush)
    bpy.utils.unregister_class(BFA_PT_brush_weight)
    bpy.utils.unregister_class(BFA_PT_brush_weight_smear)
    bpy.utils.unregister_class(BFA_PT_brush_weight_average)
    bpy.utils.unregister_class(BFA_PT_brush_weight_blur)
