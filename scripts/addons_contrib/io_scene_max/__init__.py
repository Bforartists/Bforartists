# SPDX-FileCopyrightText: 2023 Sebastian Schrand
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper,
    axis_conversion,
)
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
)

bl_info = {
    "name": "Import Autodesk MAX (.max)",
    "author": "Sebastian Sille, Philippe Lagadec, Jens M. Plonka",
    "version": (1, 1, 4),
    "blender": (4, 0, 0),
    "location": "File > Import",
    "description": "Import 3DSMAX meshes & materials",
    "warning": "",
    "filepath_url": "",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "import_max" in locals():
        importlib.reload(import_max)


@orientation_helper(axis_forward='Y', axis_up='Z')
class Import_max(bpy.types.Operator, ImportHelper):
    """Import Autodesk MAX"""
    bl_idname = "import_scene.max"
    bl_label = "Import MAX (.max)"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".max"
    filter_glob: StringProperty(default="*.max", options={'HIDDEN'})
    filepath: StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})

    scale_objects: FloatProperty(
        name="Scale",
        description="Scale factor for all objects",
        min=0.0, max=10000.0,
        soft_min=0.0, soft_max=10000.0,
        default=1.0,
    )
    use_material: BoolProperty(
        name="Materials",
        description="Import the materials of the objects",
        default=True,
    )
    use_uv_mesh: BoolProperty(
        name="UV Mesh",
        description="Import texture coordinates as mesh objects",
        default=False,
    )
    use_apply_matrix: BoolProperty(
        name="Apply Matrix",
        description="Use matrix to transform the objects",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == "VIEW_3D")

    def execute(self, context):
        from . import import_max
        if not self.filepath or not self.filepath.endswith(".max"):
            return {'CANCELLED'}

        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob"))
        global_matrix = axis_conversion(from_forward=self.axis_forward, from_up=self.axis_up,).to_4x4()
        keywords["global_matrix"] = global_matrix

        return import_max.load(self, context, **keywords)

    def invoke(self, context, event):
        if self.filepath:
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        pass


class MAX_FH_import(bpy.types.FileHandler):
    bl_idname = "MAX_FH_import"
    bl_label = "File handler for .max import"
    bl_import_operator = "import_scene.max"
    bl_file_extensions = ".max"

    @classmethod
    def poll_drop(cls, context):
        return (context.area and context.area.type == 'VIEW_3D')


class MAX_PT_import_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_max"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layrow = layout.row(align=True)
        layrow.prop(operator, "use_material")
        layrow.label(text="", icon='MATERIAL' if operator.use_material else 'SHADING_TEXTURE')
        layrow = layout.row(align=True)
        layrow.prop(operator, "use_uv_mesh")
        layrow.label(text="", icon='UV' if operator.use_uv_mesh else 'GROUP_UVS')


class MAX_PT_import_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_max"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "scale_objects")
        layrow = layout.row(align=True)
        layrow.prop(operator, "use_apply_matrix")
        layrow.label(text="", icon='VIEW_ORTHO' if operator.use_apply_matrix else 'MESH_GRID')
        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


def menu_func(self, context):
    self.layout.operator(Import_max.bl_idname, text="Autodesk MAX (.max)")


def register():
    bpy.utils.register_class(Import_max)
    bpy.utils.register_class(MAX_FH_import)
    bpy.utils.register_class(MAX_PT_import_include)
    bpy.utils.register_class(MAX_PT_import_transform)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    bpy.utils.unregister_class(MAX_PT_import_transform)
    bpy.utils.unregister_class(MAX_PT_import_include)
    bpy.utils.unregister_class(MAX_FH_import)
    bpy.utils.unregister_class(Import_max)


if __name__ == "__main__":
    register()
