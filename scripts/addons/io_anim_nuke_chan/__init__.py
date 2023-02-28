# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Nuke Animation Format (.chan)",
    "author": "Michael Krupa",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import/Export > Nuke (.chan)",
    "description": "Import/Export object's animation with nuke",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/anim_nuke_chan.html",
    "category": "Import-Export",
}


# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import importlib
    if "import_nuke_chan" in locals():
        importlib.reload(import_nuke_chan)
    if "export_nuke_chan" in locals():
        importlib.reload(export_nuke_chan)


import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (
        StringProperty,
        BoolProperty,
        EnumProperty,
        FloatProperty,
        )

# property shared by both operators
rotation_order = EnumProperty(
        name="Rotation order",
        description="Choose the export rotation order",
        items=(('XYZ', "XYZ", "XYZ"),
               ('XZY', "XZY", "XZY"),
               ('YXZ', "YXZ", "YXZ"),
               ('YZX', "YZX", "YZX"),
               ('ZXY', "ZXY", "ZXY"),
               ('ZYX', "ZYX", "ZYX"),
               ),
        default='XYZ')


class ImportChan(Operator, ImportHelper):
    """Import animation from .chan file, exported from nuke or houdini """ \
    """(the importer uses frame numbers from the file)"""
    bl_idname = "import_scene.import_chan"
    bl_label = "Import chan file"

    filename_ext = ".chan"

    filter_glob: StringProperty(default="*.chan", options={'HIDDEN'})

    rotation_order: rotation_order
    z_up: BoolProperty(
            name="Make Z up",
            description="Switch the Y and Z axis",
            default=True)

    sensor_width: FloatProperty(
            name="Camera sensor width",
            description="Imported camera sensor width",
            default=32.0)

    sensor_height: FloatProperty(
            name="Camera sensor height",
            description="Imported camera sensor height",
            default=18.0)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        from . import import_nuke_chan
        return import_nuke_chan.read_chan(context,
                                          self.filepath,
                                          self.z_up,
                                          self.rotation_order,
                                          self.sensor_width,
                                          self.sensor_height)


class ExportChan(Operator, ExportHelper):
    """Export the animation to .chan file, readable by nuke and houdini """ \
    """(the exporter uses frames from the frames range)"""
    bl_idname = "export.export_chan"
    bl_label = "Export chan file"

    filename_ext = ".chan"
    filter_glob: StringProperty(default="*.chan", options={'HIDDEN'})
    y_up: BoolProperty(
            name="Make Y up",
            description="Switch the Y and Z axis",
            default=True)
    rotation_order: rotation_order

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        from . import export_nuke_chan
        return export_nuke_chan.save_chan(context,
                                          self.filepath,
                                          self.y_up,
                                          self.rotation_order)


def menu_func_import(self, context):
    self.layout.operator(ImportChan.bl_idname, text="Nuke (.chan)")


def menu_func_export(self, context):
    self.layout.operator(ExportChan.bl_idname, text="Nuke (.chan)")


def register():
    bpy.utils.register_class(ImportChan)
    bpy.utils.register_class(ExportChan)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportChan)
    bpy.utils.unregister_class(ExportChan)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
