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
    utils = reload(utils)
    categories = reload(categories)
    ui = reload(ui)
    bkit_oauth = reload(bkit_oauth)
    version_checker = reload(version_checker)
    tasks_queue = reload(tasks_queue)
    rerequests = reload(rerequests)
else:
    from blenderkit import paths, utils, categories, ui, bkit_oauth, version_checker, tasks_queue, rerequests

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
import tempfile
import json
import bpy

search_start_time = 0
prev_time = 0


def check_errors(rdata):
    if rdata.get('statusCode') == 401:
        utils.p(rdata)
        if rdata.get('detail') == 'Invalid token.':
            user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
            if user_preferences.api_key != '':
                if user_preferences.enable_oauth:
                    bkit_oauth.refresh_token_thread()
                return False, rdata.get('detail')
            return False, 'Missing or wrong api_key in addon preferences'
    return True, ''


search_threads = []
thumb_sml_download_threads = {}
thumb_full_download_threads = {}
reports = ''


def refresh_token_timer():
    ''' this timer gets run every time the token needs refresh. It refreshes tokens and also categories.'''
    utils.p('refresh timer')
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    fetch_server_data()
    categories.load_categories()

    return max(3600, user_preferences.api_key_life - 3600)


@persistent
def scene_load(context):
    wm = bpy.context.window_manager
    fetch_server_data()
    categories.load_categories()
    if not bpy.app.timers.is_registered(refresh_token_timer):
        bpy.app.timers.register(refresh_token_timer, persistent=True, first_interval=36000)


def fetch_server_data():
    ''' download categories and addon version'''
    if not bpy.app.background:
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        api_key = user_preferences.api_key
        # Only refresh new type of tokens(by length), and only one hour before the token timeouts.
        if user_preferences.enable_oauth and \
                len(user_preferences.api_key) < 38 and \
                user_preferences.api_key_timeout < time.time() + 3600:
            bkit_oauth.refresh_token_thread()
        if api_key != '' and bpy.context.window_manager.get('bkit profile') == None:
            get_profile()
        if bpy.context.window_manager.get('bkit_categories') is None:
            categories.fetch_categories_thread(api_key)


first_time = True

@bpy.app.handlers.persistent
def timer_update():  # TODO might get moved to handle all blenderkit stuff.
    #this makes a first search after opening blender. showing latest assets.
    global first_time
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if first_time:
        first_time = False
        if preferences.show_on_start:
            search()

    global search_threads
    # don't do anything while dragging - this could switch asset type during drag, and make results list length different,
    # causing a lot of throuble literally.
    if len(search_threads) == 0 or bpy.context.scene.blenderkitUI.dragging:
        return 1
    for thread in search_threads:  # TODO this doesn't check all processes when one gets removed,
                                   # but most of the time only one is running anyway
        if not thread[0].is_alive():
            search_threads.remove(thread)  #
            icons_dir = thread[1]
            scene = bpy.context.scene
            # these 2 lines should update the previews enum and set the first result as active.
            s = bpy.context.scene
            asset_type = thread[2]
            if asset_type == 'model':
                props = scene.blenderkit_models
                json_filepath = os.path.join(icons_dir, 'model_searchresult.json')
                search_name = 'bkit model search'
            if asset_type == 'scene':
                props = scene.blenderkit_scene
                json_filepath = os.path.join(icons_dir, 'scene_searchresult.json')
                search_name = 'bkit scene search'
            if asset_type == 'material':
                props = scene.blenderkit_mat
                json_filepath = os.path.join(icons_dir, 'material_searchresult.json')
                search_name = 'bkit material search'
            if asset_type == 'brush':
                props = scene.blenderkit_brush
                json_filepath = os.path.join(icons_dir, 'brush_searchresult.json')
                search_name = 'bkit brush search'

            s[search_name] = []

            global reports
            if reports != '':
                props.report = str(reports)
                return .2
            with open(json_filepath, 'r') as data_file:
                rdata = json.load(data_file)

            result_field = []
            ok, error = check_errors(rdata)
            if ok:
                bpy.ops.object.run_assetbar_fix_context()
                for r in rdata['results']:
                    # TODO remove this fix when filesSize is fixed.
                    # this is a temporary fix for too big numbers from the server.
                    try:
                        r['filesSize'] = int(r['filesSize'] / 1024)
                    except:
                        utils.p('asset with no files-size')
                    if r['assetType'] == asset_type:
                        if len(r['files']) > 0:
                            furl = None
                            tname = None
                            allthumbs = []
                            durl, tname = None, None
                            for f in r['files']:
                                if f['fileType'] == 'thumbnail':
                                    tname = paths.extract_filename_from_url(f['fileThumbnailLarge'])
                                    small_tname = paths.extract_filename_from_url(f['fileThumbnail'])
                                    allthumbs.append(tname)  # TODO just first thumb is used now.

                                tdict = {}
                                for i, t in enumerate(allthumbs):
                                    tdict['thumbnail_%i'] = t
                                if f['fileType'] == 'blend':
                                    durl = f['downloadUrl'].split('?')[0]
                                    # fname = paths.extract_filename_from_url(f['filePath'])
                            if durl and tname:

                                tooltip = generate_tooltip(r)
                                asset_data = {'thumbnail': tname,
                                              'thumbnail_small': small_tname,
                                              # 'thumbnails':allthumbs,
                                              'download_url': durl,
                                              'id': r['id'],
                                              'asset_base_id': r['assetBaseId'],
                                              'name': r['name'],
                                              'asset_type': r['assetType'],
                                              'tooltip': tooltip,
                                              'tags': r['tags'],
                                              'can_download': r.get('canDownload', True),
                                              'verification_status': r['verificationStatus'],
                                              'author_id': str(r['author']['id'])
                                              # 'author': r['author']['firstName'] + ' ' + r['author']['lastName']
                                              # 'description': r['description'],
                                              # 'author': r['description'],
                                              }
                                asset_data['downloaded'] = 0

                                # parse extra params needed for blender here
                                params = params_to_dict(r['parameters'])

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

                                asset_data.update(tdict)
                                if r['assetBaseId'] in scene.get('assets used', {}).keys():
                                    asset_data['downloaded'] = 100

                                result_field.append(asset_data)

                                # results = rdata['results']
                s[search_name] = result_field
                s['search results'] = result_field
                s[search_name + ' orig'] = rdata
                s['search results orig'] = rdata
                load_previews()
                ui_props = bpy.context.scene.blenderkitUI
                if len(result_field) < ui_props.scrolloffset:
                    ui_props.scrolloffset = 0
                props.is_searching = False
                props.search_error = False
                props.report = 'Found %i results. ' % (s['search results orig']['count'])
                if len(s['search results']) == 0:
                    tasks_queue.add_task((ui.add_report, ('No matching results found.',)))

            # (rdata['next'])
            # if rdata['next'] != None:
            # search(False, get_next = True)
            else:
                print('error', error)
                props.report = error
                props.search_error = True

            # print('finished search thread')
            mt('preview loading finished')
    return .3


def load_previews():
    mappingdict = {
        'MODEL': 'model',
        'SCENE': 'scene',
        'MATERIAL': 'material',
        'TEXTURE': 'texture',
        'BRUSH': 'brush'
    }
    scene = bpy.context.scene
    # FIRST START SEARCH
    props = scene.blenderkitUI

    directory = paths.get_temp_dir('%s_search' % mappingdict[props.asset_type])
    s = bpy.context.scene
    results = s.get('search results')
    #
    if results is not None:
        inames = []
        tpaths = []

        i = 0
        for r in results:

            tpath = os.path.join(directory, r['thumbnail_small'])

            iname = utils.previmg_name(i)

            if os.path.exists(tpath):  # sometimes we are unlucky...
                img = bpy.data.images.get(iname)
                if img is None:
                    img = bpy.data.images.load(tpath)
                    img.name = iname
                elif img.filepath != tpath:
                    # had to add this check for autopacking files...
                    if img.packed_file is not None:
                        img.unpack(method='USE_ORIGINAL')
                    img.filepath = tpath
                    img.reload()
                img.colorspace_settings.name = 'Linear'
            i += 1
    # print('previews loaded')


#  line splitting for longer texts...
def split_subs(text, threshold=40):
    if text == '':
        return []
    # temporarily disable this, to be able to do this in drawing code

    text = text.rstrip()
    text = text.replace('\r\n', '\n')

    lines = []

    while len(text) > threshold:
        #first handle if there's an \n line ending
        i_rn = text.find('\n')
        if 1 < i_rn < threshold:
            i = i_rn
            text = text.replace('\n','',1)
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


def fmt_length(prop):
    prop = str(round(prop, 2)) + 'm'
    return prop


def has(mdata, prop):
    if mdata.get(prop) is not None and mdata[prop] is not None and mdata[prop] is not False:
        return True
    else:
        return False


def params_to_dict(params):
    params_dict = {}
    for p in params:
        params_dict[p['parameterType']] = p['value']
    return params_dict


def generate_tooltip(mdata):
    col_w = 40
    if type(mdata['parameters']) == list:
        mparams = params_to_dict(mdata['parameters'])
    else:
        mparams = mdata['parameters']
    t = ''
    t = writeblock(t, mdata['name'], width=col_w)
    t += '\n'

    t = writeblockm(t, mdata, key='description', pretext='', width=col_w)
    if mdata['description'] != '':
        t += '\n'

    bools = (('rig', None), ('animated', None), ('manifold', 'non-manifold'), ('scene', None), ('simulation', None),
             ('uv', None))
    for b in bools:
        if mparams.get(b[0]):
            mdata['tags'].append(b[0])
        elif b[1] != None:
            mdata['tags'].append(b[1])

    bools_data = ('adult',)
    for b in bools_data:
        if mdata.get(b) and mdata[b]:
            mdata['tags'].append(b)
    t = writeblockm(t, mparams, key='designer', pretext='designer', width=col_w)
    t = writeblockm(t, mparams, key='manufacturer', pretext='manufacturer', width=col_w)
    t = writeblockm(t, mparams, key='designCollection', pretext='design collection', width=col_w)

    # t = writeblockm(t, mparams, key='engines', pretext='engine', width = col_w)
    # t = writeblockm(t, mparams, key='model_style', pretext='style', width = col_w)
    # t = writeblockm(t, mparams, key='material_style', pretext='style', width = col_w)
    # t = writeblockm(t, mdata, key='tags', width = col_w)
    # t = writeblockm(t, mparams, key='condition', pretext='condition', width = col_w)
    # t = writeblockm(t, mparams, key='productionLevel', pretext='production level', width = col_w)
    if has(mdata, 'purePbr'):
        t = writeblockm(t, mparams, key='pbrType', pretext='pbr', width=col_w)

    t = writeblockm(t, mparams, key='designYear', pretext='design year', width=col_w)

    if has(mparams, 'dimensionX'):
        t += 'size: %s, %s, %s\n' % (fmt_length(mparams['dimensionX']),
                                     fmt_length(mparams['dimensionY']),
                                     fmt_length(mparams['dimensionZ']))
    if has(mparams, 'faceCount'):
        t += 'face count: %s, render: %s\n' % (mparams['faceCount'], mparams['faceCountRender'])

    # t = writeblockm(t, mparams, key='meshPolyType', pretext='mesh type', width = col_w)
    # t = writeblockm(t, mparams, key='objectCount', pretext='nubmber of objects', width = col_w)

    # t = writeblockm(t, mparams, key='materials', width = col_w)
    # t = writeblockm(t, mparams, key='modifiers', width = col_w)
    # t = writeblockm(t, mparams, key='shaders', width = col_w)

    if has(mparams, 'textureSizeMeters'):
        t += 'texture size: %s\n' % fmt_length(mparams['textureSizeMeters'])

    if has(mparams, 'textureResolutionMax') and mparams['textureResolutionMax'] > 0:
        if mparams['textureResolutionMin'] == mparams['textureResolutionMax']:
            t = writeblockm(t, mparams, key='textureResolutionMin', pretext='texture resolution', width=col_w)
        else:
            t += 'tex resolution: %i - %i\n' % (mparams['textureResolutionMin'], mparams['textureResolutionMax'])

    if has(mparams, 'thumbnailScale'):
        t = writeblockm(t, mparams, key='thumbnailScale', pretext='preview scale', width=col_w)

    # t += 'uv: %s\n' % mdata['uv']
    # t += '\n'
    # t = writeblockm(t, mdata, key='license', width = col_w)

    # generator is for both upload preview and search, this is only after search
    # if mdata.get('versionNumber'):
    #     # t = writeblockm(t, mdata, key='versionNumber', pretext='version', width = col_w)
    #     a_id = mdata['author'].get('id')
    #     if a_id != None:
    #         adata = bpy.context.window_manager['bkit authors'].get(str(a_id))
    #         if adata != None:
    #             t += generate_author_textblock(adata)

    # t += '\n'
    if len(t.split('\n')) < 6:
        t += '\n'
        t += get_random_tip(mdata)
        t += '\n'
    return t


def get_random_tip(mdata):
    t = ''
    rtips = ['Click or drag model or material in scene to link/append ',
             "Click on brushes to link them into scene.",
             "All materials are free.",
             "All brushes are free.",
             "Locked models are available if you subscribe to Full plan.",
             "Login to upload your own models, materials or brushes.",
             "Use 'A' key to search assets by same author.",
             "Use 'W' key to open Authors webpage.", ]
    tip = 'Tip: ' + random.choice(rtips)
    t = writeblock(t, tip)
    return t
    # at = mdata['assetType']
    # if at == 'brush' or at == 'texture':
    #     t += 'click to link %s' % mdata['assetType']
    # if at == 'model' or at == 'material':
    #     tips = ['Click or drag in scene to link/append %s' % mdata['assetType'],
    #             "'A' key to search assets by same author",
    #             "'W' key to open Authors webpage",
    #             ]
    #     tip = 'Tip: ' + random.choice(tips)
    #     t = writeblock(t, tip)
    return t


def generate_author_textblock(adata):
    t = '\n\n\n'

    if adata not in (None, ''):
        col_w = 40
        if len(adata['firstName'] + adata['lastName']) > 0:
            t = 'Author:\n'
            t += '%s %s\n' % (adata['firstName'], adata['lastName'])
            t += '\n'
            if adata.get('aboutMeUrl') is not None:
                t = writeblockm(t, adata, key='aboutMeUrl', pretext='', width=col_w)
                t += '\n'
            if adata.get('aboutMe') is not None:
                t = writeblockm(t, adata, key='aboutMe', pretext='', width=col_w)
                t += '\n'
    return t


def get_items_models(self, context):
    global search_items_models
    return search_items_models


def get_items_brushes(self, context):
    global search_items_brushes
    return search_items_brushes


def get_items_materials(self, context):
    global search_items_materials
    return search_items_materials


def get_items_textures(self, context):
    global search_items_textures
    return search_items_textures


class ThumbDownloader(threading.Thread):
    query = None

    def __init__(self, url, path):
        super(ThumbDownloader, self).__init__()
        self.url = url
        self.path = path
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        r = rerequests.get(self.url, stream=False)
        if r.status_code == 200:
            with open(self.path, 'wb') as f:
                f.write(r.content)
            # ORIGINALLY WE DOWNLOADED THUMBNAILS AS STREAM, BUT THIS WAS TOO SLOW.
            # with open(path, 'wb') as f:
            #     for chunk in r.iter_content(1048576*4):
            #         f.write(chunk)


def write_author(a_id, adata):
    # utils.p('writing author back')
    authors = bpy.context.window_manager['bkit authors']
    if authors.get(a_id) in (None, ''):
        adata['tooltip'] = generate_author_textblock(adata)
        authors[a_id] = adata


def fetch_author(a_id, api_key):
    utils.p('fetch author')
    try:
        a_url = paths.get_api_url() + 'accounts/' + a_id + '/'
        headers = utils.get_headers(api_key)
        r = rerequests.get(a_url, headers=headers)
        if r.status_code == 200:
            adata = r.json()
            if not hasattr(adata, 'id'):
                utils.p(adata)
            # utils.p(adata)
            tasks_queue.add_task((write_author, (a_id, adata)))
            if adata.get('gravatarHash') is not None:
                gravatar_path = paths.get_temp_dir(subdir='g/') + adata['gravatarHash'] + '.jpg'
                url = "https://www.gravatar.com/avatar/" + adata['gravatarHash'] + '?d=404'
                r = rerequests.get(url, stream=False)
                if r.status_code == 200:
                    with open(gravatar_path, 'wb') as f:
                        f.write(r.content)
                    adata['gravatarImg'] = gravatar_path
                elif r.status_code == '404':
                    adata['gravatarHash'] = None
                    utils.p('gravatar for author not available.')
    except Exception as e:
        utils.p(e)
    utils.p('finish fetch')

# profile_counter =0

def get_author(r):
    a_id = str(r['author']['id'])
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    authors = bpy.context.window_manager.get('bkit authors', {})
    if authors == {}:
        bpy.context.window_manager['bkit authors'] = authors
    a = authors.get(a_id)
    if a is None:# or a is '' or (a.get('gravatarHash') is not None and a.get('gravatarImg') is None):
        authors[a_id] = ''
        thread = threading.Thread(target=fetch_author, args=(a_id, preferences.api_key), daemon=True)
        thread.start()
        # global profile_counter
        # profile_counter+=1
        # print(profile_counter,'author:', a_id)
    return a


def write_profile(adata):
    utils.p('writing profile')
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
        utils.p(e)



def get_profile():
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    a = bpy.context.window_manager.get('bkit profile')
    thread = threading.Thread(target=fetch_profile, args=(preferences.api_key,), daemon=True)
    thread.start()
    return a

def profile_is_validator():
    a = bpy.context.window_manager.get('bkit profile')
    if a is not None and a['user'].get('exmenu'):
        return True
    return False

class Searcher(threading.Thread):
    query = None

    def __init__(self, query, params):
        super(Searcher, self).__init__()
        self.query = query
        self.params = params
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        maxthreads = 50
        query = self.query
        params = self.params
        global reports

        t = time.time()
        mt('search thread started')
        tempdir = paths.get_temp_dir('%s_search' % query['asset_type'])
        json_filepath = os.path.join(tempdir, '%s_searchresult.json' % query['asset_type'])

        headers = utils.get_headers(params['api_key'])

        rdata = {}
        rdata['results'] = []

        if params['get_next']:
            with open(json_filepath, 'r') as infile:
                try:
                    origdata = json.load(infile)
                    urlquery = origdata['next']
                    if urlquery == None:
                        return;
                except:
                    # in case no search results found on drive we don't do next page loading.
                    params['get_next'] = False
        if not params['get_next']:
            # build a new request
            url = paths.get_api_url() + 'search/'

            # build request manually
            # TODO use real queries
            requeststring = '?query=' + query['keywords'].lower() + '+'
            #
            for i, q in enumerate(query):
                requeststring += q + ':' + str(query[q]).lower()
                if i < len(query) - 1:
                    requeststring += '+'

            # result ordering: _score - relevance, score - BlenderKit score
            #first condition assumes no keywords and no category, thus an empty search that is triggered on start.
            if query['keywords'] == '' and query.get('category_subtree') == None:
                requeststring += '+order:-created'
            elif query.get('author_id') is not None and profile_is_validator():
                requeststring += '+order:-created'
            else:
                if query.get('category_subtree') is not None:
                    requeststring += '+order:-score,_score'
                else:
                    requeststring += '+order:_score'

            requeststring += '&addon_version=%s' % params['addon_version']
            if params.get('scene_uuid') is not None:
                requeststring += '&scene_uuid=%s' % params['scene_uuid']

            urlquery = url + requeststring
        try:
            utils.p(urlquery)
            r = rerequests.get(urlquery, headers=headers)
            reports = ''
            # utils.p(r.text)
        except requests.exceptions.RequestException as e:
            print(e)
            reports = e
            # props.report = e
            return
        mt('response is back ')
        try:
            rdata = r.json()
        except Exception as inst:
            reports = r.text
            print(inst)

        mt('data parsed ')

        # filter results here:
        # todo remove this in future
        nresults = []
        for d in rdata.get('results', []):
            # TODO this code is for filtering brush types, should vanish after we implement filter in Elastic
            mode = None
            if query['asset_type'] == 'brush':
                for p in d['parameters']:
                    if p['parameterType'] == 'mode':
                        mode = p['value']
            if query['asset_type'] != 'brush' or (
                    query.get('brushType') != None and query['brushType']) == mode:
                nresults.append(d)
        rdata['results'] = nresults

        # print('number of results: ', len(rdata.get('results', [])))
        if self.stopped():
            utils.p('stopping search : ' + query['keywords'])
            return

        mt('search finished')
        i = 0

        thumb_small_urls = []
        thumb_small_filepaths = []
        thumb_full_urls = []
        thumb_full_filepaths = []
        # END OF PARSING
        getting_authors = {}
        for d in rdata.get('results', []):
            if getting_authors.get(d['author']['id']) is None:
                get_author(d)
                getting_authors[d['author']['id']] = True

            for f in d['files']:
                # TODO move validation of published assets to server, too manmy checks here.
                if f['fileType'] == 'thumbnail' and f['fileThumbnail'] != None and f['fileThumbnailLarge'] != None:
                    if f['fileThumbnail'] == None:
                        f['fileThumbnail'] = 'NONE'
                    if f['fileThumbnailLarge'] == None:
                        f['fileThumbnailLarge'] = 'NONE'

                    thumb_small_urls.append(f['fileThumbnail'])
                    thumb_full_urls.append(f['fileThumbnailLarge'])

                    imgname = paths.extract_filename_from_url(f['fileThumbnail'])
                    imgpath = os.path.join(tempdir, imgname)
                    thumb_small_filepaths.append(imgpath)

                    imgname = paths.extract_filename_from_url(f['fileThumbnailLarge'])
                    imgpath = os.path.join(tempdir, imgname)
                    thumb_full_filepaths.append(imgpath)

        sml_thbs = zip(thumb_small_filepaths, thumb_small_urls)
        full_thbs = zip(thumb_full_filepaths, thumb_full_urls)

        # we save here because a missing thumbnail check is in the previous loop
        # we can also prepend previous results. These have downloaded thumbnails already...
        if params['get_next']:
            rdata['results'][0:0] = origdata['results']

        with open(json_filepath, 'w') as outfile:
            json.dump(rdata, outfile)

        killthreads_sml = []
        for k in thumb_sml_download_threads.keys():
            if k not in thumb_small_filepaths:
                killthreads_sml.append(k)  # do actual killing here?

        killthreads_full = []
        for k in thumb_full_download_threads.keys():
            if k not in thumb_full_filepaths:
                killthreads_full.append(k)  # do actual killing here?
        # TODO do the killing/ stopping here! remember threads might have finished inbetween!

        if self.stopped():
            utils.p('stopping search : ' + query['keywords'])
            return

        # this loop handles downloading of small thumbnails
        for imgpath, url in sml_thbs:
            if imgpath not in thumb_sml_download_threads and not os.path.exists(imgpath):
                thread = ThumbDownloader(url, imgpath)
                # thread = threading.Thread(target=download_thumbnail, args=([url, imgpath]),
                #                           daemon=True)
                thread.start()
                thumb_sml_download_threads[imgpath] = thread
                # threads.append(thread)

                if len(thumb_sml_download_threads) > maxthreads:
                    while len(thumb_sml_download_threads) > maxthreads:
                        threads_copy = thumb_sml_download_threads.copy()  # because for loop can erase some of the items.
                        for tk, thread in threads_copy.items():
                            if not thread.is_alive():
                                thread.join()
                                # utils.p(x)
                                del (thumb_sml_download_threads[tk])
                                # utils.p('fetched thumbnail ', i)
                                i += 1
        if self.stopped():
            utils.p('stopping search : ' + query['keywords'])
            return
        idx = 0
        while len(thumb_sml_download_threads) > 0:
            threads_copy = thumb_sml_download_threads.copy()  # because for loop can erase some of the items.
            for tk, thread in threads_copy.items():
                if not thread.is_alive():
                    thread.join()
                    del (thumb_sml_download_threads[tk])
                    i += 1

        if self.stopped():
            utils.p('stopping search : ' + query['keywords'])
            return

        # start downloading full thumbs in the end
        for imgpath, url in full_thbs:
            if imgpath not in thumb_full_download_threads and not os.path.exists(imgpath):
                thread = ThumbDownloader(url, imgpath)
                # thread = threading.Thread(target=download_thumbnail, args=([url, imgpath]),
                #                           daemon=True)
                thread.start()
                thumb_full_download_threads[imgpath] = thread
        mt('thumbnails finished')


def build_query_common(query, props):
    query_common = {
        "keywords": props.search_keywords
    }
    query.update(query_common)


# def query_add_range(query, name, rmin, rmax):

def build_query_model():
    '''use all search input to request results from server'''

    props = bpy.context.scene.blenderkit_models
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

    if props.free_only:
        query["is_free"] = True

    if props.search_advanced:
        if props.search_condition != 'UNSPECIFIED':
            query["condition"] = props.search_condition
        if props.search_design_year:
            query["designYearMin"] = props.search_design_year_min
            query["designYearMax"] = props.search_design_year_max
        if props.search_polycount:
            query["polyCountMin"] = props.search_polycount_min
            query["polyCountMax"] = props.search_polycount_max
        if props.search_texture_resolution:
            query["textureResolutionMin"] = props.search_texture_resolution_min
            query["textureResolutionMax"] = props.search_texture_resolution_max

    build_query_common(query, props)

    return query


def build_query_scene():
    '''use all search input to request results from server'''

    props = bpy.context.scene.blenderkit_scene
    query = {
        "asset_type": 'scene',
        # "engine": props.search_engine,
        # "adult": props.search_adult,
    }
    build_query_common(query, props)
    return query


def build_query_material():
    props = bpy.context.scene.blenderkit_mat
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
    props = bpy.context.scene.blenderkit_brush

    brush_type = ''
    if bpy.context.sculpt_object is not None:
        brush_type = 'sculpt'

    elif bpy.context.image_paint_object:  # could be just else, but for future p
        brush_type = 'texture_paint'

    query = {
        "asset_type": 'brush',

        "brushType": brush_type
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
    global search_threads

    while (len(search_threads) > 0):
        old_thread = search_threads.pop(0)
        old_thread[0].stop()
        # TODO CARE HERE FOR ALSO KILLING THE THREADS...AT LEAST NOW SEARCH DONE FIRST WON'T REWRITE AN OLDER ONE

    tempdir = paths.get_temp_dir('%s_search' % query['asset_type'])
    thread = Searcher(query, params)
    thread.start()

    search_threads.append([thread, tempdir, query['asset_type']])

    mt('thread started')


def search(category='', get_next=False, author_id=''):
    ''' initialize searching'''
    global search_start_time
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    search_start_time = time.time()
    mt('start')
    scene = bpy.context.scene
    uiprops = scene.blenderkitUI

    if uiprops.asset_type == 'MODEL':
        if not hasattr(scene, 'blenderkit'):
            return;
        props = scene.blenderkit_models
        query = build_query_model()

    if uiprops.asset_type == 'SCENE':
        if not hasattr(scene, 'blenderkit_scene'):
            return;
        props = scene.blenderkit_scene
        query = build_query_scene()

    if uiprops.asset_type == 'MATERIAL':
        if not hasattr(scene, 'blenderkit_mat'):
            return;
        props = scene.blenderkit_mat
        query = build_query_material()

    if uiprops.asset_type == 'TEXTURE':
        if not hasattr(scene, 'blenderkit_tex'):
            return;
        # props = scene.blenderkit_tex
        # query = build_query_texture()

    if uiprops.asset_type == 'BRUSH':
        if not hasattr(scene, 'blenderkit_brush'):
            return;
        props = scene.blenderkit_brush
        query = build_query_brush()

    if props.is_searching and get_next == True:
        return;

    if category != '':
        query['category_subtree'] = category

    if author_id != '':
        query['author_id'] = author_id

    # utils.p('searching')
    props.is_searching = True

    params = {
        'scene_uuid': bpy.context.scene.get('uuid', None),
        'addon_version': version_checker.get_addon_version(),
        'api_key': user_preferences.api_key,
        'get_next': get_next
    }

    # if free_only:
    #     query['keywords'] += '+is_free:true'

    add_search_process(query, params)
    tasks_queue.add_task((ui.add_report, ('BlenderKit searching....', 2)))

    props.report = 'BlenderKit searching....'


def search_update(self, context):
    utils.p('search updater')
    #if self.search_keywords != '':
    ui_props = bpy.context.scene.blenderkitUI
    if ui_props.down_up != 'SEARCH':
        ui_props.down_up = 'SEARCH'

    search()


class SearchOperator(Operator):
    """Tooltip"""
    bl_idname = "view3d.blenderkit_search"
    bl_label = "BlenderKit asset search"
    bl_description = "Search online for assets"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    own: BoolProperty(name="own assets only",
                      description="Find all own assets",
                      default=False)

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

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # TODO ; this should all get transferred to properties of the search operator, so sprops don't have to be fetched here at all.
        sprops = utils.get_search_props()
        if self.author_id != '':
            sprops.search_keywords = ''
        if self.keywords != '':
            sprops.search_keywords = self.keywords

        search(category=self.category, get_next=self.get_next, author_id=self.author_id)
        # bpy.ops.view3d.blenderkit_asset_bar()

        return {'FINISHED'}


classes = [
    SearchOperator
]


def register_search():
    bpy.app.handlers.load_post.append(scene_load)

    for c in classes:
        bpy.utils.register_class(c)

    bpy.app.timers.register(timer_update, persistent=True)

    categories.load_categories()


def unregister_search():
    bpy.app.handlers.load_post.remove(scene_load)

    for c in classes:
        bpy.utils.unregister_class(c)
    if bpy.app.timers.is_registered(timer_update):
        bpy.app.timers.unregister(timer_update)
