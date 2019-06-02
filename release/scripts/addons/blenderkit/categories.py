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
    tasks_queue = reload(tasks_queue)
else:
    from blenderkit import paths, utils, tasks_queue

import requests
import json
import os
import bpy

import shutil
import threading


def count_to_parent(parent):
    for c in parent['children']:
        count_to_parent(c)
        parent['assetCount'] += c['assetCount']


def fix_category_counts(categories):
    for c in categories:
        count_to_parent(c)


def filter_category(category):
    ''' filter categories with no assets, so they aren't shown in search panel'''
    if category['assetCount'] < 1:
        return True
    else:
        to_remove = []
        for c in category['children']:
            if filter_category(c):
                to_remove.append(c)
        for c in to_remove:
            category['children'].remove(c)


def filter_categories(categories):
    for category in categories:
        filter_category(category)


def get_category(categories, cat_path=()):
    for category in cat_path:
        for c in categories:
            if c['slug'] == category:
                categories = c['children']
                if category == cat_path[-1]:
                    return (c)
                break;


def copy_categories():
    # this creates the categories system on only
    tempdir = paths.get_temp_dir()
    categories_filepath = os.path.join(tempdir, 'categories.json')
    if not os.path.exists(categories_filepath):
        source_path = paths.get_addon_file(subpath='data' + os.sep + 'categories.json')
        # print('attempt to copy categories from: %s to %s' % (categories_filepath, source_path))
        try:
            shutil.copy(source_path, categories_filepath)
        except:
            print("couldn't copy categories file")


def load_categories():
    copy_categories()
    tempdir = paths.get_temp_dir()
    categories_filepath = os.path.join(tempdir, 'categories.json')

    wm = bpy.context.window_manager
    with open(categories_filepath, 'r') as catfile:
        wm['bkit_categories'] = json.load(catfile)

    wm['active_category'] = {
        'MODEL': ['model'],
        'SCENE': ['scene'],
        'MATERIAL': ['material'],
        'BRUSH': ['brush'],
    }


def fetch_categories(API_key):
    url = paths.get_api_url() + 'categories/'

    headers = utils.get_headers(API_key)

    tempdir = paths.get_temp_dir()
    categories_filepath = os.path.join(tempdir, 'categories.json')

    try:
        r = requests.get(url, headers=headers)
        rdata = r.json()
        categories = rdata['results']
        fix_category_counts(categories)
        # filter_categories(categories) #TODO this should filter categories for search, but not for upload. by now off.
        with open(categories_filepath, 'w') as s:
            json.dump(categories, s, indent=4)
        tasks_queue.add_task((load_categories, ()))
    except Exception as e:
        utils.p('category fetching failed')
        utils.p(e)
        if not os.path.exists(categories_filepath):
            source_path = paths.get_addon_file(subpath='data' + os.sep + 'categories.json')
            shutil.copy(source_path, categories_filepath)


def fetch_categories_thread(API_key):
    cat_thread = threading.Thread(target=fetch_categories, args=([API_key]), daemon=True)
    cat_thread.start()
