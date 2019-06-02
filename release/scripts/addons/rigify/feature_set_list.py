#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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
#======================= END GPL LICENSE BLOCK ========================

import bpy
from bpy.props import StringProperty
import os
import re
import importlib
from zipfile import ZipFile
from shutil import rmtree

from . import feature_sets


DEFAULT_NAME = 'rigify'

INSTALL_PATH = feature_sets._install_path()
NAME_PREFIX = feature_sets.__name__.split('.')


def get_install_path(*, create=False):
    if not os.path.exists(INSTALL_PATH):
        if create:
            os.makedirs(INSTALL_PATH, exist_ok=True)
        else:
            return None

    return INSTALL_PATH


def get_installed_list():
    features_path = get_install_path()
    if not features_path:
        return []

    sets = []

    for fs in os.listdir(features_path):
        if fs and fs[0] != '.' and fs != DEFAULT_NAME:
            fs_path = os.path.join(features_path, fs)
            if os.path.isdir(fs_path):
                sets.append(fs)

    return sets


def get_module(feature_set):
    return importlib.import_module('.'.join([*NAME_PREFIX, feature_set]))


def get_module_safe(feature_set):
    try:
        return get_module(feature_set)
    except:
        return None


def get_dir_path(feature_set, *extra_items):
    base_dir = os.path.join(INSTALL_PATH, feature_set, *extra_items)
    base_path = [*NAME_PREFIX, feature_set, *extra_items]
    return base_dir, base_path


def get_info_dict(feature_set):
    module = get_module_safe(feature_set)

    if module and hasattr(module, 'rigify_info'):
        data = module.rigify_info
        if isinstance(data, dict):
            return data

    return {}


def get_ui_name(feature_set):
    # Try to get user-defined name
    info = get_info_dict(feature_set)
    if 'name' in info:
        return info['name']

    # Default name based on directory
    name = re.sub(r'[_.-]', ' ', feature_set)
    name = re.sub(r'(?<=\d) (?=\d)', '.', name)
    return name.title()


def feature_set_items(scene, context):
    """Get items for the Feature Set EnumProperty"""
    items = [('all',)*3, ('rigify',)*3, ]

    for fs in get_installed_list():
        items.append((fs,)*3)

    return items


def verify_feature_set_archive(zipfile):
    """Verify that the zip file contains one root directory, and some required files."""
    dirname = None
    init_found = False
    data_found = False

    for name in zipfile.namelist():
        parts = re.split(r'[/\\]', name)

        if dirname is None:
            dirname = parts[0]
        elif dirname != parts[0]:
            dirname = None
            break

        if len(parts) == 2 and parts[1] == '__init__.py':
            init_found = True

        if len(parts) > 2 and parts[1] in {'rigs', 'metarigs'} and parts[-1] == '__init__.py':
            data_found = True

    return dirname, init_found, data_found


class DATA_OT_rigify_add_feature_set(bpy.types.Operator):
    bl_idname = "wm.rigify_add_feature_set"
    bl_label = "Add External Feature Set"
    bl_description = "Add external feature set (rigs, metarigs, ui templates)"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    filter_glob: StringProperty(default="*.zip", options={'HIDDEN'})
    filepath: StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences

        rigify_config_path = get_install_path(create=True)

        with ZipFile(bpy.path.abspath(self.filepath), 'r') as zip_archive:
            base_dirname, init_found, data_found = verify_feature_set_archive(zip_archive)

            if not base_dirname:
                self.report({'ERROR'}, "The feature set archive must contain one base directory.")
                return {'CANCELLED'}

            # Patch up some invalid characters to allow using 'Download ZIP' on GitHub.
            fixed_dirname = re.sub(r'[.-]', '_', base_dirname)

            if not re.fullmatch(r'[a-zA-Z][a-zA-Z_0-9]*', fixed_dirname):
                self.report({'ERROR'}, "The feature set archive base directory name is not a valid identifier: '%s'." % (base_dirname))
                return {'CANCELLED'}

            if fixed_dirname == DEFAULT_NAME:
                self.report({'ERROR'}, "The '%s' name is not allowed for feature sets." % (DEFAULT_NAME))
                return {'CANCELLED'}

            if not init_found or not data_found:
                self.report({'ERROR'}, "The feature set archive has no rigs or metarigs, or is missing __init__.py.")
                return {'CANCELLED'}

            base_dir = os.path.join(rigify_config_path, base_dirname)
            fixed_dir = os.path.join(rigify_config_path, fixed_dirname)

            for path, name in [(base_dir, base_dirname), (fixed_dir, fixed_dirname)]:
                if os.path.exists(path):
                    self.report({'ERROR'}, "Feature set directory already exists: '%s'." % (name))
                    return {'CANCELLED'}

            # Unpack the validated archive and fix the directory name if necessary
            zip_archive.extractall(rigify_config_path)

            if base_dir != fixed_dir:
                os.rename(base_dir, fixed_dir)

        addon_prefs.machin = bpy.props.EnumProperty(items=(('a',)*3, ('b',)*3, ('c',)*3),)

        addon_prefs.update_external_rigs()
        return {'FINISHED'}


class DATA_OT_rigify_remove_feature_set(bpy.types.Operator):
    bl_idname = "wm.rigify_remove_feature_set"
    bl_label = "Remove External Feature Set"
    bl_description = "Remove external feature set (rigs, metarigs, ui templates)"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    featureset: StringProperty(maxlen=1024, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences

        rigify_config_path = get_install_path()
        if rigify_config_path:
            set_path = os.path.join(rigify_config_path, self.featureset)
            if os.path.exists(set_path):
                rmtree(set_path)

        addon_prefs.update_external_rigs(force=True)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DATA_OT_rigify_add_feature_set)
    bpy.utils.register_class(DATA_OT_rigify_remove_feature_set)

def unregister():
    bpy.utils.unregister_class(DATA_OT_rigify_add_feature_set)
    bpy.utils.unregister_class(DATA_OT_rigify_remove_feature_set)
