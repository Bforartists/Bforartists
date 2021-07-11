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


from blenderkit import paths, append_link, utils, ui, colors, tasks_queue, rerequests, resolutions, ui_panels

import threading
import time
import requests
import shutil, sys, os
import uuid
import copy
import logging

bk_logger = logging.getLogger('blenderkit')

import bpy
from bpy.props import (
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
)
from bpy.app.handlers import persistent

download_threads = []


def check_missing():
    '''checks for missing files, and possibly starts re-download of these into the scene'''
    s = bpy.context.scene
    # missing libs:
    # TODO: put these into a panel and let the user decide if these should be downloaded.
    missing = []
    for l in bpy.data.libraries:
        fp = l.filepath
        if fp.startswith('//'):
            fp = bpy.path.abspath(fp)
        if not os.path.exists(fp) and l.get('asset_data') is not None:
            missing.append(l)

    # print('missing libraries', missing)

    for l in missing:
        asset_data = l['asset_data']

        downloaded = check_existing(asset_data, resolution=asset_data.get('resolution'))
        if downloaded:
            try:
                l.reload()
            except:
                download(l['asset_data'], redownload=True)
        else:
            download(l['asset_data'], redownload=True)


def check_unused():
    '''find assets that have been deleted from scene but their library is still present.'''
    # this is obviously broken. Blender should take care of the extra data automaticlaly
    return;
    used_libs = []
    for ob in bpy.data.objects:
        if ob.instance_collection is not None and ob.instance_collection.library is not None:
            # used_libs[ob.instance_collection.name] = True
            if ob.instance_collection.library not in used_libs:
                used_libs.append(ob.instance_collection.library)

        for ps in ob.particle_systems:
            set = ps.settings
            if ps.settings.render_type == 'GROUP' \
                    and ps.settings.instance_collection is not None \
                    and ps.settings.instance_collection.library not in used_libs:
                used_libs.append(ps.settings.instance_collection)

    for l in bpy.data.libraries:
        if l not in used_libs and l.getn('asset_data'):
            print('attempt to remove this library: ', l.filepath)
            # have to unlink all groups, since the file is a 'user' even if the groups aren't used at all...
            for user_id in l.users_id:
                if type(user_id) == bpy.types.Collection:
                    bpy.data.collections.remove(user_id)
            l.user_clear()


@persistent
def scene_save(context):
    ''' does cleanup of blenderkit props and sends a message to the server about assets used.'''
    # TODO this can be optimized by merging these 2 functions, since both iterate over all objects.
    if not bpy.app.background:
        check_unused()
        report_usages()


@persistent
def scene_load(context):
    '''restart broken downloads on scene load'''
    t = time.time()
    s = bpy.context.scene
    global download_threads
    download_threads = []

    # commenting this out - old restore broken download on scene start. Might come back if downloads get recorded in scene
    # reset_asset_ids = {}
    # reset_obs = {}
    # for ob in bpy.context.scene.collection.objects:
    #     if ob.name[:12] == 'downloading ':
    #         obn = ob.name
    #
    #         asset_data = ob['asset_data']
    #
    #         # obn.replace('#', '')
    #         # if asset_data['id'] not in reset_asset_ids:
    #
    #         if reset_obs.get(asset_data['id']) is None:
    #             reset_obs[asset_data['id']] = [obn]
    #             reset_asset_ids[asset_data['id']] = asset_data
    #         else:
    #             reset_obs[asset_data['id']].append(obn)
    # for asset_id in reset_asset_ids:
    #     asset_data = reset_asset_ids[asset_id]
    #     done = False
    #     if check_existing(asset_data, resolution = should be here):
    #         for obname in reset_obs[asset_id]:
    #             downloader = s.collection.objects[obname]
    #             done = try_finished_append(asset_data,
    #                                        model_location=downloader.location,
    #                                        model_rotation=downloader.rotation_euler)
    #
    #     if not done:
    #         downloading = check_downloading(asset_data)
    #         if not downloading:
    #             print('redownloading %s' % asset_data['name'])
    #             download(asset_data, downloaders=reset_obs[asset_id], delete=True)

    # check for group users that have been deleted, remove the groups /files from the file...
    # TODO scenes fixing part... download the assets not present on drive,
    # and erase from scene linked files that aren't used in the scene.
    # print('continue downlaods ', time.time() - t)
    t = time.time()
    check_missing()
    # print('missing check', time.time() - t)


def get_scene_id():
    '''gets scene id and possibly also generates a new one'''
    bpy.context.scene['uuid'] = bpy.context.scene.get('uuid', str(uuid.uuid4()))
    return bpy.context.scene['uuid']


def report_usages():
    '''report the usage of assets to the server.'''
    mt = time.time()
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    sid = get_scene_id()
    headers = utils.get_headers(api_key)
    url = paths.get_api_url() + paths.BLENDERKIT_REPORT_URL

    assets = {}
    asset_obs = []
    scene = bpy.context.scene
    asset_usages = {}

    for ob in scene.collection.objects:
        if ob.get('asset_data') != None:
            asset_obs.append(ob)

    for ob in asset_obs:
        asset_data = ob['asset_data']
        abid = asset_data['assetBaseId']

        if assets.get(abid) is None:
            asset_usages[abid] = {'count': 1}
            assets[abid] = asset_data
        else:
            asset_usages[abid]['count'] += 1

    # brushes
    for b in bpy.data.brushes:
        if b.get('asset_data') != None:
            abid = b['asset_data']['assetBaseId']
            asset_usages[abid] = {'count': 1}
            assets[abid] = b['asset_data']
    # materials
    for ob in scene.collection.objects:
        for ms in ob.material_slots:
            m = ms.material

            if m is not None and m.get('asset_data') is not None:

                abid = m['asset_data']['assetBaseId']
                if assets.get(abid) is None:
                    asset_usages[abid] = {'count': 1}
                    assets[abid] = m['asset_data']
                else:
                    asset_usages[abid]['count'] += 1

    assets_list = []
    assets_reported = scene.get('assets reported', {})

    new_assets_count = 0
    for k in asset_usages.keys():
        if k not in assets_reported.keys():
            data = asset_usages[k]
            list_item = {
                'asset': k,
                'usageCount': data['count'],
                'proximitySet': data.get('proximity', [])
            }
            assets_list.append(list_item)
            new_assets_count += 1
        if k not in assets_reported.keys():
            assets_reported[k] = True

    scene['assets reported'] = assets_reported

    if new_assets_count == 0:
        bk_logger.debug('no new assets were added')
        return;
    usage_report = {
        'scene': sid,
        'reportType': 'save',
        'assetusageSet': assets_list
    }

    au = scene.get('assets used', {})
    ad = scene.get('assets deleted', {})

    ak = assets.keys()
    for k in au.keys():
        if k not in ak:
            ad[k] = au[k]
        else:
            if k in ad:
                ad.pop(k)

    # scene['assets used'] = {}
    for k in ak:  # rewrite assets used.
        scene['assets used'][k] = assets[k]

    ###########check ratings herer too:
    scene['assets rated'] = scene.get('assets rated', {})
    for k in assets.keys():
        scene['assets rated'][k] = scene['assets rated'].get(k, False)
    thread = threading.Thread(target=utils.requests_post_thread, args=(url, usage_report, headers))
    thread.start()
    mt = time.time() - mt
    # print('report generation:                ', mt)


def udpate_asset_data_in_dicts(asset_data):
    '''
    updates asset data in all relevant dictionaries, after a threaded download task \
    - where the urls were retrieved, and now they can be reused
    Parameters
    ----------
    asset_data - data coming back from thread, thus containing also download urls
    '''
    scene = bpy.context.scene
    scene['assets used'] = scene.get('assets used', {})
    scene['assets used'][asset_data['assetBaseId']] = asset_data.copy()

    scene['assets rated'] = scene.get('assets rated', {})
    id = asset_data['assetBaseId']
    scene['assets rated'][id] = scene['assets rated'].get(id, False)
    sr = bpy.context.window_manager['search results']
    if not sr:
        return;
    for i, r in enumerate(sr):
        if r['assetBaseId'] == asset_data['assetBaseId']:
            for f in asset_data['files']:
                if f.get('url'):
                    for f1 in r['files']:
                        if f1['fileType'] == f['fileType']:
                            f1['url'] = f['url']


def append_asset(asset_data, **kwargs):  # downloaders=[], location=None,
    '''Link asset to the scene.


    '''

    file_names = paths.get_download_filepaths(asset_data, kwargs['resolution'])
    props = None
    #####
    # how to do particle  drop:
    # link the group we are interested in( there are more groups in File!!!! , have to get the correct one!)
    s = bpy.context.scene

    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    if user_preferences.api_key == '':
        user_preferences.asset_counter += 1

    if asset_data['assetType'] == 'scene':
        sprops = s.blenderkit_scene

        scene = append_link.append_scene(file_names[0], link=sprops.append_link == 'LINK', fake_user=False)
        # print('scene appended')
        if scene is not None:
            props = scene.blenderkit
            asset_main = scene
            if sprops.switch_after_append:
                bpy.context.window_manager.windows[0].scene = scene

    if asset_data['assetType'] == 'hdr':
        hdr = append_link.load_HDR(file_name=file_names[0], name=asset_data['name'])
        props = hdr.blenderkit
        asset_main = hdr


    if asset_data['assetType'] == 'model':
        downloaders = kwargs.get('downloaders')
        sprops = s.blenderkit_models
        # TODO this is here because combinations of linking objects or appending groups are rather not-usefull
        if sprops.append_method == 'LINK_COLLECTION':
            sprops.append_link = 'LINK'
            sprops.import_as = 'GROUP'
        else:
            sprops.append_link = 'APPEND'
            sprops.import_as = 'INDIVIDUAL'

        # copy for override
        al = sprops.append_link
        # set consistency for objects already in scene, otherwise this literally breaks blender :)
        ain, resolution = asset_in_scene(asset_data)
        # this is commented out since it already happens in start_download function.
        # if resolution:
        #     kwargs['resolution'] = resolution
        # override based on history
        if ain is not False:
            if ain == 'LINKED':
                al = 'LINK'
            else:
                al = 'APPEND'
                if asset_data['assetType'] == 'model':
                    source_parent = get_asset_in_scene(asset_data)
                    if source_parent:
                        asset_main, new_obs = duplicate_asset(source=source_parent, **kwargs)
                        asset_main.location = kwargs['model_location']
                        asset_main.rotation_euler = kwargs['model_rotation']
                        # this is a case where asset is already in scene and should be duplicated instead.
                        # there is a big chance that the duplication wouldn't work perfectly(hidden or unselectable objects)
                        # so here we need to check and return if there was success
                        # also, if it was successful, no other operations are needed , basically all asset data is already ready from the original asset
                        if new_obs:
                            # update here assets rated/used because there might be new download urls?
                            udpate_asset_data_in_dicts(asset_data)
                            bpy.ops.wm.undo_push_context(message='add %s to scene' % asset_data['name'])

                            return

        # first get conditions for append link
        link = al == 'LINK'
        # then append link
        if downloaders:
            for downloader in downloaders:
                # this cares for adding particle systems directly to target mesh, but I had to block it now,
                # because of the sluggishnes of it. Possibly re-enable when it's possible to do this faster?
                if 'particle_plants' in asset_data['tags']:
                    append_link.append_particle_system(file_names[-1],
                                                       target_object=kwargs['target_object'],
                                                       rotation=downloader['rotation'],
                                                       link=False,
                                                       name=asset_data['name'])
                    return

                if link:
                    asset_main, new_obs = append_link.link_collection(file_names[-1],
                                                                      location=downloader['location'],
                                                                      rotation=downloader['rotation'],
                                                                      link=link,
                                                                      name=asset_data['name'],
                                                                      parent=kwargs.get('parent'))

                else:

                    asset_main, new_obs = append_link.append_objects(file_names[-1],
                                                                     location=downloader['location'],
                                                                     rotation=downloader['rotation'],
                                                                     link=link,
                                                                     name=asset_data['name'],
                                                                     parent=kwargs.get('parent'))
                if asset_main.type == 'EMPTY' and link:
                    bmin = asset_data['bbox_min']
                    bmax = asset_data['bbox_max']
                    size_min = min(1.0, (bmax[0] - bmin[0] + bmax[1] - bmin[1] + bmax[2] - bmin[2]) / 3)
                    asset_main.empty_display_size = size_min

        elif kwargs.get('model_location') is not None:
            if link:
                asset_main, new_obs = append_link.link_collection(file_names[-1],
                                                                  location=kwargs['model_location'],
                                                                  rotation=kwargs['model_rotation'],
                                                                  link=link,
                                                                  name=asset_data['name'],
                                                                  parent=kwargs.get('parent'))
            else:
                asset_main, new_obs = append_link.append_objects(file_names[-1],
                                                                 location=kwargs['model_location'],
                                                                 rotation=kwargs['model_rotation'],
                                                                 link=link,
                                                                 name=asset_data['name'],
                                                                 parent=kwargs.get('parent'))

            # scale Empty for assets, so they don't clutter the scene.
            if asset_main.type == 'EMPTY' and link:
                bmin = asset_data['bbox_min']
                bmax = asset_data['bbox_max']
                size_min = min(1.0, (bmax[0] - bmin[0] + bmax[1] - bmin[1] + bmax[2] - bmin[2]) / 3)
                asset_main.empty_display_size = size_min

        if link:
            group = asset_main.instance_collection

            lib = group.library
            lib['asset_data'] = asset_data

    elif asset_data['assetType'] == 'brush':

        # TODO if already in scene, should avoid reappending.
        inscene = False
        for b in bpy.data.brushes:

            if b.blenderkit.id == asset_data['id']:
                inscene = True
                brush = b
                break;
        if not inscene:
            brush = append_link.append_brush(file_names[-1], link=False, fake_user=False)

            thumbnail_name = asset_data['thumbnail'].split(os.sep)[-1]
            tempdir = paths.get_temp_dir('brush_search')
            thumbpath = os.path.join(tempdir, thumbnail_name)
            asset_thumbs_dir = paths.get_download_dirs('brush')[0]
            asset_thumb_path = os.path.join(asset_thumbs_dir, thumbnail_name)
            shutil.copy(thumbpath, asset_thumb_path)
            brush.icon_filepath = asset_thumb_path

        if bpy.context.view_layer.objects.active.mode == 'SCULPT':
            bpy.context.tool_settings.sculpt.brush = brush
        elif bpy.context.view_layer.objects.active.mode == 'TEXTURE_PAINT':  # could be just else, but for future possible more types...
            bpy.context.tool_settings.image_paint.brush = brush
        # TODO set brush by by asset data(user can be downloading while switching modes.)

        # bpy.context.tool_settings.image_paint.brush = brush
        props = brush.blenderkit
        asset_main = brush

    elif asset_data['assetType'] == 'material':
        inscene = False
        sprops = s.blenderkit_mat

        for m in bpy.data.materials:
            if m.blenderkit.id == asset_data['id']:
                inscene = True
                material = m
                break;
        if not inscene:
            link = sprops.append_method == 'LINK'
            material = append_link.append_material(file_names[-1], link=link, fake_user=False)
        target_object = bpy.data.objects[kwargs['target_object']]

        if len(target_object.material_slots) == 0:
            target_object.data.materials.append(material)
        else:
            target_object.material_slots[kwargs['material_target_slot']].material = material

        asset_main = material

    asset_data['resolution'] = kwargs['resolution']
    udpate_asset_data_in_dicts(asset_data)

    asset_main['asset_data'] = asset_data  # TODO remove this??? should write to blenderkit Props?
    asset_main.blenderkit.asset_base_id = asset_data['assetBaseId']
    asset_main.blenderkit.id = asset_data['id']
    bpy.ops.wm.undo_push_context(message='add %s to scene' % asset_data['name'])
    # moving reporting to on save.
    # report_use_success(asset_data['id'])


def replace_resolution_linked(file_paths, asset_data):
    # replace one asset resolution for another.
    # this is the much simpler case
    #  - find the library,
    #  - replace the path and name of the library, reload.
    file_name = os.path.basename(file_paths[-1])

    for l in bpy.data.libraries:
        if not l.get('asset_data'):
            continue;
        if not l['asset_data']['assetBaseId'] == asset_data['assetBaseId']:
            continue;

        bk_logger.debug('try to re-link library')

        if not os.path.isfile(file_paths[-1]):
            bk_logger.debug('library file doesnt exist')
            break;
        l.filepath = os.path.join(os.path.dirname(l.filepath), file_name)
        l.name = file_name
        udpate_asset_data_in_dicts(asset_data)


def replace_resolution_appended(file_paths, asset_data, resolution):
    # In this case the texture paths need to be replaced.
    # Find the file path pattern that is present in texture paths
    # replace the pattern with the new one.
    file_name = os.path.basename(file_paths[-1])

    new_filename_pattern = os.path.splitext(file_name)[0]
    all_patterns = []
    for suff in paths.resolution_suffix.values():
        pattern = f"{asset_data['id']}{os.sep}textures{suff}{os.sep}"
        all_patterns.append(pattern)
    new_pattern = f"{asset_data['id']}{os.sep}textures{paths.resolution_suffix[resolution]}{os.sep}"

    # replace the pattern with the new one.
    # print(existing_filename_patterns)
    # print(new_filename_pattern)
    # print('existing images:')
    for i in bpy.data.images:

        for old_pattern in all_patterns:
            if i.filepath.find(old_pattern) > -1:
                fp = i.filepath.replace(old_pattern, new_pattern)
                fpabs = bpy.path.abspath(fp)
                if not os.path.exists(fpabs):
                    # this currently handles .png's that have been swapped to .jpg's during resolution generation process.
                    # should probably also handle .exr's and similar others.
                    # bk_logger.debug('need to find a replacement')
                    base, ext = os.path.splitext(fp)
                    if resolution == 'blend' and i.get('original_extension'):
                        fp = base + i.get('original_extension')
                    elif ext in ('.png', '.PNG'):
                        fp = base + '.jpg'
                i.filepath = fp
                i.filepath_raw = fp  # bpy.path.abspath(fp)
                for pf in i.packed_files:
                    pf.filepath = fp
                i.reload()
    udpate_asset_data_in_dicts(asset_data)


# @bpy.app.handlers.persistent
def download_timer():
    # TODO might get moved to handle all blenderkit stuff, not to slow down.
    '''
    check for running and finished downloads.
    Running downloads get checked for progress which is passed to UI.
    Finished downloads are processed and linked/appended to scene.
     '''
    global download_threads
    # utils.p('start download timer')

    # bk_logger.debug('timer download')

    if len(download_threads) == 0:
        # utils.p('end download timer')

        return 2
    s = bpy.context.scene
    for threaddata in download_threads:
        t = threaddata[0]
        asset_data = threaddata[1]
        tcom = threaddata[2]

        progress_bars = []
        downloaders = []

        if t.is_alive():  # set downloader size
            sr = bpy.context.window_manager.get('search results')
            if sr is not None:
                for r in sr:
                    if asset_data['id'] == r['id']:
                        r['downloaded'] = 0.5#tcom.progress
        if not t.is_alive():
            if tcom.error:
                sprops = utils.get_search_props()
                sprops.report = tcom.report
                download_threads.remove(threaddata)
                # utils.p('end download timer')

                return
            file_paths = paths.get_download_filepaths(asset_data, tcom.passargs['resolution'])

            if len(file_paths) == 0:
                bk_logger.debug('library names not found in asset data after download')
                download_threads.remove(threaddata)
                break;

            wm = bpy.context.window_manager

            at = asset_data['assetType']
            if ((bpy.context.mode == 'OBJECT' and \
                 (at == 'model' or at == 'material'))) \
                    or ((at == 'brush') \
                        and wm.get('appendable') == True) or at == 'scene' or at == 'hdr':
                # don't do this stuff in editmode and other modes, just wait...
                download_threads.remove(threaddata)

                # duplicate file if the global and subdir are used in prefs
                if len(file_paths) == 2:  # todo this should try to check if both files exist and are ok.
                    utils.copy_asset(file_paths[0], file_paths[1])
                    # shutil.copyfile(file_paths[0], file_paths[1])

                bk_logger.debug('appending asset')
                # progress bars:

                # we need to check if mouse isn't down, which means an operator can be running.
                # Especially for sculpt mode, where appending a brush during a sculpt stroke causes crasehes
                #

                if tcom.passargs.get('redownload'):
                    # handle lost libraries here:
                    for l in bpy.data.libraries:
                        if l.get('asset_data') is not None and l['asset_data']['id'] == asset_data['id']:
                            l.filepath = file_paths[-1]
                            l.reload()

                if tcom.passargs.get('replace_resolution'):
                    # try to relink
                    # HDRs are always swapped, so their swapping is handled without the replace_resolution option

                    ain, resolution = asset_in_scene(asset_data)

                    if ain == 'LINKED':
                        replace_resolution_linked(file_paths, asset_data)


                    elif ain == 'APPENDED':
                        replace_resolution_appended(file_paths, asset_data, tcom.passargs['resolution'])



                else:
                    done = try_finished_append(asset_data, **tcom.passargs)
                    if not done:
                        at = asset_data['assetType']
                        tcom.passargs['retry_counter'] = tcom.passargs.get('retry_counter', 0) + 1
                        download(asset_data, **tcom.passargs)

                    if bpy.context.window_manager['search results'] is not None and done:
                        for sres in bpy.context.window_manager['search results']:
                            if asset_data['id'] == sres['id']:
                                sres['downloaded'] = 100

                bk_logger.debug('finished download thread')
    # utils.p('end download timer')

    return .5


def delete_unfinished_file(file_name):
    '''
    Deletes download if it wasn't finished. If the folder it's containing is empty, it also removes the directory
    Parameters
    ----------
    file_name

    Returns
    -------
    None
    '''
    try:
        os.remove(file_name)
    except Exception as e:
        print(e)
    asset_dir = os.path.dirname(file_name)
    if len(os.listdir(asset_dir)) == 0:
        os.rmdir(asset_dir)
    return


def download_asset_file(asset_data, resolution='blend', api_key = ''):
    # this is a simple non-threaded way to download files for background resolution genenration tool
    file_name = paths.get_download_filepaths(asset_data, resolution)[0]  # prefer global dir if possible.

    if check_existing(asset_data, resolution=resolution):
        # this sends the thread for processing, where another check should occur, since the file might be corrupted.
        bk_logger.debug('not downloading, already in db')
        return file_name

    download_canceled = False

    with open(file_name, "wb") as f:
        print("Downloading %s" % file_name)
        res_file_info, resolution = paths.get_res_file(asset_data, resolution)
        response = requests.get(res_file_info['url'], stream=True)
        total_length = response.headers.get('Content-Length')

        if total_length is None or int(total_length) < 1000:  # no content length header
            download_canceled = True
            print(response.content)
        else:
            total_length = int(total_length)
            dl = 0
            last_percent = 0
            percent = 0
            for data in response.iter_content(chunk_size=4096 * 10):
                dl += len(data)

                # the exact output you're looking for:
                fs_str = utils.files_size_to_text(total_length)

                percent = int(dl * 100 / total_length)
                if percent > last_percent:
                    last_percent = percent
                    # sys.stdout.write('\r')
                    # sys.stdout.write(f'Downloading {asset_data['name']} {fs_str} {percent}% ')  # + int(dl * 50 / total_length) * 'x')
                    print(
                        f'Downloading {asset_data["name"]} {fs_str} {percent}% ')  # + int(dl * 50 / total_length) * 'x')
                    # sys.stdout.flush()

                # print(int(dl*50/total_length)*'x'+'\r')
                f.write(data)
    if download_canceled:
        delete_unfinished_file(file_name)
        return None

    return file_name


class Downloader(threading.Thread):
    def __init__(self, asset_data, tcom, scene_id, api_key, resolution='blend'):
        super(Downloader, self).__init__()
        self.asset_data = asset_data
        self.tcom = tcom
        self.scene_id = scene_id
        self.api_key = api_key
        self.resolution = resolution
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    # def main_download_thread(asset_data, tcom, scene_id, api_key):
    def run(self):
        '''try to download file from blenderkit'''
        # utils.p('start downloader thread')
        asset_data = self.asset_data
        tcom = self.tcom
        scene_id = self.scene_id
        api_key = self.api_key
        tcom.report = 'Looking for asset'
        # TODO get real link here...
        has_url = get_download_url(asset_data, scene_id, api_key, resolution=self.resolution, tcom=tcom)

        if not has_url:
            tasks_queue.add_task(
                (ui.add_report, ('Failed to obtain download URL for %s.' % asset_data['name'], 5, colors.RED)))
            return;
        if tcom.error:
            return
        # only now we can check if the file already exists. This should have 2 levels, for materials and for brushes
        # different than for the non free content. delete is here when called after failed append tries.

        if check_existing(asset_data, resolution=self.resolution) and not tcom.passargs.get('delete'):
            # this sends the thread for processing, where another check should occur, since the file might be corrupted.
            tcom.downloaded = 100
            bk_logger.debug('not downloading, trying to append again')
            return

        file_name = paths.get_download_filepaths(asset_data, self.resolution)[0]  # prefer global dir if possible.
        # for k in asset_data:
        #    print(asset_data[k])
        if self.stopped():
            bk_logger.debug('stopping download: ' + asset_data['name'])
            return

        download_canceled = False
        with open(file_name, "wb") as f:
            bk_logger.debug("Downloading %s" % file_name)
            headers = utils.get_headers(api_key)
            res_file_info, self.resolution = paths.get_res_file(asset_data, self.resolution)
            response = requests.get(res_file_info['url'], stream=True)
            total_length = response.headers.get('Content-Length')
            if total_length is None:  # no content length header
                print('no content length')
                print(response.content)
                tcom.report = response.content
                download_canceled = True
            else:
                # bk_logger.debug(total_length)
                if int(total_length) < 1000:  # means probably no file returned.
                    tasks_queue.add_task((ui.add_report, (response.content, 20, colors.RED)))

                    tcom.report = response.content

                tcom.file_size = int(total_length)
                fsmb = tcom.file_size // (1024 * 1024)
                fskb = tcom.file_size % 1024
                if fsmb == 0:
                    t = '%iKB' % fskb
                else:
                    t = ' %iMB' % fsmb

                tcom.report = f'Downloading {t} {self.resolution}'

                dl = 0
                totdata = []
                for data in response.iter_content(chunk_size=4096 * 32):  # crashed here... why? investigate:
                    dl += len(data)
                    tcom.downloaded = dl
                    tcom.progress = int(100 * tcom.downloaded / tcom.file_size)
                    f.write(data)
                    if self.stopped():
                        bk_logger.debug('stopping download: ' + asset_data['name'])
                        download_canceled = True
                        break

        if download_canceled:
            delete_unfinished_file(file_name)
            return
        # unpack the file immediately after download

        tcom.report = f'Unpacking files'
        self.asset_data['resolution'] = self.resolution
        resolutions.send_to_bg(self.asset_data, file_name, command='unpack')
        # utils.p('end downloader thread')



class ThreadCom:  # object passed to threads to read background process stdout info
    def __init__(self):
        self.file_size = 1000000000000000  # property that gets written to.
        self.downloaded = 0
        self.lasttext = ''
        self.error = False
        self.report = ''
        self.progress = 0.0
        self.passargs = {}


def download(asset_data, **kwargs):
    '''start the download thread'''
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    scene_id = get_scene_id()

    tcom = ThreadCom()
    tcom.passargs = kwargs

    if kwargs.get('retry_counter', 0) > 3:
        sprops = utils.get_search_props()
        report = f"Maximum retries exceeded for {asset_data['name']}"
        sprops.report = report
        ui.add_report(report, 5, colors.RED)

        bk_logger.debug(sprops.report)
        return

    # incoming data can be either directly dict from python, or blender id property
    # (recovering failed downloads on reload)
    if type(asset_data) == dict:
        asset_data = copy.deepcopy(asset_data)
    else:
        asset_data = asset_data.to_dict()
    readthread = Downloader(asset_data, tcom, scene_id, api_key, resolution=kwargs['resolution'])
    readthread.start()

    global download_threads
    download_threads.append(
        [readthread, asset_data, tcom])


def check_downloading(asset_data, **kwargs):
    ''' check if an asset is already downloading, if yes, just make a progress bar with downloader object.'''
    global download_threads

    downloading = False

    for p in download_threads:
        p_asset_data = p[1]
        if p_asset_data['id'] == asset_data['id']:
            at = asset_data['assetType']
            if at in ('model', 'material'):
                downloader = {'location': kwargs['model_location'],
                              'rotation': kwargs['model_rotation']}
                p[2].passargs['downloaders'].append(downloader)
            downloading = True

    return downloading


def check_existing(asset_data, resolution='blend', can_return_others=False):
    ''' check if the object exists on the hard drive'''
    fexists = False

    if asset_data.get('files') == None:
        # this is because of some very odl files where asset data had no files structure.
        return False

    file_names = paths.get_download_filepaths(asset_data, resolution, can_return_others=can_return_others)

    bk_logger.debug('check if file already exists' + str(file_names))
    if len(file_names) == 2:
        # TODO this should check also for failed or running downloads.
        # If download is running, assign just the running thread. if download isn't running but the file is wrong size,
        #  delete file and restart download (or continue downoad? if possible.)
        if os.path.isfile(file_names[0]):  # and not os.path.isfile(file_names[1])
            utils.copy_asset(file_names[0], file_names[1])
        elif not os.path.isfile(file_names[0]) and os.path.isfile(
                file_names[1]):  # only in case of changed settings or deleted/moved global dict.
            utils.copy_asset(file_names[1], file_names[0])

    if len(file_names) > 0 and os.path.isfile(file_names[0]):
        fexists = True
    return fexists


def try_finished_append(asset_data, **kwargs):  # location=None, material_target=None):
    ''' try to append asset, if not successfully delete source files.
     This means probably wrong download, so download should restart'''
    file_names = paths.get_download_filepaths(asset_data, kwargs['resolution'])
    done = False
    bk_logger.debug('try to append already existing asset')
    if len(file_names) > 0:
        if os.path.isfile(file_names[-1]):
            kwargs['name'] = asset_data['name']
            try:
                append_asset(asset_data, **kwargs)
                done = True
            except Exception as e:
                # TODO: this should distinguis if the appending failed (wrong file)
                # or something else happened(shouldn't delete the files)
                print(e)
                done = False
                for f in file_names:
                    try:
                        os.remove(f)
                    except Exception as e:
                        # e = sys.exc_info()[0]
                        print(e)
                        pass;
                return done

    return done


def get_asset_in_scene(asset_data):
    '''tries to find an appended copy of particular asset and duplicate it - so it doesn't have to be appended again.'''
    scene = bpy.context.scene
    for ob in bpy.context.scene.objects:
        ad1 = ob.get('asset_data')
        if not ad1:
            continue
        if ad1.get('assetBaseId') == asset_data['assetBaseId']:
            return ob
    return None


def check_all_visible(obs):
    '''checks all objects are visible, so they can be manipulated/copied.'''
    for ob in obs:
        if not ob.visible_get():
            return False
    return True


def check_selectible(obs):
    '''checks if all objects can be selected and selects them if possible.
     this isn't only select_hide, but all possible combinations of collections e.t.c. so hard to check otherwise.'''
    for ob in obs:
        ob.select_set(True)
        if not ob.select_get():
            return False
    return True


def duplicate_asset(source, **kwargs):
    '''
    Duplicate asset when it's already appended in the scene,
    so that blender's append doesn't create duplicated data.
     '''
    bk_logger.debug('duplicate asset instead')
    # we need to save selection
    sel = utils.selection_get()
    bpy.ops.object.select_all(action='DESELECT')

    # check visibility
    obs = utils.get_hierarchy(source)
    if not check_all_visible(obs):
        return None
    # check selectability and select in one run
    if not check_selectible(obs):
        return None

    # duplicate the asset objects
    bpy.ops.object.duplicate(linked=True)

    nobs = bpy.context.selected_objects[:]
    # get asset main object
    for ob in nobs:
        if ob.parent not in nobs:
            asset_main = ob
            break

    # in case of replacement,there might be a paarent relationship that can be restored
    if kwargs.get('parent'):
        parent = bpy.data.objects[kwargs['parent']]
        asset_main.parent = parent  # even if parent is None this is ok without if condition
    else:
        asset_main.parent = None
    # restore original selection
    utils.selection_set(sel)
    return asset_main, nobs


def asset_in_scene(asset_data):
    '''checks if the asset is already in scene. If yes, modifies asset data so the asset can be reached again.'''
    scene = bpy.context.scene
    au = scene.get('assets used', {})

    id = asset_data['assetBaseId']
    if id in au.keys():
        ad = au[id]
        if ad.get('files'):
            for fi in ad['files']:
                if fi.get('file_name') != None:

                    for fi1 in asset_data['files']:
                        if fi['fileType'] == fi1['fileType']:
                            fi1['file_name'] = fi['file_name']
                            fi1['url'] = fi['url']

                            # browse all collections since linked collections can have same name.
                            if asset_data['assetType'] == 'MODEL':
                                for c in bpy.data.collections:
                                    if c.name == ad['name']:
                                        # there can also be more linked collections with same name, we need to check id.
                                        if c.library and c.library.get('asset_data') and c.library['asset_data'][
                                            'assetBaseId'] == id:
                                            print('asset linked')
                                            return 'LINKED', ad.get('resolution')
                            elif asset_data['assetType'] == 'MATERIAL':
                                for m in bpy.data.materials:
                                    if not m.get('asset_data'):
                                        continue
                                    if m['asset_data']['assetBaseId'] == asset_data[
                                        'assetBaseId'] and bpy.context.active_object.active_material.library:
                                        return 'LINKED', ad.get('resolution')

                            print('asset appended')
                            return 'APPENDED', ad.get('resolution')
    return False, None


def fprint(text):
    print('###################################################################################')
    print('\n\n\n')
    print(text)
    print('\n\n\n')
    print('###################################################################################')


def get_download_url(asset_data, scene_id, api_key, tcom=None, resolution='blend'):
    ''''retrieves the download url. The server checks if user can download the item.'''
    mt = time.time()
    utils.pprint('getting download url')

    headers = utils.get_headers(api_key)

    data = {
        'scene_uuid': scene_id
    }
    r = None

    res_file_info, resolution = paths.get_res_file(asset_data, resolution)

    try:
        r = rerequests.get(res_file_info['downloadUrl'], params=data, headers=headers)
    except Exception as e:
        print(e)
        if tcom is not None:
            tcom.error = True
    if r == None:
        if tcom is not None:
            tcom.report = 'Connection Error'
            tcom.error = True
        return 'Connection Error'

    if r.status_code < 400:
        data = r.json()
        url = data['filePath']

        res_file_info['url'] = url
        res_file_info['file_name'] = paths.extract_filename_from_url(url)

        # print(res_file_info, url)
        print(url)
        return True

    # let's print it into UI
    tasks_queue.add_task((ui.add_report, (str(r), 10, colors.RED)))

    if r.status_code == 403:
        report = 'You need Full plan to get this item.'
        # r1 = 'All materials and brushes are available for free. Only users registered to Standard plan can use all models.'
        # tasks_queue.add_task((ui.add_report, (r1, 5, colors.RED)))
        if tcom is not None:
            tcom.report = report
            tcom.error = True

    if r.status_code == 404:
        report = 'Url not found - 404.'
        # r1 = 'All materials and brushes are available for free. Only users registered to Standard plan can use all models.'
        if tcom is not None:
            tcom.report = report
            tcom.error = True

    elif r.status_code >= 500:
        # bk_logger.debug(r.text)
        if tcom is not None:
            tcom.report = 'Server error'
            tcom.error = True
    return False


def start_download(asset_data, **kwargs):
    '''
    check if file isn't downloading or doesn't exist, then start new download
    '''
    # first check if the asset is already in scene. We can use that asset without checking with server
    ain, resolution = asset_in_scene(asset_data)
    # quota_ok = ain is not False

    # if resolution:
    #     kwargs['resolution'] = resolution
    # otherwise, check on server

    s = bpy.context.scene
    done = False
    # is the asseet being currently downloaded?
    downloading = check_downloading(asset_data, **kwargs)
    if not downloading:
        # check if there are files already. This check happens 2x once here(for free assets),
        # once in thread(for non-free)
        fexists = check_existing(asset_data, resolution=kwargs['resolution'])
        bk_logger.debug('does file exist?' + str(fexists))
        bk_logger.debug('asset is in scene' + str(ain))
        if ain and not kwargs.get('replace_resolution'):
            # this goes to appending asset - where it should duplicate the original asset already in scene.
            done = try_finished_append(asset_data, **kwargs)
        # else:
        #     props = utils.get_search_props()
        #     props.report = str('asset ')
        if not done:
            at = asset_data['assetType']
            if at in ('model', 'material'):
                downloader = {'location': kwargs['model_location'],
                              'rotation': kwargs['model_rotation']}
                download(asset_data, downloaders=[downloader], **kwargs)

            else:
                download(asset_data, **kwargs)


asset_types = (
    ('MODEL', 'Model', 'set of objects'),
    ('SCENE', 'Scene', 'scene'),
    ('HDR', 'Hdr', 'hdr'),
    ('MATERIAL', 'Material', 'any .blend Material'),
    ('TEXTURE', 'Texture', 'a texture, or texture set'),
    ('BRUSH', 'Brush', 'brush, can be any type of blender brush'),
    ('ADDON', 'Addon', 'addnon'),
)


class BlenderkitKillDownloadOperator(bpy.types.Operator):
    """Kill a download"""
    bl_idname = "scene.blenderkit_download_kill"
    bl_label = "BlenderKit Kill Asset Download"
    bl_options = {'REGISTER', 'INTERNAL'}

    thread_index: IntProperty(name="Thread index", description='index of the thread to kill', default=-1)

    def execute(self, context):
        global download_threads
        td = download_threads[self.thread_index]
        download_threads.remove(td)
        td[0].stop()
        return {'FINISHED'}


def available_resolutions_callback(self, context):
    '''
    Returns
    checks active asset for available resolutions and offers only those available
    TODO: this currently returns always the same list of resolutions, make it actually work
    '''
    # print('callback called', self.asset_data)
    pat_items = (
        ('512', '512', '', 1),
        ('1024', '1024', '', 2),
        ('2048', '2048', '', 3),
        ('4096', '4096', '', 4),
        ('8192', '8192', '', 5),
    )
    items = []
    for item in pat_items:
        if int(self.max_resolution) >= int(item[0]):
            items.append(item)
    items.append(('ORIGINAL', 'Original', '', 6))
    return items


def show_enum_values(obj, prop_name):
    print([item.identifier for item in obj.bl_rna.properties[prop_name].enum_items])


class BlenderkitDownloadOperator(bpy.types.Operator):
    """Download and link asset to scene. Only link if asset already available locally"""
    bl_idname = "scene.blenderkit_download"
    bl_label = "Download"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    # asset_type: EnumProperty(
    #     name="Type",
    #     items=asset_types,
    #     description="Type of download",
    #     default="MODEL",
    # )
    asset_index: IntProperty(name="Asset Index", description='asset index in search results', default=-1)

    asset_base_id: StringProperty(
        name="Asset base Id",
        description="Asset base id, used instead of search result index",
        default="")

    target_object: StringProperty(
        name="Target Object",
        description="Material or object target for replacement",
        default="")

    material_target_slot: IntProperty(name="Asset Index", description='asset index in search results', default=0)
    model_location: FloatVectorProperty(name='Asset Location', default=(0, 0, 0))
    model_rotation: FloatVectorProperty(name='Asset Rotation', default=(0, 0, 0))

    replace: BoolProperty(name='Replace', description='replace selection with the asset', default=False)

    replace_resolution: BoolProperty(name='Replace resolution', description='replace resolution of the active asset',
                                     default=False)

    invoke_resolution: BoolProperty(name='Replace resolution popup',
                                    description='pop up to ask which resolution to download', default=False)
    invoke_scene_settings: BoolProperty(name='Scene import settings popup',
                                    description='pop up scene import settings', default=False)

    resolution: EnumProperty(
        items=available_resolutions_callback,
        default=0,
        description='Replace resolution'
    )

    #needs to be passed to the operator to not show all resolution possibilities
    max_resolution: IntProperty(
        name="Max resolution",
        description="",
        default=0)
    # has_res_0_5k: BoolProperty(name='512',
    #                                 description='', default=False)

    cast_parent: StringProperty(
        name="Particles Target Object",
        description="",
        default="")

    # close_window: BoolProperty(name='Close window',
    #                            description='Try to close the window below mouse before download',
    #                            default=False)
    # @classmethod
    # def poll(cls, context):
    #     return bpy.context.window_manager.BlenderKitModelThumbnails is not ''
    def get_asset_data(self, context):
        # get asset data - it can come from scene, or from search results.
        s = bpy.context.scene

        if self.asset_index > -1:
            # either get the data from search results
            sr = bpy.context.window_manager['search results']
            asset_data = sr[
                self.asset_index].to_dict()  # TODO CHECK ALL OCCURRENCES OF PASSING BLENDER ID PROPS TO THREADS!
            asset_base_id = asset_data['assetBaseId']
        else:
            # or from the scene.
            asset_base_id = self.asset_base_id

        au = s.get('assets used')
        if au == None:
            s['assets used'] = {}
        if asset_base_id in s.get('assets used'):
            # already used assets have already download link and especially file link.
            asset_data = s['assets used'][asset_base_id].to_dict()
        return asset_data

    def execute(self, context):
        sprops = utils.get_search_props()

        self.asset_data = self.get_asset_data(context)

        # print('after getting asset data')
        # print(self.asset_base_id)

        atype = self.asset_data['assetType']
        if bpy.context.mode != 'OBJECT' and (
                atype == 'model' or atype == 'material') and bpy.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.resolution == 0 or self.resolution == '':
            resolution = sprops.resolution
        else:
            resolution = self.resolution

        resolution = resolutions.resolution_props_to_server[resolution]
        if self.replace:  # cleanup first, assign later.
            obs = utils.get_selected_replace_adepts()
            # print(obs)
            for ob in obs:
                # print('replace attempt ', ob.name)
                if self.asset_base_id != '':
                    # this is for a case when replace is called from a panel,
                    # this uses active object as replacement source instead of target.
                    if ob.get('asset_data') is not None and \
                            (ob['asset_data']['assetBaseId'] == self.asset_base_id and ob['asset_data'][
                                'resolution'] == resolution):
                        # print('skipping this one')
                        continue;
                parent = ob.parent
                if parent:
                    parent = ob.parent.name  # after this, parent is either name or None.

                kwargs = {
                    'cast_parent': self.cast_parent,
                    'target_object': ob.name,
                    'material_target_slot': ob.active_material_index,
                    'model_location': tuple(ob.matrix_world.translation),
                    'model_rotation': tuple(ob.matrix_world.to_euler()),
                    'replace': True,
                    'replace_resolution': False,
                    'parent': parent,
                    'resolution': resolution
                }
                # TODO - move this After download, not before, so that the replacement
                utils.delete_hierarchy(ob)
                start_download(self.asset_data, **kwargs)
        else:
            # replace resolution needs to replace all instances of the resolution in the scene
            # and deleting originals has to be thus done after the downlaod

            kwargs = {
                'cast_parent': self.cast_parent,
                'target_object': self.target_object,
                'material_target_slot': self.material_target_slot,
                'model_location': tuple(self.model_location),
                'model_rotation': tuple(self.model_rotation),
                'replace': False,
                'replace_resolution': self.replace_resolution,
                'resolution': resolution
            }

            start_download(self.asset_data, **kwargs)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        if self.invoke_resolution:
            layout.prop(self, 'resolution', expand=True, icon_only=False)
        if self.invoke_scene_settings:
            ui_panels.draw_scene_import_settings(self, context)

    def invoke(self, context, event):
        # if self.close_window:
        #     context.window.cursor_warp(event.mouse_x-1000, event.mouse_y - 1000);

        print(self.asset_base_id)
        wm = context.window_manager
        # only make a pop up in case of switching resolutions
        if self.invoke_resolution:
            # show_enum_values(self, 'resolution')
            self.asset_data = self.get_asset_data(context)
            sprops = utils.get_search_props()

            #set initial resolutions enum activation
            if sprops.resolution != 'ORIGINAL' and int(sprops.resolution) <= int(self.max_resolution):
                self.resolution = sprops.resolution
            elif int(self.max_resolution) > 0:
                self.resolution = str(self.max_resolution)
            else:
                self.resolution = 'ORIGINAL'
            return wm.invoke_props_dialog(self)

        if self.invoke_scene_settings:
            return wm.invoke_props_dialog(self)
        # if self.close_window:
        #     time.sleep(0.1)
        #     context.area.tag_redraw()
        #     time.sleep(0.1)
        #
        #     context.window.cursor_warp(event.mouse_x, event.mouse_y);

        return self.execute(context)


def register_download():
    bpy.utils.register_class(BlenderkitDownloadOperator)
    bpy.utils.register_class(BlenderkitKillDownloadOperator)
    bpy.app.handlers.load_post.append(scene_load)
    bpy.app.handlers.save_pre.append(scene_save)
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.use_timers:
        bpy.app.timers.register(download_timer)


def unregister_download():
    bpy.utils.unregister_class(BlenderkitDownloadOperator)
    bpy.utils.unregister_class(BlenderkitKillDownloadOperator)
    bpy.app.handlers.load_post.remove(scene_load)
    bpy.app.handlers.save_pre.remove(scene_save)
    if bpy.app.timers.is_registered(download_timer):
        bpy.app.timers.unregister(download_timer)
