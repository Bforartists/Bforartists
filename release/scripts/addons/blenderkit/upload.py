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


from blenderkit import asset_inspector, paths, utils, bg_blender, autothumb, version_checker, search, ui_panels, ui, \
    overrides, colors, rerequests, categories, upload_bg, tasks_queue, image_utils

import tempfile, os, subprocess, json, re

import bpy
import requests
import threading
import sys

BLENDERKIT_EXPORT_DATA_FILE = "data.json"

from bpy.props import (  # TODO only keep the ones actually used when cleaning
    EnumProperty,
    BoolProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup,
    UIList
)

licenses = (
    ('royalty_free', 'Royalty Free', 'royalty free commercial license'),
    ('cc_zero', 'Creative Commons Zero', 'Creative Commons Zero'),
)


def comma2array(text):
    commasep = text.split(',')
    ar = []
    for i, s in enumerate(commasep):
        s = s.strip()
        if s != '':
            ar.append(s)
    return ar


def get_app_version():
    ver = bpy.app.version
    return '%i.%i.%i' % (ver[0], ver[1], ver[2])


def add_version(data):
    app_version = get_app_version()
    addon_version = version_checker.get_addon_version()
    data["sourceAppName"] = "blender"
    data["sourceAppVersion"] = app_version
    data["addonVersion"] = addon_version


def write_to_report(props, text):
    props.report = props.report + ' - ' + text + '\n\n'


def check_missing_data_model(props):
    autothumb.update_upload_model_preview(None, None)
    if not props.has_thumbnail:
        write_to_report(props, 'Add thumbnail:')
        props.report += props.thumbnail_generating_state + '\n'
    if props.engine == 'NONE':
        write_to_report(props, 'Set at least one rendering/output engine')

    # if not any(props.dimensions):
    #     write_to_report(props, 'Run autotags operator or fill in dimensions manually')


def check_missing_data_scene(props):
    autothumb.update_upload_model_preview(None, None)
    if not props.has_thumbnail:
        write_to_report(props, 'Add thumbnail:')
        props.report += props.thumbnail_generating_state + '\n'
    if props.engine == 'NONE':
        write_to_report(props, 'Set at least one rendering/output engine')


def check_missing_data_material(props):
    autothumb.update_upload_material_preview(None, None)
    if not props.has_thumbnail:
        write_to_report(props, 'Add thumbnail:')
        props.report += props.thumbnail_generating_state
    if props.engine == 'NONE':
        write_to_report(props, 'Set rendering/output engine')


def check_missing_data_brush(props):
    autothumb.update_upload_brush_preview(None, None)
    if not props.has_thumbnail:
        write_to_report(props, 'Add thumbnail:')
        props.report += props.thumbnail_generating_state


def check_missing_data(asset_type, props):
    '''
    checks if user did everything allright for particular assets and notifies him back if not.
    Parameters
    ----------
    asset_type
    props

    Returns
    -------

    '''
    props.report = ''

    if props.name == '':
        write_to_report(props, f'Set {asset_type.lower()} name.\n'
                               f'It has to be in English and \n'
                               f'can not be  longer than 40 letters.\n')
    if len(props.name) > 40:
        write_to_report(props, f'The name is too long. maximum is 40 letters')

    if props.is_private == 'PUBLIC':

        if len(props.description) < 20:
            write_to_report(props, "The description is too short or empty. \n"
                                   "Please write a description that describes \n "
                                   "your asset as good as possible.\n"
                                   "Description helps to bring your asset up\n in relevant search results. ")
        if props.tags == '':
            write_to_report(props, 'Write at least 3 tags.\n'
                                   'Tags help to bring your asset up in relevant search results.')

    if asset_type == 'MODEL':
        check_missing_data_model(props)
    if asset_type == 'SCENE':
        check_missing_data_scene(props)
    elif asset_type == 'MATERIAL':
        check_missing_data_material(props)
    elif asset_type == 'BRUSH':
        check_missing_data_brush(props)

    if props.report != '':
        props.report = f'Please fix these issues before {props.is_private.lower()} upload:\n\n' + props.report


def sub_to_camel(content):
    replaced = re.sub(r"_.",
                      lambda m: m.group(0)[1].upper(), content)
    return (replaced)


def camel_to_sub(content):
    replaced = re.sub(r"[A-Z]", lambda m: '_' + m.group(0).lower(), content)
    return replaced


def get_upload_data(caller=None, context=None, asset_type=None):
    '''
    works though metadata from addom props and prepares it for upload to dicts.
    Parameters
    ----------
    caller - upload operator or none
    context - context
    asset_type - asset type in capitals (blender enum)

    Returns
    -------
    export_ddta- all extra data that the process needs to upload and communicate with UI from a thread.
        - eval_path_computing - string path to UI prop that denots if upload is still running
        - eval_path_state - string path to UI prop that delivers messages about upload to ui
        - eval_path - path to object holding upload data to be able to access it with various further commands
        - models - in case of model upload, list of objects
        - thumbnail_path - path to thumbnail file

    upload_data - asset_data generated from the ui properties

    '''
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key

    export_data = {
        # "type": asset_type,
    }
    upload_params = {}
    if asset_type == 'MODEL':
        # Prepare to save the file
        mainmodel = utils.get_active_model()

        props = mainmodel.blenderkit

        obs = utils.get_hierarchy(mainmodel)
        obnames = []
        for ob in obs:
            obnames.append(ob.name)
        export_data["models"] = obnames
        export_data["thumbnail_path"] = bpy.path.abspath(props.thumbnail)

        eval_path_computing = "bpy.data.objects['%s'].blenderkit.uploading" % mainmodel.name
        eval_path_state = "bpy.data.objects['%s'].blenderkit.upload_state" % mainmodel.name
        eval_path = "bpy.data.objects['%s']" % mainmodel.name

        engines = [props.engine.lower()]
        if props.engine1 != 'NONE':
            engines.append(props.engine1.lower())
        if props.engine2 != 'NONE':
            engines.append(props.engine2.lower())
        if props.engine3 != 'NONE':
            engines.append(props.engine3.lower())
        if props.engine == 'OTHER':
            engines.append(props.engine_other.lower())

        style = props.style.lower()
        # if style == 'OTHER':
        #     style = props.style_other.lower()

        pl_dict = {'FINISHED': 'finished', 'TEMPLATE': 'template'}

        upload_data = {
            "assetType": 'model',

        }
        upload_params = {
            "productionLevel": props.production_level.lower(),
            "model_style": style,
            "engines": engines,
            "modifiers": comma2array(props.modifiers),
            "materials": comma2array(props.materials),
            "shaders": comma2array(props.shaders),
            "uv": props.uv,
            "dimensionX": round(props.dimensions[0], 4),
            "dimensionY": round(props.dimensions[1], 4),
            "dimensionZ": round(props.dimensions[2], 4),

            "boundBoxMinX": round(props.bbox_min[0], 4),
            "boundBoxMinY": round(props.bbox_min[1], 4),
            "boundBoxMinZ": round(props.bbox_min[2], 4),

            "boundBoxMaxX": round(props.bbox_max[0], 4),
            "boundBoxMaxY": round(props.bbox_max[1], 4),
            "boundBoxMaxZ": round(props.bbox_max[2], 4),

            "animated": props.animated,
            "rig": props.rig,
            "simulation": props.simulation,
            "purePbr": props.pbr,
            "faceCount": props.face_count,
            "faceCountRender": props.face_count_render,
            "manifold": props.manifold,
            "objectCount": props.object_count,

            "procedural": props.is_procedural,
            "nodeCount": props.node_count,
            "textureCount": props.texture_count,
            "megapixels": round(props.total_megapixels / 1000000),
            # "scene": props.is_scene,
        }
        if props.use_design_year:
            upload_params["designYear"] = props.design_year
        if props.condition != 'UNSPECIFIED':
            upload_params["condition"] = props.condition.lower()
        if props.pbr:
            pt = props.pbr_type
            pt = pt.lower()
            upload_params["pbrType"] = pt

        if props.texture_resolution_max > 0:
            upload_params["textureResolutionMax"] = props.texture_resolution_max
            upload_params["textureResolutionMin"] = props.texture_resolution_min
        if props.mesh_poly_type != 'OTHER':
            upload_params["meshPolyType"] = props.mesh_poly_type.lower()  # .replace('_',' ')

        optional_params = ['manufacturer', 'designer', 'design_collection', 'design_variant']
        for p in optional_params:
            if eval('props.%s' % p) != '':
                upload_params[sub_to_camel(p)] = eval('props.%s' % p)

    if asset_type == 'SCENE':
        # Prepare to save the file
        s = bpy.context.scene

        props = s.blenderkit

        export_data["scene"] = s.name
        export_data["thumbnail_path"] = bpy.path.abspath(props.thumbnail)

        eval_path_computing = "bpy.data.scenes['%s'].blenderkit.uploading" % s.name
        eval_path_state = "bpy.data.scenes['%s'].blenderkit.upload_state" % s.name
        eval_path = "bpy.data.scenes['%s']" % s.name

        engines = [props.engine.lower()]
        if props.engine1 != 'NONE':
            engines.append(props.engine1.lower())
        if props.engine2 != 'NONE':
            engines.append(props.engine2.lower())
        if props.engine3 != 'NONE':
            engines.append(props.engine3.lower())
        if props.engine == 'OTHER':
            engines.append(props.engine_other.lower())

        style = props.style.lower()
        # if style == 'OTHER':
        #     style = props.style_other.lower()

        pl_dict = {'FINISHED': 'finished', 'TEMPLATE': 'template'}

        upload_data = {
            "assetType": 'scene',

        }
        upload_params = {
            "productionLevel": props.production_level.lower(),
            "model_style": style,
            "engines": engines,
            "modifiers": comma2array(props.modifiers),
            "materials": comma2array(props.materials),
            "shaders": comma2array(props.shaders),
            "uv": props.uv,

            "animated": props.animated,
            # "simulation": props.simulation,
            "purePbr": props.pbr,
            "faceCount": 1,  # props.face_count,
            "faceCountRender": 1,  # props.face_count_render,
            "objectCount": 1,  # props.object_count,

            # "scene": props.is_scene,
        }
        if props.use_design_year:
            upload_params["designYear"] = props.design_year
        if props.condition != 'UNSPECIFIED':
            upload_params["condition"] = props.condition.lower()
        if props.pbr:
            pt = props.pbr_type
            pt = pt.lower()
            upload_params["pbrType"] = pt

        if props.texture_resolution_max > 0:
            upload_params["textureResolutionMax"] = props.texture_resolution_max
            upload_params["textureResolutionMin"] = props.texture_resolution_min
        if props.mesh_poly_type != 'OTHER':
            upload_params["meshPolyType"] = props.mesh_poly_type.lower()  # .replace('_',' ')

    elif asset_type == 'MATERIAL':
        mat = bpy.context.active_object.active_material
        props = mat.blenderkit

        # props.name = mat.name

        export_data["material"] = str(mat.name)
        export_data["thumbnail_path"] = bpy.path.abspath(props.thumbnail)
        # mat analytics happen here, since they don't take up any time...
        asset_inspector.check_material(props, mat)

        eval_path_computing = "bpy.data.materials['%s'].blenderkit.uploading" % mat.name
        eval_path_state = "bpy.data.materials['%s'].blenderkit.upload_state" % mat.name
        eval_path = "bpy.data.materials['%s']" % mat.name

        engine = props.engine
        if engine == 'OTHER':
            engine = props.engine_other
        engine = engine.lower()
        style = props.style.lower()
        # if style == 'OTHER':
        #     style = props.style_other.lower()

        upload_data = {
            "assetType": 'material',

        }

        upload_params = {
            "material_style": style,
            "engine": engine,
            "shaders": comma2array(props.shaders),
            "uv": props.uv,
            "animated": props.animated,
            "purePbr": props.pbr,
            "textureSizeMeters": props.texture_size_meters,
            "procedural": props.is_procedural,
            "nodeCount": props.node_count,
            "textureCount": props.texture_count,
            "megapixels": round(props.total_megapixels / 1000000),

        }

        if props.pbr:
            upload_params["pbrType"] = props.pbr_type.lower()

        if props.texture_resolution_max > 0:
            upload_params["textureResolutionMax"] = props.texture_resolution_max
            upload_params["textureResolutionMin"] = props.texture_resolution_min

    elif asset_type == 'BRUSH':
        brush = utils.get_active_brush()

        props = brush.blenderkit
        # props.name = brush.name

        export_data["brush"] = str(brush.name)
        export_data["thumbnail_path"] = bpy.path.abspath(brush.icon_filepath)

        eval_path_computing = "bpy.data.brushes['%s'].blenderkit.uploading" % brush.name
        eval_path_state = "bpy.data.brushes['%s'].blenderkit.upload_state" % brush.name
        eval_path = "bpy.data.brushes['%s']" % brush.name

        # mat analytics happen here, since they don't take up any time...

        brush_type = ''
        if bpy.context.sculpt_object is not None:
            brush_type = 'sculpt'

        elif bpy.context.image_paint_object:  # could be just else, but for future p
            brush_type = 'texture_paint'

        upload_params = {
            "mode": brush_type,
        }

        upload_data = {
            "assetType": 'brush',
        }

    elif asset_type == 'HDR':
        ui_props = bpy.context.scene.blenderkitUI

        # imagename = ui_props.hdr_upload_image
        image = ui_props.hdr_upload_image  # bpy.data.images.get(imagename)
        if not image:
            return None, None

        props = image.blenderkit
        # props.name = brush.name
        base, ext = os.path.splitext(image.filepath)
        thumb_path = base + '.jpg'
        export_data["thumbnail_path"] = bpy.path.abspath(thumb_path)

        export_data["hdr"] = str(image.name)
        export_data["hdr_filepath"] = str(bpy.path.abspath(image.filepath))
        # export_data["thumbnail_path"] = bpy.path.abspath(brush.icon_filepath)

        eval_path_computing = "bpy.data.images['%s'].blenderkit.uploading" % image.name
        eval_path_state = "bpy.data.images['%s'].blenderkit.upload_state" % image.name
        eval_path = "bpy.data.images['%s']" % image.name

        # mat analytics happen here, since they don't take up any time...

        upload_params = {
            "textureResolutionMax": props.texture_resolution_max

        }

        upload_data = {
            "assetType": 'hdr',
        }

    elif asset_type == 'TEXTURE':
        style = props.style
        # if style == 'OTHER':
        #     style = props.style_other

        upload_data = {
            "assetType": 'texture',

        }
        upload_params = {
            "style": style,
            "animated": props.animated,
            "purePbr": props.pbr,
            "resolution": props.resolution,
        }
        if props.pbr:
            pt = props.pbr_type
            pt = pt.lower()
            upload_data["pbrType"] = pt

    add_version(upload_data)

    # caller can be upload operator, but also asset bar called from tooltip generator
    if caller and caller.properties.main_file == True:
        upload_data["name"] = props.name
        upload_data["displayName"] = props.name
    else:
        upload_data["displayName"] = props.name

    upload_data["description"] = props.description
    upload_data["tags"] = comma2array(props.tags)
    # category is always only one value by a slug, that's why we go down to the lowest level and overwrite.
    if props.category == '':
        upload_data["category"] = asset_type.lower()
    else:
        upload_data["category"] = props.category
    if props.subcategory != 'NONE':
        upload_data["category"] = props.subcategory
    if props.subcategory1 != 'NONE':
        upload_data["category"] = props.subcategory1

    upload_data["license"] = props.license
    upload_data["isFree"] = props.is_free == 'FREE'
    upload_data["isPrivate"] = props.is_private == 'PRIVATE'
    upload_data["token"] = user_preferences.api_key

    upload_data['parameters'] = upload_params

    # if props.asset_base_id != '':
    export_data['assetBaseId'] = props.asset_base_id
    export_data['id'] = props.id
    export_data['eval_path_computing'] = eval_path_computing
    export_data['eval_path_state'] = eval_path_state
    export_data['eval_path'] = eval_path

    return export_data, upload_data


def patch_individual_metadata(asset_id, metadata_dict, api_key):
    upload_data = metadata_dict
    url = paths.get_api_url() + 'assets/' + str(asset_id) + '/'
    headers = utils.get_headers(api_key)
    try:
        r = rerequests.patch(url, json=upload_data, headers=headers, verify=True)  # files = files,
    except requests.exceptions.RequestException as e:
        print(e)
        return {'CANCELLED'}
    return {'FINISHED'}


# class OBJECT_MT_blenderkit_fast_metadata_menu(bpy.types.Menu):
#     bl_label = "Fast category change"
#     bl_idname = "OBJECT_MT_blenderkit_fast_metadata_menu"
#
#     def draw(self, context):
#         layout = self.layout
#         ui_props = context.scene.blenderkitUI
#
#         # sr = bpy.context.window_manager['search results']
#         sr = bpy.context.window_manager['search results']
#         asset_data = sr[ui_props.active_index]
#         categories = bpy.context.window_manager['bkit_categories']
#         wm = bpy.context.win
#         for c in categories:
#             if c['name'].lower() == asset_data['assetType']:
#                 for ch in c['children']:
#                     op = layout.operator('wm.blenderkit_fast_metadata', text = ch['name'])
#                     op = layout.operator('wm.blenderkit_fast_metadata', text = ch['name'])


def update_free_full(self, context):
    if self.asset_type == 'material':
        if self.free_full == 'FULL':
            self.free_full = 'FREE'
            ui_panels.ui_message(title="All BlenderKit materials are free",
                                 message="Any material uploaded to BlenderKit is free." \
                                         " However, it can still earn money for the author," \
                                         " based on our fair share system. " \
                                         "Part of subscription is sent to artists based on usage by paying users.")


def can_edit_asset(active_index=-1, asset_data=None):
    if active_index < 0 and not asset_data:
        return False
    profile = bpy.context.window_manager.get('bkit profile')
    if profile is None:
        return False
    if utils.profile_is_validator():
        return True
    if not asset_data:
        sr = bpy.context.window_manager['search results']
        asset_data = dict(sr[active_index])
    # print(profile, asset_data)
    if int(asset_data['author']['id']) == int(profile['user']['id']):
        return True
    return False


class FastMetadata(bpy.types.Operator):
    """Edit metadata of the asset"""
    bl_idname = "wm.blenderkit_fast_metadata"
    bl_label = "Update metadata"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    asset_id: StringProperty(
        name="Asset Base Id",
        description="Unique name of the asset (hidden)",
        default=""
    )
    asset_type: StringProperty(
        name="Asset Type",
        description="Asset Type",
        default=""
    )
    name: StringProperty(
        name="Name",
        description="Main name of the asset",
        default="",
    )
    description: StringProperty(
        name="Description",
        description="Description of the asset",
        default="")
    tags: StringProperty(
        name="Tags",
        description="List of tags, separated by commas (optional)",
        default="",
    )
    category: EnumProperty(
        name="Category",
        description="main category to put into",
        items=categories.get_category_enums,
        update=categories.update_category_enums
    )
    subcategory: EnumProperty(
        name="Subcategory",
        description="main category to put into",
        items=categories.get_subcategory_enums,
        update=categories.update_subcategory_enums
    )
    subcategory1: EnumProperty(
        name="Subcategory",
        description="main category to put into",
        items=categories.get_subcategory1_enums
    )
    license: EnumProperty(
        items=licenses,
        default='royalty_free',
        description='License. Please read our help for choosing the right licenses',
    )
    is_private: EnumProperty(
        name="Thumbnail Style",
        items=(
            ('PRIVATE', 'Private', "You asset will be hidden to public. The private assets are limited by a quota."),
            ('PUBLIC', 'Public', '"Your asset will go into the validation process automatically')
        ),
        description="If not marked private, your asset will go into the validation process automatically\n"
                    "Private assets are limited by quota.",
        default="PUBLIC",
    )

    free_full: EnumProperty(
        name="Free or Full Plan",
        items=(
            ('FREE', 'Free', "You consent you want to release this asset as free for everyone"),
            ('FULL', 'Full', 'Your asset will be in the full plan')
        ),
        description="Choose whether the asset should be free or in the Full Plan",
        default="FULL",
        update=update_free_full
    )


    ####################



    @classmethod
    def poll(cls, context):
        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        return True

    def draw(self, context):
        layout = self.layout
        # col = layout.column()
        layout.label(text=self.message)
        row = layout.row()

        layout.prop(self, 'category')
        if self.category != 'NONE' and self.subcategory != 'NONE':
            layout.prop(self, 'subcategory')
        if self.subcategory != 'NONE' and self.subcategory1 != 'NONE':
            enums = categories.get_subcategory1_enums(self, context)
            if enums[0][0] != 'NONE':
                layout.prop(self, 'subcategory1')
        layout.prop(self, 'name')
        layout.prop(self, 'description')
        layout.prop(self, 'tags')
        layout.prop(self, 'is_private', expand=True)
        layout.prop(self, 'free_full', expand=True)
        if self.is_private == 'PUBLIC':
            layout.prop(self, 'license')

    def execute(self, context):
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        props = bpy.context.scene.blenderkitUI
        if self.subcategory1 != 'NONE':
            category = self.subcategory1
        elif self.subcategory != 'NONE':
            category = self.subcategory
        else:
            category = self.category
        utils.update_tags(self, context)

        mdict = {
            'category': category,
            'displayName': self.name,
            'description': self.description,
            'tags': comma2array(self.tags),
            'isPrivate': self.is_private == 'PRIVATE',
            'isFree': self.free_full == 'FREE',
            'license': self.license,
        }

        thread = threading.Thread(target=patch_individual_metadata,
                                  args=(self.asset_id, mdict, user_preferences.api_key))
        thread.start()
        tasks_queue.add_task((ui.add_report, (f'Uploading metadata for {self.name}. '
                                              f'Refresh search results to see that changes applied correctly.', 8,)))

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        if ui_props.active_index > -1:
            sr = bpy.context.window_manager['search results']
            asset_data = dict(sr[ui_props.active_index])
        else:

            active_asset = utils.get_active_asset_by_type(asset_type = self.asset_type)
            asset_data = active_asset.get('asset_data')

        if not can_edit_asset(asset_data=asset_data):
            return {'CANCELLED'}
        self.asset_id = asset_data['id']
        self.asset_type = asset_data['assetType']
        cat_path = categories.get_category_path(bpy.context.window_manager['bkit_categories'],
                                                asset_data['category'])
        try:
            if len(cat_path) > 1:
                self.category = cat_path[1]
            if len(cat_path) > 2:
                self.subcategory = cat_path[2]
        except Exception as e:
            print(e)

        self.message = f"Fast edit metadata of {asset_data['name']}"
        self.name = asset_data['displayName']
        self.description = asset_data['description']
        self.tags = ','.join(asset_data['tags'])
        if asset_data['isPrivate']:
            self.is_private = 'PRIVATE'
        else:
            self.is_private = 'PUBLIC'

        if asset_data['isFree']:
            self.free_full = 'FREE'
        else:
            self.free_full = 'FULL'
        self.license = asset_data['license']

        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=600)


def verification_status_change_thread(asset_id, state, api_key):
    upload_data = {
        "verificationStatus": state
    }
    url = paths.get_api_url() + 'assets/' + str(asset_id) + '/'
    headers = utils.get_headers(api_key)
    try:
        r = rerequests.patch(url, json=upload_data, headers=headers, verify=True)  # files = files,
    except requests.exceptions.RequestException as e:
        print(e)
        return {'CANCELLED'}
    return {'FINISHED'}


def get_upload_location(props):
    '''
    not used by now, gets location of uploaded asset - potentially usefull if we draw a nice upload gizmo in viewport.
    Parameters
    ----------
    props

    Returns
    -------

    '''
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI
    if ui_props.asset_type == 'MODEL':
        if bpy.context.view_layer.objects.active is not None:
            ob = utils.get_active_model()
            return ob.location
    if ui_props.asset_type == 'SCENE':
        return None
    elif ui_props.asset_type == 'MATERIAL':
        if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None:
            return bpy.context.active_object.location
    elif ui_props.asset_type == 'TEXTURE':
        return None
    elif ui_props.asset_type == 'BRUSH':
        return None
    return None


def check_storage_quota(props):
    if props.is_private == 'PUBLIC':
        return True

    profile = bpy.context.window_manager.get('bkit profile')
    if profile is None or profile.get('remainingPrivateQuota') is None:
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        adata = search.request_profile(preferences.api_key)
        if adata is None:
            props.report = 'Please log-in first.'
            return False
        search.write_profile(adata)
        profile = adata
    quota = profile['user'].get('remainingPrivateQuota')
    if quota is None or quota > 0:
        return True
    props.report = 'Private storage quota exceeded.'
    return False


def auto_fix(asset_type=''):
    # this applies various procedures to ensure coherency in the database.
    asset = utils.get_active_asset()
    props = utils.get_upload_props()
    if asset_type == 'MATERIAL':
        overrides.ensure_eevee_transparency(asset)
        asset.name = props.name


upload_threads = []


class Uploader(threading.Thread):
    '''
       Upload thread -
        - first uploads metadata
        - blender gets started to process the file if .blend is uploaded
        - if files need to be uploaded, uploads them
        - thumbnail goes first
        - files get uploaded

       Returns
       -------

   '''

    def __init__(self, upload_data=None, export_data=None, upload_set=None):
        super(Uploader, self).__init__()
        self.upload_data = upload_data
        self.export_data = export_data
        self.upload_set = upload_set
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def send_message(self, message):
        message = str(message).replace("'", "")

        # this adds a UI report but also writes above the upload panel fields.
        tasks_queue.add_task((ui.add_report, (message,)))
        estring = f"{self.export_data['eval_path_state']} = '{message}'"
        tasks_queue.add_task((exec, (estring,)))

    def end_upload(self, message):
        estring = self.export_data['eval_path_computing'] + ' = False'
        tasks_queue.add_task((exec, (estring,)))
        self.send_message(message)

    def run(self):
        # utils.pprint(upload_data)
        self.upload_data['parameters'] = utils.dict_to_params(
            self.upload_data['parameters'])  # weird array conversion only for upload, not for tooltips.

        script_path = os.path.dirname(os.path.realpath(__file__))

        # first upload metadata to server, so it can be saved inside the current file
        url = paths.get_api_url() + 'assets/'

        headers = utils.get_headers(self.upload_data['token'])

        # self.upload_data['license'] = 'ovejajojo'
        json_metadata = self.upload_data  # json.dumps(self.upload_data, ensure_ascii=False).encode('utf8')

        # tasks_queue.add_task((ui.add_report, ('Posting metadata',)))
        self.send_message('Posting metadata')
        if self.export_data['assetBaseId'] == '':
            try:
                r = rerequests.post(url, json=json_metadata, headers=headers, verify=True,
                                    immediate=True)  # files = files,

                # tasks_queue.add_task((ui.add_report, ('uploaded metadata',)))
                utils.p(r.text)
                self.send_message('uploaded metadata')

            except requests.exceptions.RequestException as e:
                print(e)
                self.end_upload(e)
                return {'CANCELLED'}

        else:
            url += self.export_data['id'] + '/'
            try:
                if 'MAINFILE' in self.upload_set:
                    json_metadata["verificationStatus"] = "uploading"
                r = rerequests.patch(url, json=json_metadata, headers=headers, verify=True,
                                     immediate=True)  # files = files,
                self.send_message('uploaded metadata')

                # tasks_queue.add_task((ui.add_report, ('uploaded metadata',)))
                # parse the request
                # print('uploaded metadata')
                print(r.text)
            except requests.exceptions.RequestException as e:
                print(e)
                self.end_upload(e)
                return {'CANCELLED'}

        if self.stopped():
            self.end_upload('Upload cancelled by user')
            return
        # props.upload_state = 'step 1'
        if self.upload_set == ['METADATA']:
            self.end_upload('Metadata posted successfully')
            return {'FINISHED'}
        try:
            rj = r.json()
            utils.pprint(rj)
            # if r.status_code not in (200, 201):
            #     if r.status_code == 401:
            #         ###ui.add_report(r.detail, 5, colors.RED)
            #     return {'CANCELLED'}
            # if props.asset_base_id == '':
            #     props.asset_base_id = rj['assetBaseId']
            #     props.id = rj['id']
            if self.export_data['assetBaseId'] == '':
                self.export_data['assetBaseId'] = rj['assetBaseId']
                self.export_data['id'] = rj['id']
                # here we need to send asset ID's back into UI to be written in asset data.
                estring = f"{self.export_data['eval_path']}.blenderkit.asset_base_id = '{rj['assetBaseId']}'"
                tasks_queue.add_task((exec, (estring,)))
                estring = f"{self.export_data['eval_path']}.blenderkit.id = '{rj['id']}'"
                tasks_queue.add_task((exec, (estring,)))
                # after that, the user's file needs to be saved to save the
                # estring = f"bpy.ops.wm.save_as_mainfile(filepath={self.export_data['source_filepath']}, compress=False, copy=True)"
                # tasks_queue.add_task((exec, (estring,)))

            self.upload_data['assetBaseId'] = self.export_data['assetBaseId']
            self.upload_data['id'] = self.export_data['id']

            # props.uploading = True

            if 'MAINFILE' in self.upload_set:
                if self.upload_data['assetType'] == 'hdr':
                    fpath = self.export_data['hdr_filepath']
                else:
                    fpath = os.path.join(self.export_data['temp_dir'], self.upload_data['assetBaseId'] + '.blend')

                    clean_file_path = paths.get_clean_filepath()

                    data = {
                        'export_data': self.export_data,
                        'upload_data': self.upload_data,
                        'debug_value': self.export_data['debug_value'],
                        'upload_set': self.upload_set,
                    }
                    datafile = os.path.join(self.export_data['temp_dir'], BLENDERKIT_EXPORT_DATA_FILE)

                    with open(datafile, 'w', encoding='utf-8') as s:
                        json.dump(data, s, ensure_ascii=False, indent=4)

                    self.send_message('preparing scene - running blender instance')

                    proc = subprocess.run([
                        self.export_data['binary_path'],
                        "--background",
                        "-noaudio",
                        clean_file_path,
                        "--python", os.path.join(script_path, "upload_bg.py"),
                        "--", datafile
                    ], bufsize=1, stdout=sys.stdout, stdin=subprocess.PIPE, creationflags=utils.get_process_flags())

            if self.stopped():
                self.end_upload('Upload stopped by user')
                return

            files = []
            if 'THUMBNAIL' in self.upload_set:
                files.append({
                    "type": "thumbnail",
                    "index": 0,
                    "file_path": self.export_data["thumbnail_path"]
                })
            if 'MAINFILE' in self.upload_set:
                files.append({
                    "type": "blend",
                    "index": 0,
                    "file_path": fpath
                })

                if not os.path.exists(fpath):
                    self.send_message("File packing failed, please try manual packing first")
                    return {'CANCELLED'}

            self.send_message('Uploading files')

            uploaded = upload_bg.upload_files(self.upload_data, files)

            if uploaded:
                # mark on server as uploaded
                if 'MAINFILE' in self.upload_set:
                    confirm_data = {
                        "verificationStatus": "uploaded"
                    }

                    url = paths.get_api_url() + 'assets/'

                    headers = utils.get_headers(self.upload_data['token'])

                    url += self.upload_data["id"] + '/'

                    r = rerequests.patch(url, json=confirm_data, headers=headers, verify=True)  # files = files,

                self.end_upload('Upload finished successfully')
            else:
                self.end_upload('Upload failed')
        except Exception as e:
            self.end_upload(e)
            print(e)
            return {'CANCELLED'}


def start_upload(self, context, asset_type, reupload, upload_set):
    '''start upload process, by processing data, then start a thread that cares about the rest of the upload.'''

    # fix the name first
    props = utils.get_upload_props()

    utils.name_update(props)

    storage_quota_ok = check_storage_quota(props)
    if not storage_quota_ok:
        self.report({'ERROR_INVALID_INPUT'}, props.report)
        return {'CANCELLED'}

    location = get_upload_location(props)
    props.upload_state = 'preparing upload'

    auto_fix(asset_type=asset_type)

    # do this for fixing long tags in some upload cases
    props.tags = props.tags[:]

    # check for missing metadata
    check_missing_data(asset_type, props)
    # if previous check did find any problems then
    if props.report != '':
        return {'CANCELLED'}

    if not reupload:
        props.asset_base_id = ''
        props.id = ''

    export_data, upload_data = get_upload_data(caller=self, context=context, asset_type=asset_type)

    # check if thumbnail exists, generate for HDR:
    if 'THUMBNAIL' in upload_set:
        if asset_type == 'HDR':
            image_utils.generate_hdr_thumbnail()
        elif not os.path.exists(export_data["thumbnail_path"]):
            props.upload_state = 'Thumbnail not found'
            props.uploading = False
            return {'CANCELLED'}

    if upload_set == {'METADATA'}:
        props.upload_state = "Updating metadata. Please don't close Blender until upload finishes"
    else:
        props.upload_state = "Starting upload. Please don't close Blender until upload finishes"
    props.uploading = True

    # save a copy of the file for processing. Only for blend files
    basename, ext = os.path.splitext(bpy.data.filepath)
    if not ext:
        ext = ".blend"
    export_data['temp_dir'] = tempfile.mkdtemp()
    export_data['source_filepath'] = os.path.join(export_data['temp_dir'], "export_blenderkit" + ext)
    if asset_type != 'HDR':
        bpy.ops.wm.save_as_mainfile(filepath=export_data['source_filepath'], compress=False, copy=True)

    export_data['binary_path'] = bpy.app.binary_path
    export_data['debug_value'] = bpy.app.debug_value

    upload_thread = Uploader(upload_data=upload_data, export_data=export_data, upload_set=upload_set)

    upload_thread.start()

    upload_threads.append(upload_thread)
    return {'FINISHED'}


asset_types = (
    ('MODEL', 'Model', 'Set of objects'),
    ('SCENE', 'Scene', 'Scene'),
    ('HDR', 'HDR', 'HDR image'),
    ('MATERIAL', 'Material', 'Any .blend Material'),
    ('TEXTURE', 'Texture', 'A texture, or texture set'),
    ('BRUSH', 'Brush', 'Brush, can be any type of blender brush'),
    ('ADDON', 'Addon', 'Addnon'),
)


class UploadOperator(Operator):
    """Tooltip"""
    bl_idname = "object.blenderkit_upload"
    bl_description = "Upload or re-upload asset + thumbnail + metadata"

    bl_label = "BlenderKit asset upload"
    bl_options = {'REGISTER', 'INTERNAL'}

    # type of upload - model, material, textures, e.t.c.
    asset_type: EnumProperty(
        name="Type",
        items=asset_types,
        description="Type of upload",
        default="MODEL",
    )

    reupload: BoolProperty(
        name="reupload",
        description="reupload but also draw so that it asks what to reupload",
        default=False,
        options={'SKIP_SAVE'}
    )

    metadata: BoolProperty(
        name="metadata",
        default=True,
        options={'SKIP_SAVE'}
    )

    thumbnail: BoolProperty(
        name="thumbnail",
        default=False,
        options={'SKIP_SAVE'}
    )

    main_file: BoolProperty(
        name="main file",
        default=False,
        options={'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        return utils.uploadable_asset_poll()

    def execute(self, context):
        bpy.ops.object.blenderkit_auto_tags()
        props = utils.get_upload_props()

        # in case of name change, we have to reupload everything, since the name is stored in blender file,
        # and is used for linking to scene
        # if props.name_changed:
        #     # TODO: this needs to be replaced with new double naming scheme (metadata vs blend data)
        #     # print('has to reupload whole data, name has changed.')
        #     self.main_file = True
        #     props.name_changed = False

        upload_set = []
        if not self.reupload:
            upload_set = ['METADATA', 'THUMBNAIL', 'MAINFILE']
        else:
            if self.metadata:
                upload_set.append('METADATA')
            if self.thumbnail:
                upload_set.append('THUMBNAIL')
            if self.main_file:
                upload_set.append('MAINFILE')

        # this is accessed later in get_upload_data and needs to be written.
        # should pass upload_set all the way to it probably
        if 'MAINFILE' in upload_set:
            self.main_file = True

        result = start_upload(self, context, self.asset_type, self.reupload, upload_set=upload_set, )

        if props.report != '':
            # self.report({'ERROR_INVALID_INPUT'}, props.report)
            self.report({'ERROR_INVALID_CONTEXT'}, props.report)

        return result

    def draw(self, context):
        props = utils.get_upload_props()
        layout = self.layout

        if self.reupload:
            # layout.prop(self, 'metadata')
            layout.prop(self, 'main_file')
            layout.prop(self, 'thumbnail')

        if props.asset_base_id != '' and not self.reupload:
            layout.label(text="Really upload as new? ")
            layout.label(text="Do this only when you create a new asset from an old one.")
            layout.label(text="For updates of thumbnail or model use reupload.")

        if props.is_private == 'PUBLIC':
            if self.asset_type == 'MODEL':
                utils.label_multiline(layout, text='You marked the asset as public.\n'
                                                   'This means it will be validated by our team.\n\n'
                                                   'Please test your upload after it finishes:\n'
                                                   '-   Open a new file\n'
                                                   '-   Find the asset and download it\n'
                                                   '-   Check if it snaps correctly to surfaces\n'
                                                   '-   Check if it has all textures and renders as expected\n'
                                                   '-   Check if it has correct size in world units (for models)'
                                      , width=400)
            else:
                utils.label_multiline(layout, text='You marked the asset as public.\n'
                                                   'This means it will be validated by our team.\n\n'
                                                   'Please test your upload after it finishes:\n'
                                                   '-   Open a new file\n'
                                                   '-   Find the asset and download it\n'
                                                   '-   Check if it works as expected\n'
                                      , width=400)

    def invoke(self, context, event):
        props = utils.get_upload_props()

        if not utils.user_logged_in():
            ui_panels.draw_not_logged_in(self, message='To upload assets you need to login/signup.')
            return {'CANCELLED'}

        if props.is_private == 'PUBLIC':
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)


class AssetDebugPrint(Operator):
    """Change verification status"""
    bl_idname = "object.blenderkit_print_asset_debug"
    bl_description = "BlenderKit print asset data for debug purposes"
    bl_label = "BlenderKit print asset data"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    # type of upload - model, material, textures, e.t.c.
    asset_id: StringProperty(
        name="asset id",
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences

        if not bpy.context.window_manager['search results']:
            print('no search results found')
            return {'CANCELLED'};
        # update status in search results for validator's clarity
        sr = bpy.context.window_manager['search results']
        sro = bpy.context.window_manager['search results orig']['results']

        result = None
        for r in sr:
            if r['id'] == self.asset_id:
                result = r.to_dict()
        if not result:
            for r in sro:
                if r['id'] == self.asset_id:
                    result = r.to_dict()
        if not result:
            ad = bpy.context.active_object.get('asset_data')
            if ad:
                result = ad.to_dict()
        if result:
            t = bpy.data.texts.new(result['name'])
            t.write(json.dumps(result, indent=4, sort_keys=True))
            print(json.dumps(result, indent=4, sort_keys=True))
        return {'FINISHED'}


class AssetVerificationStatusChange(Operator):
    """Change verification status"""
    bl_idname = "object.blenderkit_change_status"
    bl_description = "Change asset status"
    bl_label = "Change verification status"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    # type of upload - model, material, textures, e.t.c.
    asset_id: StringProperty(
        name="asset id",
    )

    state: StringProperty(
        name="verification_status",
        default='uploaded'
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        # if self.state == 'deleted':
        layout.label(text='Really delete asset from BlenderKit online storage?')
        # layout.prop(self, 'state')

    def execute(self, context):
        preferences = bpy.context.preferences.addons['blenderkit'].preferences

        if not bpy.context.window_manager['search results']:
            return {'CANCELLED'};
        # update status in search results for validator's clarity
        sr = bpy.context.window_manager['search results']
        sro = bpy.context.window_manager['search results orig']['results']

        for r in sr:
            if r['id'] == self.asset_id:
                r['verificationStatus'] = self.state
        for r in sro:
            if r['id'] == self.asset_id:
                r['verificationStatus'] = self.state

        thread = threading.Thread(target=verification_status_change_thread,
                                  args=(self.asset_id, self.state, preferences.api_key))
        thread.start()
        return {'FINISHED'}

    def invoke(self, context, event):
        # print(self.state)
        if self.state == 'deleted':
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}


def register_upload():
    bpy.utils.register_class(UploadOperator)
    # bpy.utils.register_class(FastMetadataMenu)
    bpy.utils.register_class(FastMetadata)
    bpy.utils.register_class(AssetDebugPrint)
    bpy.utils.register_class(AssetVerificationStatusChange)


def unregister_upload():
    bpy.utils.unregister_class(UploadOperator)
    # bpy.utils.unregister_class(FastMetadataMenu)
    bpy.utils.unregister_class(FastMetadata)
    bpy.utils.unregister_class(AssetDebugPrint)
    bpy.utils.unregister_class(AssetVerificationStatusChange)
