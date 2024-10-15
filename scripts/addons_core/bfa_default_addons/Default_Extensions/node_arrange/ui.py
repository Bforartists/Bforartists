# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Context, Panel
from bpy.utils import register_class, unregister_class


class NA_PT_Panel(Panel):
    bl_label = "Node Arrange"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Arrange"

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.use_property_split = True

        scene = context.scene
        settings = scene.na_settings

        layout.operator("node.na_arrange_selected")

        layout.prop(settings, "margin")


classes = [NA_PT_Panel]


def register() -> None:
    for cls in classes:
        register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        if cls.is_registered:
            unregister_class(cls)
