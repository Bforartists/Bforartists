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



from blenderkit import utils, append_link, bg_blender, download, upload_bg, upload

import sys, json, math, os
import bpy
import mathutils

BLENDERKIT_EXPORT_DATA = sys.argv[-1]


def get_obnames():
    with open(BLENDERKIT_EXPORT_DATA, 'r',encoding='utf-8') as s:
        data = json.load(s)
    obnames = eval(data['models'])
    return obnames


def center_obs_for_thumbnail(obs):
    s = bpy.context.scene
    # obs = bpy.context.selected_objects
    parent = obs[0]
    if parent.type == 'EMPTY' and parent.instance_collection is not None:
        obs = parent.instance_collection.objects[:]

    while parent.parent != None:
        parent = parent.parent
    # reset parent rotation, so we see how it really snaps.
    parent.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    minx, miny, minz, maxx, maxy, maxz = utils.get_bounds_worldspace(obs)

    cx = (maxx - minx) / 2 + minx
    cy = (maxy - miny) / 2 + miny
    for ob in s.collection.objects:
        ob.select_set(False)

    bpy.context.view_layer.objects.active = parent
    parent.location += mathutils.Vector((-cx, -cy, -minz))

    camZ = s.camera.parent.parent
    camZ.location.z = (maxz - minz) / 2
    dx = (maxx - minx)
    dy = (maxy - miny)
    dz = (maxz - minz)
    r = math.sqrt(dx * dx + dy * dy + dz * dz)

    scaler = bpy.context.view_layer.objects['scaler']
    scaler.scale = (r, r, r)
    coef = .7
    r *= coef
    camZ.scale = (r, r, r)
    bpy.context.view_layer.update()


def render_thumbnails():
    bpy.ops.render.render(write_still=True, animation=False)


if __name__ == "__main__":
    try:
        with open(BLENDERKIT_EXPORT_DATA, 'r',encoding='utf-8') as s:
            data = json.load(s)

        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences


        if data.get('do_download'):
            #need to save the file, so that asset doesn't get downloaded into addon directory
            temp_blend_path = os.path.join(data['tempdir'], 'temp.blend')
            bpy.ops.wm.save_as_mainfile(filepath = temp_blend_path)

            bg_blender.progress('Downloading asset')
            asset_data = data['asset_data']
            has_url = download.get_download_url(asset_data, download.get_scene_id(), user_preferences.api_key, tcom=None,
                                                resolution='blend')
            if not has_url == True:
                bg_blender.progress("couldn't download asset for thumnbail re-rendering")
            # download first, or rather make sure if it's already downloaded
            bg_blender.progress('downloading asset')
            fpath = download.download_asset_file(asset_data)
            data['filepath'] = fpath
            main_object, allobs = append_link.link_collection(fpath,
                                                          location=(0,0,0),
                                                          rotation=(0,0,0),
                                                          link=True,
                                                          name=asset_data['name'],
                                                          parent=None)
            allobs = [main_object]
        else:
            bg_blender.progress('preparing thumbnail scene')

            obnames = get_obnames()
            main_object, allobs = append_link.append_objects(file_name=data['filepath'],
                                                         obnames=obnames,
                                                             link=True)
        bpy.context.view_layer.update()


        camdict = {
            'GROUND': 'camera ground',
            'WALL': 'camera wall',
            'CEILING': 'camera ceiling',
            'FLOAT': 'camera float'
        }

        bpy.context.scene.camera = bpy.data.objects[camdict[data['thumbnail_snap_to']]]
        center_obs_for_thumbnail(allobs)
        bpy.context.scene.render.filepath = data['thumbnail_path']
        if user_preferences.thumbnail_use_gpu:
            bpy.context.scene.cycles.device = 'GPU'

        fdict = {
            'DEFAULT': 1,
            'FRONT': 2,
            'SIDE': 3,
            'TOP': 4,
        }
        s = bpy.context.scene
        s.frame_set(fdict[data['thumbnail_angle']])

        snapdict = {
            'GROUND': 'Ground',
            'WALL': 'Wall',
            'CEILING': 'Ceiling',
            'FLOAT': 'Float'
        }

        collection = bpy.context.scene.collection.children[snapdict[data['thumbnail_snap_to']]]
        collection.hide_viewport = False
        collection.hide_render = False
        collection.hide_select = False

        main_object.rotation_euler = (0, 0, 0)
        bpy.data.materials['bkit background'].node_tree.nodes['Value'].outputs['Value'].default_value \
            = data['thumbnail_background_lightness']
        s.cycles.samples = data['thumbnail_samples']
        bpy.context.view_layer.cycles.use_denoising = data['thumbnail_denoising']
        bpy.context.view_layer.update()

        # import blender's HDR here
        # hdr_path = Path('datafiles/studiolights/world/interior.exr')
        # bpath = Path(bpy.utils.resource_path('LOCAL'))
        # ipath = bpath / hdr_path
        # ipath = str(ipath)

        # this  stuff is for mac and possibly linux. For blender // means relative path.
        # for Mac, // means start of absolute path
        # if ipath.startswith('//'):
        #     ipath = ipath[1:]
        #
        # img = bpy.data.images['interior.exr']
        # img.filepath = ipath
        # img.reload()

        bpy.context.scene.render.resolution_x = int(data['thumbnail_resolution'])
        bpy.context.scene.render.resolution_y = int(data['thumbnail_resolution'])

        bg_blender.progress('rendering thumbnail')
        render_thumbnails()
        fpath = data['thumbnail_path'] + '.jpg'
        if data.get('upload_after_render') and data.get('asset_data'):
            # try to patch for the sake of older assets where thumbnail update doesn't work for the reasont
            # that original thumbnail files aren't available.
            # upload.patch_individual_metadata(data['asset_data']['id'], {}, user_preferences)
            bg_blender.progress('uploading thumbnail')
            file = {
                "type": "thumbnail",
                "index": 0,
                "file_path": fpath
            }
            upload_data = {
                "name": data['asset_data']['name'],
                "token": user_preferences.api_key,
                "id": data['asset_data']['id']
            }

            upload_bg.upload_file(upload_data, file)

        bg_blender.progress('background autothumbnailer finished successfully')

    except:
        import traceback

        traceback.print_exc()
        sys.exit(1)
