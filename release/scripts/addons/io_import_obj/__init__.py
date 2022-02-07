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

# <pep8-80 compliant>

bl_info = {
    "name": "Import Wavefront OBJ format",
    "author": "Campbell Barton, Bastien Montagne",
    "version": (3, 9, 0),
    "blender": (3, 0, 0),
    "location": "File > Import",
    "description": "Import OBJ, Import OBJ mesh, UV's, materials and textures",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/scene_obj.html",
    "support": 'OFFICIAL',
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "import_obj" in locals():
        importlib.reload(import_obj)


import bpy
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
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


def menu_func_import(self, context):
    self.layout.operator(ImportOBJ.bl_idname, text="Wavefront (.obj)", icon = "LOAD_OBJ")


classes = (
    ImportOBJ,
    OBJ_PT_import_include,
    OBJ_PT_import_transform,
    OBJ_PT_import_geometry,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
