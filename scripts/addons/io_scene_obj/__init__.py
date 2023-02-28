# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Wavefront OBJ format (legacy)",
    "author": "Campbell Barton, Bastien Montagne",
    "version": (3, 9, 0),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "description": "Import-Export OBJ, Import OBJ mesh, UV's, materials and textures",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/scene_obj.html",
    "support": 'OFFICIAL',
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "import_obj" in locals():
        importlib.reload(import_obj)
    if "export_obj" in locals():
        importlib.reload(export_obj)


import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
)


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportOBJ(bpy.types.Operator, ImportHelper):
    """Load a Wavefront OBJ File"""
    bl_idname = "import_scene.obj"
    bl_label = "Import OBJ"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".obj"
    filter_glob: StringProperty(
        default="*.obj;*.mtl",
        options={'HIDDEN'},
    )

    use_edges: BoolProperty(
        name="Lines",
        description="Import lines and faces with 2 verts as edge",
        default=True,
    )
    use_smooth_groups: BoolProperty(
        name="Smooth Groups",
        description="Surround smooth groups by sharp edges",
        default=True,
    )

    use_split_objects: BoolProperty(
        name="Object",
        description="Import OBJ Objects into Blender Objects",
        default=True,
    )
    use_split_groups: BoolProperty(
        name="Group",
        description="Import OBJ Groups into Blender Objects",
        default=False,
    )

    use_groups_as_vgroups: BoolProperty(
        name="Poly Groups",
        description="Import OBJ groups as vertex groups",
        default=False,
    )

    use_image_search: BoolProperty(
        name="Image Search",
        description="Search subdirs for any associated images "
        "(Warning, may be slow)",
        default=True,
    )

    split_mode: EnumProperty(
        name="Split",
        items=(
            ('ON', "Split", "Split geometry, omits vertices unused by edges or faces"),
            ('OFF', "Keep Vert Order", "Keep vertex order from file"),
        ),
    )

    global_clamp_size: FloatProperty(
        name="Clamp Size",
        description="Clamp bounds under this value (zero to disable)",
        min=0.0, max=1000.0,
        soft_min=0.0, soft_max=1000.0,
        default=0.0,
    )

    def execute(self, context):
        # print("Selected: " + context.active_object.name)
        from . import import_obj

        if self.split_mode == 'OFF':
            self.use_split_objects = False
            self.use_split_groups = False
        else:
            self.use_groups_as_vgroups = False

        keywords = self.as_keywords(
            ignore=(
                "axis_forward",
                "axis_up",
                "filter_glob",
                "split_mode",
            ),
        )

        global_matrix = axis_conversion(
            from_forward=self.axis_forward,
            from_up=self.axis_up,
        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        if bpy.data.is_saved and context.preferences.filepaths.use_relative_paths:
            import os
            keywords["relpath"] = os.path.dirname(bpy.data.filepath)

        return import_obj.load(context, **keywords)

    def draw(self, context):
        pass


class OBJ_PT_import_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_obj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'use_image_search')
        layout.prop(operator, 'use_smooth_groups')
        layout.prop(operator, 'use_edges')


class OBJ_PT_import_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_obj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_clamp_size")
        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


class OBJ_PT_import_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_obj"

    def draw(self, context):
        layout = self.layout

        sfile = context.space_data
        operator = sfile.active_operator

        layout.row().prop(operator, "split_mode", expand=True)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column()
        if operator.split_mode == 'ON':
            col.prop(operator, "use_split_objects", text="Split by Object")
            col.prop(operator, "use_split_groups", text="Split by Group")
        else:
            col.prop(operator, "use_groups_as_vgroups")


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportOBJ(bpy.types.Operator, ExportHelper):
    """Save a Wavefront OBJ File"""

    bl_idname = "export_scene.obj"
    bl_label = 'Export OBJ'
    bl_options = {'PRESET'}

    filename_ext = ".obj"
    filter_glob: StringProperty(
        default="*.obj;*.mtl",
        options={'HIDDEN'},
    )

    # context group
    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
    )
    use_animation: BoolProperty(
        name="Animation",
        description="Write out an OBJ for each frame",
        default=False,
    )

    # object group
    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers",
        default=True,
    )
    # extra data group
    use_edges: BoolProperty(
        name="Include Edges",
        description="",
        default=True,
    )
    use_smooth_groups: BoolProperty(
        name="Smooth Groups",
        description="Write sharp edges as smooth groups",
        default=False,
    )
    use_smooth_groups_bitflags: BoolProperty(
        name="Bitflag Smooth Groups",
        description="Same as 'Smooth Groups', but generate smooth groups IDs as bitflags "
        "(produces at most 32 different smooth groups, usually much less)",
        default=False,
    )
    use_normals: BoolProperty(
        name="Write Normals",
        description="Export one normal per vertex and per face, to represent flat faces and sharp edges",
        default=True,
    )
    use_uvs: BoolProperty(
        name="Include UVs",
        description="Write out the active UV coordinates",
        default=True,
    )
    use_materials: BoolProperty(
        name="Write Materials",
        description="Write out the MTL file",
        default=True,
    )
    use_triangles: BoolProperty(
        name="Triangulate Faces",
        description="Convert all faces to triangles",
        default=False,
    )
    use_nurbs: BoolProperty(
        name="Write Nurbs",
        description="Write nurbs curves as OBJ nurbs rather than "
        "converting to geometry",
        default=False,
    )
    use_vertex_groups: BoolProperty(
        name="Polygroups",
        description="",
        default=False,
    )

    # grouping group
    use_blen_objects: BoolProperty(
        name="OBJ Objects",
        description="Export Blender objects as OBJ objects",
        default=True,
    )
    group_by_object: BoolProperty(
        name="OBJ Groups",
        description="Export Blender objects as OBJ groups",
        default=False,
    )
    group_by_material: BoolProperty(
        name="Material Groups",
        description="Generate an OBJ group for each part of a geometry using a different material",
        default=False,
    )
    keep_vertex_order: BoolProperty(
        name="Keep Vertex Order",
        description="",
        default=False,
    )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
    )

    path_mode: path_reference_mode

    check_extension = True

    def execute(self, context):
        from . import export_obj

        from mathutils import Matrix
        keywords = self.as_keywords(
            ignore=(
                "axis_forward",
                "axis_up",
                "global_scale",
                "check_existing",
                "filter_glob",
            ),
        )

        global_matrix = (
            Matrix.Scale(self.global_scale, 4) @
            axis_conversion(
                to_forward=self.axis_forward,
                to_up=self.axis_up,
            ).to_4x4()
        )

        keywords["global_matrix"] = global_matrix
        return export_obj.save(context, **keywords)

    def draw(self, context):
        pass


class OBJ_PT_export_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_obj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        col = layout.column(heading="Limit to")
        col.prop(operator, 'use_selection')

        col = layout.column(heading="Objects as", align=True)
        col.prop(operator, 'use_blen_objects')
        col.prop(operator, 'group_by_object')
        col.prop(operator, 'group_by_material')

        layout.separator()

        layout.prop(operator, 'use_animation')


class OBJ_PT_export_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_obj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'global_scale')
        layout.prop(operator, 'path_mode')
        layout.prop(operator, 'axis_forward')
        layout.prop(operator, 'axis_up')


class OBJ_PT_export_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_obj"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, 'use_mesh_modifiers')
        layout.prop(operator, 'use_smooth_groups')
        layout.prop(operator, 'use_smooth_groups_bitflags')
        layout.prop(operator, 'use_normals')
        layout.prop(operator, 'use_uvs')
        layout.prop(operator, 'use_materials')
        layout.prop(operator, 'use_triangles')
        layout.prop(operator, 'use_nurbs', text="Curves as NURBS")
        layout.prop(operator, 'use_vertex_groups')
        layout.prop(operator, 'keep_vertex_order')


def menu_func_import(self, context):
    self.layout.operator(ImportOBJ.bl_idname, text="Wavefront (.obj) (legacy)", icon = "LOAD_OBJ")


def menu_func_export(self, context):
    self.layout.operator(ExportOBJ.bl_idname, text="Wavefront (.obj) (legacy)", icon = "SAVE_OBJ")


classes = (
    ImportOBJ,
    OBJ_PT_import_include,
    OBJ_PT_import_transform,
    OBJ_PT_import_geometry,
    ExportOBJ,
    OBJ_PT_export_include,
    OBJ_PT_export_transform,
    OBJ_PT_export_geometry,
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
