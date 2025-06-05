import os
from dataclasses import dataclass
from typing import Callable, Dict, Union

import bpy
import bpy.utils.previews

DEFAULT_ICON_FOR_BLEND_MODE = {
    # "MIX": "PAINT_DRAW", # This currently overrides all other brush defaults since the other brushes default to "Mix".
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


DEFAULT_ICON_FOR_TOOLNAME = {
    "AVERAGE": "PAINT_AVERAGE", ### General brushes
    "SMEAR": "PAINT_SMEAR",
    "DRAW": "PAINT_DRAW",
    "BLUR": "PAINT_BLUR",
    "MASK": "MOD_MASK",
    "CLONE": "PAINT_DRAW",
    "SOFTEN": "PAINT_DRAW",
    "FILL": "PAINT_DRAW",
    "TINT": "PAINT_DRAW",
    "DRAW": "PAINT_DRAW", ### Draw Sculpt Brushes
    "DRAW_SHARP": "PAINT_DRAW",
    "CLAY": "PAINT_DRAW",
    "CLAY_STRIPS": "PAINT_DRAW",
    "CLAY_THUMB": "PAINT_DRAW",
    "LAYER": "PAINT_DRAW",
    "INFLATE": "PAINT_DRAW",
    "BLOB": "PAINT_DRAW",
    "CREASE": "PAINT_DRAW",
    "SMOOTH": "PAINT_DRAW", ### Surface Sculpt Brushes
    "FLATTEN": "PAINT_DRAW",
    "FILL": "FLOODFILL",
    "SCRAPE": "PAINT_DRAW",
    "MULTIPLANE_SCRAPE": "PAINT_DRAW",
    "PINCH": "PAINT_DRAW",
    "GRAB" : "PAINT_DRAW", ### Deform Sculpt Brushes
    "ELASTIC_DEFORM" : "PAINT_DRAW",
    "SNAKE_HOOK" : "PAINT_DRAW",
    "THUMB" : "PAINT_DRAW",
    "POSE" : "PAINT_DRAW",
    "NUDGE" : "PAINT_DRAW",
    "ROTATE" : "PAINT_DRAW",
    "TOPOLOGY" : "PAINT_DRAW",
    "BOUNDARY" : "PAINT_DRAW",
    "CLOTH" : "PAINT_DRAW", ### Misc Sculpt Brushes
    "SIMPLIFY" : "PAINT_DRAW",
    "MASK": "MOD_MASK",
    "DRAW_FACE_SETS": "PAINT_DRAW",
    "DISPLACEMENT_ERASER": "PAINT_DRAW",
    "DISPLACEMENT_SMEAR": "PAINT_DRAW",
    "PAINT": "PAINT_DRAW",
}


DEFAULT_ICON_FOR_GP_DRAW = {
    "PENCIL": "PAINT_DRAW",
    "PEN": "PAINT_DRAW",
    "INK": "PAINT_DRAW",
    "INKNOISE": "PAINT_DRAW",
    "BLOCK": "PAINT_DRAW",
    "MARKER": "PAINT_DRAW",
    "AIRBRUSH": "PAINT_DRAW",
    "CHISEL": "PAINT_DRAW",
    "FILL": "PAINT_DRAW",
    "SOFT": "PAINT_DRAW",
    "HARD": "PAINT_DRAW",
    "STROKE": "PAINT_DRAW",
}


__icon_cache = dict()

# Custom Image Previews
preview_collections: Dict[
    str,
    Union[bpy.utils.previews.ImagePreviewCollection, Dict[str, bpy.types.ImagePreview]],
] = {}


@dataclass
class BrushIcon:
    icon_name: str
    icon_value: int


def _icon_value_from_icon_name(icon_name):
    # Based on BFA/Blender toolsystem
    # release\scripts\startup\bl_ui\space_toolsystem_common.py
    icon_value = __icon_cache.get(icon_name, None)
    if icon_value is not None:
        return __icon_cache[icon_name]

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
            icon_value = _icon_value_from_icon_name("none")
        else:
            icon_value = 0
    __icon_cache[icon_name] = icon_value
    return icon_value


def get_brush_icon(
    brush: bpy.types.Brush,
    icon_name_from_brush: Callable[[bpy.types.Brush], str],
    tool_name_from_brush: Callable[[bpy.types.Brush], str],
):
    if "main" not in preview_collections:
        pcoll = bpy.utils.previews.new()
        preview_collections["main"] = pcoll

    # Custom Icon code, so that it override any default icon
    if brush.use_custom_icon and brush.icon_filepath:
        pcoll = preview_collections["main"]
        filepath = os.path.abspath(bpy.path.abspath(brush.icon_filepath))
        try:
            preview = pcoll.load(filepath, filepath, "IMAGE")
        except KeyError:
            # Blender API raises KeyError if image is already in the collection
            preview = pcoll[filepath]

        return BrushIcon("NONE", preview.icon_id)

    if brush.blend == "MIX":
        icon_name = DEFAULT_ICON_FOR_TOOLNAME.get(tool_name_from_brush(brush), None)
        # Check if the attribute gpencil_tool exists, if not, carry on.
        try:
            if brush.gpencil_tool == "TINT":
                icon_name = DEFAULT_ICON_FOR_TOOLNAME.get(tool_name_from_brush(brush), None)
            else:
                icon_name = DEFAULT_ICON_FOR_GP_DRAW.get(brush.gpencil_settings.gpencil_paint_icon, None)
        except AttributeError:
            pass
    else:
        icon_name = DEFAULT_ICON_FOR_BLEND_MODE.get(brush.blend, None)

    ##### Vertex Paint, Texture Paint and Weight Paint icons based on blend type
    # Override default by blend type if it's not mix.
    # This works by checking if mix blend is on, if not, it will go normal.
    # This is applicable for Weight Paint, Vertex Paint and Texture Paint modes.

    # if brush.blend == "MIX":
    #    icon_name = DEFAULT_ICON_FOR_TOOLNAME.get(tool_name_from_brush(brush), None)
    # else:
    #    icon_name = DEFAULT_ICON_FOR_BLEND_MODE.get(brush.blend, None)

    ##### Grease Pencil Icons based on icon type
    # Override the greae pencil brushes, base code.

    # if brush.gpencil_tool == "TINT":
    #    icon_name = DEFAULT_ICON_FOR_TOOLNAME.get(tool_name_from_brush(brush), None)
    # else:
    #    icon_name = DEFAULT_ICON_FOR_GP_DRAW.get(brush.gpencil_settings.gpencil_paint_icon, None)

    # Take 02 - fusion the systems with an attempt to detect grease pencil brushes and iconize them correctly.
    # This may be revised for later.

    if icon_name is not None:
        return BrushIcon(icon_name, 0)

    icon_name = icon_name_from_brush(brush)
    return BrushIcon("NONE", _icon_value_from_icon_name(icon_name))


def register():
    pass


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
