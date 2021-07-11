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


from blenderkit import paths, rerequests, image_utils

import bpy
from mathutils import Vector
import json
import os
import sys
import shutil
import logging
import traceback
import inspect

bk_logger = logging.getLogger('blenderkit')

ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
HIGH_PRIORITY_CLASS = 0x00000080
IDLE_PRIORITY_CLASS = 0x00000040
NORMAL_PRIORITY_CLASS = 0x00000020
REALTIME_PRIORITY_CLASS = 0x00000100

supported_material_click = ('MESH', 'CURVE', 'META', 'FONT', 'SURFACE', 'VOLUME', 'GPENCIL')
# supported_material_drag = ('MESH', 'CURVE', 'META', 'FONT', 'SURFACE', 'VOLUME', 'GPENCIL')
supported_material_drag = ('MESH')


def experimental_enabled():
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    return preferences.experimental_features


def get_process_flags():
    flags = BELOW_NORMAL_PRIORITY_CLASS
    if sys.platform != 'win32':  # TODO test this on windows
        flags = 0
    return flags


def activate(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def selection_get():
    aob = bpy.context.view_layer.objects.active
    selobs = bpy.context.view_layer.objects.selected[:]
    return (aob, selobs)


def selection_set(sel):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = sel[0]
    for ob in sel[1]:
        ob.select_set(True)


def get_active_model():
    if bpy.context.view_layer.objects.active is not None:
        ob = bpy.context.view_layer.objects.active
        while ob.parent is not None:
            ob = ob.parent
        return ob
    return None


def get_active_HDR():
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI
    image = ui_props.hdr_upload_image
    return image


def get_selected_models():
    '''
    Detect all hierarchies that contain asset data from selection. Only parents that have actual ['asset data'] get returned
    Returns
    list of objects containing asset data.

    '''
    obs = bpy.context.selected_objects[:]
    done = {}
    parents = []
    for ob in obs:
        if ob not in done:
            while ob.parent is not None and ob not in done and ob.blenderkit.asset_base_id == '' and ob.instance_collection is None:
                done[ob] = True
                ob = ob.parent

            if ob not in parents and ob not in done:
                if ob.blenderkit.name != '' or ob.instance_collection is not None:
                    parents.append(ob)
            done[ob] = True

    # if no blenderkit - like objects were found, use the original selection.
    if len(parents) == 0:
        parents = obs
    return parents


def get_selected_replace_adepts():
    '''
    Detect all hierarchies that contain either asset data from selection, or selected objects themselves.
    Returns
    list of objects for replacement.

    '''
    obs = bpy.context.selected_objects[:]
    done = {}
    parents = []
    for selected_ob in obs:
        ob = selected_ob
        if ob not in done:
            while ob.parent is not None and ob not in done and ob.blenderkit.asset_base_id == '' and ob.instance_collection is None:
                done[ob] = True
                # print('step,',ob.name)
                ob = ob.parent

            # print('fin', ob.name)
            if ob not in parents and ob not in done:
                if ob.blenderkit.name != '' or ob.instance_collection is not None:
                    parents.append(ob)

            done[ob] = True
    # print(parents)
    # if no blenderkit - like objects were found, use the original selection.
    if len(parents) == 0:
        parents = obs
    pprint('replace adepts')
    pprint(str(parents))
    return parents


def get_search_props():
    scene = bpy.context.scene
    if scene is None:
        return;
    uiprops = scene.blenderkitUI
    props = None
    if uiprops.asset_type == 'MODEL':
        if not hasattr(scene, 'blenderkit_models'):
            return;
        props = scene.blenderkit_models
    if uiprops.asset_type == 'SCENE':
        if not hasattr(scene, 'blenderkit_scene'):
            return;
        props = scene.blenderkit_scene
    if uiprops.asset_type == 'HDR':
        if not hasattr(scene, 'blenderkit_HDR'):
            return;
        props = scene.blenderkit_HDR
    if uiprops.asset_type == 'MATERIAL':
        if not hasattr(scene, 'blenderkit_mat'):
            return;
        props = scene.blenderkit_mat

    if uiprops.asset_type == 'TEXTURE':
        if not hasattr(scene, 'blenderkit_tex'):
            return;
        # props = scene.blenderkit_tex

    if uiprops.asset_type == 'BRUSH':
        if not hasattr(scene, 'blenderkit_brush'):
            return;
        props = scene.blenderkit_brush
    return props


def get_active_asset_by_type(asset_type = 'model'):
    asset_type =asset_type.lower()
    if asset_type == 'model':
        if bpy.context.view_layer.objects.active is not None:
            ob = get_active_model()
            return ob
    if asset_type == 'scene':
        return bpy.context.scene
    if asset_type == 'hdr':
        return get_active_HDR()
    if asset_type == 'material':
        if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None:
            return bpy.context.active_object.active_material
    if asset_type == 'texture':
        return None
    if asset_type == 'brush':
        b = get_active_brush()
        if b is not None:
            return b
    return None

def get_active_asset():
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI
    if ui_props.asset_type == 'MODEL':
        if bpy.context.view_layer.objects.active is not None:
            ob = get_active_model()
            return ob
    if ui_props.asset_type == 'SCENE':
        return bpy.context.scene
    if ui_props.asset_type == 'HDR':
        return get_active_HDR()
    elif ui_props.asset_type == 'MATERIAL':
        if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None:
            return bpy.context.active_object.active_material
    elif ui_props.asset_type == 'TEXTURE':
        return None
    elif ui_props.asset_type == 'BRUSH':
        b = get_active_brush()
        if b is not None:
            return b
    return None


def get_upload_props():
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI
    if ui_props.asset_type == 'MODEL':
        if bpy.context.view_layer.objects.active is not None:
            ob = get_active_model()
            return ob.blenderkit
    if ui_props.asset_type == 'SCENE':
        s = bpy.context.scene
        return s.blenderkit
    if ui_props.asset_type == 'HDR':

        hdr = ui_props.hdr_upload_image  # bpy.data.images.get(ui_props.hdr_upload_image)
        if not hdr:
            return None
        return hdr.blenderkit
    elif ui_props.asset_type == 'MATERIAL':
        if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None:
            return bpy.context.active_object.active_material.blenderkit
    elif ui_props.asset_type == 'TEXTURE':
        return None
    elif ui_props.asset_type == 'BRUSH':
        b = get_active_brush()
        if b is not None:
            return b.blenderkit
    return None


def previmg_name(index, fullsize=False):
    if not fullsize:
        return '.bkit_preview_' + str(index).zfill(3)
    else:
        return '.bkit_preview_full_' + str(index).zfill(3)


def get_active_brush():
    context = bpy.context
    brush = None
    if context.sculpt_object:
        brush = context.tool_settings.sculpt.brush
    elif context.image_paint_object:  # could be just else, but for future possible more types...
        brush = context.tool_settings.image_paint.brush
    return brush


def load_prefs():
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    # if user_preferences.api_key == '':
    fpath = paths.BLENDERKIT_SETTINGS_FILENAME
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as s:
                prefs = json.load(s)
                user_preferences.api_key = prefs.get('API_key', '')
                user_preferences.global_dir = prefs.get('global_dir', paths.default_global_dict())
                user_preferences.api_key_refresh = prefs.get('API_key_refresh', '')
        except Exception as e:
            print('failed to read addon preferences.')
            print(e)
            os.remove(fpath)


def save_prefs(self, context):
    # first check context, so we don't do this on registration or blender startup
    if not bpy.app.background:  # (hasattr kills blender)
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        # we test the api key for length, so not a random accidentally typed sequence gets saved.
        lk = len(user_preferences.api_key)
        if 0 < lk < 25:
            # reset the api key in case the user writes some nonsense, e.g. a search string instead of the Key
            user_preferences.api_key = ''
            props = get_search_props()
            props.report = 'Login failed. Please paste a correct API Key.'

        prefs = {
            'API_key': user_preferences.api_key,
            'API_key_refresh': user_preferences.api_key_refresh,
            'global_dir': user_preferences.global_dir,
        }
        try:
            fpath = paths.BLENDERKIT_SETTINGS_FILENAME
            if not os.path.exists(paths._presets):
                os.makedirs(paths._presets)
            with open(fpath, 'w', encoding='utf-8') as s:
                json.dump(prefs, s, ensure_ascii=False, indent=4)
        except Exception as e:
            print(e)


def uploadable_asset_poll():
    '''returns true if active asset type can be uploaded'''
    ui_props = bpy.context.scene.blenderkitUI
    if ui_props.asset_type == 'MODEL':
        return bpy.context.view_layer.objects.active is not None
    if ui_props.asset_type == 'MATERIAL':
        return bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None
    if ui_props.asset_type == 'HDR':
        return ui_props.hdr_upload_image is not None
    return True


def get_hidden_texture(name, force_reload=False):
    t = bpy.data.textures.get(name)
    if t is None:
        t = bpy.data.textures.new(name, 'IMAGE')
    if not t.image or t.image.name != name:
        img = bpy.data.images.get(name)
        if img:
            t.image = img
    return t


def img_to_preview(img, copy_original = False):
    if bpy.app.version[0]>=3:
        img.preview_ensure()
    if not copy_original:
        return;
    if img.preview.image_size != img.size:
        img.preview.image_size = (img.size[0], img.size[1])
        img.preview.image_pixels_float = img.pixels[:]
    # img.preview.icon_size = (img.size[0], img.size[1])
    # img.preview.icon_pixels_float = img.pixels[:]

def get_hidden_image(tpath, bdata_name, force_reload=False, colorspace='sRGB'):
    if bdata_name[0] == '.':
        hidden_name = bdata_name
    else:
        hidden_name = '.%s' % bdata_name
    img = bpy.data.images.get(hidden_name)

    if tpath.startswith('//'):
        tpath = bpy.path.abspath(tpath)

    if img == None or (img.filepath != tpath):
        if tpath.startswith('//'):
            tpath = bpy.path.abspath(tpath)
        if not os.path.exists(tpath) or os.path.isdir(tpath):
            tpath = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')

        if img is None:
            img = bpy.data.images.load(tpath)
            img_to_preview(img)
            img.name = hidden_name
        else:
            if img.filepath != tpath:
                if img.packed_file is not None:
                    img.unpack(method='USE_ORIGINAL')

                img.filepath = tpath
                img.reload()
                img_to_preview(img)
        image_utils.set_colorspace(img, colorspace)

    elif force_reload:
        if img.packed_file is not None:
            img.unpack(method='USE_ORIGINAL')
        img.reload()
        img_to_preview(img)
        image_utils.set_colorspace(img, colorspace)

    return img


def get_thumbnail(name):
    p = paths.get_addon_thumbnail_path(name)
    name = '.%s' % name
    img = bpy.data.images.get(name)
    if img == None:
        img = bpy.data.images.load(p)
        image_utils.set_colorspace(img, 'sRGB')
        img.name = name
        img.name = name

    return img


def files_size_to_text(size):
    fsmb = size / (1024 * 1024)
    fskb = size % 1024
    if fsmb == 0:
        return f'{round(fskb)}KB'
    else:
        return f'{round(fsmb, 1)}MB'


def get_brush_props(context):
    brush = get_active_brush()
    if brush is not None:
        return brush.blenderkit
    return None


def p(text, text1='', text2='', text3='', text4='', text5='', level='DEBUG'):
    '''debug printing depending on blender's debug value'''

    if 1:  # bpy.app.debug_value != 0:
        # print('-----BKit debug-----\n')
        # traceback.print_stack()
        texts = [text1, text2, text3, text4, text5]
        text = str(text)
        for t in texts:
            if t != '':
                text += ' ' + str(t)

        bk_logger.debug(text)
        # print('---------------------\n')


def copy_asset(fp1, fp2):
    '''synchronizes the asset between folders, including it's texture subdirectories'''
    if 1:
        bk_logger.debug('copy asset')
        bk_logger.debug(fp1 + ' ' + fp2)
        if not os.path.exists(fp2):
            shutil.copyfile(fp1, fp2)
            bk_logger.debug('copied')
        source_dir = os.path.dirname(fp1)
        target_dir = os.path.dirname(fp2)
        for subdir in os.scandir(source_dir):
            if not subdir.is_dir():
                continue
            target_subdir = os.path.join(target_dir, subdir.name)
            if os.path.exists(target_subdir):
                continue
            bk_logger.debug(str(subdir) + ' ' + str(target_subdir))
            shutil.copytree(subdir, target_subdir)
            bk_logger.debug('copied')

    # except Exception as e:
    #     print('BlenderKit failed to copy asset')
    #     print(fp1, fp2)
    #     print(e)


def pprint(data, data1=None, data2=None, data3=None, data4=None):
    '''pretty print jsons'''
    p(json.dumps(data, indent=4, sort_keys=True))


def get_hierarchy(ob):
    '''get all objects in a tree'''
    obs = []
    doobs = [ob]
    # pprint('get hierarchy')
    pprint(ob.name)
    while len(doobs) > 0:
        o = doobs.pop()
        doobs.extend(o.children)
        obs.append(o)
    return obs


def select_hierarchy(ob, state=True):
    obs = get_hierarchy(ob)
    for ob in obs:
        ob.select_set(state)
    return obs


def delete_hierarchy(ob):
    obs = get_hierarchy(ob)
    bpy.ops.object.delete({"selected_objects": obs})


def get_bounds_snappable(obs, use_modifiers=False):
    # progress('getting bounds of object(s)')
    parent = obs[0]
    while parent.parent is not None:
        parent = parent.parent
    maxx = maxy = maxz = -10000000
    minx = miny = minz = 10000000

    s = bpy.context.scene

    obcount = 0  # calculates the mesh obs. Good for non-mesh objects
    matrix_parent = parent.matrix_world
    for ob in obs:
        # bb=ob.bound_box
        mw = ob.matrix_world
        subp = ob.parent
        # while parent.parent is not None:
        #     mw =

        if ob.type == 'MESH' or ob.type == 'CURVE':
            # If to_mesh() works we can use it on curves and any other ob type almost.
            # disabled to_mesh for 2.8 by now, not wanting to use dependency graph yet.
            depsgraph = bpy.context.evaluated_depsgraph_get()

            object_eval = ob.evaluated_get(depsgraph)
            if ob.type == 'CURVE':
                mesh = object_eval.to_mesh()
            else:
                mesh = object_eval.data

            # to_mesh(context.depsgraph, apply_modifiers=self.applyModifiers, calc_undeformed=False)
            obcount += 1
            if mesh is not None:
                for c in mesh.vertices:
                    coord = c.co
                    parent_coord = matrix_parent.inverted() @ mw @ Vector(
                        (coord[0], coord[1], coord[2]))  # copy this when it works below.
                    minx = min(minx, parent_coord.x)
                    miny = min(miny, parent_coord.y)
                    minz = min(minz, parent_coord.z)
                    maxx = max(maxx, parent_coord.x)
                    maxy = max(maxy, parent_coord.y)
                    maxz = max(maxz, parent_coord.z)
                # bpy.data.meshes.remove(mesh)
            if ob.type == 'CURVE':
                object_eval.to_mesh_clear()

    if obcount == 0:
        minx, miny, minz, maxx, maxy, maxz = 0, 0, 0, 0, 0, 0

    minx *= parent.scale.x
    maxx *= parent.scale.x
    miny *= parent.scale.y
    maxy *= parent.scale.y
    minz *= parent.scale.z
    maxz *= parent.scale.z

    return minx, miny, minz, maxx, maxy, maxz


def get_bounds_worldspace(obs, use_modifiers=False):
    # progress('getting bounds of object(s)')
    s = bpy.context.scene
    maxx = maxy = maxz = -10000000
    minx = miny = minz = 10000000
    obcount = 0  # calculates the mesh obs. Good for non-mesh objects
    for ob in obs:
        # bb=ob.bound_box
        mw = ob.matrix_world
        if ob.type == 'MESH' or ob.type == 'CURVE':
            depsgraph = bpy.context.evaluated_depsgraph_get()
            ob_eval = ob.evaluated_get(depsgraph)
            mesh = ob_eval.to_mesh()
            obcount += 1
            if mesh is not None:
                for c in mesh.vertices:
                    coord = c.co
                    world_coord = mw @ Vector((coord[0], coord[1], coord[2]))
                    minx = min(minx, world_coord.x)
                    miny = min(miny, world_coord.y)
                    minz = min(minz, world_coord.z)
                    maxx = max(maxx, world_coord.x)
                    maxy = max(maxy, world_coord.y)
                    maxz = max(maxz, world_coord.z)
            ob_eval.to_mesh_clear()

    if obcount == 0:
        minx, miny, minz, maxx, maxy, maxz = 0, 0, 0, 0, 0, 0
    return minx, miny, minz, maxx, maxy, maxz


def is_linked_asset(ob):
    return ob.get('asset_data') and ob.instance_collection != None


def get_dimensions(obs):
    minx, miny, minz, maxx, maxy, maxz = get_bounds_snappable(obs)
    bbmin = Vector((minx, miny, minz))
    bbmax = Vector((maxx, maxy, maxz))
    dim = Vector((maxx - minx, maxy - miny, maxz - minz))
    return dim, bbmin, bbmax


def requests_post_thread(url, json, headers):
    r = rerequests.post(url, json=json, verify=True, headers=headers)


def get_headers(api_key):
    headers = {
        "accept": "application/json",
    }
    if api_key != '':
        headers["Authorization"] = "Bearer %s" % api_key
    return headers


def scale_2d(v, s, p):
    '''scale a 2d vector with a pivot'''
    return (p[0] + s[0] * (v[0] - p[0]), p[1] + s[1] * (v[1] - p[1]))


def scale_uvs(ob, scale=1.0, pivot=Vector((.5, .5))):
    mesh = ob.data
    if len(mesh.uv_layers) > 0:
        uv = mesh.uv_layers[mesh.uv_layers.active_index]

        # Scale a UV map iterating over its coordinates to a given scale and with a pivot point
        for uvindex in range(len(uv.data)):
            uv.data[uvindex].uv = scale_2d(uv.data[uvindex].uv, scale, pivot)


# map uv cubic and switch of auto tex space and set it to 1,1,1
def automap(target_object=None, target_slot=None, tex_size=1, bg_exception=False, just_scale=False):
    s = bpy.context.scene
    mat_props = s.blenderkit_mat
    if mat_props.automap:
        tob = bpy.data.objects[target_object]
        # only automap mesh models
        if tob.type == 'MESH' and len(tob.data.polygons) > 0:
            # check polycount for a rare case where no polys are in editmesh
            actob = bpy.context.active_object
            bpy.context.view_layer.objects.active = tob

            # auto tex space
            if tob.data.use_auto_texspace:
                tob.data.use_auto_texspace = False

            if not just_scale:
                tob.data.texspace_size = (1, 1, 1)

            if 'automap' not in tob.data.uv_layers:
                bpy.ops.mesh.uv_texture_add()
                uvl = tob.data.uv_layers[-1]
                uvl.name = 'automap'

            # TODO limit this to active material
            # tob.data.uv_textures['automap'].active = True

            scale = tob.scale.copy()

            if target_slot is not None:
                tob.active_material_index = target_slot
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')

            # this exception is just for a 2.8 background thunmbnailer crash, can be removed when material slot select works...
            if bg_exception:
                bpy.ops.mesh.select_all(action='SELECT')
            else:
                bpy.ops.object.material_slot_select()

            scale = (scale.x + scale.y + scale.z) / 3.0
            if not just_scale:
                bpy.ops.uv.cube_project(
                    cube_size=scale * 2.0 / (tex_size),
                    correct_aspect=False)  # it's * 2.0 because blender can't tell size of a unit cube :)

            bpy.ops.object.editmode_toggle()
            tob.data.uv_layers.active = tob.data.uv_layers['automap']
            tob.data.uv_layers["automap"].active_render = True
            # this by now works only for thumbnail preview, but should be extended to work on arbitrary objects.
            # by now, it takes the basic uv map = 1 meter. also, it now doeasn't respect more materials on one object,
            # it just scales whole UV.
            if just_scale:
                scale_uvs(tob, scale=Vector((1 / tex_size, 1 / tex_size)))
            bpy.context.view_layer.objects.active = actob


def name_update(props):
    '''
    Update asset name function, gets run also before upload. Makes sure name doesn't change in case of reuploads,
    and only displayName gets written to server.
    '''
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI

    # props = get_upload_props()
    if props.name_old != props.name:
        props.name_changed = True
        props.name_old = props.name
        nname = props.name.strip()
        nname = nname.replace('_', ' ')

        if nname.isupper():
            nname = nname.lower()
        nname = nname[0].upper() + nname[1:]
        props.name = nname
        # here we need to fix the name for blender data = ' or " give problems in path evaluation down the road.
    fname = props.name
    fname = fname.replace('\'', '')
    fname = fname.replace('\"', '')
    asset = get_active_asset()
    if ui_props.asset_type != 'HDR':
        # Here we actually rename assets datablocks, but don't do that with HDR's and possibly with others
        asset.name = fname

def fmt_length(prop):
    prop = str(round(prop, 2))
    return prop

def get_param(asset_data, parameter_name, default = None):
    if not asset_data.get('parameters'):
        # this can appear in older version files.
        return default

    for p in asset_data['parameters']:
        if p.get('parameterType') == parameter_name:
            return p['value']
    return default


def params_to_dict(params):
    params_dict = {}
    for p in params:
        params_dict[p['parameterType']] = p['value']
    return params_dict


def dict_to_params(inputs, parameters=None):
    if parameters == None:
        parameters = []
    for k in inputs.keys():
        if type(inputs[k]) == list:
            strlist = ""
            for idx, s in enumerate(inputs[k]):
                strlist += s
                if idx < len(inputs[k]) - 1:
                    strlist += ','

            value = "%s" % strlist
        elif type(inputs[k]) != bool:
            value = inputs[k]
        else:
            value = str(inputs[k])
        parameters.append(
            {
                "parameterType": k,
                "value": value
            })
    return parameters


def update_tags(self, context):
    props = self

    commasep = props.tags.split(',')
    ntags = []
    for tag in commasep:
        if len(tag) > 19:
            short_tags = tag.split(' ')
            for short_tag in short_tags:
                if len(short_tag) > 19:
                    short_tag = short_tag[:18]
                ntags.append(short_tag)
        else:
            ntags.append(tag)
    if len(ntags) == 1:
        ntags = ntags[0].split(' ')
    ns = ''
    for t in ntags:
        if t != '':
            ns += t + ','
    ns = ns[:-1]
    if props.tags != ns:
        props.tags = ns


def user_logged_in():
    a = bpy.context.window_manager.get('bkit profile')
    if a is not None:
        return True
    return False


def profile_is_validator():
    a = bpy.context.window_manager.get('bkit profile')
    if a is not None and a['user'].get('exmenu'):
        return True
    return False

def user_is_owner(asset_data=None):
    '''Checks if the current logged in user is owner of the asset'''
    profile = bpy.context.window_manager.get('bkit profile')
    if profile is None:
        return False
    if int(asset_data['author']['id']) == int(profile['user']['id']):
        return True
    return False

def guard_from_crash():
    '''
    Blender tends to crash when trying to run some functions
     with the addon going through unregistration process.
     This function is used in these functions (like draw callbacks)
     so these don't run during unregistration.
     '''
    if bpy.context.preferences.addons.get('blenderkit') is None:
        return False;
    if bpy.context.preferences.addons['blenderkit'].preferences is None:
        return False;
    return True


def get_largest_area(area_type='VIEW_3D'):
    maxsurf = 0
    maxa = None
    maxw = None
    region = None
    for w in bpy.data.window_managers[0].windows:
        for a in w.screen.areas:
            if a.type == area_type:
                asurf = a.width * a.height
                if asurf > maxsurf:
                    maxa = a
                    maxw = w
                    maxsurf = asurf

                    for r in a.regions:
                        if r.type == 'WINDOW':
                            region = r
    global active_area_pointer, active_window_pointer, active_region_pointer
    active_window_pointer = maxw.as_pointer()
    active_area_pointer = maxa.as_pointer()
    active_region_pointer = region.as_pointer()
    return maxw, maxa, region


def get_fake_context(context, area_type='VIEW_3D'):
    C_dict = {}  # context.copy() #context.copy was a source of problems - incompatibility with addons that also define context
    C_dict.update(region='WINDOW')

    # try:
    #     context = context.copy()
    #     # print('bk context copied successfully')
    # except Exception as e:
    #     print(e)
    #     print('BlenderKit: context.copy() failed. Can be a colliding addon.')
    context = {}

    if context.get('area') is None or context.get('area').type != area_type:
        w, a, r = get_largest_area(area_type=area_type)
        if w:
            # sometimes there is no area of the requested type. Let's face it, some people use Blender without 3d view.
            override = {'window': w, 'screen': w.screen, 'area': a, 'region': r}
            C_dict.update(override)
        # print(w,a,r)
    return C_dict

# def is_url(text):


def label_multiline(layout, text='', icon='NONE', width=-1, max_lines = 10):
    '''
     draw a ui label, but try to split it in multiple lines.

    Parameters
    ----------
    layout
    text
    icon
    width width to split by in character count
    max_lines maximum lines to draw

    Returns
    -------
    True if max_lines was overstepped
    '''
    if text.strip() == '':
        return
    text = text.replace('\r\n','\n')
    lines = text.split('\n')
    if width > 0:
        threshold = int(width / 5.5)
    else:
        threshold = 35
    li = 0
    for l in lines:
        # if is_url(l):
        li+=1
        while len(l) > threshold:
            i = l.rfind(' ', 0, threshold)
            if i < 1:
                i = threshold
            l1 = l[:i]
            layout.label(text=l1, icon=icon)
            icon = 'NONE'
            l = l[i:].lstrip()
            li += 1
            if li > max_lines:
                break;
        if li > max_lines:
            break;
        layout.label(text=l, icon=icon)
        icon = 'NONE'
    if li>max_lines:
        return True



def trace():
    traceback.print_stack()
