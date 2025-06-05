# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import io, platform, struct, urllib, json
from pathlib import Path
from collections import defaultdict

import bpy
from bpy.types import AddonPreferences, Operator
from bpy.props import BoolProperty
from bl_ui.space_userpref import USERPREF_PT_interface_menus_pie

from .hotkeys import (
    get_sidebar,
    draw_hotkey_list,
    PIE_ADDON_KEYMAPS,
    get_user_kmis_of_addon,
    get_user_kmi_of_addon,
    refresh_all_kmis,
    print_kmi,
)
from . import __package__ as base_package
from . import bl_info_copy


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context

    addons = context.preferences.addons
    if base_package.startswith('bl_ext'):
        # 4.2 and later
        name = base_package
    else:
        # Pre-4.2
        name = base_package.split(".")[0]

    if name in addons:
        prefs = addons[name].preferences
        if prefs == None:
            print("This happens when packaging the extension, due to the registration delay.")
        return addons[name].preferences


def update_prefs_on_file(self=None, context=None) -> tuple[str, dict]:
    prefs = get_addon_prefs(context)
    if not prefs:
        return
    if not type(prefs).loading:
        filepath, data = prefs.save_prefs_to_file()
        return filepath, data
    return "", {}


class PrefsFileSaveLoadMixin:
    """Mix-in class that can be used by any add-on to store their preferences in a file,
    so that they don't get lost when the add-on is disabled.
    To use it, copy this class and the two functions above it, and do this in your code:

    ```
    import bpy, json
    from pathlib import Path

    class MyAddonPrefs(PrefsFileSaveLoadMixin, bpy.types.AddonPreferences):
        some_prop: bpy.props.IntProperty(update=update_prefs_on_file)

    def register():
        bpy.utils.register_class(MyAddonPrefs)
        MyAddonPrefs.register_autoload_from_file()
    ```

    """

    loading = False

    @staticmethod
    def register_autoload_from_file(delay=0.0):
        def timer_func(_scene=None):
            kc = bpy.context.window_manager.keyconfigs
            areas = 'Window', 'Text', 'Object Mode', '3D View'
            if not all(i in kc.active.keymaps for i in areas):
                print("3D Viewport Pie Menus: Keymaps aren't ready yet, waiting a sec...")
                return 1
            prefs = get_addon_prefs()
            if not prefs:
                return 1
            prefs.load_prefs_from_file()
        bpy.app.timers.register(timer_func, first_interval=delay)

    def prefs_to_dict_recursive(self, propgroup: 'IDPropertyGroup') -> dict:
        """Recursively convert AddonPreferences to a dictionary.
        Note that AddonPreferences don't support PointerProperties,
        so this function doesn't either."""
        from rna_prop_ui import IDPropertyGroup

        ret = {}

        if hasattr(propgroup, 'bl_rna'):
            rna_class = propgroup.bl_rna
        else:
            property_group_class_name = type(propgroup).__name__
            rna_class = bpy.types.PropertyGroup.bl_rna_get_subclass_py(
                property_group_class_name
            )

        for key, value in propgroup.items():
            if type(value) == list:
                ret[key] = [self.prefs_to_dict_recursive(elem) for elem in value]
            elif type(value) == IDPropertyGroup:
                ret[key] = self.prefs_to_dict_recursive(value)
            else:
                if (
                    rna_class
                    and key in rna_class.properties
                    and hasattr(rna_class.properties[key], 'enum_items')
                ):
                    # Save enum values as string, not int.
                    ret[key] = rna_class.properties[key].enum_items[value].identifier
                else:
                    ret[key] = value
        return ret

    def apply_prefs_from_dict_recursive(self, propgroup, data):
        for key, value in data.items():
            if not hasattr(propgroup, key):
                # Property got removed or renamed in the implementation.
                continue
            if type(value) == list:
                for elem in value:
                    collprop = getattr(propgroup, key)
                    entry = collprop.get(elem['name'])
                    if not entry:
                        entry = collprop.add()
                    self.apply_prefs_from_dict_recursive(entry, elem)
            elif type(value) == dict:
                self.apply_prefs_from_dict_recursive(getattr(propgroup, key), value)
            else:
                setattr(propgroup, key, value)

    @staticmethod
    def get_prefs_filepath() -> Path:
        addon_name = __package__.split(".")[-1]
        return Path(bpy.utils.user_resource('CONFIG')) / Path(addon_name + ".txt")

    def save_prefs_to_file(self, _context=None):
        data_dict = self.prefs_to_dict_recursive(propgroup=self)

        filepath = self.get_prefs_filepath()

        with open(filepath, "w") as f:
            json.dump(data_dict, f, indent=4)

        return filepath, json.dumps(data_dict, indent=4)

    def load_prefs_from_file(self) -> bool:
        filepath = self.get_prefs_filepath()
        if not filepath.exists():
            return False

        success = True
        with open(filepath, "r") as f:
            addon_data = json.load(f)
            type(self).loading = True
            try:
                if 'hotkeys' in addon_data:
                    hotkeys = addon_data.pop("hotkeys")
                    if type(hotkeys) == dict:
                        # Pre-1.6.8 code, with the keymap hash system.
                        if not(self.apply_hotkeys_pre_v168(hotkeys)):
                            success = False
                    else:
                        # v1.6.8 and beyond.
                        for hotkey in hotkeys:
                            op_kwargs = {}
                            if 'name' in hotkey['op_kwargs']:
                                op_kwargs['name'] = hotkey['op_kwargs']['name']
                            _user_km, user_kmi = get_user_kmi_of_addon(bpy.context, hotkey['keymap'], hotkey['operator'], op_kwargs)
                            if not user_kmi:
                                print("Failed to apply Keymap: ", hotkey['keymap'], hotkey['operator'], op_kwargs)
                                success = False
                                continue
                            op_kwargs = hotkey.pop('op_kwargs')
                            for key, value in op_kwargs.items():
                                setattr(user_kmi.properties, key, value)
                            for key, value in hotkey['key_kwargs'].items():
                                if key == "any" and not value:
                                    continue
                                setattr(user_kmi, key, value)
                self.apply_prefs_from_dict_recursive(self, addon_data)
                refresh_all_kmis()
            except Exception as exc:
                # If we get an error raised here, and it isn't handled,
                # the add-on seems to break.
                print(
                    f"{base_package}: Failed to load {__package__} preferences from file."
                )
                raise exc
            type(self).loading = False
        return success


class ExtraPies_AddonPrefs(
    PrefsFileSaveLoadMixin,
    AddonPreferences,
    USERPREF_PT_interface_menus_pie, # We use this class's `draw_centered` function to draw built-in pie settings.
):
    bl_idname = __package__

    show_in_sidebar: BoolProperty(
        name="Show in Sidebar",
        default=False,
        description="Show a compact version of the preferences in the sidebar. Useful when picking up the add-on for the first time to learn and customize it to your liking",
    )

    def draw(self, context):
        draw_prefs(self.layout, context, compact=False)

    def prefs_to_dict_recursive(self, propgroup: 'IDPropertyGroup') -> dict:
        ret = super().prefs_to_dict_recursive(propgroup)

        all_keymap_data = []
        for user_km, user_kmi in get_user_kmis_of_addon(bpy.context):
            data = {}
            data['keymap'] = user_km.name
            data['operator'] = user_kmi.idname

            NO_SAVE_OP_KWARGS = ('fallback_operator', 'fallback_op_kwargs')

            op_kwargs = {}
            if user_kmi.properties:
                op_kwargs = {
                    key: getattr(user_kmi.properties, key)
                    for key in user_kmi.properties.keys()
                    if hasattr(user_kmi.properties, key) and key not in NO_SAVE_OP_KWARGS
                }

            data['op_kwargs'] = op_kwargs

            data['key_kwargs'] = {
                'type' : user_kmi.type,
                'value' : user_kmi.value,
                'ctrl' : bool(user_kmi.ctrl),
                'shift' : bool(user_kmi.shift),
                'alt' : bool(user_kmi.alt),
                'any' : bool(user_kmi.any),
                'oskey' : bool(user_kmi.oskey),
                'key_modifier' : user_kmi.key_modifier,
                'active' : user_kmi.active
            }

            all_keymap_data.append(data)

        ret["hotkeys"] = all_keymap_data

        return ret



    def apply_hotkeys_pre_v168(self, hotkeys):
        """Best effort to read the old, hash-based keymap storage format. 
        This caused issues so it had to be re-worked, and versioned."""

        context = bpy.context

        complete_success = True

        for _kmi_hash, kmi_props in hotkeys.items():
            if 'key_cat' in kmi_props:
                keymap_name = kmi_props.pop('key_cat')

            op_kwargs = {}
            if 'name' in kmi_props['properties']:
                op_kwargs['name'] = kmi_props['properties']['name']

            idname = kmi_props['idname']
            if idname in ('wm.call_menu_pie', 'wm.call_menu_pie_wrapper'):
                idname = 'wm.call_menu_pie_drag_only'

            _user_km, user_kmi = get_user_kmi_of_addon(context, keymap_name, idname, op_kwargs)
            if not user_kmi:
                complete_success = False
                # print("No such user KeymapItem: ", keymap_name, idname, op_kwargs)
                continue

            if "properties" in kmi_props:
                op_kwargs = kmi_props.pop("properties")
                for key, value in op_kwargs.items():
                    if hasattr(user_kmi.properties, key):
                        setattr(user_kmi.properties, key, value)

            for key, value in kmi_props.items():
                if key == "any" and not value:
                    continue
                if key == "name":
                    continue
                if key == "idname":
                    continue
                try:
                    setattr(user_kmi, key, value)
                except:
                    # print("Failed to load keymap item:")
                    # print_kmi(user_kmi)
                    pass

        return complete_success



def draw_prefs(layout, context, compact=False):
    prefs = get_addon_prefs(context)

    sidebar = get_sidebar(context)
    if sidebar:
        compact = sidebar.width < 600

    layout.use_property_split = True
    layout.use_property_decorate = False

    if not compact:
        layout.operator('wm.url_open', text="Report Bug", icon='URL').url = (
            get_bug_report_url()
        )
        layout.prop(prefs, 'show_in_sidebar')

    header, builtins_panel = layout.panel(idname="Extra Pies Builtin Prefs")
    header.label(text="Pie Preferences")
    if builtins_panel:
        prefs.draw_centered(context, layout)

    if not sidebar:
        # In the Preferences UI, still draw compact hotkeys list if the window is quite small.
        compact = context.area.width < 600
    header, hotkeys_panel = layout.panel(idname="Extra Pies Hotkeys")
    header.label(text="Hotkeys")
    if hotkeys_panel:
        draw_hotkey_list(hotkeys_panel, context, compact=compact)


def get_bug_report_url(stack_trace=""):
    fh = io.StringIO()

    fh.write("CC @Mets\n\n")
    fh.write("**System Information**\n")
    fh.write(
        "Operating system: %s %d Bits\n"
        % (
            platform.platform(),
            struct.calcsize("P") * 8,
        )
    )
    fh.write("\n" "**Blender Version:** ")
    fh.write(
        "%s, branch: %s, commit: [%s](https://projects.blender.org/blender/blender/commit/%s)\n"
        % (
            bpy.app.version_string,
            bpy.app.build_branch.decode('utf-8', 'replace'),
            bpy.app.build_commit_date.decode('utf-8', 'replace'),
            bpy.app.build_hash.decode('ascii'),
        )
    )

    addon_version = bl_info_copy['version']
    fh.write(f"**Add-on Version**: {addon_version}\n")

    if stack_trace != "":
        fh.write("\nStack trace\n```\n" + stack_trace + "\n```\n")

    fh.write("\n" "---")

    fh.write("\n" "Description of the problem:\n" "\n")

    fh.seek(0)

    return (
        "https://projects.blender.org/extensions/space_view3d_pie_menus/issues/new?template=.gitea/issue_template/bug.yaml&field:body="
        + urllib.parse.quote(fh.read())
    )


class WINDOW_OT_extra_pies_prefs_save(Operator):
    """Save Extra Pies add-on preferences"""

    bl_idname = "window.extra_pies_prefs_save"
    bl_label = "Save Pie Hotkeys"
    bl_options = {'REGISTER'}

    def execute(self, context):
        filepath, data = update_prefs_on_file(context)
        self.report({'INFO'}, f"Saved Pie Prefs to {filepath}.")
        return {'FINISHED'}


class WINDOW_OT_extra_pies_prefs_load(Operator):
    """Load Extra Pies add-on preferences"""

    bl_idname = "window.extra_pies_prefs_load"
    bl_label = "Load Pie Hotkeys"
    bl_options = {'REGISTER'}

    def execute(self, context):
        prefs = get_addon_prefs(context)
        filepath = prefs.get_prefs_filepath()
        success = prefs.load_prefs_from_file()

        if success:
            self.report({'INFO'}, f"Loaded pie preferences from {filepath}.")
        else:
            self.report({'ERROR'}, "Failed to load Pie preferences.")

        return {'FINISHED'}


registry = [
    ExtraPies_AddonPrefs,
    WINDOW_OT_extra_pies_prefs_save,
    WINDOW_OT_extra_pies_prefs_load,
]


def register():
    ExtraPies_AddonPrefs.register_autoload_from_file()
