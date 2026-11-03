import bpy
import os
import bpy.utils.previews


#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_custom_icon(icon_name: str):
    """Returns the ID of a custom icon registered by add-on."""

    svg_icons = preview_collections["main"]
    if not svg_icons:
        return 0

    icon = svg_icons[icon_name].icon_id
    if not icon:
        return 0

    return icon



#### ------------------------------ REGISTRATION ------------------------------ ####

preview_collections = {}
svg_icons_dir = os.path.join(os.path.dirname(__file__), "svg")

icons = {
    "MEASURE": "measure.svg",
    "CPU": "cpu.svg",
}


def register():
    svg_icons = bpy.utils.previews.new()

    for key, file in icons.items():
        svg_icons.load(key, os.path.join(svg_icons_dir, file), 'IMAGE')

    preview_collections["main"] = svg_icons


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
