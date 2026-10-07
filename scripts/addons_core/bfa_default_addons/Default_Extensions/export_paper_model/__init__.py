# This script is Free software. Please share and reuse.
# ♡2010-2025 Adam Dominec <adominec@gmail.com>

bl_info = {
    "name": "Export Paper Model",
    "author": "Addam Dominec",
    "version": (1, 4, 2),
    "blender": (5, 0, 0),
    "location": "File > Export > Paper Model",
    "warning": "",
    "description": "Export printable net of the active mesh",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/paper_model.html",
    "category": "Import-Export",
}


# TODO:
# QuickSweepline is very much broken -- it throws GeometryError for all nets > ~15 faces

# check conflicts in island naming and either:
# * append a number to the conflicting names or
# * enumerate faces uniquely within all islands of the same name (requires a check that both label and abbr. equals)


import bpy
from . import unfold_operator


def factory_update_addon_category(cls, prop):
    def func(self, context):
        print(self, type(self))
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        cls.bl_category = getattr(self, prop)
        bpy.utils.register_class(cls)
    return func


class PaperAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    unfold_category: bpy.props.StringProperty(
        name="Unfold Panel Category", description="Category in 3D View Toolbox where the Unfold panel is displayed",
        default="Paper", update=factory_update_addon_category(unfold_operator.VIEW3D_PT_paper_model_tools, 'unfold_category'))
    export_category: bpy.props.StringProperty(
        name="Export Panel Category", description="Category in 3D View Toolbox where the Export panel is displayed",
        default="Paper", update=factory_update_addon_category(unfold_operator.VIEW3D_PT_paper_model_settings, 'export_category'))

    def draw(self, context):
        sub = self.layout.column(align=True)
        sub.use_property_split = True
        sub.label(text="3D View Panel Category:")
        sub.prop(self, "unfold_category", text="Unfold Panel:")
        sub.prop(self, "export_category", text="Export Panel:")


module_classes = (
    unfold_operator.Unfold,
    unfold_operator.ExportPaperModel,
    unfold_operator.ClearAllSeams,
    unfold_operator.SelectIsland,
    unfold_operator.FaceList,
    unfold_operator.IslandList,
    unfold_operator.PaperModelSettings,
    unfold_operator.DATA_PT_paper_model_islands,
    unfold_operator.VIEW3D_PT_paper_model_tools,
    unfold_operator.VIEW3D_PT_paper_model_settings,
    PaperAddonPreferences,
)


def register():
    for cls in module_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.paper_model = bpy.props.PointerProperty(
        name="Paper Model", description="Settings of the Export Paper Model script",
        type=unfold_operator.PaperModelSettings, options={'SKIP_SAVE'})
    bpy.types.Mesh.paper_island_list = bpy.props.CollectionProperty(
        name="Island List", type=unfold_operator.IslandList)
    bpy.types.Mesh.paper_island_index = bpy.props.IntProperty(
        name="Island List Index",
        default=-1, min=-1, max=100, options={'SKIP_SAVE'}, update=unfold_operator.island_index_changed)
    bpy.types.TOPBAR_MT_file_export.append(unfold_operator.menu_func_export)
    bpy.types.VIEW3D_MT_edit_mesh.prepend(unfold_operator.menu_func_unfold)
    # Force an update on the panel category properties
    prefs = bpy.context.preferences.addons[__name__].preferences
    prefs.unfold_category = prefs.unfold_category
    prefs.export_category = prefs.export_category


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(unfold_operator.menu_func_export)
    bpy.types.VIEW3D_MT_edit_mesh.remove(unfold_operator.menu_func_unfold)
    del bpy.types.Scene.paper_model
    del bpy.types.Mesh.paper_island_list
    del bpy.types.Mesh.paper_island_index
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)
