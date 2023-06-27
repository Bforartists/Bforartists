# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Contributed to by meta-androcto, pitiwazou, chromoly, italic, kc98

import bpy
from bpy.props import (
    BoolProperty,
    PointerProperty,
)
from bpy.types import (
    PropertyGroup,
    AddonPreferences,
)


bl_info = {
    "name": "3D Viewport Pie Menus",
    "author": "meta-androcto",
    "version": (1, 3, 0),
    "blender": (2, 80, 0),
    "description": "Pie Menu Activation",
    "location": "Addons Preferences",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/viewport_pies.html",
    "category": "Interface"
}

sub_modules_names = (
    "pie_modes_menu",
    "pie_views_numpad_menu",
    "pie_sculpt_menu",
    "pie_origin",
    "pie_manipulator_menu",
    "pie_shading_menu",
    "pie_align_menu",
    "pie_delete_menu",
    "pie_apply_transform_menu",
    "pie_select_menu",
    "pie_animation_menu",
    "pie_save_open_menu",
    "pie_editor_switch_menu",
    "pie_defaults_menu",
    "pie_proportional_menu",
)


sub_modules = [__import__(__package__ + "." + submod, {}, {}, submod) for submod in sub_modules_names]
sub_modules.sort(key=lambda mod: (mod.bl_info['category'], mod.bl_info['name']))


def _get_pref_class(mod):
    import inspect

    for obj in vars(mod).values():
        if inspect.isclass(obj) and issubclass(obj, PropertyGroup):
            if hasattr(obj, 'bl_idname') and obj.bl_idname == mod.__name__:
                return obj


def get_addon_preferences(name=''):
    """Acquisition and registration"""
    addons = bpy.context.preferences.addons
    if __name__ not in addons:  # wm.read_factory_settings()
        return None
    addon_prefs = addons[__name__].preferences
    if name:
        if not hasattr(addon_prefs, name):
            for mod in sub_modules:
                if mod.__name__.split('.')[-1] == name:
                    cls = _get_pref_class(mod)
                    if cls:
                        prop = PointerProperty(type=cls)
                        create_property(PIEToolsPreferences, name, prop)
                        bpy.utils.unregister_class(PIEToolsPreferences)
                        bpy.utils.register_class(PIEToolsPreferences)
        return getattr(addon_prefs, name, None)
    else:
        return addon_prefs


def create_property(cls, name, prop):
    if not hasattr(cls, '__annotations__'):
        cls.__annotations__ = dict()
    cls.__annotations__[name] = prop


def register_submodule(mod):
    mod.register()
    mod.__addon_enabled__ = True


def unregister_submodule(mod):
    if mod.__addon_enabled__:
        mod.unregister()
        mod.__addon_enabled__ = False

        prefs = get_addon_preferences()
        name = mod.__name__.split('.')[-1]
        if hasattr(PIEToolsPreferences, name):
            delattr(PIEToolsPreferences, name)
            if prefs:
                bpy.utils.unregister_class(PIEToolsPreferences)
                bpy.utils.register_class(PIEToolsPreferences)
                if name in prefs:
                    del prefs[name]


class PIEToolsPreferences(AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout

        for mod in sub_modules:
            mod_name = mod.__name__.split('.')[-1]
            info = mod.bl_info
            column = layout.column()
            box = column.box()

            # first stage
            expand = getattr(self, 'show_expanded_' + mod_name)
            icon = 'TRIA_DOWN' if expand else 'TRIA_RIGHT'
            col = box.column()
            row = col.row()
            sub = row.row()
            sub.context_pointer_set('addon_prefs', self)
            op = sub.operator('wm.context_toggle', text='', icon=icon,
                              emboss=False)
            op.data_path = 'addon_prefs.show_expanded_' + mod_name
            sub.label(text='{}: {}'.format(info['category'], info['name']))
            sub = row.row()
            sub.alignment = 'RIGHT'
            if info.get('warning'):
                sub.label(text='', icon='ERROR')
            sub.prop(self, 'use_' + mod_name, text='')

            # The second stage
            if expand:
                if info.get('description'):
                    split = col.row().split(factor=0.15)
                    split.label(text='Description:')
                    split.label(text=info['description'])
                if info.get('location'):
                    split = col.row().split(factor=0.15)
                    split.label(text='Location:')
                    split.label(text=info['location'])
                """
                if info.get('author'):
                    split = col.row().split(factor=0.15)
                    split.label(text='Author:')
                    split.label(text=info['author'])
                """
                if info.get('version'):
                    split = col.row().split(factor=0.15)
                    split.label(text='Version:')
                    split.label(text='.'.join(str(x) for x in info['version']),
                                translate=False)
                if info.get('warning'):
                    split = col.row().split(factor=0.15)
                    split.label(text='Warning:')
                    split.label(text='  ' + info['warning'], icon='ERROR')

                tot_row = int(bool(info.get('doc_url')))
                if tot_row:
                    split = col.row().split(factor=0.15)
                    split.label(text='Internet:')
                    if info.get('doc_url'):
                        op = split.operator('wm.url_open',
                                            text='Documentation', icon='HELP')
                        op.url = info.get('doc_url')
                    for i in range(4 - tot_row):
                        split.separator()

                # Details and settings
                if getattr(self, 'use_' + mod_name):
                    prefs = get_addon_preferences(mod_name)

                    if prefs and hasattr(prefs, 'draw'):
                        box = box.column()
                        prefs.layout = box
                        try:
                            prefs.draw(context)
                        except:
                            import traceback
                            traceback.print_exc()
                            box.label(text='Error (see console)', icon='ERROR')
                        del prefs.layout

        row = layout.row()
        row.label(text="End of Pie Menu Activations", icon="FILE_PARENT")


for mod in sub_modules:
    info = mod.bl_info
    mod_name = mod.__name__.split('.')[-1]

    def gen_update(mod):
        def update(self, context):
            enabled = getattr(self, 'use_' + mod.__name__.split('.')[-1])
            if enabled:
                register_submodule(mod)
            else:
                unregister_submodule(mod)
            mod.__addon_enabled__ = enabled
        return update

    create_property(
        PIEToolsPreferences,
        'use_' + mod_name,
        BoolProperty(
            name=info['name'],
            description=info.get('description', ''),
            update=gen_update(mod),
            default=True,
        ))

    create_property(
        PIEToolsPreferences,
        'show_expanded_' + mod_name,
        BoolProperty())


classes = (
    PIEToolsPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    prefs = get_addon_preferences()
    for mod in sub_modules:
        if not hasattr(mod, '__addon_enabled__'):
            mod.__addon_enabled__ = False
        name = mod.__name__.split('.')[-1]
        if getattr(prefs, 'use_' + name):
            register_submodule(mod)


def unregister():
    for mod in sub_modules:
        if mod.__addon_enabled__:
            unregister_submodule(mod)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
