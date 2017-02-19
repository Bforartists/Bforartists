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

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


#import python stuff


# import io_scene_fpx stuff
from io_scene_fpx.fpx_strings import (
        fpx_str,
        )
#from io_scene_fpx.fpx_spec import ()
from io_scene_fpx.fpx_utils import (
        FpxUtilities,
        )


#import blender stuff
from bpy.utils import (
        register_class,
        unregister_class,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        )
from bpy.props import (
        BoolProperty,
        CollectionProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        )
from bpy.types import (
        Operator,
        PropertyGroup,
        Panel,
        Object,
        UIList,
        )
from bpy.app import (
        debug,
        )


from addon_utils import (
        check,
        )


class FpxUI:
    VERBOSE_MODE_NONE = 'NONE'
    VERBOSE_MODE_NORMAL = 'NORMAL'
    VERBOSE_MODE_MAXIMAL = 'MAXIMAL'

    VERBOSE_NONE = {}
    VERBOSE_NORMAL = { VERBOSE_MODE_NORMAL, VERBOSE_MODE_MAXIMAL, }
    VERBOSE_MAXIMAL = { VERBOSE_MODE_MAXIMAL, }

    DEFAULT_VERBOSE = VERBOSE_MODE_NONE

    ###########################################################################
    PROP_DEFAULT_RESOLUTION_WIRE_BEVEL = 8
    PROP_DEFAULT_RESOLUTION_WIRE = 8
    PROP_DEFAULT_RESOLUTION_RUBBER_BEVEL = 8
    PROP_DEFAULT_RESOLUTION_RUBBER = 8
    PROP_DEFAULT_RESOLUTION_SHAPE = 8
    PROP_DEFAULT_CONVERT_TO_MESH = True
    PROP_DEFAULT_USE_HERMITE_HANDLE = True

    ###########################################################################
    ICON_OPTIONS = 'LAMP'
    ICON_EXTERNAL_DATA = 'EXTERNAL_DATA'
    ICON_ERROR = 'ERROR'
    ICON_MODEL = "OBJECT_DATA"
    ICON_TABLE = "IMPORT"

    ###########################################################################
    PROP_DEFAULT_VERBOSE = DEFAULT_VERBOSE

    PROP_DEFAULT_SCENE = False
    PROP_DEFAULT_ALL_MODELS = False
    PROP_DEFAULT_MODEL_ADJUST_FPM = False
    PROP_DEFAULT_MODEL_ADJUST_FPL = True
    PROP_DEFAULT_MODEL_ADJUST_FPT = True
    PROP_DEFAULT_NAME_EXTRA = None

    PROP_DEFAULT_LIBRARIES_PATH = "C:\\Games\\Future Pinball\\Libraries"
    PROP_DEFAULT_DMDFONTS_PATH = "C:\\Games\\Future Pinball\\DmdFonts"
    PROP_DEFAULT_TABLES_PATH = "C:\\Games\\Future Pinball\\Tables"

    USE_MODEL_FILTER_SECONDARY = 'SECONDARY'
    USE_MODEL_FILTER_REFLECTION = 'REFLECTION'
    USE_MODEL_FILTER_MASK = 'MASK'
    USE_MODEL_FILTER_COLLISION = 'COLLISION'
    #PROP_DEFAULT_USE_MODEL_FILTER = { USE_MODEL_FILTER_SECONDARY, USE_MODEL_FILTER_REFLECTION, USE_MODEL_FILTER_MASK, USE_MODEL_FILTER_COLLISION, }
    PROP_DEFAULT_USE_MODEL_FILTER = { USE_MODEL_FILTER_MASK, }
    #PROP_DEFAULT_USE_MODEL_FILTER = set()

    USE_LIBRARY_FILTER_DMDFONT = 'DMDFONT'
    USE_LIBRARY_FILTER_GRAPHIC = 'GRAPHIC'
    USE_LIBRARY_FILTER_MODEL = 'MODEL'
    USE_LIBRARY_FILTER_MUSIC = 'MUSIC'
    USE_LIBRARY_FILTER_SCRIPT = 'SCRIPT'
    USE_LIBRARY_FILTER_SOUND = 'SOUND'
    #PROP_DEFAULT_USE_LIBRARY_FILTER = { USE_LIBRARY_FILTER_DMDFONT, USE_LIBRARY_FILTER_GRAPHIC, USE_LIBRARY_FILTER_MODEL, USE_LIBRARY_FILTER_MUSIC, USE_LIBRARY_FILTER_SCRIPT, USE_LIBRARY_FILTER_SOUND, }
    PROP_DEFAULT_USE_LIBRARY_FILTER = { USE_LIBRARY_FILTER_MODEL, USE_LIBRARY_FILTER_GRAPHIC, }

    PROP_DEFAULT_ALL_LIBRARIES = False

    PROP_DEFAULT_KEEP_TEMP = False

def NotImplemented(layout):
    box = layout.box()
    box.label(fpx_str['LABEL_NAME_NOT_IMPLEMENTED'], icon='ERROR')
    flow = box.column_flow()
    flow.label(fpx_str['LABEL_NAME_NOT_IMPLEMENTED_1'])
    flow.label(fpx_str['LABEL_NAME_NOT_IMPLEMENTED_2'])

###############################################################################
class FptEmptyItemProperties(PropertyGroup):
    prop = StringProperty(
            default="",
            #options={'HIDDEN', },
            )
    model = StringProperty(
            default="",
            #options={'HIDDEN', },
            )

class FptEmptyProperties(PropertyGroup):
    name = StringProperty(
            name=fpx_str['PROP_NAME_EMPTY_PROP_NAME'],
            description=fpx_str['PROP_DESC_EMPTY_PROP_NAME'],
            default="",
            #options={'HIDDEN', },
            )

    id = StringProperty(
            name=fpx_str['PROP_NAME_EMPTY_PROP_ID'],
            description=fpx_str['PROP_DESC_EMPTY_PROP_ID'],
            default="",
            #options={'HIDDEN', },
            )

    models = CollectionProperty(
            type=FptEmptyItemProperties,
            #options={'HIDDEN', },
            )

    selected_model_index = IntProperty(
            default=-1,
            min=-1,
            options={'HIDDEN', 'SKIP_SAVE', },
            )

    def add_model(self, prop, model):
        selected_model_index = len(self.models)
        item = self.models.add()
        item.prop = prop
        item.model = model


class FptEmptyUILise(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT', }:
            layout.label(text=item.model, icon_value=icon)
        elif self.layout_type in {'GRID', }:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class FptEmptyPanel(Panel):
    bl_label = fpx_str['LABEL_EMPTY_PANEL']
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, blender_context):
        return (blender_context
                and blender_context.object.type in {'EMPTY', }
                and blender_context.object.fpt is not None
                and blender_context.object.fpt.name
                )

    def draw_header(self, blender_context):
        layout = self.layout
        layout.label(icon='PLUGIN')

    def draw(self, blender_context):
        import bpy
        layout = self.layout
        custom_data = blender_context.object.fpt

        col = layout.column()
        col.prop(custom_data, 'name', icon='SCENE_DATA', text="")
        col.prop(custom_data, 'id', icon='OBJECT_DATA', text="")
        col.template_list(
                listtype_name='FptEmptyUILise',
                dataptr=custom_data,
                propname='models',
                active_dataptr=custom_data,
                active_propname='selected_model_index',
                rows=2,
                type='DEFAULT',
                )
        layout.enabled = False



###############################################################################
class FpmImportOperator(Operator, ImportHelper):
    """ Load a Future Pinball Model FPM File """
    bl_idname = 'import_scene.fpm'
    bl_label = fpx_str['BL_LABEL_IMPORTER_FPM']
    bl_description = fpx_str['BL_DESCRIPTION_IMPORTER_FPM']
    bl_options = {'PRESET', }
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filepath = StringProperty(
            subtype='FILE_PATH',
            options={'HIDDEN', }
            )


    verbose = EnumProperty(
            name=fpx_str['PROP_NAME_VERBOSE'],
            description=fpx_str['PROP_DESC_VERBOSE'],
            items=( (FpxUI.VERBOSE_MODE_NONE,
                            fpx_str['ENUM_VERBOSE_NONE_1'],
                            fpx_str['ENUM_VERBOSE_NONE_2'],
                            ),
                    (FpxUI.VERBOSE_MODE_NORMAL,
                            fpx_str['ENUM_VERBOSE_NORMAL_1'],
                            fpx_str['ENUM_VERBOSE_NORMAL_2'],
                            ),
                    (FpxUI.VERBOSE_MODE_MAXIMAL,
                            fpx_str['ENUM_VERBOSE_MAXIMALIMAL_1'],
                            fpx_str['ENUM_VERBOSE_MAXIMALIMAL_2'],
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_VERBOSE,
            )

    keep_temp = BoolProperty(
            name=fpx_str['PROP_NAME_KEEP_TEMP'],
            description=fpx_str['PROP_DESC_KEEP_TEMP'],
            default=FpxUI.PROP_DEFAULT_KEEP_TEMP,
            )


    use_all_models_of_folder = BoolProperty(
            name=fpx_str['PROP_NAME_ALL_MODELS'],
            description=fpx_str['PROP_DESC_ALL_MODELS'],
            default=FpxUI.PROP_DEFAULT_ALL_MODELS,
            )

    use_scene_per_model = BoolProperty(
            name=fpx_str['PROP_NAME_SCENE'],
            description=fpx_str['PROP_DESC_SCENE'],
            default=FpxUI.PROP_DEFAULT_SCENE,
            )

    name_extra = StringProperty(
            #options={'HIDDEN', },
            )


    use_model_filter = EnumProperty(
            name=fpx_str['PROP_NAME_USE_MODEL_FILTER'],
            description=fpx_str['PROP_DESC_USE_MODEL_FILTER'],
            items=(
                    (FpxUI.USE_MODEL_FILTER_SECONDARY,
                            fpx_str['PROP_NAME_MODEL_SECONDARY'],
                            fpx_str['PROP_DESC_MODEL_SECONDARY'],
                            'MESH_CUBE',
                            1,
                            ),
                    (FpxUI.USE_MODEL_FILTER_REFLECTION,
                            fpx_str['PROP_NAME_MODEL_REFLECTION'],
                            fpx_str['PROP_DESC_MODEL_REFLECTION'],
                            'MOD_MIRROR',
                            2,
                            ),
                    (FpxUI.USE_MODEL_FILTER_MASK,
                            fpx_str['PROP_NAME_MODEL_MASK'],
                            fpx_str['PROP_DESC_MODEL_MASK'],
                            'MOD_MASK',
                            4,
                            ),
                    (FpxUI.USE_MODEL_FILTER_COLLISION,
                            fpx_str['PROP_NAME_MODEL_COLLISION'],
                            fpx_str['PROP_DESC_MODEL_COLLISION'],
                            'MOD_PHYSICS',
                            8,
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_USE_MODEL_FILTER,
            options={'ENUM_FLAG', },
            )

    use_model_adjustment = BoolProperty(
            name=fpx_str['PROP_NAME_MODEL_ADJUST'],
            description=fpx_str['PROP_DESC_MODEL_ADJUST'],
            default=FpxUI.PROP_DEFAULT_MODEL_ADJUST_FPM,
            )


    filename_ext = fpx_str['FILE_EXT_FPM']

    filter_glob = StringProperty(
            default=fpx_str['FILE_FILTER_FPM'],
            options={'HIDDEN', }
            )

    # check add-on dependency
    @classmethod
    def poll(cls, blender_context):
        loaded_default, loaded_state = check("io_scene_ms3d")
        return loaded_state

    # draw the option panel
    def draw(self, blender_context):
        layout = self.layout

        box = layout.box()
        box.label(fpx_str['LABEL_NAME_OPTIONS'], icon=FpxUI.ICON_OPTIONS)
        flow = box.column_flow()
        flow.prop(self, 'verbose', icon='SPEAKER')
        flow = box.column_flow()
        flow.prop(self, 'keep_temp', icon='GHOST')
        flow.prop(self, 'use_all_models_of_folder', icon='FILE_FOLDER')
        flow.prop(self, 'use_scene_per_model', icon='SCENE_DATA')
        flow.prop(self, 'name_extra', icon='TEXT', text="")

        FpmImportOperator.draw_model_options(self, layout)

    # entrypoint for FPM -> blender
    def execute(self, blender_context):
        """ start executing """

        FpxUtilities.set_scene_to_default(blender_context.scene)

        from io_scene_fpx.fpx_import import (FpmImporter, )
        FpmImporter(
                report=self.report,
                verbose=self.verbose,
                keep_temp=self.keep_temp,
                use_all_models_of_folder=self.use_all_models_of_folder,
                use_scene_per_model=self.use_scene_per_model,
                name_extra=self.name_extra,
                use_model_filter=self.use_model_filter,
                use_model_adjustment=self.use_model_adjustment,
                ).read(
                        blender_context,
                        self.filepath,
                        )

        FpxUtilities.set_scene_to_metric(blender_context)

        for scene in blender_context.blend_data.scenes:
            scene.layers = (True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
            scene.update()

        return {"FINISHED"}

    def invoke(self, blender_context, event):
        blender_context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL', }

    @staticmethod
    def menu_func(cls, blender_context):
        cls.layout.operator(
                FpmImportOperator.bl_idname,
                text=fpx_str['TEXT_OPERATOR_FPM'],
                )

    @staticmethod
    def draw_model_options(cls, layout):
        box = layout.box()
        box.label(fpx_str['LABEL_NAME_MODEL_OPTIONS'], icon=FpxUI.ICON_MODEL)
        if FpxUI.USE_MODEL_FILTER_COLLISION in cls.use_model_filter:
            NotImplemented(box)
        flow = box.column_flow()
        flow.prop(cls, 'use_model_filter', icon='FILTER')
        flow = box.column_flow()
        flow.prop(cls, 'use_model_adjustment', icon='MODIFIER')

###############################################################################
class FplImportOperator(Operator, ImportHelper):
    """ Load a Future Pinball Library FPL File """
    bl_idname = 'import_scene.fpl'
    bl_label = fpx_str['BL_LABEL_IMPORTER_FPL']
    bl_description = fpx_str['BL_DESCRIPTION_IMPORTER_FPL']
    bl_options = {'PRESET', }
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filepath = StringProperty(
            subtype='FILE_PATH',
            options={'HIDDEN', }
            )


    verbose = EnumProperty(
            name=fpx_str['PROP_NAME_VERBOSE'],
            description=fpx_str['PROP_DESC_VERBOSE'],
            items=( (FpxUI.VERBOSE_MODE_NONE,
                            fpx_str['ENUM_VERBOSE_NONE_1'],
                            fpx_str['ENUM_VERBOSE_NONE_2'],
                            ),
                    (FpxUI.VERBOSE_MODE_NORMAL,
                            fpx_str['ENUM_VERBOSE_NORMAL_1'],
                            fpx_str['ENUM_VERBOSE_NORMAL_2'],
                            ),
                    (FpxUI.VERBOSE_MODE_MAXIMAL,
                            fpx_str['ENUM_VERBOSE_MAXIMALIMAL_1'],
                            fpx_str['ENUM_VERBOSE_MAXIMALIMAL_2'],
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_VERBOSE,
            )

    keep_temp = BoolProperty(
            name=fpx_str['PROP_NAME_KEEP_TEMP'],
            description=fpx_str['PROP_DESC_KEEP_TEMP'],
            default=FpxUI.PROP_DEFAULT_KEEP_TEMP,
            )


    use_all_libraries_of_folder = BoolProperty(
            name=fpx_str['PROP_NAME_ALL_LIBRARIES'],
            description=fpx_str['PROP_DESC_ALL_LIBRARIES'],
            default=FpxUI.PROP_DEFAULT_ALL_LIBRARIES,
            )

    use_library_filter = EnumProperty(
            name=fpx_str['PROP_NAME_USE_LIBRARY_FILTER'],
            description=fpx_str['PROP_DESC_USE_LIBRARY_FILTER'],
            items=(
                    (FpxUI.USE_LIBRARY_FILTER_MODEL,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MODEL_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MODEL_2'],
                            'FILE_BLEND',
                            1,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_GRAPHIC,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_GRAPHIC_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_GRAPHIC_2'],
                            'FILE_IMAGE',
                            2,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_DMDFONT,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_DMDFONT_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_DMDFONT_2'],
                            'FILE_FONT',
                            4,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_SOUND,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SOUND_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SOUND_2'],
                            'FILE_SOUND',
                            8,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_MUSIC,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MUSIC_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MUSIC_2'],
                            'FILE_MOVIE',
                            16,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_SCRIPT,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SCRIPT_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SCRIPT_2'],
                            'FILE_SCRIPT',
                            32,
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_USE_LIBRARY_FILTER,
            options={'ENUM_FLAG', },
            )

    use_model_filter = EnumProperty(
            name=fpx_str['PROP_NAME_USE_MODEL_FILTER'],
            description=fpx_str['PROP_DESC_USE_MODEL_FILTER'],
            items=(
                    (FpxUI.USE_MODEL_FILTER_SECONDARY,
                            fpx_str['PROP_NAME_MODEL_SECONDARY'],
                            fpx_str['PROP_DESC_MODEL_SECONDARY'],
                            'MESH_CUBE',
                            1,
                            ),
                    (FpxUI.USE_MODEL_FILTER_REFLECTION,
                            fpx_str['PROP_NAME_MODEL_REFLECTION'],
                            fpx_str['PROP_DESC_MODEL_REFLECTION'],
                            'MOD_MIRROR',
                            2,
                            ),
                    (FpxUI.USE_MODEL_FILTER_MASK,
                            fpx_str['PROP_NAME_MODEL_MASK'],
                            fpx_str['PROP_DESC_MODEL_MASK'],
                            'MOD_MASK',
                            4,
                            ),
                    (FpxUI.USE_MODEL_FILTER_COLLISION,
                            fpx_str['PROP_NAME_MODEL_COLLISION'],
                            fpx_str['PROP_DESC_MODEL_COLLISION'],
                            'MOD_PHYSICS',
                            8,
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_USE_MODEL_FILTER,
            options={'ENUM_FLAG', },
            )

    use_model_adjustment = BoolProperty(
            name=fpx_str['PROP_NAME_MODEL_ADJUST'],
            description=fpx_str['PROP_DESC_MODEL_ADJUST'],
            default=FpxUI.PROP_DEFAULT_MODEL_ADJUST_FPL,
            )


    filename_ext = fpx_str['FILE_EXT_FPL']

    filter_glob = StringProperty(
            default=fpx_str['FILE_FILTER_FPL'],
            options={'HIDDEN', }
            )

    # check add-on dependency
    @classmethod
    def poll(cls, blender_context):
        loaded_default, loaded_state = check("io_scene_ms3d")
        return loaded_state

    # draw the option panel
    def draw(self, blender_context):
        layout = self.layout

        box = layout.box()
        box.label(fpx_str['LABEL_NAME_OPTIONS'], icon=FpxUI.ICON_OPTIONS)
        flow = box.column_flow()
        flow.prop(self, 'verbose', icon='SPEAKER')
        flow = box.column_flow()
        flow.prop(self, 'keep_temp', icon='GHOST')
        flow.prop(self, 'use_all_libraries_of_folder', icon='FILE_FOLDER')

        FplImportOperator.draw_library_options(self, layout)
        FpmImportOperator.draw_model_options(self, layout)

    # entrypoint for FPL -> blender
    def execute(self, blender_context):
        """ start executing """

        FpxUtilities.set_scene_to_default(blender_context.scene)

        from io_scene_fpx.fpx_import import (FplImporter, )
        FplImporter(
                report=self.report,
                verbose=self.verbose,
                keep_temp=self.keep_temp,
                use_all_libraries_of_folder=self.use_all_libraries_of_folder,
                use_library_filter=self.use_library_filter,
                use_model_filter=self.use_model_filter,
                use_model_adjustment=self.use_model_adjustment,
                ).read(
                        blender_context,
                        self.filepath,
                        )

        FpxUtilities.set_scene_to_metric(blender_context)

        for scene in blender_context.blend_data.scenes:
            scene.layers = (True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
            scene.update()

        return {"FINISHED"}

    def invoke(self, blender_context, event):
        blender_context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL', }

    @staticmethod
    def menu_func(cls, blender_context):
        cls.layout.operator(
                FplImportOperator.bl_idname,
                text=fpx_str['TEXT_OPERATOR_FPL'],
                )

    @staticmethod
    def draw_library_options(cls, layout):
        box = layout.box()
        box.label(fpx_str['LABEL_NAME_LIBRARYL_OPTIONS'], icon='IMPORT')
        if FpxUI.USE_LIBRARY_FILTER_DMDFONT in cls.use_library_filter \
                or FpxUI.USE_LIBRARY_FILTER_SOUND in cls.use_library_filter \
                or FpxUI.USE_LIBRARY_FILTER_MUSIC in cls.use_library_filter \
                or FpxUI.USE_LIBRARY_FILTER_SCRIPT in cls.use_library_filter:
            NotImplemented(box)
        flow = box.column_flow()
        flow.prop(cls, 'use_library_filter', icon='FILTER')


###############################################################################
class FptImportOperator(Operator, ImportHelper):
    """ Load a Future Pinball Table FPT File """
    bl_idname = 'import_scene.fpt'
    bl_label = fpx_str['BL_LABEL_IMPORTER_FPT']
    bl_description = fpx_str['BL_DESCRIPTION_IMPORTER_FPT']
    bl_options = {'PRESET', }
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filepath = StringProperty(
            subtype='FILE_PATH',
            options={'HIDDEN', }
            )


    verbose = EnumProperty(
            name=fpx_str['PROP_NAME_VERBOSE'],
            description=fpx_str['PROP_DESC_VERBOSE'],
            items=( (FpxUI.VERBOSE_MODE_NONE,
                            fpx_str['ENUM_VERBOSE_NONE_1'],
                            fpx_str['ENUM_VERBOSE_NONE_2'],
                            ),
                    (FpxUI.VERBOSE_MODE_NORMAL,
                            fpx_str['ENUM_VERBOSE_NORMAL_1'],
                            fpx_str['ENUM_VERBOSE_NORMAL_2'],
                            ),
                    (FpxUI.VERBOSE_MODE_MAXIMAL,
                            fpx_str['ENUM_VERBOSE_MAXIMALIMAL_1'],
                            fpx_str['ENUM_VERBOSE_MAXIMALIMAL_2'],
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_VERBOSE,
            )

    keep_temp = BoolProperty(
            name=fpx_str['PROP_NAME_KEEP_TEMP'],
            description=fpx_str['PROP_DESC_KEEP_TEMP'],
            default=FpxUI.PROP_DEFAULT_KEEP_TEMP,
            )


    path_libraries = StringProperty(
            name=fpx_str['PROP_NAME_LIBRARIES_PATH'],
            description=fpx_str['PROP_DESC_LIBRARIES_PATH'],
            default=FpxUI.PROP_DEFAULT_LIBRARIES_PATH,
            #subtype = 'DIR_PATH',
            #options={'HIDDEN', },
            )

    path_dmdfonts = StringProperty(
            name=fpx_str['PROP_NAME_DMDFONTS_PATH'],
            description=fpx_str['PROP_DESC_DMDFONTS_PATH'],
            default=FpxUI.PROP_DEFAULT_DMDFONTS_PATH,
            #subtype = 'DIR_PATH',
            #options={'HIDDEN', },
            )

    path_tables = StringProperty(
            name=fpx_str['PROP_NAME_TABLES_PATH'],
            description=fpx_str['PROP_DESC_TABLES_PATH'],
            default=FpxUI.PROP_DEFAULT_TABLES_PATH,
            #subtype = 'DIR_PATH',
            #options={'HIDDEN', },
            )


    convert_to_mesh = BoolProperty(
            name=fpx_str['PROP_NAME_CONVERT_TO_MESH'],
            description=fpx_str['PROP_DESC_CONVERT_TO_MESH'],
            default=FpxUI.PROP_DEFAULT_CONVERT_TO_MESH,
            )

    resolution_wire_bevel = IntProperty(
            name=fpx_str['PROP_NAME_RESOLUTION_WIRE_BEVEL'],
            description=fpx_str['PROP_DESC_RESOLUTION_WIRE_BEVEL'],
            default=FpxUI.PROP_DEFAULT_RESOLUTION_WIRE_BEVEL,
            min=2,
            max=16,
            )

    resolution_wire = IntProperty(
            name=fpx_str['PROP_NAME_RESOLUTION_WIRE'],
            description=fpx_str['PROP_DESC_RESOLUTION_WIRE'],
            default=FpxUI.PROP_DEFAULT_RESOLUTION_WIRE,
            min=2,
            max=16,
            )

    resolution_rubber_bevel = IntProperty(
            name=fpx_str['PROP_NAME_RESOLUTION_RUBBER_BEVEL'],
            description=fpx_str['PROP_DESC_RESOLUTION_RUBBER_BEVEL'],
            default=FpxUI.PROP_DEFAULT_RESOLUTION_RUBBER_BEVEL,
            min=2,
            max=16,
            )

    resolution_rubber = IntProperty(
            name=fpx_str['PROP_NAME_RESOLUTION_RUBBER'],
            description=fpx_str['PROP_DESC_RESOLUTION_RUBBER'],
            default=FpxUI.PROP_DEFAULT_RESOLUTION_RUBBER,
            min=2,
            max=16,
            )

    resolution_shape = IntProperty(
            name=fpx_str['PROP_NAME_RESOLUTION_SHAPE'],
            description=fpx_str['PROP_DESC_RESOLUTION_SHAPE'],
            default=FpxUI.PROP_DEFAULT_RESOLUTION_SHAPE,
            min=2,
            max=16,
            )

    use_hermite_handle = BoolProperty(
            name=fpx_str['PROP_NAME_USE_HERMITE_HANDLE'],
            description=fpx_str['PROP_DESC_USE_HERMITE_HANDLE'],
            default=FpxUI.PROP_DEFAULT_USE_HERMITE_HANDLE,
            )


    use_library_filter = EnumProperty(
            name=fpx_str['PROP_NAME_USE_LIBRARY_FILTER'],
            description=fpx_str['PROP_DESC_USE_LIBRARY_FILTER'],
            items=(
                    (FpxUI.USE_LIBRARY_FILTER_MODEL,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MODEL_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MODEL_2'],
                            'FILE_BLEND',
                            1,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_GRAPHIC,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_GRAPHIC_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_GRAPHIC_2'],
                            'FILE_IMAGE',
                            2,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_DMDFONT,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_DMDFONT_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_DMDFONT_2'],
                            'FILE_FONT',
                            4,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_SOUND,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SOUND_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SOUND_2'],
                            'FILE_SOUND',
                            8,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_MUSIC,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MUSIC_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_MUSIC_2'],
                            'FILE_MOVIE',
                            16,
                            ),
                    (FpxUI.USE_LIBRARY_FILTER_SCRIPT,
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SCRIPT_1'],
                            fpx_str['ENUM_USE_LIBRARY_FILTER_SCRIPT_2'],
                            'FILE_SCRIPT',
                            32,
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_USE_LIBRARY_FILTER,
            options={'ENUM_FLAG', },
            )

    use_model_filter = EnumProperty(
            name=fpx_str['PROP_NAME_USE_MODEL_FILTER'],
            description=fpx_str['PROP_DESC_USE_MODEL_FILTER'],
            items=(
                    (FpxUI.USE_MODEL_FILTER_SECONDARY,
                            fpx_str['PROP_NAME_MODEL_SECONDARY'],
                            fpx_str['PROP_DESC_MODEL_SECONDARY'],
                            'MESH_CUBE',
                            1,
                            ),
                    (FpxUI.USE_MODEL_FILTER_REFLECTION,
                            fpx_str['PROP_NAME_MODEL_REFLECTION'],
                            fpx_str['PROP_DESC_MODEL_REFLECTION'],
                            'MOD_MIRROR',
                            2,
                            ),
                    (FpxUI.USE_MODEL_FILTER_MASK,
                            fpx_str['PROP_NAME_MODEL_MASK'],
                            fpx_str['PROP_DESC_MODEL_MASK'],
                            'MOD_MASK',
                            4,
                            ),
                    (FpxUI.USE_MODEL_FILTER_COLLISION,
                            fpx_str['PROP_NAME_MODEL_COLLISION'],
                            fpx_str['PROP_DESC_MODEL_COLLISION'],
                            'MOD_PHYSICS',
                            8,
                            ),
                    ),
            default=FpxUI.PROP_DEFAULT_USE_MODEL_FILTER,
            options={'ENUM_FLAG', },
            )

    use_model_adjustment = BoolProperty(
            name=fpx_str['PROP_NAME_MODEL_ADJUST'],
            description=fpx_str['PROP_DESC_MODEL_ADJUST'],
            default=FpxUI.PROP_DEFAULT_MODEL_ADJUST_FPT,
            )


    filename_ext = fpx_str['FILE_EXT_FPT']

    filter_glob = StringProperty(
            default=fpx_str['FILE_FILTER_FPT'],
            options={'HIDDEN', }
            )

    # check add-on dependency
    @classmethod
    def poll(cls, blender_context):
        loaded_default, loaded_state = check("io_scene_ms3d")
        return loaded_state

    # draw the option panel
    def draw(self, blender_context):
        layout = self.layout

        box = layout.box()
        box.label(fpx_str['LABEL_NAME_OPTIONS'], icon=FpxUI.ICON_OPTIONS)
        flow = box.column_flow()
        flow.prop(self, 'verbose', icon='SPEAKER')
        flow = box.column_flow()
        flow.prop(self, 'keep_temp', icon='GHOST')

        box.label(fpx_str['LABEL_NAME_EXTERNAL_DATA'], icon=FpxUI.ICON_EXTERNAL_DATA)
        flow = box.column_flow()
        flow.prop(self, 'path_libraries', icon='FILESEL', text="")
        flow.prop(self, 'path_dmdfonts', icon='IMASEL', text="")
        flow.prop(self, 'path_tables', icon='FILE_FOLDER', text="")

        box = layout.box()
        box.label(fpx_str['LABEL_NAME_TABLE_OPTIONS'], icon=FpxUI.ICON_MODEL)
        #if self.convert_to_mesh:
        #    NotImplemented(box)
        flow = box.column_flow()
        flow.prop(self, 'convert_to_mesh', icon='MOD_TRIANGULATE')
        flow = box.column_flow()
        flow.prop(self, 'resolution_wire_bevel', icon='MOD_REMESH')
        flow.prop(self, 'resolution_wire', icon='MOD_REMESH')
        flow.prop(self, 'resolution_rubber_bevel', icon='MOD_REMESH')
        flow.prop(self, 'resolution_rubber', icon='MOD_REMESH')
        flow.prop(self, 'resolution_shape', icon='MOD_REMESH')
        flow = box.column_flow()
        flow.prop(self, 'use_hermite_handle', icon='CURVE_BEZCURVE')

        FplImportOperator.draw_library_options(self, layout)
        FpmImportOperator.draw_model_options(self, layout)

    # entrypoint for FPT -> blender
    def execute(self, blender_context):
        """ start executing """

        FpxUtilities.set_scene_to_default(blender_context.scene)

        from io_scene_fpx.fpx_import import (FptImporter, )
        FptImporter(
                report = self.report,
                verbose = self.verbose,
                keep_temp = self.keep_temp,
                path_libraries = self.path_libraries,
                convert_to_mesh = self.convert_to_mesh,
                resolution_wire_bevel = self.resolution_wire_bevel,
                resolution_wire = self.resolution_wire,
                resolution_rubber_bevel = self.resolution_rubber_bevel,
                resolution_rubber = self.resolution_rubber,
                resolution_shape = self.resolution_shape,
                use_hermite_handle = self.use_hermite_handle,
                use_library_filter = self.use_library_filter,
                use_model_filter = self.use_model_filter,
                use_model_adjustment = self.use_model_adjustment,
                ).read(
                        blender_context,
                        self.filepath,
                        )

        FpxUtilities.set_scene_to_metric(blender_context)

        for scene in blender_context.blend_data.scenes:
            scene.layers = (True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
            scene.update()

        return {"FINISHED"}

    def invoke(self, blender_context, event):
        blender_context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL', }

    @staticmethod
    def menu_func(cls, blender_context):
        cls.layout.operator(
                FptImportOperator.bl_idname,
                text=fpx_str['TEXT_OPERATOR_FPT'],
                )


###############################################################################
class FpxSetSceneToMetricOperator(Operator):
    """ . """
    bl_idname = 'io_scene_fpx.set_scene_to_metric'
    bl_label = fpx_str['BL_LABEL_SET_SCENE_TO_METRIC']
    bl_description = fpx_str['BL_DESC_SET_SCENE_TO_METRIC']


    #
    @classmethod
    def poll(cls, blender_context):
        return True

    # entrypoint for option
    def execute(self, blender_context):
        return self.set_scene_to_metric(blender_context)

    # entrypoint for option via UI
    def invoke(self, blender_context, event):
        return blender_context.window_manager.invoke_props_dialog(self)


    ###########################################################################
    def set_scene_to_metric(self, blender_context):
        FpxUtilities.set_scene_to_metric(blender_context)
        return {"FINISHED"}


###############################################################################
def register():
    register_class(FpxSetSceneToMetricOperator)
    register_class(FptEmptyItemProperties)
    register_class(FptEmptyProperties)
    inject_properties()

def unregister():
    delete_properties()
    unregister_class(FptEmptyProperties)
    unregister_class(FptEmptyItemProperties)
    unregister_class(FpxSetSceneToMetricOperator)

def inject_properties():
    Object.fpt = PointerProperty(type=FptEmptyProperties)

def delete_properties():
    del Object.fpt

###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
