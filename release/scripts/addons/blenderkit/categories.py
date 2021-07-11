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


from blenderkit import paths, utils, tasks_queue, rerequests, ui, colors

import requests
import json
import os
import bpy
import time

import shutil
import threading
import logging

bk_logger = logging.getLogger('blenderkit')


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


def get_category_path(categories, category):
    '''finds the category in all possible subcategories and returns the path to it'''
    category_path = []
    check_categories = categories[:]
    parents = {}
    while len(check_categories) > 0:
        ccheck = check_categories.pop()
        #        print(ccheck['name'])
        if not ccheck.get('children'):
            continue

        for ch in ccheck['children']:
            #                print(ch['name'])
            parents[ch['slug']] = ccheck['slug']

            if ch['slug'] == category:
                category_path = [ch['slug']]
                slug = ch['slug']
                while parents.get(slug):
                    slug = parents.get(slug)
                    category_path.insert(0, slug)
                return category_path
            check_categories.append(ch)
    return category_path

def get_category_name_path(categories, category):
    '''finds the category in all possible subcategories and returns the path to it'''
    category_path = []
    check_categories = categories[:]
    parents = {}
    # utils.pprint(categories)
    while len(check_categories) > 0:
        ccheck = check_categories.pop()
        #        print(ccheck['name'])
        if not ccheck.get('children'):
            continue

        for ch in ccheck['children']:
            #                print(ch['name'])
            parents[ch['slug']] = ccheck

            if ch['slug'] == category:
                category_path = [ch['name']]
                slug = ch['slug']
                while parents.get(slug):
                    parent = parents.get(slug)
                    slug = parent['slug']

                    category_path.insert(0, parent['name'])
                return category_path
            check_categories.append(ch)
    return category_path

def get_category(categories, cat_path=()):
    for category in cat_path:
        for c in categories:
            if c['slug'] == category:
                categories = c['children']
                if category == cat_path[-1]:
                    return (c)
                break;


# def get_upload_asset_type(self):
#     typemapper = {
#         bpy.types.Object.blenderkit: 'model',
#         bpy.types.Scene.blenderkit: 'scene',
#         bpy.types.Image.blenderkit: 'hdr',
#         bpy.types.Material.blenderkit: 'material',
#         bpy.types.Brush.blenderkit: 'brush'
#     }
#     asset_type = typemapper[type(self)]
#     return asset_type

def update_category_enums(self, context):
    '''Fixes if lower level is empty - sets it to None, because enum value can be higher.'''
    enums = get_subcategory_enums(self, context)
    if enums[0][0] == 'NONE' and self.subcategory != 'NONE':
        self.subcategory = 'NONE'


def update_subcategory_enums(self, context):
    '''Fixes if lower level is empty - sets it to None, because enum value can be higher.'''
    enums = get_subcategory1_enums(self, context)
    if enums[0][0] == 'NONE' and self.subcategory1 != 'NONE':
        self.subcategory1 = 'NONE'


def get_category_enums(self, context):
    wm = bpy.context.window_manager
    props = bpy.context.scene.blenderkitUI
    asset_type = props.asset_type.lower()
    # asset_type = self.asset_type#get_upload_asset_type(self)
    asset_categories = get_category(wm['bkit_categories'], cat_path=(asset_type,))
    items = []
    for c in asset_categories['children']:
        items.append((c['slug'], c['name'], c['description']))
    if len(items) == 0:
        items.append(('NONE', '', 'no categories on this level defined'))
    return items


def get_subcategory_enums(self, context):
    wm = bpy.context.window_manager
    props = bpy.context.scene.blenderkitUI
    asset_type = props.asset_type.lower()
    items = []
    if self.category != '':
        asset_categories = get_category(wm['bkit_categories'], cat_path=(asset_type, self.category,))
        for c in asset_categories['children']:
            items.append((c['slug'], c['name'], c['description']))
    if len(items) == 0:
        items.append(('NONE', '', 'no categories on this level defined'))
    # print('subcategory', items)
    return items


def get_subcategory1_enums(self, context):
    wm = bpy.context.window_manager
    props = bpy.context.scene.blenderkitUI
    asset_type = props.asset_type.lower()
    items = []
    if self.category != '' and self.subcategory != '':
        asset_categories = get_category(wm['bkit_categories'], cat_path=(asset_type, self.category, self.subcategory,))
        if asset_categories:
            for c in asset_categories['children']:
                items.append((c['slug'], c['name'], c['description']))
    if len(items) == 0:
        items.append(('NONE', '', 'no categories on this level defined'))
    return items


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
    try:
        with open(categories_filepath, 'r', encoding='utf-8') as catfile:
            wm['bkit_categories'] = json.load(catfile)

        wm['active_category'] = {
            'MODEL': ['model'],
            'SCENE': ['scene'],
            'HDR': ['hdr'],
            'MATERIAL': ['material'],
            'BRUSH': ['brush'],
        }
    except:
        print('categories failed to read')


#
catfetch_counter = 0


def fetch_categories(API_key, force=False):
    url = paths.get_api_url() + 'categories/'

    headers = utils.get_headers(API_key)

    tempdir = paths.get_temp_dir()
    categories_filepath = os.path.join(tempdir, 'categories.json')
    if os.path.exists(categories_filepath):
        catfile_age = time.time() - os.path.getmtime(categories_filepath)
    else:
        catfile_age = 10000000

    # global catfetch_counter
    # catfetch_counter += 1
    # bk_logger.debug('fetching categories: ', catfetch_counter)
    # bk_logger.debug('age of cat file', catfile_age)
    try:
        # read categories only once per day maximum, or when forced to do so.
        if catfile_age > 86400 or force:
            bk_logger.debug('requesting categories from server')
            r = rerequests.get(url, headers=headers)
            rdata = r.json()
            categories = rdata['results']
            fix_category_counts(categories)
            # filter_categories(categories) #TODO this should filter categories for search, but not for upload. by now off.
            with open(categories_filepath, 'w', encoding='utf-8') as s:
                json.dump(categories, s, ensure_ascii=False, indent=4)
        tasks_queue.add_task((load_categories, ()))
    except Exception as e:
        t = 'BlenderKit failed to download fresh categories from the server'
        tasks_queue.add_task((ui.add_report,(t, 15, colors.RED)))
        bk_logger.debug(t)
        bk_logger.exception(e)
        if not os.path.exists(categories_filepath):
            source_path = paths.get_addon_file(subpath='data' + os.sep + 'categories.json')
            shutil.copy(source_path, categories_filepath)


def fetch_categories_thread(API_key, force=False):
    cat_thread = threading.Thread(target=fetch_categories, args=([API_key, force]), daemon=True)
    cat_thread.start()
