# SPDX-FileCopyrightText: 2011-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name":"Web3D X3D/VRML2 format",
    "description": "Import-Export X3D, Import VRML2",
    "author": "maintainer: Bujus_Krachus",
    "version": (2, 5, 1),
    "blender": (4, 2, 0),
    "location": "",
    "warning": "",
    "doc_url": "",
    'tracker_url': "https://projects.blender.org/extensions/io_scene_x3d",
    'support': 'COMMUNITY',
    "category": "IO",
}
bl_info_copy = bl_info.copy()


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
    CollectionProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    axis_conversion
)
from bpy.types import (
    Operator,
    OperatorFileListElement,
)
from bpy_extras.io_utils import (
    poll_file_object_drop,
)

from .translations import get_language, translate
from .prefs import X3D_Preferences

blender_version = bpy.app.version
blender_version_higher_279 = blender_version[0] > 2 or (blender_version[0] == 2 and blender_version[1] >= 79)
blender_version_higher_44 = blender_version[0] > 4 and blender_version[1] >= 4

lang = get_language()

@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportX3D(bpy.types.Operator, ImportHelper):
    """Import an X3D or VRML2 file"""
    bl_idname = "import_scene.x3d"
    bl_label = translate(lang,"import")
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".x3d"

    filter_glob: StringProperty(default="*.x3d;*.wrl;*x3dv;*.x3dz", options={'HIDDEN'})

    files: CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
    )
    directory: StringProperty(
        subtype='DIR_PATH',
    )

    def _file_unit_update(self, context):
        if self.file_unit == 'CUSTOM':
            return
        UNITS_FACTOR = {'M': 1.0, 'DM': 0.1, 'CM': 0.01, 'MM': 0.001, 'IN': 0.0254}
        self.global_scale = UNITS_FACTOR[self.file_unit]

    file_unit: EnumProperty(
        name=translate(lang, "file_unit"),
        items=(('M', translate(lang, "meter"), translate(lang, "meter_description")),
               ('DM', translate(lang,"decimeter"), translate(lang, "decimeter_description")),
               ('CM', translate(lang, "centimeter"), translate(lang, "centimeter_description")),
               ('MM', translate(lang, "milimeter"), translate(lang, "milimeter_description")),
               ('IN', translate(lang, "inch"), translate(lang, "inch_description")),
               ('CUSTOM', translate(lang, "custom"), translate(lang, "custom_description")),
               ),
        description=translate(lang, "file_unit_description"),
        default='M',
        update=_file_unit_update,
    )

    global_scale: FloatProperty(
        name=translate(lang, "scale"),
        min=0.001, max=1000.0,
        default=1.0,
        precision=4,
        step=1.0,
        description=translate(lang, "scale_description"),
    )

    as_collection: BoolProperty(
        name=translate(lang, "as_collection"),
        description=translate(lang, "as_collection_description"),
        default=False,
    )

    solidify: BoolProperty(
        name=translate(lang, "solidify"),
        description=translate(lang, "solidify_description"),
        default=False,
    )

    solidify_value: FloatProperty(
        name=translate(lang, "solidify_value"),
        min=-10.0, max=10.0,
        default=0.1,
        precision=2,
        step=1.0,
        description=translate(lang, "solidify_value_description"),
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        import_ui_general(layout, self)
        import_ui_transform(layout, self)
        import_ui_mesh(layout, self)

    def execute(self, context):
        from . import import_x3d

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "file_unit",
                                            "filter_glob",
                                            ))
        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return import_x3d.load(context, **keywords)

    def invoke(self, context, event):
        return self.invoke_popup(context)

def import_ui_general(layout, operator):
    header, body = layout.panel("IMPORT_SCENE_OT_x3d_general", default_closed=False)
    header.label(text=translate(lang, "label_general"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "as_collection")

def import_ui_transform(layout, operator):
    header, body = layout.panel("IMPORT_SCENE_OT_x3d_transform", default_closed=False)
    header.label(text=translate(lang, "label_transform"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "file_unit")

        sub = body.row(align=True)
        sub.enabled = operator.file_unit == 'CUSTOM'
        sub.prop(operator, "global_scale")

        line = body.row(align=True)
        line.prop(operator, "axis_forward")
        line = body.row(align=True)
        line.prop(operator, "axis_up")

def import_ui_mesh(layout, operator):
    header, body = layout.panel("IMPORT_SCENE_OT_x3d_mesh", default_closed=False)
    header.label(text=translate(lang, "label_mesh"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "solidify")

        sub = body.row(align=True)
        sub.enabled = operator.solidify == True
        sub.prop(operator, "solidify_value")


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ExportX3D(bpy.types.Operator, ExportHelper):
    """Export selection to Extensible 3D file (.x3d)"""
    bl_idname = "export_scene.x3d"
    bl_label = translate(lang, "export")
    bl_options = {'PRESET'}

    filename_ext = ".x3d"
    filter_glob: StringProperty(default="*.x3d", options={'HIDDEN'})

    def _batch_mode_update(self, context):
        if self.batch_mode == 'SCENE' or self.batch_mode == 'COLLECTION':
            self.use_visible = False
            self.use_selection = False
            self.use_active_collection = False
            return
    batch_mode: EnumProperty(
        name="Batch Mode",
        items=(('OFF',
                translate(lang, "batch_off"),
                translate(lang, "batch_off_description")),
               ('COLLECTION',
                translate(lang, "batch_collection"),
                translate(lang, "batch_collection_description")),
               ('OBJECT',
                translate(lang, "batch_object"),
                translate(lang, "batch_object_description")),
               ('OBJECT_HIERARCHY',
                translate(lang, "batch_object_hierarchy"),
                translate(lang, "batch_object_hierarchy_description")),
               ('SCENE',
                translate(lang, "batch_scene"),
                translate(lang, "batch_scene_description")),
               ),
        update=_batch_mode_update,
    )
    use_batch_own_dir: BoolProperty(
        name=translate(lang, "batch_dir"),
        description=translate(lang, "batch_dir_description"),
        default=False,
    )

    use_selection: BoolProperty(
        name=translate(lang, "selection_only"),
        description=translate(lang, "selection_only_description"),
        default=False,
    )
    use_visible: BoolProperty(
        name=translate(lang, "visible_only"),
        description=translate(lang, "visible_only_description"),
        default=False,
    )
    use_active_collection: BoolProperty(
        name=translate(lang, "active_collection_only"),
        description=translate(lang, "active_collection_only_description"),
        default=False,
    )
    use_mesh_modifiers: BoolProperty(
        name=translate(lang, "apply_modifiers"),
        description=translate(lang, "apply_modifiers_description"),
        default=True,
    )
    use_triangulate: BoolProperty(
        name=translate(lang, "triangulate"),
        description=translate(lang, "triangulate_description"),
        default=False,
    )
    use_normals: BoolProperty(
        name=translate(lang, "normals"),
        description=translate(lang, "normals_description"),
        default=False,
    )
    use_compress: BoolProperty(
        name=translate(lang, "compress"),
        description=translate(lang, "compress_description"),
        default=False,
    )
    use_hierarchy: BoolProperty(
        name=translate(lang, "hierarchy"),
        description=translate(lang, "hierarchy_description"),
        default=True,
    )
    name_decorations: BoolProperty(
        name=translate(lang, "name_decorations"),
        description=translate(lang, "name_decorations_description"),
        default=True,
    )

    def _h3d_update(self, context):
        """Disable h3d permanently even if set programmatically"""
        if blender_version_higher_279:
            self.use_h3d = False
    use_h3d: BoolProperty(
        name=translate(lang, "h3d_extensions"),
        description=translate(lang, "h3d_extensions_description"),
        default=False,
        update=_h3d_update,
    )

    def _file_unit_update(self, context):
        if self.file_unit == 'CUSTOM':
            return
        UNITS_FACTOR = {'M': 1.0, 'DM': 10.0, 'CM': 100.0, 'MM': 1000.0, 'IN': 1.0 / 0.0254}
        self.global_scale = UNITS_FACTOR[self.file_unit]

    file_unit: EnumProperty(
        name=translate(lang, "file_unit"),
        items=(('M', translate(lang, "meter"), translate(lang, "meter_description")),
               ('DM', translate(lang, "decimeter"), translate(lang, "decimeter_description")),
               ('CM', translate(lang, "centimeter"), translate(lang, "centimeter_description")),
               ('MM', translate(lang, "milimeter"), translate(lang, "milimeter_description")),
               ('IN', translate(lang, "inch"), translate(lang, "inch_description")),
               ('CUSTOM', translate(lang, "custom"), translate(lang, "custom_description")),
               ),
        description=translate(lang, "file_unit_description"),
        default='M',
        update=_file_unit_update,
    )

    global_scale: FloatProperty(
        name="Scale",
        min=0.01, max=1000.0,
        default=1.0,
        precision=4,
        step=1.0,
        description=translate(lang, "scale_description"),
    )

    path_mode: EnumProperty(
        name=translate(lang, "path_mode_name"),
        description= translate(lang, "path_mode_description"),
        #   A subset of the items in bpy_extras.io_utils.path_reference_mode
        items=(
            ('RELATIVE', translate(lang,"relative_mode"), translate(lang, "relative_mode_description")),
            ('STRIP', translate(lang,"strip_mode"), translate(lang, "strip_mode_description")),
            ('COPY', translate(lang, "copy_mode"), translate(lang, "copy_mode_description")),
        ),
        default='COPY',
    )

    meta_creator: StringProperty(
        name=translate(lang, "meta_creator"),
        default="",
        description=translate(lang, "meta_creator_description"),
    )
    meta_title: StringProperty(
        name=translate(lang, "meta_title"),
        default="",
        description=translate(lang, "meta_title_description"),
    )
    meta_description: StringProperty(
        name=translate(lang, "meta_description"),
        default="",
        description=translate(lang, "meta_description_description"),
    )
    meta_keywords: StringProperty(
        name=translate(lang, "meta_keywords"),
        default="",
        description=translate(lang, "meta_keywords_description"),
    )
    meta_reference: StringProperty(
        name=translate(lang, "meta_reference"),
        default="",
        description=translate(lang, "meta_reference_description"),
    )

    meta_license: EnumProperty(
        name=translate(lang, "meta_license"),
        description=translate(lang, "meta_license_description"),
        items=(('NONE',
                translate(lang, "meta_license_none"),
                translate(lang, "meta_license_none_description")),
               ('CUSTOM',
                translate(lang, "custom"),
                translate(lang, "meta_license_custom_description")),
               None, # Creative Commons (CC) Licenses
               ('CC_BY_4.0',
                translate(lang, "meta_license_CC_BY_4.0"),
                translate(lang, "meta_license_CC_BY_4.0_description")),
               ('CC_BY-SA_4.0',
                translate(lang, "meta_license_CC_BY-SA_4.0"),
                translate(lang, "meta_license_CC_BY-SA_4.0_description")),
               ('CC_BY-NC_4.0',
                translate(lang, "meta_license_CC_BY-NC_4.0"),
                translate(lang, "meta_license_CC_BY-NC_4.0_description")),
               ('CC0_1.0',
                translate(lang, "meta_license_CC0_1.0"),
                translate(lang, "meta_license_CC0_1.0_description")),
               ('CC_BY-ND_4.0',
                translate(lang, "meta_license_CC_BY-ND_4.0"),
                translate(lang, "meta_license_CC_BY-ND_4.0_description")),
                None, # Open Source & Free Culture Licenses
               ('GPL_v3',
                translate(lang, "meta_license_GPL_v3"),
                translate(lang, "meta_license_GPL_v3_description")),
               ('GPL_v2',
                translate(lang, "meta_license_GPL_v2"),
                translate(lang, "meta_license_GPL_v2_description")),
               ('LGPL_v3',
                translate(lang, "meta_license_LGPL_v3"),
                translate(lang, "meta_license_LGPL_v3_description")),
               ('LGPL_v2.1',
                translate(lang, "meta_license_LGPL_v2.1"),
                translate(lang, "meta_license_LGPL_v2.1_description")),
               ('MIT_License',
                translate(lang, "meta_license_MIT_License"),
                translate(lang, "meta_license_MIT_License_description")),
               ('MIT_No_Attribution',
                translate(lang, "meta_license_MIT_No_Attribution"),
                translate(lang, "meta_license_MIT_No_Attribution_description")),
               ('Apache_2.0',
                translate(lang, "meta_license_Apache_2.0"),
                translate(lang, "meta_license_Apache_2.0_description")),
               ('BSD_3',
                translate(lang, "meta_license_BSD_3"),
                translate(lang, "meta_license_BSD_3_description")),
               ('BSD_2',
                translate(lang, "meta_license_BSD_2"),
                translate(lang, "meta_license_BSD_2_description")),
               ('BSD_1',
                translate(lang, "meta_license_BSD_1"),
                translate(lang, "meta_license_BSD_1_description")),
               ('Mozilla_2.0',
                translate(lang, "meta_license_Mozilla_2.0"),
                translate(lang, "meta_license_Mozilla_2.0_description")),
               ('Pixar',
                translate(lang, "meta_license_Pixar"),
                translate(lang, "meta_license_Pixar_description")),
               None, # Proprietary & Commercial Licenses
               ('Standard_Royalty-Free',
                translate(lang, "meta_license_Standard_Royalty-Free"),
                translate(lang, "meta_license_Standard_Royalty-Free_description")),
               ('Extended_Commercial',
                translate(lang, "meta_license_Extended_Commercial"),
                translate(lang, "meta_license_Extended_Commercial_description")),
               None, # Public Domain & Government Licenses
               ('Public_Domain',
                translate(lang, "meta_license_Public_Domain"),
                translate(lang, "meta_license_Public_Domain_description")),
               ('Unlicense',
                translate(lang, "meta_license_Unlicense"),
                translate(lang, "meta_license_Unlicense_description")),
               ('NOSA_1.3',
                translate(lang, "meta_license_NOSA_1.3"),
                translate(lang, "meta_license_NOSA_1.3_description")),
               ),
    )

    def _meta_license_custom_update(self, context):
        if self.file_unit != 'CUSTOM':
            return
        self.license = self.meta_license_custom
    meta_license_custom: StringProperty(
        name=translate(lang, "meta_license_custom"),
        default="",
        description=translate(lang, "meta_license_custom_description"),
        update = _meta_license_custom_update,
    )

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        from . import export_x3d

        from mathutils import Matrix

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "file_unit",
                                            "global_scale",
                                            "check_existing",
                                            "filter_glob",
                                            "meta_license_custom",
                                            ))
        global_matrix = axis_conversion(to_forward=self.axis_forward,
                                        to_up=self.axis_up,
                                        ).to_4x4() @ Matrix.Scale(self.global_scale, 4)
        keywords["global_matrix"] = global_matrix
        if self.meta_license == 'CUSTOM' and self.meta_license_custom:
            keywords["meta_license"] = self.meta_license_custom

        return export_x3d.save(context, **keywords)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        export_ui_include(layout, self)
        export_ui_transform(layout, self)
        export_ui_mesh(layout, self)
        export_ui_external_resource(layout, self)
        export_ui_meta_data(layout, self)

def export_ui_include(layout, operator):
    header, body = layout.panel("EXPORT_SCENE_OT_x3d_include", default_closed=False)
    header.label(text=translate(lang, "label_include"))
    if body:
        row = body.row(align=True)
        row.prop(operator, "batch_mode")
        sub = row.row(align=True)
        sub.prop(operator, "use_batch_own_dir", text="", icon='NEWFOLDER')

        sublayout = body.column(heading="Limit to")
        sublayout.enabled = (operator.batch_mode == 'OFF' or operator.batch_mode == 'OBJECT'
                             or operator.batch_mode == 'OBJECT_HIERARCHY')
        sublayout.prop(operator, "use_selection")
        sublayout.prop(operator, "use_visible")
        sublayout.prop(operator, "use_active_collection")

        sublayout = body.column(heading="Include data")
        sublayout.enabled = True
        sublayout.prop(operator, "use_hierarchy")
        sublayout.prop(operator, "name_decorations")
        # keeping h3d disabled for now as the underlying gpu.export_shader() got removed since 2.80
        # see https://projects.blender.org/blender/blender-addons/issues/79991 for details
        # when readding it, don't forget to change the description
        # layout.prop(operator, "use_h3d")
        col = body.column()
        col.enabled = not blender_version_higher_279
        col.prop(operator, "use_h3d")

def export_ui_transform(layout, operator):
    header, body = layout.panel("EXPORT_SCENE_OT_x3d_transform", default_closed=False)
    header.label(text=translate(lang, "label_transform"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "file_unit")

        sub = body.row(align=True)
        sub.enabled = operator.file_unit == 'CUSTOM'
        sub.prop(operator, "global_scale")

        line = body.row(align=True)
        line.prop(operator, "axis_forward")
        line = body.row(align=True)
        line.prop(operator, "axis_up")

def export_ui_mesh(layout, operator):
    header, body = layout.panel("EXPORT_SCENE_OT_x3d_geometry", default_closed=False)
    header.label(text=translate(lang, "label_geometry"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "use_mesh_modifiers")
        line = body.row(align=True)
        line.prop(operator, "use_triangulate")
        line = body.row(align=True)
        line.prop(operator, "use_normals")
        line = body.row(align=True)
        line.prop(operator, "use_compress")

def export_ui_external_resource(layout, operator):
    header, body = layout.panel("EXPORT_SCENE_OT_x3d_external_resource", default_closed=False)
    header.label(text=translate(lang, "label_media"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "path_mode")

def export_ui_meta_data(layout, operator):
    header, body = layout.panel("EXPORT_SCENE_OT_x3d_meta_data", default_closed=True)
    header.label(text=translate(lang, "label_meta_data"))
    if body:
        line = body.row(align=True)
        line.prop(operator, "meta_creator")
        line = body.row(align=True)
        line.prop(operator, "meta_title")
        line = body.row(align=True)
        line.prop(operator, "meta_description")
        line = body.row(align=True)
        line.prop(operator, "meta_keywords")
        line = body.row(align=True)
        line.prop(operator, "meta_reference")
        line = body.row(align=True)
        line.prop(operator, "meta_license")

        sub = body.row(align=True)
        sub.enabled = operator.meta_license == 'CUSTOM'
        sub.prop(operator, "meta_license_custom")


class IO_FH_X3D(bpy.types.FileHandler):
    """File Handler for drag drop import of x3d files"""
    bl_idname = "IO_FH_x3d"
    bl_label = "X3D"
    bl_import_operator = "import_scene.x3d"
    bl_export_operator = "export_scene.x3d"
    bl_file_extensions = ".x3d;.wrl;.x3dv;.x3dz"
    # officially supported: .x3d; .wrl; .x3dz
    # partially supported: .x3dv (gets parsed as vrml and thus may not fully work)

    @classmethod
    def poll_drop(cls, context):
        return poll_file_object_drop(context)


def menu_func_import(self, context):
    self.layout.operator(ImportX3D.bl_idname,
                         text="X3D Extensible 3D (.x3d/.wrl)")

def menu_func_export(self, context):
    self.layout.operator(ExportX3D.bl_idname,
                         text="X3D Extensible 3D (.x3d)")


classes = (
    ExportX3D,
    ImportX3D,
    IO_FH_X3D,
    X3D_Preferences
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
