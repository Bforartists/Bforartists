# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Copy Render Settings",
    "author": "Bastien Montagne",
    "version": (1, 2, 0),
    "blender": (3, 6, 0),
    "location": "Render buttons (Properties window)",
    "description": "Allows to copy a selection of render settings "
                   "from current scene to others.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/render/copy_settings.html",
    "category": "Render",
}


if "bpy" in locals():
    import importlib
    importlib.reload(data)
    importlib.reload(operator)
    importlib.reload(panel)
    importlib.reload(translations)

else:
    from . import (
        data,
        operator,
        panel,
        translations,
    )


import bpy
from bpy.props import (
    PointerProperty,
)


classes = data.classes + operator.classes + panel.classes


def scene_render_copy_settings_timer():
    operator.scene_render_copy_settings_update()
    return 1.0  # Run every second.


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_copy_settings = PointerProperty(type=data.RenderCopySettingsData)

    bpy.app.translations.register(__name__, translations.translations_dict)

    bpy.app.timers.register(scene_render_copy_settings_timer, persistent=True)


def unregister():
    bpy.app.timers.unregister(scene_render_copy_settings_timer)

    bpy.app.translations.unregister(__name__)

    del bpy.types.Scene.render_copy_settings
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
