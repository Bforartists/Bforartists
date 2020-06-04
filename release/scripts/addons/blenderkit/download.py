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
    append_link = reload(append_link)
    utils = reload(utils)
    ui = reload(ui)
    colors = reload(colors)
    tasks_queue = reload(tasks_queue)
    rerequests = reload(rerequests)
else:
    from blenderkit import paths, append_link, utils, ui, colors, tasks_queue, rerequests

import threading
import time
import requests
import shutil, sys, os
import uuid
import copy

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
        downloaded = check_existing(asset_data)
        if downloaded:
            try:
                l.reload()
            except:
                download(l['asset_data'], redownload=True)
        else:
            download(l['asset_data'], redownload=True)


def check_unused():
    '''find assets that have been deleted from scene but their library is still present.'''

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
        if l not in used_libs:
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
    #     if check_existing(asset_data):
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
        abid = asset_data['asset_base_id']

        if assets.get(abid) is None:
            asset_usages[abid] = {'count': 1}
            assets[abid] = asset_data
        else:
            asset_usages[abid]['count'] += 1

    # brushes
    for b in bpy.data.brushes:
        if b.get('asset_data') != None:
            abid = b['asset_data']['asset_base_id']
            asset_usages[abid] = {'count': 1}
            assets[abid] = b['asset_data']
    # materials
    for ob in scene.collection.objects:
        for ms in ob.material_slots:
            m = ms.material

            if m is not None and m.get('asset_data') is not None:

                abid = m['asset_data']['asset_base_id']
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
        utils.p('no new assets were added')
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
    print('report generation:                ', mt)


def append_asset(asset_data, **kwargs):  # downloaders=[], location=None,
    '''Link asset to the scene'''

    file_names = paths.get_download_filenames(asset_data)
    props = None
    #####
    # how to do particle  drop:
    # link the group we are interested in( there are more groups in File!!!! , have to get the correct one!)
    #
    scene = bpy.context.scene


    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    if user_preferences.api_key == '':
        user_preferences.asset_counter += 1

    if asset_data['asset_type'] == 'scene':
        scene = append_link.append_scene(file_names[0], link=False, fake_user=False)
        props = scene.blenderkit
        parent = scene

    if asset_data['asset_type'] == 'model':
        s = bpy.context.scene
        downloaders = kwargs.get('downloaders')
        s = bpy.context.scene
        sprops = s.blenderkit_models
        # TODO this is here because combinations of linking objects or appending groups are rather not-usefull
        if sprops.append_method == 'LINK_COLLECTION':
            sprops.append_link = 'LINK'
            sprops.import_as = 'GROUP'
        else:
            sprops.append_link = 'APPEND'
            sprops.import_as = 'INDIVIDUAL'

        #copy for override
        al = sprops.append_link
        import_as = sprops.import_as
        # set consistency for objects already in scene, otherwise this literally breaks blender :)
        ain = asset_in_scene(asset_data)
        #override based on history
        if ain is not False:
            if ain == 'LINKED':
                al = 'LINK'
                import_as = 'GROUP'
            else:
                al = 'APPEND'
                import_as = 'INDIVIDUAL'


        # first get conditions for append link
        link = al == 'LINK'
        # then append link
        if downloaders:
            for downloader in downloaders:
                # this cares for adding particle systems directly to target mesh, but I had to block it now,
                # because of the sluggishnes of it. Possibly re-enable when it's possible to do this faster?
                if 0:  # 'particle_plants' in asset_data['tags']:
                    append_link.append_particle_system(file_names[-1],
                                                       target_object=kwargs['target_object'],
                                                       rotation=downloader['rotation'],
                                                       link=False,
                                                       name=asset_data['name'])
                    return

                if sprops.import_as == 'GROUP':
                    parent, newobs = append_link.link_collection(file_names[-1],
                                                            location=downloader['location'],
                                                            rotation=downloader['rotation'],
                                                            link=link,
                                                            name=asset_data['name'],
                                                            parent=kwargs.get('parent'))

                else:
                    parent, newobs = append_link.append_objects(file_names[-1],
                                                                location=downloader['location'],
                                                                rotation=downloader['rotation'],
                                                                link=link,
                                                                name=asset_data['name'],
                                                                parent=kwargs.get('parent'))
                if parent.type == 'EMPTY' and link:
                    bmin = asset_data['bbox_min']
                    bmax = asset_data['bbox_max']
                    size_min = min(1.0, (bmax[0] - bmin[0] + bmax[1] - bmin[1] + bmax[2] - bmin[2]) / 3)
                    parent.empty_display_size = size_min

        elif kwargs.get('model_location') is not None:
            if sprops.import_as == 'GROUP':
                parent, newobs = append_link.link_collection(file_names[-1],
                                                        location=kwargs['model_location'],
                                                        rotation=kwargs['model_rotation'],
                                                        link=link,
                                                        name=asset_data['name'],
                                                        parent=kwargs.get('parent'))
            else:
                parent, newobs = append_link.append_objects(file_names[-1],
                                                            location=kwargs['model_location'],
                                                            rotation=kwargs['model_rotation'],
                                                            link=link,
                                                            parent=kwargs.get('parent'))
            if parent.type == 'EMPTY' and link:
                bmin = asset_data['bbox_min']
                bmax = asset_data['bbox_max']
                size_min = min(1.0, (bmax[0] - bmin[0] + bmax[1] - bmin[1] + bmax[2] - bmin[2]) / 3)
                parent.empty_display_size = size_min

        if link:
            group = parent.instance_collection

            lib = group.library
            lib['asset_data'] = asset_data

    elif asset_data['asset_type'] == 'brush':

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
        parent = brush

    elif asset_data['asset_type'] == 'material':
        inscene = False
        for m in bpy.data.materials:
            if m.blenderkit.id == asset_data['id']:
                inscene = True
                material = m
                break;
        if not inscene:
            material = append_link.append_material(file_names[-1], link=False, fake_user=False)
        target_object = bpy.data.objects[kwargs['target_object']]

        if len(target_object.material_slots) == 0:
            target_object.data.materials.append(material)
        else:
            target_object.material_slots[kwargs['material_target_slot']].material = material

        parent = material

    scene['assets used'] = scene.get('assets used', {})
    scene['assets used'][asset_data['asset_base_id']] = asset_data.copy()

    scene['assets rated'] = scene.get('assets rated', {})

    id = asset_data['asset_base_id']
    scene['assets rated'][id] = scene['assets rated'].get(id, False)

    parent['asset_data'] = asset_data  # TODO remove this??? should write to blenderkit Props?
    bpy.ops.wm.undo_push_context(message = 'add %s to scene'% asset_data['name'])
    # moving reporting to on save.
    # report_use_success(asset_data['id'])


# @bpy.app.handlers.persistent
def timer_update():  # TODO might get moved to handle all blenderkit stuff, not to slow down.
    '''check for running and finished downloads and react. write progressbars too.'''
    global download_threads
    if len(download_threads) == 0:
        return 1.0
    s = bpy.context.scene
    for threaddata in download_threads:
        t = threaddata[0]
        asset_data = threaddata[1]
        tcom = threaddata[2]

        progress_bars = []
        downloaders = []

        if t.is_alive():  # set downloader size
            sr = bpy.context.scene.get('search results')
            if sr is not None:
                for r in sr:
                    if asset_data['id'] == r['id']:
                        r['downloaded'] = tcom.progress

        if not t.is_alive():
            if tcom.error:
                sprops = utils.get_search_props()
                sprops.report = tcom.report
                download_threads.remove(threaddata)
                return
            file_names = paths.get_download_filenames(asset_data)
            wm = bpy.context.window_manager

            at = asset_data['asset_type']
            if ((bpy.context.mode == 'OBJECT' and (at == 'model' \
                                                   or at == 'material'))) \
                    or ((at == 'brush') \
                        and wm.get(
                        'appendable') == True) or at == 'scene':  # don't do this stuff in editmode and other modes, just wait...
                download_threads.remove(threaddata)

                # duplicate file if the global and subdir are used in prefs
                if len(file_names) == 2:  # todo this should try to check if both files exist and are ok.
                    shutil.copyfile(file_names[0], file_names[1])

                utils.p('appending asset')
                # progress bars:

                # we need to check if mouse isn't down, which means an operator can be running.
                # Especially for sculpt mode, where appending a brush during a sculpt stroke causes crasehes
                #

                if tcom.passargs.get('redownload'):
                    # handle lost libraries here:
                    for l in bpy.data.libraries:
                        if l.get('asset_data') is not None and l['asset_data']['id'] == asset_data['id']:
                            l.filepath = file_names[-1]
                            l.reload()
                else:
                    done = try_finished_append(asset_data, **tcom.passargs)
                    if not done:
                        at = asset_data['asset_type']
                        tcom.passargs['retry_counter'] = tcom.passargs.get('retry_counter', 0) + 1
                        if at in ('model', 'material'):
                            download(asset_data, **tcom.passargs)
                        elif asset_data['asset_type'] == 'material':
                            download(asset_data, **tcom.passargs)
                        elif asset_data['asset_type'] == 'scene':
                            download(asset_data, **tcom.passargs)
                        elif asset_data['asset_type'] == 'brush' or asset_data['asset_type'] == 'texture':
                            download(asset_data, **tcom.passargs)
                    if bpy.context.scene['search results'] is not None and done:
                        for sres in bpy.context.scene['search results']:
                            if asset_data['id'] == sres['id']:
                                sres['downloaded'] = 100

                utils.p('finished download thread')
    return .5


def download_file(asset_data):
    #this is a simple non-threaded way to download files for background resolution genenration tool
    file_name = paths.get_download_filenames(asset_data)[0]  # prefer global dir if possible.

    if check_existing(asset_data):
        # this sends the thread for processing, where another check should occur, since the file might be corrupted.
        utils.p('not downloading, already in db')
        return file_name
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = preferences.api_key

    with open(file_name, "wb") as f:
        print("Downloading %s" % file_name)
        headers = utils.get_headers(api_key)

        response = requests.get(asset_data['url'], stream=True)
        total_length = response.headers.get('Content-Length')

        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                print(dl)
                f.write(data)
    return file_name

class Downloader(threading.Thread):
    def __init__(self, asset_data, tcom, scene_id, api_key):
        super(Downloader, self).__init__()
        self.asset_data = asset_data
        self.tcom = tcom
        self.scene_id = scene_id
        self.api_key = api_key
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    # def main_download_thread(asset_data, tcom, scene_id, api_key):
    def run(self):
        '''try to download file from blenderkit'''
        asset_data = self.asset_data
        tcom = self.tcom
        scene_id = self.scene_id
        api_key = self.api_key

        # TODO get real link here...
        has_url = get_download_url(asset_data, scene_id, api_key, tcom=tcom)

        if not has_url:
            tasks_queue.add_task(
                (ui.add_report, ('Failed to obtain download URL for %s.' % asset_data['name'], 5, colors.RED)))
            return;
        if tcom.error:
            return
        # only now we can check if the file already exists. This should have 2 levels, for materials and for brushes
        # different than for the non free content. delete is here when called after failed append tries.
        if check_existing(asset_data) and not tcom.passargs.get('delete'):
            # this sends the thread for processing, where another check should occur, since the file might be corrupted.
            tcom.downloaded = 100
            utils.p('not downloading, trying to append again')
            return;

        file_name = paths.get_download_filenames(asset_data)[0]  # prefer global dir if possible.
        # for k in asset_data:
        #    print(asset_data[k])
        if self.stopped():
            utils.p('stopping download: ' + asset_data['name'])
            return;

        with open(file_name, "wb") as f:
            print("Downloading %s" % file_name)
            headers = utils.get_headers(api_key)

            response = requests.get(asset_data['url'], stream=True)
            total_length = response.headers.get('Content-Length')

            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                tcom.file_size = int(total_length)
                dl = 0
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    tcom.downloaded = dl
                    tcom.progress = int(100 * tcom.downloaded / tcom.file_size)
                    f.write(data)
                    if self.stopped():
                        utils.p('stopping download: ' + asset_data['name'])
                        f.close()
                        os.remove(file_name)
                        return;


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

        utils.p(sprops.report)
        return

    # incoming data can be either directly dict from python, or blender id property
    # (recovering failed downloads on reload)
    if type(asset_data) == dict:
        asset_data = copy.deepcopy(asset_data)
    else:
        asset_data = asset_data.to_dict()
    readthread = Downloader(asset_data, tcom, scene_id, api_key)
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
            at = asset_data['asset_type']
            if at in ('model', 'material'):
                downloader = {'location': kwargs['model_location'],
                              'rotation': kwargs['model_rotation']}
                p[2].passargs['downloaders'].append(downloader)
            downloading = True

    return downloading


def check_existing(asset_data):
    ''' check if the object exists on the hard drive'''
    fexists = False

    file_names = paths.get_download_filenames(asset_data)

    utils.p('check if file already exists')
    if len(file_names) == 2:
        # TODO this should check also for failed or running downloads.
        # If download is running, assign just the running thread. if download isn't running but the file is wrong size,
        #  delete file and restart download (or continue downoad? if possible.)
        if os.path.isfile(file_names[0]) and not os.path.isfile(file_names[1]):
            shutil.copy(file_names[0], file_names[1])
        elif not os.path.isfile(file_names[0]) and os.path.isfile(
                file_names[1]):  # only in case of changed settings or deleted/moved global dict.
            shutil.copy(file_names[1], file_names[0])

    if len(file_names) > 0 and os.path.isfile(file_names[0]):
        fexists = True
    return fexists


def try_finished_append(asset_data, **kwargs):  # location=None, material_target=None):
    ''' try to append asset, if not successfully delete source files.
     This means probably wrong download, so download should restart'''
    file_names = paths.get_download_filenames(asset_data)
    done = False
    utils.p('try to append already existing asset')
    if len(file_names) > 0:
        if os.path.isfile(file_names[-1]):
            kwargs['name'] = asset_data['name']
            try:
                append_asset(asset_data, **kwargs)
                done = True
            except Exception as e:
                print(e)
                for f in file_names:
                    try:
                        os.remove(f)
                    except:
                        e = sys.exc_info()[0]
                        print(e)
                        pass;
                done = False
    return done


def asset_in_scene(asset_data):
    '''checks if the asset is already in scene. If yes, modifies asset data so the asset can be reached again.'''
    scene = bpy.context.scene
    au = scene.get('assets used', {})

    id = asset_data['asset_base_id']
    if id in au.keys():
        ad = au[id]
        if ad.get('file_name') != None:

            asset_data['file_name'] = ad['file_name']
            asset_data['url'] = ad['url']

            c = bpy.data.collections.get(ad['name'])
            if c is not None:
                if c.users > 0:
                    return 'LINKED'
            return 'APPENDED'
    return False


def fprint(text):
    print('###################################################################################')
    print('\n\n\n')
    print(text)
    print('\n\n\n')
    print('###################################################################################')


def get_download_url(asset_data, scene_id, api_key, tcom=None):
    ''''retrieves the download url. The server checks if user can download the item.'''
    mt = time.time()

    headers = utils.get_headers(api_key)

    data = {
        'scene_uuid': scene_id
    }
    r = None

    try:
        r = rerequests.get(asset_data['download_url'], params=data, headers=headers)
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
        asset_data['url'] = url
        asset_data['file_name'] = paths.extract_filename_from_url(url)
        return True

    if r.status_code == 403:
        r = 'You need Full plan to get this item.'
        # r1 = 'All materials and brushes are available for free. Only users registered to Standard plan can use all models.'
        # tasks_queue.add_task((ui.add_report, (r1, 5, colors.RED)))
        if tcom is not None:
            tcom.report = r
            tcom.error = True

    elif r.status_code >= 500:
        utils.p(r.text)
        if tcom is not None:
            tcom.report = 'Server error'
            tcom.error = True
    return False


def start_download(asset_data, **kwargs):
    '''
    check if file isn't downloading or doesn't exist, then start new download
    '''
    # first check if the asset is already in scene. We can use that asset without checking with server
    quota_ok = asset_in_scene(asset_data) is not False

    # otherwise, check on server

    s = bpy.context.scene
    done = False
    # is the asseet being currently downloaded?
    downloading = check_downloading(asset_data, **kwargs)
    if not downloading:
        # check if there are files already. This check happens 2x once here(for free assets),
        # once in thread(for non-free)
        fexists = check_existing(asset_data)

        if fexists and quota_ok:
            done = try_finished_append(asset_data, **kwargs)
        # else:
        #     props = utils.get_search_props()
        #     props.report = str('asset ')
        if not done:
            at = asset_data['asset_type']
            if at in ('model', 'material'):
                downloader = {'location': kwargs['model_location'],
                              'rotation': kwargs['model_rotation']}
                download(asset_data, downloaders=[downloader], **kwargs)

            elif asset_data['asset_type'] == 'scene':
                download(asset_data, **kwargs)
            elif asset_data['asset_type'] == 'brush' or asset_data['asset_type'] == 'texture':
                download(asset_data)


asset_types = (
    ('MODEL', 'Model', 'set of objects'),
    ('SCENE', 'Scene', 'scene'),
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


class BlenderkitDownloadOperator(bpy.types.Operator):
    """Download and link asset to scene. Only link if asset already available locally."""
    bl_idname = "scene.blenderkit_download"
    bl_label = "BlenderKit Asset Download"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    asset_type: EnumProperty(
        name="Type",
        items=asset_types,
        description="Type of download",
        default="MODEL",
    )
    asset_index: IntProperty(name="Asset Index", description='asset index in search results', default=-1)

    target_object: StringProperty(
        name="Target Object",
        description="Material or object target for replacement",
        default="")

    material_target_slot: IntProperty(name="Asset Index", description='asset index in search results', default=0)
    model_location: FloatVectorProperty(name='Asset Location', default=(0, 0, 0))
    model_rotation: FloatVectorProperty(name='Asset Rotation', default=(0, 0, 0))

    replace: BoolProperty(name='Replace', description='replace selection with the asset', default=False)

    cast_parent: StringProperty(
        name="Particles Target Object",
        description="",
        default="")

    # @classmethod
    # def poll(cls, context):
    #     return bpy.context.window_manager.BlenderKitModelThumbnails is not ''

    def execute(self, context):
        s = bpy.context.scene
        sr = s['search results']

        asset_data = sr[self.asset_index].to_dict()  # TODO CHECK ALL OCCURRENCES OF PASSING BLENDER ID PROPS TO THREADS!
        au = s.get('assets used')
        if au == None:
            s['assets used'] = {}
        if asset_data['asset_base_id'] in s.get('assets used'):
            asset_data = s['assets used'][asset_data['asset_base_id']].to_dict()

        atype = asset_data['asset_type']
        if bpy.context.mode != 'OBJECT' and (
                atype == 'model' or atype == 'material') and bpy.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.replace:  # cleanup first, assign later.
            obs = utils.get_selected_models()

            for ob in obs:
                kwargs = {
                    'cast_parent': self.cast_parent,
                    'target_object': ob.name,
                    'material_target_slot': ob.active_material_index,
                    'model_location': tuple(ob.matrix_world.translation),
                    'model_rotation': tuple(ob.matrix_world.to_euler()),
                    'replace': False,
                    'parent': ob.parent
                }
                utils.delete_hierarchy(ob)
                start_download(asset_data, **kwargs)
        else:
            kwargs = {
                'cast_parent': self.cast_parent,
                'target_object': self.target_object,
                'material_target_slot': self.material_target_slot,
                'model_location': tuple(self.model_location),
                'model_rotation': tuple(self.model_rotation),
                'replace': False
            }

            start_download(asset_data, **kwargs)
        return {'FINISHED'}


def register_download():
    bpy.utils.register_class(BlenderkitDownloadOperator)
    bpy.utils.register_class(BlenderkitKillDownloadOperator)
    bpy.app.handlers.load_post.append(scene_load)
    bpy.app.handlers.save_pre.append(scene_save)
    bpy.app.timers.register(timer_update)


def unregister_download():
    bpy.utils.unregister_class(BlenderkitDownloadOperator)
    bpy.utils.unregister_class(BlenderkitKillDownloadOperator)
    bpy.app.handlers.load_post.remove(scene_load)
    bpy.app.handlers.save_pre.remove(scene_save)
    if bpy.app.timers.is_registered(timer_update):
        bpy.app.timers.unregister(timer_update)
