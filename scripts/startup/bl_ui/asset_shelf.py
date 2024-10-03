# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import (
    Operator,
    Panel,
)

from bpy.props import EnumProperty


# BFA - Preset sizes for asset shelf thumbnails
thumbnail_sizes = {
    "TINY" : 48,
    "SMALL" : 96,
    "MEDIUM" : 128,
    "LARGE" : 256,
}

# BFA - Preset sizes and their corresponding UI labels
thumbnail_size_labels = tuple((item, item.title(), "") for item in thumbnail_sizes)


class ASSETSHELF_OT_change_thumbnail_size(Operator):
    bl_label = "Change Thumbnail Size"
    bl_idname = "asset_shelf.change_thumbnail_size"
    bl_description = "Change the size of thumbnails in discrete steps"
   
    size : EnumProperty(
        name="Thumbnail Size",
        description="Change the size of thumbnails in discrete steps",
        default="TINY",
        items=thumbnail_size_labels
    )

    def execute(self, context):
        shelf = context.asset_shelf
        shelf.preview_size = thumbnail_sizes[self.size]

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.asset_shelf is not None


class ASSETSHELF_PT_display(Panel):
    bl_label = "Display Settings"
    # Doesn't actually matter. Panel is instanced through popover only.
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        shelf = context.asset_shelf
        
        # BFA - Thumbnail preset buttons
        row = layout.row(align=True)
        row.context_pointer_set("asset_shelf", shelf)
        # BFA - operator_menu_enum doesn't seem to support horizontal button layout 
        # in popover panels, so the buttons are created one-by-one instead
        for value, label, _description in thumbnail_size_labels:
            row.operator("asset_shelf.change_thumbnail_size", text=label).size = value

        layout.prop(shelf, "preview_size", text="Size")
        layout.use_property_split = False
        layout.prop(shelf, "show_names", text="Names")

    @classmethod
    def poll(cls, context):
        return context.asset_shelf is not None


classes = (
    ASSETSHELF_PT_display,
    ASSETSHELF_OT_change_thumbnail_size
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
