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
    # this function isn't used anywhere,should probably get removed.
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
    if asset:
        bkit_ratings = asset.bkit_ratings
        url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'
    else:
        # this part is for operator rating:
        bkit_ratings = self
        url = paths.get_api_url() + f'assets/{self.asset_id}/rating/'

    if bkit_ratings.rating_quality > 0.1:
        ratings = [('quality', bkit_ratings.rating_quality)]
        tasks_queue.add_task((send_rating_to_thread_quality, (url, ratings, headers)), wait=2.5, only_last=True)


def update_ratings_work_hours(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    headers = utils.get_headers(api_key)
    asset = self.id_data
    if asset:
        bkit_ratings = asset.bkit_ratings
        url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'
    else:
        # this part is for operator rating:
        bkit_ratings = self
        url = paths.get_api_url() + f'assets/{self.asset_id}/rating/'

    if bkit_ratings.rating_work_hours > 0.05:
        ratings = [('working_hours', round(bkit_ratings.rating_work_hours, 1))]
        tasks_queue.add_task((send_rating_to_thread_work_hours, (url, ratings, headers)), wait=2.5, only_last=True)


def upload_rating(asset):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    api_key = user_preferences.api_key
    headers = utils.get_headers(api_key)

    bkit_ratings = asset.bkit_ratings
    # print('rating asset', asset_data['name'], asset_data['assetBaseId'])
    url = paths.get_api_url() + 'assets/' + asset['asset_data']['id'] + '/rating/'

    ratings = [

    ]

    if bkit_ratings.rating_quality > 0.1:
        ratings = (('quality', bkit_ratings.rating_quality),)
        tasks_queue.add_task((send_rating_to_thread_quality, (url, ratings, headers)), wait=2.5, only_last=True)
    if bkit_ratings.rating_work_hours > 0.1:
        ratings=(('working_hours', round(bkit_ratings.rating_work_hours, 1)),)
        tasks_queue.add_task((send_rating_to_thread_work_hours, (url, ratings, headers)), wait=2.5, only_last=True)


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
        s['assets rated'][asset['asset_data']['assetBaseId']] = True


def get_assets_for_rating():
    '''
    gets assets from scene that could/should be rated by the user.
    TODO this is only a draft.

    '''
    assets = []
    for ob in bpy.context.scene.objects:
        if ob.get('asset_data'):
            assets.append(ob)
    for m in bpy.data.materials:
        if m.get('asset_data'):
            assets.append(m)
    for b in bpy.data.brushes:
        if b.get('asset_data'):
            assets.append(b)
    return assets


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


def stars_enum_callback(self, context):
    '''regenerates the enum property used to display rating stars, so that there are filled/empty stars correctly.'''
    items = []
    for a in range(0, 10):
        if self.rating_quality < a + 1:
            icon = 'SOLO_OFF'
        else:
            icon = 'SOLO_ON'
        # has to have something before the number in the value, otherwise fails on registration.
        items.append((f'{a + 1}', f'{a + 1}', '', icon, a + 1))
    return items


def update_quality_ui(self, context):
    '''Converts the _ui the enum into actual quality number.'''
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        self.rating_quality_ui = '0'
    self.rating_quality = int(self.rating_quality_ui)


def update_ratings_work_hours_ui(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        self.rating_work_hours_ui = '0'
    self.rating_work_hours = float(self.rating_work_hours_ui)

def update_ratings_work_hours_ui_1_5(self, context):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.api_key == '':
        # ui_panels.draw_not_logged_in(self, message='Please login/signup to rate assets.')
        # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_login_menu')
        # return
        bpy.ops.wm.blenderkit_login('INVOKE_DEFAULT',
                                    message='Please login/signup to rate assets. Clicking OK takes you to web login.')
        self.rating_work_hours_ui_1_5 = '0'
    # print('updating 1-5')
    # print(float(self.rating_work_hours_ui_1_5))
    self.rating_work_hours = float(self.rating_work_hours_ui_1_5)



class FastRateMenu(Operator):
    """Fast rating of the assets directly in the asset bar - without need to download assets."""
    bl_idname = "wm.blenderkit_menu_rating_upload"
    bl_label = "Send Rating"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    message: StringProperty(
        name="message",
        description="message",
        default="Rating asset")

    asset_id: StringProperty(
        name="Asset Base Id",
        description="Unique name of the asset (hidden)",
        default="")

    asset_type: StringProperty(
        name="Asset type",
        description="asset type",
        default="")

    rating_quality: IntProperty(name="Quality",
                                description="quality of the material",
                                default=0,
                                min=-1, max=10,
                                update=update_ratings_quality)

    # the following enum is only to ease interaction - enums support 'drag over' and enable to draw the stars easily.
    rating_quality_ui: EnumProperty(name='rating_quality_ui',
                                    items=stars_enum_callback,
                                    description='Rating stars 0 - 10',
                                    default=0,
                                    update=update_quality_ui,
                                    )

    rating_work_hours: FloatProperty(name="Work Hours",
                                     description="How many hours did this work take?",
                                     default=0.00,
                                     min=0.0, max=1000, update=update_ratings_work_hours
                                     )

    rating_work_hours_ui: EnumProperty(name="Work Hours",
                                       description="How many hours did this work take?",
                                       items=[('0', '0', ''),
                                              ('.5', '0.5', ''),
                                              ('1', '1', ''),
                                              ('2', '2', ''),
                                              ('3', '3', ''),
                                              ('4', '4', ''),
                                              ('5', '5', ''),
                                              ('6', '6', ''),
                                              ('8', '8', ''),
                                              ('10', '10', ''),
                                              ('15', '15', ''),
                                              ('20', '20', ''),
                                              ('50', '50', ''),
                                              ('100', '100', ''),
                                              ('150', '150', ''),
                                              ('200', '200', ''),
                                              ('250', '250', ''),
                                              ],
                                       default='0', update=update_ratings_work_hours_ui
                                       )

    rating_work_hours_ui_1_5: EnumProperty(name="Work Hours",
                                           description="How many hours did this work take?",
                                           items=[('0', '0', ''),
                                                  ('.2', '0.2', ''),
                                                  ('.5', '0.5', ''),
                                                  ('1', '1', ''),
                                                  ('2', '2', ''),
                                                  ('3', '3', ''),
                                                  ('4', '4', ''),
                                                  ('5', '5', '')
                                                  ],
                                           default='0', update=update_ratings_work_hours_ui_1_5
                                           )

    @classmethod
    def poll(cls, context):
        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        return ui_props.active_index > -1

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # layout.template_icon_view(bkit_ratings, property, show_labels=False, scale=6.0, scale_popup=5.0)
        col.label(text=self.message)
        row = col.row()
        row.prop(self, 'rating_quality_ui', expand=True, icon_only=True, emboss=False)
        col.separator()
        col.prop(self, 'rating_work_hours')
        row = col.row()
        if self.asset_type == 'model':
            row.prop(self, 'rating_work_hours_ui', expand=True, icon_only=False, emboss=True)
        else:
            row.prop(self, 'rating_work_hours_ui_1_5', expand=True, icon_only=False, emboss=True)

    def execute(self, context):
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        api_key = user_preferences.api_key
        headers = utils.get_headers(api_key)

        url = paths.get_api_url() + f'assets/{self.asset_id}/rating/'

        rtgs = [

        ]

        if self.rating_quality_ui == '':
            self.rating_quality = 0
        else:
            self.rating_quality = int(self.rating_quality_ui)

        if self.rating_quality > 0.1:
            rtgs = (('quality', self.rating_quality),)
            tasks_queue.add_task((send_rating_to_thread_quality, (url, rtgs, headers)), wait=2.5, only_last=True)

        if self.rating_work_hours > 0.1:
            rtgs = (('working_hours', round(self.rating_work_hours, 1)),)
            tasks_queue.add_task((send_rating_to_thread_work_hours, (url, rtgs, headers)), wait=2.5, only_last=True)
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        if ui_props.active_index > -1:
            sr = bpy.context.scene['search results']
            asset_data = dict(sr[ui_props.active_index])
            self.asset_id = asset_data['id']
            self.asset_type = asset_data['assetType']
            self.message = f"Rate asset {asset_data['name']}"
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def rating_menu_draw(self, context):
    layout = self.layout

    ui_props = context.scene.blenderkitUI
    sr = bpy.context.scene['search results orig']

    asset_search_index = ui_props.active_index
    if asset_search_index > -1:
        asset_data = dict(sr['results'][asset_search_index])

    col = layout.column()
    layout.label(text='Admin rating Tools:')
    col.operator_context = 'INVOKE_DEFAULT'

    op = col.operator('wm.blenderkit_menu_rating_upload', text='Fast rate')
    op.asset_id = asset_data['id']
    op.asset_type = asset_data['assetType']

def register_ratings():
    bpy.utils.register_class(UploadRatingOperator)
    bpy.utils.register_class(FastRateMenu)
    # bpy.types.OBJECT_MT_blenderkit_asset_menu.append(rating_menu_draw)


def unregister_ratings():
    pass;
    # bpy.utils.unregister_class(StarRatingOperator)
    bpy.utils.unregister_class(UploadRatingOperator)
    bpy.utils.unregister_class(FastRateMenu)
