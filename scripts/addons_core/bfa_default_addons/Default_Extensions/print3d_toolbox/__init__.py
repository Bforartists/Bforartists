# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2024 Campbell Barton
# SPDX-FileCopyrightText: 2016-2026 Mikhail Rachinskiy


if "bpy" in locals():
    from pathlib import Path
    essentials.reload_recursive(Path(__file__).parent, locals())
else:
    import bpy
    from bpy.props import PointerProperty

    from . import essentials, localization, operators, preferences, ui


classes = essentials.get_classes((operators, preferences, ui))


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.print3d_toolbox = PointerProperty(type=preferences.SceneProperties)

    # Menu
    # ---------------------------

    bpy.types.VIEW3D_MT_object.append(ui.draw_print3d_menu)
    bpy.types.VIEW3D_MT_edit_mesh.append(ui.draw_print3d_menu)

    # Translations
    # ---------------------------

    bpy.app.translations.register(__package__, localization.DICTIONARY)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.print3d_toolbox

    # Menu
    # ---------------------------

    bpy.types.VIEW3D_MT_object.remove(ui.draw_print3d_menu)
    bpy.types.VIEW3D_MT_edit_mesh.remove(ui.draw_print3d_menu)

    # Translations
    # ---------------------------

    bpy.app.translations.unregister(__package__)
