# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Stanford PLY format",
    "author": "Bruce Merry, Campbell Barton, Bastien Montagne, Mikhail Rachinsky",
    "version": (2, 2, 0),
    "blender": (3, 0, 0),
    "location": "File > Import/Export",
    "description": "Import-Export PLY mesh data with UVs and vertex colors",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/mesh_ply.html",
    "support": 'OFFICIAL',
    "category": "Import-Export",
}

# Copyright (C) 2004, 2005: Bruce Merry, bmerry@cs.uct.ac.za
# Contributors: Bruce Merry, Campbell Barton

if "bpy" in locals():
    import importlib
    if "export_ply" in locals():
        importlib.reload(export_ply)
    if "import_ply" in locals():
        importlib.reload(import_ply)


import bpy
from bpy.props import (
    CollectionProperty,
    StringProperty,
    BoolProperty,
    FloatProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    axis_conversion,
    orientation_helper,
)


class ImportPLY(bpy.types.Operator, ImportHelper):
    """Load a PLY geometry file"""
    bl_idname = "import_mesh.ply"
    bl_label = "Import PLY"
    bl_options = {'UNDO'}

    files: CollectionProperty(
        name="File Path",
        description="File path used for importing the PLY file",
        type=bpy.types.OperatorFileListElement,
    )

    # Hide opertator properties, rest of this is managed in C. See WM_operator_properties_filesel().
    hide_props_region: BoolProperty(
        name="Hide Operator Properties",
        description="Collapse the region displaying the operator settings",
        default=True,
    )

    directory: StringProperty()

    filename_ext = ".ply"
    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    def execute(self, context):
        import os
        from . import import_ply

        context.window.cursor_set('WAIT')

        paths = [
            os.path.join(self.directory, name.name)
            for name in self.files
        ]

        if not paths:
            paths.append(self.filepath)

        for path in paths:
            import_ply.load(self, context, path)

        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}


@orientation_helper(axis_forward='Y', axis_up='Z')
class ExportPLY(bpy.types.Operator, ExportHelper):
    bl_idname = "export_mesh.ply"
    bl_label = "Export PLY"
    bl_description = "Export as a Stanford PLY with normals, vertex colors and texture coordinates"

    filename_ext = ".ply"
    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    use_ascii: BoolProperty(
        name="ASCII",
        description="Export using ASCII file format, otherwise use binary",
    )
    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
    )
    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply Modifiers to the exported mesh",
        default=True,
    )
    use_normals: BoolProperty(
        name="Normals",
        description="Export vertex normals",
        default=True,
    )
    use_uv_coords: BoolProperty(
        name="UVs",
        description="Export the active UV layer (will split edges by seams)",
        default=True,
    )
    use_colors: BoolProperty(
        name="Vertex Colors",
        description="Export the active vertex color layer",
        default=True,
    )
    global_scale: FloatProperty(
        name="Scale",
        min=0.01,
        max=1000.0,
        default=1.0,
    )

    def execute(self, context):
        from mathutils import Matrix
        from . import export_ply

        context.window.cursor_set('WAIT')

        keywords = self.as_keywords(
            ignore=(
                "axis_forward",
                "axis_up",
                "global_scale",
                "check_existing",
                "filter_glob",
            )
        )
        global_matrix = axis_conversion(
            to_forward=self.axis_forward,
            to_up=self.axis_up,
        ).to_4x4() @ Matrix.Scale(self.global_scale, 4)
        keywords["global_matrix"] = global_matrix

        export_ply.save(context, **keywords)

        context.window.cursor_set('DEFAULT')

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(heading="Format")
        col.prop(operator, "use_ascii")


class PLY_PT_export_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_ply"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_selection")


class PLY_PT_export_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_ply"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")
        layout.prop(operator, "global_scale")


class PLY_PT_export_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_ply"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_mesh_modifiers")
        layout.prop(operator, "use_normals")
        layout.prop(operator, "use_uv_coords")
        layout.prop(operator, "use_colors")


def menu_func_import(self, context):
    self.layout.operator(ImportPLY.bl_idname, text="Stanford (.ply)", icon = "LOAD_PLY")


def menu_func_export(self, context):
    self.layout.operator(ExportPLY.bl_idname, text="Stanford (.ply)", icon = "SAVE_PLY")


classes = (
    ImportPLY,
    ExportPLY,
    PLY_PT_export_include,
    PLY_PT_export_transform,
    PLY_PT_export_geometry,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
