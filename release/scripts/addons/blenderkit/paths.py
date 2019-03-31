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

import bpy, os, sys

BLENDERKIT_API_LOCAL = "http://localhost:8001/api/v1/"
BLENDERKIT_API_MAIN = "https://www.blenderkit.com/api/v1/"
BLENDERKIT_API_DEVEL = "https://devel.blenderkit.com/api/v1/"
BLENDERKIT_REPORT_URL = "usage_report/"
BLENDERKIT_USER_ASSETS = "https://www.blenderkit.com/my-assets"
BLENDERKIT_PLANS = "https://www.blenderkit.com/plans/pricing/"
BLENDERKIT_MANUAL = "https://youtu.be/1hVgcQhIAo8"
BLENDERKIT_MODEL_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/upload/"
BLENDERKIT_MATERIAL_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/uploading-material/"
BLENDERKIT_SIGNUP_URL = "https://www.blenderkit.com/accounts/register/"
BLENDERKIT_ADDON_URL = "https://www.blenderkit.com/api/v1/assets/6923b215-7df0-46f3-95ae-a2b5ff44ddd5/"
BLENDERKIT_ADDON_FILE_URL = "https://www.blenderkit.com/get-blenderkit/"
_presets = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets")
BLENDERKIT_SETTINGS_FILENAME = os.path.join(_presets, "bkit.json")


def get_bkit_url():
    d = bpy.app.debug_value
    # d = 2
    if d == 1:
        url = BLENDERKIT_API_LOCAL
    elif d == 2:
        url = BLENDERKIT_API_DEVEL
    else:
        url = BLENDERKIT_API_MAIN
    return url


def get_categories_filepath():
    tempdir = get_temp_dir()
    return os.path.join(tempdir, 'categories.json')


def get_temp_dir(subdir=None):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    # tempdir = user_preferences.temp_dir
    tempdir = os.path.join(user_preferences.global_dir, 'temp')
    if tempdir.startswith('//'):
        tempdir = bpy.path.abspath(tempdir)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    if subdir is not None:
        tempdir = tempdir + os.sep + subdir
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
    return tempdir


def get_download_dirs(asset_type):
    ''' get directories where assets will be downloaded'''
    subdmapping = {'brush': 'brushes', 'texture': 'textures', 'model': 'models', 'scene': 'scenes',
                   'material': 'materials'}

    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    dirs = []
    if user_preferences.directory_behaviour == 'BOTH' or 'GLOBAL':
        ddir = user_preferences.global_dir
        if ddir.startswith('//'):
            ddir = bpy.path.abspath(ddir)
        if not os.path.exists(ddir):
            os.makedirs(ddir)

        subdirs = ['brushes', 'textures', 'models', 'scenes', 'materials']
        for subd in subdirs:
            subdir = ddir + os.sep + subd
            if not os.path.exists(subdir):
                os.makedirs(subdir)
            if subdmapping[asset_type] == subd:
                dirs.append(subdir)
    if (
            user_preferences.directory_behaviour == 'BOTH' or user_preferences.directory_behaviour == 'LOCAL') and bpy.data.is_saved:  # it's important local get's solved as second, since for the linking process only last filename will be taken. For download process first name will be taken and if 2 filenames were returned, file will be copied to the 2nd path.
        ddir = user_preferences.project_subdir
        if ddir.startswith('//'):
            ddir = bpy.path.abspath(ddir)
            if not os.path.exists(ddir):
                os.makedirs(ddir)

        subdirs = ['textures', 'models', 'scenes', 'materials']  # brushes get stored only globally.
        for subd in subdirs:
            subdir = ddir + os.sep + subd
            if not os.path.exists(subdir):
                os.makedirs(subdir)
            if subdmapping[asset_type] == subd:
                dirs.append(subdir)

    return dirs


def slugify(slug):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """

    import unicodedata, re
    slug = slug.lower()
    slug.replace('.', '_')
    slug = slug.replace(' ', '_')
    # import re
    # slug = unicodedata.normalize('NFKD', slug)
    # slug = slug.encode('ascii', 'ignore').lower()
    slug = re.sub(r'[^a-z0-9]+.- ', '-', slug).strip('-')
    slug = re.sub(r'[-]+', '-', slug)
    slug = re.sub(r'/', '_', slug)
    return slug


def extract_filename_from_url(url):
    if url is not None:
        imgname = url.split('/')[-1]
        imgname = imgname.split('?')[0]
        return imgname
    return ''


def get_download_filenames(asset_data):
    dirs = get_download_dirs(asset_data['asset_type'])
    file_names = []
    # fn = asset_data['file_name'].replace('blend_', '')
    if asset_data.get('url') is not None:
        # this means asset is allready in scene and we don't nedd to check

        fn = extract_filename_from_url(asset_data['url'])
        fn.replace('_blend', '')
        n = slugify(asset_data['name']) + '_' + fn
        # n = 'x.blend'
        # strs = (n, asset_data['name'], asset_data['file_name'])
        for d in dirs:
            file_name = os.path.join(d, n)
            file_names.append(file_name)
    return file_names


def delete_asset_debug(asset_data):
    from blenderkit import download
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key

    download.get_download_url(asset_data, download.get_scene_id(), api_key)

    file_names = get_download_filenames(asset_data)
    for f in file_names:
        if os.path.isfile(f):
            try:
                print(f)
                os.remove(f)
            except:
                e = sys.exc_info()[0]
                print(e)
                pass;


def get_clean_filepath():
    script_path = os.path.dirname(os.path.realpath(__file__))
    subpath = "blendfiles" + os.sep + "cleaned.blend"
    cp = os.path.join(script_path, subpath)
    return cp


def get_thumbnailer_filepath():
    script_path = os.path.dirname(os.path.realpath(__file__))
    # fpath = os.path.join(p, subpath)
    subpath = "blendfiles" + os.sep + "thumbnailer.blend"
    return os.path.join(script_path, subpath)


def get_material_thumbnailer_filepath():
    script_path = os.path.dirname(os.path.realpath(__file__))
    # fpath = os.path.join(p, subpath)
    subpath = "blendfiles" + os.sep + "material_thumbnailer_cycles.blend"
    return os.path.join(script_path, subpath)
    """
    for p in bpy.utils.script_paths():
        testfname= os.path.join(p, subpath)#p + '%saddons%sobject_fracture%sdata.blend' % (s,s,s)
        if os.path.isfile( testfname):
            fname=testfname
            return(fname)
    return None
    """


def get_addon_file(subpath=''):
    script_path = os.path.dirname(os.path.realpath(__file__))
    # fpath = os.path.join(p, subpath)
    return os.path.join(script_path, subpath)


def get_addon_thumbnail_path(name):
    script_path = os.path.dirname(os.path.realpath(__file__))
    # fpath = os.path.join(p, subpath)
    ext = name.split('.')[-1]
    next = ''
    if not (ext == 'jpg' or ext == 'png'):  # allready has ext?
        next = '.jpg'
    subpath = "thumbnails" + os.sep + name + next
    return os.path.join(script_path, subpath)
