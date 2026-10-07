# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# -----------------------------------------------------------------------------
# This addon is a Bforartists exclusive. It ships the Legacy Add-ons and the
# Pre-downloaded Extensions, so they can be installed without internet access.
# The Pre-downloaded Extensions operators live in `bl_pkg.bl_extension_ops`.
# -----------------------------------------------------------------------------

import bpy
import contextlib
import os
import shutil

from pathlib import Path

from bpy.types import (
    AddonPreferences,
    Context,
    Operator,
    UILayout,
)
from bpy.props import BoolProperty

bl_info = {
    "name": "Built-in Legacy Add-ons and Extensions",
    "author": "Draise (@trinumedia)",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "Preferences > Extensions",
    "description": "Ships the Legacy Add-ons and Pre-downloaded Extensions, to install without internet access",
    "warning": "Bforartists Exclusive",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    "support": "OFFICIAL",
    "category": "Bforartists",
}

# ---------
# Variables

# The Legacy Add-ons shipped with this bundle.
source_addon_folder = os.path.join(os.path.dirname(__file__), "Default_Addons")

# The versioned user folder, e.g. `.../Bforartists/5.3`.
major_minor = '.'.join(bpy.app.version_string.split('.')[:-1])
version_path = Path(Path(bpy.utils.resource_path('USER')).parent, major_minor)

# Where the Legacy Add-ons get installed to.
destination_addon_folder = version_path / 'scripts' / 'addons'

user_default = version_path / 'extensions' / 'user_default'
# ---------


@contextlib.contextmanager
def silence_output():
    """Suppress the terminal messages of installing many add-ons, so the first load does not spam."""
    with open(os.devnull, 'w') as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
        yield


def legacy_addons_installed_set(value):
    """Store whether the Legacy Add-ons are installed on the add-on preferences."""
    addon = bpy.context.preferences.addons.get(__package__)
    if addon is not None:
        addon.preferences.legacy_addons_installed = value


def legacy_addons_install_files():
    """Install the single file (`.py`) and zipped (`.zip`) Legacy Add-ons."""
    destination_addon_folder.mkdir(parents=True, exist_ok=True)
    for file in sorted(os.listdir(source_addon_folder)):
        file_path = os.path.join(source_addon_folder, file)
        if file.endswith((".py", ".zip")) and os.path.isfile(file_path):
            bpy.ops.preferences.addon_install(filepath=file_path)


# --------- INTERFACE START -------
class DEFAULTADDON_APT_preferences(AddonPreferences):
    bl_idname = __package__

    # BFA - these must be real RNA properties on this AddonPreferences subclass.
    # Declaring them on `bpy.types.AddonPreferences` did not work (reads returned the
    # `BoolProperty` object, which is always truthy), which made the UI always show
    # "Remove" and never "Install" for the legacy add-ons (#4568).
    legacy_addons_installed: BoolProperty(
        name="Legacy Add-ons Installed",
        description="The Legacy Add-ons are installed to the user add-ons",
        default=False,
    )
    extensions_installed: BoolProperty(
        name="Pre-downloaded Extensions Installed",
        description="The Pre-downloaded Extensions are installed",
        default=False,
    )

    def draw(self, context: Context):
        layout: UILayout = self.layout

        # BFA - the same buttons as in the Extensions preferences (#4568).
        from bl_pkg.bl_extension_ui import bfa_bundle_operators_draw
        bfa_bundle_operators_draw(context, layout.row())

        col = layout.column()
        col.label(text="Legacy Add-ons work offline. While offline, they are installed on first start.", icon='INFO')
        col.label(text="Pre-downloaded Extensions replace them and can be updated when online.", icon='BLANK1')
        col.label(text="Disable a Legacy Add-on before you enable its Extension, and the other way around.", icon='ERROR')
# --------- INTERFACE END ---------


class DEFAULTADDON_OT_installlegacy(Operator):
    """Install the Legacy Add-ons shipped with Bforartists, no internet access needed"""
    bl_idname = "bfa.install_legacy_addons"
    bl_label = "Install Legacy Add-ons"
    bl_options = {'INTERNAL'}  # BFA - use `extensions.install_legacy_addons`.

    def execute(self, context):
        legacy_addons_install_files()

        # Copy the Legacy Add-ons that are in sub-directories.
        # BFA - copy idempotently so re-running the operator updates an existing install,
        # the zipped add-ons are already installed above.
        for item in os.listdir(source_addon_folder):
            s = os.path.join(source_addon_folder, item)
            d = os.path.join(destination_addon_folder, item)
            if os.path.isdir(s):
                if item != "__pycache__":
                    shutil.copytree(s, d, dirs_exist_ok=True)
            elif item.endswith(".py"):
                shutil.copy2(s, d)  # copies also metadata

        bpy.ops.preferences.addon_refresh()
        context.window_manager.addon_search = ""

        legacy_addons_installed_set(True)
        return {'FINISHED'}


class DEFAULTADDON_OT_removelegacy(Operator):
    """Remove the Legacy Add-ons shipped with Bforartists from the user add-ons"""
    bl_idname = "bfa.remove_legacy_addons"
    bl_label = "Remove Legacy Add-ons"
    bl_options = {'INTERNAL'}  # BFA - use `extensions.remove_legacy_addons`.

    def execute(self, context):
        with silence_output():
            # Uninstall the add-ons found in the source_addon_folder.
            # BFA - `addon_remove` expects a module name, not a file name.
            for file in os.listdir(source_addon_folder):
                if file.endswith((".py", ".zip")):
                    try:
                        bpy.ops.preferences.addon_remove(module=os.path.splitext(file)[0])
                    except Exception:
                        pass

            # Delete any remaining files that came from the source folder.
            for root, _dirs, files in os.walk(source_addon_folder):
                for file in files:
                    dest_file = os.path.join(destination_addon_folder, os.path.relpath(os.path.join(root, file), source_addon_folder))
                    if os.path.exists(dest_file):
                        os.remove(dest_file)

            # Delete the sub-folders from the source folder that are now left without files.
            for root, dirs, _files in os.walk(source_addon_folder):
                for dir in dirs:
                    dest_dir = os.path.join(destination_addon_folder, os.path.relpath(os.path.join(root, dir), source_addon_folder))
                    if not os.path.isdir(dest_dir):
                        continue
                    if not any(os.path.isfile(os.path.join(dest_dir, f)) for f in os.listdir(dest_dir)):
                        shutil.rmtree(dest_dir)

        bpy.ops.preferences.addon_refresh()

        legacy_addons_installed_set(False)
        return {'FINISHED'}


def register_addons():
    """
    Install the Legacy Add-ons on the first start, as long as this add-on is enabled,
    online access is disabled and the user did not opt into the Pre-downloaded Extensions.
    """
    prefs = bpy.context.preferences

    if prefs.system.use_online_access:
        return None # BFA - don't cancel, just return none.

    # BFA - if the user opted into the pre-downloaded extensions, never auto-install the
    # Legacy Add-ons. Removing them stays a separate, manual action (#4568).
    addon = prefs.addons.get(__package__)
    if addon is not None and getattr(addon.preferences, "extensions_installed", False):
        return None

    # Ensure the user_default extensions sub-folder exists.
    user_default.mkdir(parents=True, exist_ok=True)

    # Only on the first start, before the user chose to continue offline or go online.
    if prefs.extensions.use_online_access_handled:
        return None

    with silence_output():
        legacy_addons_install_files()
        bpy.ops.preferences.addon_refresh()

    bpy.context.window_manager.addon_search = ""
    legacy_addons_installed_set(True)
    return None


classes = (
    DEFAULTADDON_APT_preferences,
    DEFAULTADDON_OT_installlegacy,
    DEFAULTADDON_OT_removelegacy,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.timers.register(register_addons, first_interval=0.1)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    try:
        bpy.app.timers.unregister(register_addons)
    except Exception:
        pass
