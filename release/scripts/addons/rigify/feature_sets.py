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
from zipfile import ZipFile
from shutil import rmtree


def feature_set_items(scene, context):
    """Get items for the Feature Set EnumProperty"""
    feature_sets_path = os.path.join(
        bpy.utils.script_path_user(), 'rigify')
    items = [('all',)*3, ('rigify',)*3, ]
    if os.path.exists(feature_sets_path):
        for fs in os.listdir(feature_sets_path):
            items.append((fs,)*3)

    return items

class DATA_OT_rigify_add_feature_set(bpy.types.Operator):
    bl_idname = "wm.rigify_add_feature_set"
    bl_label = "Add External Feature Set"
    bl_description = "Add external feature set (rigs, metarigs, ui templates)"
    bl_options = {"REGISTER", "UNDO"}

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

        rigify_config_path = os.path.join(bpy.utils.script_path_user(), 'rigify')
        os.makedirs(rigify_config_path, exist_ok=True)
        with ZipFile(bpy.path.abspath(self.filepath), 'r') as zip_archive:
            zip_archive.extractall(rigify_config_path)

        addon_prefs.machin = bpy.props.EnumProperty(items=(('a',)*3, ('b',)*3, ('c',)*3),)

        addon_prefs.update_external_rigs()
        return {'FINISHED'}


class DATA_OT_rigify_remove_feature_set(bpy.types.Operator):
    bl_idname = "wm.rigify_remove_feature_set"
    bl_label = "Remove External Feature Set"
    bl_description = "Remove external feature set (rigs, metarigs, ui templates)"
    bl_options = {"REGISTER", "UNDO"}

    featureset: StringProperty(maxlen=1024, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        addon_prefs = context.preferences.addons[__package__].preferences

        rigify_config_path = os.path.join(bpy.utils.script_path_user(), 'rigify')
        if os.path.exists(os.path.join(rigify_config_path, self.featureset)):
            rmtree(os.path.join(rigify_config_path, self.featureset))

        addon_prefs.update_external_rigs()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DATA_OT_rigify_add_feature_set)
    bpy.utils.register_class(DATA_OT_rigify_remove_feature_set)

def unregister():
    bpy.utils.unregister_class(DATA_OT_rigify_add_feature_set)
    bpy.utils.unregister_class(DATA_OT_rigify_remove_feature_set)
