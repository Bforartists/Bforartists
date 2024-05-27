# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Web3D X3D/VRML2 format",
    "author": "Campbell Barton, Bart, Bastien Montagne, Seva Alekseyev",
    "version": (2, 3, 1),
    "blender": (2, 93, 0),
    "location": "File > Import-Export",
    "description": "Import-Export X3D, Import VRML2",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/scene_x3d.html",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "import_x3d" in locals():
        importlib.reload(import_x3d)
    if "export_x3d" in locals():
        importlib.reload(export_x3d)

import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        axis_conversion,
        path_reference_mode,
        )


@orientation_helper(axis_forward='Z', axis_up='Y')
class ImportX3D(bpy.types.Operator, ImportHelper):
    """Import an X3D or VRML2 file"""
    bl_idname = "import_scene.x3d"
    bl_label = "Import X3D/VRML2"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".x3d"
    filter_glob: StringProperty(default="*.x3d;*.wrl", options={'HIDDEN'})

    def execute(self, context):
        from . import import_x3d

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            ))
        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return import_x3d.load(context, **keywords)

    def draw(self, context):
        pass


class X3D_PT_export_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_x3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_selection")
        layout.prop(operator, "use_hierarchy")
        layout.prop(operator, "name_decorations")
        layout.prop(operator, "use_h3d")


class X3D_PT_export_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_x3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_scale")
        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


class X3D_PT_export_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_x3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_mesh_modifiers")
        layout.prop(operator, "use_triangulate")
        layout.prop(operator, "use_normals")
        layout.prop(operator, "use_compress")


@orientation_helper(axis_forward='Z', axis_up='Y')
class ExportX3D(bpy.types.Operator, ExportHelper):
    """Export selection to Extensible 3D file (.x3d)"""
    bl_idname = "export_scene.x3d"
    bl_label = 'Export X3D'
    bl_options = {'PRESET'}

    filename_ext = ".x3d"
    filter_glob: StringProperty(default="*.x3d", options={'HIDDEN'})

    use_selection: BoolProperty(
            name="Selection Only",
            description="Export selected objects only",
            default=False,
            )
    use_mesh_modifiers: BoolProperty(
            name="Apply Modifiers",
            description="Use transformed mesh data from each object",
            default=True,
            )
    use_triangulate: BoolProperty(
            name="Triangulate",
            description="Write quads into 'IndexedTriangleSet'",
            default=False,
            )
    use_normals: BoolProperty(
            name="Normals",
            description="Write normals with geometry",
            default=False,
            )
    use_compress: BoolProperty(
            name="Compress",
            description="Compress the exported file",
            default=False,
            )
    use_hierarchy: BoolProperty(
            name="Hierarchy",
            description="Export parent child relationships",
            default=True,
            )
    name_decorations: BoolProperty(
            name="Name decorations",
            description=("Add prefixes to the names of exported nodes to "
                         "indicate their type"),
            default=True,
            )
    use_h3d: BoolProperty(
            name="H3D Extensions",
            description="Export shaders for H3D",
            default=False,
            )

    global_scale: FloatProperty(
            name="Scale",
            min=0.01, max=1000.0,
            default=1.0,
            )

    path_mode: path_reference_mode

    def execute(self, context):
        from . import export_x3d

        from mathutils import Matrix

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "global_scale",
                                            "check_existing",
                                            "filter_glob",
                                            ))
        global_matrix = axis_conversion(to_forward=self.axis_forward,
                                        to_up=self.axis_up,
                                        ).to_4x4() @ Matrix.Scale(self.global_scale, 4)
        keywords["global_matrix"] = global_matrix

        return export_x3d.save(context, **keywords)

    def draw(self, context):
        pass


class X3D_PT_import_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_x3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


def menu_func_import(self, context):
    self.layout.operator(ImportX3D.bl_idname,
                         text="X3D Extensible 3D (.x3d/.wrl)")


def menu_func_export(self, context):
    self.layout.operator(ExportX3D.bl_idname,
                         text="X3D Extensible 3D (.x3d)")


classes = (
    ExportX3D,
    X3D_PT_export_include,
    X3D_PT_export_transform,
    X3D_PT_export_geometry,
    ImportX3D,
    X3D_PT_import_transform,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
