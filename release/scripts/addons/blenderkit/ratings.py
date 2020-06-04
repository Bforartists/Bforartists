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
    rerequests = reload(rerequests)
    tasks_queue = reload(tasks_queue)
else:
    from blenderkit import paths, utils, rerequests, tasks_queue

import bpy
import requests, threading

from bpy.props import (
    IntProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
)
from bpy.types import (
    Operator,
    Panel,
)


def pretty_print_POST(req):
    """
    pretty print a request
    """
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


def upload_rating_thread(url, ratings, headers):
    ''' Upload rating thread function / disconnected from blender data.'''
    utils.p('upload rating', url, ratings)
    for rating_name, score in ratings:
        if (score != -1 and score != 0):
            rating_url = url + rating_name + '/'
            data = {
                "score": score,  # todo this kind of mixing is too much. Should have 2 bkit structures, upload, use
            }

            try:
                r = rerequests.put(rating_url, data=data, verify=True, headers=headers)

            except requests.exceptions.RequestException as e:
                print('ratings upload failed: %s' % str(e))


def send_rating_to_thread_quality(url, ratings, headers):
    '''Sens rating into thread rating, main purpose is for tasks_queue.
    One function per property to avoid lost data due to stashing.'''
    thread = threading.Thread(target=upload_rating_thread, args=(url, ratings, headers))
    thread.start()

def send_rating_to_thread_work_hours(url, ratings, headers):
    '''Sens rating into thread rating, main purpose is for tasks_queue.
    One function per property to avoid lost data due to stashing.'''
    thread = threading.Thread(target=upload_rating_thread, args=(url, ratings, headers))
    thread.start()


def upload_review_thread(url, reviews, headers):
    r = rerequests.put(url, data=reviews, verify=True, headers=headers)

    # except requests.exceptions.RequestException as e:
    #     print('reviews upload failed: %s' % str(e))


def get_rating(asset_id):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    headers = utils.get_headers(api_key)
    rl = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'
    rtypes = ['quality', 'working_hours']
    for rt in rtypes:
        params = {
            'rating_type': rt
        }
        r = rerequests.get(r1, params=data, verify=True, headers=headers)
        print(r.text)


def update_ratings_quality(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key

    headers = utils.get_headers(api_key)
    asset = self.id_data
    bkit_ratings = asset.bkit_ratings
    url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'

    if bkit_ratings.rating_quality > 0.1:
        ratings = [('quality', bkit_ratings.rating_quality)]
        tasks_queue.add_task((send_rating_to_thread_quality, (url, ratings, headers)), wait=1, only_last=True)


def update_ratings_work_hours(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    headers = utils.get_headers(api_key)
    asset = self.id_data
    bkit_ratings = asset.bkit_ratings
    url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'

    if bkit_ratings.rating_quality > 0.1:
        ratings = [('working_hours', round(bkit_ratings.rating_work_hours, 1))]
        tasks_queue.add_task((send_rating_to_thread_work_hours, (url, ratings, headers)), wait=1, only_last=True)


def upload_rating(asset):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    headers = utils.get_headers(api_key)

    bkit_ratings = asset.bkit_ratings
    # print('rating asset', asset_data['name'], asset_data['asset_base_id'])
    url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'

    ratings = [

    ]

    if bkit_ratings.rating_quality > 0.1:
        ratings.append(('quality', bkit_ratings.rating_quality))
    if bkit_ratings.rating_work_hours > 0.1:
        ratings.append(('working_hours', round(bkit_ratings.rating_work_hours, 1)))

    thread = threading.Thread(target=upload_rating_thread, args=(url, ratings, headers))
    thread.start()

    url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/review'

    reviews = {
        'reviewText': bkit_ratings.rating_compliments,
        'reviewTextProblems': bkit_ratings.rating_problems,
    }
    if not (bkit_ratings.rating_compliments == '' and bkit_ratings.rating_compliments == ''):
        thread = threading.Thread(target=upload_review_thread, args=(url, reviews, headers))
        thread.start()

    # the info that the user rated an item is stored in the scene
    s = bpy.context.scene
    s['assets rated'] = s.get('assets rated', {})
    if bkit_ratings.rating_quality > 0.1 and bkit_ratings.rating_work_hours > 0.1:
        s['assets rated'][asset['asset_data']['asset_base_id']] = True


class StarRatingOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.blenderkit_rating"
    bl_label = "Rate the Asset Quality"
    bl_options = {'REGISTER', 'INTERNAL'}

    property_name: StringProperty(
        name="Rating Property",
        description="Property that is rated",
        default="",
    )

    rating: IntProperty(name="Rating", description="rating value", default=1, min=1, max=10)

    def execute(self, context):
        asset = utils.get_active_asset()
        props = asset.bkit_ratings
        props.rating_quality = self.rating
        return {'FINISHED'}


asset_types = (
    ('MODEL', 'Model', 'set of objects'),
    ('SCENE', 'Scene', 'scene'),
    ('MATERIAL', 'Material', 'any .blend Material'),
    ('TEXTURE', 'Texture', 'a texture, or texture set'),
    ('BRUSH', 'Brush', 'brush, can be any type of blender brush'),
    ('ADDON', 'Addon', 'addnon'),
)


# TODO drop this operator, not needed anymore.
class UploadRatingOperator(bpy.types.Operator):
    """Upload rating to the web db"""
    bl_idname = "object.blenderkit_rating_upload"
    bl_label = "Send Rating"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    # type of upload - model, material, textures, e.t.c.
    # asset_type: EnumProperty(
    #     name="Type",
    #     items=asset_types,
    #     description="Type of asset",
    #     default="MODEL",
    # )

    # @classmethod
    # def poll(cls, context):
    #    return bpy.context.active_object != None and bpy.context.active_object.get('asset_id') is not None
    def draw(self, context):
        layout = self.layout
        layout.label(text='Rating sent to server. Thanks for rating!')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        asset = utils.get_active_asset()
        upload_rating(asset)
        return wm.invoke_props_dialog(self)


def draw_rating(layout, props, prop_name, name):
    # layout.label(name)

    row = layout.row(align=True)

    for a in range(0, 10):
        if eval('props.' + prop_name) < a + 1:
            icon = 'SOLO_OFF'
        else:
            icon = 'SOLO_ON'

        op = row.operator('object.blenderkit_rating', icon=icon, emboss=False, text='')
        op.property_name = prop_name
        op.rating = a + 1


def register_ratings():
    pass;
    bpy.utils.register_class(StarRatingOperator)
    bpy.utils.register_class(UploadRatingOperator)


def unregister_ratings():
    pass;
    bpy.utils.unregister_class(StarRatingOperator)
    bpy.utils.unregister_class(UploadRatingOperator)
