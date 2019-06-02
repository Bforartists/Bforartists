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
else:
    from blenderkit import paths, ratings, utils, download, categories

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
    maxlines = 6
    li = 0
    for l in lines:
        while len(l) > threshold:
            i = l.rfind(' ', 0, threshold)
            if i < 1:
                i = threshold
            l1 = l[:i]
            layout.label(text=l1, icon=icon)
            icon = 'NONE'
            l = l[i:]
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
    bkit_ratings = asset.bkit_ratings

    ratings.draw_rating(layout, bkit_ratings, 'rating_quality', 'Quality')
    layout.separator()
    layout.prop(bkit_ratings, 'rating_work_hours')
    w = context.region.width

    layout.label(text='problems')
    layout.prop(bkit_ratings, 'rating_problems', text='')
    layout.label(text='compliments')
    layout.prop(bkit_ratings, 'rating_compliments', text='')

    row = layout.row()
    op = row.operator("object.blenderkit_rating_upload", text="Send rating", icon='URL')
    return op


def draw_upload_common(layout, props, asset_type, context):
    op = layout.operator("wm.url_open", text="Read upload instructions",
                         icon='QUESTION')
    if asset_type == 'MODEL':
        op.url = paths.BLENDERKIT_MODEL_UPLOAD_INSTRUCTIONS_URL
    if asset_type == 'MATERIAL':
        op.url = paths.BLENDERKIT_MATERIAL_UPLOAD_INSTRUCTIONS_URL

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
    else:
        optext = 'Reupload %s (with thumbnail)' % asset_type.lower()

    op = layout.operator("object.blenderkit_upload", text=optext, icon='EXPORT')
    op.asset_type = asset_type
    op.as_new = False

    if props.asset_base_id != '':
        op = layout.operator("object.blenderkit_upload", text='Reupload only metadata', icon='EXPORT')
        op.asset_type = asset_type
        op.metadata_only = True

        op = layout.operator("object.blenderkit_upload", text='Upload as new asset', icon='EXPORT')
        op.asset_type = asset_type
        op.as_new = True
        # layout.label(text = 'asset id, overwrite only for reuploading')
        if props.asset_base_id != '':
            row = layout.row()

            row.prop(props, 'asset_base_id', icon='FILE_TICK')
        # layout.operator("object.blenderkit_mark_for_validation", icon='EXPORT')

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
        row.prop(props, name, icon=icon)
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
    prop_needed(layout, props, 'tags', props.tags)
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
    if props.work_hours == 0:
        row.label(text='', icon='ERROR')
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
    prop_needed(layout, props, 'tags', props.tags)
    layout.prop(props, 'style')
    layout.prop(props, 'production_level')
    layout.prop(props, 'use_design_year')
    if props.use_design_year:
        layout.prop(props, 'design_year')
    layout.prop(props, 'condition')
    row = layout.row()
    if props.work_hours == 0:
        row.label(text='', icon='ERROR')
    row.prop(props, 'work_hours')
    layout.prop(props, 'adult')


def draw_panel_model_search(self, context):
    s = context.scene
    props = s.blenderkit_models
    layout = self.layout
    layout.prop(props, "search_keywords", text="", icon='VIEWZOOM')

    icon = 'NONE'
    if props.report == 'Available only in higher plans.':
        icon = 'ERROR'
    label_multiline(layout, text=props.report, icon=icon)
    if props.report == 'Available only in higher plans.':
        layout.operator("wm.url_open", text="Check plans", icon='URL').url = paths.BLENDERKIT_PLANS

    layout.prop(props, "search_style")
    layout.prop(props, "free_only")
    # if props.search_style == 'OTHER':
    #     layout.prop(props, "search_style_other")
    # layout.prop(props, "search_engine")
    # col = layout.column()
    # layout.prop(props, 'append_link', expand=True, icon_only=False)
    # layout.prop(props, 'import_as', expand=True, icon_only=False)

    # layout.prop(props, "search_advanced")
    if props.search_advanced:
        layout.separator()

        # layout.label(text = "common searches keywords:")
        # layout.prop(props, "search_global_keywords", text = "")
        # layout.prop(props, "search_modifier_keywords")
        # if props.search_engine == 'OTHER':
        #     layout.prop(props, "search_engine_keyword")

        # AGE
        layout.prop(props, "search_condition")  # , text ='condition of object new/old e.t.c.')

        # DESIGN YEAR
        layout.prop(props, "search_design_year", text='designed in ( min - max )')
        row = layout.row(align=True)
        if not props.search_design_year_min:
            row.active = False
        row.prop(props, "search_design_year_min", text='min')
        row.prop(props, "search_design_year_max", text='max')

        # POLYCOUNT
        layout.prop(props, "search_polycount", text='polycount in ( min - max )')
        row = layout.row(align=True)
        if not props.search_polycount:
            row.active = False
        row.prop(props, "search_polycount_min", text='min')
        row.prop(props, "search_polycount_max", text='max')

        # TEXTURE RESOLUTION
        layout.prop(props, "search_texture_resolution", text='texture resolution ( min - max )')
        row = layout.row(align=True)
        if not props.search_texture_resolution:
            row.active = False
        row.prop(props, "search_texture_resolution_min", text='min')
        row.prop(props, "search_texture_resolution_max", text='max')

        # ADULT
        layout.prop(props, "search_adult")  # , text ='condition of object new/old e.t.c.')

    draw_panel_categories(self, context)

    layout.separator()
    layout.label(text='how to import assets:')
    col = layout.column()
    col.prop(props, 'append_method', expand=True, icon_only=False)
    layout.prop(props, 'randomize_rotation')
    if props.randomize_rotation:
        layout.prop(props, 'randomize_rotation_amount')


def draw_panel_scene_search(self, context):
    s = context.scene
    props = s.blenderkit_scene
    layout = self.layout
    # layout.label(text = "common search properties:")
    layout.prop(props, "search_keywords", text="", icon='VIEWZOOM')

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
    bl_label = "Model tweaking"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        p = bpy.context.active_object is not None and bpy.context.active_object.get('asset_data') is not None
        return p

    def draw(self, context):
        # draw asset properties here
        layout = self.layout

        o = bpy.context.active_object
        ad = o['asset_data']
        layout.label(text=str(ad['name']))
        # proxies just don't make it in 2.79... they should stay hidden and used only by pros ...
        # if 'rig' in ad['tags']:
        #     # layout.label(text = 'can make proxy')
        #     layout.operator('object.blenderkit_make_proxy', text = 'Make Armature proxy')

        layout.operator('object.blenderkit_bring_to_scene', text='Bring to scene')
        # layout.operator('object.blenderkit_color_corrector')


class VIEW3D_PT_blenderkit_profile(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_profile"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Profile"

    @classmethod
    def poll(cls, context):

        return True

    def draw(self, context):
        # draw asset properties here
        layout = self.layout
        user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

        if user_preferences.login_attempt:
            layout.label(text='Login through browser')
            layout.label(text='in progress.')
            layout.operator("wm.blenderkit_login_cancel", text="Cancel", icon='CANCEL')
            return

        if len(user_preferences.api_key) < 20:
            if user_preferences.enable_oauth:
                draw_login_buttons(layout)
        else:
            me = bpy.context.window_manager.get('bkit profile')
            if me is not None:
                me = me['user']
                layout.label(text='User: %s %s' % (me['firstName'], me['lastName']))
                layout.label(text='Email: %s' % (me['email']))
                if me.get('sumAssetFilesSize') is not None:  # TODO remove this when production server has these too.
                    layout.label(text='Public assets: %i MiB' % (me['sumAssetFilesSize']))
                if me.get('sumPrivateAssetFilesSize') is not None:
                    layout.label(text='Private assets: %i MiB' % (me['sumPrivateAssetFilesSize']))
                if me.get('remainingPrivateQuota') is not None:
                    layout.label(text='Remaining private storage: %i MiB' % (me['remainingPrivateQuota']))
            layout.operator("wm.url_open", text="See my uploads",
                            icon='URL').url = paths.BLENDERKIT_USER_ASSETS
            if user_preferences.enable_oauth:
                layout.operator("wm.blenderkit_logout", text="Logout",
                                icon='URL')


def draw_panel_model_rating(self, context):
    o = bpy.context.active_object
    op = draw_ratings(self.layout, context)  # , props)
    op.asset_type = 'MODEL'


def draw_panel_material_upload(self, context):
    o = bpy.context.active_object
    mat = bpy.context.active_object.active_material

    props = mat.blenderkit
    layout = self.layout

    draw_upload_common(layout, props, 'MATERIAL', context)

    prop_needed(layout, props, 'name', props.name)
    layout.prop(props, 'description')
    layout.prop(props, 'style')
    if props.style == 'OTHER':
        layout.prop(props, 'style_other')
    # layout.prop(props, 'engine')
    # if props.engine == 'OTHER':
    #     layout.prop(props, 'engine_other')
    prop_needed(layout, props, 'tags', props.tags)
    # layout.prop(props,'shaders')#TODO autofill on upload
    # row = layout.row()
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
    layout.prop(props, "search_keywords", text="", icon='VIEWZOOM')

    label_multiline(layout, text=props.report)

    # layout.prop(props, 'search_style')
    # if props.search_style == 'OTHER':
    #     layout.prop(props, 'search_style_other')
    # layout.prop(props, 'search_engine')
    # if props.search_engine == 'OTHER':
    #     layout.prop(props, 'search_engine_other')

    layout.prop(props, 'automap')

    draw_panel_categories(self, context)


def draw_panel_material_ratings(self, context):
    op = draw_ratings(self.layout, context)  # , props)
    op.asset_type = 'MATERIAL'


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
    layout.prop(props, "search_keywords", text="", icon='VIEWZOOM')
    label_multiline(layout, text=props.report)
    draw_panel_categories(self, context)


def draw_panel_brush_ratings(self, context):
    # props = utils.get_brush_props(context)
    op = draw_ratings(self.layout, context)  # , props)

    op.asset_type = 'BRUSH'


def draw_login_buttons(layout):
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences

    if user_preferences.login_attempt:
        layout.label(text='Login through browser')
        layout.label(text='in progress.')
        layout.operator("wm.blenderkit_login_cancel", text="Cancel", icon='CANCEL')
    else:
        layout.operator("wm.blenderkit_login", text="Login",
                        icon='URL').signup = False
        layout.operator("wm.blenderkit_login", text="Sign up",
                        icon='URL').signup = True


class VIEW3D_PT_blenderkit_unified(Panel):
    bl_category = "BlenderKit"
    bl_idname = "VIEW3D_PT_blenderkit_unified"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "BlenderKit"

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

        row = layout.row()

        #
        row.prop(ui_props, 'down_up', expand=True, icon_only=True)
        # row.label(text='')
        row = row.split().row()
        row.prop(ui_props, 'asset_type', expand=True, icon_only=True)

        w = context.region.width
        if user_preferences.login_attempt:
            layout.label(text='Login through browser')
            layout.label(text='in progress.')
            layout.operator("wm.blenderkit_login_cancel", text="Cancel", icon='CANCEL')
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
        if bpy.data.filepath == '':
            label_multiline(layout, text="It's better to save the file first.", width=w)
            layout.separator()
        if wm.get('bkit_update'):
            label_multiline(layout, text="New version available!", icon='INFO', width=w)
            layout.operator("wm.url_open", text="Get new version",
                            icon='URL').url = paths.BLENDERKIT_ADDON_FILE_URL
            layout.separator()
            layout.separator()
            layout.separator()
        if ui_props.down_up == 'SEARCH':
            # global assetbar_on
            if not ui_props.assetbar_on:
                icon = 'EXPORT'
                text = 'Show AssetBar - ;'
                row = layout.row()
                sr = bpy.context.scene.get('search results')
                if sr != None:
                    icon = 'RESTRICT_VIEW_OFF'
                    row.scale_y = 1
                    text = 'Show Assetbar to see %i results - ;' % len(sr)
                op = row.operator('view3d.blenderkit_asset_bar', text=text, icon=icon)

            else:

                op = layout.operator('view3d.blenderkit_asset_bar', text='Hide AssetBar - ;', icon='EXPORT')
            op.keep_running = False
            op.do_search = False

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
            e = s.render.engine
            if e not in ('CYCLES', 'BLENDER_EEVEE'):
                rtext = 'Only Cycles and EEVEE render engines are currently supported. ' \
                        'Please use Cycles for all assets you upload to BlenderKit.'
                label_multiline(layout, rtext, icon='ERROR', width=w)
                return;

            if ui_props.asset_type == 'MODEL':
                label_multiline(layout, "Uploaded models won't be available in b2.79", icon='ERROR')
                if bpy.context.active_object is not None:
                    draw_panel_model_upload(self, context)
                else:
                    layout.label(text='selet object to upload')
            elif ui_props.asset_type == 'SCENE':
                draw_panel_scene_upload(self, context)

            elif ui_props.asset_type == 'MATERIAL':
                label_multiline(layout, "Uploaded materials won't be available in b2.79", icon='ERROR')

                if bpy.context.active_object is not None and bpy.context.active_object.active_material is not None:
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
                if bpy.context.active_object is not None and bpy.context.active_object.get('asset_data') != None:
                    ad = bpy.context.active_object.get('asset_data')
                    layout.label(text=ad['name'])
                    draw_panel_model_rating(self, context)
            if ui_props.asset_type == 'MATERIAL':
                if bpy.context.active_object is not None and \
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


class SetCategoryOperator(bpy.types.Operator):
    """Visit subcategory"""
    bl_idname = "view3d.blenderkit_set_category"
    bl_label = "BlenderKit Set Active Category"

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


classess = (
    SetCategoryOperator,

    VIEW3D_PT_blenderkit_unified,
    VIEW3D_PT_blenderkit_model_properties,
    VIEW3D_PT_blenderkit_downloads,
    VIEW3D_PT_blenderkit_profile
)


def register_ui_panels():
    for c in classess:
        bpy.utils.register_class(c)


def unregister_ui_panels():
    for c in classess:
        bpy.utils.unregister_class(c)
