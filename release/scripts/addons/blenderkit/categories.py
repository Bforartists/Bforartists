import requests
import json
import os
from blenderkit import paths
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


def fetch_categories(API_key):
    BLENDERKIT_API_MAIN = "https://www.blenderkit.com/api/v1/"

    url = paths.get_bkit_url() + 'categories/'

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer %s" % API_key
    }
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
    except:
        # print('category fetching failed')
        if not os.path.exists(categories_filepath):
            source_path = paths.get_addon_file(subpath='data' + os.sep + 'categories.json')
            shutil.copy(source_path, categories_filepath)


def fetch_categories_thread(API_key):
    cat_thread = threading.Thread(target=fetch_categories, args=([API_key]), daemon=True)
    cat_thread.start()
