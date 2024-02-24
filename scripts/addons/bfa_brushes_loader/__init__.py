# ##### BEGIN GPL LICENSE BLOCK #####
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
# ##### END GPL LICENSE BLOCK #####

from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy.types import Panel, Operator
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "Bforartists Brushes Loader",
    "author": "Bforartists",
    "version": (0, 0, 1),
    "blender": (4, 0, 0),
    "location": "User Preferences > Addons",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface",
}

BRUSHES_BLEND_FILEPATH = (Path(__file__).parent / "brushes2.blend").as_posix()


def load_all_brushes_from_blend(filepath: str):
    with bpy.data.libraries.load(
        filepath,
        # appending is broken (https://projects.blender.org/blender/blender/issues/118686),
        # so we link instead, we can convert linked data to local later if we want
        link=True,
        relative=False,
        assets_only=False,
        create_liboverrides=False,
        reuse_liboverrides=False,
        create_liboverrides_runtime=False,
    ) as (data_from, data_to):
        data_to.brushes = data_from.brushes

    for brush in data_to.brushes:
        if brush is None:
            continue
        brush.make_local()
        if not brush.icon_filepath:
            continue  # Fix icon filepath if needed  # (aka modify brush.icon_filepath)


class BFA_OT_load_brushes(Operator):
    bl_idname = "bfa.load_brushes"
    bl_label = "Load Brushes"
    bl_description = "Load all brushes from the bundled .blend file"
    bl_options = {"UNDO", "REGISTER"}

    def execute(self, context):
        try:
            load_all_brushes_from_blend(BRUSHES_BLEND_FILEPATH)
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        return {"FINISHED"}


class BFA_OT_export_brushes(Operator):
    bl_idname = "bfa.export_brushes"
    bl_label = "Export Brushes"
    bl_description = "Export all brushes from current file"
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        try:
            bpy.data.libraries.write(
                self.filepath, set(bpy.data.brushes), fake_user=True
            )
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class BFA_PT_brushes_loader(Panel):
    bl_label = "Brushes Loader"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bforartists"

    def draw(self, context):
        self.layout.operator(BFA_OT_load_brushes.bl_idname)
        # self.layout.operator(BFA_OT_export_brushes.bl_idname)


def register():
    register_class(BFA_OT_load_brushes)
    register_class(BFA_OT_export_brushes)
    register_class(BFA_PT_brushes_loader)


def unregister():
    unregister_class(BFA_PT_brushes_loader)
    unregister_class(BFA_OT_export_brushes)
    unregister_class(BFA_OT_load_brushes)
