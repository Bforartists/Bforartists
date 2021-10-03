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

from blenderkit import paths, utils, categories, ui, colors, bkit_oauth, version_checker, tasks_queue, rerequests, \
    resolutions, image_utils, ratings_utils

import blenderkit
from bpy.app.handlers import persistent

from bpy.props import (  # TODO only keep the ones actually used when cleaning
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
)
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup,
    UIList
)

import requests, os, random
import time
import threading
import platform
import bpy
import copy
import json
import math
import unicodedata
import urllib
import queue
import logging

bk_logger = logging.getLogger('blenderkit')

search_start_time = 0
prev_time = 0


def check_errors(rdata):
    if rdata.get('statusCode') and int(rdata.get('statusCode')) > 299:
        utils.p(rdata)
        if rdata.get('detail') == 'Invalid token.':
            user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
            if user_preferences.api_key != '':
                if user_preferences.enable_oauth:
                    bkit_oauth.refresh_token_thread()
                return False, rdata.get('detail')
            return False, 'Use login panel to connect your profile.'
        else:
            return False, rdata.get('detail')
    if rdata.get('statusCode') is None and rdata.get('results') is None:
        return False, 'Connection error'
    return True, ''


search_threads = []
thumb_workers_sml = []
thumb_workers_full = []
thumb_sml_download_threads = queue.Queue()
thumb_full_download_threads = queue.Queue()
reports_queue = queue.Queue()
all_thumbs_loaded = True

rtips = ['Click or drag model or material in scene to link/append ',
         "Please rate responsively and plentifully. This helps us distribute rewards to the authors.",
         "Click on brushes to link them into scene.",
         "All materials are free.",
         "Storage for public assets is unlimited.",
         "Locked models are available if you subscribe to Full plan.",
         "Login to upload your own models, materials or brushes.",
         "Use 'A' key over asset bar to search assets by same author.",
         "Use 'W' key over asset bar to open Authors webpage.", ]


def refresh_token_timer():
    ''' this timer gets run every time the token needs refresh. It refreshes tokens and also categories.'''
    utils.p('refresh timer')
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    fetch_server_data()
    categories.load_categories()

    return max(3600, user_preferences.api_key_life - 3600)


def update_ad(ad):
    if not ad.get('assetBaseId'):
        try:
            ad['assetBaseId'] = ad['asset_base_id']  # this should stay ONLY for compatibility with older scenes
            ad['assetType'] = ad['asset_type']  # this should stay ONLY for compatibility with older scenes
            ad['verificationStatus'] = ad[
                'verification_status']  # this should stay ONLY for compatibility with older scenes
            ad['author'] = {}
            ad['author']['id'] = ad['author_id']  # this should stay ONLY for compatibility with older scenes
            ad['canDownload'] = ad['can_download']  # this should stay ONLY for compatibility with older scenes
        except Exception as e:
            bk_logger.error('BlenderKit failed to update older asset data')
    return ad


def update_assets_data():  # updates assets data on scene load.
    '''updates some properties that were changed on scenes with older assets.
    The properties were mainly changed from snake_case to CamelCase to fit the data that is coming from the server.
    '''
    data = bpy.data

    datablocks = [
        bpy.data.objects,
        bpy.data.materials,
        bpy.data.brushes,
    ]
    for dtype in datablocks:
        for block in dtype:
            if block.get('asset_data') != None:
                update_ad(block['asset_data'])

    dicts = [
        'assets used',
        # 'assets rated',# assets rated stores only true/false, not asset data.
    ]
    for s in bpy.data.scenes:
        for bkdict in dicts:

            d = s.get(bkdict)
            if not d:
                continue;

            for asset_id in d.keys():
                update_ad(d[asset_id])
                # bpy.context.scene['assets used'][ad] = ad


def purge_search_results():
    ''' clean up search results on save/load.'''

    s = bpy.context.scene

    sr_props = [
        'search results',
        'search results orig',
    ]
    asset_types = ['model', 'material', 'scene', 'hdr', 'brush']
    for at in asset_types:
        sr_props.append('bkit {at} search')
        sr_props.append('bkit {at} search orig')
    for sr_prop in sr_props:
        if s.get(sr_prop):
            del (s[sr_prop])


@persistent
def scene_load(context):
    '''
    Loads categories , checks timers registration, and updates scene asset data.
    Should (probably)also update asset data from server (after user consent)
    '''
    wm = bpy.context.window_manager
    purge_search_results()
    fetch_server_data()
    categories.load_categories()
    if not bpy.app.timers.is_registered(refresh_token_timer):
        bpy.app.timers.register(refresh_token_timer, persistent=True, first_interval=36000)
    update_assets_data()


def fetch_server_data():
    ''' download categories , profile, and refresh token if needed.'''
    if not bpy.app.background:
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        api_key = user_preferences.api_key
        # Only refresh new type of tokens(by length), and only one hour before the token timeouts.
        if user_preferences.enable_oauth and \
                len(user_preferences.api_key) < 38 and len(user_preferences.api_key) > 0 and \
                user_preferences.api_key_timeout < time.time() + 3600:
            bkit_oauth.refresh_token_thread()
        if api_key != '' and bpy.context.window_manager.get('bkit profile') == None:
            get_profile()
        if bpy.context.window_manager.get('bkit_categories') is None:
            categories.fetch_categories_thread(api_key, force=False)


first_time = True
last_clipboard = ''


def check_clipboard():
    '''
    Checks clipboard for an exact string containing asset ID.
    The string is generated on www.blenderkit.com as for example here:
    https://www.blenderkit.com/get-blenderkit/54ff5c85-2c73-49e9-ba80-aec18616a408/
    '''

    # clipboard monitoring to search assets from web
    if platform.system() != 'Linux':
        global last_clipboard
        if bpy.context.window_manager.clipboard != last_clipboard:
            last_clipboard = bpy.context.window_manager.clipboard
            instr = 'asset_base_id:'
            # first check if contains asset id, then asset type
            if last_clipboard[:len(instr)] == instr:
                atstr = 'asset_type:'
                ati = last_clipboard.find(atstr)
                # this only checks if the asset_type keyword is there but let's the keywords update function do the parsing.
                if ati > -1:
                    search_props = utils.get_search_props()
                    search_props.search_keywords = last_clipboard
                    # don't run search after this - assigning to keywords runs the search_update function.


def parse_result(r):
    '''
    needed to generate some extra data in the result(by now)
    Parameters
    ----------
    r - search result, also called asset_data
    '''
    scene = bpy.context.scene

    # TODO remove this fix when filesSize is fixed.
    # this is a temporary fix for too big numbers from the server.
    # try:
    #     r['filesSize'] = int(r['filesSize'] / 1024)
    # except:
    #     utils.p('asset with no files-size')
    asset_type = r['assetType']
    if len(r['files']) > 0:  # TODO remove this condition so all assets are parsed.
        get_author(r)

        r['available_resolutions'] = []
        allthumbs = []
        durl, tname, small_tname = '', '', ''

        if r['assetType'] == 'hdr':
            tname = paths.extract_filename_from_url(r['thumbnailLargeUrlNonsquared'])
        else:
            tname = paths.extract_filename_from_url(r['thumbnailMiddleUrl'])
        small_tname = paths.extract_filename_from_url(r['thumbnailSmallUrl'])
        allthumbs.append(tname)  # TODO just first thumb is used now.
        # if r['fileType'] == 'thumbnail':
        #     tname = paths.extract_filename_from_url(f['fileThumbnailLarge'])
        #     small_tname = paths.extract_filename_from_url(f['fileThumbnail'])
        #     allthumbs.append(tname)  # TODO just first thumb is used now.

        for f in r['files']:
            # if f['fileType'] == 'thumbnail':
            #     tname = paths.extract_filename_from_url(f['fileThumbnailLarge'])
            #     small_tname = paths.extract_filename_from_url(f['fileThumbnail'])
            #     allthumbs.append(tname)  # TODO just first thumb is used now.

            if f['fileType'] == 'blend':
                durl = f['downloadUrl'].split('?')[0]
                # fname = paths.extract_filename_from_url(f['filePath'])

            if f['fileType'].find('resolution') > -1:
                r['available_resolutions'].append(resolutions.resolutions[f['fileType']])

        # code for more thumbnails
        # tdict = {}
        # for i, t in enumerate(allthumbs):
        #     tdict['thumbnail_%i'] = t

        r['max_resolution'] = 0
        if r['available_resolutions']:  # should check only for non-empty sequences
            r['max_resolution'] = max(r['available_resolutions'])

        # tooltip = generate_tooltip(r)
        # for some reason, the id was still int on some occurances. investigate this.
        r['author']['id'] = str(r['author']['id'])

        # some helper props, but generally shouldn't be renaming/duplifiying original properties,
        # so blender's data is same as on server.
        asset_data = {'thumbnail': tname,
                      'thumbnail_small': small_tname,
                      # 'tooltip': tooltip,

                      }
        asset_data['downloaded'] = 0

        # parse extra params needed for blender here
        params = r['dictParameters']  # utils.params_to_dict(r['parameters'])

        if asset_type == 'model':
            if params.get('boundBoxMinX') != None:
                bbox = {
                    'bbox_min': (
                        float(params['boundBoxMinX']),
                        float(params['boundBoxMinY']),
                        float(params['boundBoxMinZ'])),
                    'bbox_max': (
                        float(params['boundBoxMaxX']),
                        float(params['boundBoxMaxY']),
                        float(params['boundBoxMaxZ']))
                }

            else:
                bbox = {
                    'bbox_min': (-.5, -.5, 0),
                    'bbox_max': (.5, .5, 1)
                }
            asset_data.update(bbox)
        if asset_type == 'material':
            asset_data['texture_size_meters'] = params.get('textureSizeMeters', 1.0)

        # asset_data.update(tdict)

        au = scene.get('assets used', {})
        if au == {}:
            scene['assets used'] = au
        if r['assetBaseId'] in au.keys():
            asset_data['downloaded'] = 100
            # transcribe all urls already fetched from the server
            r_previous = au[r['assetBaseId']]
            if r_previous.get('files'):
                for f in r_previous['files']:
                    if f.get('url'):
                        for f1 in r['files']:
                            if f1['fileType'] == f['fileType']:
                                f1['url'] = f['url']

        # attempt to switch to use original data gradually, since the parsing as itself should become obsolete.
        asset_data.update(r)
        return asset_data


# @bpy.app.handlers.persistent
def search_timer():
    # this makes a first search after opening blender. showing latest assets.
    # utils.p('timer search')
    # utils.p('start search timer')
    global first_time
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if first_time and not bpy.app.background:  # first time

        first_time = False
        if preferences.show_on_start:
            # TODO here it should check if there are some results, and only open assetbar if this is the case, not search.
            # if bpy.context.window_manager.get('search results') is None:
            search()
            # preferences.first_run = False
        if preferences.tips_on_start:
            utils.get_largest_area()
            ui.update_ui_size(ui.active_area_pointer, ui.active_region_pointer)
            ui.add_report(text='BlenderKit Tip: ' + random.choice(rtips), timeout=12, color=colors.GREEN)
        # utils.p('end search timer')

        return 3.0

    # if preferences.first_run:
    #     search()
    #     preferences.first_run = False

    # check_clipboard()

    # finish loading thumbs from queues
    global all_thumbs_loaded
    if not all_thumbs_loaded:
        ui_props = bpy.context.scene.blenderkitUI
        search_name = f'bkit {ui_props.asset_type.lower()} search'
        wm = bpy.context.window_manager
        if wm.get(search_name) is not None:
            all_loaded = True
            for ri, r in enumerate(wm[search_name]):
                if not r.get('thumb_small_loaded'):
                    all_loaded = all_loaded and load_preview(r, ri)
            all_thumbs_loaded = all_loaded

    global search_threads
    if len(search_threads) == 0:
        # utils.p('end search timer')
        props = utils.get_search_props()
        props.is_searching = False
        return 1.0
    # don't do anything while dragging - this could switch asset during drag, and make results list length different,
    # causing a lot of throuble.
    if bpy.context.scene.blenderkitUI.dragging:
        # utils.p('end search timer')

        return 0.5

    for thread in search_threads:
        # TODO this doesn't check all processes when one gets removed,
        # but most of the time only one is running anyway
        if not thread[0].is_alive():

            search_threads.remove(thread)  #
            icons_dir = thread[1]
            scene = bpy.context.scene
            # these 2 lines should update the previews enum and set the first result as active.
            wm = bpy.context.window_manager
            asset_type = thread[2]

            props = utils.get_search_props()
            search_name = f'bkit {asset_type} search'

            if not thread[0].params.get('get_next'):
                # wm[search_name] = []
                result_field = []
            else:
                result_field = []
                for r in wm[search_name]:
                    result_field.append(r.to_dict())

            global reports_queue

            while not reports_queue.empty():
                props.report = str(reports_queue.get())
                # utils.p('end search timer')

                return .2

            rdata = thread[0].result

            ok, error = check_errors(rdata)
            if ok:
                ui_props = bpy.context.scene.blenderkitUI
                orig_len = len(result_field)

                for ri, r in enumerate(rdata['results']):
                    asset_data = parse_result(r)
                    if asset_data != None:
                        result_field.append(asset_data)
                        all_thumbs_loaded = all_thumbs_loaded and load_preview(asset_data, ri + orig_len)

                # Get ratings from BlenderKit server
                user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
                api_key = user_preferences.api_key
                headers = utils.get_headers(api_key)
                if utils.profile_is_validator():
                    for r in rdata['results']:
                        if ratings_utils.get_rating_local(r['id']) is None:
                            rating_thread = threading.Thread(target=ratings_utils.get_rating, args=([r['id'], headers]),
                                                             daemon=True)
                            rating_thread.start()

                wm[search_name] = result_field
                wm['search results'] = result_field

                # rdata=['results']=[]
                wm[search_name + ' orig'] = rdata
                wm['search results orig'] = rdata

                if len(result_field) < ui_props.scrolloffset or not (thread[0].params.get('get_next')):
                    # jump back
                    ui_props.scrolloffset = 0
                props.search_error = False
                props.report = 'Found %i results. ' % (wm['search results orig']['count'])
                if len(wm['search results']) == 0:
                    tasks_queue.add_task((ui.add_report, ('No matching results found.',)))
                # undo push
                # bpy.ops.wm.undo_push_context(message='Get BlenderKit search')
                # show asset bar automatically, but only on first page - others are loaded also when asset bar is hidden.
                if not ui_props.assetbar_on and not thread[0].params.get('get_next'):
                    bpy.ops.object.run_assetbar_fix_context()

            else:
                bk_logger.error(error)
                props.report = error
                props.search_error = True

            props.is_searching = False
            # print('finished search thread')
            mt('preview loading finished')
    # utils.p('end search timer')
    if not all_thumbs_loaded:
        return .1
    return .3


def load_preview(asset, index):
    scene = bpy.context.scene
    # FIRST START SEARCH
    props = scene.blenderkitUI
    directory = paths.get_temp_dir('%s_search' % props.asset_type.lower())
    s = bpy.context.scene
    results = bpy.context.window_manager.get('search results')
    loaded = True

    tpath = os.path.join(directory, asset['thumbnail_small'])
    if not asset['thumbnail_small'] or asset['thumbnail_small'] == '' or not os.path.exists(tpath):
        # tpath = paths.get_addon_thumbnail_path('thumbnail_notready.jpg')
        asset['thumb_small_loaded'] = False

    iname = utils.previmg_name(index)

    # if os.path.exists(tpath):  # sometimes we are unlucky...
    img = bpy.data.images.get(iname)

    if img is None:
        if not os.path.exists(tpath):
            return False
        # wrap into try statement since sometimes
        try:
            img = bpy.data.images.load(tpath)
            img.name = iname
        except:
            return False
    elif img.filepath != tpath:
        if not os.path.exists(tpath):
            # unload loaded previews from previous results
            bpy.data.images.remove(img)
            return False
        # had to add this check for autopacking files...
        if bpy.data.use_autopack and img.packed_file is not None:
            img.unpack(method='USE_ORIGINAL')
        img.filepath = tpath
        try:
            img.reload()
        except:
            return False

    if asset['assetType'] == 'hdr':
        # to display hdr thumbnails correctly, we use non-color, otherwise looks shifted
        image_utils.set_colorspace(img, 'Non-Color')
    else:
        image_utils.set_colorspace(img, 'sRGB')
    asset['thumb_small_loaded'] = True
    return True


def load_previews():
    scene = bpy.context.scene
    # FIRST START SEARCH
    props = scene.blenderkitUI
    directory = paths.get_temp_dir('%s_search' % props.asset_type.lower())
    s = bpy.context.scene
    results = bpy.context.window_manager.get('search results')
    #
    if results is not None:
        i = 0
        for r in results:
            load_preview(r, i)
            i += 1


#  line splitting for longer texts...
def split_subs(text, threshold=40):
    if text == '':
        return []
    # temporarily disable this, to be able to do this in drawing code

    text = text.rstrip()
    text = text.replace('\r\n', '\n')

    lines = []

    while len(text) > threshold:
        # first handle if there's an \n line ending
        i_rn = text.find('\n')
        if 1 < i_rn < threshold:
            i = i_rn
            text = text.replace('\n', '', 1)
        else:
            i = text.rfind(' ', 0, threshold)
            i1 = text.rfind(',', 0, threshold)
            i2 = text.rfind('.', 0, threshold)
            i = max(i, i1, i2)
            if i <= 0:
                i = threshold
        lines.append(text[:i])
        text = text[i:]
    lines.append(text)
    return lines


def list_to_str(input):
    output = ''
    for i, text in enumerate(input):
        output += text
        if i < len(input) - 1:
            output += ', '
    return output


def writeblock(t, input, width=40):  # for longer texts
    dlines = split_subs(input, threshold=width)
    for i, l in enumerate(dlines):
        t += '%s\n' % l
    return t


def writeblockm(tooltip, mdata, key='', pretext=None, width=40):  # for longer texts
    if mdata.get(key) == None:
        return tooltip
    else:
        intext = mdata[key]
        if type(intext) == list:
            intext = list_to_str(intext)
        if type(intext) == float:
            intext = round(intext, 3)
        intext = str(intext)
        if intext.rstrip() == '':
            return tooltip
        if pretext == None:
            pretext = key
        if pretext != '':
            pretext = pretext + ': '
        text = pretext + intext
        dlines = split_subs(text, threshold=width)
        for i, l in enumerate(dlines):
            tooltip += '%s\n' % l

    return tooltip


def has(mdata, prop):
    if mdata.get(prop) is not None and mdata[prop] is not None and mdata[prop] is not False:
        return True
    else:
        return False


def generate_tooltip(mdata):
    col_w = 40
    if type(mdata['parameters']) == list:
        mparams = utils.params_to_dict(mdata['parameters'])
    else:
        mparams = mdata['parameters']
    t = ''
    t = writeblock(t, mdata['displayName'], width=int(col_w * .6))
    # t += '\n'

    # t = writeblockm(t, mdata, key='description', pretext='', width=col_w)
    return t


def get_random_tip():
    t = ''
    tip = 'Tip: ' + random.choice(rtips)
    t = writeblock(t, tip)
    return t


def generate_author_textblock(adata):
    t = ''

    if adata not in (None, ''):
        col_w = 2000
        if len(adata['firstName'] + adata['lastName']) > 0:
            t = '%s %s\n' % (adata['firstName'], adata['lastName'])
            t += '\n'
            if adata.get('aboutMe') is not None:
                t = writeblockm(t, adata, key='aboutMe', pretext='', width=col_w)
    return t


def download_image(session, url, filepath):
    r = None
    try:
        r = session.get(url, stream=False)
    except Exception as e:
        bk_logger.error('Thumbnail download failed')
        bk_logger.error(str(e))
    if r and r.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(r.content)


def thumb_download_worker(queue_sml, queue_full):
    # print('thumb downloader', self.url)
    # utils.p('start thumbdownloader thread')
    while 1:
        session = None
        # start a session only for single search usually, if users starts scrolling, the session might last longer if
        # queue gets filled.
        if not queue_sml.empty() or not queue_full.empty():
            if session is None:
                session = requests.Session()
            while not queue_sml.empty():
                # first empty the small thumbs queue
                url, filepath = queue_sml.get()
                download_image(session, url, filepath)
            exit_full = False
            # download full resolution image, but only if no small thumbs are waiting. If there are small
            while not queue_full.empty() and queue_sml.empty():
                url, filepath = queue_full.get()
                download_image(session, url, filepath)

        if queue_sml.empty() and queue_full.empty():
            if session is not None:
                session.close()
                session = None
            time.sleep(.5)


def write_gravatar(a_id, gravatar_path):
    '''
    Write down gravatar path, as a result of thread-based gravatar image download.
    This should happen on timer in queue.
    '''
    # print('write author', a_id, type(a_id))
    authors = bpy.context.window_manager['bkit authors']
    if authors.get(a_id) is not None:
        adata = authors.get(a_id)
        adata['gravatarImg'] = gravatar_path


def fetch_gravatar(adata):
    '''
    Gets avatars from blenderkit server
    Parameters
    ----------
    adata - author data from elastic search result

    '''
    # utils.p('fetch gravatar')

    # fetch new avatars if available already
    if adata.get('avatar128') is not None:
        avatar_path = paths.get_temp_dir(subdir='bkit_g/') + adata['id'] + '.jpg'
        if os.path.exists(avatar_path):
            tasks_queue.add_task((write_gravatar, (adata['id'], avatar_path)))
            return;

        url = paths.get_bkit_url() + adata['avatar128']
        r = rerequests.get(url, stream=False)
        # print(r.body)
        if r.status_code == 200:
            # print(url)
            # print(r.headers['content-disposition'])
            with open(avatar_path, 'wb') as f:
                f.write(r.content)
            tasks_queue.add_task((write_gravatar, (adata['id'], avatar_path)))
        elif r.status_code == '404':
            adata['avatar128'] = None
            utils.p('avatar for author not available.')
        return

    # older gravatar code
    if adata.get('gravatarHash') is not None:
        gravatar_path = paths.get_temp_dir(subdir='bkit_g/') + adata['gravatarHash'] + '.jpg'

        if os.path.exists(gravatar_path):
            tasks_queue.add_task((write_gravatar, (adata['id'], gravatar_path)))
            return;

        url = "https://www.gravatar.com/avatar/" + adata['gravatarHash'] + '?d=404'
        r = rerequests.get(url, stream=False)
        if r.status_code == 200:
            with open(gravatar_path, 'wb') as f:
                f.write(r.content)
            tasks_queue.add_task((write_gravatar, (adata['id'], gravatar_path)))
        elif r.status_code == '404':
            adata['gravatarHash'] = None
            utils.p('gravatar for author not available.')


fetching_gravatars = {}


def get_author(r):
    ''' Writes author info (now from search results) and fetches gravatar if needed.'''
    global fetching_gravatars

    a_id = str(r['author']['id'])
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    authors = bpy.context.window_manager.get('bkit authors', {})
    if authors == {}:
        bpy.context.window_manager['bkit authors'] = authors
    a = authors.get(a_id)
    if a is None:  # or a is '' or (a.get('gravatarHash') is not None and a.get('gravatarImg') is None):
        a = r['author']
        a['id'] = a_id
        a['tooltip'] = generate_author_textblock(a)

        authors[a_id] = a
        if fetching_gravatars.get(a['id']) is None:
            fetching_gravatars[a['id']] = True

        thread = threading.Thread(target=fetch_gravatar, args=(a.copy(),), daemon=True)
        thread.start()
    return a


def write_profile(adata):
    utils.p('writing profile information')
    user = adata['user']
    # we have to convert to MiB here, numbers too big for python int type
    if user.get('sumAssetFilesSize') is not None:
        user['sumAssetFilesSize'] /= (1024 * 1024)
    if user.get('sumPrivateAssetFilesSize') is not None:
        user['sumPrivateAssetFilesSize'] /= (1024 * 1024)
    if user.get('remainingPrivateQuota') is not None:
        user['remainingPrivateQuota'] /= (1024 * 1024)

    if adata.get('canEditAllAssets') is True:
        user['exmenu'] = True
    else:
        user['exmenu'] = False

    bpy.context.window_manager['bkit profile'] = adata


def request_profile(api_key):
    a_url = paths.get_api_url() + 'me/'
    headers = utils.get_headers(api_key)
    r = rerequests.get(a_url, headers=headers)
    adata = r.json()
    if adata.get('user') is None:
        utils.p(adata)
        utils.p('getting profile failed')
        return None
    return adata


def fetch_profile(api_key):
    utils.p('fetch profile')
    try:
        adata = request_profile(api_key)
        if adata is not None:
            tasks_queue.add_task((write_profile, (adata,)))
    except Exception as e:
        bk_logger.error(e)


def get_profile():
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    a = bpy.context.window_manager.get('bkit profile')
    thread = threading.Thread(target=fetch_profile, args=(preferences.api_key,), daemon=True)
    thread.start()
    return a


def query_to_url(query={}, params={}):
    # build a new request
    url = paths.get_api_url() + 'search/'

    # build request manually
    # TODO use real queries
    requeststring = '?query='
    #
    if query.get('query') not in ('', None):
        requeststring += query['query'].lower()
    for i, q in enumerate(query):
        if q != 'query':
            requeststring += '+'
            requeststring += q + ':' + str(query[q]).lower()

    # add dict_parameters to make results smaller
    # result ordering: _score - relevance, score - BlenderKit score
    order = []
    if params['free_first']:
        order = ['-is_free', ]
    if query.get('query') is None and query.get('category_subtree') == None:
        # assumes no keywords and no category, thus an empty search that is triggered on start.
        # orders by last core file upload
        if query.get('verification_status') == 'uploaded':
            # for validators, sort uploaded from oldest
            order.append('created')
        else:
            order.append('-last_upload')
    elif query.get('author_id') is not None and utils.profile_is_validator():

        order.append('-created')
    else:
        if query.get('category_subtree') is not None:
            order.append('-score,_score')
        else:
            order.append('_score')
    if requeststring.find('+order:') == -1:
        requeststring += '+order:' + ','.join(order)
    requeststring += '&dict_parameters=1'

    requeststring += '&page_size=' + str(params['page_size'])
    requeststring += '&addon_version=%s' % params['addon_version']
    if params.get('scene_uuid') is not None:
        requeststring += '&scene_uuid=%s' % params['scene_uuid']
    # print('params', params)
    urlquery = url + requeststring
    return urlquery


def parse_html_formated_error(text):
    report = text[text.find('<title>') + 7: text.find('</title>')]

    return report


class Searcher(threading.Thread):
    query = None

    def __init__(self, query, params, tempdir='', headers=None, urlquery=''):
        super(Searcher, self).__init__()
        self.query = query
        self.params = params
        self._stop_event = threading.Event()
        self.result = {}
        self.tempdir = tempdir
        self.headers = headers
        self.urlquery = urlquery

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        global reports_queue, thumb_sml_download_threads, thumb_full_download_threads

        maxthreads = 50
        query = self.query
        params = self.params

        t = time.time()
        # utils.p('start search thread')

        mt('search thread started')
        # tempdir = paths.get_temp_dir('%s_search' % query['asset_type'])
        # json_filepath = os.path.join(tempdir, '%s_searchresult.json' % query['asset_type'])

        rdata = {}
        rdata['results'] = []

        try:
            utils.p(self.urlquery)
            r = rerequests.get(self.urlquery, headers=self.headers)  # , params = rparameters)
        except requests.exceptions.RequestException as e:
            bk_logger.error(e)
            reports_queue.put(str(e))
            # utils.p('end search thread')

            return

        mt('search response is back ')
        try:
            rdata = r.json()
        except Exception as e:
            if hasattr(r, 'text'):
                error_description = parse_html_formated_error(r.text)
                reports_queue.put(error_description)
                tasks_queue.add_task((ui.add_report, (error_description, 10, colors.RED)))

            bk_logger.error(e)
            return
        mt('data parsed ')
        if not rdata.get('results'):
            utils.pprint(rdata)
            # if the result was converted to json and didn't return results,
            # it means it's a server error that has a clear message.
            # That's why it gets processed in the update timer, where it can be passed in messages to user.
            self.result = rdata
            # utils.p('end search thread')

            return
        # print('number of results: ', len(rdata.get('results', [])))
        if self.stopped():
            utils.p('stopping search : ' + str(query))
            # utils.p('end search thread')

            return

        mt('search finished')
        i = 0

        thumb_small_urls = []
        thumb_small_filepaths = []
        thumb_full_urls = []
        thumb_full_filepaths = []
        # END OF PARSING
        for d in rdata.get('results', []):
            thumb_small_urls.append(d["thumbnailSmallUrl"])
            imgname = paths.extract_filename_from_url(d['thumbnailSmallUrl'])
            imgpath = os.path.join(self.tempdir, imgname)
            thumb_small_filepaths.append(imgpath)

            if d["assetType"] == 'hdr':
                larege_thumb_url = d['thumbnailLargeUrlNonsquared']

            else:
                larege_thumb_url = d['thumbnailMiddleUrl']

            thumb_full_urls.append(larege_thumb_url)
            imgname = paths.extract_filename_from_url(larege_thumb_url)
            imgpath = os.path.join(self.tempdir, imgname)
            thumb_full_filepaths.append(imgpath)

            # for f in d['files']:
            #     # TODO move validation of published assets to server, too manmy checks here.
            #     if f['fileType'] == 'thumbnail' and f['fileThumbnail'] != None and f['fileThumbnailLarge'] != None:
            #         if f['fileThumbnail'] == None:
            #             f['fileThumbnail'] = 'NONE'
            #         if f['fileThumbnailLarge'] == None:
            #             f['fileThumbnailLarge'] = 'NONE'
            #
            #         thumb_small_urls.append(f['fileThumbnail'])
            #         thumb_full_urls.append(f['fileThumbnailLarge'])
            #
            #         imgname = paths.extract_filename_from_url(f['fileThumbnail'])
            #         imgpath = os.path.join(self.tempdir, imgname)
            #         thumb_small_filepaths.append(imgpath)
            #
            #         imgname = paths.extract_filename_from_url(f['fileThumbnailLarge'])
            #         imgpath = os.path.join(self.tempdir, imgname)
            #         thumb_full_filepaths.append(imgpath)

        sml_thbs = zip(thumb_small_filepaths, thumb_small_urls)
        full_thbs = zip(thumb_full_filepaths, thumb_full_urls)

        # we save here because a missing thumbnail check is in the previous loop
        # we can also prepend previous results. These have downloaded thumbnails already...

        self.result = rdata

        if self.stopped():
            utils.p('stopping search : ' + str(query))
            # utils.p('end search thread')
            return

        # this loop handles downloading of small thumbnails
        for imgpath, url in sml_thbs:
            if not os.path.exists(imgpath):
                thumb_sml_download_threads.put((url, imgpath))

        if self.stopped():
            utils.p('stopping search : ' + str(query))
            # utils.p('end search thread')
            return

        if self.stopped():
            # utils.p('end search thread')

            utils.p('stopping search : ' + str(query))
            return

        # start downloading full thumbs in the end
        tsession = requests.Session()

        for imgpath, url in full_thbs:
            if not os.path.exists(imgpath):
                thumb_full_download_threads.put((url, imgpath))
        # utils.p('end search thread')
        mt('thumbnails finished')


def build_query_common(query, props):
    '''add shared parameters to query'''
    query_common = {}
    if props.search_keywords != '':
        # keywords = urllib.parse.urlencode(props.search_keywords)
        keywords = props.search_keywords.replace('&', '%26')
        query_common["query"] = keywords

    if props.search_verification_status != 'ALL' and utils.profile_is_validator():
        query_common['verification_status'] = props.search_verification_status.lower()

    if props.unrated_only and utils.profile_is_validator():
        query["quality_count"] = 0

    if props.search_file_size:
        query_common["files_size_gte"] = props.search_file_size_min * 1024 * 1024
        query_common["files_size_lte"] = props.search_file_size_max * 1024 * 1024

    if props.quality_limit > 0:
        query["quality_gte"] = props.quality_limit

    query.update(query_common)


def build_query_model():
    '''use all search input to request results from server'''

    props = bpy.context.window_manager.blenderkit_models
    query = {
        "asset_type": 'model',
        # "engine": props.search_engine,
        # "adult": props.search_adult,
    }
    if props.search_style != 'ANY':
        if props.search_style != 'OTHER':
            query["model_style"] = props.search_style
        else:
            query["model_style"] = props.search_style_other

    # the 'free_only' parametr gets moved to the search command and is used for ordering the assets as free first
    # if props.free_only:
    #     query["is_free"] = True

    if props.search_condition != 'UNSPECIFIED':
        query["condition"] = props.search_condition

    if props.search_design_year:
        query["designYear_gte"] = props.search_design_year_min
        query["designYear_lte"] = props.search_design_year_max
    if props.search_polycount:
        query["faceCount_gte"] = props.search_polycount_min
        query["faceCount_lte"] = props.search_polycount_max
    if props.search_texture_resolution:
        query["textureResolutionMax_gte"] = props.search_texture_resolution_min
        query["textureResolutionMax_lte"] = props.search_texture_resolution_max

    build_query_common(query, props)

    return query


def build_query_scene():
    '''use all search input to request results from server'''

    props = bpy.context.window_manager.blenderkit_scene
    query = {
        "asset_type": 'scene',
        # "engine": props.search_engine,
        # "adult": props.search_adult,
    }
    build_query_common(query, props)
    return query


def build_query_HDR():
    '''use all search input to request results from server'''

    props = bpy.context.window_manager.blenderkit_HDR
    query = {
        "asset_type": 'hdr',

        # "engine": props.search_engine,
        # "adult": props.search_adult,
    }
    if props.true_hdr:
        query["trueHDR"] = props.true_hdr
    build_query_common(query, props)
    return query


def build_query_material():
    props = bpy.context.window_manager.blenderkit_mat
    query = {
        "asset_type": 'material',

    }
    # if props.search_engine == 'NONE':
    #     query["engine"] = ''
    # if props.search_engine != 'OTHER':
    #     query["engine"] = props.search_engine
    # else:
    #     query["engine"] = props.search_engine_other
    if props.search_style != 'ANY':
        if props.search_style != 'OTHER':
            query["style"] = props.search_style
        else:
            query["style"] = props.search_style_other
    if props.search_procedural == 'TEXTURE_BASED':
        # todo this procedural hack should be replaced with the parameter
        query["textureResolutionMax_gte"] = 0
        # query["procedural"] = False
        if props.search_texture_resolution:
            query["textureResolutionMax_gte"] = props.search_texture_resolution_min
            query["textureResolutionMax_lte"] = props.search_texture_resolution_max



    elif props.search_procedural == "PROCEDURAL":
        # todo this procedural hack should be replaced with the parameter
        query["files_size_lte"] = 1024 * 1024
        # query["procedural"] = True

    build_query_common(query, props)

    return query


def build_query_texture():
    props = bpy.context.scene.blenderkit_tex
    query = {
        "asset_type": 'texture',

    }

    if props.search_style != 'ANY':
        if props.search_style != 'OTHER':
            query["search_style"] = props.search_style
        else:
            query["search_style"] = props.search_style_other

    build_query_common(query, props)

    return query


def build_query_brush():
    props = bpy.context.window_manager.blenderkit_brush

    brush_type = ''
    if bpy.context.sculpt_object is not None:
        brush_type = 'sculpt'

    elif bpy.context.image_paint_object:  # could be just else, but for future p
        brush_type = 'texture_paint'

    query = {
        "asset_type": 'brush',

        "mode": brush_type
    }

    build_query_common(query, props)

    return query


def mt(text):
    global search_start_time, prev_time
    alltime = time.time() - search_start_time
    since_last = time.time() - prev_time
    prev_time = time.time()
    utils.p(text, alltime, since_last)


def add_search_process(query, params):
    global search_threads, thumb_workers_sml, thumb_workers_full, all_thumbs_loaded

    while (len(search_threads) > 0):
        old_thread = search_threads.pop(0)
        old_thread[0].stop()
        # TODO CARE HERE FOR ALSO KILLING THE Thumbnail THREADS.?
        #  AT LEAST NOW SEARCH DONE FIRST WON'T REWRITE AN NEWER ONE
    tempdir = paths.get_temp_dir('%s_search' % query['asset_type'])
    headers = utils.get_headers(params['api_key'])

    if params.get('get_next'):
        urlquery = params['next']
    else:
        urlquery = query_to_url(query, params)

    if thumb_workers_sml == []:
        for a in range(0, 8):
            thread = threading.Thread(target=thumb_download_worker,
                                      args=(thumb_sml_download_threads, thumb_full_download_threads),
                                      daemon=True)
            thread.start()
            thumb_workers_sml.append(thread)

    all_thumbs_loaded = False

    thread = Searcher(query, params, tempdir=tempdir, headers=headers, urlquery=urlquery)
    thread.start()

    search_threads.append([thread, tempdir, query['asset_type'], {}])  # 4th field is for results

    mt('search thread started')


def get_search_simple(parameters, filepath=None, page_size=100, max_results=100000000, api_key=''):
    '''
    Searches and returns the


    Parameters
    ----------
    parameters - dict of blenderkit elastic parameters
    filepath - a file to save the results. If None, results are returned
    page_size - page size for retrieved results
    max_results - max results of the search
    api_key - BlenderKit api key

    Returns
    -------
    Returns search results as a list, and optionally saves to filepath

    '''
    headers = utils.get_headers(api_key)
    url = paths.get_api_url() + 'search/'
    requeststring = url + '?query='
    for p in parameters.keys():
        requeststring += f'+{p}:{parameters[p]}'

    requeststring += '&page_size=' + str(page_size)
    requeststring += '&dict_parameters=1'

    bk_logger.debug(requeststring)
    response = rerequests.get(requeststring, headers=headers)  # , params = rparameters)
    # print(response.json())
    search_results = response.json()

    results = []
    results.extend(search_results['results'])
    page_index = 2
    page_count = math.ceil(search_results['count'] / page_size)
    while search_results.get('next') and len(results) < max_results:
        bk_logger.info(f'getting page {page_index} , total pages {page_count}')
        response = rerequests.get(search_results['next'], headers=headers)  # , params = rparameters)
        search_results = response.json()
        # print(search_results)
        results.extend(search_results['results'])
        page_index += 1

    if not filepath:
        return results

    with open(filepath, 'w', encoding='utf-8') as s:
        json.dump(results, s, ensure_ascii=False, indent=4)
    bk_logger.info(f'retrieved {len(results)} assets from elastic search')
    return results

def get_single_asset(asset_base_id):
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    params = {
        'asset_base_id': asset_base_id
    }
    results = get_search_simple(params, api_key=preferences.api_key)
    if len(results)>0:
        return results[0]
    return None

def search(category='', get_next=False, author_id=''):
    ''' initialize searching'''
    global search_start_time
    # print(category,get_next,author_id)
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    search_start_time = time.time()
    # mt('start')
    scene = bpy.context.scene
    wm = bpy.context.window_manager
    ui_props = scene.blenderkitUI

    props = utils.get_search_props()
    if ui_props.asset_type == 'MODEL':
        if not hasattr(wm, 'blenderkit_models'):
            return;
        query = build_query_model()

    if ui_props.asset_type == 'SCENE':
        if not hasattr(wm, 'blenderkit_scene'):
            return;
        query = build_query_scene()

    if ui_props.asset_type == 'HDR':
        if not hasattr(wm, 'blenderkit_HDR'):
            return;
        query = build_query_HDR()

    if ui_props.asset_type == 'MATERIAL':
        if not hasattr(wm, 'blenderkit_mat'):
            return;

        query = build_query_material()

    if ui_props.asset_type == 'TEXTURE':
        if not hasattr(wm, 'blenderkit_tex'):
            return;
        # props = scene.blenderkit_tex
        # query = build_query_texture()

    if ui_props.asset_type == 'BRUSH':
        if not hasattr(wm, 'blenderkit_brush'):
            return;
        query = build_query_brush()

    # crop long searches
    if query.get('query'):
        if len(query['query']) > 50:
            query['query'] = strip_accents(query['query'])

        if len(query['query']) > 150:
            idx = query['query'].find(' ', 142)
            query['query'] = query['query'][:idx]

    # it's possible get_next was requested more than once.
    # print(category,props.is_searching, get_next)
    # print(query)
    if props.is_searching and get_next == True:
        # print('return because of get next and searching is happening')
        return;

    if category != '':
        if utils.profile_is_validator() and user_preferences.categories_fix:
            query['category'] = category
        else:
            query['category_subtree'] = category

    if author_id != '':
        query['author_id'] = author_id

    elif props.own_only:
        # if user searches for [another] author, 'only my assets' is invalid. that's why in elif.
        profile = bpy.context.window_manager.get('bkit profile')
        if profile is not None:
            query['author_id'] = str(profile['user']['id'])

    # utils.p('searching')
    props.is_searching = True

    page_size = min(30, ui_props.wcount * user_preferences.max_assetbar_rows)

    params = {
        'scene_uuid': bpy.context.scene.get('uuid', None),
        'addon_version': version_checker.get_addon_version(),
        'api_key': user_preferences.api_key,
        'get_next': get_next,
        'free_first': props.free_only,
        'page_size': page_size,
    }

    orig_results = bpy.context.window_manager.get(f'bkit {ui_props.asset_type.lower()} search orig')
    if orig_results is not None and get_next:
        params['next'] = orig_results['next']
    add_search_process(query, params)
    tasks_queue.add_task((ui.add_report, ('BlenderKit searching....', 2)))

    props.report = 'BlenderKit searching....'


def update_filters():
    sprops = utils.get_search_props()
    ui_props = bpy.context.scene.blenderkitUI
    fcommon = sprops.own_only or \
              sprops.search_texture_resolution or \
              sprops.search_file_size or \
              sprops.search_procedural != 'BOTH' or \
              sprops.free_only or \
              sprops.quality_limit > 0

    if ui_props.asset_type == 'MODEL':
        sprops.use_filters = fcommon or \
                             sprops.search_style != 'ANY' or \
                             sprops.search_condition != 'UNSPECIFIED' or \
                             sprops.search_design_year or \
                             sprops.search_polycount
    elif ui_props.asset_type == 'MATERIAL':
        sprops.use_filters = fcommon
    elif ui_props.asset_type == 'HDR':
        sprops.use_filters = sprops.true_hdr


def search_update(self, context):
    utils.p('search updater')
    # if self.search_keywords != '':
    update_filters()
    ui_props = bpy.context.scene.blenderkitUI
    if ui_props.down_up != 'SEARCH':
        ui_props.down_up = 'SEARCH'

    # here we tweak the input if it comes form the clipboard. we need to get rid of asset type and set it in UI
    sprops = utils.get_search_props()
    instr = 'asset_base_id:'
    atstr = 'asset_type:'
    kwds = sprops.search_keywords
    idi = kwds.find(instr)
    ati = kwds.find(atstr)
    # if the asset type already isn't there it means this update function
    # was triggered by it's last iteration and needs to cancel
    if ati > -1:
        at = kwds[ati:].lower()
        # uncertain length of the remaining string -  find as better method to check the presence of asset type
        if at.find('model') > -1:
            ui_props.asset_type = 'MODEL'
        elif at.find('material') > -1:
            ui_props.asset_type = 'MATERIAL'
        elif at.find('brush') > -1:
            ui_props.asset_type = 'BRUSH'
        elif at.find('scene') > -1:
            ui_props.asset_type = 'SCENE'
        elif at.find('hdr') > -1:
            ui_props.asset_type = 'HDR'
        # now we trim the input copypaste by anything extra that is there,
        # this is also a way for this function to recognize that it already has parsed the clipboard
        # the search props can have changed and this needs to transfer the data to the other field
        # this complex behaviour is here for the case where the user needs to paste manually into blender?
        sprops = utils.get_search_props()
        sprops.search_keywords = kwds[:ati].rstrip()
        # return here since writing into search keywords triggers this update function once more.
        return

    # print('search update search')
    search()


# accented_string is of type 'unicode'
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


class SearchOperator(Operator):
    """Tooltip"""
    bl_idname = "view3d.blenderkit_search"
    bl_label = "BlenderKit asset search"
    bl_description = "Search online for assets"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    esc: BoolProperty(name="Escape window",
                      description="Escape window right after start",
                      default=False,
                      options={'SKIP_SAVE'}
                      )

    own: BoolProperty(name="own assets only",
                      description="Find all own assets",
                      default=False,
                      options={'SKIP_SAVE'})

    category: StringProperty(
        name="category",
        description="search only subtree of this category",
        default="",
        options={'SKIP_SAVE'}
    )

    author_id: StringProperty(
        name="Author ID",
        description="Author ID - search only assets by this author",
        default="",
        options={'SKIP_SAVE'}
    )

    get_next: BoolProperty(name="next page",
                           description="get next page from previous search",
                           default=False,
                           options={'SKIP_SAVE'}
                           )

    keywords: StringProperty(
        name="Keywords",
        description="Keywords",
        default="",
        options={'SKIP_SAVE'}
    )

    # close_window: BoolProperty(name='Close window',
    #                            description='Try to close the window below mouse before download',
    #                            default=False)

    tooltip: bpy.props.StringProperty(default='Runs search and displays the asset bar at the same time')

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # TODO ; this should all get transferred to properties of the search operator, so sprops don't have to be fetched here at all.
        if self.esc:
            bpy.ops.view3d.close_popup_button('INVOKE_DEFAULT')
        sprops = utils.get_search_props()
        if self.author_id != '':
            sprops.search_keywords = ''
        if self.keywords != '':
            sprops.search_keywords = self.keywords

        search(category=self.category, get_next=self.get_next, author_id=self.author_id)
        # bpy.ops.view3d.blenderkit_asset_bar()

        return {'FINISHED'}

    # def invoke(self, context, event):
    #     if self.close_window:
    #         context.window.cursor_warp(event.mouse_x, event.mouse_y - 100);
    #         context.area.tag_redraw()
    #
    #         context.window.cursor_warp(event.mouse_x, event.mouse_y);
    #     return self. execute(context)


class UrlOperator(Operator):
    """"""
    bl_idname = "wm.blenderkit_url"
    bl_label = ""
    bl_description = "Search online for assets"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    tooltip: bpy.props.StringProperty(default='Open a web page')
    url: bpy.props.StringProperty(default='Runs search and displays the asset bar at the same time')

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        bpy.ops.wm.url_open(url=self.url)
        return {'FINISHED'}


class TooltipLabelOperator(Operator):
    """"""
    bl_idname = "wm.blenderkit_tooltip"
    bl_label = ""
    bl_description = "Empty operator to be able to create tooltips on labels in UI"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    tooltip: bpy.props.StringProperty(default='Open a web page')

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'FINISHED'}


classes = [
    SearchOperator,
    UrlOperator,
    TooltipLabelOperator
]


def register_search():
    bpy.app.handlers.load_post.append(scene_load)

    for c in classes:
        bpy.utils.register_class(c)

    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.use_timers:
        bpy.app.timers.register(search_timer)

    categories.load_categories()


def unregister_search():
    bpy.app.handlers.load_post.remove(scene_load)

    for c in classes:
        bpy.utils.unregister_class(c)

    if bpy.app.timers.is_registered(search_timer):
        bpy.app.timers.unregister(search_timer)
