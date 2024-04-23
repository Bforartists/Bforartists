# SPDX-FileCopyrightText: 2011-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    axis_conversion,
    poll_file_object_drop,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    StringProperty,
    CollectionProperty,
)
import bpy
bl_info = {
    "name": "Autodesk 3DS format",
    "author": "Bob Holcomb, Campbell Barton, Sebastian Schrand",
    "version": (2, 5, 1),
    "blender": (4, 2, 0),
    "location": "File > Import-Export",
    "description": "3DS Import/Export meshes, UVs, materials, textures, "
                   "cameras, lamps & animation",
    "warning": "Images must be in file folder, "
               "filenames are limited to DOS 8.3 format",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/scene_3ds.html",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    if "import_3ds" in locals():
        importlib.reload(import_3ds)
    if "export_3ds" in locals():
        importlib.reload(export_3ds)


@orientation_helper(axis_forward='Y', axis_up='Z')
class Import3DS(bpy.types.Operator, ImportHelper):
    """Import from 3DS file format (.3ds)"""
    bl_idname = "import_scene.max3ds"
    bl_label = 'Import 3DS'
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".3ds"
    filter_glob: StringProperty(default="*.3ds", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: StringProperty(subtype='DIR_PATH')

    constrain_size: FloatProperty(
        name="Constrain Size",
        description="Scale the model by 10 until it reaches the "
        "size constraint (0 to disable)",
        min=0.0, max=1000.0,
        soft_min=0.0, soft_max=1000.0,
        default=10.0,
    )
    use_scene_unit: BoolProperty(
        name="Scene Units",
        description="Convert to scene unit length settings",
        default=False,
    )
    use_center_pivot: BoolProperty(
        name="Pivot Origin",
        description="Move all geometry to pivot origin",
        default=False,
    )
    use_image_search: BoolProperty(
        name="Image Search",
        description="Search subdirectories for any associated images "
        "(Warning, may be slow)",
        default=True,
    )
    object_filter: EnumProperty(
        name="Object Filter", options={'ENUM_FLAG'},
        items=(('WORLD', "World".rjust(11), "", 'WORLD_DATA', 0x1),
               ('MESH', "Mesh".rjust(11), "", 'MESH_DATA', 0x2),
               ('LIGHT', "Light".rjust(12), "", 'LIGHT_DATA', 0x4),
               ('CAMERA', "Camera".rjust(11), "", 'CAMERA_DATA', 0x8),
               ('EMPTY', "Empty".rjust(11), "", 'EMPTY_AXIS', 0x10),
               ),
        description="Object types to import",
        default={'WORLD', 'MESH', 'LIGHT', 'CAMERA', 'EMPTY'},
    )
    use_apply_transform: BoolProperty(
        name="Apply Transform",
        description="Workaround for object transformations "
        "importing incorrectly",
        default=True,
    )
    use_keyframes: BoolProperty(
        name="Animation",
        description="Read the keyframe data",
        default=True,
    )
    use_world_matrix: BoolProperty(
        name="World Space",
        description="Transform to matrix world",
        default=False,
    )
    use_collection: BoolProperty(
        name="Collection",
        description="Create a new collection",
        default=False,
    )
    use_cursor: BoolProperty(
        name="Cursor Origin",
        description="Read the 3D cursor location",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        import_include(layout, self)
        import_transform(layout, self)

    def execute(self, context):
        from . import import_3ds
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            ))
        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return import_3ds.load(self, context, **keywords)

    def invoke(self, context, event):
        return self.invoke_popup(context)


def import_include(layout, operator):
    header, body = layout.panel("MAX3DS_import_include", default_closed=False)
    header.label(text="Include")
    if body:
        line = body.row(align=True)
        line.prop(operator, "use_image_search")
        line.label(text="", icon='OUTLINER_OB_IMAGE' if operator.use_image_search else 'IMAGE_DATA')
        body.column().prop(operator, "object_filter")
        line = body.row(align=True)
        line.prop(operator, "use_keyframes")
        line.label(text="", icon='ANIM' if operator.use_keyframes else 'DECORATE_DRIVER')
        line = body.row(align=True)
        line.prop(operator, "use_collection")
        line.label(text="", icon='OUTLINER_COLLECTION' if operator.use_collection else 'GROUP')
        line = body.row(align=True)
        line.prop(operator, "use_cursor")
        line.label(text="", icon='PIVOT_CURSOR' if operator.use_cursor else 'CURSOR')


def import_transform(layout, operator):
    header, body = layout.panel("MAX3DS_import_transform", default_closed=False)
    header.label(text="Transform")
    if body:
        body.prop(operator, "constrain_size")
        line = body.row(align=True)
        line.prop(operator, "use_scene_unit")
        line.label(text="", icon='EMPTY_ARROWS' if operator.use_scene_unit else 'EMPTY_DATA')
        line = body.row(align=True)
        line.prop(operator, "use_center_pivot")
        line.label(text="", icon='OVERLAY' if operator.use_center_pivot else 'PIVOT_ACTIVE')
        line = body.row(align=True)
        line.prop(operator, "use_apply_transform")
        line.label(text="", icon='MESH_CUBE' if operator.use_apply_transform else 'MOD_SOLIDIFY')
        line = body.row(align=True)
        line.prop(operator, "use_world_matrix")
        line.label(text="", icon='WORLD' if operator.use_world_matrix else 'META_BALL')
        body.prop(operator, "axis_forward")
        body.prop(operator, "axis_up")


@orientation_helper(axis_forward='Y', axis_up='Z')
class Export3DS(bpy.types.Operator, ExportHelper):
    """Export to 3DS file format (.3ds)"""
    bl_idname = "export_scene.max3ds"
    bl_label = 'Export 3DS'
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".3ds"
    filter_glob: StringProperty(default="*.3ds", options={'HIDDEN'})

    collection: StringProperty(
        name="Source Collection",
        description="Export objects from this collection",
        default="",
    )
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Master scale factor for all objects",
        min=0.0, max=100000.0,
        soft_min=0.0, soft_max=100000.0,
        default=1.0,
    )
    use_scene_unit: BoolProperty(
        name="Scene Units",
        description="Take the scene unit length settings into account",
        default=False,
    )
    use_selection: BoolProperty(
        name="Selection",
        description="Export selected objects only",
        default=False,
    )
    object_filter: EnumProperty(
        name="Object Filter", options={'ENUM_FLAG'},
        items=(('WORLD', "World".rjust(11), "", 'WORLD_DATA',0x1),
               ('MESH', "Mesh".rjust(11), "", 'MESH_DATA', 0x2),
               ('LIGHT', "Light".rjust(12), "", 'LIGHT_DATA',0x4),
               ('CAMERA', "Camera".rjust(11), "", 'CAMERA_DATA',0x8),
               ('EMPTY', "Empty".rjust(11), "", 'EMPTY_AXIS',0x10),
               ),
        description="Object types to export",
        default={'WORLD', 'MESH', 'LIGHT', 'CAMERA', 'EMPTY'},
    )
    use_keyframes: BoolProperty(
        name="Animation",
        description="Write the keyframe data",
        default=True,
    )
    use_hierarchy: BoolProperty(
        name="Hierarchy",
        description="Export hierarchy chunks",
        default=False,
    )
    use_collection: BoolProperty(
        name="Collection",
        description="Export active collection only",
        default=False,
    )
    use_cursor: BoolProperty(
        name="Cursor Origin",
        description="Save the 3D cursor location",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        browser = context.space_data.type == 'FILE_BROWSER'

        export_include(layout, self, browser)
        export_transform(layout, self)

    def execute(self, context):
        from . import export_3ds
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
        global_matrix = axis_conversion(to_forward=self.axis_forward,
                                        to_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return export_3ds.save(self, context, **keywords)


def export_include(layout, operator, browser):
    header, body = layout.panel("MAX3DS_export_include", default_closed=False)
    header.label(text="Include")
    if body:
        if browser:
            line = body.row(align=True)
            line.prop(operator, "use_selection")
            line.label(text="", icon='RESTRICT_SELECT_OFF' if operator.use_selection else 'RESTRICT_SELECT_ON')
        body.column().prop(operator, "object_filter")
        line = body.row(align=True)
        line.prop(operator, "use_keyframes")
        line.label(text="", icon='ANIM' if operator.use_keyframes else 'DECORATE_DRIVER')
        line = body.row(align=True)
        line.prop(operator, "use_hierarchy")
        line.label(text="", icon='OUTLINER' if operator.use_hierarchy else 'CON_CHILDOF')
        if browser:
            line = body.row(align=True)
            line.prop(operator, "use_collection")
            line.label(text="", icon='OUTLINER_COLLECTION' if operator.use_collection else 'GROUP')
        line = body.row(align=True)
        line.prop(operator, "use_cursor")
        line.label(text="", icon='PIVOT_CURSOR' if operator.use_cursor else 'CURSOR')


def export_transform(layout, operator):
    header, body = layout.panel("MAX3DS_export_transform", default_closed=False)
    header.label(text="Transform")
    if body:
        body.prop(operator, "scale_factor")
        line = body.row(align=True)
        line.prop(operator, "use_scene_unit")
        line.label(text="", icon='EMPTY_ARROWS' if operator.use_scene_unit else 'EMPTY_DATA')
        body.prop(operator, "axis_forward")
        body.prop(operator, "axis_up")


class IO_FH_3ds(bpy.types.FileHandler):
    bl_idname = "IO_FH_3ds"
    bl_label = "Autodesk 3DS"
    bl_import_operator = "import_scene.max3ds"
    bl_export_operator = "export_scene.max3ds"
    bl_file_extensions = ".3ds;.3DS"

    @classmethod
    def poll_drop(cls, context):
        return poll_file_object_drop(context)


# Add to a menu
def menu_func_export(self, context):
    self.layout.operator(Export3DS.bl_idname, text="3D Studio (.3ds)", icon='SAVE_3DS') #bfa - added icon


def menu_func_import(self, context):
    self.layout.operator(Import3DS.bl_idname, text="3D Studio (.3ds)", icon='LOAD_3DS') #bfa - added icon


def register():
    bpy.utils.register_class(Import3DS)
    bpy.utils.register_class(Export3DS)
    bpy.utils.register_class(IO_FH_3ds)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(Import3DS)
    bpy.utils.unregister_class(Export3DS)
    bpy.utils.unregister_class(IO_FH_3ds)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
