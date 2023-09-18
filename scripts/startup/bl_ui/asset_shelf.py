# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
    Panel,
)


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

        layout.prop(shelf, "preview_size", text="Size")
        layout.prop(shelf, "show_names", text="Names")

    @classmethod
    def poll(cls, context):
        return context.asset_shelf is not None


classes = (
    ASSETSHELF_PT_display,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
