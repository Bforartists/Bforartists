import os

import bpy


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


DEFAULT_ICON_FOR_IDNAME = {
    "AVERAGE": "PAINT_AVERAGE",
    "SMEAR": "PAINT_SMEAR",
    "DRAW": "PAINT_DRAW",
    "BLUR": "PAINT_BLUR",
}

__icon_cache = dict()


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
