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


if "bpy" in locals():
    from importlib import reload

    paths = reload(paths)
else:
    from blenderkit import paths

import bpy
from mathutils import Vector
import json
import os
import requests


def activate(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def selection_get():
    aob = bpy.context.active_object
    selobs = bpy.context.selected_objects
    return (aob, selobs)


def selection_set(sel):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = sel[0]
    for ob in sel[1]:
        ob.select_set(True)


def get_active_model():
    if hasattr(bpy.context, 'active_object'):
        ob = bpy.context.active_object
        while ob.parent is not None:
            ob = ob.parent
        return ob
    return None


def get_selected_models():
    obs = bpy.context.selected_objects[:]
    done = {}
    parents = []
    for ob in obs:
        if ob not in done:
            while ob.parent is not None and ob not in done:
                done[ob] = True
                ob = ob.parent

            if ob not in parents and ob not in done:
                if ob.blenderkit.name != '':
                    parents.append(ob)
            done[ob] = True
    return parents


def get_search_props():
    scene = bpy.context.scene
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


def get_active_asset():
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI
    if ui_props.asset_type == 'MODEL':
        if bpy.context.active_object is not None:
            ob = get_active_model()
            return ob
    if ui_props.asset_type == 'SCENE':
        return bpy.context.scene

    elif ui_props.asset_type == 'MATERIAL':
        if bpy.context.active_object is not None and bpy.context.active_object.active_material is not None:
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
        if bpy.context.active_object is not None:
            ob = get_active_model()
            return ob.blenderkit
    if ui_props.asset_type == 'SCENE':
        s = bpy.context.scene
        return s.blenderkit
    elif ui_props.asset_type == 'MATERIAL':
        if bpy.context.active_object is not None and bpy.context.active_object.active_material is not None:
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
        return '.bkit_preview_' + str(index).zfill(2)
    else:
        return '.bkit_preview_full_' + str(index).zfill(2)


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
        with open(fpath, 'r') as s:
            prefs = json.load(s)
            user_preferences.api_key = prefs.get('API_key', '')
            user_preferences.global_dir = prefs.get('global_dir', paths.default_global_dict())
            user_preferences.api_key_refresh = prefs.get('API_key_refresh', '')


def save_prefs(self, context):
    # first check context, so we don't do this on registration or blender startup
    if not bpy.app.background and hasattr(bpy.context, 'view_layer'):
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        # we test the api key for lenght, so not a random accidentaly typed sequence gets saved.
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
        # user_preferences.api_key = user_preferences.api_key.strip()
        fpath = paths.BLENDERKIT_SETTINGS_FILENAME
        f = open(fpath, 'w')
        with open(fpath, 'w') as s:
            json.dump(prefs, s)
        bpy.ops.wm.save_userpref()


def get_hidden_image(tpath, bdata_name, force_reload=False):
    hidden_name = '.%s' % bdata_name
    img = bpy.data.images.get(hidden_name)

    if tpath.startswith('//'):
        tpath = bpy.path.abspath(tpath)

    gap = '\n\n\n'
    en = '\n'
    if img == None or (img.filepath != tpath):
        if tpath.startswith('//'):
            tpath = bpy.path.abspath(tpath)
        if not os.path.exists(tpath) or tpath == '':
            tpath = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')

        if img is None:
            img = bpy.data.images.load(tpath)
            img.name = hidden_name
        else:
            if img.filepath != tpath:
                if img.packed_file is not None:
                    img.unpack(method='USE_ORIGINAL')

                img.filepath = tpath
                img.reload()
    elif force_reload:
        if img.packed_file is not None:
            img.unpack(method='USE_ORIGINAL')
        img.reload()
    img.colorspace_settings.name = 'Linear'
    return img


def get_thumbnail(name):
    p = paths.get_addon_thumbnail_path(name)
    name = '.%s' % name
    img = bpy.data.images.get(name)
    if img == None:
        img = bpy.data.images.load(p)
        img.colorspace_settings.name = 'Linear'
        img.name = name
        img.name = name

    return img


def get_brush_props(context):
    brush = get_active_brush()
    if brush is not None:
        return brush.blenderkit
    return None


def p(text, text1='', text2='', text3='', text4='', text5=''):
    '''debug printing depending on blender's debug value'''
    if bpy.app.debug_value > 0:
        print(text, text1, text2, text3, text4, text5)


def pprint(data):
    '''pretty print jsons'''
    p(json.dumps(data, indent=4, sort_keys=True))


def get_hierarchy(ob):
    '''get all objects in a tree'''
    obs = []
    doobs = [ob]
    while len(doobs) > 0:
        o = doobs.pop()
        doobs.extend(o.children)
        obs.append(o)
    return obs


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
    r = requests.post(url, json=json, verify=True, headers=headers)


def get_headers(api_key):
    headers = {
        "accept": "application/json",
    }
    if api_key != '':
        headers["Authorization"] = "Bearer %s" % api_key
    return headers


# map uv cubic and switch of auto tex space and set it to 1,1,1
def automap(target_object=None, target_slot=None, tex_size=1, bg_exception=False):
    from blenderkit import bg_blender as bg
    s = bpy.context.scene
    mat_props = s.blenderkit_mat
    if mat_props.automap:
        tob = bpy.data.objects[target_object]
        # only automap mesh models
        if tob.type == 'MESH':
            actob = bpy.context.active_object
            bpy.context.view_layer.objects.active = tob

            # auto tex space
            if tob.data.use_auto_texspace:
                tob.data.use_auto_texspace = False

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
            bpy.ops.uv.cube_project(
                cube_size=scale * 2.0 / (tex_size),
                correct_aspect=False)  # it's 2.0 because blender can't tell size of a cube :)
            bpy.ops.object.editmode_toggle()
            tob.data.uv_layers.active = tob.data.uv_layers['automap']
            tob.data.uv_layers["automap"].active_render = True
            bpy.context.view_layer.objects.active = actob
