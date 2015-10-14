import gzip
import os
import pickle
import shutil

import bpy
from bpy.props import (BoolProperty,
                       StringProperty)

from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import bl_info
from . operators import DataStore

# TODO: reinstate filters?
class IO_Utils():
    @staticmethod
    def get_preset_path():
        # locate stored_views preset folder
        paths = bpy.utils.preset_paths("stored_views")
        if not paths:
            # stored_views preset folder doesn't exist, so create it
            paths = [os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
                "stored_views")]
            if not os.path.exists(paths[0]):
                os.makedirs(paths[0])

        return(paths)

    @staticmethod
    def stored_views_apply_from_scene(scene_name, replace=True):
        scene = bpy.context.scene
        sv = bpy.context.scene.stored_views
#        io_filters = sv.settings.io_filters

        structs = [sv.view_list, sv.pov_list, sv.layers_list, sv.display_list]
        if replace == True:
            for st in structs:  # clear swap and list
                while len(st) > 0:
                    st.remove(0)

        f_sv = bpy.data.scenes[scene_name].stored_views
        f_structs = [f_sv.view_list, f_sv.pov_list, f_sv.layers_list, f_sv.display_list]
#        is_filtered = [io_filters.views, io_filters.point_of_views, io_filters.layers, io_filters.displays]

        for i in range(len(f_structs)):
#            if is_filtered[i] == False:
#                continue
            for j in f_structs[i]:
                item = structs[i].add()
                #stored_views_copy_item(j, item)
                for k, v in j.items():
                    item[k] = v
        DataStore.sanitize_data(scene)

    @staticmethod
    def stored_views_export_to_blsv(filepath, name='Custom Preset'):
        # create dictionary with all information
        dump = {"info": {}, "data": {}}
        dump["info"]["script"] = bl_info['name']
        dump["info"]["script_version"] = bl_info['version']
        dump["info"]["version"] = bpy.app.version
        dump["info"]["build_revision"] = bpy.app.build_revision
        dump["info"]["preset_name"] = name

        # get current stored views settings
        scene = bpy.context.scene
        sv = scene.stored_views

        def dump_view_list(dict, list):
            if str(type(list)) == "<class 'bpy_prop_collection_idprop'>":
                for i, struct_dict in enumerate(list):
                    dict[i] = {"name": str,
                               "pov": {},
                               "layers": {},
                               "display": {}}
                    dict[i]["name"] = struct_dict.name
                    dump_item(dict[i]["pov"], struct_dict.pov)
                    dump_item(dict[i]["layers"], struct_dict.layers)
                    dump_item(dict[i]["display"], struct_dict.display)

        def dump_list(dict, list):
            if str(type(list)) == "<class 'bpy_prop_collection_idprop'>":
                for i, struct in enumerate(list):
                    dict[i] = {}
                    dump_item(dict[i], struct)

        def dump_item(dict, struct):
            for prop in struct.bl_rna.properties:
                if prop.identifier == "rna_type":
                    # not a setting, so skip
                    continue
                val = getattr(struct, prop.identifier)
                if str(type(val)) in ["<class 'bpy_prop_array'>",
                                      "<class 'mathutils.Quaternion'>",
                                      "<class 'mathutils.Vector'>"]:
                    # array
                    dict[prop.identifier] = [v \
                        for v in val]
                else:
                    # single value
                    dict[prop.identifier] = val

#        io_filters = sv.settings.io_filters
        dump["data"] = {"point_of_views": {},
                        "layers": {},
                        "displays": {},
                        "views": {}}

        others_data = [(dump["data"]["point_of_views"], sv.pov_list), # , io_filters.point_of_views),
                       (dump["data"]["layers"], sv.layers_list), # , io_filters.layers),
                       (dump["data"]["displays"], sv.display_list)]  # , io_filters.displays)]
        for list_data in others_data:
#            if list_data[2] == True:
            dump_list(list_data[0], list_data[1])

        views_data = (dump["data"]["views"], sv.view_list)
#        if io_filters.views == True:
        dump_view_list(views_data[0], views_data[1])

        # save to file
        filepath = filepath
        filepath = bpy.path.ensure_ext(filepath, '.blsv')
        file = gzip.open(filepath, mode='w')
        pickle.dump(dump, file)
        file.close()

    @staticmethod
    def stored_views_apply_preset(filepath, replace=True):
        file = gzip.open(filepath, mode='r')
        dump = pickle.load(file)
        file.close()

        # apply preset
        scene = bpy.context.scene
        sv = scene.stored_views
#        io_filters = sv.settings.io_filters
        sv_data = {"point_of_views": sv.pov_list,
                   "views": sv.view_list,
                   "layers": sv.layers_list,
                   "displays": sv.display_list}

        for sv_struct, props in dump["data"].items():
#            is_filtered = getattr(io_filters, sv_struct)
#            if is_filtered == False:
#                continue
            sv_list = sv_data[sv_struct]#.list
            if replace == True:  # clear swap and list
                while len(sv_list) > 0:
                    sv_list.remove(0)
            for key, prop_struct in props.items():
                sv_item = sv_list.add()
                for subprop, subval in prop_struct.items():
                    if type(subval) == type({}):  # views : pov, layers, displays
                        v_subprop = getattr(sv_item, subprop)
                        for v_subkey, v_subval in subval.items():
                            if type(v_subval) == type([]):  # array like of pov,...
                                v_array_like = getattr(v_subprop, v_subkey)
                                for i in range(len(v_array_like)):
                                    v_array_like[i] = v_subval[i]
                            else:
                                setattr(v_subprop, v_subkey, v_subval)  # others
                    elif type(subval) == type([]):
                        array_like = getattr(sv_item, subprop)
                        for i in range(len(array_like)):
                            array_like[i] = subval[i]
                    else:
                        setattr(sv_item, subprop, subval)

        DataStore.sanitize_data(scene)


class VIEW3D_stored_views_import(bpy.types.Operator, ImportHelper):
    bl_idname = "stored_views.import"
    bl_label = "Import Stored Views preset"
    bl_description = "Import a .blsv preset file to the current Stored Views"

    filename_ext = ".blsv"
    filter_glob = StringProperty(default="*.blsv", options={'HIDDEN'})
    replace = BoolProperty(name="Replace",
                                     default=True,
                                     description="Replace current stored views, otherwise append")

    def execute(self, context):
        # apply chosen preset
        IO_Utils.stored_views_apply_preset(filepath=self.filepath, replace=self.replace)

        # copy preset to presets folder
        filename = os.path.basename(self.filepath)
        try:
            shutil.copyfile(self.filepath,
                            os.path.join(IO_Utils.get_preset_path()[0], filename))
        except:
            self.report({'WARNING'}, "Stored Views: preset applied, but installing failed (preset already exists?)")
            return{'CANCELLED'}

        return{'FINISHED'}


class VIEW3D_stored_views_import_from_scene(bpy.types.Operator):
    bl_idname = "stored_views.import_from_scene"
    bl_label = "Import stored views from scene"
    bl_description = "Import current stored views by those from another scene"

    scene_name = bpy.props.StringProperty(name="Scene Name",
                                        description="A current blend scene",
                                        default="")

    replace = BoolProperty(name="Replace",
                           default=True,
                           description="Replace current stored views, otherwise append")

    def execute(self, context):
        # filepath should always be given
        if not self.scene_name:
            self.report("ERROR", "Could not find scene")
            return{'CANCELLED'}

        IO_Utils.stored_views_apply_from_scene(self.scene_name, replace=self.replace)

        return{'FINISHED'}


class VIEW3D_stored_views_export(bpy.types.Operator, ExportHelper):
    bl_idname = "stored_views.export"
    bl_label = "Export Stored Views preset"
    bl_description = "Export the current Stored Views to a .blsv preset file"

    filename_ext = ".blsv"
    filepath = StringProperty(default=os.path.join(IO_Utils.get_preset_path()[0], "untitled"))
    filter_glob = StringProperty(default="*.blsv", options={'HIDDEN'})
    preset_name = StringProperty(name="Preset name",
                                 default="",
                                 description="Name of the stored views preset")

    def execute(self, context):
        IO_Utils.stored_views_export_to_blsv(self.filepath, self.preset_name)
        return{'FINISHED'}
