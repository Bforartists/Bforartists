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
    import importlib

    paths = importlib.reload(paths)
    ratings = importlib.reload(ratings)
    utils = importlib.reload(utils)
    download = importlib.reload(download)
    categories = importlib.reload(categories)
    icons = importlib.reload(icons)
else:
    from blenderkit import paths, ratings, utils, download, categories, icons

from bpy.types import (
    Panel
)

import bpy


def label_multiline(layout, text='', icon='NONE', width=-1):
    ''' draw a ui label, but try to split it in multiple lines.'''
    if text.strip() == '':
        return
    lines = text.split('\n')
    if width > 0:
        threshold = int(width / 5.5)
    else:
        threshold = 35
    maxlines = 8
    li = 0
    for l in lines:
        while len(l) > threshold:
            i = l.rfind(' ', 0, threshold)
            if i < 1:
                i = threshold
            l1 = l[:i]
            layout.label(text=l1, icon=icon)
            icon = 'NONE'
            l = l[i:].lstrip()
            li += 1
            if li > maxlines:
                break;
        if li > maxlines:
            break;
        layout.label(text=l, icon=icon)
        icon = 'NONE'


#   this was moved to separate interface:

def draw_ratings(layout, context):
    # layout.operator("wm.url_open", text="Read rating instructions", icon='QUESTION').url = 'https://support.google.com/?hl=en'
    asset = utils.get_active_asset()
    # the following shouldn't happen at all in an optimal case,
    # this function should run only when asset was already checked to be existing
    if asset == None:
        return;

    if not utils.user_logged_in():
        label_multiline(layout, text='Please login or sign up '
                                     'to rate assets.')
        return
    bkit_ratings = asset.bkit_ratings

    ratings.draw_rating(layout, bkit_ratings, 'rating_quality', 'Quality')
    layout.separator()
    layout.prop(bkit_ratings, 'rating_work_hours')
    w = context.region.width

    # layout.label(text='problems')
    # layout.prop(bkit_ratings, 'rating_problems', text='')
    # layout.label(text='compliments')
    # layout.prop(bkit_ratings, 'rating_compliments', text='')

    # row = layout.row()
    # op = row.operator("object.blenderkit_rating_upload", text="Send rating", icon='URL')
    # return op

def draw_not_logged_in(source):
    title = "User not logged in"
    def draw_message(source, context):
        layout = source.layout
        label_multiline(layout, text='Please login or sign up '
                                               'to upload files.')
        draw_login_buttons(layout)
    bpy.context.window_manager.popup_menu(draw_message, title=title, icon='INFO')

def draw_upload_common(layout, props, asset_type, context):
    op = layout.operator("wm.url_open", text="Read upload instructions",
                         icon='QUESTION')
    if asset_type == 'MODEL':
        op.url = paths.BLENDERKIT_MODEL_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'MATERIAL':
        op.url = paths.BLENDERKIT_MATERIAL_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'BRUSH':
        op.url = paths.BLENDERKIT_BRUSH_UPLOAD_INSTRUCTIONS_URL

    row = layout.row(align=True)
    if props.upload_state != '':
        label_multiline(layout, text=props.upload_state, width=context.region.width)
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
    if asset_type == 'MODEL' and props.subcategory != '':  # by now block this for other asset types.
        layout.prop(props, 'subcategory')

    layout.prop(props, 'is_private', expand=True)
    if props.is_private == 'PUBLIC':
        layout.prop(props, 'license')


def poll_local_panels():
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    return user_preferences.panel_behaviour == 'BOTH' or user_preferences.panel_behaviour == 'LOCAL'


def prop_needed(layout, props, name, value, is_not_filled=''):
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


def draw_panel_model_upload(self, context):
    ob = bpy.context.active_object
    while ob.parent is not None:
        ob = ob.parent
    props = ob.blenderkit

    layout = self.layout

    draw_upload_common(layout, props, 'MODEL', context)

    prop_needed(layout, props, 'name', props.name)

    col = layout.column()
    if props.is_generating_thumbnail:
        col.enabled = False
    prop_needed(col, props, 'thumbnail', props.has_thumbnail, False)
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
        label_multiline(layout, text=props.thumbnail_generating_state)

    layout.prop(props, 'description')
    layout.prop(props, 'tags')
    # prop_needed(layout, props, 'style', props.style)
    # prop_needed(layout, props, 'production_level', props.production_level)
    layout.prop(props, 'style')
    layout.prop(props, 'production_level')

    layout.prop(props, 'condition')
    layout.prop(props, 'is_free')
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
    if bpy.app.debug_value != -1:
        layout.label(text='Scene upload not Implemented')
        return
    draw_upload_common(layout, props, 'SCENE', context)

    #    layout = layout.column()

    # row = layout.row()

    # if props.dimensions[0] + props.dimensions[1] == 0 and props.face_count == 0:
    #     icon = 'ERROR'
    #     layout.operator("object.blenderkit_auto_tags", text='Auto fill tags', icon=icon)
    # else:
    #     layout.operator("object.blenderkit_auto_tags", text='Auto fill tags')

    prop_needed(layout, props, 'name', props.name)

    col = layout.column()
    # if props.is_generating_thumbnail:
    #     col.enabled = False
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
    #     label_multiline(layout, text = props.thumbnail_generating_state)

    layout.prop(props, 'description')
    layout.prop(props, 'tags')
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
    label_multiline(layout, text=props.report, icon=icon)
    if props.report == 'You need Full plan to get this item.':
        layout.operator("wm.url_open", text="Get Full plan", icon='URL').url = paths.BLENDERKIT_PLANS

    layout.prop(props, "search_style")
    layout.prop(props, "own_only")
    layout.prop(props, "free_only")

    # if props.search_style == 'OTHER':
    #     layout.prop(props, "search_style_other")
    # layout.prop(props, "search_engine")
    # col = layout.column()
    # layout.prop(props, 'append_link', expand=True, icon_only=False)
    # layout.prop(props, 'import_as', expand=True, icon_only=False)

    layout.prop(props, "search_advanced")
    if props.search_advanced:
        layout.separator()

        # layout.label(text = "common searches keywords:")
        # layout.prop(props, "search_global_keywords", text = "")
        # layout.prop(props, "search_modifier_keywords")
        # if props.search_engine == 'OTHER':
        #     layout.prop(props, "search_engine_keyword")

        # AGE
        layout.prop(props, "search_condition", text='Condition')  # , text ='condition of object new/old e.t.c.')

        # DESIGN YEAR
        layout.prop(props, "search_design_year", text='designed in ( min - max )')
        if props.search_design_year:
            row = layout.row(align=True)
            row.prop(props, "search_design_year_min", text='min')
            row.prop(props, "search_design_year_max", text='max')

        # POLYCOUNT
        layout.prop(props, "search_polycount", text='Poly count in ( min - max )')
        if props.search_polycount:
            row = layout.row(align=True)
            row.prop(props, "search_polycount_min", text='min')
            row.prop(props, "search_polycount_max", text='max')

        # TEXTURE RESOLUTION
        layout.prop(props, "search_texture_resolution", text='texture resolution ( min - max )')
        if props.search_texture_resolution:
            row = layout.row(align=True)
            row.prop(props, "search_texture_resolution_min", text='min')
            row.prop(props, "search_texture_resolution_max", text='max')

        # FILE SIZE
        layout.prop(props, "search_file_size", text='File size ( min - max )')
        if props.search_file_size:
            row = layout.row(align=True)
            row.prop(props, "search_file_size_min", text='min')
            row.prop(props, "search_file_size_max", text='max')

        # layout.prop(props, "search_procedural", expand=True)
        # ADULT
        # layout.prop(props, "search_adult")  # , text ='condition of object new/old e.t.c.')

    draw_panel_categories(self, context)

    layout.separator()
    layout.label(text='Import method:')
    row = layout.row()
    row.prop(props, 'append_method', expand=True, icon_only=False)
    layout.prop(props, 'randomize_rotation')
    if props.randomize_rotation:
        layout.prop(props, 'randomize_rotation_amount')


def draw_panel_scene_search(self, context):
    s = context.scene
    props = s.blenderkit_scene
    layout = self.layout
    # layout.label(text = "common search properties:")
    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)
    layout.prop(props, "own_only")
    label_multiline(layout, text=props.report)

    # layout.prop(props, "search_style")
    # if props.search_style == 'OTHER':
    #     layout.prop(props, "search_style_other")
    # layout.prop(props, "search_engine")
    layout.separator()
    draw_panel_categories(self, context)


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
            label_multiline(layout, text='To upload this asset to BlenderKit, go to the Find and Upload Assets panel.')
            layout.prop(o, 'name')

        if o.get('asset_data') is not None:
            ad = o['asset_data']
            layout.label(text=str(ad['name']))
            if o.instance_type == 'COLLECTION' and o.instance_collection is not None:
                layout.operator('object.blenderkit_bring_to_scene', text='Bring to scene')

            draw_panel_model_rating(self, context)

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
                layout.label(text='Me: %s %s' % (me['firstName'], me['lastName']))
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
                    if pn =='Free':
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
    o = bpy.context.active_object
    draw_ratings(self.layout, context)  # , props)
    # op.asset_type = 'MODEL'


def draw_panel_material_upload(self, context):
    o = bpy.context.active_object
    mat = bpy.context.active_object.active_material

    props = mat.blenderkit
    layout = self.layout

    draw_upload_common(layout, props, 'MATERIAL', context)

    prop_needed(layout, props, 'name', props.name)
    layout.prop(props, 'description')
    layout.prop(props, 'style')
    # if props.style == 'OTHER':
    #     layout.prop(props, 'style_other')
    # layout.prop(props, 'engine')
    # if props.engine == 'OTHER':
    #     layout.prop(props, 'engine_other')
    layout.prop(props, 'tags')
    # layout.prop(props,'shaders')#TODO autofill on upload
    # row = layout.row()
    layout.prop(props, 'is_free')

    layout.prop(props, 'pbr')
    layout.prop(props, 'uv')
    layout.prop(props, 'animated')
    layout.prop(props, 'texture_size_meters')

    # THUMBNAIL
    row = layout.row()
    if props.is_generating_thumbnail:
        row.enabled = False
    prop_needed(row, props, 'thumbnail', props.has_thumbnail, False)

    if props.is_generating_thumbnail:
        row = layout.row(align=True)
        row.label(text=props.thumbnail_generating_state, icon='RENDER_STILL')
        op = row.operator('object.kill_bg_process', text="", icon='CANCEL')
        op.process_source = 'MATERIAL'
        op.process_type = 'THUMBNAILER'
    elif props.thumbnail_generating_state != '':
        label_multiline(layout, text=props.thumbnail_generating_state)

    if bpy.context.scene.render.engine in ('CYCLES', 'BLENDER_EEVEE'):
        layout.operator("object.blenderkit_material_thumbnail", text='Render thumbnail with Cycles', icon='EXPORT')

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
    layout.prop(props, "own_only")
    label_multiline(layout, text=props.report)

    # layout.prop(props, 'search_style')
    # if props.search_style == 'OTHER':
    #     layout.prop(props, 'search_style_other')
    # layout.prop(props, 'search_engine')
    # if props.search_engine == 'OTHER':
    #     layout.prop(props, 'search_engine_other')

    layout.prop(props, "search_advanced")
    if props.search_advanced:
        layout.separator()

        layout.label(text='texture types')
        col = layout.column()
        col.prop(props, "search_procedural", expand=True)

        if props.search_procedural == 'TEXTURE_BASED':
            # TEXTURE RESOLUTION
            layout.prop(props, "search_texture_resolution", text='texture resolution ( min - max )')
            if props.search_texture_resolution:
                row = layout.row(align=True)
                row.prop(props, "search_texture_resolution_min", text='min')
                row.prop(props, "search_texture_resolution_max", text='max')

        # FILE SIZE
        layout.prop(props, "search_file_size", text='File size ( min - max in mb)')
        if props.search_file_size:
            row = layout.row(align=True)
            row.prop(props, "search_file_size_min", text='min')
            row.prop(props, "search_file_size_max", text='max')

    draw_panel_categories(self, context)

    layout.prop(props, 'automap')


def draw_panel_material_ratings(self, context):
    draw_ratings(self.layout, context)  # , props)
    # op.asset_type = 'MATERIAL'


def draw_panel_brush_upload(self, context):
    brush = utils.get_active_brush()
    if brush is not None:
        props = brush.blenderkit

        layout = self.layout

        draw_upload_common(layout, props, 'BRUSH', context)

        layout.prop(props, 'name')
        layout.prop(props, 'description')
        layout.prop(props, 'tags')


def draw_panel_brush_search(self, context):
    wm = context.scene
    props = wm.blenderkit_brush

    layout = self.layout
    row = layout.row()
    row.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    draw_assetbar_show_hide(row, props)
    layout.prop(props, "own_only")

    label_multiline(layout, text=props.report)
    draw_panel_categories(self, context)


def draw_panel_brush_ratings(self, context):
    # props = utils.get_brush_props(context)
    draw_ratings(self.layout, context)  # , props)
    #
    # op.asset_type = 'BRUSH'


def draw_login_buttons(layout):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    if user_preferences.login_attempt:
        draw_login_progress(layout)
    else:
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
    # bl_parent_id = "VIEW3D_PT_blenderkit_unified"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Advanced search options"

    @classmethod
    def poll(cls, context):
        return True

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

        # AGE
        layout.prop(props, "search_condition", text='Condition')  # , text ='condition of object new/old e.t.c.')

        # DESIGN YEAR
        layout.prop(props, "search_design_year", text='designed in ( min - max )')
        if props.search_design_year:
            row = layout.row(align=True)
            row.prop(props, "search_design_year_min", text='min')
            row.prop(props, "search_design_year_max", text='max')

        # POLYCOUNT
        layout.prop(props, "search_polycount", text='Poly count in ( min - max )')
        if props.search_polycount:
            row = layout.row(align=True)
            row.prop(props, "search_polycount_min", text='min')
            row.prop(props, "search_polycount_max", text='max')

        # TEXTURE RESOLUTION
        layout.prop(props, "search_texture_resolution", text='texture resolution ( min - max )')
        if props.search_texture_resolution:
            row = layout.row(align=True)
            row.prop(props, "search_texture_resolution_min", text='min')
            row.prop(props, "search_texture_resolution_max", text='max')

        # FILE SIZE
        layout.prop(props, "search_file_size", text='File size ( min - max )')
        if props.search_file_size:
            row = layout.row(align=True)
            row.prop(props, "search_file_size_min", text='min')
            row.prop(props, "search_file_size_max", text='max')

        # layout.prop(props, "search_procedural", expand=True)
        # ADULT
        # layout.prop(props, "search_adult")  # , text ='condition of object new/old e.t.c.')


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
        # row = layout.row(align = True)
        # split = row.split(factor=.5)
        # row.prop(ui_props, 'asset_type', expand=True, icon_only=True)
        # row = layout.column(align = False)
        layout.prop(ui_props, 'asset_type', expand=False, text='')

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
        #     label_multiline(layout, text="It's better to save your file first.", width=w)
        #     layout.alert = False
        #     layout.separator()

        if ui_props.down_up == 'SEARCH':
            if utils.profile_is_validator():
                search_props = utils.get_search_props()
                layout.prop(search_props, 'search_verification_status')
            if ui_props.asset_type == 'MODEL':
                # noinspection PyCallByClass
                draw_panel_model_search(self, context)
            if ui_props.asset_type == 'SCENE':
                # noinspection PyCallByClass
                draw_panel_scene_search(self, context)

            elif ui_props.asset_type == 'MATERIAL':
                draw_panel_material_search(self, context)
            elif ui_props.asset_type == 'BRUSH':
                if context.sculpt_object or context.image_paint_object:
                    # noinspection PyCallByClass
                    draw_panel_brush_search(self, context)
                else:
                    label_multiline(layout, text='switch to paint or sculpt mode.', width=context.region.width)
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
                label_multiline(layout, rtext, icon='ERROR', width=w)
                return;

            if ui_props.asset_type == 'MODEL':
                # label_multiline(layout, "Uploaded models won't be available in b2.79", icon='ERROR')
                if bpy.context.view_layer.objects.active is not None:
                    draw_panel_model_upload(self, context)
                else:
                    layout.label(text='selet object to upload')
            elif ui_props.asset_type == 'SCENE':
                draw_panel_scene_upload(self, context)

            elif ui_props.asset_type == 'MATERIAL':
                # label_multiline(layout, "Uploaded materials won't be available in b2.79", icon='ERROR')

                if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.active_material is not None:
                    draw_panel_material_upload(self, context)
                else:
                    label_multiline(layout, text='select object with material to upload materials', width=w)

            elif ui_props.asset_type == 'BRUSH':
                if context.sculpt_object or context.image_paint_object:
                    draw_panel_brush_upload(self, context)
                else:
                    layout.label(text='switch to paint or sculpt mode.')

        elif ui_props.down_up == 'RATING':  # the poll functions didn't work here, don't know why.

            if ui_props.asset_type == 'MODEL':
                # TODO improve poll here to parenting structures
                if bpy.context.view_layer.objects.active is not None and bpy.context.active_object.get(
                        'asset_data') != None:
                    ad = bpy.context.active_object.get('asset_data')
                    layout.label(text=ad['name'])
                    draw_panel_model_rating(self, context)
            if ui_props.asset_type == 'MATERIAL':
                if bpy.context.view_layer.objects.active is not None and \
                        bpy.context.active_object.active_material is not None and \
                        bpy.context.active_object.active_material.blenderkit.asset_base_id != '':
                    layout.label(text=bpy.context.active_object.active_material.blenderkit.name + ' :')
                    # noinspection PyCallByClass
                    draw_panel_material_ratings(self, context)
            if ui_props.asset_type == 'BRUSH':
                if context.sculpt_object or context.image_paint_object:
                    props = utils.get_brush_props(context)
                    if props.asset_base_id != '':
                        layout.label(text=props.name + ' :')
                        # noinspection PyCallByClass
                        draw_panel_brush_ratings(self, context)
            if ui_props.asset_type == 'TEXTURE':
                layout.label(text='not yet implemented')


class OBJECT_MT_blenderkit_asset_menu(bpy.types.Menu):
    bl_label = "Asset options:"
    bl_idname = "OBJECT_MT_blenderkit_asset_menu"

    def draw(self, context):
        layout = self.layout
        ui_props = context.scene.blenderkitUI

        sr = bpy.context.scene['search results']
        sr = bpy.context.scene['search results orig']['results']
        asset_data = sr[ui_props.active_index]
        author_id = str(asset_data['author']['id'])

        wm = bpy.context.window_manager
        if wm.get('bkit authors') is not None:
            a = bpy.context.window_manager['bkit authors'].get(author_id)
            if a is not None:
                # utils.p('author:', a)
                if a.get('aboutMeUrl') is not None:
                    op = layout.operator('wm.url_open', text="Open Author's Website")
                    op.url = a['aboutMeUrl']

                op = layout.operator('view3d.blenderkit_search', text="Show Assets By Author")
                op.keywords = ''
                op.author_id = author_id

        op = layout.operator('view3d.blenderkit_search', text='Search Similar')
        op.keywords = asset_data['name'] + ' ' + asset_data['description'] + ' ' + ' '.join(asset_data['tags'])
        if asset_data.get('canDownload') != 0:
            if len(bpy.context.selected_objects)>0 and ui_props.asset_type == 'MODEL':
                aob = bpy.context.active_object
                if aob is None:
                    aob = bpy.context.selected_objects[0]
                op = layout.operator('scene.blenderkit_download', text='Replace Active Models')
                op.asset_type = ui_props.asset_type
                op.asset_index = ui_props.active_index
                op.model_location = aob.location
                op.model_rotation = aob.rotation_euler
                op.target_object = aob.name
                op.material_target_slot = aob.active_material_index
                op.replace = True

        wm = bpy.context.window_manager
        profile = wm.get('bkit profile')
        if profile is not None:
            # validation
            if utils.profile_is_validator():
                layout.label(text='Validation tools:')
                if asset_data['verificationStatus'] != 'uploaded':
                    op = layout.operator('object.blenderkit_change_status', text='set Uploaded')
                    op.asset_id = asset_data['id']
                    op.state = 'uploaded'
                if asset_data['verificationStatus'] != 'validated':
                    op = layout.operator('object.blenderkit_change_status', text='Validate')
                    op.asset_id = asset_data['id']
                    op.state = 'validated'
                if asset_data['verificationStatus'] != 'on_hold':
                    op = layout.operator('object.blenderkit_change_status', text='Put on Hold')
                    op.asset_id = asset_data['id']
                    op.state = 'on_hold'
                if asset_data['verificationStatus'] != 'rejected':
                    op = layout.operator('object.blenderkit_change_status', text='Reject')
                    op.asset_id = asset_data['id']
                    op.state = 'rejected'

            if author_id == str(profile['user']['id']):
                layout.label(text='Management tools:')
                row = layout.row()
                row.operator_context = 'INVOKE_DEFAULT'
                op = row.operator('object.blenderkit_change_status', text='Delete')
                op.asset_id = asset_data['id']
                op.state = 'deleted'
            # else:
            #     #not an author - can rate
            #     draw_ratings(layout, context)


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
        label_multiline(layout, text=self.message)

        layout.active_default = True
        op = layout.operator("wm.url_open", text=self.link_text, icon='QUESTION')
        op.url = self.url

    def execute(self, context):
        # start_thumbnailer(self, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.bl_label = 'ahoj'
        wm = context.window_manager

        return wm.invoke_props_dialog(self)


def draw_panel_categories(self, context):
    s = context.scene
    ui_props = s.blenderkitUI
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    layout = self.layout
    # row = layout.row()
    # row.prop(ui_props, 'asset_type', expand=True, icon_only=True)
    layout.separator()

    layout.label(text='Categories')
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
        if c['assetCount'] > 0:
            row = col.row(align=True)
            if len(c['children']) > 0 and c['assetCount'] > 15:
                row = row.split(factor=.8, align=True)
            # row = split.split()
            ctext = '%s (%i)' % (c['name'], c['assetCount'])
            op = row.operator('view3d.blenderkit_asset_bar', text=ctext)
            op.do_search = True
            op.keep_running = True
            op.category = c['slug']
            # TODO enable subcategories, now not working due to some bug on server probably
            if len(c['children']) > 0 and c['assetCount'] > 15:
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
        for threaddata in download.download_threads:
            tcom = threaddata[2]
            asset_data = threaddata[1]
            row = layout.row()
            row.label(text=asset_data['name'])
            row.label(text=str(int(tcom.progress)) + ' %')
            row.operator('scene.blenderkit_download_kill', text='', icon='CANCEL')
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

        # the center snap menu is in edit and object mode if tool settings are off.
        if context.space_data.show_region_tool_header == True or context.mode[:4] not in ('EDIT', 'OBJE'):
            layout.separator_spacer()
        layout.prop(ui_props, "asset_type", text='', icon='URL')
        layout.prop(props, "search_keywords", text="", icon='VIEWZOOM')
        draw_assetbar_show_hide(layout, props)


# We can store multiple preview collections here,
# however in this example we only store "main"
preview_collections = {}
classess = (
    SetCategoryOperator,
    VIEW3D_PT_blenderkit_profile,
    VIEW3D_PT_blenderkit_login,
    VIEW3D_PT_blenderkit_unified,
    # VIEW3D_PT_blenderkit_advanced_model_search,
    VIEW3D_PT_blenderkit_model_properties,
    VIEW3D_PT_blenderkit_downloads,
    OBJECT_MT_blenderkit_asset_menu,
    UrlPopupDialog
)


def register_ui_panels():
    for c in classess:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_editor_menus.append(header_search_draw)


def unregister_ui_panels():
    bpy.types.VIEW3D_MT_editor_menus.remove(header_search_draw)
    for c in classess:
        print('unregister', c)
        bpy.utils.unregister_class(c)
