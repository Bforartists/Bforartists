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


DEV_MODE__APPEND_TO_EXISTING = False # do not enable - only for developing purpose (e.g. appending fpx_resource.blend)


#import python stuff
import io
from mathutils import (
        Euler,
        Vector,
        Matrix,
        Quaternion,
        )
from math import (
        radians,
        )
from os import (
        path,
        listdir,
        rmdir,
        remove,
        )
from sys import (
        exc_info,
        )
from time import (
        time,
        )


# import io_scene_fpx stuff
if repr(globals()).find("bpy") != -1:
    from io_scene_fpx.fpx_strings import (
            fpx_str,
            )
    from io_scene_fpx.fpx_spec import (
            Fpm_File_Reader,
            Fpl_File_Reader,
            Fpt_File_Reader,
            Fpm_Model_Type,
            Fpl_Library_Type,
            FptElementType,
            Fpt_PackedLibrary_Type,
            )
    from io_scene_fpx.fpx_ui import (
            FpxUI,
            )
    from io_scene_fpx.fpx_utils import (
            FpxUtilities,
            )
else:
    from fpx_strings import (
            fpx_str,
            )
    from fpx_spec import (
            Fpm_File_Reader,
            Fpl_File_Reader,
            Fpt_File_Reader,
            Fpm_Model_Type,
            Fpl_Library_Type,
            FptElementType,
            Fpt_PackedLibrary_Type,
            )
    from fpx_ui import (
            FpxUI,
            )
    from fpx_utils import (
            FpxUtilities,
            )


#import blender stuff
from bpy import (
        ops,
        app,
        #data,
        )
import bmesh
from bpy_extras.image_utils import (
        load_image,
        )


###############################################################################
FORMAT_SCENE = "{}.s"
FORMAT_GROUP = "{}.g"
FORMAT_IMAGE = "{}.i"
FORMAT_TEXTURE = "{}.tex"
# keep material name like it is (prevent name "snakes" on re-import)
#FORMAT_MATERIAL = "{}.mat"
FORMAT_MATERIAL = "{}"
FORMAT_ACTION = "{}.act"
FORMAT_MESH = "{}.m"
FORMAT_MESH_OBJECT = "{}.mo"
FORMAT_EMPTY_OBJECT = "{}.eo"
FORMAT_DUPLI_OBJECT = "{}.do"
FORMAT_CURVE = "{}.c"
FORMAT_CURVE_OBJECT = "{}.co"
FORMAT_ARMATURE = "{}.a"
FORMAT_ARMATURE_OBJECT = "{}.ao"
FORMAT_ARMATURE_NLA = "{}.an"
FORMAT_LAMP = "{}.l"
FORMAT_LAMP_OBJECT = "{}.lo"

FORMAT_RESOURCE = "{{{}}}.{}"

PREFIX_LOCAL = "1"
PREFIX_EMBEDDED = "0"

FORMAT_MODEL_SECONDARY = "{}.low"
FORMAT_MODEL_MASK = "{}.mask"
FORMAT_MODEL_MIRROR = "{}.mirror"
FORMAT_MODEL_START = "{}.start"
FORMAT_MODEL_END = "{}.end"
FORMAT_MODEL_CAP1 = "{}.cap1"
FORMAT_MODEL_CAP2 = "{}.cap2"
FORMAT_MODEL_RING = "{}.ring{:02d}"

DEFAULT_LAMP_TEXTURE = "rsrc_bmp_254"
DEFAULT_SLINGHAMMER_TEXTURE = "rsrc_bmp_290"

TRANSLITE_OBJECT = 2
###############################################################################
class FpmImporter():
    """ Load a Future Pinball Model FPM File """
    LAYERS_PRIMARY_MODEL = (
            True, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False
            )
    LAYERS_SECONDARY_MODEL = (
            False, True, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False
            )
    LAYERS_MASK_MODEL = (
            False, False, True, False, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False
            )
    LAYERS_REFLECTION_MODEL = (
            False, False, False, True, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False
            )
    LAYERS_COLLISION_MODEL = (
            False, False, False, False, True,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False
            )

    def __init__(self,
            report,
            verbose=FpxUI.PROP_DEFAULT_VERBOSE,
            keep_temp=FpxUI.PROP_DEFAULT_KEEP_TEMP,
            use_all_models_of_folder=FpxUI.PROP_DEFAULT_ALL_MODELS,
            use_scene_per_model=FpxUI.PROP_DEFAULT_SCENE,
            name_extra=FpxUI.PROP_DEFAULT_NAME_EXTRA,
            use_model_filter=FpxUI.PROP_DEFAULT_USE_MODEL_FILTER,
            use_model_adjustment=FpxUI.PROP_DEFAULT_MODEL_ADJUST_FPM,
            keep_name=False,
            ):
        self.report = report
        self.verbose = verbose
        self.keep_temp = keep_temp
        self.use_all_models_of_folder = use_all_models_of_folder
        self.use_scene_per_model = use_scene_per_model
        self.name_extra = name_extra
        self.use_model_filter = use_model_filter
        self.use_model_adjustment = use_model_adjustment
        self.keep_name = keep_name

    def read(self, blender_context, filepath):
        """ read fpm file and convert fpm content to bender content """
        t1 = time()
        t2 = None

        fpx_reader = None

        self.__context = blender_context
        self.__data = blender_context.blend_data
        self.__scene = blender_context.scene

        self.__table_width = 0.0
        self.__table_length = 0.0
        self.__translite_width = 0.0
        self.__translite_length = 0.0

        try:
            self.folder_name, file_name = path.split(filepath)

            debug_data = []

            files = None
            if self.use_all_models_of_folder:
                files = [path.join(self.folder_name, f) for f in listdir(self.folder_name) if f.endswith(".fpm")]
            else:
                files = [filepath, ]

            for file in files:
                self.folder_name, file_name = path.split(filepath)
                try:
                    with io.FileIO(file, 'rb') as raw_io:
                        # read and inject fpm data from disk to internal structure
                        fpx_reader = Fpm_File_Reader(raw_io)
                        fpx_reader.read_model()
                        raw_io.close()
                finally:
                    pass

                # if option is set, this time will enlarges the io time
                #if self.verbose and reader:
                #    fpx_reader.print_internal()
                t2 = time()

                if fpx_reader:
                    temp_name = path.join(app.tempdir, "__grab__fpm__")
                    dst_path, dst_sub_path_names = fpx_reader.grab_content(temp_name)

                    model_name = fpx_reader.PinModel.get_value("name")
                    model_name = FpxUtilities.toGoodName(model_name) ####
                    #model_name = path.split(file)[1]
                    #model_name = model_name.lower()
                    #if model_name.endswith(".fpm"):
                    #    model_name = model_name[:-4]

                    if self.name_extra:
                        model_name = FORMAT_RESOURCE.format(self.name_extra, model_name)


                    model_filepath = dst_sub_path_names.get("modeldata")
                    debug_data.append("type={}, model_filepath='{}'".format(dst_sub_path_names.get("type"), model_filepath))
                    if model_filepath:
                        self.read_ex(blender_context, dst_sub_path_names, model_name, debug_data)

                    # cleanup
                    if not self.keep_temp:
                        try:
                            rmdir(dst_path)
                        except:
                            pass

            if self.verbose in FpxUI.VERBOSE_NORMAL:
                print()
                print("##########################################################")
                print("Import from FPM to Blender")
                for item in debug_data:
                    print("#DEBUG", item)
                print("##########################################################")

        except Exception as ex:
            type, value, traceback = exc_info()
            if self.verbose in FpxUI.VERBOSE_NORMAL:
                print("read fpm - exception in try block\n  type: '{0}'\n"
                        "  value: '{1}'".format(type, value, traceback))

            if t2 is None:
                t2 = time()

            raise

        else:
            pass

        finally:
            self.__context = None
            self.__data = None
            self.__scene = None

        t3 = time()
        if self.verbose in FpxUI.VERBOSE_NORMAL:
            print(fpx_str['SUMMARY_IMPORT'].format(
                    (t3 - t1), (t2 - t1), (t3 - t2)))

        return {"FINISHED"}

    ###########################################################################
    def read_ex(self, blender_context, dst_sub_path_names, model_name, debug_data):
        model_filepath = dst_sub_path_names.get("primary_model_data")
        if model_filepath:
            if self.use_scene_per_model:
                if DEV_MODE__APPEND_TO_EXISTING:
                    blender_scene = blender_context.blend_data.scenes.get(FpxUtilities.toGoodName(FORMAT_SCENE.format(model_name)))
                    if not blender_scene:
                        print("#DEBUG missing scene for:", model_name)
                        return
                else:
                    blender_scene = blender_context.blend_data.scenes.new(FpxUtilities.toGoodName(FORMAT_SCENE.format(model_name)))
                blender_context.screen.scene = blender_scene
            else:
                blender_scene = blender_context.scene
                # setup current Scene to default units
                FpxUtilities.set_scene_to_default(blender_scene)

            blender_scene.layers = self.LAYERS_PRIMARY_MODEL
            #{'FINISHED'}
            #{'CANCELLED'}
            if DEV_MODE__APPEND_TO_EXISTING or 'FINISHED' in ops.import_scene.ms3d(filepath=model_filepath, use_animation=True):
                if not DEV_MODE__APPEND_TO_EXISTING:
                    remove_material(blender_context)

                    if not self.keep_name:
                        src_name = get_object_src_name(blender_context)
                        rename_active_ms3d(blender_context, src_name, model_name)

                    if self.use_model_adjustment:
                        adjust_position(blender_context, blender_scene, dst_sub_path_names)

                if FpxUI.USE_MODEL_FILTER_SECONDARY in self.use_model_filter:
                    model_filepath = dst_sub_path_names.get("secondary_model_data")
                    if model_filepath:
                        blender_scene.layers = self.LAYERS_SECONDARY_MODEL
                        if 'FINISHED' in ops.import_scene.ms3d(filepath=model_filepath, use_animation=False):
                            remove_material(blender_context)
                            if not self.keep_name:
                                src_name = get_object_src_name(blender_context)
                                rename_active_ms3d(blender_context, src_name, model_name, "secondary")

                if FpxUI.USE_MODEL_FILTER_MASK in self.use_model_filter:
                    model_filepath = dst_sub_path_names.get("mask_model_data")
                    if model_filepath:
                        blender_scene.layers = self.LAYERS_MASK_MODEL
                        if 'FINISHED' in ops.import_scene.ms3d(filepath=model_filepath, use_animation=False):
                            remove_material(blender_context)
                            if not self.keep_name:
                                src_name = get_object_src_name(blender_context)
                                rename_active_ms3d(blender_context, src_name, model_name, "mask")

                if FpxUI.USE_MODEL_FILTER_REFLECTION in self.use_model_filter:
                    model_filepath = dst_sub_path_names.get("reflection_model_data")
                    if model_filepath:
                        blender_scene.layers = self.LAYERS_REFLECTION_MODEL
                        if 'FINISHED' in ops.import_scene.ms3d(filepath=model_filepath, use_animation=False):
                            remove_material(blender_context)
                            if not self.keep_name:
                                src_name = get_object_src_name(blender_context)
                                rename_active_ms3d(blender_context, src_name, model_name, "reflection")

                if FpxUI.USE_MODEL_FILTER_COLLISION in self.use_model_filter:
                    ## TODO
                    pass

                blender_scene.layers = self.LAYERS_PRIMARY_MODEL

        # setup all current 3d Views of the current scene to metric units
        FpxUtilities.set_scene_to_metric(blender_context)

        # cleanup
        if not self.keep_temp:
            for key, file in dst_sub_path_names.items():
                if key in {'type', 'sub_dir', }:
                    continue
                try:
                    remove(file)
                except:
                    pass

            sub_dir_path = dst_sub_path_names.get('sub_dir')
            if sub_dir_path:
                try:
                    rmdir(sub_dir_path)
                except:
                    pass


###############################################################################
class FplImporter():
    """ Load a Future Pinball Library FPL File """
    def __init__(self,
            report,
            verbose=FpxUI.PROP_DEFAULT_VERBOSE,
            keep_temp=FpxUI.PROP_DEFAULT_KEEP_TEMP,
            use_all_libraries_of_folder=FpxUI.PROP_DEFAULT_ALL_LIBRARIES,
            use_library_filter=FpxUI.PROP_DEFAULT_USE_LIBRARY_FILTER,
            use_model_filter=FpxUI.PROP_DEFAULT_USE_MODEL_FILTER,
            use_model_adjustment=FpxUI.PROP_DEFAULT_MODEL_ADJUST_FPL,
            keep_name=False,
            ):
        self.report = report
        self.verbose = verbose
        self.keep_temp = keep_temp
        self.use_all_libraries_of_folder = use_all_libraries_of_folder
        self.use_library_filter = use_library_filter
        self.use_model_filter = use_model_filter
        self.use_model_adjustment = use_model_adjustment
        self.keep_name = keep_name

    def read(self, blender_context, filepath):
        """ read fpl file and convert fpm content to bender content """
        t1 = time()
        t2 = None

        fpx_reader = None

        self.__context = blender_context
        self.__data = blender_context.blend_data
        self.__scene = blender_context.scene

        active_scene = self.__context.screen.scene

        try:
            self.folder_name, file_name = path.split(filepath)

            debug_data = []

            if self.use_all_libraries_of_folder:
                files = [path.join(self.folder_name, f) for f in listdir(self.folder_name) if f.endswith(".fpl")]
            else:
                files = [filepath, ]

            for file in files:
                self.folder_name, file_name = path.split(file)
                try:
                    with io.FileIO(file, 'rb') as raw_io:
                        # read and inject fpl data from disk to internal structure
                        fpx_reader = Fpl_File_Reader(raw_io)
                        fpx_reader.read_library()
                        raw_io.close()
                finally:
                    pass

                # if option is set, this time will enlarges the io time
                #if self.verbose and reader:
                #    fpx_reader.print_internal()
                t2 = time()

                if fpx_reader:
                    temp_name = path.join(app.tempdir, "__grab__fpl__")
                    dst_path, dst_sub_path_names = fpx_reader.grab_content(temp_name)

                    for key, item in dst_sub_path_names.items():
                        if key is not None and key.startswith('type_'):
                            type = item
                            key_name = key[5:]
                            #print("#DEBUG", key_name, type)

                            if type not in self.use_library_filter:
                                continue

                            item_path = dst_sub_path_names.get(key_name)

                            if type == Fpl_Library_Type.TYPE_MODEL:
                                #print("#DEBUG", type, key_name)
                                FpmImporter(
                                        report=self.report,
                                        verbose=self.verbose,
                                        keep_temp=self.keep_temp,
                                        use_scene_per_model=True,
                                        name_extra=file_name,
                                        use_model_filter=self.use_model_filter,
                                        use_model_adjustment=self.use_model_adjustment,
                                    ).read(
                                            blender_context=self.__context,
                                            filepath=item_path,
                                        )
                                if not self.keep_name:
                                    rename_active_fpm(self.__context, FORMAT_RESOURCE.format(file_name, key_name))

                            elif type == Fpl_Library_Type.TYPE_GRAPHIC:
                                #print("#DEBUG fpl images.load", item_path)
                                #print("#DEBUG", type, key_name, item_path)
                                blend_image = self.__data.images.load(item_path)
                                if blend_image:
                                    blend_image.name = FpxUtilities.toGoodName(FORMAT_RESOURCE.format(file_name, FORMAT_IMAGE.format(key_name)))
                                    if blend_image.has_data:
                                        blend_image.update()
                                    blend_image.pack()
                                    blend_image.use_fake_user = True
                                    item_dir, item_file = path.split(item_path)
                                    blend_image.filepath_raw = "//unpacked_resource/{}".format(item_file)
                                if not blend_image or not blend_image.has_data:
                                    print("#DEBUG fpl images.load failed", item_path)

                        else:
                            pass


                    # cleanup
                    if not self.keep_temp:
                        cleanup_sub_dirs = []

                        for key, file in dst_sub_path_names.items():
                            if key is not None and key.startswith('sub_dir'):
                                cleanup_sub_dirs.append(file)
                                continue

                            if key in {'type', None, } or key.startswith('type'):
                                continue

                            try:
                                remove(file)
                            except:
                                pass

                        sub_dir_path = dst_sub_path_names.get('sub_dir')
                        if sub_dir_path:
                            try:
                                rmdir(sub_dir_path)
                            except:
                                pass

                        for sub_dir_path in cleanup_sub_dirs:
                            try:
                                rmdir(sub_dir_path)
                            except:
                                pass

                        try:
                            rmdir(dst_path)
                        except:
                            pass

            if self.verbose in FpxUI.VERBOSE_NORMAL:
                print()
                print("##########################################################")
                print("Import from FPM to Blender")
                for item in debug_data:
                    print("#DEBUG", item)
                print("##########################################################")

        except Exception as ex:
            type, value, traceback = exc_info()
            if self.verbose in FpxUI.VERBOSE_NORMAL:
                print("read fpl - exception in try block\n  type: '{0}'\n"
                        "  value: '{1}'".format(type, value, traceback))

            if t2 is None:
                t2 = time()

            raise

        else:
            pass

        finally:
            self.__context.screen.scene = active_scene
            self.__context = None
            self.__data = None
            self.__scene = None

        t3 = time()
        if self.verbose in FpxUI.VERBOSE_NORMAL:
            print(fpx_str['SUMMARY_IMPORT'].format(
                    (t3 - t1), (t2 - t1), (t3 - t2)))

        return {"FINISHED"}

    ###########################################################################


###############################################################################
class FptImporter():
    """ Load a Future Pinball Table FPT File """
    LAYERS_WIRE_RING = (
            True, True, False, False, True,
            False, False, False, False, False,
            False, False, True, False, False,
            False, False, False, False, False
            )
    LAYERS_LIGHT_SPHERE = (
            True, True, False, False, True,
            False, False, False, False, False,
            True, False, False, False, False,
            False, False, False, False, False
            )
    LAYERS_AO = (
            True, True, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False,
            False, False, False, False, False
            )
    BLENDER_OBJECT_NAME = 0

    def __init__(self,
            report,
            verbose=FpxUI.PROP_DEFAULT_VERBOSE,
            keep_temp=FpxUI.PROP_DEFAULT_KEEP_TEMP,
            path_libraries=FpxUI.PROP_DEFAULT_LIBRARIES_PATH,
            convert_to_mesh=FpxUI.PROP_DEFAULT_CONVERT_TO_MESH,
            resolution_wire_bevel=FpxUI.PROP_DEFAULT_RESOLUTION_WIRE_BEVEL,
            resolution_wire=FpxUI.PROP_DEFAULT_RESOLUTION_WIRE,
            resolution_rubber_bevel=FpxUI.PROP_DEFAULT_RESOLUTION_RUBBER_BEVEL,
            resolution_rubber=FpxUI.PROP_DEFAULT_RESOLUTION_RUBBER,
            resolution_shape=FpxUI.PROP_DEFAULT_RESOLUTION_SHAPE,
            use_hermite_handle=FpxUI.PROP_DEFAULT_USE_HERMITE_HANDLE,
            use_library_filter=FpxUI.PROP_DEFAULT_USE_LIBRARY_FILTER,
            use_model_filter=FpxUI.PROP_DEFAULT_USE_MODEL_FILTER,
            use_model_adjustment=FpxUI.PROP_DEFAULT_MODEL_ADJUST_FPT,
            keep_name=False,
            ):
        self.report = report
        self.verbose = verbose
        self.keep_temp = keep_temp
        self.path_libraries = path_libraries
        self.convert_to_mesh = convert_to_mesh
        self.resolution_wire_bevel = resolution_wire_bevel
        self.resolution_wire = resolution_wire
        self.resolution_rubber_bevel = resolution_rubber_bevel
        self.resolution_rubber = resolution_rubber
        self.resolution_shape = resolution_shape
        self.use_hermite_handle = use_hermite_handle
        self.use_library_filter = use_library_filter
        self.use_model_filter = use_model_filter
        self.use_model_adjustment = use_model_adjustment
        self.keep_name = keep_name

        self.blend_resource_file = get_blend_resource_file_name()

        self.debug_light_extrude = 0.2
        self.debug_lightball_size = 2.0
        self.debug_lightball_height = 4.5
        self.debug_create_full_ramp_wires = False
        self.debug_missing_resources = set()

    ###########################################################################
    # create empty blender fp_table
    # read fpt file
    # fill blender with fp_table content
    def read(self, blender_context, filepath, ):
        """ read fpt file and convert fpt content to bender content """
        t1 = time()
        t2 = None

        fpx_reader = None

        self.__context = blender_context
        self.__data = blender_context.blend_data
        self.__scene = blender_context.scene

        try:
            try:
                with io.FileIO(filepath, 'rb') as raw_io:
                    # read and inject fpt data from disk to internal structure
                    fpx_reader = Fpt_File_Reader(raw_io)
                    fpx_reader.read_table()
                    raw_io.close()
            finally:
                pass

            # if option is set, this time will enlarges the io time
            #if self.options.verbose and reader:
            #    fpx_reader.print_internal()

            t2 = time()
            if fpx_reader:
                temp_name = path.join(app.tempdir, "__grab__fpt__")
                dst_path, dst_sub_path_names = fpx_reader.grab_content(temp_name)

                # setup current Scene to default units
                ##FpxUtilities.set_scene_to_default(self.__scene)

                self.folder_name, file_name = path.split(filepath)

                # search linked libraries
                self.fpx_images = {}
                self.GetLinked(fpx_reader.Image, self.fpx_images, Fpt_PackedLibrary_Type.TYPE_IMAGE, dst_sub_path_names)

                self.fpx_image_lists = {}
                for image_list in fpx_reader.ImageList.values():
                    key = image_list.get_value("name")
                    images = image_list.get_value("images")
                    self.fpx_image_lists[key] = images

                blender_image_name = FpxUtilities.toGoodName(FORMAT_RESOURCE.format(PREFIX_LOCAL, FORMAT_IMAGE.format(DEFAULT_LAMP_TEXTURE)))
                self.LoadObjectLite(blender_image_name, Fpt_PackedLibrary_Type.TYPE_IMAGE)
                self.fpx_images[DEFAULT_LAMP_TEXTURE] = [blender_image_name, ]

                self.fpx_pinmodels = {}
                self.GetLinked(fpx_reader.PinModel, self.fpx_pinmodels, Fpt_PackedLibrary_Type.TYPE_MODEL, dst_sub_path_names)

                """
                for key, item in self.fpx_images.items():
                    print("#DEBUG image:", key, item)

                for key, item in self.fpx_image_lists.items():
                    print("#DEBUG image_list:", key, item)

                for key, item in self.fpx_pinmodels.items():
                    print("#DEBUG pinmodel:", key, item)
                """

                # build pincab
                self.CreatePinCab(fpx_reader.Table_Data)

                # handle table elements
                for key, fpx_item in fpx_reader.Table_Element.items():
                    if fpx_item:
                        object_appers_on = fpx_item.get_value("object_appers_on")
                        if object_appers_on == TRANSLITE_OBJECT:
                            continue
                        #print("#DEBUG", object_appers_on, key, fpx_item)

                        fpx_item_name = fpx_item.get_value("name")
                        fpx_item_name = FpxUtilities.toGoodName(fpx_item_name) ####
                        if not fpx_item_name:
                            continue

                        fpx_id = fpx_item.get_obj_value("id")

                        ## get the height level (wall and/or surface) on what the item will be placed
                        fpx_surface_name = fpx_item.get_value("surface")
                        fpx_surface = None
                        fpx_position_z = None
                        fpx_position_zw = None
                        if fpx_surface_name:
                            fpx_wall = fpx_reader.Walls.get(FpxUtilities.toGoodName(fpx_surface_name))
                            if fpx_wall:
                                fpx_position_zw = fpx_wall.get_value("height")
                                fpx_surface_name = fpx_wall.get_value("surface")
                                if fpx_surface_name:
                                    fpx_surface = fpx_reader.Walls.get(FpxUtilities.toGoodName(fpx_surface_name))
                            else:
                                fpx_surface = fpx_reader.Surfaces.get(FpxUtilities.toGoodName(fpx_surface_name))
                            if fpx_surface:
                                fpx_position_z = fpx_surface.get_value("top_height")

                        if fpx_position_zw is None:
                            fpx_position_zw = 0.0
                        if fpx_position_z is None:
                            fpx_position_z = 0.0

                        fpx_position_z += fpx_position_zw

                        fpx_offset = fpx_item.get_value("offset")
                        if fpx_offset:
                            fpx_position_z += fpx_offset

                        ## gather common information
                        blender_object = None
                        fpx_shape_points = fpx_item.get_value("shape_point")
                        fpx_ramp_points =  fpx_item.get_value("ramp_point")
                        fpx_position_xy = fpx_item.get_value("position")
                        fpx_render_object = fpx_item.get_value("render_object")
                        fpx_transparency = fpx_item.get_value("transparency")
                        fpx_layer = fpx_item.get_value("layer")
                        fpx_sphere_mapping = fpx_item.get_value("sphere_mapping")
                        fpx_crystal = fpx_item.get_value("crystal")
                        fpx_base = None # TODO:

                        layers = self.FpxLayerToBlenderLayers(fpx_layer, fpx_id, fpx_render_object, fpx_transparency, fpx_sphere_mapping, fpx_crystal, fpx_base)

                        # handle curve objects with shape_points
                        if fpx_shape_points:
                            if fpx_id == FptElementType.SURFACE:
                                blender_object = self.CreateSurface(fpx_item, fpx_item_name, layers, fpx_shape_points)
                            elif fpx_id == FptElementType.LIGHT_SHAPEABLE:
                                blender_object = self.CreateLightShapeable(fpx_item, fpx_item_name, layers, fpx_shape_points, fpx_position_z)
                            elif fpx_id == FptElementType.RUBBER_SHAPEABLE:
                                blender_object = self.CreateRubberShapeable(fpx_item, fpx_item_name, layers, fpx_shape_points, fpx_position_z)
                            elif fpx_id == FptElementType.GUIDE_WALL:
                                blender_object = self.CreateGuideWall(fpx_item, fpx_item_name, layers, fpx_shape_points, fpx_position_z)
                            elif fpx_id == FptElementType.GUIDE_WIRE:
                                blender_object = self.CreateGuideWire(fpx_item, fpx_item_name, layers, fpx_shape_points, fpx_position_z)
                            else:
                                blender_object = None
                        # handle curve objects with ramp_points
                        elif fpx_ramp_points:
                            if fpx_id == FptElementType.RAMP_WIRE:
                                blender_object = self.CreateWireRamp(fpx_item, fpx_item_name, layers, fpx_ramp_points, fpx_position_z, fpx_id)
                            elif fpx_id == FptElementType.RAMP_RAMP:
                                blender_object = self.CreateRamp(fpx_item, fpx_item_name, layers, fpx_ramp_points, fpx_position_z)
                            else:
                                blender_object = None
                        else:
                            if fpx_id == FptElementType.LIGHT_LIGHTIMAGE:
                                blender_object = self.CreateLightImage(fpx_item, fpx_item_name, layers, fpx_position_xy, fpx_position_z)
                            else:
                                blender_object = None

                        # put the just created object (curve) to its layer
                        #if blender_object:
                        #    blender_object.layers = layers

                        if fpx_position_xy:
                            fpx_rotation = fpx_item.get_value("rotation")
                            if fpx_rotation:
                                blender_rotation = Euler((0.0, 0.0, radians(self.angle_correction(fpx_rotation))), 'XZY')
                            else:
                                blender_rotation = Euler((0.0, 0.0, radians(self.angle_correction(0.0))), 'XZY')

                            if fpx_id in {FptElementType.CONTROL_FLIPPER, FptElementType.CONTROL_DIVERTER, }:
                                fpx_start_angle = fpx_item.get_value("start_angle")
                                if fpx_start_angle is None:
                                    fpx_start_angle = 0
                                m0 = blender_rotation.to_matrix()
                                m1 = Euler((0.0, 0.0, radians(self.angle_correction(fpx_start_angle) + 90)), 'XZY').to_matrix()
                                blender_rotation = (m0 * m1).to_euler('XZY')

                            blender_position = self.geometry_correction((fpx_position_xy[0], fpx_position_xy[1], fpx_position_z))

                            blender_empty_object = self.__data.objects.new(FORMAT_EMPTY_OBJECT.format(fpx_item_name), None)
                            blender_empty_object.location = blender_position
                            blender_empty_object.rotation_mode = 'XZY'
                            blender_empty_object.rotation_euler = blender_rotation
                            blender_empty_object.empty_draw_type = 'ARROWS'
                            blender_empty_object.empty_draw_size = 10.0
                            self.__scene.objects.link(blender_empty_object)
                            blender_empty_object.layers = layers

                            blender_empty_object.fpt.name = fpx_item_name

                            # handle model object (try to create an instance of existing group)
                            fpx_model_name = fpx_item.get_value("model")
                            if fpx_model_name:
                                fpx_model_beam_width = fpx_item.get_value("beam_width")
                                if fpx_model_beam_width:
                                    offset = 3.75
                                    blender_object = self.attach_dupli_group(blender_empty_object, layers, fpx_model_name, "model", Vector((0.0 , ((fpx_model_beam_width / 2.0) + offset), 0.0)), -90)
                                    texture = fpx_item.get_value("texture_emitter")
                                    if texture:
                                        self.append_texture_material(blender_object, texture, uv_layer="ms3d_uv_layer")
                                    blender_object = self.attach_dupli_group(blender_empty_object, layers, fpx_model_name, "model", Vector((0.0 , -((fpx_model_beam_width / 2.0) + offset), 0.0)), 90)
                                    texture = fpx_item.get_value("texture_collector")
                                    if texture:
                                        self.append_texture_material(blender_object, texture, uv_layer="ms3d_uv_layer")
                                else:
                                    blender_object = self.attach_dupli_group(blender_empty_object, layers, fpx_model_name, "model")
                                    if fpx_transparency or fpx_crystal or fpx_id in FptElementType.SET_LIGHT_OBJECTS:
                                        self.append_christal_material(blender_object)
                                    elif fpx_sphere_mapping and fpx_id not in FptElementType.SET_LIGHT_OBJECTS:
                                        self.append_chrome_material(blender_object)
                                    else:
                                        texture = fpx_item.get_value("texture")
                                        if texture:
                                            #print("#DEBUG texture", texture)
                                            self.append_texture_material(blender_object, texture, light_on=(fpx_id not in FptElementType.SET_LIGHT_OBJECTS), uv_layer="ms3d_uv_layer")


                            fpx_model_name_cap = fpx_item.get_value("model_cap")
                            if fpx_model_name_cap:
                                blender_object = self.attach_dupli_group(blender_empty_object, layers, fpx_model_name_cap, "model_cap")
                                texture = fpx_item.get_value("cap_texture")
                                if texture:
                                    self.append_texture_material(blender_object, texture, light_on=True, uv_layer="ms3d_uv_layer")

                            fpx_model_name_base = fpx_item.get_value("model_base")
                            if fpx_model_name_base:
                                blender_object = self.attach_dupli_group(blender_empty_object, layers, fpx_model_name_base, "model_base")
                                if not fpx_item.get_value("passive"):
                                    blender_object = self.attach_dupli_group(blender_empty_object, layers, "bumperring", 'LOCAL', Vector((0.0 , 0.0, 4.0)))
                                    self.append_chrome_material(blender_object)
                                if fpx_item.get_value("trigger_skirt"):
                                    blender_object = self.attach_dupli_group(blender_empty_object, layers, "bumperskirt", 'LOCAL', Vector((0.0 , 0.0, 3.5)))

                            if fpx_id == FptElementType.RUBBER_ROUND:
                                blender_object = self.CreateRubberRound(fpx_item, fpx_item_name, layers, fpx_position_xy, fpx_position_z)

                            if fpx_id:
                                blender_empty_object.fpt.id = FptElementType.VALUE_INT_TO_NAME.get(fpx_id)

                            if fpx_id == FptElementType.LIGHT_ROUND:
                                blender_object = self.CreateLightRound(fpx_item, fpx_item_name, layers, fpx_position_xy, fpx_position_z)
                                if blender_object:
                                    blender_object.layers = layers

                            ## #DEBUG : light dummies
                            if fpx_id in FptElementType.SET_LIGHT_OBJECTS: # and not blender_empty_object.children:
                                #if ops.mesh.primitive_ico_sphere_add.poll():
                                #    ops.mesh.primitive_ico_sphere_add(subdivisions=2, size=self.debug_lightball_size, location=blender_empty_object.location + Vector((0.0, 0.0, self.debug_lightball_height)), layers=FptImporter.LAYERS_LIGHT_SPHERE)
                                #    self.append_light_material(self.__context.active_object)
                                #self.add_lamp(fpx_item_name, blender_empty_object.location + Vector((0.0, 0.0, self.debug_lightball_height)), layers=FptImporter.LAYERS_LIGHT_SPHERE)
                                pass

                    # cleanup
                    if not self.keep_temp:
                        cleanup_sub_dirs = []

                        for key, file in dst_sub_path_names.items():
                            if key is not None and key.startswith('sub_dir'):
                                cleanup_sub_dirs.append(file)
                                continue

                            if key in {'type', 'data', None, } or key.startswith('type') or key.startswith('data'):
                                continue

                            try:
                                remove(file)
                            except:
                                pass

                        sub_dir_path = dst_sub_path_names.get('sub_dir')
                        if sub_dir_path:
                            try:
                                rmdir(sub_dir_path)
                            except:
                                pass

                        for sub_dir_path in cleanup_sub_dirs:
                            try:
                                rmdir(sub_dir_path)
                            except:
                                pass

                        try:
                            rmdir(dst_path)
                        except:
                            pass


                self.add_table_camera(fpx_reader.Table_Data)
                self.add_table_lamp(fpx_reader.Table_Data)

                # setup all current 3d Views of the current scene to metric units
                FpxUtilities.set_scene_to_metric(self.__context)
                FpxUtilities.select_all(False)

            if self.verbose in FpxUI.VERBOSE_NORMAL:
                print()
                print("##########################################################")
                print("Import from FPT to Blender")
                print("##########################################################")

        except Exception as ex:
            type, value, traceback = exc_info()
            if self.verbose in FpxUI.VERBOSE_NORMAL:
                print("read fpt - exception in try block\n  type: '{0}'\n"
                        "  value: '{1}'".format(type, value, traceback))

            if t2 is None:
                t2 = time()

            raise

        else:
            pass

        finally:
            self.__context = None
            self.__data = None
            self.__scene = None

        t3 = time()
        if self.verbose in FpxUI.VERBOSE_NORMAL:
            print(fpx_str['SUMMARY_IMPORT'].format(
                    (t3 - t1), (t2 - t1), (t3 - t2)))

        return {"FINISHED"}

    def add_table_camera(self, fpx_table_data):
        name = "Camera.table"
        camera = self.__data.cameras.new(name)
        obj = self.__data.objects.new(name, camera)
        self.__scene.objects.link(obj)
        width = fpx_table_data.get_value("width", default=0.0)
        obj.location = (width / 2.0, -1600.0, 550.0)
        obj.rotation_euler = (radians(63.0), 0.0, 0.0)
        obj.select = True
        obj.layers = FptImporter.LAYERS_AO
        camera.lens_unit = 'FOV'
        camera.clip_start = 1.0 # 1.0mm
        camera.clip_end = 10000.0 # 10.0m
        camera.dof_distance = 1211.0
        camera.draw_size = 100.0
        self.__scene.camera = obj
        for area in self.__context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'PERSP'
                        space.region_3d.view_camera_zoom = 0.0
                        space.region_3d.view_distance = 969.49365234375
                        space.region_3d.view_matrix = Matrix((
                                (1.0000,  0.0000, 0.0000, -width / 2.0),
                                (0.0000,  0.4540, 0.8910,  236.3312),
                                (0.0000, -0.8910, 0.4540, -969.4935),
                                (0.0000,  0.0000, 0.0000,    1.0000)))
                        space.region_3d.view_location = (width / 2.0, -107.2920, -210.5727)
                        space.region_3d.view_rotation = obj.rotation_euler.to_quaternion()

    def add_table_lamp(self, fpx_table_data):
        width = fpx_table_data.get_value("width", default=100.0)
        length = fpx_table_data.get_value("length", default=500.0)
        width2 = width / 2.0
        length2 = length / 2.0
        width4 = width / 4.0
        length4 = length / 4.0

        name = "AreaLamp.table"
        lamp = self.__data.lamps.get(name)

        # blender internal
        if not lamp:
            lamp = self.__data.lamps.new(name, 'AREA')
            tmp_engine = self.__scene.render.engine
            self.__scene.render.engine = 'BLENDER_RENDER'
            lamp.shadow_method = 'RAY_SHADOW'
            lamp.shadow_ray_samples_x = 10
            lamp.shadow_ray_samples_y = 10
            lamp.distance = 500.0
            lamp.energy = 1.0
            lamp.use_specular = False
            lamp.size = width2
            lamp.shape = 'RECTANGLE'
            lamp.size_y = length2

            self.__scene.render.engine = 'CYCLES'
            lamp.cycles.use_multiple_importance_sampling = True
            lamp.use_nodes = True
            self.__scene.render.engine = tmp_engine

        obj = self.__data.objects.new(FORMAT_LAMP_OBJECT.format(name), lamp)
        self.__scene.objects.link(obj)
        obj.location = (width2, -length * (2.0/3.0), 600.0)
        obj.layers = FptImporter.LAYERS_AO

        # cycles
        mesh = self.__data.meshes.new(FORMAT_MESH.format("{}.arealamp".format(name)))
        obj = self.__data.objects.new(FORMAT_MESH_OBJECT.format(name), mesh)
        self.__scene.objects.link(obj)
        obj.location = (width2, -length * (2.0/3.0), 610.0)
        obj.layers = FptImporter.LAYERS_AO
        bm = bmesh.new()
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((width4, -length4, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((width4, length4, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((-width4, length4, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((-width4, -length4, 0.0)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)
        bm.to_mesh(mesh)
        bm.free()
        self.append_light_material(obj)

    def add_lamp(self, name, location, layers):
        name_lamp = FORMAT_LAMP.format(name)
        lamp = self.__data.lamps.get(name_lamp)
        if not lamp:
            lamp = self.__data.lamps.new(name_lamp, 'POINT')
            tmp_engine = self.__scene.render.engine
            self.__scene.render.engine = 'BLENDER_RENDER'
            #lamp.shadow_method = 'RAY_SHADOW'
            #lamp.shadow_ray_samples = 6
            #lamp.shadow_soft_size = 3.0
            lamp.distance = 1000.0
            lamp.energy = 1.0
            lamp.use_specular = False
            self.__scene.render.engine = 'CYCLES'
            lamp.cycles.use_multiple_importance_sampling = True
            lamp.use_nodes = True
            self.__scene.render.engine = tmp_engine

        obj = self.__data.objects.new(FORMAT_LAMP_OBJECT.format(name), lamp)
        self.__scene.objects.link(obj)

        obj.location = location
        obj.layers = layers

    def append_texture_material(self, blender_object, fpx_image_name, light_on=False, uv_layer=None):
        if not blender_object:
            return
        if blender_object.type not in {'MESH', 'CURVE', }:
            for child in blender_object.children:
                self.append_texture_material(child, fpx_image_name, light_on, uv_layer)
            return

        #print("#DEBUG append_texture_material *:", fpx_image_name)
        fpx_image_object = self.fpx_images.get(fpx_image_name)
        if not fpx_image_object:
            fpx_image_name = FpxUtilities.toGoodName(fpx_image_name)
            fpx_image_object = self.fpx_images.get(fpx_image_name)
            #print("#DEBUG append_texture_material **:", fpx_image_name)
        if fpx_image_object:
            blender_image = self.__data.images.get(fpx_image_object[self.BLENDER_OBJECT_NAME])
            if blender_image:
                if uv_layer:
                    bm_name = "uv_{}".format(FORMAT_MATERIAL.format(fpx_image_name))
                else:
                    bm_name = "gen_{}".format(FORMAT_MATERIAL.format(fpx_image_name))
                blender_material = self.__data.materials.get(bm_name)
                if not blender_material:
                    #print("#DEBUG create material", bm_name)
                    blender_material = self.__data.materials.new(bm_name)
                    render_engine = self.__scene.render.engine

                    #blender internal
                    self.__scene.render.engine = 'BLENDER_RENDER'
                    blender_material.use_transparency = True
                    #blender_material.use_raytrace = False # Material | Options | Traceable
                    blender_material.use_transparent_shadows = True
                    blender_material.alpha = 0.0
                    #blender_material.use_shadeless = True #DEBUG
                    if light_on:
                        blender_material.emit = 1.0
                    else:
                        #blender_material.subsurface_scattering.use = True
                        #blender_material.subsurface_scattering.scale = 1.0
                        #blender_material.subsurface_scattering.radius = (5.0, 5.0, 5.0)
                        #blender_material.subsurface_scattering.front = 0.0
                        pass

                    if uv_layer:
                        bt_name = "uv_{}".format(FORMAT_TEXTURE.format(fpx_image_name))
                    else:
                        bt_name = "gen_{}".format(FORMAT_TEXTURE.format(fpx_image_name))
                    blender_texture = self.__data.textures.get(bt_name)
                    if not blender_texture:
                        #print("#DEBUG create texture", bt_name)
                        blender_texture = self.__data.textures.new(bt_name, 'IMAGE')
                        blender_texture.image = blender_image
                    tex_slot = blender_material.texture_slots.create(0)
                    tex_slot.texture = blender_texture
                    tex_slot.use_map_alpha = True
                    if uv_layer:
                        tex_slot.texture_coords = 'UV'
                        tex_slot.uv_layer = uv_layer

                    # prepare for nodes
                    blender_material.use_nodes = True
                    nodes = blender_material.node_tree.nodes
                    links = blender_material.node_tree.links
                    gap = 50.0
                    nodes.clear()

                    # blender internal nodes
                    node_i0 = nodes.new('ShaderNodeOutput')
                    node_i1 = nodes.new('ShaderNodeMaterial')
                    node_i1.material = blender_material
                    link_i1_0 = links.new(node_i1.outputs['Color'], node_i0.inputs['Color'])
                    link_i1_0 = links.new(node_i1.outputs['Alpha'], node_i0.inputs['Alpha'])
                    node_i1_height = 410.0 # issue: [#37075] the height of nodes are always 100.0
                    node_i1.location = (0.0, node_i1_height + gap)
                    node_i0.location = (node_i1.location.x + node_i1.width + gap, node_i1_height + gap)

                    # blender cycles nodes
                    self.__scene.render.engine = 'CYCLES'
                    node_c0 = nodes.new('ShaderNodeOutputMaterial')
                    node_c1 = nodes.new('ShaderNodeMixShader')
                    node_c2 = nodes.new('ShaderNodeBsdfTransparent')
                    node_c3 = nodes.new('ShaderNodeAddShader')
                    node_c4 = nodes.new('ShaderNodeEmission')
                    if light_on:
                        node_c4.inputs['Strength'].default_value = 1.0
                    else:
                        node_c4.inputs['Strength'].default_value = 0.0
                    #node_c5 = nodes.new('ShaderNodeBsdfGlossy')
                    #node_c5.inputs['Roughness'].default_value = 0.25
                    node_c5 = nodes.new('ShaderNodeBsdfDiffuse')
                    node_c6 = nodes.new('ShaderNodeTexImage')
                    node_c6.image = blender_image
                    node_c7 = nodes.new('ShaderNodeTexCoord')
                    node_c7.location = (0.0, 0.0)
                    node_c6.location = (node_c7.location.x + node_c7.width + gap, 0.0)
                    node_c5.location = (node_c6.location.x + node_c6.width + gap, 0.0)
                    node_c4.location = (node_c5.location.x + node_c5.width + gap, 0.0)
                    node_c3.location = (node_c4.location.x + node_c4.width + gap, 0.0)
                    node_c2.location = (node_c3.location.x + node_c3.width + gap, 0.0)
                    node_c1.location = (node_c2.location.x + node_c2.width + gap, 0.0)
                    node_c0.location = (node_c1.location.x + node_c1.width + gap, 0.0)
                    link_c1_0 = links.new(node_c1.outputs['Shader'], node_c0.inputs['Surface'])
                    link_c6_1a = links.new(node_c6.outputs['Alpha'], node_c1.inputs[0]) # Fac
                    link_c2_1b = links.new(node_c2.outputs['BSDF'], node_c1.inputs[1]) # 1'st Shader
                    link_c3_1c = links.new(node_c3.outputs['Shader'], node_c1.inputs[2]) # 2'nd Shader
                    link_c4_3a = links.new(node_c4.outputs['Emission'], node_c3.inputs[0]) # 1'st Shader
                    link_c5_3b = links.new(node_c5.outputs['BSDF'], node_c3.inputs[1]) # 2'nd Shader
                    link_c6_4 = links.new(node_c6.outputs['Color'], node_c4.inputs['Color'])
                    link_c6_5 = links.new(node_c6.outputs['Color'], node_c5.inputs['Color'])
                    if uv_layer:
                        link_c7_6 = links.new(node_c7.outputs['UV'], node_c6.inputs['Vector'])
                    else:
                        link_c7_6 = links.new(node_c7.outputs['Generated'], node_c6.inputs['Vector'])

                    """
                    # blender game
                    self.__scene.render.engine = 'BLENDER_GAME'
                    #TODO
                    """

                    self.__scene.render.engine = render_engine

                if not blender_object.data.materials.get(bm_name):
                    blender_object.data.materials.append(blender_material)

    def append_chrome_material(self, blender_object, color=(1.0, 1.0, 1.0, 1.0)):
        if not blender_object:
            return
        if blender_object.type not in {'MESH', 'CURVE', }:
            for child in blender_object.children:
                self.append_chrome_material(child)
            return

        bm_name = FORMAT_MATERIAL.format("chrome")
        blender_material = self.__data.materials.get(bm_name)
        if not blender_material:
            #print("#DEBUG create material", bm_name)
            blender_material = self.__data.materials.new(bm_name)
            render_engine = self.__scene.render.engine

            #blender internal
            self.__scene.render.engine = 'BLENDER_RENDER'
            blender_material.diffuse_color=color[:3]
            blender_material.specular_color=color[:3]
            blender_material.specular_shader = 'WARDISO'
            blender_material.specular_hardness = 128
            blender_material.specular_slope = 0.020
            blender_material.raytrace_mirror.use = True
            blender_material.raytrace_mirror.reflect_factor = 1.0
            blender_material.raytrace_mirror.depth = 6

            # prepare for nodes
            blender_material.use_nodes = True
            nodes = blender_material.node_tree.nodes
            links = blender_material.node_tree.links
            gap = 50.0
            nodes.clear()

            # blender internal nodes
            node_i0 = nodes.new('ShaderNodeOutput')
            node_i1 = nodes.new('ShaderNodeMaterial')
            node_i1.material = blender_material
            link_i1_0 = links.new(node_i1.outputs['Color'], node_i0.inputs['Color'])
            link_i1_0 = links.new(node_i1.outputs['Alpha'], node_i0.inputs['Alpha'])
            node_i1_height = 410.0 # issue: [#37075] the height of nodes are always 100.0
            node_i1.location = (0.0, node_i1_height + gap)
            node_i0.location = (node_i1.location.x + node_i1.width + gap, node_i1_height + gap)

            # blender cycles nodes
            self.__scene.render.engine = 'CYCLES'
            node_c0 = nodes.new('ShaderNodeOutputMaterial')
            node_c1 = nodes.new('ShaderNodeBsdfGlossy')
            node_c1.inputs['Roughness'].default_value = 0.0
            node_c1.inputs['Color'].default_value = color
            node_c1.location = (0.0, 0.0)
            node_c0.location = (node_c1.location.x + node_c1.width + gap, 0.0)
            link_c1_0 = links.new(node_c1.outputs['BSDF'], node_c0.inputs['Surface'])

            """
            # blender game
            self.__scene.render.engine = 'BLENDER_GAME'
            #TODO
            """

            self.__scene.render.engine = render_engine

        if not blender_object.data.materials.get(bm_name):
            blender_object.data.materials.append(blender_material)

    def append_christal_material(self, blender_object, color=(0.9, 0.9, 0.9, 1.0)):
        if not blender_object:
            return
        if blender_object.type not in {'MESH', 'CURVE', }:
            for child in blender_object.children:
                self.append_chrome_material(child)
            return

        bm_name = FORMAT_MATERIAL.format("christal")
        blender_material = self.__data.materials.get(bm_name)
        if not blender_material:
            #print("#DEBUG create material", bm_name)
            blender_material = self.__data.materials.new(bm_name)
            render_engine = self.__scene.render.engine

            #blender internal
            self.__scene.render.engine = 'BLENDER_RENDER'
            blender_material.diffuse_color=color[:3]
            blender_material.specular_color=color[:3]
            blender_material.specular_shader = 'WARDISO'
            blender_material.specular_hardness = 128
            blender_material.specular_slope = 0.020
            blender_material.raytrace_mirror.use = True
            blender_material.raytrace_mirror.reflect_factor = 1.0
            blender_material.raytrace_mirror.fresnel = 4.0
            blender_material.raytrace_mirror.depth = 6
            blender_material.use_transparency = True
            blender_material.transparency_method = 'RAYTRACE'
            blender_material.raytrace_transparency.ior = 1.45
            blender_material.raytrace_transparency.fresnel = 4.0
            blender_material.raytrace_transparency.filter = 1.0
            blender_material.raytrace_transparency.depth = 6

            # prepare for nodes
            blender_material.use_nodes = True
            nodes = blender_material.node_tree.nodes
            links = blender_material.node_tree.links
            gap = 50.0
            nodes.clear()

            # blender internal nodes
            node_i0 = nodes.new('ShaderNodeOutput')
            node_i1 = nodes.new('ShaderNodeMaterial')
            node_i1.material = blender_material
            link_i1_0 = links.new(node_i1.outputs['Color'], node_i0.inputs['Color'])
            link_i1_0 = links.new(node_i1.outputs['Alpha'], node_i0.inputs['Alpha'])
            node_i1_height = 410.0 # issue: [#37075] the height of nodes are always 100.0
            node_i1.location = (0.0, node_i1_height + gap)
            node_i0.location = (node_i1.location.x + node_i1.width + gap, node_i1_height + gap)

            # blender cycles nodes
            self.__scene.render.engine = 'CYCLES'
            node_c0 = nodes.new('ShaderNodeOutputMaterial')
            node_c1 = nodes.new('ShaderNodeBsdfGlass')
            node_c1.inputs['Roughness'].default_value = 0.0
            node_c1.inputs['Color'].default_value = color
            node_c1.location = (0.0, 0.0)
            node_c0.location = (node_c1.location.x + node_c1.width + gap, 0.0)
            link_c1_0 = links.new(node_c1.outputs['BSDF'], node_c0.inputs['Surface'])

            """
            # blender game
            self.__scene.render.engine = 'BLENDER_GAME'
            #TODO
            """

            self.__scene.render.engine = render_engine

        if not blender_object.data.materials.get(bm_name):
            blender_object.data.materials.append(blender_material)

    def append_light_material(self, blender_object, color=(0.9, 0.9, 0.8, 1.0), strength=10.0):
        if not blender_object:
            return
        if blender_object.type not in {'MESH', 'CURVE', }:
            for child in blender_object.children:
                self.append_chrome_material(child)
            return

        bm_name = FORMAT_MATERIAL.format("light")
        blender_material = self.__data.materials.get(bm_name)
        if not blender_material:
            #print("#DEBUG create material", bm_name)
            blender_material = self.__data.materials.new(bm_name)
            render_engine = self.__scene.render.engine

            #blender internal
            self.__scene.render.engine = 'BLENDER_RENDER'
            blender_material.diffuse_color=color[:3]
            blender_material.specular_color=color[:3]
            blender_material.use_shadeless = True
            blender_material.emit = strength

            # prepare for nodes
            blender_material.use_nodes = True
            nodes = blender_material.node_tree.nodes
            links = blender_material.node_tree.links
            gap = 50.0
            nodes.clear()

            # blender internal nodes
            node_i0 = nodes.new('ShaderNodeOutput')
            node_i1 = nodes.new('ShaderNodeMaterial')
            node_i1.material = blender_material
            link_i1_0 = links.new(node_i1.outputs['Color'], node_i0.inputs['Color'])
            link_i1_0 = links.new(node_i1.outputs['Alpha'], node_i0.inputs['Alpha'])
            node_i1_height = 410.0 # issue: [#37075] the height of nodes are always 100.0
            node_i1.location = (0.0, node_i1_height + gap)
            node_i0.location = (node_i1.location.x + node_i1.width + gap, node_i1_height + gap)

            # blender cycles nodes
            self.__scene.render.engine = 'CYCLES'
            node_c0 = nodes.new('ShaderNodeOutputMaterial')
            node_c1 = nodes.new('ShaderNodeEmission')
            node_c1.inputs['Strength'].default_value = strength
            node_c1.inputs['Color'].default_value = color
            node_c1.location = (0.0, 0.0)
            node_c0.location = (node_c1.location.x + node_c1.width + gap, 0.0)
            link_c1_0 = links.new(node_c1.outputs['Emission'], node_c0.inputs['Surface'])

            """
            # blender game
            self.__scene.render.engine = 'BLENDER_GAME'
            #TODO
            """

            self.__scene.render.engine = render_engine

        if not blender_object.data.materials.get(bm_name):
            blender_object.data.materials.append(blender_material)

    def apply_uv_map_from_texspace(self, blender_object, fpx_image_name):
        box_x = blender_object.bound_box[0][0]
        box_y = blender_object.bound_box[0][1]
        tex_size_width = blender_object.data.texspace_size[0] * 2.0
        tex_size_length = blender_object.data.texspace_size[1] * 2.0
        tex_loc_x = blender_object.data.texspace_location[0]
        tex_loc_y = blender_object.data.texspace_location[1]

        offset_x = tex_size_width - 2.0 * (tex_loc_x - box_x)
        offset_y = tex_size_length - 2.0 * (tex_loc_y - box_y)

        blender_object.select = True
        self.__scene.objects.active = blender_object
        self.__scene.update()
        if ops.object.convert.poll():
            ops.object.convert()

        mesh = blender_object.data

        bm = bmesh.new()
        bm.from_mesh(mesh)

        uv_layer = bm.loops.layers.uv.new("UVMap")
        tex_layer = bm.faces.layers.tex.new(uv_layer.name)

        blender_image = None
        if fpx_image_name:
            #print("#DEBUG fpx_image_name *:", fpx_image_name)
            fpx_image_object = self.fpx_images.get(fpx_image_name)
            if not fpx_image_object:
                fpx_image_name = FpxUtilities.toGoodName(fpx_image_name)
                fpx_image_object = self.fpx_images.get(fpx_image_name)
                #print("#DEBUG fpx_image_name **:", fpx_image_name)
            if fpx_image_object:
                blender_image = self.__data.images.get(fpx_image_object[self.BLENDER_OBJECT_NAME])
            else:
                print("#DEBUG fpx_image_name ***:", fpx_image_name, "not found")

        for bmf in bm.faces:
            for ivert, bmv in enumerate(bmf.verts):
                u = ((0.5 * offset_x + (bmv.co[0] - box_x)) / tex_size_width)
                v = ((0.5 * offset_y + (bmv.co[1] - box_y)) / tex_size_length)
                while u < 0:
                    u += 1
                while v < 0:
                    v += 1
                bmf.loops[ivert][uv_layer].uv = (u, v)

            if blender_image:
                bmf[tex_layer].image = blender_image

        bm.to_mesh(mesh)
        bm.free()

    ###########################################################################
    def CreatePinCab(self, fpx_table_data):
        name = fpx_table_data.get_value("name")
        name = FpxUtilities.toGoodName(name) ####

        dy = fpx_table_data.get_value("length")
        dx = fpx_table_data.get_value("width")
        z0 = fpx_table_data.get_value("glass_height_front")
        z1 = fpx_table_data.get_value("glass_height_rear")
        dtx = fpx_table_data.get_value("translite_height")
        dtz = fpx_table_data.get_value("translite_width")
        texture_table = fpx_table_data.get_value("playfield_texture")
        texture_translite = fpx_table_data.get_value("translite_image")

        texture_table = FpxUtilities.toGoodName(texture_table) ####
        texture_translite = FpxUtilities.toGoodName(texture_translite) ####

        if not dtx:
            dtx = 676.0
        if not dtz:
            dtz = 676.0

        self.__translite_width = dtx
        self.__translite_length = dtz

        self.__table_width = dx
        self.__table_length = dy

        mesh = self.__data.meshes.new(FORMAT_MESH.format(name))
        obj = self.__data.objects.new(FORMAT_MESH_OBJECT.format(name), mesh)
        self.__scene.objects.link(obj)
        obj.layers = FptImporter.LAYERS_AO

        #inner playfield
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")
        tex_layer = bm.faces.layers.tex.new(uv_layer.name)
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((0.0, 0.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((0.0, dy, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, dy, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, 0.0, 0.0)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)
        bmluv = bmf.loops[0][uv_layer]
        bmluv.uv = (0.0, 1.0)
        bmluv = bmf.loops[1][uv_layer]
        bmluv.uv = (0.0, 0.0)
        bmluv = bmf.loops[2][uv_layer]
        bmluv.uv = (1.0, 0.0)
        bmluv = bmf.loops[3][uv_layer]
        bmluv.uv = (1.0, 1.0)
        if texture_table:
            fpx_image_object = self.fpx_images.get(texture_table)
            if fpx_image_object:
                bmf[tex_layer].image = self.__data.images.get(fpx_image_object[self.BLENDER_OBJECT_NAME])
                self.append_texture_material(obj, texture_table, uv_layer=uv_layer.name)
        bm.to_mesh(mesh)
        bm.free()

        mesh_box = self.__data.meshes.new(FORMAT_MESH.format("{}.playfield".format(name)))
        obj_box = self.__data.objects.new(FORMAT_MESH_OBJECT.format("{}.playfield".format(name)), mesh_box)
        obj_box.parent = obj
        self.__scene.objects.link(obj_box)
        obj_box.layers = FptImporter.LAYERS_AO

        bm = bmesh.new()
        #inner back
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((0.0, 0.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, 0.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, 0.0, z1)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((0.0, 0.0, z1)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)

        #inner front
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((0.0, dy, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((0.0, dy, z0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, dy, z0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, dy, 0.0)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)

        #inner left
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((0.0, 0.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((0.0, 0.0, z1)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((0.0, dy, z0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((0.0, dy, 0.0)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)

        #inner right
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((dx, 0.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, dy, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, dy, z0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((dx, 0.0, z1)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)

        bm.to_mesh(mesh_box)
        bm.free()

        ##
        mesh_translite = self.__data.meshes.new(FORMAT_MESH.format("{}.translite".format(name)))
        obj_translite = self.__data.objects.new(FORMAT_MESH_OBJECT.format("{}.translite".format(name)), mesh_translite)
        obj_translite.parent = obj
        self.__scene.objects.link(obj_translite)
        obj_translite.layers = FptImporter.LAYERS_AO

        #inner translite
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")
        tex_layer = bm.faces.layers.tex.new(uv_layer.name)
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction(((dx - dtx) / 2.0, 0.0, z1 + 20.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction(((dx + dtx) / 2.0, 0.0, z1 + 20.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction(((dx + dtx) / 2.0, 0.0, z1 + 20.0 + dtz)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction(((dx - dtx) / 2.0, 0.0, z1 + 20.0 + dtz)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)
        bmluv = bmf.loops[0][uv_layer]
        bmluv.uv = (0.0, 0.0)
        bmluv = bmf.loops[1][uv_layer]
        bmluv.uv = (1.0, 0.0)
        bmluv = bmf.loops[2][uv_layer]
        bmluv.uv = (1.0, 1.0)
        bmluv = bmf.loops[3][uv_layer]
        bmluv.uv = (0.0, 1.0)
        if texture_translite:
            fpx_image_object = self.fpx_images.get(texture_translite)
            if fpx_image_object:
                bmf[tex_layer].image = self.__data.images.get(fpx_image_object[self.BLENDER_OBJECT_NAME])
                self.append_texture_material(obj_translite, texture_translite, light_on=True, uv_layer=uv_layer.name)
        bm.to_mesh(mesh_translite)
        bm.free()

        return obj

    def CreateSurface(self, fpx_item, name, layers, fpx_points):
        top = fpx_item.get_value("top_height")
        bottom = fpx_item.get_value("bottom_height")
        cookie_cut = fpx_item.get_value("cookie_cut")
        texture = fpx_item.get_value("top_texture")
        sphere_map_the_top = fpx_item.get_value("sphere_map_the_top")
        transparency = fpx_item.get_value("transparency")

        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_shape)

        modifier_edge_split = obj.modifiers.new("edge_split", type='EDGE_SPLIT')

        if top is None:
            top = 0.0
        if bottom is None:
            bottom = 0.0
        cu.extrude = (top - bottom) / 2.0
        cu.dimensions = '2D'

        act_spline.use_cyclic_u = True
        self.create_curve_points(act_spline, fpx_points)

        obj.location = Vector((obj.location.x, obj.location.y, (top - cu.extrude)))
        if cookie_cut:
            cu.use_auto_texspace = False
            cu.texspace_location = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
            cu.texspace_size = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
        else:
            cu.use_auto_texspace = False
            self.__scene.update()
            cu.texspace_location = Vector(obj.bound_box[0]) + (obj.dimensions / 2.0)
            cu.texspace_size = Vector(obj.dimensions / 2.0)

        if self.convert_to_mesh:
            self.apply_uv_map_from_texspace(obj, texture)

        if texture and not sphere_map_the_top:
            if self.convert_to_mesh:
                self.append_texture_material(obj, texture, uv_layer='UVMap')
            else:
                self.append_texture_material(obj, texture)
        elif transparency:
            self.append_christal_material(obj)

        return obj

    def CreateRubberShapeable(self, fpx_item, name, layers, fpx_points, surface):
        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_shape)

        bevel_name = "__fpx_rubber_shapeable_bevel__"
        rubber_bevel = self.__data.objects.get(bevel_name)
        if rubber_bevel is None:
            scale = 2.4
            rubber_bevel = self.create_bevel(bevel_name, scale, self.resolution_rubber)

        cu.bevel_object = rubber_bevel

        offset = 2.5
        act_spline.use_cyclic_u = True
        self.create_curve_points(act_spline, fpx_points, (surface + offset))

        return obj

    def CreateRubberRound(self, fpx_item, name, layers, position_xy, surface):
        subtype = fpx_item.get_value("subtype")

        #diameter = [44, 18.5, 13.5, 12, ]
        diameter = [13.5, 18.5, 12, 44, ]

        bevel_name = "__fpx_guide_rubber_bevel__"
        rubber_bevel = self.__data.objects.get(bevel_name)
        if rubber_bevel is None:
            cu0 = self.__data.curves.new(bevel_name, 'CURVE')
            rubber_bevel = self.__data.objects.new(bevel_name, cu0)
            self.__scene.objects.link(rubber_bevel)
            cu0.dimensions = '2D'
            cu0.resolution_u = self.resolution_rubber_bevel

            h = 'AUTO'
            cu0.splines.new('BEZIER')
            p0 = Vector((0.0, 0.0, 0.0))
            s0 = 5.0 / 2.0
            spline0 = cu0.splines[-1]
            spline0.resolution_u = self.resolution_rubber_bevel
            spline0.use_cyclic_u = True
            spline0.bezier_points.add(3)
            spline0.bezier_points[0].co = p0 + Vector((0.0, -s0, 0.0))
            spline0.bezier_points[0].handle_left_type = h
            spline0.bezier_points[0].handle_right_type = h
            spline0.bezier_points[1].co = p0 + Vector((-s0, 0.0, 0.0))
            spline0.bezier_points[1].handle_left_type = h
            spline0.bezier_points[1].handle_right_type = h
            spline0.bezier_points[2].co = p0 + Vector((0.0, s0, 0.0))
            spline0.bezier_points[2].handle_left_type = h
            spline0.bezier_points[2].handle_right_type = h
            spline0.bezier_points[3].co = p0 + Vector((s0, 0.0, 0.0))
            spline0.bezier_points[3].handle_left_type = h
            spline0.bezier_points[3].handle_right_type = h

        obj, cu1, spline1 = self.create_curve(name, layers, self.resolution_rubber)

        h = 'AUTO'
        p1 = self.geometry_correction((position_xy[0], position_xy[1], surface + 2.5))
        s1 = (diameter[subtype] - 5.0) / 2.0
        spline1.use_cyclic_u = True
        spline1.resolution_u = self.resolution_rubber * 2
        spline1.bezier_points.add(3)
        spline1.bezier_points[0].co = p1 + Vector((0.0, -s1, 0.0))
        spline1.bezier_points[0].handle_left_type = h
        spline1.bezier_points[0].handle_right_type = h
        spline1.bezier_points[1].co = p1 + Vector((-s1, 0.0, 0.0))
        spline1.bezier_points[1].handle_left_type = h
        spline1.bezier_points[1].handle_right_type = h
        spline1.bezier_points[2].co = p1 + Vector((0.0, s1, 0.0))
        spline1.bezier_points[2].handle_left_type = h
        spline1.bezier_points[2].handle_right_type = h
        spline1.bezier_points[3].co = p1 + Vector((s1, 0.0, 0.0))
        spline1.bezier_points[3].handle_left_type = h
        spline1.bezier_points[3].handle_right_type = h

        cu1.bevel_object = rubber_bevel

        return obj

    def CreateGuideWire(self, fpx_item, name, layers, fpx_points, surface):
        height = fpx_item.get_value("height")
        width = fpx_item.get_value("width")

        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_wire)
        self.append_chrome_material(obj)

        if height is None:
            height = 0.0
        if width is not None:
            bevel_name = "__fpx_guide_wire_bevel_{}__".format(width)
            wire_bevel = self.__data.objects.get(bevel_name)
            if wire_bevel is None:
                scale = width / 2.0
                wire_bevel = self.create_bevel(bevel_name, scale, self.resolution_wire_bevel)

            cu.bevel_object = wire_bevel
            cu.use_fill_caps = True
        else:
            width = 0.0

        act_spline.use_cyclic_u = False
        self.create_curve_points(act_spline, fpx_points, (surface + height + width / 2.0))

        # create pole caps
        co1 = act_spline.bezier_points[0].co
        h_left1 = act_spline.bezier_points[0].handle_left
        h_right1 = act_spline.bezier_points[0].handle_right
        co2 = act_spline.bezier_points[-1].co
        h_left2 = act_spline.bezier_points[-1].handle_left
        h_right2 = act_spline.bezier_points[-1].handle_right
        self.create_wire_pole(cu.splines, co1, h_left1, h_right1, surface, width)
        self.create_wire_pole(cu.splines, co2, h_right2, h_left2, surface, width)

        # merge wire curve with pole caps
        self.__scene.objects.active = obj
        self.merge_caps(cu.splines, width)

        cu.splines[0].type = 'NURBS' # looks better for wires
        cu.twist_mode = 'MINIMUM'

        return obj

    def CreateGuideWall(self, fpx_item, name, layers, fpx_points, surface):
        height = fpx_item.get_value("height")
        width = fpx_item.get_value("width")
        cookie_cut = fpx_item.get_value("cookie_cut")
        texture = fpx_item.get_value("top_texture")
        sphere_map_the_top = fpx_item.get_value("sphere_map_the_top")

        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_shape)

        modifier_solidify = obj.modifiers.new("width", type='SOLIDIFY')
        modifier_solidify.thickness = width
        modifier_solidify.offset = 0.0
        modifier_solidify.use_even_offset = True

        modifier_edge_split = obj.modifiers.new("edge_split", type='EDGE_SPLIT')

        if height is None:
            height = 0.0
        cu.extrude = height / 2.0
        cu.dimensions = '2D'

        act_spline.use_cyclic_u = False
        self.create_curve_points(act_spline, fpx_points)

        obj.location = Vector((obj.location.x, obj.location.y, (surface + cu.extrude)))

        if cookie_cut:
            cu.use_auto_texspace = False
            cu.texspace_location = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
            cu.texspace_size = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
        else:
            cu.use_auto_texspace = False
            self.__scene.update()
            cu.texspace_location = Vector(obj.bound_box[0]) + (obj.dimensions / 2.0)
            cu.texspace_size = Vector(obj.dimensions / 2.0)

        if self.convert_to_mesh:
            self.apply_uv_map_from_texspace(obj, texture)

        if texture and not sphere_map_the_top:
            if self.convert_to_mesh:
                self.append_texture_material(obj, texture, uv_layer='UVMap')
            else:
                self.append_texture_material(obj, texture)

        return obj

    def CreateLightRound(self, fpx_item, name, layers, position_xy, surface):
        diameter = fpx_item.get_value("diameter")
        cookie_cut = fpx_item.get_value("cookie_cut")
        texture = fpx_item.get_value("lens_texture")

        obj, cu, spline = self.create_curve(name, layers, self.resolution_shape)

        modifier_edge_split = obj.modifiers.new("edge_split", type='EDGE_SPLIT')

        h = 'AUTO'
        p0 = self.geometry_correction((position_xy[0], position_xy[1], 0.0))
        d = diameter / 2.0
        spline.bezier_points.add(3)
        spline.bezier_points[0].co = p0 + Vector((0.0, -d, 0.0))
        spline.bezier_points[0].handle_left_type = h
        spline.bezier_points[0].handle_right_type = h
        spline.bezier_points[1].co = p0 + Vector((-d, 0.0, 0.0))
        spline.bezier_points[1].handle_left_type = h
        spline.bezier_points[1].handle_right_type = h
        spline.bezier_points[2].co = p0 + Vector((0.0, d, 0.0))
        spline.bezier_points[2].handle_left_type = h
        spline.bezier_points[2].handle_right_type = h
        spline.bezier_points[3].co = p0 + Vector((d, 0.0, 0.0))
        spline.bezier_points[3].handle_left_type = h
        spline.bezier_points[3].handle_right_type = h
        spline.use_cyclic_u = True

        cu.extrude = self.debug_light_extrude
        cu.dimensions = '2D'

        obj.location = Vector((obj.location.x, obj.location.y, surface))

        if texture:
            if cookie_cut:
                cu.use_auto_texspace = False
                cu.texspace_location = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
                cu.texspace_size = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
            else:
                cu.use_auto_texspace = False
                self.__scene.update()
                cu.texspace_location = Vector(obj.bound_box[0]) + (obj.dimensions / 2.0)
                cu.texspace_size = Vector(obj.dimensions / 2.0)
        else:
            self.append_texture_material(obj, DEFAULT_LAMP_TEXTURE, light_on=True)
            cu.use_auto_texspace = False
            #obj.update_from_editmode()
            self.__scene.update()
            cu.texspace_location = Vector(obj.bound_box[0]) + (obj.dimensions / 2.0)
            size = max(obj.dimensions)
            cu.texspace_size = (size, size, 0)

        if self.convert_to_mesh:
            self.apply_uv_map_from_texspace(obj, texture)

        if texture:
            if self.convert_to_mesh:
                self.append_texture_material(obj, texture, uv_layer='UVMap', light_on=True)
            else:
                self.append_texture_material(obj, texture, light_on=True)

        return obj

    def CreateLightShapeable(self, fpx_item, name, layers, fpx_points, surface):
        cookie_cut = fpx_item.get_value("cookie_cut")
        texture = fpx_item.get_value("lens_texture")

        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_shape)

        modifier_edge_split = obj.modifiers.new("edge_split", type='EDGE_SPLIT')

        cu.extrude = self.debug_light_extrude
        cu.dimensions = '2D'

        act_spline.use_cyclic_u = True
        self.create_curve_points(act_spline, fpx_points)

        obj.location = Vector((obj.location.x, obj.location.y, surface))

        if texture:
            if cookie_cut:
                cu.use_auto_texspace = False
                cu.texspace_location = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
                cu.texspace_size = Vector((self.__table_width / 2.0, self.__table_length / 2.0, 0))
            else:
                cu.use_auto_texspace = False
                self.__scene.update()
                cu.texspace_location = Vector(obj.bound_box[0]) + (obj.dimensions / 2.0)
                cu.texspace_size = Vector(obj.dimensions / 2.0)
        else:
            self.append_texture_material(obj, DEFAULT_LAMP_TEXTURE, light_on=True)
            cu.use_auto_texspace = False
            #obj.update_from_editmode()
            self.__scene.update()
            cu.texspace_location = Vector(obj.bound_box[0]) + (obj.dimensions / 2.0)
            size = max(obj.dimensions)
            cu.texspace_size = (size, size, 0)

        if self.convert_to_mesh:
            self.apply_uv_map_from_texspace(obj, texture)

        if texture:
            if self.convert_to_mesh:
                self.append_texture_material(obj, texture, uv_layer='UVMap', light_on=True)
            else:
                self.append_texture_material(obj, texture, light_on=True)

        return obj

    def CreateLightImage(self, fpx_item, name, layers, position_xy, surface):
        height = fpx_item.get_value("height")
        width = fpx_item.get_value("width")
        rotation = fpx_item.get_value("rotation")
        image_list = fpx_item.get_value("image_list")

        mesh = self.__data.meshes.new(FORMAT_MESH.format(name))
        obj = self.__data.objects.new(FORMAT_MESH_OBJECT.format(name), mesh)
        self.__scene.objects.link(obj)

        z = surface + self.debug_light_extrude
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")
        tex_layer = bm.faces.layers.tex.new(uv_layer.name)
        bmv_list = []
        bmv = bm.verts.new(self.geometry_correction((-width / 2.0, height / 2.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((width / 2.0, height / 2.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((width / 2.0, -height / 2.0, 0.0)))
        bmv_list.append(bmv)
        bmv = bm.verts.new(self.geometry_correction((-width / 2.0, -height / 2.0, 0.0)))
        bmv_list.append(bmv)
        bmf = bm.faces.new(bmv_list)
        bmluv = bmf.loops[0][uv_layer]
        bmluv.uv = (0.0, 1.0)
        bmluv = bmf.loops[1][uv_layer]
        bmluv.uv = (0.0, 0.0)
        bmluv = bmf.loops[2][uv_layer]
        bmluv.uv = (1.0, 0.0)
        bmluv = bmf.loops[3][uv_layer]
        bmluv.uv = (1.0, 1.0)
        if image_list:
            image_list_data = self.fpx_image_lists.get(image_list)
            if image_list_data:
                fpx_image_name = image_list_data[-1] # -1 for light on, 0 for light off
                fpx_image_name = FpxUtilities.toGoodName(fpx_image_name) ####
                fpx_image_object = self.fpx_images.get(fpx_image_name)
                if fpx_image_object:
                    bmf[tex_layer].image = self.__data.images.get(fpx_image_object[self.BLENDER_OBJECT_NAME])
                    self.append_texture_material(obj, fpx_image_name, uv_layer=uv_layer.name, light_on=True)
        bm.to_mesh(mesh)
        bm.free()

        obj.location = self.geometry_correction((position_xy[0], position_xy[1], z))
        obj.rotation_mode = 'XZY'
        obj.rotation_euler = Euler((0.0, 0.0, radians(self.angle_correction(rotation))), obj.rotation_mode)
        return obj

    def CreateWireRamp(self, fpx_item, name, layers, fpx_points, surface, fpx_id):
        start_height = fpx_item.get_value("start_height")
        end_height = fpx_item.get_value("end_height")
        model_name_start = fpx_item.get_value("model_start")
        model_name_end = fpx_item.get_value("model_end")

        if start_height is None:
            start_height = 0.0
        if end_height is None:
            end_height = 0.0

        wire_bevel = self.prepare_wire_ramp_bevel()

        #"ramp_point"
        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_wire)
        self.append_chrome_material(obj)

        cu.bevel_object = wire_bevel
        cu.use_fill_caps = True

        act_spline.use_cyclic_u = False
        self.create_ramp_curve_points(act_spline, fpx_points, surface, start_height, end_height)

        # ramp start
        if model_name_start:
            blender_empty_object = self.__data.objects.new(FORMAT_EMPTY_OBJECT.format(FORMAT_MODEL_CAP1.format(name)), None)
            blender_empty_object.location = cu.splines[-1].bezier_points[0].co
            blender_empty_object.rotation_mode = 'XZY'
            v = (cu.splines[-1].bezier_points[0].handle_left - cu.splines[-1].bezier_points[0].co)
            blender_empty_object.rotation_euler = Euler((0, 0, Vector((v.x, v.y)).angle_signed(Vector((1.0, 0.0)))), 'XZY')
            blender_empty_object.empty_draw_type = 'ARROWS'
            blender_empty_object.empty_draw_size = 10.0
            self.__scene.objects.link(blender_empty_object)
            blender_empty_object.fpt.name = FORMAT_EMPTY_OBJECT.format(FORMAT_MODEL_START.format(name))
            if fpx_id:
                blender_empty_object.fpt.id = FptElementType.VALUE_INT_TO_NAME.get(fpx_id)
            blender_object = self.attach_dupli_group(blender_empty_object, FptImporter.LAYERS_WIRE_RING, model_name_start, "model_start")
            self.append_chrome_material(blender_object)
            blender_empty_object.layers = FptImporter.LAYERS_WIRE_RING

        # ramp end
        if model_name_end:
            blender_empty_object = self.__data.objects.new(FORMAT_EMPTY_OBJECT.format(FORMAT_MODEL_CAP2.format(name)), None)
            blender_empty_object.location = cu.splines[-1].bezier_points[-1].co
            blender_empty_object.rotation_mode = 'XZY'
            v = (cu.splines[-1].bezier_points[-1].handle_right - cu.splines[-1].bezier_points[-1].co)
            blender_empty_object.rotation_euler = Euler((0, 0, Vector((v.x, v.y)).angle_signed(Vector((1.0, 0.0)))), 'XZY')
            blender_empty_object.empty_draw_type = 'ARROWS'
            blender_empty_object.empty_draw_size = 10.0
            self.__scene.objects.link(blender_empty_object)
            blender_empty_object.fpt.name = FORMAT_EMPTY_OBJECT.format(FORMAT_MODEL_END.format(name))
            if fpx_id:
                blender_empty_object.fpt.id = FptElementType.VALUE_INT_TO_NAME.get(fpx_id)
            blender_object = self.attach_dupli_group(blender_empty_object, FptImporter.LAYERS_WIRE_RING, model_name_end, "model_end")
            self.append_chrome_material(blender_object)
            blender_empty_object.layers = FptImporter.LAYERS_WIRE_RING

        # create rings
        wire_ring_model = [
                None, # NoRing
                'wirering01', # FullRing = 1
                'wirering02', # OpenUp = 2
                'wirering04', # OpenRight = 3
                'wirering03', # OpenDown = 4
                'wirering05', # OpenLeft = 5
                'wirering06', # HalfLeft = 6
                'wirering07', # HalfRight = 7
                'wirering08', # Joiner = 8
                'wirering09', # HalfDown = 9
                'wirering10', # HalfUp = 10
                'wirering14', # OpenUPLeft = 11
                'wirering13', # OpenDownLeft = 12
                'wirering12', # OpenDownRight = 13
                'wirering11', # OpenUPRight = 14
                'wirering15', # Split = 15
                'wirering17', # QuarterRight = 16
                'wirering16', # QuarterLeft = 17
                'wirering19', # CresentRight = 18
                'wirering18', # CresentLeft = 19
                ]

        left_wires_bevel = self.prepare_wire_ramp_side_bevel(2)
        right_wires_bevel = self.prepare_wire_ramp_side_bevel(3)
        left_upper_wires_bevel = self.prepare_wire_ramp_side_bevel(4)
        right_upper_wires_bevel = self.prepare_wire_ramp_side_bevel(5)
        top_wires_bevel = self.prepare_wire_ramp_side_bevel(6)

        last_bezier_point = None
        last_fpx_point = None

        last_left_wire = None
        last_right_wire = None
        last_left_upper_wire = None
        last_right_upper_wire = None
        last_top_wire = None

        for index, fpx_point in enumerate(fpx_points):
            bezier_point = act_spline.bezier_points[index]

            if self.debug_create_full_ramp_wires:
                pass
            else:
                """
                there are problems, see [#36007] https://developer.blender.org/T36007
                """
                if index:
                    if last_fpx_point.get_value("left_guide"):
                        last_left_wire = self.create_wire_ramp_guide_piece(name, obj, layers, left_wires_bevel, 2, index, last_bezier_point, bezier_point, last_left_wire)
                    else:
                        last_left_wire = None

                    if last_fpx_point.get_value("right_guide"):
                        last_right_wire = self.create_wire_ramp_guide_piece(name, obj, layers, right_wires_bevel, 3, index, last_bezier_point, bezier_point, last_right_wire)
                    else:
                        last_right_wire = None

                    if last_fpx_point.get_value("left_upper_guide"):
                        last_left_upper_wire = self.create_wire_ramp_guide_piece(name, obj, layers, left_upper_wires_bevel, 4, index, last_bezier_point, bezier_point, last_left_upper_wire)
                    else:
                        last_left_upper_wire = None

                    if last_fpx_point.get_value("right_upper_guide"):
                        last_right_upper_wire = self.create_wire_ramp_guide_piece(name, obj, layers, right_upper_wires_bevel, 5, index, last_bezier_point, bezier_point, last_right_upper_wire)
                    else:
                        last_right_upper_wire = None

                    if last_fpx_point.get_value("top_wire"):
                        last_top_wire = self.create_wire_ramp_guide_piece(name, obj, layers, top_wires_bevel, 6, index, last_bezier_point, bezier_point, last_top_wire)
                    else:
                        last_top_wire = None


            last_bezier_point = bezier_point
            last_fpx_point = fpx_point

            type = fpx_point.get_value("ring_type")
            raw_model_name = wire_ring_model[type]
            if raw_model_name is None:
                continue

            blender_empty_object = self.__data.objects.new(FORMAT_EMPTY_OBJECT.format(FORMAT_MODEL_RING.format(name, index)), None)
            blender_empty_object.location = bezier_point.co
            blender_empty_object.rotation_mode = 'XZY'
            v = (bezier_point.handle_right - bezier_point.co)
            blender_empty_object.rotation_euler = Euler((0, 0, Vector((v.x, v.y)).angle_signed(Vector((1.0, 0.0)))), 'XZY')
            blender_empty_object.empty_draw_type = 'ARROWS'
            blender_empty_object.empty_draw_size = 10.0
            self.__scene.objects.link(blender_empty_object)
            blender_empty_object.fpt.name = FORMAT_MODEL_RING.format(name, index)
            if fpx_id:
                blender_empty_object.fpt.id = FptElementType.VALUE_INT_TO_NAME.get(fpx_id)
            blender_object = self.attach_dupli_group(blender_empty_object, FptImporter.LAYERS_WIRE_RING, raw_model_name, 'LOCAL')
            self.append_chrome_material(blender_object)
            blender_empty_object.layers = FptImporter.LAYERS_WIRE_RING

        #cu.splines[0].type = 'NURBS' # looks better for wires
        #cu.twist_mode = 'MINIMUM'
        return obj

    def create_wire_ramp_guide_piece(self, name, parent_obj, layers, wire_bevel, wire_index, point_index, last_bezier_point_template, bezier_point_template, last_object):
        if last_object:
            #reuse previous curve
            spline = last_object.data.splines[0]
            spline.bezier_points.add(1)
            bezier_point = spline.bezier_points[-1]
            bezier_point.co = bezier_point_template.co
            bezier_point.radius = bezier_point_template.radius
            bezier_point.handle_left_type = bezier_point_template.handle_left_type
            bezier_point.handle_right_type = bezier_point_template.handle_right_type
            bezier_point.handle_left = bezier_point_template.handle_left
            bezier_point.handle_right = bezier_point_template.handle_right
            bezier_point.tilt = bezier_point_template.tilt
            obj = last_object
        else:
            #start to make a new curve
            sub_name = "{}_{}_{}".format(name, wire_index, point_index-1)

            obj, cu, spline = self.create_curve(sub_name, layers, self.resolution_wire)
            self.append_chrome_material(obj)
            obj.fpt.name = sub_name
            obj.parent = parent_obj
            cu.bevel_object = wire_bevel
            cu.use_fill_caps = True
            spline.use_cyclic_u = False

            spline.bezier_points.add(1)
            bezier_point = spline.bezier_points[0]
            bezier_point.co = last_bezier_point_template.co
            bezier_point.radius = last_bezier_point_template.radius
            bezier_point.handle_left_type = last_bezier_point_template.handle_left_type
            bezier_point.handle_right_type = last_bezier_point_template.handle_right_type
            bezier_point.handle_left = last_bezier_point_template.handle_left
            bezier_point.handle_right = last_bezier_point_template.handle_right
            bezier_point.tilt = last_bezier_point_template.tilt

            bezier_point = spline.bezier_points[1]
            bezier_point.co = bezier_point_template.co
            bezier_point.radius = bezier_point_template.radius
            bezier_point.handle_left_type = bezier_point_template.handle_left_type
            bezier_point.handle_right_type = bezier_point_template.handle_right_type
            bezier_point.handle_left = bezier_point_template.handle_left
            bezier_point.handle_right = bezier_point_template.handle_right
            bezier_point.tilt = bezier_point_template.tilt

        return obj

    def CreateRamp(self, fpx_item, name, layers, fpx_points, surface):
        start_height = fpx_item.get_value("start_height")
        end_height = fpx_item.get_value("end_height")
        start_width = fpx_item.get_value("start_width")
        end_width = fpx_item.get_value("end_width")
        height_left = fpx_item.get_value("left_side_height")
        height_right = fpx_item.get_value("right_side_height")

        if start_width is None:
            start_width = 0.0
        if end_width is None:
            end_width = 0.0

        if height_left is None:
            height_left = 0.0
        if height_right is None:
            height_right = 0.0

        bevel_name = "__fpx_guide_ramp_wire_bevel_{}_{}_{}__".format(start_width, height_left, height_right, )
        wire_bevel = self.__data.objects.get(bevel_name)
        if wire_bevel is None:
            cu = self.__data.curves.new(bevel_name, 'CURVE')
            wire_bevel = self.__data.objects.new(bevel_name, cu)
            self.__scene.objects.link(wire_bevel)
            cu.dimensions = '2D'
            cu.resolution_u = self.resolution_shape

            h = 'VECTOR'
            cu.splines.new('BEZIER')
            spline0 = cu.splines[-1]
            spline0.resolution_u = self.resolution_shape
            p0 = Vector((0.0, 0.0, 0.0))
            spline0.use_cyclic_u = False
            spline0.bezier_points.add(3)
            spline0.bezier_points[0].co = p0 + Vector((-start_width / 2.0, height_left, 0.0))
            spline0.bezier_points[0].handle_left_type = h
            spline0.bezier_points[0].handle_right_type = h
            spline0.bezier_points[1].co = p0 + Vector((-start_width / 2.0, 0.0, 0.0))
            spline0.bezier_points[1].handle_left_type = h
            spline0.bezier_points[1].handle_right_type = h
            spline0.bezier_points[2].co = p0 + Vector((start_width / 2.0, 0.0, 0.0))
            spline0.bezier_points[2].handle_left_type = h
            spline0.bezier_points[2].handle_right_type = h
            spline0.bezier_points[3].co = p0 + Vector((start_width / 2.0, height_right, 0.0))
            spline0.bezier_points[3].handle_left_type = h
            spline0.bezier_points[3].handle_right_type = h

        #"ramp_point"
        obj, cu, act_spline = self.create_curve(name, layers, self.resolution_wire)

        modifier_solidify = obj.modifiers.new("solidify", type='SOLIDIFY')
        modifier_solidify.offset = 0.0
        modifier_solidify.thickness = 1.0
        modifier_edge_split = obj.modifiers.new("edge_split", type='EDGE_SPLIT')

        cu.bevel_object = wire_bevel
        cu.use_fill_caps = False


        if start_height is None:
            start_height = 0.0
        if end_height is None:
            end_height = 0.0

        self.create_ramp_curve_points(act_spline, fpx_points, surface, start_height, end_height, start_width, end_width)

        return obj

    def create_wire_pole(self, cu_splines, co, t, ti, surface, width):
        d = (t - co)
        dn = d.normalized()
        w = width / 2.0
        dw = dn * w
        co_dw = co + dw

        cu_splines.new('BEZIER')
        act_spline = cu_splines[-1]
        act_spline.use_cyclic_u = False

        point_0 = act_spline.bezier_points[-1]
        point_0.co = Vector((co_dw.x, co_dw.y, co.z - w))
        point_0.handle_left_type = 'ALIGNED'
        point_0.handle_right_type = 'ALIGNED'
        point_0.handle_left = Vector((point_0.co.x, point_0.co.y, point_0.co.z + w))
        point_0.handle_right = Vector((point_0.co.x, point_0.co.y, point_0.co.z - w))

        act_spline.bezier_points.add()
        point_1 = act_spline.bezier_points[-1]
        point_1.co = Vector((co_dw.x, co_dw.y, surface))
        point_1.handle_left_type = 'ALIGNED'
        point_1.handle_right_type = 'ALIGNED'
        point_1.handle_left = Vector((point_1.co.x, point_1.co.y, point_1.co.z + (co.z - surface) / 4.0))
        point_1.handle_right = Vector((point_1.co.x, point_1.co.y, point_1.co.z - (co.z - surface) / 4.0))

    def merge_caps(self, cu_splines, width):
        w = width / 2.0

        # adjust endpoint of curve
        b_point = cu_splines[0].bezier_points[0]
        co = b_point.co.copy()
        h_left = b_point.handle_left.copy()
        h_right = b_point.handle_right.copy()
        b_point.handle_left_type = 'ALIGNED'
        b_point.handle_right_type = 'ALIGNED'
        b_point.handle_left = co + ((h_left - co).normalized() * w)
        b_point.handle_right = co + ((h_right - co).normalized() * w)
        # select endpoint of curve and start-point of pole-cap
        cu_splines[0].bezier_points[0].select_control_point = True
        cu_splines[1].bezier_points[0].select_control_point = True
        # merge curve an pole
        FpxUtilities.enable_edit_mode(True, self.__context)
        if ops.curve.make_segment.poll():
            ops.curve.make_segment()
        FpxUtilities.enable_edit_mode(False, self.__context)

        # adjust endpoint of curve
        b_point = cu_splines[0].bezier_points[-1]
        co = b_point.co.copy()
        h_left = b_point.handle_left.copy()
        h_right = b_point.handle_right.copy()
        b_point.handle_left_type = 'ALIGNED'
        b_point.handle_right_type = 'ALIGNED'
        b_point.handle_left = co + ((h_left - co).normalized() * w)
        b_point.handle_right = co + ((h_right - co).normalized() * w)
        # select endpoint of curve and start-point of pole-cap
        cu_splines[0].bezier_points[-1].select_control_point = True
        cu_splines[1].bezier_points[0].select_control_point = True
        # merge curve an pole
        FpxUtilities.enable_edit_mode(True, self.__context)
        if ops.curve.make_segment.poll():
            ops.curve.make_segment()
        FpxUtilities.enable_edit_mode(False, self.__context)

    def create_curve(self, name, layers, curve_resolution):
        cu = self.__data.curves.new(FORMAT_CURVE.format(name), 'CURVE')
        obj = self.__data.objects.new(FORMAT_CURVE_OBJECT.format(name), cu)
        self.__scene.objects.link(obj)

        cu.dimensions = '3D'
        cu.twist_mode = 'Z_UP'
        cu.splines.new('BEZIER')
        spline = cu.splines[-1]
        spline.resolution_u = curve_resolution
        cu.resolution_u = curve_resolution

        obj.layers = layers
        return obj, cu, spline

    def create_ramp_curve_points(self, spline, fpx_points, z, z0, z1, w0=1.0, w1=1.0):
        ramp_length_sum = 0.0
        ramp_length_sum2 = 0.0
        ramp_length = []
        last_point = None

        reached_end_point = False
        for index, fpx_point in enumerate(fpx_points):
            fpx_position_xy = Vector(fpx_point.get_value("position"))
            if last_point:
                length = (fpx_position_xy - last_point).length
                ramp_length_sum += length
                if not reached_end_point:
                    ramp_length_sum2 += length
            ramp_length.append(ramp_length_sum)
            last_point = fpx_position_xy

            is_end_point = fpx_point.get_value("mark_as_ramp_end_point")
            if is_end_point:
                reached_end_point = True

        # create_curve_points & radius
        spline.bezier_points.add(len(fpx_points) - 1)

        for index, fpx_point in enumerate(fpx_points):
            fpx_position_xy = fpx_point.get_value("position")
            fpx_smooth = fpx_point.get_value("smooth")
            is_end_point = fpx_point.get_value("mark_as_ramp_end_point")

            factor = (ramp_length[index] / ramp_length_sum)
            factor2 = (ramp_length[index] / ramp_length_sum2)
            if factor2 > 1.0:
                factor2 = 1.0
            offset = (z1 - z0) * factor
            offset2 = (z1 - z0) * factor2

            bezier_point = spline.bezier_points[index]
            bezier_point.co = self.geometry_correction((fpx_position_xy[0], fpx_position_xy[1], (z + z0 + offset2)))
            bezier_point.radius = (w0 + ((w1 - w0) * factor)) / w0

            #if fpx_smooth and not is_end_point: (TODO)
            if fpx_smooth:
                handle_type = 'AUTO'
            else:
                handle_type = 'VECTOR'

            bezier_point.handle_left_type = handle_type
            bezier_point.handle_right_type = handle_type

        if self.use_hermite_handle:
            self.set_catmull_rom_hermite_bezier_handle(spline)

    def create_curve_points(self, spline, fpx_points, z=0.0):
        spline.bezier_points.add(len(fpx_points) - 1)

        for index, fpx_point in enumerate(fpx_points):
            fpx_position_xy = fpx_point.get_value("position")
            fpx_smooth = fpx_point.get_value("smooth")

            bezier_point = spline.bezier_points[index]
            bezier_point.co = self.geometry_correction((fpx_position_xy[0], fpx_position_xy[1], z))

            if fpx_smooth:
                handle_type = 'AUTO'
            else:
                handle_type = 'VECTOR'

            bezier_point.handle_left_type = handle_type
            bezier_point.handle_right_type = handle_type

        if self.use_hermite_handle:
            self.set_catmull_rom_hermite_bezier_handle(spline)

    def set_catmull_rom_hermite_bezier_handle(self, spline):
        if spline.type != 'BEZIER':
            return
        count_bezier_point = len(spline.bezier_points)
        max_index_bezier_point = count_bezier_point - 1
        min_index_bezier_point = 0

        ## Catmull-Rom
        catmull_rom_vectors = []
        for index_bezier_point in range(count_bezier_point):
            if index_bezier_point > 0 and index_bezier_point < max_index_bezier_point:
                point_prev = spline.bezier_points[index_bezier_point - 1].co
                point_next = spline.bezier_points[index_bezier_point + 1].co
                catmull_rom_vector = (point_next - point_prev) / 2.0
            elif not spline.use_cyclic_u and index_bezier_point == 0:
                point_prev = spline.bezier_points[index_bezier_point].co
                point_next = spline.bezier_points[index_bezier_point + 1].co
                catmull_rom_vector = (point_next - point_prev) / 2.0
            elif not spline.use_cyclic_u and index_bezier_point == max_index_bezier_point:
                point_prev = spline.bezier_points[index_bezier_point - 1].co
                point_next = spline.bezier_points[index_bezier_point].co
                catmull_rom_vector = (point_next - point_prev) / 2.0
            elif spline.use_cyclic_u and index_bezier_point == 0:
                point_prev = spline.bezier_points[max_index_bezier_point].co
                point_next = spline.bezier_points[index_bezier_point + 1].co
                catmull_rom_vector = (point_next - point_prev) / 2.0
            elif spline.use_cyclic_u and index_bezier_point == max_index_bezier_point:
                point_prev = spline.bezier_points[index_bezier_point - 1].co
                point_next = spline.bezier_points[min_index_bezier_point].co
                catmull_rom_vector = (point_next - point_prev) / 2.0
            else:
                catmull_rom_vector = Vector()
            catmull_rom_vectors.append(catmull_rom_vector)

        ## Hermite to Cubic Bezier right handles
        for index_bezier_point in range(count_bezier_point):
            bezier_point = spline.bezier_points[index_bezier_point]
            point = bezier_point.co
            if bezier_point.handle_right_type in {'VECTOR', }:
                if index_bezier_point < max_index_bezier_point:
                    bezier_point_next = spline.bezier_points[index_bezier_point + 1]
                    point_next = bezier_point_next.co
                    catmull_rom_vector = (point_next - point) / 2.0
                elif spline.use_cyclic_u and index_bezier_point == max_index_bezier_point:
                    bezier_point_next = spline.bezier_points[min_index_bezier_point]
                    point_next = bezier_point_next.co
                    catmull_rom_vector = (point_next - point) / 2.0
                else:
                    bezier_point_prev = spline.bezier_points[index_bezier_point - 1]
                    point_prev = bezier_point_prev.co
                    catmull_rom_vector = (point - point_prev) / 2.0
            else:
                catmull_rom_vector = catmull_rom_vectors[index_bezier_point]
            bezier_handle_point = point + (catmull_rom_vector / 3.0)
            bezier_point.handle_right_type = 'FREE'
            bezier_point.handle_right = bezier_handle_point

        ## Hermite to Cubic Bezier left handles
        for index_bezier_point in range(count_bezier_point):
            bezier_point = spline.bezier_points[index_bezier_point]
            point = bezier_point.co
            if bezier_point.handle_left_type in {'VECTOR', }:
                bezier_point.handle_left_type = 'FREE'
                if index_bezier_point > 0:
                    bezier_point_prev = spline.bezier_points[index_bezier_point - 1]
                    point_prev = bezier_point_prev.co
                    catmull_rom_vector = (point - point_prev) / 2.0
                elif spline.use_cyclic_u and index_bezier_point == min_index_bezier_point:
                    bezier_point_prev = spline.bezier_points[max_index_bezier_point]
                    point_prev = bezier_point_prev.co
                    catmull_rom_vector = (point - point_prev) / 2.0
                else:
                    bezier_point_next = spline.bezier_points[index_bezier_point + 1]
                    point_next = bezier_point_next.co
                    catmull_rom_vector = (point_next - point) / 2.0
            else:
                bezier_point.handle_left_type = 'ALIGNED'
                bezier_point.handle_right_type = 'ALIGNED'
                catmull_rom_vector = catmull_rom_vectors[index_bezier_point]
            bezier_handle_point = point - (catmull_rom_vector / 3.0)
            #bezier_point.handle_left_type = 'FREE'
            bezier_point.handle_left = bezier_handle_point

    def create_bevel(self, name, size, resolution):
        curve_points = [(0.0, size), (size, 0.0), (0.0, -size), (-size, 0.0),]

        cu = self.__data.curves.new("{}.bevel_curve".format(name), 'CURVE')
        obj = self.__data.objects.new("{}".format(name), cu)
        self.__scene.objects.link(obj)

        cu.dimensions = '2D'
        cu.twist_mode = 'Z_UP'
        cu.resolution_u = resolution
        cu.splines.new('BEZIER')
        sp = cu.splines[-1]
        sp.resolution_u = resolution
        sp.use_cyclic_u = True

        # create curve points
        sp.bezier_points.add(len(curve_points) - len(sp.bezier_points))

        for index, curve_point in enumerate(curve_points):
            bezier_point = sp.bezier_points[index]
            bezier_point.co = (curve_point[0], curve_point[1], 0.0)

            handle_type = 'AUTO'
            bezier_point.handle_left_type = handle_type
            bezier_point.handle_right_type = handle_type

        return obj

    def create_wire_ramp_bevel(self, curve, wire_index):
        wire_diameter = [Vector((0.0, -2.0, 0.0)), Vector((-2.0, 0.0, 0.0)), Vector((0.0, 2.0, 0.0)), Vector((2.0, 0.0, 0.0))]
        wire_position = [Vector((-11.0, -2.0, 0.0)), Vector((11.0, -2.0, 0.0)), Vector((-17.0, 11, 0.0)), Vector((17.0, 11.0, 0.0)), Vector((-11.0, 24.0, 0.0)), Vector((11.0, 24.0, 0.0)), Vector((0.0, 33.0, 0.0))]
        w0 = Vector((0.0, 0.0, 0.0))
        handle = 'AUTO'
        curve.splines.new('BEZIER')
        p0 = wire_position[wire_index] + w0
        spline = curve.splines[-1]
        spline.resolution_u = self.resolution_wire_bevel
        spline.use_cyclic_u = True
        spline.bezier_points.add(3)
        spline.bezier_points[0].co = p0 + wire_diameter[0]
        spline.bezier_points[0].handle_left_type = handle
        spline.bezier_points[0].handle_right_type = handle
        spline.bezier_points[1].co = p0 + wire_diameter[1]
        spline.bezier_points[1].handle_left_type = handle
        spline.bezier_points[1].handle_right_type = handle
        spline.bezier_points[2].co = p0 + wire_diameter[2]
        spline.bezier_points[2].handle_left_type = handle
        spline.bezier_points[2].handle_right_type = handle
        spline.bezier_points[3].co = p0 + wire_diameter[3]
        spline.bezier_points[3].handle_left_type = handle
        spline.bezier_points[3].handle_right_type = handle

    def prepare_wire_ramp_bevel(self):
        bevel_name = "__fpx_guide_ramp_wire_bevel__"
        wire_bevel = self.__data.objects.get(bevel_name)
        if wire_bevel is None:
            cu = self.__data.curves.new(bevel_name, 'CURVE')
            wire_bevel = self.__data.objects.new(bevel_name, cu)
            self.__scene.objects.link(wire_bevel)
            cu.dimensions = '2D'
            cu.resolution_u = self.resolution_wire_bevel

            self.create_wire_ramp_bevel(cu, 0) # base left inner
            self.create_wire_ramp_bevel(cu, 1) # base right inner

            if self.debug_create_full_ramp_wires:
                self.create_wire_ramp_bevel(cu, 2) # left inner
                self.create_wire_ramp_bevel(cu, 3) # right inner
                self.create_wire_ramp_bevel(cu, 4) # upper left inner
                self.create_wire_ramp_bevel(cu, 5) # upper right inner
                self.create_wire_ramp_bevel(cu, 6) # top outer
            else:
                pass

        return wire_bevel

    def prepare_wire_ramp_side_bevel(self, wire_index):
        bevel_name = "__fpx_guide_ramp_wire_bevel_{}__".format(wire_index)
        wire_bevel = self.__data.objects.get(bevel_name)
        if wire_bevel is None:
            cu = self.__data.curves.new(bevel_name, 'CURVE')
            wire_bevel = self.__data.objects.new(bevel_name, cu)
            self.__scene.objects.link(wire_bevel)
            cu.dimensions = '2D'
            cu.resolution_u = self.resolution_wire_bevel

            self.create_wire_ramp_bevel(cu, wire_index)

        return wire_bevel

    ###########################################################################
    def geometry_correction(self, value):
        return Vector((value[0], -value[1], value[2]))

    def angle_correction(self, value):
        return -90 - value

    def attach_dupli_group(self, blender_empty_object, layers, fpx_model_name, fpx_type_name, offset=Vector(), angle=0):
        blender_empty_object_new = None
        fpx_model_name = FpxUtilities.toGoodName(fpx_model_name) ####
        if fpx_model_name in self.debug_missing_resources:
            return blender_empty_object_new

        if fpx_type_name == 'RAW':
            blender_group_name = FpxUtilities.toGoodName(FORMAT_GROUP.format(fpx_model_name))
            self.LoadObjectLite(blender_group_name, Fpt_PackedLibrary_Type.TYPE_MODEL)
        if fpx_type_name == 'LOCAL':
            blender_group_name = FpxUtilities.toGoodName(FORMAT_RESOURCE.format(PREFIX_LOCAL, FORMAT_GROUP.format(fpx_model_name)))
            self.LoadObjectLite(blender_group_name, Fpt_PackedLibrary_Type.TYPE_MODEL)
        else:
            fpx_model_object = self.fpx_pinmodels.get(fpx_model_name)
            if not fpx_model_object:
                if self.verbose in FpxUI.VERBOSE_NORMAL:
                    print("#DEBUG attach_dupli_group, fpx_pinmodel not found!", fpx_model_name, fpx_type_name)
                    self.debug_missing_resources.add(fpx_model_name)
                return blender_empty_object_new
            blender_group_name = fpx_model_object[self.BLENDER_OBJECT_NAME]

        blender_group = self.__data.groups.get(blender_group_name)
        if blender_group:
            old_mesh = None
            old_object = None
            for o in blender_group.objects:
                if o.type == 'MESH':
                    old_object = o
                    old_mesh = old_object.data

            blender_empty_object_new = self.__data.objects.new(FORMAT_DUPLI_OBJECT.format(blender_empty_object.name), old_mesh)
            blender_empty_object_new.location = old_object.parent.location + old_object.location + offset
            blender_empty_object_new.rotation_mode = blender_empty_object.rotation_mode
            blender_empty_object_new.rotation_euler = Euler((0, 0, radians(angle)), blender_empty_object.rotation_mode)
            blender_empty_object_new.empty_draw_type = blender_empty_object.empty_draw_type
            blender_empty_object_new.empty_draw_size = blender_empty_object.empty_draw_size
            self.__scene.objects.link(blender_empty_object_new)

            old_group_dict = {}
            for old_vert in old_mesh.vertices:
                for group in old_vert.groups:
                    group_index = group.group
                    old_vertex_index_list = old_group_dict.get(group_index)
                    if not old_vertex_index_list:
                        old_vertex_index_list = []
                        old_group_dict[group_index] = old_vertex_index_list
                    old_vertex_index_list.append(old_vert.index)
            for old_group in old_object.vertex_groups:
                new_group = blender_empty_object_new.vertex_groups.new(old_group.name)
                old_vertex_index_list = old_group_dict[old_group.index]
                new_group.add(old_vertex_index_list, 0.0, 'ADD')

            for old_modifier in old_object.modifiers.values():
                new_modifier = blender_empty_object_new.modifiers.new(name=old_modifier.name, type=old_modifier.type)
                for attr in dir(old_modifier):
                    try:
                        setattr(new_modifier, attr, getattr(old_modifier, attr))
                    except:
                        pass

            blender_empty_object_new.parent = blender_empty_object

            #blender_empty_object_new.dupli_type = 'GROUP'
            #blender_empty_object_new.dupli_group = blender_group
            blender_empty_object_new.layers = layers
            blender_empty_object_new.select = True
            """
            active_object = self.__scene.objects.active
            self.__scene.objects.active = blender_empty_object_new
            if ops.object.duplicates_make_real.poll():
                ops.object.duplicates_make_real(use_base_parent=True, use_hierarchy=True)
                print("#DEBUG duplicates_make_real", self.__scene.objects.active.name)
            self.__scene.objects.active = active_object
            """
        else:
            print("#DEBUG attach_dupli_group, blender_group not found!", fpx_model_name, fpx_type_name, blender_group_name)
            self.debug_missing_resources.add(fpx_model_name)

        # add name to fpt property
        blender_empty_object.fpt.add_model(fpx_type_name, fpx_model_name)

        return blender_empty_object_new


    ###########################################################################
    def FpxLayerToBlenderLayers(self, layer, id=None, render=None, alpha=None, sphere_mapping=None, crystal=None, base=None):
        if layer is None:
            layer = 0x000

        if id is None:
            id = 0

        if render is None:
            render = True

        if alpha is None:
            alpha = 10

        if crystal is None:
            crystal = False

        if base is None:
            base = False

        layers = []
        for index in range(20):
            # layers, left block, top row
            if index == 0:
                layers.append(True)
            elif index == 1 and (render and alpha > 0): # visible objects
                layers.append(True)
            elif index == 2 and (not render or alpha <= 0): # invisible objects
                layers.append(True)
            elif index == 3 and id in FptElementType.SET_CURVE_OBJECTS: # curve object
                layers.append(True)
            elif index == 4 and id in FptElementType.SET_MESH_OBJECTS: # mesh object
                layers.append(True)

            # layers, left block, bottom row
            elif index == 10 and id in FptElementType.SET_LIGHT_OBJECTS: # light object
                layers.append(True)
            elif index == 11 and id in FptElementType.SET_RUBBER_OBJECTS: # rubber object
                layers.append(True)
            elif index == 12 and ((id in FptElementType.SET_SPHERE_MAPPING_OBJECTS and sphere_mapping) or id in FptElementType.SET_WIRE_OBJECTS): # chrome object
                layers.append(True)
            elif index == 13 and (crystal or (alpha > 0 and alpha < 10)): # crystal and transparent but visible objects
                layers.append(True)
            elif index == 14: # TODO: base mesh object
                layers.append(False)

            # layers, right block, top row
            elif index == 5 and (layer & 0x002) == 0x002: # layer 2
                layers.append(True)
            elif index == 6 and (layer & 0x008) == 0x008: # layer 4
                layers.append(True)
            elif index == 7 and (layer & 0x020) == 0x020: # layer 6
                layers.append(True)
            elif index == 8 and (layer & 0x080) == 0x080: # layer 8
                layers.append(True)
            elif index == 9 and (layer & 0x200) == 0x200: # layer 0
                layers.append(True)

            # layers, right block, bottom row
            elif index == 15 and (layer & 0x001) == 0x001: # layer 1
                layers.append(True)
            elif index == 16 and (layer & 0x004) == 0x004: # layer 3
                layers.append(True)
            elif index == 17 and (layer & 0x010) == 0x010: # layer 5
                layers.append(True)
            elif index == 18 and (layer & 0x040) == 0x040: # layer 7
                layers.append(True)
            elif index == 19 and (layer & 0x100) == 0x100: # layer 9
                layers.append(True)

            else:
                layers.append(False)
        return tuple(layers)

    def LoadObjectLite(self, name, type):
        """
        name: 'fpmodel.fpl\\<object>.g', 'fpmodel.fpl\\<object>.i'
        type: 'IMAGE', 'MODEL'
        """
        obj = self.LoadFromEmbedded(name, type)

        if not obj:
            obj = self.LoadFromBlendLibrary(name, type, self.blend_resource_file)

        if not obj:
            print("#DEBUG resource finally not found", name, type)

        return obj

    def LoadObject(self, name, type, lib):
        """
        name: 'fpmodel.fpl\\<object>.g', 'fpmodel.fpl\\<object>.i'
        type: 'IMAGE', 'MODEL'
        lib_name: fpmodel.fpl
        path_name: '.\\', 'C:\\FuturePinball\\Libraries\\', '<addons>\\io_scene_fpx\\'
        """
        #print("#DEBUG LoadObject", name, type, lib)

        obj = self.LoadFromEmbedded(name, type)

        if not obj and lib:
            obj = self.LoadFromPathLibrary(name, type, lib, self.folder_name)

        if not obj:
            obj = self.LoadFromBlendLibrary(name, type, self.blend_resource_file)

        if not obj and lib:
            obj = self.LoadFromPathLibrary(name, type, lib, self.path_libraries)

        if not obj:
            print("#DEBUG resource finally not found", name, type, lib)

        return obj

    def LoadFromEmbedded(self, name, type):
        #print("#DEBUG LoadFromEmbedded", name, type)

        if type == Fpt_PackedLibrary_Type.TYPE_IMAGE:
            data_from_dict = self.__data.images
        elif type == Fpt_PackedLibrary_Type.TYPE_MODEL:
            #print("#DEBUG LoadFromEmbedded groups", [g for g in self.__data.groups])
            data_from_dict = self.__data.groups
        else:
            return None
        return data_from_dict.get(name)

    def LoadFromBlendLibrary(self, name, type, file):
        """
        name: 'fpmodel.fpl\\<object>.g'
        type: 'IMAGE', 'MODEL'
        file: '<addons>\\io_scene_fpx\\fpx_resource.blend'
        """
        #print("#DEBUG LoadFromBlendLibrary", name, type, file)

        with self.__data.libraries.load(file) as (data_from, data_to):
            # imports data from library
            if type == Fpt_PackedLibrary_Type.TYPE_IMAGE:
                data_from_list = data_from.images
                name_temp = name

                if name_temp not in data_from.images:
                    return None
                # embed image data from library
                data_to.images = [name_temp, ]

            elif type == Fpt_PackedLibrary_Type.TYPE_MODEL:
                if name.endswith(".g"):
                    name_scene = "{}.s".format(name[:-2])
                    if name_scene not in data_from.scenes:
                        return None
                    # embed scene data from library
                    data_to.scenes = [name_scene, ]

                if name not in data_from.groups:
                    return None
                # embed group data from library
                data_to.groups = [name, ]

            else:
                return None

        # try to get internal data
        return self.LoadFromEmbedded(name, type)

    def LoadFromPathLibrary(self, name, type, lib, folder):
        """
        name: 'fpmodel.fpl\\<object>.g'
        type: 'IMAGE', 'MODEL'
        lib:  'fpmodel.fpl'
        folder: '.\\'
        """
        #print("#DEBUG LoadFromPathLibrary", name, type, lib, folder)

        filepath = path.join(folder, lib)
        filepath = FpxUtilities.toGoodFilePath(filepath)
        if path.exists(filepath):
            FplImporter(
                    report=self.report,
                    verbose=self.verbose,
                    keep_temp=self.keep_temp,
                    use_library_filter=self.use_library_filter,
                    use_model_filter=self.use_model_filter,
                    use_model_adjustment=self.use_model_adjustment,
                    keep_name=False,
                    ).read(
                            self.__context,
                            filepath,
                            )

            return self.LoadFromEmbedded(name, type)

        return None

    def GetLinked(self, dictIn, dictOut, type, dst_sub_path_names):
        """
        loads external resources
        """
        if type not in self.use_library_filter:
            return

        for key, fpx_item in dictIn.items():
            if not fpx_item:
                continue

            fpx_item_name = fpx_item.get_value("name")
            fpx_item_name = FpxUtilities.toGoodName(fpx_item_name) ####

            if type == Fpt_PackedLibrary_Type.TYPE_IMAGE:
                blender_resource_name_format = FORMAT_IMAGE.format(FORMAT_RESOURCE)
            elif type == Fpt_PackedLibrary_Type.TYPE_MODEL:
                blender_resource_name_format = FORMAT_GROUP.format(FORMAT_RESOURCE)
            else:
                ## TODO
                continue

            lib_name = None

            if fpx_item.get_value("linked"):
                #print("#DEBUG GetLinked linked > ", type, fpx_item_name)

                win_linked_path = fpx_item.get_value("linked_path").lower()
                linked_path = FpxUtilities.toGoodFilePath(win_linked_path)
                library_file, file_name = linked_path.split(path.sep) #Fpt_File_Reader.SEPARATOR)
                ## "Sci-Fi Classic GFX.fpl"
                ## library_file = FpxUtilities.toGoodName(library_file)
                ## file_name = FpxUtilities.toGoodName(file_name)

                lib_name = library_file

                if file_name.endswith(".fpm") or file_name.endswith(".jpg") or file_name.endswith(".bmp") or file_name.endswith(".tga"):
                    file_name = file_name[:-4]

                if library_file == "":
                    prefix_library_file = PREFIX_LOCAL
                else:
                    prefix_library_file = library_file

                blender_resource_name = FpxUtilities.toGoodName(blender_resource_name_format.format(prefix_library_file, file_name))

                dictOut[fpx_item_name] = [ blender_resource_name, ]

            else:
                #print("#DEBUG GetLinked intern > ", type, fpx_item_name)

                blender_resource_name = FpxUtilities.toGoodName(blender_resource_name_format.format(PREFIX_EMBEDDED, fpx_item_name))
                dictOut[fpx_item_name] = [ blender_resource_name, ]

                item_type = dst_sub_path_names.get("type_{}".format(fpx_item_name))
                if item_type == Fpt_PackedLibrary_Type.TYPE_IMAGE:
                    item_path = dst_sub_path_names.get(fpx_item_name)
                    if item_path:
                        #print("#DEBUG fpt images.load", item_path)
                        blend_image = self.__data.images.load(item_path)
                        if blend_image:
                            blend_image.name = blender_resource_name
                            if blend_image.has_data:
                                blend_image.update()
                            blend_image.pack()
                            #blend_image.use_fake_user = True
                            item_dir, item_file = path.split(item_path)
                            blend_image.filepath_raw = "//unpacked_resource/{}".format(item_file)
                        if not blend_image or not blend_image.has_data:
                            print("#DEBUG fpt images.load failed", item_path)
                elif item_type == Fpt_PackedLibrary_Type.TYPE_MODEL:
                    item_data = dst_sub_path_names.get("data_{}".format(fpx_item_name))
                    if item_data:
                        #print("#DEBUG", fpx_item_name, item_data[1]["sub_dir"])
                        active_scene = self.__context.screen.scene
                        FpmImporter(
                                report=self.report,
                                verbose=self.verbose,
                                keep_temp=self.keep_temp,
                                use_scene_per_model=True,
                                name_extra="",
                                use_model_filter=self.use_model_filter,
                                use_model_adjustment=self.use_model_adjustment,
                                keep_name=False,
                            ).read_ex(
                                    blender_context=self.__context,
                                    dst_sub_path_names=item_data[1],
                                    model_name=FpxUtilities.toGoodName(FORMAT_RESOURCE.format(PREFIX_EMBEDDED, fpx_item_name)),
                                    debug_data=[],
                                    )
                        #rename_active_fpm(self.__context, blender_resource_name)
                        self.__context.screen.scene = active_scene
                else:
                    pass

            self.LoadObject(blender_resource_name, type, lib_name)

    ###########################################################################

###############################################################################
def get_min_max(blender_object):
    min_x = max_x = min_y = max_y = min_z = max_z = None

    for vert in blender_object.data.vertices:
        x, y, z = vert.co

        if min_x is None:
            min_x = max_x = x
            min_y = max_y = y
            min_z = max_z = z
            continue

        if x < min_x:
            min_x = x
        elif x > max_x:
            max_x = x

        if y < min_y:
            min_y = y
        elif y > max_y:
            max_y = y

        if z < min_z:
            min_z = z
        elif z > max_z:
            max_z = z

    return min_x, min_y, min_z, max_x, max_y, max_z

def adjust_position(blender_context, blender_scene, fpx_model, fpx_model_type=None):
    if not blender_context.active_object:
        return
    fpx_type = fpx_model.get("type")
    has_mask = fpx_model.get("mask_model_data")

    blender_object = blender_context.active_object
    blender_parent = blender_object.parent

    # Fpm_Model_Type.OBJECT_OBJECT = 0
    ## Fpm_Model_Type.OBJECT_PEG = 1
    ## Fpm_Model_Type.OBJECT_ORNAMENT = 8

    # Fpm_Model_Type.CONTROL_BUMPER_BASE = 3
    # Fpm_Model_Type.CONTROL_BUMPER_CAP = 4

    ## Fpm_Model_Type.CONTROL_FLIPPER = 2
    # Fpm_Model_Type.CONTROL_PLUNGER = 7
    # Fpm_Model_Type.CONTROL_KICKER = 9
    # Fpm_Model_Type.CONTROL_DIVERTER = 18
    # Fpm_Model_Type.CONTROL_AUTOPLUNGER = 19
    # Fpm_Model_Type.CONTROL_POPUP = 20
    # Fpm_Model_Type.CONTROL_EMKICKER = 24

    # Fpm_Model_Type.TARGET_TARGET = 5
    # Fpm_Model_Type.TARGET_DROP = 6
    # Fpm_Model_Type.TARGET_VARI = 26

    # Fpm_Model_Type.TRIGGER_TRIGGER = 12
    # Fpm_Model_Type.TRIGGER_GATE = 15
    # Fpm_Model_Type.TRIGGER_SPINNER = 16
    # Fpm_Model_Type.TRIGGER_OPTO = 25

    ## Fpm_Model_Type.LIGHT_FLASHER = 13
    ## Fpm_Model_Type.LIGHT_BULB = 14

    ## Fpm_Model_Type.TOY_SPINNINGDISK = 23
    ## Fpm_Model_Type.TOY_CUSTOM = 17

    # Fpm_Model_Type.GUIDE_LANE = 10
    # Fpm_Model_Type.RUBBER_MODEL = 11
    # Fpm_Model_Type.RAMP_MODEL = 21
    # Fpm_Model_Type.RAMP_WIRE_CAP = 22

    # fpx_model_type=None
    # fpx_model_type="lo"
    # fpx_model_type="ma"
    # fpx_model_type="mi"

    # bumper ring = top + 31
    #
    #

    blender_location = None
    if fpx_type in {
            Fpm_Model_Type.OBJECT_PEG, #
            Fpm_Model_Type.OBJECT_ORNAMENT, # mask
            Fpm_Model_Type.CONTROL_BUMPER_BASE, #
            Fpm_Model_Type.CONTROL_FLIPPER, #
            Fpm_Model_Type.CONTROL_DIVERTER, #
            Fpm_Model_Type.CONTROL_AUTOPLUNGER,
            Fpm_Model_Type.CONTROL_KICKER, #
            Fpm_Model_Type.LIGHT_FLASHER, # mask
            Fpm_Model_Type.LIGHT_BULB, #
            Fpm_Model_Type.TRIGGER_OPTO, #
            Fpm_Model_Type.TOY_CUSTOM,
            }:
        static_offset = 0
        if has_mask:
            #align to top
            #blender_location = Vector((blender_parent.location.x, blender_parent.location.y, -blender_object.dimensions.z / 2.0))
            blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[2] + static_offset))
        else:
            # align to bottom
            #blender_location = Vector((blender_parent.location.x, blender_parent.location.y, blender_object.dimensions.z / 2.0))
            blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[5] + static_offset))

    elif fpx_type in {
            Fpm_Model_Type.CONTROL_BUMPER_CAP, #
            }:
        # align to bottom + static offset
        static_offset = 31.5
        #blender_location = Vector((blender_parent.location.x, blender_parent.location.y, (blender_object.dimensions.z / 2.0) + static_offset))
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[5] + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.TOY_SPINNINGDISK, #
            }:
        # align to top + static offset
        static_offset = 0.25
        #blender_location = Vector((blender_parent.location.x, blender_parent.location.y, (-blender_object.dimensions.z / 2.0) + static_offset))
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[2] + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.TRIGGER_TRIGGER, #
            }:
        # dont touch
        pass
    elif fpx_type in {
            Fpm_Model_Type.TRIGGER_SPINNER, #
            }:
        # static offset
        static_offset = 3
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, blender_parent.location.z + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.TRIGGER_GATE, #
            }:
        # align to top + static offset
        static_offset = 6
        #blender_location = Vector((blender_parent.location.x, blender_parent.location.y, (-blender_object.dimensions.z / 2.0) + static_offset))
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[2] + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.CONTROL_POPUP, #
            }:
        # align to top
        static_offset = 0
        #blender_location = Vector((blender_parent.location.x, blender_parent.location.y, (-blender_object.dimensions.z / 2.0) + static_offset))
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[2] + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.TARGET_DROP, #
            }:
        # static offset
        static_offset = 12.5
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, blender_parent.location.z + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.TARGET_TARGET, #
            }:
        # static offset
        static_offset = 15
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, blender_parent.location.z + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.RAMP_WIRE_CAP, #
            }:
        # static offset
        static_offset = 13
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, blender_parent.location.z + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.OBJECT_OBJECT, # wire ring
            }:
        # static offset
        static_offset = 11
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, blender_parent.location.z + static_offset))
    elif fpx_type in {
            Fpm_Model_Type.RUBBER_MODEL, #
            Fpm_Model_Type.GUIDE_LANE, #
            Fpm_Model_Type.RAMP_MODEL, #
            }:
        # align to bottom + static offset
        static_offset = 0
        blender_location = Vector((blender_parent.location.x, blender_parent.location.y, get_min_max(blender_object)[5] + static_offset))
    else:
        pass

    if blender_location:
        blender_scene.objects.active = blender_parent
        blender_scene.objects.active.location = blender_location
        blender_scene.update()

def remove_material(blender_context):
    if not blender_context.active_object:
        return
    active_object = blender_context.active_object
    blender_data = blender_context.blend_data

    used_materials = []
    used_textures = []
    used_images = []

    for material_slot in active_object.material_slots:
        if not material_slot or not material_slot.material:
            continue
        material = material_slot.material
        used_materials.append(material)
        for texture_slot in material.texture_slots:
            if not texture_slot or not texture_slot.texture:
                continue
            texture = texture_slot.texture
            used_textures.append(texture)
            if texture.type == 'IMAGE' and texture.image:
                used_images.append(texture.image)
                texture.image = None
            texture_slot.texture = None
        material_slot.material = None

    if ops.object.material_slot_remove.poll():
        ops.object.material_slot_remove()

    for material in used_materials:
        material.user_clear()
        blender_data.materials.remove(material)

    for texture in used_textures:
        texture.user_clear()
        blender_data.textures.remove(texture)

    for image in used_images:
        image.user_clear()
        blender_data.images.remove(image)

def get_object_src_name(blender_context):
    name = blender_context.active_object.name
    src_ext = "ms3d"
    index = name.rfind(".{}.".format(src_ext))
    if index < 0:
        index = name.rfind(".")
        #if index < 0:
        #    return

    src_name = "{}.{}".format(name[:index], src_ext)
    return src_name

def rename_active_ms3d(blender_context, src_name, dst_name, dst_type=None):
    #print("#DEBUG rename_active_ms3d >", blender_context.active_object, src_name, dst_name, dst_type)
    if not blender_context.active_object:
        return

    data = blender_context.blend_data

    src_empty_object_name = FORMAT_EMPTY_OBJECT.format(src_name)
    src_mesh_object_name = FORMAT_MESH_OBJECT.format(src_name)
    src_mesh_name = FORMAT_MESH.format(src_name)
    src_armature_name = FORMAT_ARMATURE.format(src_name)
    src_armature_object_name = FORMAT_ARMATURE_OBJECT.format(src_name)
    src_action_name = FORMAT_ACTION.format(src_name)
    src_group_name = FORMAT_GROUP.format(src_name)

    if dst_type:
        dst_name = "{}.{}".format(dst_name, dst_type)

    dst_empty_object_name = FpxUtilities.toGoodName(FORMAT_EMPTY_OBJECT.format(dst_name))
    dst_mesh_object_name = FpxUtilities.toGoodName(FORMAT_MESH_OBJECT.format(dst_name))
    dst_mesh_name = FpxUtilities.toGoodName(FORMAT_MESH.format(dst_name))
    dst_armature_name = FpxUtilities.toGoodName(FORMAT_ARMATURE.format(dst_name))
    dst_armature_object_name = FpxUtilities.toGoodName(FORMAT_ARMATURE_OBJECT.format(dst_name))
    dst_action_name = FpxUtilities.toGoodName(FORMAT_ACTION.format(dst_name))
    dst_group_name = FpxUtilities.toGoodName(FORMAT_GROUP.format(dst_name))

    obj = blender_context.blend_data.objects.get(src_empty_object_name)
    if obj and not blender_context.blend_data.objects.get(dst_empty_object_name):
        obj.name = dst_empty_object_name

    obj = data.objects.get(src_mesh_object_name)
    if obj and not data.objects.get(dst_mesh_object_name):
        obj.name = dst_mesh_object_name
        mod = obj.modifiers.get(src_armature_name)
        if mod and not obj.modifiers.get(dst_armature_name):
            mod.name = dst_armature_name

    obj = data.objects.get(src_armature_object_name)
    if obj and not data.objects.get(dst_armature_object_name):
        obj.name = dst_armature_object_name

    obj = data.meshes.get(src_mesh_name)
    if obj and not data.meshes.get(dst_mesh_name):
        obj.name = dst_mesh_name

    obj = data.armatures.get(src_armature_name)
    if obj and not data.armatures.get(dst_armature_name):
        obj.name = dst_armature_name

    obj = data.actions.get(src_action_name)
    if obj and not data.actions.get(dst_action_name):
        obj.name = dst_action_name

    obj = data.groups.get(src_group_name)
    if obj and not data.groups.get(dst_group_name):
        obj.name = dst_group_name

def rename_active_fpm(blender_context, dst_name):
    #print("#DEBUG rename_active_fpm >", blender_context.active_object, dst_name)
    if not blender_context.active_object:
        return
    blender_name = blender_context.active_object.name
    fpm_ext = "fpm"
    index = blender_name.find(".{}.".format(fpm_ext))
    if index < 0:
        index = blender_name.rfind(".")
        if index < 0:
            return

    src_name = blender_name[:index]

    #print("#DEBUG rename_active_fpm 2>", src_name, dst_name)

    #if src_name.endswith(".fpm"):
    #    src_name = src_name[:-4]

    src_scene_name = blender_context.scene.name

    blender_scene = blender_context.blend_data.scenes.get(src_scene_name)
    if blender_scene:
        blender_scene.name = FORMAT_SCENE.format(dst_name).lower()

    for object_type in {'', '.secondary', '.mask', '.reflection', '.collision', }:
        fpm_ext_ex = "{}{}".format(src_name, object_type)
        rename_active_ms3d(blender_context, fpm_ext_ex, dst_name, object_type);

def get_blend_resource_file_name():
    from importlib import ( find_loader, )
    from os import ( path, )

    module_path = find_loader('io_scene_fpx').path
    module_path, module_file = path.split(module_path)

    resource_blend = path.join(module_path, 'fpx_resource.blend')

    if not path.exists(resource_blend):
        print("#DEBUG", "resource not found!")

    return resource_blend



###############################################################################


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
