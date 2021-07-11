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


from blenderkit import paths, ratings, ratings_utils, utils, download, categories, icons, search, resolutions, ui, \
    tasks_queue, \
    autothumb, upload

from bpy.types import (
    Panel
)
from bpy.props import (
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
)

import bpy
import os
import random
import logging

bk_logger = logging.getLogger('blenderkit')


#   this was moved to separate interface:

def draw_ratings(layout, context, asset):
    # layout.operator("wm.url_open", text="Read rating instructions", icon='QUESTION').url = 'https://support.google.com/?hl=en'
    # the following shouldn't happen at all in an optimal case,
    # this function should run only when asset was already checked to be existing
    if asset == None:
        return;

    col = layout.column()
    bkit_ratings = asset.bkit_ratings

    # layout.template_icon_view(bkit_ratings, property, show_labels=False, scale=6.0, scale_popup=5.0)

    row = col.row()
    row.prop(bkit_ratings, 'rating_quality_ui', expand=True, icon_only=True, emboss=False)
    if bkit_ratings.rating_quality > 0:
        col.separator()
        col.prop(bkit_ratings, 'rating_work_hours')
    # w = context.region.width

    # layout.label(text='problems')
    # layout.prop(bkit_ratings, 'rating_problems', text='')
    # layout.label(text='compliments')
    # layout.prop(bkit_ratings, 'rating_compliments', text='')

    # row = layout.row()
    # op = row.operator("object.blenderkit_rating_upload", text="Send rating", icon='URL')
    # return op
    # re-enable layout if included in longer panel


def draw_not_logged_in(source, message='Please Login/Signup to use this feature'):
    title = "You aren't logged in"

    def draw_message(source, context):
        layout = source.layout
        utils.label_multiline(layout, text=message)
        draw_login_buttons(layout)

    bpy.context.window_manager.popup_menu(draw_message, title=title, icon='INFO')


def draw_upload_common(layout, props, asset_type, context):
    op = layout.operator("wm.url_open", text=f"Read {asset_type.lower()} upload instructions",
                         icon='QUESTION')
    if asset_type == 'MODEL':
        op.url = paths.BLENDERKIT_MODEL_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'MATERIAL':
        op.url = paths.BLENDERKIT_MATERIAL_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'BRUSH':
        op.url = paths.BLENDERKIT_BRUSH_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'SCENE':
        op.url = paths.BLENDERKIT_SCENE_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'HDR':
        op.url = paths.BLENDERKIT_HDR_UPLOAD_INSTRUCTIONS_URL

    row = layout.row(align=True)
    if props.upload_state != '':
        utils.label_multiline(layout, text=props.upload_state, width=context.region.width)
    if props.uploading:
        op = layout.operator('object.kill_bg_process', text="", icon='CANCEL')
        op.process_source = asset_type
        op.process_type = 'UPLOAD'
        layout = layout.column()
        layout.enabled = False
    # if props.upload_state.find('Error') > -1:
    #     layout.label(text = props.upload_state)

    if props.asset_base_id == '':
        optext = 'Upload %s' % asset_type.lower()
        op = layout.operator("object.blenderkit_upload", text=optext, icon='EXPORT')
        op.asset_type = asset_type
        op.reupload = False
        # make sure everything gets uploaded.
        op.main_file = True
        op.metadata = True
        op.thumbnail = True

    if props.asset_base_id != '':
        op = layout.operator("object.blenderkit_upload", text='Reupload asset', icon='EXPORT')
        op.asset_type = asset_type
        op.reupload = True

        op = layout.operator("object.blenderkit_upload", text='Upload as new asset', icon='EXPORT')
        op.asset_type = asset_type
        op.reupload = False

        # layout.label(text = 'asset id, overwrite only for reuploading')
        layout.label(text='asset has a version online.')
        # row = layout.row()
        # row.enabled = False
        # row.prop(props, 'asset_base_id', icon='FILE_TICK')
        # row = layout.row()
        # row.enabled = False
        # row.prop(props, 'id', icon='FILE_TICK')
    layout.prop(props, 'category')
    if props.category != 'NONE' and props.subcategory != 'NONE':
        layout.prop(props, 'subcategory')
    if props.subcategory != 'NONE' and props.subcategory1 != 'NONE':
        layout.prop(props, 'subcategory1')

    layout.prop(props, 'is_private', expand=True)
    if props.is_private == 'PUBLIC':
        layout.prop(props, 'license')
        layout.prop(props, 'is_free', expand=True)

    prop_needed(layout, props, 'name', props.name)
    if props.is_private == 'PUBLIC':
        prop_needed(layout, props, 'description', props.description)
        prop_needed(layout, props, 'tags', props.tags)
    else:
        layout.prop(props, 'description')
        layout.prop(props, 'tags')


def poll_local_panels():
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    return user_preferences.panel_behaviour == 'BOTH' or user_preferences.panel_behaviour == 'LOCAL'


def prop_needed(layout, props, name, value='', is_not_filled=''):
    row = layout.row()
    if value == is_not_filled:
        # row.label(text='', icon = 'ERROR')
        icon = 'ERROR'
        row.alert = True
        row.prop(props, name)  # , icon=icon)
        row.alert = False
    else:
        # row.label(text='', icon = 'FILE_TICK')
        icon = None
        row.prop(props, name)


def draw_panel_hdr_upload(self, context):
    layout = self.layout
    ui_props = bpy.context.scene.blenderkitUI

    # layout.prop_search(ui_props, "hdr_upload_image", bpy.data, "images")
    layout.prop(ui_props, "hdr_upload_image")

    hdr = utils.get_active_HDR()

    if hdr is not None:
        props = hdr.blenderkit

        layout = self.layout

        draw_upload_common(layout, props, 'HDR', context)


def draw_panel_hdr_search(self, context):
    s = context.scene
    props = s.blenderkit_HDR

    layout = self.layout
    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)
    layout.prop(props, "own_only")

    utils.label_multiline(layout, text=props.report)


def draw_thumbnail_upload_panel(layout, props):
    update = False
    tex = autothumb.get_texture_ui(props.thumbnail, '.upload_preview')
    if not tex or not tex.image:
        return
    box = layout.box()
    box.template_icon(icon_value=tex.image.preview.icon_id, scale=6.0)


def draw_panel_model_upload(self, context):
    ob = bpy.context.active_object
    while ob.parent is not None:
        ob = ob.parent
    props = ob.blenderkit

    layout = self.layout

    draw_upload_common(layout, props, 'MODEL', context)

    col = layout.column()
    if props.is_generating_thumbnail:
        col.enabled = False

    draw_thumbnail_upload_panel(col, props)

    prop_needed(col, props, 'thumbnail', props.thumbnail)
    if bpy.context.scene.render.engine in ('CYCLES', 'BLENDER_EEVEE'):
        col.operator("object.blenderkit_generate_thumbnail", text='Generate thumbnail', icon='IMAGE')

    # row = layout.row(align=True)
    if props.is_generating_thumbnail:
        row = layout.row(align=True)
        row.label(text=props.thumbnail_generating_state)
        op = row.operator('object.kill_bg_process', text="", icon='CANCEL')
        op.process_source = 'MODEL'
        op.process_type = 'THUMBNAILER'
    elif props.thumbnail_generating_state != '':
        utils.label_multiline(layout, text=props.thumbnail_generating_state)

    # prop_needed(layout, props, 'style', props.style)
    # prop_needed(layout, props, 'production_level', props.production_level)
    layout.prop(props, 'style')
    layout.prop(props, 'production_level')

    layout.prop(props, 'condition')
    layout.prop(props, 'pbr')
    layout.label(text='design props:')
    layout.prop(props, 'manufacturer')
    layout.prop(props, 'designer')
    layout.prop(props, 'design_collection')
    layout.prop(props, 'design_variant')
    layout.prop(props, 'use_design_year')
    if props.use_design_year:
        layout.prop(props, 'design_year')

    row = layout.row()
    row.prop(props, 'work_hours')

    layout.prop(props, 'adult')


def draw_panel_scene_upload(self, context):
    s = bpy.context.scene
    props = s.blenderkit

    layout = self.layout
    # if bpy.app.debug_value != -1:
    #     layout.label(text='Scene upload not Implemented')
    #     return
    draw_upload_common(layout, props, 'SCENE', context)

    #    layout = layout.column()

    # row = layout.row()

    # if props.dimensions[0] + props.dimensions[1] == 0 and props.face_count == 0:
    #     icon = 'ERROR'
    #     layout.operator("object.blenderkit_auto_tags", text='Auto fill tags', icon=icon)
    # else:
    #     layout.operator("object.blenderkit_auto_tags", text='Auto fill tags')

    col = layout.column()
    # if props.is_generating_thumbnail:
    #     col.enabled = False
    draw_thumbnail_upload_panel(col, props)

    prop_needed(col, props, 'thumbnail', props.has_thumbnail, False)
    # if bpy.context.scene.render.engine == 'CYCLES':
    #     col.operator("object.blenderkit_generate_thumbnail", text='Generate thumbnail', icon='IMAGE_COL')

    # row = layout.row(align=True)
    # if props.is_generating_thumbnail:
    #     row = layout.row(align=True)
    #     row.label(text = props.thumbnail_generating_state)
    #     op = row.operator('object.kill_bg_process', text="", icon='CANCEL')
    #     op.process_source = 'MODEL'
    #     op.process_type = 'THUMBNAILER'
    # elif props.thumbnail_generating_state != '':
    #    utils.label_multiline(layout, text = props.thumbnail_generating_state)

    layout.prop(props, 'style')
    layout.prop(props, 'production_level')
    layout.prop(props, 'use_design_year')
    if props.use_design_year:
        layout.prop(props, 'design_year')
    layout.prop(props, 'condition')
    row = layout.row()
    row.prop(props, 'work_hours')
    layout.prop(props, 'adult')


def draw_assetbar_show_hide(layout, props):
    s = bpy.context.scene
    ui_props = s.blenderkitUI

    if ui_props.assetbar_on:
        icon = 'HIDE_OFF'
        ttip = 'Click to Hide Asset Bar'
    else:
        icon = 'HIDE_ON'
        ttip = 'Click to Show Asset Bar'

    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if preferences.experimental_features:
        op = layout.operator('view3d.blenderkit_asset_bar_widget', text='', icon=icon)
        op.keep_running = False
        op.do_search = False
        op.tooltip = ttip
    else:
        op = layout.operator('view3d.blenderkit_asset_bar', text='', icon=icon)
        op.keep_running = False
        op.do_search = False

        op.tooltip = ttip


def draw_panel_model_search(self, context):
    s = context.scene

    props = s.blenderkit_models
    layout = self.layout

    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)

    icon = 'NONE'
    if props.report == 'You need Full plan to get this item.':
        icon = 'ERROR'
    utils.label_multiline(layout, text=props.report, icon=icon)
    if props.report == 'You need Full plan to get this item.':
        layout.operator("wm.url_open", text="Get Full plan", icon='URL').url = paths.BLENDERKIT_PLANS

    # layout.prop(props, "search_style")
    # layout.prop(props, "own_only")
    # layout.prop(props, "free_only")

    # if props.search_style == 'OTHER':
    #     layout.prop(props, "search_style_other")
    # layout.prop(props, "search_engine")
    # col = layout.column()
    # layout.prop(props, 'append_link', expand=True, icon_only=False)
    # layout.prop(props, 'import_as', expand=True, icon_only=False)

    # draw_panel_categories(self, context)


def draw_panel_scene_search(self, context):
    s = context.scene
    props = s.blenderkit_scene
    layout = self.layout
    # layout.label(text = "common search properties:")
    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)
    layout.prop(props, "own_only")
    utils.label_multiline(layout, text=props.report)

    # layout.prop(props, "search_style")
    # if props.search_style == 'OTHER':
    #     layout.prop(props, "search_style_other")
    # layout.prop(props, "search_engine")
    layout.separator()
    # draw_panel_categories(self, context)


class VIEW3D_PT_blenderkit_model_properties(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_model_properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Selected Model"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        p = bpy.context.view_layer.objects.active is not None
        return p

    def draw(self, context):
        # draw asset properties here
        layout = self.layout

        o = utils.get_active_model()
        # o = bpy.context.active_object
        if o.get('asset_data') is None:
            utils.label_multiline(layout,
                                  text='To upload this asset to BlenderKit, go to the Find and Upload Assets panel.')
            layout.prop(o, 'name')

        if o.get('asset_data') is not None:
            ad = o['asset_data']
            layout.label(text=str(ad['name']))
            if o.instance_type == 'COLLECTION' and o.instance_collection is not None:
                layout.operator('object.blenderkit_bring_to_scene', text='Bring to scene')

            layout.label(text='Asset tools:')
            draw_asset_context_menu(self.layout, context, ad, from_panel=True)
            # if 'rig' in ad['tags']:
            #     # layout.label(text = 'can make proxy')
            #     layout.operator('object.blenderkit_make_proxy', text = 'Make Armature proxy')
        # fast upload, blocked by now
        # else:
        #     op = layout.operator("object.blenderkit_upload", text='Store as private', icon='EXPORT')
        #     op.asset_type = 'MODEL'
        #     op.fast = True
        # fun override project, not finished
        # layout.operator('object.blenderkit_color_corrector')


class NODE_PT_blenderkit_material_properties(Panel):
    bl_category = "BlenderKit"
    bl_idname = "NODE_PT_blenderkit_material_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Selected Material"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        p = bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None
        return p

    def draw(self, context):
        # draw asset properties here
        layout = self.layout

        m = bpy.context.active_object.active_material
        # o = bpy.context.active_object
        if m.get('asset_data') is None and m.blenderkit.id == '':
            utils.label_multiline(layout,
                                  text='To upload this asset to BlenderKit, go to the Find and Upload Assets panel.')
            layout.prop(m, 'name')

        if m.get('asset_data') is not None:
            ad = m['asset_data']
            layout.label(text=str(ad['name']))

            layout.label(text='Asset tools:')
            draw_asset_context_menu(self.layout, context, ad, from_panel=True)
            # if 'rig' in ad['tags']:
            #     # layout.label(text = 'can make proxy')
            #     layout.operator('object.blenderkit_make_proxy', text = 'Make Armature proxy')
        # fast upload, blocked by now
        # else:
        #     op = layout.operator("object.blenderkit_upload", text='Store as private', icon='EXPORT')
        #     op.asset_type = 'MODEL'
        #     op.fast = True
        # fun override project, not finished
        # layout.operator('object.blenderkit_color_corrector')


def draw_rating_asset(self, context, asset):
    layout = self.layout
    col = layout.box()
    # split = layout.split(factor=0.5)
    # col1 = split.column()
    # col2 = split.column()
    # print('%s_search' % asset['asset_data']['assetType'])
    directory = paths.get_temp_dir('%s_search' % asset['asset_data']['assetType'])
    tpath = os.path.join(directory, asset['asset_data']['thumbnail_small'])
    for image in bpy.data.images:
        if image.filepath == tpath:
            # split = row.split(factor=1.0, align=False)
            col.template_icon(icon_value=image.preview.icon_id, scale=6.0)
            break;
        # layout.label(text = '', icon_value=image.preview.icon_id, scale = 10)
    col.label(text=asset.name)
    draw_ratings(col, context, asset=asset)


class VIEW3D_PT_blenderkit_ratings(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_ratings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Please rate"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        #
        p = bpy.context.view_layer.objects.active is not None
        return p

    def draw(self, context):
        # TODO make a list of assets inside asset appending code, to happen only when assets are added to the scene.
        # draw asset properties here
        layout = self.layout
        assets = ratings.get_assets_for_rating()
        if len(assets) > 0:
            utils.label_multiline(layout, text='Please help BlenderKit community by rating these assets:')

            for a in assets:
                if a.bkit_ratings.rating_work_hours == 0:
                    draw_rating_asset(self, context, asset=a)


def draw_login_progress(layout):
    layout.label(text='Login through browser')
    layout.label(text='in progress.')
    layout.operator("wm.blenderkit_login_cancel", text="Cancel", icon='CANCEL')


class VIEW3D_PT_blenderkit_profile(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_profile"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "BlenderKit Profile"

    @classmethod
    def poll(cls, context):

        return True

    def draw(self, context):
        # draw asset properties here
        layout = self.layout
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

        if user_preferences.login_attempt:
            draw_login_progress(layout)
            return

        if user_preferences.api_key != '':
            me = bpy.context.window_manager.get('bkit profile')
            if me is not None:
                me = me['user']
                # user name
                if len(me['firstName']) > 0 or len(me['lastName']) > 0:
                    layout.label(text=f"Me: {me['firstName']} {me['lastName']}")
                else:
                    layout.label(text=f"Me: {me['email']}")
                # layout.label(text='Email: %s' % (me['email']))

                # plan information

                if me.get('currentPlanName') is not None:
                    pn = me['currentPlanName']
                    pcoll = icons.icon_collections["main"]
                    if pn == 'Free':
                        my_icon = pcoll['free']
                    else:
                        my_icon = pcoll['full']

                    row = layout.row()
                    row.label(text='My plan:')
                    row.label(text='%s plan' % pn, icon_value=my_icon.icon_id)
                    if pn == 'Free':
                        layout.operator("wm.url_open", text="Change plan",
                                        icon='URL').url = paths.get_bkit_url() + paths.BLENDERKIT_PLANS

                # storage statistics
                # if me.get('sumAssetFilesSize') is not None:  # TODO remove this when production server has these too.
                #     layout.label(text='My public assets: %i MiB' % (me['sumAssetFilesSize']))
                # if me.get('sumPrivateAssetFilesSize') is not None:
                #     layout.label(text='My private assets: %i MiB' % (me['sumPrivateAssetFilesSize']))
                if me.get('remainingPrivateQuota') is not None:
                    layout.label(text='My free storage: %i MiB' % (me['remainingPrivateQuota']))

            layout.operator("wm.url_open", text="See my uploads",
                            icon='URL').url = paths.get_bkit_url() + paths.BLENDERKIT_USER_ASSETS


class VIEW3D_PT_blenderkit_login(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_login"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "BlenderKit Login"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

        if user_preferences.login_attempt:
            draw_login_progress(layout)
            return

        if user_preferences.enable_oauth:
            draw_login_buttons(layout)


def draw_panel_model_rating(self, context):
    # o = bpy.context.active_object
    o = utils.get_active_model()
    # print('ratings active',o)
    draw_ratings(self.layout, context, asset=o)  # , props)
    # op.asset_type = 'MODEL'


def draw_panel_material_upload(self, context):
    o = bpy.context.active_object
    mat = bpy.context.active_object.active_material

    props = mat.blenderkit
    layout = self.layout

    draw_upload_common(layout, props, 'MATERIAL', context)

    # THUMBNAIL
    row = layout.column()
    if props.is_generating_thumbnail:
        row.enabled = False

    draw_thumbnail_upload_panel(row, props)

    prop_needed(row, props, 'thumbnail', props.has_thumbnail, False)

    if bpy.context.scene.render.engine in ('CYCLES', 'BLENDER_EEVEE'):
        layout.operator("object.blenderkit_generate_material_thumbnail", text='Render thumbnail with Cycles',
                        icon='EXPORT')
    if props.is_generating_thumbnail:
        row = layout.row(align=True)
        row.label(text=props.thumbnail_generating_state, icon='RENDER_STILL')
        op = row.operator('object.kill_bg_process', text="", icon='CANCEL')
        op.process_source = 'MATERIAL'
        op.process_type = 'THUMBNAILER'
    elif props.thumbnail_generating_state != '':
        utils.label_multiline(layout, text=props.thumbnail_generating_state)

    layout.prop(props, 'style')
    # if props.style == 'OTHER':
    #     layout.prop(props, 'style_other')
    # layout.prop(props, 'engine')
    # if props.engine == 'OTHER':
    #     layout.prop(props, 'engine_other')
    # layout.prop(props,'shaders')#TODO autofill on upload
    # row = layout.row()

    layout.prop(props, 'pbr')
    layout.prop(props, 'uv')
    layout.prop(props, 'animated')
    layout.prop(props, 'texture_size_meters')

    # tname = "." + bpy.context.active_object.active_material.name + "_thumbnail"
    # if props.has_thumbnail and bpy.data.textures.get(tname) is not None:
    #     row = layout.row()
    #     # row.scale_y = 1.5
    #     row.template_preview(bpy.data.textures[tname], preview_id='test')


def draw_panel_material_search(self, context):
    wm = context.scene
    props = wm.blenderkit_mat

    layout = self.layout
    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)
    utils.label_multiline(layout, text=props.report)

    # layout.prop(props, 'search_style')F
    # if props.search_style == 'OTHER':
    #     layout.prop(props, 'search_style_other')
    # layout.prop(props, 'search_engine')
    # if props.search_engine == 'OTHER':
    #     layout.prop(props, 'search_engine_other')

    # draw_panel_categories(self, context)


def draw_panel_material_ratings(self, context):
    asset = bpy.context.active_object.active_material
    draw_ratings(self.layout, context, asset)  # , props)
    # op.asset_type = 'MATERIAL'


def draw_panel_brush_upload(self, context):
    brush = utils.get_active_brush()
    if brush is not None:
        props = brush.blenderkit

        layout = self.layout

        draw_upload_common(layout, props, 'BRUSH', context)


def draw_panel_brush_search(self, context):
    s = context.scene
    props = s.blenderkit_brush

    layout = self.layout
    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)
    layout.prop(props, "own_only")

    utils.label_multiline(layout, text=props.report)
    # draw_panel_categories(self, context)


def draw_panel_brush_ratings(self, context):
    # props = utils.get_brush_props(context)
    brush = utils.get_active_brush()
    draw_ratings(self.layout, context, asset=brush)  # , props)
    #
    # op.asset_type = 'BRUSH'


def draw_login_buttons(layout, invoke=False):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    if user_preferences.login_attempt:
        draw_login_progress(layout)
    else:
        if invoke:
            layout.operator_context = 'INVOKE_DEFAULT'
        else:
            layout.operator_context = 'EXEC_DEFAULT'
        if user_preferences.api_key == '':
            layout.operator("wm.blenderkit_login", text="Login",
                            icon='URL').signup = False
            layout.operator("wm.blenderkit_login", text="Sign up",
                            icon='URL').signup = True

        else:
            layout.operator("wm.blenderkit_login", text="Login as someone else",
                            icon='URL').signup = False
            layout.operator("wm.blenderkit_logout", text="Logout",
                            icon='URL')


class VIEW3D_PT_blenderkit_advanced_model_search(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_advanced_model_search"
    bl_parent_id = "VIEW3D_PT_blenderkit_unified"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Search filters"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        s = context.scene
        ui_props = s.blenderkitUI
        return ui_props.down_up == 'SEARCH' and ui_props.asset_type == 'MODEL'

    def draw(self, context):
        s = context.scene

        props = s.blenderkit_models
        layout = self.layout
        layout.separator()

        # layout.label(text = "common searches keywords:")
        # layout.prop(props, "search_global_keywords", text = "")
        # layout.prop(props, "search_modifier_keywords")
        # if props.search_engine == 'OTHER':
        #     layout.prop(props, "search_engine_keyword")

        layout.prop(props, "own_only")
        layout.prop(props, "free_only")
        layout.prop(props, "search_style")

        # DESIGN YEAR
        layout.prop(props, "search_design_year", text='Designed in Year')
        if props.search_design_year:
            row = layout.row(align=True)
            row.prop(props, "search_design_year_min", text='Min')
            row.prop(props, "search_design_year_max", text='Max')

        # POLYCOUNT
        layout.prop(props, "search_polycount", text='Poly Count ')
        if props.search_polycount:
            row = layout.row(align=True)
            row.prop(props, "search_polycount_min", text='Min')
            row.prop(props, "search_polycount_max", text='Max')

        # TEXTURE RESOLUTION
        layout.prop(props, "search_texture_resolution", text='Texture Resolutions')
        if props.search_texture_resolution:
            row = layout.row(align=True)
            row.prop(props, "search_texture_resolution_min", text='Min')
            row.prop(props, "search_texture_resolution_max", text='Max')

        # FILE SIZE
        layout.prop(props, "search_file_size", text='File Size (MB)')
        if props.search_file_size:
            row = layout.row(align=True)
            row.prop(props, "search_file_size_min", text='Min')
            row.prop(props, "search_file_size_max", text='Max')

        # AGE
        layout.prop(props, "search_condition", text='Condition')  # , text ='condition of object new/old e.t.c.')

        # layout.prop(props, "search_procedural", expand=True)
        # ADULT
        # layout.prop(props, "search_adult")  # , text ='condition of object new/old e.t.c.')


class VIEW3D_PT_blenderkit_advanced_material_search(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_advanced_material_search"
    bl_parent_id = "VIEW3D_PT_blenderkit_unified"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Search filters"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        s = context.scene
        ui_props = s.blenderkitUI
        return ui_props.down_up == 'SEARCH' and ui_props.asset_type == 'MATERIAL'

    def draw(self, context):
        s = context.scene

        props = s.blenderkit_mat
        layout = self.layout
        layout.separator()

        layout.prop(props, "own_only")

        layout.label(text='Texture:')
        col = layout.column()
        col.prop(props, "search_procedural", expand=True)

        if props.search_procedural == 'TEXTURE_BASED':
            # TEXTURE RESOLUTION
            layout.prop(props, "search_texture_resolution", text='Texture Resolution')
            if props.search_texture_resolution:
                row = layout.row(align=True)
                row.prop(props, "search_texture_resolution_min", text='Min')
                row.prop(props, "search_texture_resolution_max", text='Max')

        # FILE SIZE
        layout.prop(props, "search_file_size", text='File size (MB)')
        if props.search_file_size:
            row = layout.row(align=True)
            row.prop(props, "search_file_size_min", text='Min')
            row.prop(props, "search_file_size_max", text='Max')


class VIEW3D_PT_blenderkit_categories(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_categories"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Categories"
    bl_parent_id = "VIEW3D_PT_blenderkit_unified"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        s = context.scene
        ui_props = s.blenderkitUI
        mode = True
        if ui_props.asset_type == 'BRUSH' and not (context.sculpt_object or context.image_paint_object):
            mode = False
        return ui_props.down_up == 'SEARCH' and mode

    def draw(self, context):
        draw_panel_categories(self, context)

def draw_scene_import_settings(self, context):
    s = context.scene
    props = s.blenderkit_scene
    layout = self.layout
    layout.prop(props, 'switch_after_append')
    # layout.label(text='Import method:')
    row = layout.row()
    row.prop(props, 'append_link', expand=True, icon_only=False)


class VIEW3D_PT_blenderkit_import_settings(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_import_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Import settings"
    bl_parent_id = "VIEW3D_PT_blenderkit_unified"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        s = context.scene
        ui_props = s.blenderkitUI
        return ui_props.down_up == 'SEARCH' and ui_props.asset_type in ['MATERIAL', 'MODEL', 'SCENE', 'HDR']

    def draw(self, context):
        layout = self.layout

        s = context.scene
        ui_props = s.blenderkitUI

        if ui_props.asset_type == 'MODEL':
            # noinspection PyCallByClass
            props = s.blenderkit_models
            layout.prop(props, 'randomize_rotation')
            if props.randomize_rotation:
                layout.prop(props, 'randomize_rotation_amount')
            layout.prop(props, 'perpendicular_snap')
            # if props.perpendicular_snap:
            #     layout.prop(props,'perpendicular_snap_threshold')

            layout.label(text='Import method:')
            row = layout.row()
            row.prop(props, 'append_method', expand=True, icon_only=False)

        if ui_props.asset_type == 'MATERIAL':
            props = s.blenderkit_mat
            layout.prop(props, 'automap')
            layout.label(text='Import method:')
            row = layout.row()

            row.prop(props, 'append_method', expand=True, icon_only=False)
        if ui_props.asset_type == 'SCENE':
            draw_scene_import_settings(self,context)

        if ui_props.asset_type == 'HDR':
            props = s.blenderkit_HDR

        if ui_props.asset_type in ['MATERIAL', 'MODEL', 'HDR']:
            layout.prop(props, 'resolution')
        # layout.prop(props, 'unpack_files')


class VIEW3D_PT_blenderkit_unified(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_unified"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Find and Upload Assets"

    @classmethod
    def poll(cls, context):
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        return user_preferences.panel_behaviour == 'BOTH' or user_preferences.panel_behaviour == 'UNIFIED'

    def draw(self, context):
        s = context.scene
        ui_props = s.blenderkitUI
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        wm = bpy.context.window_manager
        layout = self.layout
        # layout.prop_tabs_enum(ui_props, "asset_type", icon_only = True)

        row = layout.row()
        # row.scale_x = 1.6
        # row.scale_y = 1.6
        #
        row.prop(ui_props, 'down_up', expand=True, icon_only=False)
        # row.label(text='')
        # row = row.split().row()
        # layout.alert = True
        # layout.alignment = 'CENTER'
        row = layout.row(align=True)
        row.scale_x = 1.6
        row.scale_y = 1.6
        # split = row.split(factor=.

        expand_icon = 'TRIA_DOWN'
        if ui_props.asset_type_fold:
            expand_icon = 'TRIA_RIGHT'
        row = layout.row()
        split = row.split(factor=0.15)
        split.prop(ui_props, 'asset_type_fold', icon=expand_icon, icon_only=True, emboss=False)

        if ui_props.asset_type_fold:
            pass
            # expanded interface with names in column
            split = split.row()
            split.scale_x = 8
            split.scale_y = 1.6
            # split = row
            # split = layout.row()
        else:
            split = split.column()

        split.prop(ui_props, 'asset_type', expand=True, icon_only=ui_props.asset_type_fold)
        # row = layout.column(align = False)
        # layout.prop(ui_props, 'asset_type', expand=False, text='')

        w = context.region.width
        if user_preferences.login_attempt:
            draw_login_progress(layout)
            return

        if len(user_preferences.api_key) < 20 and user_preferences.asset_counter > 20:
            if user_preferences.enable_oauth:
                draw_login_buttons(layout)
            else:
                op = layout.operator("wm.url_open", text="Get your API Key",
                                     icon='QUESTION')
                op.url = paths.BLENDERKIT_SIGNUP_URL
                layout.label(text='Paste your API Key:')
                layout.prop(user_preferences, 'api_key', text='')
            layout.separator()
        # if bpy.data.filepath == '':
        #     layout.alert = True
        #    utils.label_multiline(layout, text="It's better to save your file first.", width=w)
        #     layout.alert = False
        #     layout.separator()

        if ui_props.down_up == 'SEARCH':
            if utils.profile_is_validator():
                search_props = utils.get_search_props()
                layout.prop(search_props, 'search_verification_status')
                layout.prop(search_props, "unrated_only")

            if ui_props.asset_type == 'MODEL':
                # noinspection PyCallByClass
                draw_panel_model_search(self, context)
            if ui_props.asset_type == 'SCENE':
                # noinspection PyCallByClass
                draw_panel_scene_search(self, context)
            if ui_props.asset_type == 'HDR':
                # noinspection PyCallByClass
                draw_panel_hdr_search(self, context)
            elif ui_props.asset_type == 'MATERIAL':
                draw_panel_material_search(self, context)
            elif ui_props.asset_type == 'BRUSH':
                if context.sculpt_object or context.image_paint_object:
                    # noinspection PyCallByClass
                    draw_panel_brush_search(self, context)
                else:
                    utils.label_multiline(layout, text='Switch to paint or sculpt mode.', width=context.region.width)
                    return


        elif ui_props.down_up == 'UPLOAD':
            if not ui_props.assetbar_on:
                text = 'Show asset preview - ;'
            else:
                text = 'Hide asset preview - ;'
            op = layout.operator('view3d.blenderkit_asset_bar', text=text, icon='EXPORT')
            op.keep_running = False
            op.do_search = False
            op.tooltip = 'Show/Hide asset preview'

            e = s.render.engine
            if e not in ('CYCLES', 'BLENDER_EEVEE'):
                rtext = 'Only Cycles and EEVEE render engines are currently supported. ' \
                        'Please use Cycles for all assets you upload to BlenderKit.'
                utils.label_multiline(layout, rtext, icon='ERROR', width=w)
                return;

            if ui_props.asset_type == 'MODEL':
                # utils.label_multiline(layout, "Uploaded models won't be available in b2.79", icon='ERROR')
                if bpy.context.view_layer.objects.active is not None:
                    draw_panel_model_upload(self, context)
                else:
                    layout.label(text='selet object to upload')
            elif ui_props.asset_type == 'SCENE':
                draw_panel_scene_upload(self, context)
            elif ui_props.asset_type == 'HDR':
                draw_panel_hdr_upload(self, context)

            elif ui_props.asset_type == 'MATERIAL':
                # utils.label_multiline(layout, "Uploaded materials won't be available in b2.79", icon='ERROR')

                if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None:
                    draw_panel_material_upload(self, context)
                else:
                    utils.label_multiline(layout, text='select object with material to upload materials', width=w)

            elif ui_props.asset_type == 'BRUSH':
                if context.sculpt_object or context.image_paint_object:
                    draw_panel_brush_upload(self, context)
                else:
                    layout.label(text='Switch to paint or sculpt mode.')


class BlenderKitWelcomeOperator(bpy.types.Operator):
    """Login online on BlenderKit webpage"""

    bl_idname = "wm.blenderkit_welcome"
    bl_label = "Welcome to BlenderKit!"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    step: IntProperty(
        name="step",
        description="Tutorial Step",
        default=0,
        options={'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        if self.step == 0:
            user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

            # message = "BlenderKit connects from Blender to an online, " \
            #           "community built shared library of models, " \
            #           "materials, and brushes. " \
            #           "Use addon preferences to set up where files will be saved in the Global directory setting."
            #
            # utils.label_multiline(layout, text=message, width=300)

            layout.template_icon(icon_value=self.img.preview.icon_id, scale=18)

            # utils.label_multiline(layout, text="\n Let's start by searching for some cool materials?", width=300)
            op = layout.operator("wm.url_open", text='Watch Video Tutorial', icon='QUESTION')
            op.url = paths.BLENDERKIT_MANUAL

        else:
            message = "Operator Tutorial called with invalid step"

    def execute(self, context):
        if self.step == 0:
            # move mouse:
            # bpy.context.window_manager.windows[0].cursor_warp(1000, 1000)
            # show n-key sidebar (spaces[index] has to be found for view3d too:
            # bpy.context.window_manager.windows[0].screen.areas[5].spaces[0].show_region_ui = False
            print('running search no')
            ui_props = bpy.context.scene.blenderkitUI
            random_searches = [
                ('MATERIAL','ice'),
                ('MODEL','car'),
                ('MODEL','vase'),
                ('MODEL','grass'),
                ('MODEL','plant'),
                ('MODEL','man'),
                ('MATERIAL','metal'),
                ('MATERIAL','wood'),
                ('MATERIAL','floor'),
                ('MATERIAL','bricks'),
            ]
            random_search = random.choice(random_searches)
            ui_props.asset_type = random_search[0]

            bpy.context.scene.blenderkit_mat.search_keywords = ''#random_search[1]
            bpy.context.scene.blenderkit_mat.search_keywords = '+is_free:true+score_gte:1000+order:-created'#random_search[1]
            # search.search()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = bpy.context.window_manager
        img = utils.get_thumbnail('intro.jpg')
        utils.img_to_preview(img, copy_original = True)
        self.img = img
        w, a, r = utils.get_largest_area(area_type='VIEW_3D')
        if a is not None:
            a.spaces.active.show_region_ui = True

        return wm.invoke_props_dialog(self, width = 500)


def draw_asset_context_menu(layout, context, asset_data, from_panel=False):
    ui_props = context.scene.blenderkitUI

    author_id = str(asset_data['author'].get('id'))
    wm = bpy.context.window_manager

    layout.operator_context = 'INVOKE_DEFAULT'

    if from_panel:
        op = layout.operator('wm.blenderkit_menu_rating_upload', text='Rate')
        op.asset_name = asset_data['name']
        op.asset_id = asset_data['id']
        op.asset_type = asset_data['assetType']

    if from_panel and wm.get('bkit authors') is not None and author_id is not None:
        a = bpy.context.window_manager['bkit authors'].get(author_id)
        if a is not None:
            # utils.p('author:', a)
            op = layout.operator('wm.url_open', text="Open Author's Website")
            if a.get('aboutMeUrl') is not None:
                op.url = a['aboutMeUrl']
            else:
                op.url = paths.get_author_gallery_url(a['id'])
            op = layout.operator('view3d.blenderkit_search', text="Show Assets By Author")
            op.keywords = ''
            op.author_id = author_id

    op = layout.operator('view3d.blenderkit_search', text='Search Similar')
    op.tooltip = 'Search for similar assets in the library'
    # build search string from description and tags:
    op.keywords = asset_data['name']
    if asset_data.get('description'):
        op.keywords += ' ' + asset_data.get('description') + ' '
    op.keywords += ' '.join(asset_data.get('tags'))

    if asset_data.get('canDownload') != 0:
        if len(bpy.context.selected_objects) > 0 and ui_props.asset_type == 'MODEL':
            aob = bpy.context.active_object
            if aob is None:
                aob = bpy.context.selected_objects[0]
            op = layout.operator('scene.blenderkit_download', text='Replace Active Models')

            # this checks if the menu got called from right-click in assetbar(then index is 0 - x) or
            # from a panel(then replacement happens from the active model)
            if from_panel:
                # called from addon panel
                op.asset_base_id = asset_data['assetBaseId']
            else:
                op.asset_index = ui_props.active_index

            # op.asset_type = ui_props.asset_type
            op.model_location = aob.location
            op.model_rotation = aob.rotation_euler
            op.target_object = aob.name
            op.material_target_slot = aob.active_material_index
            op.replace = True
            op.replace_resolution = False

        # resolution replacement operator
        # if asset_data['downloaded'] == 100: # only show for downloaded/used assets
        # if ui_props.asset_type in ('MODEL', 'MATERIAL'):
        #     layout.menu(OBJECT_MT_blenderkit_resolution_menu.bl_idname)

        if ui_props.asset_type in ('MODEL', 'MATERIAL', 'HDR') and \
                utils.get_param(asset_data, 'textureResolutionMax') is not None and \
                utils.get_param(asset_data, 'textureResolutionMax') > 512:

            s = bpy.context.scene

            col = layout.column()
            col.operator_context = 'INVOKE_DEFAULT'

            if from_panel:
                # Called from addon panel

                if asset_data.get('resolution'):
                    op = col.operator('scene.blenderkit_download', text='Replace asset resolution')
                    op.asset_base_id = asset_data['assetBaseId']
                    if asset_data['assetType'] == 'MODEL':
                        o = utils.get_active_model()
                        op.model_location = o.location
                        op.model_rotation = o.rotation_euler
                        op.target_object = o.name
                        op.material_target_slot = o.active_material_index

                    elif asset_data['assetType'] == 'MATERIAL':
                        aob = bpy.context.active_object
                        op.model_location = aob.location
                        op.model_rotation = aob.rotation_euler
                        op.target_object = aob.name
                        op.material_target_slot = aob.active_material_index
                    op.replace_resolution = True
                    op.replace = False

                    op.invoke_resolution = True
                    op.max_resolution = asset_data.get('max_resolution',
                                                       0)  # str(utils.get_param(asset_data, 'textureResolutionMax'))

            elif asset_data['assetBaseId'] in s['assets used'].keys() and asset_data['assetType'] != 'hdr':
                # HDRs are excluded from replacement, since they are always replaced.
                # called from asset bar:
                op = col.operator('scene.blenderkit_download', text='Replace asset resolution')

                op.asset_index = ui_props.active_index
                # op.asset_type = ui_props.asset_type
                op.replace_resolution = True
                op.replace = False
                op.invoke_resolution = True
                o = utils.get_active_model()
                if o and o.get('asset_data'):
                    if o['asset_data']['assetBaseId'] == bpy.context.window_manager['search results'][
                        ui_props.active_index]:
                        op.model_location = o.location
                        op.model_rotation = o.rotation_euler
                    else:
                        op.model_location = (0, 0, 0)
                        op.model_rotation = (0, 0, 0)
                op.max_resolution = asset_data.get('max_resolution',
                                                   0)  # str(utils.get_param(asset_data, 'textureResolutionMax'))
            # print('operator res ', resolution)
            # op.resolution = resolution

    wm = bpy.context.window_manager
    profile = wm.get('bkit profile')
    if profile is not None:
        # validation

        if author_id == str(profile['user']['id']) or utils.profile_is_validator():
            layout.label(text='Management tools:')

            row = layout.row()
            row.operator_context = 'INVOKE_DEFAULT'
            op = layout.operator('wm.blenderkit_fast_metadata', text='Edit Metadata')
            op.asset_id = asset_data['id']
            op.asset_type = asset_data['assetType']

            if asset_data['assetType'] == 'model':
                op = layout.operator('object.blenderkit_regenerate_thumbnail', text='Regenerate thumbnail')
                op.asset_index = ui_props.active_index

            if asset_data['assetType'] == 'material':
                op = layout.operator('object.blenderkit_regenerate_material_thumbnail', text='Regenerate thumbnail')
                op.asset_index = ui_props.active_index
                # op.asset_id = asset_data['id']
                # op.asset_type = asset_data['assetType']

        if author_id == str(profile['user']['id']):
            row = layout.row()
            row.operator_context = 'INVOKE_DEFAULT'
            op = row.operator('object.blenderkit_change_status', text='Delete')
            op.asset_id = asset_data['id']
            op.state = 'deleted'

        if utils.profile_is_validator():
            layout.label(text='Dev Tools:')

            op = layout.operator('object.blenderkit_print_asset_debug', text='Print asset debug')
            op.asset_id = asset_data['id']


# def draw_asset_resolution_replace(self, context, resolution):
#     layout = self.layout
#     ui_props = bpy.context.scene.blenderkitUI
#
#     op = layout.operator('scene.blenderkit_download', text=resolution)
#     if ui_props.active_index == -3:
#         # This happens if the command is called from addon panel
#         o = utils.get_active_model()
#         op.asset_base_id = o['asset_data']['assetBaseId']
#
#     else:
#         op.asset_index = ui_props.active_index
#
#         op.asset_type = ui_props.asset_type
#     if len(bpy.context.selected_objects) > 0:  # and ui_props.asset_type == 'MODEL':
#         aob = bpy.context.active_object
#         op.model_location = aob.location
#         op.model_rotation = aob.rotation_euler
#         op.target_object = aob.name
#         op.material_target_slot = aob.active_material_index
#     op.replace_resolution = True
#     print('operator res ', resolution)
#     op.resolution = resolution


# class OBJECT_MT_blenderkit_resolution_menu(bpy.types.Menu):
#     bl_label = "Replace Asset Resolution"
#     bl_idname = "OBJECT_MT_blenderkit_resolution_menu"
#
#     def draw(self, context):
#         ui_props = context.scene.blenderkitUI
#
#         # sr = bpy.context.window_manager['search results']
#
#         # sr = bpy.context.window_manager['search results']
#         # asset_data = sr[ui_props.active_index]
#
#         for k in resolutions.resolution_props_to_server.keys():
#             draw_asset_resolution_replace(self, context, k)


class OBJECT_MT_blenderkit_asset_menu(bpy.types.Menu):
    bl_label = "Asset options:"
    bl_idname = "OBJECT_MT_blenderkit_asset_menu"

    def draw(self, context):
        ui_props = context.scene.blenderkitUI

        sr = bpy.context.window_manager['search results']
        asset_data = sr[ui_props.active_index]
        draw_asset_context_menu(self.layout, context, asset_data, from_panel=False)


def numeric_to_str(s):
    if s:
        s = str(round(s))
    else:
        s = '-'
    return s


def push_op_left(layout, strength =5):
    for a in range(0, strength):
        layout.label(text='')


def label_or_url(layout, text='', tooltip='', url='', icon_value=None, icon=None):
    '''automatically switch between different layout options for linking or tooltips'''
    layout.emboss = 'NONE'
    if url != '':
        if icon:
            op = layout.operator('wm.blenderkit_url', text=text, icon=icon)
        elif icon_value:
            op = layout.operator('wm.blenderkit_url', text=text, icon_value=icon_value)
        else:
            op = layout.operator('wm.blenderkit_url', text=text)
        op.url = url
        op.tooltip = tooltip
        push_op_left(layout)

        return
    if tooltip != '':
        if icon:
            op = layout.operator('wm.blenderkit_tooltip', text=text, icon=icon)
        elif icon_value:
            op = layout.operator('wm.blenderkit_tooltip', text=text, icon_value=icon_value)
        else:
            op = layout.operator('wm.blenderkit_tooltip', text=text)
        op.tooltip = tooltip
        # these are here to move the text to left, since operators can only center text by default
        push_op_left(layout)
        return
    if icon:
        layout.label(text=text, icon=icon)
    elif icon_value:
        layout.label(text=text, icon_value=icon_value)
    else:
        layout.label(text=text)


class AssetPopupCard(bpy.types.Operator, ratings_utils.RatingsProperties):
    """Generate Cycles thumbnail for model assets"""
    bl_idname = "wm.blenderkit_asset_popup"
    bl_label = "BlenderKit asset popup"

    width = 800

    @classmethod
    def poll(cls, context):
        return True

    def draw_menu(self, context, layout):
        # layout = layout.column()
        draw_asset_context_menu(layout, context, self.asset_data, from_panel=False)

    def draw_property(self, layout, left, right, icon=None, icon_value=None, url='', tooltip=''):
        right = str(right)
        row = layout.row()
        split = row.split(factor=0.35)
        split.alignment = 'RIGHT'
        split.label(text=left)
        split = split.split()
        split.alignment = 'LEFT'
        # split for questionmark:
        if url != '':
            split = split.split(factor=0.6)
        label_or_url(split, text=right, tooltip=tooltip, url=url, icon_value=icon_value, icon=icon)
        # additional questionmark icon where it's important?
        if url != '':
            split = split.split()
            op = split.operator('wm.blenderkit_url', text='', icon='QUESTION')
            op.url = url
            op.tooltip = tooltip

    def draw_asset_parameter(self, layout, key='', pretext=''):
        parameter = utils.get_param(self.asset_data, key)
        if parameter == None:
            return
        if type(parameter) == int:
            parameter = f"{parameter:,d}"
        elif type(parameter) == float:
            parameter = f"{parameter:,.1f}"
        self.draw_property(layout, pretext, parameter)

    def draw_description(self, layout, width=250):
        if len(self.asset_data['description']) > 0:
            box = layout.box()
            box.scale_y = 0.4
            box.label(text='Description')
            box.separator()
            link_more = utils.label_multiline(box, self.asset_data['description'], width=width, max_lines = 10)
            if link_more:
                row = box.row()
                row.scale_y = 2
                op = row.operator('wm.blenderkit_url', text='See full description', icon='URL')
                op.url = paths.get_asset_gallery_url(self.asset_data['assetBaseId'])
                op.tooltip = 'Read full description on website'
            box.separator()

    def draw_properties(self, layout, width=250):

        if type(self.asset_data['parameters']) == list:
            mparams = utils.params_to_dict(self.asset_data['parameters'])
        else:
            mparams = self.asset_data['parameters']

        pcoll = icons.icon_collections["main"]

        box = layout.box()

        box.scale_y = 0.4
        box.label(text='Properties')
        box.separator()

        if self.asset_data.get('license') == 'cc_zero':
            t = 'CC Zero          '
            icon = pcoll['cc0']

        else:
            t = 'Royalty free'
            icon = pcoll['royalty_free']

        self.draw_property(box,
                           'License', t,
                           # icon_value=icon.icon_id,
                           url="https://www.blenderkit.com/docs/licenses/",
                           tooltip='All BlenderKit assets are available for commercial use. \n' \
                                   'Click to read more about BlenderKit licenses on the website'
                           )

        if upload.can_edit_asset(asset_data=self.asset_data):
            icon = pcoll[self.asset_data['verificationStatus']]
            verification_status_tooltips = {
                'uploading': "Your asset got stuck during upload. Probably, your file was too large "
                             "or your connection too slow or interrupting. If you have repeated issues, "
                             "please contact us and let us know, it might be a bug",
                'uploaded': "Your asset uploaded successfully. Yay! If it's public, "
                            "it's awaiting validation. If it's private, use it",
                'on_hold': "Your asset needs some (usually smaller) fixes, "
                           "so we can make it public for everybody."
                           " Please check your email to see the feedback "
                           "that we send to every creator personally",
                'rejected': "The asset has serious quality issues, " \
                            "and it's probable that it might be good to start " \
                            "all over again or try with something simpler. " \
                            "You also get personal feedback into your e-mail, " \
                            "since we believe that together, we can all learn " \
                            "to become awesome 3D artists",
                'deleted': "You deleted this asset",
                'validated': "Your asset passed our validation process, "
                             "and is now available to BlenderKit users"

            }
            self.draw_property(box,
                               'Verification',
                               self.asset_data['verificationStatus'],
                               icon_value=icon.icon_id,
                               url="https://www.blenderkit.com/docs/validation-status/",
                               tooltip=verification_status_tooltips[self.asset_data['verificationStatus']]

                               )
        # resolution/s
        resolution = utils.get_param(self.asset_data, 'textureResolutionMax')

        if resolution is not None:
            fs = self.asset_data['files']

            ress = f"{int(round(resolution / 1024, 0))}K"
            self.draw_property(box, 'Resolution', ress,
                               tooltip='Maximal resolution of textures in this asset.\n' \
                                       'Most texture asset have also lower resolutions generated.\n' \
                                       'Go to BlenderKit add-on import settings to set default resolution')

            if fs and len(fs) > 2 and utils.profile_is_validator():
                resolutions = ''
                list.sort(fs, key=lambda f: f['fileType'])
                for f in fs:
                    if f['fileType'].find('resolution') > -1:
                        resolutions += f['fileType'][11:] + ' '
                resolutions = resolutions.replace('_', '.')
                self.draw_property(box, 'Generated', resolutions)

        self.draw_asset_parameter(box, key='designer', pretext='Designer')
        self.draw_asset_parameter(box, key='manufacturer', pretext='Manufacturer')  # TODO make them clickable!
        self.draw_asset_parameter(box, key='designCollection', pretext='Collection')
        self.draw_asset_parameter(box, key='designVariant', pretext='Variant')
        self.draw_asset_parameter(box, key='designYear', pretext='Design year')

        self.draw_asset_parameter(box, key='faceCount', pretext='Face count')
        # self.draw_asset_parameter(box, key='thumbnailScale', pretext='Preview scale')
        # self.draw_asset_parameter(box, key='purePbr', pretext='Pure PBR')
        # self.draw_asset_parameter(box, key='productionLevel', pretext='Readiness')
        # self.draw_asset_parameter(box, key='condition', pretext='Condition')
        self.draw_asset_parameter(box, key='material_style', pretext='Style')
        self.draw_asset_parameter(box, key='model_style', pretext='Style')

        if utils.get_param(self.asset_data, 'dimensionX'):
            t = '%s×%s×%s m' % (utils.fmt_length(mparams['dimensionX']),
                                utils.fmt_length(mparams['dimensionY']),
                                utils.fmt_length(mparams['dimensionZ']))
            self.draw_property(box, 'Size', t)
        if self.asset_data.get('filesSize'):
            fs = self.asset_data['filesSize']
            fsmb = fs // (1024 * 1024)
            fskb = fs % 1024
            if fsmb == 0:
                self.draw_property(box, 'Original size', f'{fskb} KB')
            else:
                self.draw_property(box, 'Original size', f'{fsmb} MB')
        # Tags section
        # row = box.row()
        # letters_on_row = 0
        # max_on_row = width / 10
        # for tag in self.asset_data['tags']:
        #     if tag in ('manifold', 'uv', 'non-manifold'):
        #         # these are sometimes accidentally stored in the lib
        #         continue
        #
        #     # row.emboss='NONE'
        #     # we need to split wisely
        #     remaining_row = (max_on_row - letters_on_row) / max_on_row
        #     split_factor = (len(tag) / max_on_row) / remaining_row
        #     row = row.split(factor=split_factor)
        #     letters_on_row += len(tag)
        #     if letters_on_row > max_on_row:
        #         letters_on_row = len(tag)
        #         row = box.row()
        #         remaining_row = (max_on_row - letters_on_row) / max_on_row
        #         split_factor = (len(tag) / max_on_row) / remaining_row
        #         row = row.split(factor=split_factor)
        #
        #     op = row.operator('wm')
        #     op = row.operator('view3d.blenderkit_search', text=tag)
        #     op.tooltip = f'Search items with tag {tag}'
        #     # build search string from description and tags:
        #     op.keywords = f'+tags:{tag}'

        # self.draw_property(box, 'Tags', self.asset_data['tags']) #TODO make them clickable!

        # Free/Full plan or private Access
        plans_tooltip = 'BlenderKit has 2 plans:\n' \
                        '  *  Free plan - more than 50% of all assets\n' \
                        '  *  Full plan - unlimited access to everything\n' \
                        'Click to go to subscriptions page'
        plans_link = 'https://www.blenderkit.com/plans/pricing/'
        if self.asset_data['isPrivate']:
            t = 'Private'
            self.draw_property(box, 'Access', t, icon='LOCKED')
        elif self.asset_data['isFree']:
            t = 'Free plan'
            icon = pcoll['free']
            self.draw_property(box, 'Access', t,
                               icon_value=icon.icon_id,
                               tooltip=plans_tooltip,
                               url=plans_link)
        else:
            t = 'Full plan'
            icon = pcoll['full']
            self.draw_property(box, 'Access', t,
                               icon_value=icon.icon_id,
                               tooltip=plans_tooltip,
                               url=plans_link)
        if utils.profile_is_validator():
            date = self.asset_data['created'][:10]
            date = f"{date[8:10]}. {date[5:7]}. {date[:4]}"
            self.draw_property(box, 'Created', date)
        box.separator()

    def draw_author_area(self, context, layout, width=330):
        self.draw_author(context, layout, width=width)

    def draw_author(self, context, layout, width=330):
        image_split = 0.25
        text_width = width
        authors = bpy.context.window_manager['bkit authors']
        a = authors.get(self.asset_data['author']['id'])
        if a is not None:  # or a is '' or (a.get('gravatarHash') is not None and a.get('gravatarImg') is None):

            row = layout.row()
            author_box = row.box()
            author_box.scale_y = 0.6  # get text lines closer to each other
            author_box.label(text='Author')  # just one extra line to give spacing
            if hasattr(self, 'gimg'):

                author_left = author_box.split(factor=image_split)
                author_left.template_icon(icon_value=self.gimg.preview.icon_id, scale=7)
                text_area = author_left.split()
                text_width = int(text_width * (1 - image_split))
            else:
                text_area = author_box

            author_right = text_area.column()
            row = author_right.row()
            col = row.column()

            utils.label_multiline(col, text=a['tooltip'], width=text_width)
            # check if author didn't fill any data about himself and prompt him if that's the case
            if utils.user_is_owner(asset_data=self.asset_data) and a.get('aboutMe') is not None and len(
                    a.get('aboutMe', '')) == 0:
                row = col.row()
                row.enabled = False
                row.label(text='Please introduce yourself to the community!')

                op = col.operator('wm.blenderkit_url', text='Edit your profile')
                op.url = 'https://www.blenderkit.com/profile'
                op.tooltip = 'Edit your profile on BlenderKit webpage'

            button_row = author_box.row()
            button_row.scale_y = 2.0

            if a.get('aboutMeUrl') is not None:
                url = a['aboutMeUrl']
                text = url
                if len(url) > 25:
                    text = url[:25] + '...'
            else:
                url = paths.get_author_gallery_url(a['id'])
                text = "Open Author's Profile"

            op = button_row.operator('wm.url_open', text=text)
            op.url = url

            op = button_row.operator('view3d.blenderkit_search', text="Find Assets By Author")
            op.keywords = ''
            op.author_id = self.asset_data['author']['id']

    def draw_thumbnail_box(self, layout, width=250):
        layout.emboss = 'NORMAL'

        box_thumbnail = layout.box()

        box_thumbnail.scale_y = .4
        box_thumbnail.template_icon(icon_value=self.img.preview.icon_id, scale=width * .12)

        # row = box_thumbnail.row()
        # row.scale_y = 3
        # op = row.operator('view3d.asset_drag_drop', text='Drag & Drop from here', depress=True)

        row = box_thumbnail.row()
        row.alignment = 'EXPAND'

        # display_ratings = can_display_ratings(self.asset_data)
        rc = self.asset_data.get('ratingsCount')
        show_rating_threshold = 0
        show_rating_prompt_threshold = 5

        if rc:
            rcount = min(rc['quality'], rc['workingHours'])
        else:
            rcount = 0
        if rcount >= show_rating_threshold or upload.can_edit_asset(asset_data=self.asset_data):
            s = numeric_to_str(self.asset_data['score'])
            q = numeric_to_str(self.asset_data['ratingsAverage'].get('quality'))
            c = numeric_to_str(self.asset_data['ratingsAverage'].get('workingHours'))
        else:
            s = '-'
            q = '-'
            c = '-'

        pcoll = icons.icon_collections["main"]

        row.emboss = 'NONE'
        op = row.operator('wm.blenderkit_tooltip', text=str(s), icon_value=pcoll['trophy'].icon_id)
        op.tooltip = 'Asset score calculated from averaged user ratings. \n\n' \
                     'Score = quality × complexity × 10*\n\n *Happiness multiplier'
        row.label(text='   ')

        tooltip_extension = f'.\n\nRatings results are shown for assets with more than {show_rating_threshold} ratings'
        op = row.operator('wm.blenderkit_tooltip', text=str(q), icon='SOLO_ON')
        op.tooltip = f"Quality, average from {rc['quality']} ratings" \
                     f"{tooltip_extension if rcount <= show_rating_threshold else ''}"
        row.label(text='   ')

        op = row.operator('wm.blenderkit_tooltip', text=str(c), icon_value=pcoll['dumbbell'].icon_id)
        op.tooltip = f"Complexity, average from {rc['workingHours']} ratings" \
                     f"{tooltip_extension if rcount <= show_rating_threshold else ''}"

        if rcount <= show_rating_prompt_threshold:
            box_thumbnail.alert = True
            box_thumbnail.label(text=f"")
            box_thumbnail.label(text=f"This asset has only {rcount} rating{'' if rcount == 1 else 's'}, please rate.")
            # box_thumbnail.label(text=f"Please rate this asset.")

    def draw_menu_desc_author(self, context, layout, width=330):
        box = layout.column()

        box.emboss = 'NORMAL'
        # left - tooltip & params
        row = box.row()
        split_factor = 0.7
        split_left = row.split(factor=split_factor)
        col = split_left.column()
        width_left = int(width * split_factor)
        self.draw_description(col, width=width_left)

        self.draw_properties(col, width=width_left)

        # right - menu
        split_right = split_left.split()
        col = split_right.column()
        self.draw_menu(context, col)

        # author
        self.draw_author_area(context, box, width=width)

        # self.draw_author_area(context, box, width=width)
        #
        # col = box.column_flow(columns=2)
        # self.draw_menu(context, col)
        #
        #
        # # self.draw_description(box, width=int(width))
        # self.draw_properties(box, width=int(width))

    def draw(self, context):
        ui_props = context.scene.blenderkitUI

        sr = bpy.context.window_manager['search results']
        asset_data = sr[ui_props.active_index]
        self.asset_data = asset_data
        layout = self.layout
        # top draggabe bar with name of the asset
        top_row = layout.row()
        top_drag_bar = top_row.box()
        bcats  = bpy.context.window_manager['bkit_categories']

        cat_path = categories.get_category_path(bcats,
                                                self.asset_data['category'])[1:]


        cat_path_names = categories.get_category_name_path(bcats,
                                        self.asset_data['category'])[1:]

        aname = asset_data['displayName']
        aname = aname[0].upper() + aname[1:]

        if 1:
            name_row = top_drag_bar.row()
            # name_row = name_row.split(factor=0.5)
            # name_row = name_row.column()
            # name_row = name_row.row()
            for i, c in enumerate(cat_path):
                cat_name = cat_path_names[i]
                op = name_row.operator('view3d.blenderkit_asset_bar', text=cat_name + ' >', emboss=True)
                op.do_search = True
                op.keep_running = True
                op.tooltip = f"Browse {cat_name} category"
                op.category = c
                # name_row.label(text='>')

            name_row.label(text=aname)
            push_op_left(name_row, strength = 3)
        # for i,c in enumerate(cat_path_names):
        #     cat_path_names[i] = c.capitalize()
        # cat_path_names_string = ' > '.join(cat_path_names)
        # # box.label(text=cat_path)
        #
        #
        #
        #
        # # name_row.label(text='                                           ')
        # top_drag_bar.label(text=f'{cat_path_names_string} > {aname}')

        # left side
        row = layout.row(align=True)

        split_ratio = 0.45
        split_left = row.split(factor=split_ratio)
        left_column = split_left.column()
        self.draw_thumbnail_box(left_column, width=int(self.width * split_ratio))
        # self.draw_description(left_column, width = int(self.width*split_ratio))
        # right split
        split_right = split_left.split()
        self.draw_menu_desc_author(context, split_right, width=int(self.width * (1 - split_ratio)))

        if not utils.user_is_owner(asset_data=asset_data):
            # Draw ratings, but not for owners of assets - doesn't make sense.
            ratings_box = layout.box()
            ratings.draw_ratings_menu(self, context, ratings_box)
        # else:
        #     ratings_box.label('Here you should find ratings, but you can not rate your own assets ;)')

        tip_box = layout.box()
        tip_box.label(text=self.tip)

    def execute(self, context):
        wm = context.window_manager
        ui_props = context.scene.blenderkitUI
        ui_props.draw_tooltip = False
        sr = bpy.context.window_manager['search results']
        asset_data = sr[ui_props.active_index]
        self.img = ui.get_large_thumbnail_image(asset_data)
        utils.img_to_preview(self.img, copy_original = True)

        self.asset_type = asset_data['assetType']
        self.asset_id = asset_data['id']
        # self.tex = utils.get_hidden_texture(self.img)
        # self.tex.update_tag()

        authors = bpy.context.window_manager['bkit authors']
        a = authors.get(asset_data['author']['id'])
        if a.get('gravatarImg') is not None:
            self.gimg = utils.get_hidden_image(a['gravatarImg'], a['gravatarHash'])

        bl_label = asset_data['name']
        self.tip = search.get_random_tip()
        self.tip = self.tip.replace('\n', '')

        # pre-fill ratings
        self.prefill_ratings()

        return wm.invoke_popup(self, width=self.width)


class OBJECT_MT_blenderkit_login_menu(bpy.types.Menu):
    bl_label = "BlenderKit login/signup:"
    bl_idname = "OBJECT_MT_blenderkit_login_menu"

    def draw(self, context):
        layout = self.layout

        # utils.label_multiline(layout, text=message)
        draw_login_buttons(layout)


class SetCategoryOperator(bpy.types.Operator):
    """Visit subcategory"""
    bl_idname = "view3d.blenderkit_set_category"
    bl_label = "BlenderKit Set Active Category"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    category: bpy.props.StringProperty(
        name="Category",
        description="set this category active",
        default="")

    asset_type: bpy.props.StringProperty(
        name="Asset Type",
        description="asset type",
        default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        acat = bpy.context.window_manager['active_category'][self.asset_type]
        if self.category == '':
            acat.remove(acat[-1])
        else:
            acat.append(self.category)
        # we have to write back to wm. Thought this should happen with original list.
        bpy.context.window_manager['active_category'][self.asset_type] = acat
        return {'FINISHED'}


class UrlPopupDialog(bpy.types.Operator):
    """Generate Cycles thumbnail for model assets"""
    bl_idname = "wm.blenderkit_url_dialog"
    bl_label = "BlenderKit message:"
    bl_options = {'REGISTER', 'INTERNAL'}

    url: bpy.props.StringProperty(
        name="Url",
        description="url",
        default="")

    link_text: bpy.props.StringProperty(
        name="Url",
        description="url",
        default="Go to website")

    message: bpy.props.StringProperty(
        name="Text",
        description="text",
        default="")

    # @classmethod
    # def poll(cls, context):
    #     return bpy.context.view_layer.objects.active is not None

    def draw(self, context):
        layout = self.layout
        utils.label_multiline(layout, text=self.message, width=300)

        layout.active_default = True
        op = layout.operator("wm.url_open", text=self.link_text, icon='QUESTION')
        if not utils.user_logged_in():
            utils.label_multiline(layout,
                                  text='Already subscribed? You need to login to access your Full Plan.',
                                  width=300)

            layout.operator_context = 'EXEC_DEFAULT'
            layout.operator("wm.blenderkit_login", text="Login",
                            icon='URL').signup = False
        op.url = self.url

    def execute(self, context):
        # start_thumbnailer(self, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=300)


class LoginPopupDialog(bpy.types.Operator):
    """Popup a dialog which enables the user to log in after being logged out automatically."""
    bl_idname = "wm.blenderkit_login_dialog"
    bl_label = "BlenderKit login"
    bl_options = {'REGISTER', 'INTERNAL'}

    message: bpy.props.StringProperty(
        name="Message",
        description="",
        default="Your were logged out from BlenderKit. Please login again. ")

    # @classmethod
    # def poll(cls, context):
    #     return bpy.context.view_layer.objects.active is not None

    def draw(self, context):
        layout = self.layout
        utils.label_multiline(layout, text=self.message)

        layout.active_default = True
        op = layout.operator
        op = layout.operator("wm.url_open", text=self.link_text, icon='QUESTION')
        op.url = self.url

    def execute(self, context):
        # start_thumbnailer(self, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self)


def draw_panel_categories(self, context):
    s = context.scene
    ui_props = s.blenderkitUI
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    layout = self.layout
    # row = layout.row()
    # row.prop(ui_props, 'asset_type', expand=True, icon_only=True)
    wm = bpy.context.window_manager
    if wm.get('bkit_categories') == None:
        return
    col = layout.column(align=True)
    if wm.get('active_category') is not None:
        acat = wm['active_category'][ui_props.asset_type]
        if len(acat) > 1:
            # we are in subcategory, so draw the parent button
            op = col.operator('view3d.blenderkit_set_category', text='...', icon='FILE_PARENT')
            op.asset_type = ui_props.asset_type
            op.category = ''
    cats = categories.get_category(wm['bkit_categories'], cat_path=acat)
    # draw freebies only in models parent category
    # if ui_props.asset_type == 'MODEL' and len(acat) == 1:
    #     op = col.operator('view3d.blenderkit_asset_bar', text='freebies')
    #     op.free_only = True

    for c in cats['children']:
        if c['assetCount'] > 0 or (utils.profile_is_validator() and user_preferences.categories_fix):
            row = col.row(align=True)
            if len(c['children']) > 0 and c['assetCount'] > 15 or (
                    utils.profile_is_validator() and user_preferences.categories_fix):
                row = row.split(factor=.8, align=True)
            # row = split.split()
            ctext = '%s (%i)' % (c['name'], c['assetCount'])

            preferences = bpy.context.preferences.addons['blenderkit'].preferences
            if preferences.experimental_features:
                op = row.operator('view3d.blenderkit_asset_bar_widget', text=ctext)
            else:
                op = row.operator('view3d.blenderkit_asset_bar', text=ctext)
                op.do_search = True
                op.keep_running = True
                op.tooltip = f"Browse {c['name']} category"
                op.category = c['slug']
            if len(c['children']) > 0 and c['assetCount'] > 15 or (
                    utils.profile_is_validator() and user_preferences.categories_fix):
                # row = row.split()
                op = row.operator('view3d.blenderkit_set_category', text='>>')
                op.asset_type = ui_props.asset_type
                op.category = c['slug']
                # for c1 in c['children']:
                #     if c1['assetCount']>0:
                #         row = col.row()
                #         split = row.split(percentage=.2)
                #         row = split.split()
                #         row = split.split()
                #         ctext = '%s (%i)' % (c1['name'], c1['assetCount'])
                #         op = row.operator('view3d.blenderkit_search', text=ctext)
                #         op.category = c1['slug']


class VIEW3D_PT_blenderkit_downloads(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_downloads"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Downloads"

    @classmethod
    def poll(cls, context):
        return len(download.download_threads) > 0

    def draw(self, context):
        layout = self.layout
        for i, threaddata in enumerate(download.download_threads):
            tcom = threaddata[2]
            asset_data = threaddata[1]
            row = layout.row()
            row.label(text=asset_data['name'])
            row.label(text=str(int(tcom.progress)) + ' %')
            op = row.operator('scene.blenderkit_download_kill', text='', icon='CANCEL')
            op.thread_index = i
            if tcom.passargs.get('retry_counter', 0) > 0:
                row = layout.row()
                row.label(text='failed. retrying ... ', icon='ERROR')
                row.label(text=str(tcom.passargs["retry_counter"]))

                layout.separator()


def header_search_draw(self, context):
    '''Top bar menu in 3D view'''

    if not utils.guard_from_crash():
        return;

    preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if preferences.search_in_header:
        layout = self.layout
        s = bpy.context.scene
        ui_props = s.blenderkitUI
        if ui_props.asset_type == 'MODEL':
            props = s.blenderkit_models
        if ui_props.asset_type == 'MATERIAL':
            props = s.blenderkit_mat
        if ui_props.asset_type == 'BRUSH':
            props = s.blenderkit_brush
        if ui_props.asset_type == 'HDR':
            props = s.blenderkit_HDR
        if ui_props.asset_type == 'SCENE':
            props = s.blenderkit_scene

        # the center snap menu is in edit and object mode if tool settings are off.
        if context.space_data.show_region_tool_header == True or context.mode[:4] not in ('EDIT', 'OBJE'):
            layout.separator_spacer()
        layout.prop(ui_props, "asset_type", expand=True, icon_only=True, text='', icon='URL')
        layout.prop(props, "search_keywords", text="", icon='VIEWZOOM')
        draw_assetbar_show_hide(layout, props)


def ui_message(title, message):
    def draw_message(self, context):
        layout = self.layout
        utils.label_multiline(layout, text=message, width=400)

    bpy.context.window_manager.popup_menu(draw_message, title=title, icon='INFO')


# We can store multiple preview collections here,
# however in this example we only store "main"
preview_collections = {}

classes = (
    SetCategoryOperator,
    VIEW3D_PT_blenderkit_profile,
    VIEW3D_PT_blenderkit_login,
    VIEW3D_PT_blenderkit_unified,
    VIEW3D_PT_blenderkit_advanced_model_search,
    VIEW3D_PT_blenderkit_advanced_material_search,
    VIEW3D_PT_blenderkit_categories,
    VIEW3D_PT_blenderkit_import_settings,
    VIEW3D_PT_blenderkit_model_properties,
    NODE_PT_blenderkit_material_properties,
    # VIEW3D_PT_blenderkit_ratings,
    VIEW3D_PT_blenderkit_downloads,
    # OBJECT_MT_blenderkit_resolution_menu,
    OBJECT_MT_blenderkit_asset_menu,
    OBJECT_MT_blenderkit_login_menu,
    AssetPopupCard,
    UrlPopupDialog,
    BlenderKitWelcomeOperator,
)


def register_ui_panels():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_editor_menus.append(header_search_draw)


def unregister_ui_panels():
    bpy.types.VIEW3D_MT_editor_menus.remove(header_search_draw)
    for c in classes:
        # print('unregister', c)
        bpy.utils.unregister_class(c)
