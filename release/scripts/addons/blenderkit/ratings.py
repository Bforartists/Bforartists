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

from blenderkit import paths, utils, rerequests, tasks_queue, ratings_utils, icons

import bpy
import requests, threading
import logging

bk_logger = logging.getLogger('blenderkit')

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


def upload_review_thread(url, reviews, headers):
    r = rerequests.put(url, data=reviews, verify=True, headers=headers)

    # except requests.exceptions.RequestException as e:
    #     print('reviews upload failed: %s' % str(e))


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
        tasks_queue.add_task((ratings_utils.send_rating_to_thread_quality, (url, ratings, headers)), wait=2.5,
                             only_last=True)
    if bkit_ratings.rating_work_hours > 0.1:
        ratings = (('working_hours', round(bkit_ratings.rating_work_hours, 1)),)
        tasks_queue.add_task((ratings_utils.send_rating_to_thread_work_hours, (url, ratings, headers)), wait=2.5,
                             only_last=True)

    thread = threading.Thread(target=ratings_utils.upload_rating_thread, args=(url, ratings, headers))
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
    ('HDR', 'HDR', 'hdr'),
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


def draw_ratings_menu(self, context, layout):
    pcoll = icons.icon_collections["main"]

    profile_name = ''
    profile = bpy.context.window_manager.get('bkit profile')
    if profile and len(profile['user']['firstName']) > 0:
        profile_name = ' ' + profile['user']['firstName']

    col = layout.column()
    # layout.template_icon_view(bkit_ratings, property, show_labels=False, scale=6.0, scale_popup=5.0)
    row = col.row()
    row.label(text='Quality:', icon='SOLO_ON')
    row = col.row()
    row.label(text='Please help the community by rating quality:')

    row = col.row()
    row.prop(self, 'rating_quality_ui', expand=True, icon_only=True, emboss=False)
    if self.rating_quality > 0:
        # row = col.row()

        row.label(text=f'    Thanks{profile_name}!', icon='FUND')
    # row.label(text=str(self.rating_quality))
    col.separator()
    col.separator()

    row = col.row()
    row.label(text='Complexity:', icon_value=pcoll['dumbbell'].icon_id)
    row = col.row()
    row.label(text=f"How many hours did this {self.asset_type} save you?")

    if utils.profile_is_validator():
        row = col.row()
        row.prop(self, 'rating_work_hours')

    if self.asset_type in ('model', 'scene'):
        row = col.row()

        row.prop(self, 'rating_work_hours_ui', expand=True, icon_only=False, emboss=True)
        if float(self.rating_work_hours_ui) > 100:
            utils.label_multiline(col,
                                  text=f"\nThat's huge! please be sure to give such rating only to godly {self.asset_type}s.\n",
                                  width=500)
        elif float(self.rating_work_hours_ui) > 18:
            col.separator()

            utils.label_multiline(col,
                                  text=f"\nThat's a lot! please be sure to give such rating only to amazing {self.asset_type}s.\n",
                                  width=500)


    elif self.asset_type == 'hdr':
        row = col.row()
        row.prop(self, 'rating_work_hours_ui_1_10', expand=True, icon_only=False, emboss=True)
    else:
        row = col.row()
        row.prop(self, 'rating_work_hours_ui_1_5', expand=True, icon_only=False, emboss=True)

    if self.rating_work_hours > 0:
        row = col.row()
        row.label(text=f'Thanks{profile_name}, you are amazing!', icon='FUND')


class FastRateMenu(Operator, ratings_utils.RatingsProperties):
    """Rating of the assets , also directly from the asset bar - without need to download assets"""
    bl_idname = "wm.blenderkit_menu_rating_upload"
    bl_label = "Ratings"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        return True;

    def draw(self, context):
        layout = self.layout
        draw_ratings_menu(self, context, layout)

    def execute(self, context):
        scene = bpy.context.scene
        ui_props = scene.blenderkitUI
        #get asset id
        if ui_props.active_index > -1:
            sr = bpy.context.window_manager['search results']
            asset_data = dict(sr[ui_props.active_index])
            self.asset_id = asset_data['id']
            self.asset_type = asset_data['assetType']

        if self.asset_id == '':
            return {'CANCELLED'}

        wm = context.window_manager

        self.prefill_ratings()

        if self.asset_type in ('model', 'scene'):
            # spawn a wider one for validators for the enum buttons
            return wm.invoke_popup(self, width=500)
        else:
            return wm.invoke_popup(self)


def rating_menu_draw(self, context):
    layout = self.layout

    ui_props = context.scene.blenderkitUI
    sr = bpy.context.window_manager['search results orig']

    asset_search_index = ui_props.active_index
    if asset_search_index > -1:
        asset_data = dict(sr['results'][asset_search_index])

    col = layout.column()
    layout.label(text='Admin rating Tools:')
    col.operator_context = 'INVOKE_DEFAULT'

    op = col.operator('wm.blenderkit_menu_rating_upload', text='Rate')
    op.asset_id = asset_data['id']
    op.asset_name = asset_data['name']
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
