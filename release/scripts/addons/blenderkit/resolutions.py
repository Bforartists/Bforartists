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


from blenderkit import paths, append_link, bg_blender, utils, download, search, rerequests, upload_bg, image_utils

import sys, json, os, time
import subprocess
import tempfile
import bpy
import requests
import math
import threading

resolutions = {
    'resolution_0_5K': 512,
    'resolution_1K': 1024,
    'resolution_2K': 2048,
    'resolution_4K': 4096,
    'resolution_8K': 8192,
}
rkeys = list(resolutions.keys())

resolution_props_to_server = {

    '512': 'resolution_0_5K',
    '1024': 'resolution_1K',
    '2048': 'resolution_2K',
    '4096': 'resolution_4K',
    '8192': 'resolution_8K',
    'ORIGINAL': 'blend',
}


def get_current_resolution():
    actres = 0
    for i in bpy.data.images:
        if i.name != 'Render Result':
            actres = max(actres, i.size[0], i.size[1])
    return actres


def save_image_safely(teximage, filepath):
    '''
    Blender makes it really hard to save images...
    Would be worth investigating PIL or similar instead
    Parameters
    ----------
    teximage

    Returns
    -------

    '''
    JPEG_QUALITY = 98

    rs = bpy.context.scene.render
    ims = rs.image_settings

    orig_file_format = ims.file_format
    orig_quality = ims.quality
    orig_color_mode = ims.color_mode
    orig_compression = ims.compression

    ims.file_format = teximage.file_format
    if teximage.file_format == 'PNG':
        ims.color_mode = 'RGBA'
    elif teximage.channels == 3:
        ims.color_mode = 'RGB'
    else:
        ims.color_mode = 'BW'

    # all pngs with max compression
    if ims.file_format == 'PNG':
        ims.compression = 100
    # all jpgs brought to reasonable quality
    if ims.file_format == 'JPG':
        ims.quality = JPEG_QUALITY
    # it's actually very important not to try to change the image filepath and packed file filepath before saving,
    # blender tries to re-pack the image after writing to image.packed_image.filepath and reverts any changes.
    teximage.save_render(filepath=bpy.path.abspath(filepath), scene=bpy.context.scene)

    teximage.filepath = filepath
    for packed_file in teximage.packed_files:
        packed_file.filepath = filepath
    teximage.filepath_raw = filepath
    teximage.reload()

    ims.file_format = orig_file_format
    ims.quality = orig_quality
    ims.color_mode = orig_color_mode
    ims.compression = orig_compression


def extxchange_to_resolution(filepath):
    base, ext = os.path.splitext(filepath)
    if ext in ('.png', '.PNG'):
        ext = 'jpg'






def upload_resolutions(files, asset_data):
    preferences = bpy.context.preferences.addons['blenderkit'].preferences

    upload_data = {
        "name": asset_data['name'],
        "token": preferences.api_key,
        "id": asset_data['id']
    }

    uploaded = upload_bg.upload_files(upload_data, files)

    if uploaded:
        bg_blender.progress('upload finished successfully')
    else:
        bg_blender.progress('upload failed.')


def unpack_asset(data):
    utils.p('unpacking asset')
    asset_data = data['asset_data']
    # utils.pprint(asset_data)

    blend_file_name = os.path.basename(bpy.data.filepath)
    ext = os.path.splitext(blend_file_name)[1]

    resolution = asset_data.get('resolution', 'blend')
    # TODO - passing resolution inside asset data might not be the best solution
    tex_dir_path = paths.get_texture_directory(asset_data, resolution=resolution)
    tex_dir_abs = bpy.path.abspath(tex_dir_path)
    if not os.path.exists(tex_dir_abs):
        try:
            os.mkdir(tex_dir_abs)
        except Exception as e:
            print(e)
    bpy.data.use_autopack = False
    for image in bpy.data.images:
        if image.name != 'Render Result':
            # suffix = paths.resolution_suffix(data['suffix'])
            fp = get_texture_filepath(tex_dir_path, image, resolution=resolution)
            utils.p('unpacking file', image.name)
            utils.p(image.filepath, fp)

            for pf in image.packed_files:
                pf.filepath = fp  # bpy.path.abspath(fp)
            image.filepath = fp  # bpy.path.abspath(fp)
            image.filepath_raw = fp  # bpy.path.abspath(fp)
            # image.save()
            if len(image.packed_files) > 0:
                # image.unpack(method='REMOVE')
                image.unpack(method='WRITE_ORIGINAL')

    bpy.ops.wm.save_mainfile(compress=False)
    # now try to delete the .blend1 file
    try:
        os.remove(bpy.data.filepath + '1')
    except Exception as e:
        print(e)


def patch_asset_empty(asset_id, api_key):
    '''
        This function patches the asset for the purpose of it getting a reindex.
        Should be removed once this is fixed on the server and
        the server is able to reindex after uploads of resolutions
        Returns
        -------
    '''
    upload_data = {
    }
    url = paths.get_api_url() + 'assets/' + str(asset_id) + '/'
    headers = utils.get_headers(api_key)
    try:
        r = rerequests.patch(url, json=upload_data, headers=headers, verify=True)  # files = files,
    except requests.exceptions.RequestException as e:
        print(e)
        return {'CANCELLED'}
    return {'FINISHED'}


def reduce_all_images(target_scale=1024):
    for img in bpy.data.images:
        if img.name != 'Render Result':
            print('scaling ', img.name, img.size[0], img.size[1])
            # make_possible_reductions_on_image(i)
            if max(img.size) > target_scale:
                ratio = float(target_scale) / float(max(img.size))
                print(ratio)
                # i.save()
                fp = '//tempimagestorage'
                # print('generated filename',fp)
                # for pf in img.packed_files:
                #     pf.filepath = fp  # bpy.path.abspath(fp)

                img.filepath = fp
                img.filepath_raw = fp
                print(int(img.size[0] * ratio), int(img.size[1] * ratio))
                img.scale(int(img.size[0] * ratio), int(img.size[1] * ratio))
                img.update()
                # img.save()
                # img.reload()
                img.pack()


def get_texture_filepath(tex_dir_path, image, resolution='blend'):
    image_file_name = bpy.path.basename(image.filepath)
    if image_file_name == '':
        image_file_name = image.name.split('.')[0]

    suffix = paths.resolution_suffix[resolution]

    fp = os.path.join(tex_dir_path, image_file_name)
    # check if there is allready an image with same name and thus also assigned path
    # (can happen easily with genearted tex sets and more materials)
    done = False
    fpn = fp
    i = 0
    while not done:
        is_solo = True
        for image1 in bpy.data.images:
            if image != image1 and image1.filepath == fpn:
                is_solo = False
                fpleft, fpext = os.path.splitext(fp)
                fpn = fpleft + str(i).zfill(3) + fpext
                i += 1
        if is_solo:
            done = True

    return fpn


def generate_lower_resolutions_hdr(asset_data, fpath):
    '''generates lower resolutions for HDR images'''
    hdr = bpy.data.images.load(fpath)
    actres = max(hdr.size[0], hdr.size[1])
    p2res = paths.round_to_closest_resolution(actres)
    original_filesize = os.path.getsize(fpath) # for comparison on the original level
    i = 0
    finished = False
    files = []
    while not finished:
        dirn = os.path.dirname(fpath)
        fn_strip, ext = os.path.splitext(fpath)
        ext = '.exr'
        if i>0:
            image_utils.downscale(hdr)


        hdr_resolution_filepath = fn_strip + paths.resolution_suffix[p2res] + ext
        image_utils.img_save_as(hdr, filepath=hdr_resolution_filepath, file_format='OPEN_EXR', quality=20, color_mode='RGB', compression=15,
                    view_transform='Raw', exr_codec = 'DWAA')

        if os.path.exists(hdr_resolution_filepath):
            reduced_filesize = os.path.getsize(hdr_resolution_filepath)

        # compare file sizes
        print(f'HDR size was reduced from {original_filesize} to {reduced_filesize}')
        if reduced_filesize < original_filesize:
            # this limits from uploaidng especially same-as-original resolution files in case when there is no advantage.
            # usually however the advantage can be big also for same as original resolution
            files.append({
                "type": p2res,
                "index": 0,
                "file_path": hdr_resolution_filepath
            })

            print('prepared resolution file: ', p2res)

        if rkeys.index(p2res) == 0:
            finished = True
        else:
            p2res = rkeys[rkeys.index(p2res) - 1]
        i+=1

    print('uploading resolution files')
    upload_resolutions(files, asset_data)

    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    patch_asset_empty(asset_data['id'], preferences.api_key)


def generate_lower_resolutions(data):
    asset_data = data['asset_data']
    actres = get_current_resolution()
    # first let's skip procedural assets
    base_fpath = bpy.data.filepath

    s = bpy.context.scene

    print('current resolution of the asset ', actres)
    if actres > 0:
        p2res = paths.round_to_closest_resolution(actres)
        orig_res = p2res
        print(p2res)
        finished = False
        files = []
        # now skip assets that have lowest possible resolution already
        if p2res != [0]:
            original_textures_filesize = 0
            for i in bpy.data.images:
                abspath = bpy.path.abspath(i.filepath)
                if os.path.exists(abspath):
                    original_textures_filesize += os.path.getsize(abspath)

            while not finished:

                blend_file_name = os.path.basename(base_fpath)

                dirn = os.path.dirname(base_fpath)
                fn_strip, ext = os.path.splitext(blend_file_name)

                fn = fn_strip + paths.resolution_suffix[p2res] + ext
                fpath = os.path.join(dirn, fn)

                tex_dir_path = paths.get_texture_directory(asset_data, resolution=p2res)

                tex_dir_abs = bpy.path.abspath(tex_dir_path)
                if not os.path.exists(tex_dir_abs):
                    os.mkdir(tex_dir_abs)

                reduced_textures_filessize = 0
                for i in bpy.data.images:
                    if i.name != 'Render Result':

                        print('scaling ', i.name, i.size[0], i.size[1])
                        fp = get_texture_filepath(tex_dir_path, i, resolution=p2res)

                        if p2res == orig_res:
                            # first, let's link the image back to the original one.
                            i['blenderkit_original_path'] = i.filepath
                            # first round also makes reductions on the image, while keeping resolution
                            image_utils.make_possible_reductions_on_image(i, fp, do_reductions=True, do_downscale=False)

                        else:
                            # lower resolutions only downscale
                            image_utils.make_possible_reductions_on_image(i, fp, do_reductions=False, do_downscale=True)

                        abspath = bpy.path.abspath(i.filepath)
                        if os.path.exists(abspath):
                            reduced_textures_filessize += os.path.getsize(abspath)

                        i.pack()
                # save
                print(fpath)
                # save the file
                bpy.ops.wm.save_as_mainfile(filepath=fpath, compress=True, copy=True)
                # compare file sizes
                print(f'textures size was reduced from {original_textures_filesize} to {reduced_textures_filessize}')
                if reduced_textures_filessize < original_textures_filesize:
                    # this limits from uploaidng especially same-as-original resolution files in case when there is no advantage.
                    # usually however the advantage can be big also for same as original resolution
                    files.append({
                        "type": p2res,
                        "index": 0,
                        "file_path": fpath
                    })

                print('prepared resolution file: ', p2res)
                if rkeys.index(p2res) == 0:
                    finished = True
                else:
                    p2res = rkeys[rkeys.index(p2res) - 1]
            print('uploading resolution files')
            upload_resolutions(files, data['asset_data'])
            preferences = bpy.context.preferences.addons['blenderkit'].preferences
            patch_asset_empty(data['asset_data']['id'], preferences.api_key)
        return


def regenerate_thumbnail_material(data):
    # this should re-generate material thumbnail and re-upload it.
    # first let's skip procedural assets
    base_fpath = bpy.data.filepath
    blend_file_name = os.path.basename(base_fpath)
    bpy.ops.mesh.primitive_cube_add()
    aob = bpy.context.active_object
    bpy.ops.object.material_slot_add()
    aob.material_slots[0].material = bpy.data.materials[0]
    props = aob.active_material.blenderkit
    props.thumbnail_generator_type = 'BALL'
    props.thumbnail_background = False
    props.thumbnail_resolution = '256'
    # layout.prop(props, 'thumbnail_generator_type')
    # layout.prop(props, 'thumbnail_scale')
    # layout.prop(props, 'thumbnail_background')
    # if props.thumbnail_background:
    #     layout.prop(props, 'thumbnail_background_lightness')
    # layout.prop(props, 'thumbnail_resolution')
    # layout.prop(props, 'thumbnail_samples')
    # layout.prop(props, 'thumbnail_denoising')
    # layout.prop(props, 'adaptive_subdivision')
    # preferences = bpy.context.preferences.addons['blenderkit'].preferences
    # layout.prop(preferences, "thumbnail_use_gpu")
    # TODO: here it should call start_material_thumbnailer , but with the wait property on, so it can upload afterwards.
    bpy.ops.object.blenderkit_generate_material_thumbnail()
    time.sleep(130)
    # save
    # this does the actual job

    return


def assets_db_path():
    dpath = os.path.dirname(bpy.data.filepath)
    fpath = os.path.join(dpath, 'all_assets.json')
    return fpath


def get_assets_search():
    # bpy.app.debug_value = 2

    results = []
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    url = paths.get_api_url() + 'search/all'
    i = 0
    while url is not None:
        headers = utils.get_headers(preferences.api_key)
        print('fetching assets from assets endpoint')
        print(url)
        retries = 0
        while retries < 3:
            r = rerequests.get(url, headers=headers)

            try:
                adata = r.json()
                url = adata.get('next')
                print(i)
                i += 1
            except Exception as e:
                print(e)
                print('failed to get next')
                if retries == 2:
                    url = None
            if adata.get('results') != None:
                results.extend(adata['results'])
                retries = 3
            print(f'fetched page {i}')
            retries += 1

    fpath = assets_db_path()
    with open(fpath, 'w', encoding = 'utf-8') as s:
        json.dump(results, s, ensure_ascii=False, indent=4)


def get_assets_for_resolutions(page_size=100, max_results=100000000):
    preferences = bpy.context.preferences.addons['blenderkit'].preferences

    dpath = os.path.dirname(bpy.data.filepath)
    filepath = os.path.join(dpath, 'assets_for_resolutions.json')
    params = {
        'order': '-created',
        'textureResolutionMax_gte': '100',
        #    'last_resolution_upload_lt':'2020-9-01'
    }
    search.get_search_simple(params, filepath=filepath, page_size=page_size, max_results=max_results,
                             api_key=preferences.api_key)
    return filepath


def get_materials_for_validation(page_size=100, max_results=100000000):
    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    dpath = os.path.dirname(bpy.data.filepath)
    filepath = os.path.join(dpath, 'materials_for_validation.json')
    params = {
        'order': '-created',
        'asset_type': 'material',
        'verification_status': 'uploaded'
    }
    search.get_search_simple(params, filepath=filepath, page_size=page_size, max_results=max_results,
                             api_key=preferences.api_key)
    return filepath




def load_assets_list(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as s:
            assets = json.load(s)
    return assets


def check_needs_resolutions(a):
    if a['verificationStatus'] == 'validated' and a['assetType'] in ('material', 'model', 'scene', 'hdr'):
        # the search itself now picks the right assets so there's no need to filter more than asset types.
        # TODO needs to check first if the upload date is older than resolution upload date, for that we need resolution upload date.
        for f in a['files']:
            if f['fileType'].find('resolution') > -1:
                return False

        return True
    return False


def download_asset(asset_data, resolution='blend', unpack=False, api_key=''):
    '''
    Download an asset non-threaded way.
    Parameters
    ----------
    asset_data - search result from elastic or assets endpoints from API

    Returns
    -------
    path to the resulting asset file or None if asset isn't accessible
    '''

    has_url = download.get_download_url(asset_data, download.get_scene_id(), api_key, tcom=None,
                                        resolution='blend')
    if has_url:
        fpath = download.download_asset_file(asset_data, api_key = api_key)
        if fpath and unpack and asset_data['assetType'] != 'hdr':
            send_to_bg(asset_data, fpath, command='unpack', wait=True)
        return fpath

    return None


def generate_resolution_thread(asset_data, api_key):
    '''
    A thread that downloads file and only then starts an instance of Blender that generates the resolution
    Parameters
    ----------
    asset_data

    Returns
    -------

    '''

    fpath = download_asset(asset_data, unpack=True, api_key=api_key)

    if fpath:
        if asset_data['assetType'] != 'hdr':
            print('send to bg ', fpath)
            proc = send_to_bg(asset_data, fpath, command='generate_resolutions', wait=True);
        else:
            generate_lower_resolutions_hdr(asset_data, fpath)
        # send_to_bg by now waits for end of the process.
        # time.sleep((5))


def iterate_for_resolutions(filepath, process_count=12, api_key='', do_checks = True):
    ''' iterate through all assigned assets, check for those which need generation and send them to res gen'''
    assets = load_assets_list(filepath)
    print(len(assets))
    threads = []
    for asset_data in assets:
        asset_data = search.parse_result(asset_data)
        if asset_data is not None:

            if not do_checks or check_needs_resolutions(asset_data):
                print('downloading and generating resolution for  %s' % asset_data['name'])
                # this is just a quick hack for not using original dirs in blendrkit...
                generate_resolution_thread(asset_data, api_key)
                # thread = threading.Thread(target=generate_resolution_thread, args=(asset_data, api_key))
                # thread.start()
                #
                # threads.append(thread)
                # print('processes ', len(threads))
                # while len(threads) > process_count - 1:
                #     for t in threads:
                #         if not t.is_alive():
                #             threads.remove(t)
                #         break;
                # else:
                #     print(f'Failed to generate resolution:{asset_data["name"]}')
            else:
                print('not generated resolutions:', asset_data['name'])


def send_to_bg(asset_data, fpath, command='generate_resolutions', wait=True):
    '''
    Send varioust task to a new blender instance that runs and closes after finishing the task.
    This function waits until the process finishes.
    The function tries to set the same bpy.app.debug_value in the instance of Blender that is run.
    Parameters
    ----------
    asset_data
    fpath - file that will be processed
    command - command which should be run in background.

    Returns
    -------
    None
    '''
    data = {
        'fpath': fpath,
        'debug_value': bpy.app.debug_value,
        'asset_data': asset_data,
        'command': command,
    }
    binary_path = bpy.app.binary_path
    tempdir = tempfile.mkdtemp()
    datafile = os.path.join(tempdir + 'resdata.json')
    script_path = os.path.dirname(os.path.realpath(__file__))
    with open(datafile, 'w', encoding = 'utf-8') as s:
        json.dump(data, s,  ensure_ascii=False, indent=4)

    print('opening Blender instance to do processing - ', command)

    if wait:
        proc = subprocess.run([
            binary_path,
            "--background",
            "-noaudio",
            fpath,
            "--python", os.path.join(script_path, "resolutions_bg.py"),
            "--", datafile
        ], bufsize=1, stdout=sys.stdout, stdin=subprocess.PIPE, creationflags=utils.get_process_flags())

    else:
        # TODO this should be fixed to allow multithreading.
        proc = subprocess.Popen([
            binary_path,
            "--background",
            "-noaudio",
            fpath,
            "--python", os.path.join(script_path, "resolutions_bg.py"),
            "--", datafile
        ], bufsize=1, stdout=subprocess.PIPE, stdin=subprocess.PIPE, creationflags=utils.get_process_flags())
        return proc


def write_data_back(asset_data):
    '''ensures that the data in the resolution file is the same as in the database.'''
    pass;


def run_bg(datafile):
    print('background file operation')
    with open(datafile, 'r',encoding='utf-8') as f:
        data = json.load(f)
    bpy.app.debug_value = data['debug_value']
    write_data_back(data['asset_data'])
    if data['command'] == 'generate_resolutions':
        generate_lower_resolutions(data)
    elif data['command'] == 'unpack':
        unpack_asset(data)
    elif data['command'] == 'regen_thumbnail':
        regenerate_thumbnail_material(data)

# load_assets_list()
# generate_lower_resolutions()
# class TestOperator(bpy.types.Operator):
#     """Tooltip"""
#     bl_idname = "object.test_anything"
#     bl_label = "Test Operator"
#
#     @classmethod
#     def poll(cls, context):
#         return True
#
#     def execute(self, context):
#         iterate_for_resolutions()
#         return {'FINISHED'}
#
#
# def register():
#     bpy.utils.register_class(TestOperator)
#
#
# def unregister():
#     bpy.utils.unregister_class(TestOperator)
