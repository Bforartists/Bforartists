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
# This addon is a Bforartists exclusive addons the pre-downloadeds legacy addons
# and extensions without requiring opt-in access to the internet.
# -----------------------------------------------------------------------------

import bpy
import os

import sys

from bpy.types import (
    AddonPreferences,
    Context,
    Operator,
    UILayout,
)

import shutil
from pathlib import Path
from os import path as p
from bpy.types import Operator
from bpy.props import BoolProperty

bl_info = {
    "name": "Built-in Legacy Addons and Extensions",
    "author": "Draise (@trinumedia)",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "Preferences - Extensions",
    "description": "Adds all the Built-in Legacy addons as a pre-downloaded bundle of addons and/or extensions",
    "warning": "Bforartists Exclusive",
    "doc_url": "https://github.com/Bforartists/Manual",
    "tracker_url": "https://github.com/Bforartists/Bforartists",
    # Please go to https://github.com/BlenderDefender/implement_addon_updater to implement support for automatic library updates:
    "endpoint_url": "",
    "support": "OFFICIAL",
    "category": "Bforartists",
}

# ---------
# Variables

# Configure the display name and sub-folder of your Library here:
source_ext = "Default_Extensions"
source_addons = "Default_Addons"

prefs = bpy.context.preferences

# Get the addon path
path = p.dirname(__file__)

# Get the extensions source files
source_addon_folder = os.path.join(path, source_addons)

# Get the USER path
user_path = Path(bpy.utils.resource_path('USER')).parent

# Get the version string
version_string = bpy.app.version_string

# Split the string at the last dot to get 'MAJOR.MINOR'
major_minor = '.'.join(version_string.split('.')[:-1])

# Join with the user_path
version_path = Path(user_path, major_minor)

# Define the addons  sub-folder path
destination_addon_folder = version_path / 'scripts' / 'addons'

user_default = version_path / 'extensions' / 'user_default'

legacy_addons_installed = False
extensions_installed = False
# ---------

# --------- INTERFACE START -------
class DEFAULTADDON_APT_preferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context: Context):
        layout: UILayout = self.layout

        # Display addon inormation
        #addon_version = bl_info['version']

        #layout.label(
        #    text=f"{source_ext} - Version {'.'.join(map(str, addon_version))}")


        box = layout.box()

        box.operator("bfa.install_legacy_addons", text="Install Built-In Legacy Addo-ns", icon='IMPORT')
        box.operator("bfa.remove_legacy_addons", text="Remove Built-in Legacy Add-ons", icon='CANCEL')
        box.operator("bfa.install_downloaded_extensions", text="Install Pre-downloaded Extensions Equivalents", icon='PLUGIN')

        layout.separator()

        box = layout.box()
        box.label(
            text="When enabled, this installs the Built-in Legacy Add-ons to the user preferences.", icon='INFO')
        box.label(
            text="When you opt-in to use Online Access, you should remove Built-in Legacy Add-ons.")
        box.label(
            text="Built-in Legacy Add-ons can be replaced with Extensions that can update from the internet.")

        layout.separator()

        layout.label(
            text="WARNING: Disable legacy Add-ons before you enable the Extension equivalent.", icon='ERROR')
# --------- INTERFACE END ---------


class DEFAULTADDON_OT_installlegacy(Operator):
    """Installs all legacy addons that are not core addons"""
    bl_idname = "bfa.install_legacy_addons"
    bl_label = "Install Legacy Addons"

    def execute(self, context):
        # --------------------------
        # Ensure the addons sub-folder exists
        if not destination_addon_folder.exists():
            destination_addon_folder.mkdir(parents=True)

        print("INFO: Extensions not enabled, copying Built-in Legacy addons...")
        # If extensions is not on, and the addon is on, then install the legacy addons

        # Loop through each file in the source_addon_folder to install them, so the pycache is set
        for file in os.listdir(source_addon_folder):
            file_path = os.path.join(source_addon_folder, file)

            # Check if the file is a .py file and is directly in the source_addon_folder
            if file.endswith(".py") or file.endswith(".zip")  and os.path.isfile(file_path):
                # install the addon
                bpy.ops.preferences.addon_install(filepath=file_path)
                print("Installed: " + file)

        # Copy the other addons that are in sub-directories
        for item in os.listdir(source_addon_folder):
            s = os.path.join(source_addon_folder, item)
            d = os.path.join(destination_addon_folder, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d, False, None)
            else:
                shutil.copy2(s, d)  # copies also metadata

        print("INFO: Legacy addons installed")

        # Refresh to see all
        bpy.ops.preferences.addon_refresh()

        bpy.data.window_managers["WinMan"].addon_search = ""

        bpy.types.AddonPreferences.legacy_addons_installed = True

        return {'FINISHED'}


class DEFAULTADDON_OT_removelegacy(Operator):
    """Removes all legacy addons that are not core addons"""
    bl_idname = "bfa.remove_legacy_addons"
    bl_label = "Remove Built-In Legacy Addons"

    def execute(self, context):

        # Redirect stdout and stderr to /dev/null - surpresses terminal messages to not spam on first load.
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

        # Batch uninstall the addons found in the source_addon_folder
        for file in os.listdir(source_addon_folder):
            file_path = os.path.join(source_addon_folder, file)

            if os.path.exists(file_path) and (file.endswith(".py") or file.endswith(".zip")):
                # Uninstall the addon
                bpy.ops.preferences.addon_remove(module=file)

        # --------------------------
        # Iterate over all files in the source folder
        for root, dirs, files in os.walk(source_addon_folder):
            for file in files:
                # Construct the full filepath
                src_file = os.path.join(root, file)

                # Construct the corresponding filepath in the destination folder
                dest_file = str(src_file).replace(str(source_addon_folder), str(destination_addon_folder))

                # Skip if the file does not exist in the destination folder
                if not os.path.exists(dest_file):
                    continue

                # If the file also exists in the destination folder, delete it
                os.remove(dest_file)

        # Iterate over all sub-folders in the source folder
        for root, dirs, files in os.walk(source_addon_folder):
            for dir in dirs:
                # Construct the full directory path
                src_dir = os.path.join(root, dir)

                # Construct the corresponding directory path in the destination folder
                dest_dir = os.path.join(destination_addon_folder, os.path.relpath(src_dir, source_addon_folder))

                # Skip if the directory does not exist in the destination folder
                if not os.path.exists(dest_dir):
                    continue

                # If the directory exists in the destination folder and is empty (contains no files), delete it
                if not any(os.path.isfile(os.path.join(dest_dir, f)) for f in os.listdir(dest_dir)):
                    shutil.rmtree(dest_dir)

        # Reactivate the console by resetting stdout and stderr to default
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # Refresh to see all
        bpy.ops.preferences.addon_refresh()

        # Force reload to reset the preferences
        #bpy.ops.script.reload()

        bpy.types.AddonPreferences.legacy_addons_installed = False

        return {'FINISHED'}


class DEFAULTADDON_OT_install_downloaded_extensions(Operator):
    """Copy and prepare pre-downloaded Extensions Addons when opt-in to be online is enabled"""
    bl_idname = "bfa.install_downloaded_extensions"
    bl_label = "Replace Legacy with Extension"

    def execute(self, context):
        print("NOTE: Copying Extensions..")
        # ----------
        # Variables

        current_script_path = p.dirname(__file__)

        # Get the addon path
        path = os.path.join(os.path.dirname(current_script_path), "bfa_default_addons")
        #path = os.path.join(os.path.dirname(current_script_path))

        # Get the USER path
        user_path = Path(bpy.utils.resource_path('USER')).parent

        # Get the version string
        version_string = bpy.app.version_string

        # Split the string at the last dot to get 'MAJOR.MINOR'
        major_minor = '.'.join(version_string.split('.')[:-1])

        # Join with the user_path
        version_path = Path(user_path, major_minor)

        # Get the source files
        source_ext = "Default_Extensions"
        source_ext_folder = os.path.join(path, source_ext)

        # Define the Extensions sub-folder path
        destination_ext_folder = version_path / 'extensions' / 'blender_org'

        # --------------------------
        # Copy the extension addons

        # Ensure the extensions sub-folder exists
        if not destination_ext_folder.exists():
            destination_ext_folder.mkdir(parents=True)

        # Copy the other extenions that are in sub-directories
        for item in os.listdir(source_ext_folder):
            s = os.path.join(source_ext_folder, item)
            d = os.path.join(destination_ext_folder, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d, False, None)
            else:
                shutil.copy2(s, d)  # copies also metadata

        bpy.types.AddonPreferences.extensions_installed = False

        print("NOTE: Extensions copied successfully.")

        bpy.ops.extensions.repo_sync_all()
        return {'FINISHED'}


def register_addons():
    """Register the built-in legacy add-ons in Bforartists, as long as the add-on is enabled."""
    """and when Internet Access is disabled."""

    if bpy.context.preferences.system.use_online_access:
        return None # BFA - don't cancel, just return none.

    # Redirect stdout and stderr to /dev/null - surpresses terminal messages to not spam on first load.
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    # Ensure the addons sub-folder exists
    if not destination_addon_folder.exists():
        destination_addon_folder.mkdir(parents=True)

    # Ensure the user_default extensions sub-folder exists
    if not user_default.exists():
        user_default.mkdir(parents=True)

    # Check if extensions is on on first load, if not, bypass
    if prefs.extensions.use_online_access_handled == True :
        # If addon is enabled and extensions is on, do nothing
        #print("INFO: Extensions are already enabled, so never mind...")
        pass
    else:
        print("INFO: Extensions not enabled, copying Built-in Legacy addons...")
        # If extensions is not on, and the addon is on, then install the legacy addons

        # Loop through each file in the source_addon_folder to install them, so the pycache is set
        for file in os.listdir(source_addon_folder):
            file_path = os.path.join(source_addon_folder, file)

            # Check if the file is a .py file and is directly in the source_addon_folder
            if file.endswith(".py") or file.endswith(".zip")  and os.path.isfile(file_path):
                # install the addon
                bpy.ops.preferences.addon_install(filepath=file_path)
                print("NOTE: Installed - " + file)

        # Refresh to see all
        bpy.ops.preferences.addon_refresh()

        bpy.data.window_managers["WinMan"].addon_search = ""

        bpy.types.AddonPreferences.legacy_addons_installed = True

        # Reactivate the console by resetting stdout and stderr to default
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        pass

    return None


classes = (
    DEFAULTADDON_APT_preferences,
    DEFAULTADDON_OT_installlegacy,
    DEFAULTADDON_OT_removelegacy,
    DEFAULTADDON_OT_install_downloaded_extensions
)

#Adds the the bundle when you load the addon.
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.timers.register(register_addons, first_interval=0.1)

    bpy.types.AddonPreferences.legacy_addons_installed = bpy.props.BoolProperty(name="legacy_addons_installed", default=False)
    bpy.types.AddonPreferences.extensions_installed = bpy.props.BoolProperty(name="extensions_installed", default=False)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.AddonPreferences.extensions_installed
    del bpy.types.AddonPreferences.legacy_addons_installed

    try:
        bpy.app.timers.unregister(register_addons)
    except Exception:
        pass


