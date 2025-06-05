# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, json
import io, platform, struct, urllib
from pathlib import Path
from bpy.types import AddonPreferences
from bpy.props import BoolProperty
from bl_ui.space_userpref import USERPREF_PT_interface_menus_pie
from .hotkeys import draw_hotkey_list, PIE_ADDON_KEYMAPS, find_kmi_in_km_by_hash, print_kmi, get_kmi_ui_info
from . import __package__ as base_package
from . import bl_info_copy


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


def update_prefs_on_file(self=None, context=None):
    prefs = get_addon_prefs(context)
    if not type(prefs).loading:
        prefs.save_prefs_to_file()


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
    def register_autoload_from_file(delay=0.5):
        def timer_func(_scene=None):
            prefs = get_addon_prefs()
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
            rna_class = bpy.types.PropertyGroup.bl_rna_get_subclass_py(property_group_class_name)

        for key, value in propgroup.items():
            if type(value) == list:
                ret[key] = [self.prefs_to_dict_recursive(elem) for elem in value]
            elif type(value) == IDPropertyGroup:
                ret[key] = self.prefs_to_dict_recursive(value)
            else:
                if (
                    rna_class and 
                    key in rna_class.properties and 
                    hasattr(rna_class.properties[key], 'enum_items')
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

        with open(self.get_prefs_filepath(), "w") as f:
            json.dump(data_dict, f, indent=4)

    def load_prefs_from_file(self):
        filepath = self.get_prefs_filepath()
        if not filepath.exists():
            return

        with open(filepath, "r") as f:
            addon_data = json.load(f)
            type(self).loading = True
            try:
                self.apply_prefs_from_dict_recursive(self, addon_data)
            except Exception as exc:
                # If we get an error raised here, and it isn't handled,
                # the add-on seems to break.
                print(f"Failed to load {__package__} preferences from file.")
                raise exc
            type(self).loading = False


class ExtraPies_AddonPrefs(PrefsFileSaveLoadMixin, AddonPreferences, USERPREF_PT_interface_menus_pie):
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

        keymap_data = list(PIE_ADDON_KEYMAPS.items())
        keymap_data = sorted(keymap_data, key=lambda tup: "".join(get_kmi_ui_info(tup[1][1], tup[1][2])))

        hotkeys = {}
        for kmi_hash, kmi_tup in keymap_data:
            _addon_kc, addon_km, addon_kmi = kmi_tup
            context = bpy.context
            user_kc = context.window_manager.keyconfigs.user
            user_km = user_kc.keymaps.get(addon_km.name)
            if not user_km:
                continue
            user_kmi = find_kmi_in_km_by_hash(user_km, kmi_hash)
            if not user_kmi:
                print(base_package + ": Failed to find UserKeymapItem to store: ")
                print_kmi(addon_kmi)
                continue

            try:
                hotkeys[kmi_hash] = {key:getattr(user_kmi, key) for key in ('idname', 'active', 'type', 'value', 'shift_ui', 'ctrl_ui', 'alt_ui', 'oskey_ui', 'any', 'map_type', 'key_modifier')}
            except:
                # TODO: Add debug logging or just print, but can't exit if something goes wrong here.
                continue
            hotkeys[kmi_hash]["key_cat"] = addon_km.name
            if user_kmi.properties:
                hotkeys[kmi_hash]["properties"] = {key:getattr(user_kmi.properties, key) for key in user_kmi.properties.keys() if hasattr(user_kmi.properties, key)}

        ret["hotkeys"] = hotkeys

        return ret

    def apply_prefs_from_dict_recursive(self, propgroup, data):
        hotkeys = data.pop("hotkeys")

        context = bpy.context
        user_kc = context.window_manager.keyconfigs.user

        for kmi_hash, kmi_props in hotkeys.items():
            key_cat = kmi_props.pop("key_cat")
            user_km = user_kc.keymaps.get(key_cat)
            if not user_km:
                continue
            user_kmi = find_kmi_in_km_by_hash(user_km, kmi_hash)
            if not user_kmi:
                continue

            if "properties" in kmi_props:
                op_kwargs = kmi_props.pop("properties")
                for key, value in op_kwargs.items():
                    if hasattr(user_kmi.properties, key):
                        setattr(user_kmi.properties, key, value)

            for key, value in kmi_props.items():
                if key=="any" and not value:
                    continue
                if key == "name":
                    continue
                try:
                    setattr(user_kmi, key, value)
                except:
                    # TODO: Implement debug logging or just print, but we can't exit if something goes wrong here.
                    pass

        super().apply_prefs_from_dict_recursive(propgroup, data)


def draw_prefs(layout, context, compact=False):
    prefs = get_addon_prefs(context)

    layout.use_property_split = True
    layout.use_property_decorate = False
    layout.operator('wm.url_open', text="Report Bug", icon='URL').url=get_bug_report_url()

    if not compact:
        layout.prop(prefs, 'show_in_sidebar')

    header, builtins_panel = layout.panel(idname="Extra Pies Builtin Prefs")
    header.label(text="Pie Preferences")
    if builtins_panel:
        prefs.draw_centered(context, layout)

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

    fh.write(
        "\n"
        "Description of the problem:\n"
        "\n"
    )

    fh.seek(0)

    return (
        "https://projects.blender.org/extensions/space_view3d_pie_menus/issues/new?template=.gitea/issue_template/bug.yaml&field:body="
        + urllib.parse.quote(fh.read())
    )


def register():
    bpy.utils.register_class(ExtraPies_AddonPrefs)
    ExtraPies_AddonPrefs.register_autoload_from_file()


def unregister():
    bpy.utils.unregister_class(ExtraPies_AddonPrefs)
