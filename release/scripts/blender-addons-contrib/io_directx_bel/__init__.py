# Blender directX importer
bl_info = {
    "name": "DirectX Importer",
    "description": "Import directX Model Format (.x)",
    "author": "Littleneo (Jerome Mahieux)",
    "version": (0, 18),
    "blender": (2, 63, 0),
    "location": "File > Import > DirectX (.x)",
    "warning": "",
    "wiki_url": "https://github.com/littleneo/directX_blender/wiki",
    "tracker_url": "https://github.com/littleneo/directX_blender/issues",
    "category": "Import-Export",
    "dependencies": ""
}

if "bpy" in locals():
    import imp
    if "import_x" in locals():
        imp.reload(import_x)
    #if "export_x" in locals():
    #    imp.reload(export_x)


import bpy
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import (ExportHelper,
                                 ImportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )
try : import bel
except : import io_directx_bel.bel

class ImportX(bpy.types.Operator, ImportHelper):
    '''Load a Direct x File'''
    bl_idname = "import_scene.x"
    bl_label = "Import X"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".x"
    filter_glob = StringProperty(
            default="*.x",
            options={'HIDDEN'},
            )
    show_tree = BoolProperty(
            name="Show x tokens tree",
            description="display relationships between x items in the console",
            default=False,
            )
    show_templates = BoolProperty(
            name="Show x templates",
            description="display templates defined in the .x file",
            default=False,
            )
    show_geninfo = BoolProperty(
            name="Show processing",
            description="display details for each imported thing",
            default=False,
            )

    quickmode = BoolProperty(
            name="Quick mode",
            description="only retrieve mesh basics",
            default=False,
            )

    parented = BoolProperty(
            name="Object Relationships",
            description="import armatures, empties, rebuild parent-childs relations",
            default=True,
            )

    bone_maxlength = FloatProperty(
            name="Bone length",
            description="Bones max length",
            min=0.1, max=10.0,
            soft_min=0.1, soft_max=10.0,
            default=1.0,
            )

    chunksize = EnumProperty(
            name="Chunksize",
            items=(('0', "all", ""),
                   ('4096', "4KB", ""),
                   ('2048', "2KB", ""),
                   ('1024', "1KB", ""),
                   ),
            default='2048',
            description="number of bytes red in a row",
            )
    naming_method = EnumProperty(
            name="Naming method",
            items=(('0', "increment name if exists", "blender default"),
                   ('1', "use existing", "this only append new elements"),
                   ('2', "rename existing", "names are forced"),
                   ('3', "replace existing", ""),
                   ),
            default='0',
            description="behaviour when a name already exists in Blender Data",
            )
    use_ngons = BoolProperty(
            name="NGons",
            description="Import faces with more than 4 verts as fgons",
            default=True,
            )
    use_edges = BoolProperty(
            name="Lines",
            description="Import lines and faces with 2 verts as edge",
            default=True,
            )
    use_smooth_groups = BoolProperty(
            name="Smooth Groups",
            description="Surround smooth groups by sharp edges",
            default=True,
            )

    use_split_objects = BoolProperty(
            name="Object",
            description="Import OBJ Objects into Blender Objects",
            default=True,
            )
    use_split_groups = BoolProperty(
            name="Group",
            description="Import OBJ Groups into Blender Objects",
            default=True,
            )

    use_groups_as_vgroups = BoolProperty(
            name="Poly Groups",
            description="Import OBJ groups as vertex groups",
            default=False,
            )

    use_image_search = BoolProperty(
            name="Image Search",
            description="Search subdirs for any assosiated images " \
                        "(Warning, may be slow)",
            default=True,
            )

    split_mode = EnumProperty(
            name="Split",
            items=(('ON', "Split", "Split geometry, omits unused verts"),
                   ('OFF', "Keep Vert Order", "Keep vertex order from file"),
                   ),
            )

    global_clamp_size = FloatProperty(
            name="Clamp Scale",
            description="Clamp the size to this maximum (Zero to Disable)",
            min=0.0, max=1000.0,
            soft_min=0.0, soft_max=1000.0,
            default=0.0,
            )

    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "Left (x)", ""),
                   ('Y', "Same (y)", ""),
                   ('Z', "Bottom (z)", ""),
                   ('-X', "Right (-x)", ""),
                   ('-Y', "Back (-y)", ""),
                   ('-Z', "Up (-z)", ""),
                   ),
            default='-Z',
            )

    axis_up = EnumProperty(
            name="Up",
            items=(('X', "Right (x)", ""),
                   ('Y', "Back (y)", ""),
                   ('Z', "Same (z)", ""),
                   ('-X', "Left (-x)", ""),
                   ('-Y', "Front (-y)", ""),
                   ('-Z', "Bottom (-z)", ""),
                   ),
            default='Y',
            )

    def execute(self, context):
        from . import import_x
        if self.split_mode == 'OFF':
            self.use_split_objects = False
            self.use_split_groups = False
        else:
            self.use_groups_as_vgroups = False

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "split_mode",
                                            ))

        keywords["naming_method"] = int(self.naming_method)

        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix


        bel.fs.saveOptions(self,'import_scene.x', self.as_keywords(ignore=(
                                            "filter_glob",
                                            "filepath",
                                            )))
        return import_x.load(self, context, **keywords)

    def draw(self, context):
        layout = self.layout

        # import box
        box = layout.box()
        col = box.column(align=True)
        col.label('Import Options :')
        col.prop(self, "chunksize")
        col.prop(self, "use_smooth_groups")
        actif = not(self.quickmode)
        row = col.row()
        row.enabled = actif
        row.prop(self, "parented")
        if self.parented :
            row = col.row()
            row.enabled = actif
            row.prop(self, "bone_maxlength")
        col.prop(self, "quickmode")

        # source orientation box
        box = layout.box()
        col = box.column(align=True)
        col.label('Source Orientation :')
        col.prop(self, "axis_forward")
        col.prop(self, "axis_up")

        # naming methods box
        box = layout.box()
        col = box.column(align=True)
        col.label('Naming Method :')
        col.props_enum(self,"naming_method")

        # info/debug box
        box = layout.box()
        col = box.column(align=True)
        col.label('Info / Debug :')
        col.prop(self, "show_tree")
        col.prop(self, "show_templates")
        col.prop(self, "show_geninfo")

        #row = layout.row(align=True)
        #row.prop(self, "use_ngons")
        #row.prop(self, "use_edges")

        '''
        box = layout.box()
        row = box.row()
        row.prop(self, "split_mode", expand=True)

        row = box.row()
        if self.split_mode == 'ON':
            row.label(text="Split by:")
            row.prop(self, "use_split_objects")
            row.prop(self, "use_split_groups")
        else:
            row.prop(self, "use_groups_as_vgroups")

        row = layout.split(percentage=0.67)
        row.prop(self, "global_clamp_size")

        layout.prop(self, "use_image_search")
        '''

def menu_func_import(self, context):
    self.layout.operator(ImportX.bl_idname, text="DirectX (.x)")

#def menu_func_export(self, context):
#    self.layout.operator(ExportX.bl_idname, text="DirectX (.x)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    #bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    #bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()