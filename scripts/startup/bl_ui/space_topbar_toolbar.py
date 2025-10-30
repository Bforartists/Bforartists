# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import os
import math
from pathlib import Path

user_path = Path(bpy.utils.resource_path('USER')).parent
local_path = Path(bpy.utils.resource_path('LOCAL')).parent

from bpy.types import Header, Menu, Panel
from bpy.types import Operator, Scene, AddonPreferences
from bpy.props import BoolProperty, EnumProperty, IntProperty

import bpy.utils.previews


from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
)


######################################## Topbar ########################################
class TOPBAR_HT_tool_bar(Header):
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout

        window = context.window
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        layout.popover(panel="TOPBAR_PT_main", text = "", icon="NONE")

        ############## toolbars ##########################################################################

        if addon_prefs.topbar_show_quicktoggle:
            if addon_prefs.topbar_file_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_file", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_file.hide_file_topbar(context, layout) # bfa - show hide the complete toolbar container
            if addon_prefs.topbar_mesh_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_meshedit", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_meshedit.hide_meshedit_topbar(context, layout)
            if addon_prefs.topbar_primitives_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_primitives", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_primitives.hide_primitives_topbar(context, layout)
            if addon_prefs.topbar_image_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_image", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_image.hide_image_topbar(context, layout)
            if addon_prefs.topbar_tools_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_tools", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_tools.hide_tools_topbar(context, layout)
            if addon_prefs.topbar_animation_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_animation", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_animation.hide_animation_topbar(context, layout)
            if addon_prefs.topbar_edit_cbox:
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_edit", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_edit.hide_edit_topbar(context, layout)

            if addon_prefs.topbar_misc_cbox:
                layout.separator_spacer()
                layout.scale_x = 0.7
                layout.operator("screen.header_topbar_misc", text = "", icon = "THREE_DOTS")
                layout.scale_x = 1
                TOPBAR_MT_misc.hide_misc_topbar(context, layout)
        else:

            TOPBAR_MT_file.hide_file_topbar(context, layout)
            TOPBAR_MT_meshedit.hide_meshedit_topbar(context, layout)
            TOPBAR_MT_primitives.hide_primitives_topbar(context, layout)
            TOPBAR_MT_image.hide_image_topbar(context, layout)
            TOPBAR_MT_tools.hide_tools_topbar(context, layout)
            TOPBAR_MT_animation.hide_animation_topbar(context, layout)
            TOPBAR_MT_edit.hide_edit_topbar(context, layout)

            layout.separator_spacer()

            TOPBAR_MT_misc.hide_misc_topbar(context, layout)


######################################## Main (Options) ########################################
class TOPBAR_PT_main(Panel):
    bl_label = 'Topbar Manager'
    bl_idname = 'TOPBAR_PT_main'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_category = 'BTM'
    bl_ui_units_x=16

    @classmethod
    def poll(cls, context):
        return (True)

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        box = layout.box()
        row = box.row()
        row.alignment = 'Center'.upper()
        row.label(text='Topbar Manager')

        row.alignment = 'Center'.upper()
        row.prop(bpy.context.screen, 'show_bfa_topbar', text='', icon='TOPBAR', emboss=True)
        row.prop(bpy.context.scene, 'bfa_defaults', text='', icon='OPTIONS', emboss=True)

        # Reset Settings Panel
        if (bpy.context.scene.bfa_defaults == True):

            row = box.row(heading='', align=True)
            row.alignment = 'Center'.upper()

            row.label(text='Defaults')
            row.separator()
            row.operator("bfa.reset_topbar", text='All')

            grid = box.grid_flow(row_major=False, columns=2, even_columns=True, even_rows=True, align=True)

            grid.operator("bfa.reset_files", text='Files')
            grid.operator("bfa.reset_meshedit", text='Mesh Edit')
            grid.operator("bfa.reset_primitives", text='Primitives')
            grid.operator("bfa.reset_image", text='Image')
            grid.operator("bfa.reset_tools", text='Tools')
            grid.operator("bfa.reset_animation", text='Animation')
            grid.operator("bfa.reset_edit", text='Edit')
            grid.operator("bfa.reset_misc", text='Misc')

        grid = layout.grid_flow(row_major=False, columns=2, even_columns=True, even_rows=True, align=True)
        col_amount = 2

        # Main Panels Preferences
        box = grid.box()
        row = box.row()
        row.alignment = 'Center'.upper()

        row.label(text='Types', icon='DOWNARROW_HLT')
        row = box.grid_flow(columns=col_amount, align=True)
        row.prop(addon_prefs, "topbar_file_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_mesh_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_primitives_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_image_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_tools_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_animation_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_edit_cbox", toggle=True)
        row.prop(addon_prefs, "topbar_misc_cbox", toggle=True)

        # Sub panels Settings
        box = grid.box()
        row = box.row()
        row.alignment = 'Center'.upper()

        row.label(text='Options', icon="RIGHTARROW")
        row = box.grid_flow(columns=col_amount, align=True)
        row.prop(addon_prefs, 'bfa_topbar_types', text='Types', icon="NONE", emboss=True, expand=True)

        box = layout.box()
        row = box.row(heading='', align=False)
        row.alignment = 'Center'.upper()
        row.label(text='Show / Hide Toolbars')

        if (addon_prefs.bfa_topbar_types == 'Files'):
            if addon_prefs.topbar_file_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_file_load_save",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_recover",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_link_append",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_import_menu",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_export_menu",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_import_common",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_import_common2",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_import_uncommon",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_export_common",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_export_common2",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_export_uncommon",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_render",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_render_opengl",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_file_render_misc",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Files is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Mesh Edit'):
            if addon_prefs.topbar_mesh_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_mesh_vertices_splitconnect",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_vertices_misc",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_edges_subdiv",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_edges_sharp",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_edges_freestyle",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_edges_misc",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_faces_general",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_faces_freestyle",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_faces_tris",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_faces_rotatemisc",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_mesh_cleanup",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Mesh Edit is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Primitives'):
            if addon_prefs.topbar_primitives_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_primitives_mesh",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_curve",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_surface",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_metaball",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_volume",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_point_cloud",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_gpencil",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_gpencil_lineart",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_light",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_other",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_empties",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_image",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_lightprobe",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_forcefield",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_primitives_collection",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Primitives is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Image'):
            if addon_prefs.topbar_image_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_image_uv_mirror",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_image_uv_rotate",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_image_uv_align",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_image_uv_unwrap",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_image_uv_modify",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Image is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Tools'):
            if addon_prefs.topbar_tools_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_tools_parent",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_objectdata",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_link_to_scn",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_linked_objects",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_join",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_origin",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_shading",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_datatransfer",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_tools_relations",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Tools is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Animation'):
            if addon_prefs.topbar_animation_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_animation_keyframes",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_animation_range",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_animation_play",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_animation_sync",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_animation_keyframetype",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_animation_keyingset",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Animation is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Edit'):
            if addon_prefs.topbar_edit_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_edit_edit",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_edit_weightinedit",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_edit_objectapply",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_edit_objectapply2",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_edit_objectapplydeltas",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_edit_objectclear",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Edit is hidden', icon="NONE")

        if (addon_prefs.bfa_topbar_types == 'Misc'):
            if addon_prefs.topbar_misc_cbox:
                row = box.grid_flow(columns=2, align=True)
                row.prop(addon_prefs, "topbar_misc_viewport",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_undoredo",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_undohistory",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_repeat",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_scene",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_viewlayer",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_last",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_operatorsearch",toggle=addon_prefs.bfa_button_style)
                row.prop(addon_prefs, "topbar_misc_info",toggle=addon_prefs.bfa_button_style)
            else:
                row = box.row()
                row.alignment = 'Center'.upper()
                row.alert = True
                row.label(text='Misc is hidden', icon="NONE")

        col = layout.column()
        col.label( text = "Extra Options:")
        row = layout.row()
        row.separator()
        row.prop(addon_prefs, "topbar_show_quicktoggle")

        col = layout.column()
        row = col.row()
        row.separator()
        row.label( text = "Note that you need to save the startup file")
        row = col.row()
        row.separator()
        row.label( text = "to make the changes to the topbar permanent")



#######################################################################

################ Toolbar type

# Everything menu in this class is collapsible.
class TOPBAR_MT_toolbar_type(Menu):
    bl_idname = "TOPBAR_MT_toolbar_type"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.operator("screen.toolbar_toolbox", text="Type")

######################################## Toolbars ##############################################


######################################## File Menu ########################################
class TOPBAR_MT_file(Menu):
    bl_idname = "TOPBAR_MT_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_file_cbox:

            layout.popover(panel = "TOPBAR_PT_file", text="", icon = "NONE")

            ## ------------------ Load / Save sub toolbars

            if addon_prefs.topbar_file_load_save:
                row = layout.row(align=True)
                row.operator("wm.read_homefile", text="", icon='NEW')
                row.menu("TOPBAR_MT_file_new", text="", icon='FILE_NEW')

                row = layout.row(align=True)
                row.operator("wm.open_mainfile", text="", icon='FILE_FOLDER')
                row.menu("TOPBAR_MT_file_open_recent", text="", icon='OPEN_RECENT')

                row = layout.row(align=True)
                row.operator("wm.save_mainfile", text="", icon='FILE_TICK')
                row.operator("wm.save_as_mainfile", text="", icon='SAVE_AS')
                row.operator("wm.save_as_mainfile", text="", icon='SAVE_COPY')

            if addon_prefs.topbar_file_recover:

                row = layout.row(align=True)
                row.operator("wm.revert_mainfile", text="", icon='FILE_REFRESH')
                row.operator("wm.recover_last_session", text="", icon='RECOVER_LAST')
                row.operator("wm.recover_auto_save", text="", icon='RECOVER_AUTO')

            ## ------------------ Link Append

            if addon_prefs.topbar_file_link_append:

                row = layout.row(align=True)
                row.operator("wm.link", text="", icon='LINK_BLEND')
                row.operator("wm.append", text="", icon='APPEND_BLEND')

            ## ------------------ Import menu

            if addon_prefs.topbar_file_import_menu:

                layout.menu("TOPBAR_MT_file_import", icon='IMPORT', text = "")

            if addon_prefs.topbar_file_export_menu:

                layout.menu("TOPBAR_MT_file_export", icon='EXPORT', text = "")

            ## ------------------ Import single types

            if addon_prefs.topbar_file_import_common:

                row = layout.row(align=True)

                if bpy.app.build_options.io_fbx:
                    row.operator("wm.fbx_import", text="", icon='LOAD_FBX')
                if "io_scene_fbx" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("import_scene.fbx", text="", icon='LOAD_FBX')
                if bpy.app.build_options.io_wavefront_obj: # bfa - only show if built option is true
                    row.operator("wm.obj_import", text="", icon='LOAD_OBJ')
                if bpy.app.build_options.alembic: # bfa - only show if built option is true
                    row.operator("wm.alembic_import", text="", icon = "LOAD_ABC" )

            if addon_prefs.topbar_file_import_common2:

                row = layout.row(align=True)
                row.operator("import_anim.bvh", text="", icon='LOAD_BVH')
                if bpy.app.build_options.usd: # bfa - only show if built option is true
                    row.operator("wm.usd_import", text="", icon='LOAD_USD')
                if "io_scene_gltf2" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("import_scene.gltf", text="", icon='LOAD_GLTF')

            ## ------------------ Import uncommon

            if addon_prefs.topbar_file_import_uncommon:

                row = layout.row(align=True)

                if "io_mesh_stl" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("import_mesh.stl", text="", icon='LOAD_STL')
                if bpy.app.build_options.io_ply: # bfa - only show if built option is true
                    row.operator("wm.ply_import", text="", icon='LOAD_PLY')
                if "io_scene_x3d" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("import_scene.x3d", text="", icon='LOAD_X3D')
                if "io_curve_svg" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("import_curve.svg", text="", icon='LOAD_SVG')

            ## ------------------ Export common

            if addon_prefs.topbar_file_export_common:

                row = layout.row(align=True)
                # BFA - WIP - future fbx api?
                #if bpy.app.build_options.io_fbx:
                #    row.operator("wm.fbx_export", text="", icon='SAVE_FBX')
                if "io_scene_fbx" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("export_scene.fbx", text="", icon='SAVE_FBX')
                if bpy.app.build_options.io_wavefront_obj: # bfa - only show if built option is true
                    row.operator("wm.obj_export", text="", icon='SAVE_OBJ')
                if bpy.app.build_options.alembic: # bfa - only show if built option is true
                    row.operator("wm.alembic_export", text="", icon = "SAVE_ABC" )

            if addon_prefs.topbar_file_export_common2:

                row = layout.row(align=True)
                row.operator("export_anim.bvh", text="", icon='SAVE_BVH')
                if bpy.app.build_options.usd: # bfa - only show if built option is true
                    row.operator("wm.usd_export", text="", icon='SAVE_USD')
                if "io_scene_gltf2" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("export_scene.gltf", text="", icon='SAVE_GLTF')

            ## ------------------ Export uncommon

            if addon_prefs.topbar_file_export_uncommon:

                row = layout.row(align=True)
                if "io_mesh_stl" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("export_mesh.stl", text="", icon='SAVE_STL')
                if bpy.app.build_options.io_ply: # bfa - only show if built option is true
                    row.operator("wm.ply_export", text="", icon='SAVE_PLY')
                if "io_scene_x3d" in context.preferences.addons.keys(): # bfa - only show if addon is enabled
                    row.operator("export_scene.x3d", text="", icon='SAVE_X3D')

            ## ------------------ Render

            if addon_prefs.topbar_file_render:

                row = layout.row(align=True)
                row.operator("render.render", text="", icon='RENDER_STILL').use_viewport = True
                props = row.operator("render.render", text="", icon='RENDER_ANIMATION')
                props.animation = True
                props.use_viewport = True

            ## ------------------ Render

            if addon_prefs.topbar_file_render_opengl:

                row = layout.row(align=True)
                row.operator("render.opengl", text="", icon = 'RENDER_STILL_VIEW')
                row.operator("render.opengl", text="", icon = 'RENDER_ANI_VIEW').animation = True

            ## ------------------ Render

            if addon_prefs.topbar_file_render_misc:

                row = layout.row(align=True)
                row.operator("sound.mixdown", text="", icon='PLAY_AUDIO')

                row = layout.row(align=True)
                row.operator("render.view_show", text="", icon = 'HIDE_RENDERVIEW')
                row.operator("render.play_rendered_anim", icon='PLAY', text="")


######################################## File Panel ########################################
class TOPBAR_PT_file(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_category = "BTM"
    bl_label = "Topbar File"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        col = layout.column(align = True)
        col.label(text = "Topbar File Options:", icon="NONE")
        col.separator()
        col.prop(addon_prefs, "topbar_file_load_save",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_recover",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_link_append",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_import_menu",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_export_menu",toggle=addon_prefs.bfa_button_style)
        col.separator()
        col.prop(addon_prefs, "topbar_file_import_common",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_import_common2",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_import_uncommon",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_export_common",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_export_common2",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_export_uncommon",toggle=addon_prefs.bfa_button_style)
        col.separator()
        col.prop(addon_prefs, "topbar_file_render",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_render_opengl",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_file_render_misc",toggle=addon_prefs.bfa_button_style)


######################################## Mesh Edit Menu ########################################
class TOPBAR_MT_meshedit(Menu):
    bl_idname = "TOPBAR_MT_meshedit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_mesh_cbox:

            layout.popover(panel = "TOPBAR_PT_meshedit", text="", icon = "NONE")

            obj = context.object
            if obj is not None:

                mode = obj.mode
                with_freestyle = bpy.app.build_options.freestyle

                if mode == 'EDIT':

                    if obj.type == 'MESH':

                        if addon_prefs.topbar_mesh_vertices_splitconnect:

                            row = layout.row(align=True)
                            row.operator("mesh.split", text = "", icon = "SPLIT")
                            row.operator("mesh.vert_connect_path", text = "", icon = "VERTEXCONNECTPATH")
                            row.operator("mesh.vert_connect", text = "", icon = "VERTEXCONNECT")

                        if addon_prefs.topbar_mesh_vertices_misc:

                            row = layout.row(align=True)
                            with_bullet = bpy.app.build_options.bullet

                            if with_bullet:
                                row.operator("mesh.convex_hull", text = "", icon = "CONVEXHULL")

                            row.operator("mesh.blend_from_shape", text = "", icon = "BLENDFROMSHAPE")
                            row.operator("mesh.shape_propagate_to_all", text = "", icon = "SHAPEPROPAGATE")


                        ## ------------------ Edges

                        if addon_prefs.topbar_mesh_edges_subdiv:

                            row = layout.row(align=True)
                            row.operator("mesh.subdivide", text = "", icon = "SUBDIVIDE_EDGES")
                            row.operator("mesh.subdivide_edgering", text = "", icon = "SUBDIVEDGELOOP")
                            row.operator("mesh.unsubdivide", text = "", icon = "UNSUBDIVIDE")

                        if addon_prefs.topbar_mesh_edges_sharp:

                            row = layout.row(align=True)
                            row.operator("mesh.mark_sharp", text = "", icon = "MARKSHARPEDGES")
                            row.operator("mesh.mark_sharp", text = "", icon = "CLEARSHARPEDGES").clear = True
                            row.operator("mesh.set_sharpness_by_angle", text = "", icon="MARKSHARPANGLE")

                        if addon_prefs.topbar_mesh_edges_freestyle:

                            row = layout.row(align=True)
                            if with_freestyle:
                                row.operator("mesh.mark_freestyle_edge", text = "", icon = "MARK_FS_EDGE").clear = False
                                row.operator("mesh.mark_freestyle_edge", text = "", icon = "CLEAR_FS_EDGE").clear = True

                        if addon_prefs.topbar_mesh_edges_rotate:

                            row = layout.row(align=True)
                            row.operator("mesh.edge_rotate", text = "", icon = "ROTATECW").use_ccw = False

                        if addon_prefs.topbar_mesh_edges_misc:

                            row = layout.row(align=True)
                            row.operator("mesh.edge_split", text = "", icon = "SPLITEDGE")
                            row.operator("mesh.bridge_edge_loops", text = "", icon = "BRIDGE_EDGELOOPS")

                        ## ------------------ Faces

                        if addon_prefs.topbar_mesh_faces_general:

                            with_freestyle = bpy.app.build_options.freestyle
                            row = layout.row(align=True)
                            row.operator("mesh.fill", text = "", icon = "FILL")
                            row.operator("mesh.fill_grid", text = "", icon = "GRIDFILL")
                            row.operator("mesh.beautify_fill", text = "", icon = "BEAUTIFY")
                            row.operator("mesh.solidify", text = "", icon = "SOLIDIFY")
                            row.operator("mesh.intersect", text = "", icon = "INTERSECT")
                            row.operator("mesh.intersect_boolean", text = "", icon = "BOOLEAN_INTERSECT")
                            row.operator("mesh.wireframe", text = "", icon = "WIREFRAME")

                        if addon_prefs.topbar_mesh_faces_freestyle:

                            row = layout.row(align=True)
                            if with_freestyle:
                                row.operator("mesh.mark_freestyle_face", text = "", icon = "MARKFSFACE").clear = False
                                row.operator("mesh.mark_freestyle_face", text = "", icon = "CLEARFSFACE").clear = True

                        if addon_prefs.topbar_mesh_faces_tris:

                            row = layout.row(align=True)
                            row.operator("mesh.poke", text = "", icon = "POKEFACES")
                            props = row.operator("mesh.quads_convert_to_tris", text = "", icon = "TRIANGULATE")
                            props.quad_method = props.ngon_method = 'BEAUTY'
                            row.operator("mesh.tris_convert_to_quads", text = "", icon = "TRISTOQUADS")
                            row.operator("mesh.face_split_by_edges", text = "", icon = "SPLITBYEDGES")

                        if addon_prefs.topbar_mesh_faces_rotatemisc:

                            row = layout.row(align=True)
                            row.operator("mesh.uvs_rotate", text = "", icon = "ROTATE_UVS")
                            row.operator("mesh.uvs_reverse", text = "", icon = "REVERSE_UVS")
                            row.operator("mesh.colors_rotate", text = "", icon = "ROTATE_COLORS")
                            row.operator("mesh.colors_reverse", text = "", icon = "REVERSE_COLORS")

                        ## ------------------ Cleanup

                        if addon_prefs.topbar_mesh_cleanup:

                            row = layout.row(align=True)
                            row.operator("mesh.delete_loose", text = "", icon = "DELETE_LOOSE")

                            row = layout.row(align=True)
                            row.operator("mesh.decimate", text = "", icon = "DECIMATE")
                            row.operator("mesh.dissolve_degenerate", text = "", icon = "DEGENERATE_DISSOLVE")
                            row.operator("mesh.face_make_planar", text = "", icon = "MAKE_PLANAR")
                            row.operator("mesh.vert_connect_nonplanar", text = "", icon = "SPLIT_NONPLANAR")
                            row.operator("mesh.vert_connect_concave", text = "", icon = "SPLIT_CONCAVE")
                            row.operator("mesh.fill_holes", text = "", icon = "FILL_HOLE")


######################################## Mesh Edit Panel ########################################
class TOPBAR_PT_meshedit(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_category = "BTM"
    bl_label = "Topbar Mesh Edit"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        obj = context.object

        if obj is None:

            col = layout.column(align = True)
            col.alert=False
            col.label(text = "Topbar Mesh Edit:", icon="NONE")
            col.separator()
            col.alert=True
            col.label(text = "No Active Mesh", icon="INFO")

        if obj is not None:

            col = layout.column(align = True)
            col.label(text = "Topbar Mesh Edit:", icon="NONE")
            col.separator()
            col.alert=True
            col.label(text = "Edit Mode Only", icon="EDITMODE_HLT")
            col = layout.column(align = True)

            col.prop(addon_prefs, "topbar_mesh_vertices_splitconnect",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_vertices_misc",toggle=addon_prefs.bfa_button_style)
            col.separator()
            col.prop(addon_prefs, "topbar_mesh_edges_subdiv",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_edges_sharp",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_edges_freestyle",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_edges_misc",toggle=addon_prefs.bfa_button_style)
            col.separator()
            col.prop(addon_prefs, "topbar_mesh_faces_general",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_faces_freestyle",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_faces_tris",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_faces_rotatemisc",toggle=addon_prefs.bfa_button_style)
            col.prop(addon_prefs, "topbar_mesh_cleanup",toggle=addon_prefs.bfa_button_style)


######################################## Primitives Menu ########################################
class TOPBAR_MT_primitives(Menu):
    bl_idname = "TOPBAR_MT_primitives"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_primitives_cbox:

            layout.popover(panel = "TOPBAR_PT_primitives", text="", icon = "NONE")

            obj = context.object

            if obj is None:

                ## ------------------ primitives sub toolbars

                if addon_prefs.topbar_primitives_mesh:

                    row = layout.row(align=True)
                    row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                    row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                    row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                    row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                    row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
                    row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                    row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                    row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')
                    row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')

                if addon_prefs.topbar_primitives_curve:

                    row = layout.row(align=True)
                    row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                    row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                    row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                    row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                    row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                if addon_prefs.topbar_primitives_surface:

                    row = layout.row(align=True)
                    row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                    row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                    row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                    row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                    row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                    row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                if addon_prefs.topbar_primitives_metaball:

                    row = layout.row(align=True)
                    row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                    row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                    row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                    row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                    row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

                if addon_prefs.topbar_primitives_point_cloud:

                    row = layout.row(align=True)
                    row.operator("object.pointcloud_random_add", text="", icon='OUTLINER_OB_POINTCLOUD')

                if addon_prefs.topbar_primitives_volume:

                    row = layout.row(align=True)
                    row.operator("object.volume_import", text="", icon='FILE_VOLUME')
                    row.operator("object.volume_add", text="", icon='OUTLINER_OB_VOLUME')

                if addon_prefs.topbar_primitives_gpencil:

                    row = layout.row(align=True)
                    row.operator("object.grease_pencil_add", text="", icon='EMPTY_AXIS').type= 'EMPTY'
                    row.operator("object.grease_pencil_add", text="", icon='STROKE').type= 'STROKE'
                    row.operator("object.grease_pencil_add", text="", icon='MONKEY').type= 'MONKEY'

                if addon_prefs.topbar_primitives_gpencil_lineart:

                    row = layout.row(align=True)
                    row.operator("object.grease_pencil_add", text="", icon='LINEART_SCENE').type= 'LINEART_SCENE'
                    row.operator("object.grease_pencil_add", text="", icon='LINEART_COLLECTION').type= 'LINEART_COLLECTION'
                    row.operator("object.grease_pencil_add", text="", icon='LINEART_OBJECT').type= 'LINEART_OBJECT'

                if addon_prefs.topbar_primitives_light:

                    row = layout.row(align=True)
                    row.operator("object.light_add", text="", icon='LIGHT_POINT').type= 'POINT'
                    row.operator("object.light_add", text="", icon='LIGHT_SUN').type= 'SUN'
                    row.operator("object.light_add", text="", icon='LIGHT_SPOT').type= 'SPOT'
                    row.operator("object.light_add", text="", icon='LIGHT_AREA').type= 'AREA'

                if addon_prefs.topbar_primitives_other:

                    row = layout.row(align=True)
                    row.operator("object.text_add", text="", icon='OUTLINER_OB_FONT')
                    row.operator("object.armature_add", text="", icon='OUTLINER_OB_ARMATURE')
                    row.operator("object.add", text="", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
                    row.operator("object.lattice_add_to_selected", text="", icon='OBJECT_LATTICE')
                    row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA').rotation = (1.5708, 0.0, 0.0)
                    row.operator("object.speaker_add", text="", icon='OUTLINER_OB_SPEAKER')

                if addon_prefs.topbar_primitives_empties:

                    row = layout.row(align=True)
                    row.operator("object.empty_add", text="", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
                    row.operator("object.empty_add", text="", icon='EMPTY_SPHERE').type = 'SPHERE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CIRCLE').type = 'CIRCLE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CONE').type = 'CONE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CUBE').type = 'CUBE'
                    row.operator("object.empty_add", text="", icon='EMPTY_SINGLE_ARROW').type = 'SINGLE_ARROW'
                    row.operator("object.empty_add", text="", icon='EMPTY_ARROWS').type = 'ARROWS'
                    row.operator("object.empty_add", text="", icon='EMPTY_IMAGE').type = 'IMAGE'

                if addon_prefs.topbar_primitives_image:

                    row = layout.row(align=True)
                    row.operator("image.import_as_mesh_planes", text="", icon='MESH_PLANE')

                if addon_prefs.topbar_primitives_lightprobe:

                    row = layout.row(align=True)
                    row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_SPHERE').type='SPHERE'
                    row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_PLANE').type='PLANE'
                    row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_VOLUME').type='VOLUME'

                if addon_prefs.topbar_primitives_forcefield:

                    row = layout.row(align=True)
                    row.operator("object.effector_add", text="", icon='FORCE_BOID').type='BOID'
                    row.operator("object.effector_add", text="", icon='FORCE_CHARGE').type='CHARGE'
                    row.operator("object.effector_add", text="", icon='FORCE_CURVE').type='GUIDE'
                    row.operator("object.effector_add", text="", icon='FORCE_DRAG').type='DRAG'
                    row.operator("object.effector_add", text="", icon='FORCE_FORCE').type='FORCE'
                    row.operator("object.effector_add", text="", icon='FORCE_HARMONIC').type='HARMONIC'
                    row.operator("object.effector_add", text="", icon='FORCE_LENNARDJONES').type='LENNARDJ'
                    row.operator("object.effector_add", text="", icon='FORCE_MAGNETIC').type='MAGNET'
                    row.operator("object.effector_add", text="", icon='FORCE_FLUIDFLOW').type='FLUID'
                    row.operator("object.effector_add", text="", icon='FORCE_TEXTURE').type='TEXTURE'
                    row.operator("object.effector_add", text="", icon='FORCE_TURBULENCE').type='TURBULENCE'
                    row.operator("object.effector_add", text="", icon='FORCE_VORTEX').type='VORTEX'
                    row.operator("object.effector_add", text="", icon='FORCE_WIND').type='WIND'

                if addon_prefs.topbar_primitives_collection:

                    row = layout.row(align=True)

                    row.operator("object.collection_instance_add", text="", icon='GROUP')

            elif obj is not None:

                mode = obj.mode

                if mode == 'OBJECT':

                    ## ------------------ primitives sub toolbars

                    if addon_prefs.topbar_primitives_mesh:

                        row = layout.row(align=True)
                        row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                        row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                        row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                        row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                        row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
                        row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                        row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                        row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')
                        row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')

                    if addon_prefs.topbar_primitives_curve:

                        row = layout.row(align=True)
                        row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                        row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                        row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                        row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                        row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                    if addon_prefs.topbar_primitives_surface:

                        row = layout.row(align=True)
                        row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                        row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                        row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                        row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                        row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                        row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                    if addon_prefs.topbar_primitives_metaball:

                        row = layout.row(align=True)
                        row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                        row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                        row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                        row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                        row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

                    if addon_prefs.topbar_primitives_point_cloud:

                        row = layout.row(align=True)
                        row.operator("object.pointcloud_random_add", text="", icon='OUTLINER_OB_POINTCLOUD')

                    if addon_prefs.topbar_primitives_volume:

                        row = layout.row(align=True)
                        row.operator("object.volume_import", text="", icon='FILE_VOLUME')
                        row.operator("object.volume_add", text="", icon='OUTLINER_OB_VOLUME')

                    if addon_prefs.topbar_primitives_gpencil:

                        row = layout.row(align=True)
                        row.operator("object.grease_pencil_add", text="", icon='EMPTY_AXIS').type= 'EMPTY'
                        row.operator("object.grease_pencil_add", text="", icon='STROKE').type= 'STROKE'
                        row.operator("object.grease_pencil_add", text="", icon='MONKEY').type= 'MONKEY'

                    if addon_prefs.topbar_primitives_gpencil_lineart:

                        row = layout.row(align=True)
                        row.operator("object.grease_pencil_add", text="", icon='LINEART_SCENE').type= 'LINEART_SCENE'
                        row.operator("object.grease_pencil_add", text="", icon='LINEART_COLLECTION').type= 'LINEART_COLLECTION'
                        row.operator("object.grease_pencil_add", text="", icon='LINEART_OBJECT').type= 'LINEART_OBJECT'

                    if addon_prefs.topbar_primitives_light:

                        row = layout.row(align=True)
                        row.operator("object.light_add", text="", icon='LIGHT_POINT').type= 'POINT'
                        row.operator("object.light_add", text="", icon='LIGHT_SUN').type= 'SUN'
                        row.operator("object.light_add", text="", icon='LIGHT_SPOT').type= 'SPOT'
                        row.operator("object.light_add", text="", icon='LIGHT_AREA').type= 'AREA'

                    if addon_prefs.topbar_primitives_other:

                        row = layout.row(align=True)
                        row.operator("object.text_add", text="", icon='OUTLINER_OB_FONT')
                        row.operator("object.armature_add", text="", icon='OUTLINER_OB_ARMATURE')
                        row.operator("object.add", text="", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
                        derow.operator("object.lattice_add_to_selected", text="", icon='OBJECT_LATTICE')
                        row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA').rotation = (1.5708, 0.0, 0.0)
                        row.operator("object.speaker_add", text="", icon='OUTLINER_OB_SPEAKER')

                    if addon_prefs.topbar_primitives_empties:

                        row = layout.row(align=True)
                        row.operator("object.empty_add", text="", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
                        row.operator("object.empty_add", text="", icon='EMPTY_SPHERE').type = 'SPHERE'
                        row.operator("object.empty_add", text="", icon='EMPTY_CIRCLE').type = 'CIRCLE'
                        row.operator("object.empty_add", text="", icon='EMPTY_CONE').type = 'CONE'
                        row.operator("object.empty_add", text="", icon='EMPTY_CUBE').type = 'CUBE'
                        row.operator("object.empty_add", text="", icon='EMPTY_SINGLE_ARROW').type = 'SINGLE_ARROW'
                        row.operator("object.empty_add", text="", icon='EMPTY_ARROWS').type = 'ARROWS'
                        row.operator("object.empty_add", text="", icon='EMPTY_IMAGE').type = 'IMAGE'

                    if addon_prefs.topbar_primitives_image:

                        row = layout.row(align=True)
                        row.operator("image.import_as_mesh_planes", text="", icon='MESH_PLANE')

                    if addon_prefs.topbar_primitives_lightprobe:

                        row = layout.row(align=True)
                        row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_SPHERE').type='SPHERE'
                        row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_PLANE').type='PLANE'
                        row.operator("object.lightprobe_add", text="", icon='LIGHTPROBE_VOLUME').type='VOLUME'

                    if addon_prefs.topbar_primitives_forcefield:

                        row = layout.row(align=True)
                        row.operator("object.effector_add", text="", icon='FORCE_BOID').type='BOID'
                        row.operator("object.effector_add", text="", icon='FORCE_CHARGE').type='CHARGE'
                        row.operator("object.effector_add", text="", icon='FORCE_CURVE').type='GUIDE'
                        row.operator("object.effector_add", text="", icon='FORCE_DRAG').type='DRAG'
                        row.operator("object.effector_add", text="", icon='FORCE_FORCE').type='FORCE'
                        row.operator("object.effector_add", text="", icon='FORCE_HARMONIC').type='HARMONIC'
                        row.operator("object.effector_add", text="", icon='FORCE_LENNARDJONES').type='LENNARDJ'
                        row.operator("object.effector_add", text="", icon='FORCE_MAGNETIC').type='MAGNET'
                        row.operator("object.effector_add", text="", icon='FORCE_FLUIDFLOW').type='FLUID'
                        row.operator("object.effector_add", text="", icon='FORCE_TEXTURE').type='TEXTURE'
                        row.operator("object.effector_add", text="", icon='FORCE_TURBULENCE').type='TURBULENCE'
                        row.operator("object.effector_add", text="", icon='FORCE_VORTEX').type='VORTEX'
                        row.operator("object.effector_add", text="", icon='FORCE_WIND').type='WIND'

                    if addon_prefs.topbar_primitives_collection:

                        row = layout.row(align=True)
                        row.operator("object.collection_instance_add", text="", icon='GROUP')

                if mode == 'EDIT':

                    if obj.type == 'MESH':

                        if addon_prefs.topbar_primitives_mesh:

                            row = layout.row(align=True)
                            row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                            row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                            row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                            row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                            row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')
                            row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                            row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                            row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')
                            row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')

                    if obj.type == 'CURVE':

                        if addon_prefs.topbar_primitives_curve:

                            row = layout.row(align=True)
                            row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                            row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                            row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                            row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                            row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                    if obj.type == 'SURFACE':

                        if addon_prefs.topbar_primitives_surface:

                            row = layout.row(align=True)
                            row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                            row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                            row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                            row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                            row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                            row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                    if obj.type == 'META':

                        if addon_prefs.topbar_primitives_metaball:

                            row = layout.row(align=True)
                            row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                            row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                            row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                            row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                            row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'


######################################## Primitives Panel ########################################
class TOPBAR_PT_primitives(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_category = "BTM"
    bl_label = "Topbar Primitives"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        col = layout.column(align = True)
        col.label(text = "Topbar Primitives:", icon="NONE")

        col.prop(addon_prefs, "topbar_primitives_mesh",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_curve",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_surface",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_metaball",toggle=addon_prefs.bfa_button_style)
        col.separator()
        col.prop(addon_prefs, "topbar_primitives_volume",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_point_cloud",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_gpencil",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_gpencil_lineart",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_light",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_other",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_empties",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_image",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_lightprobe",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_forcefield",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_primitives_collection",toggle=addon_prefs.bfa_button_style)

######################################## Image ########################################

# Try to give unique tooltip fails at wrong context issue. Code remains for now. Maybe we find a solution here.

#class VIEW3D_MT_uv_straighten(bpy.types.Operator):
#    """Straighten\nStraightens the selected geometry"""
#    bl_idname = "image.uv_straighten"
#    bl_label = "straighten"
#    bl_options = {'REGISTER', 'UNDO'}

#    def execute(self, context):
#        for area in bpy.context.screen.areas:
#            if area.type == 'IMAGE_EDITOR':
#                override = context.copy()
#                override['area'] = area
#                bpy.ops.uv.align(axis = 'ALIGN_S')
#        return {'FINISHED'}


######################################## Image Menu ########################################
class TOPBAR_MT_image(Menu):
    bl_idname = "TOPBAR_MT_image"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_image_cbox:

            layout.popover(panel = "TOPBAR_PT_menu_image", text="", icon = "NONE")

            obj = context.active_object
            mode = 'OBJECT' if obj is None else obj.mode

            if mode == 'EDIT':

                if addon_prefs.topbar_image_uv_mirror:

                    row = layout.row(align=True)

                    row.operator("image.uv_mirror_x", text="", icon = "MIRROR_X")
                    row.operator("image.uv_mirror_y", text="", icon = "MIRROR_Y")

                if addon_prefs.topbar_image_uv_rotate:

                    row = layout.row(align=True)

                    row.operator("image.uv_rotate_clockwise", text="", icon = "ROTATE_PLUS_90")
                    row.operator("image.uv_rotate_counterclockwise", text="", icon = "ROTATE_MINUS_90")

                if addon_prefs.topbar_image_uv_align:

                    row = layout.row(align=True)

                    #row.operator_enum("uv.align", "axis")  # W, 2/3/4 # bfa - enum is no good idea in header. It enums below each other. And the header just shows besides ..

                    row.operator("uv.align", text= "", icon = "ALIGN").axis = 'ALIGN_S'
                    row.operator("uv.align", text= "", icon = "STRAIGHTEN_X").axis = 'ALIGN_T'
                    row.operator("uv.align", text= "", icon = "STRAIGHTEN_Y").axis = 'ALIGN_U'
                    row.operator("uv.align", text= "", icon = "ALIGNAUTO").axis = 'ALIGN_AUTO'
                    row.operator("uv.align", text= "", icon = "ALIGNHORIZONTAL").axis = 'ALIGN_X'
                    row.operator("uv.align", text= "", icon = "ALIGNVERTICAL").axis = 'ALIGN_Y'
                    row.operator("uv.align_rotation", text= "", icon = "DRIVER_ROTATIONAL_DIFFERENCE")

                    # Try to give unique tooltip fails at wrong context issue. It throws an error when you are not in edit mode, have no uv editor open, and there is no mesh selected.
                    # Code remains here for now. Maybe we find a solution at a later point.
                    #row.operator("image.uv_straighten", text= "straighten")

                if addon_prefs.topbar_image_uv_unwrap:

                    row = layout.row(align=True)

                    row.operator("uv.mark_seam", text="", icon ="MARK_SEAM").clear = False
                    sub = row.row()
                    sub.active = (mode == 'EDIT')
                    sub.operator("uv.clear_seam", text="", icon ="CLEAR_SEAM")
                    row.operator("uv.seams_from_islands", text="", icon ="SEAMSFROMISLAND")

                    row = layout.row(align=True)

                    row.operator("uv.unwrap", text = "", icon='UNWRAP_ABF').method='ANGLE_BASED'
                    row.operator("uv.unwrap", text = "", icon='UNWRAP_LSCM').method='CONFORMAL'
                    row.operator("uv.unwrap", text = "", icon='UNWRAP_MINSTRETCH').method = 'MINIMUM_STRETCH'
                    row.operator_context = 'EXEC_REGION_WIN'
                    row.operator("uv.cube_project", text= "",icon = "CUBEPROJECT")
                    row.operator("uv.cylinder_project", text= "",icon = "CYLINDERPROJECT")
                    row.operator("uv.sphere_project", text= "",icon = "SPHEREPROJECT")

                if addon_prefs.topbar_image_uv_modify:

                    row = layout.row(align=True)

                    row.operator("uv.pin", text= "", icon = "PINNED").clear = False
                    row.operator("uv.pin", text="", icon = "UNPINNED").clear = True

                    row = layout.row(align=True)
                    row.operator("uv.weld", text="", icon='WELD')
                    #row.operator("uv.stitch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.
                    row.operator("uv.remove_doubles", text="", icon='REMOVE_DOUBLES')

                    row = layout.row(align=True)

                    row.operator("uv.average_islands_scale", text="", icon ="AVERAGEISLANDSCALE")
                    row.operator("uv.pack_islands", text="", icon ="PACKISLAND")
                    sub = row.row()
                    sub.active = (mode == 'EDIT')
                    sub.operator("uv.copy_mirrored_faces", text="", icon ="COPYMIRRORED")
                    #row.operator("uv.minimize_stretch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.


######################################## Image Panel ########################################
class TOPBAR_PT_menu_image(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Topbar Image"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        obj = context.object

        if obj is None:

            col = layout.column(align = True)
            row = col.row()
            col.label(text = "Topbar Image:", icon="NONE")
            col.alert=True
            col.label(text = "No Active Mesh", icon="INFO")

        if obj is not None:
            col = layout.column(align = True)
            col.label(text = "Topbar Image:", icon="NONE")
            col.alert=True
            col.label(text = "Edit Mode Only", icon="NONE")
            col.label(text = "UV Editor must be open!", icon="NONE")

            col = layout.column(align = True)
            col.prop(addon_prefs, "topbar_image_uv_mirror")
            col.prop(addon_prefs, "topbar_image_uv_rotate")
            col.prop(addon_prefs, "topbar_image_uv_align")
            col.prop(addon_prefs, "topbar_image_uv_unwrap")
            col.prop(addon_prefs, "topbar_image_uv_modify")


######################################## Tools Menu ########################################
class TOPBAR_MT_tools(Menu):
    bl_idname = "TOPBAR_MT_tools"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        obj = context.object

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_tools_cbox:

            layout.popover(panel = "TOPBAR_PT_tools", text="", icon = "NONE")

            if obj is not None:

                mode = obj.mode

                if mode == 'OBJECT':

                    if addon_prefs.topbar_tools_parent:

                        row = layout.row(align=True)
                        row.operator("object.parent_set", icon='PARENT_SET', text="")
                        row.operator("object.parent_clear", icon='PARENT_CLEAR', text="")

                    if addon_prefs.topbar_tools_objectdata:

                        row = layout.row(align=True)
                        row.operator("object.make_single_user", icon='MAKE_SINGLE_USER', text="")
                        row.menu("VIEW3D_MT_make_links", text = "", icon='LINK_DATA' )

                    if addon_prefs.topbar_tools_link_to_scn:

                        operator_context_default = layout.operator_context
                        if len(bpy.data.scenes) > 10:
                            layout.operator_context = 'INVOKE_REGION_WIN'
                            layout.operator("object.make_links_scene", text="Link to SCN", icon='OUTLINER_OB_EMPTY')
                        else:
                            layout.operator_context = 'EXEC_REGION_WIN'
                            layout.operator_menu_enum("object.make_links_scene", "scene", text="Link to SCN")

                    if addon_prefs.topbar_tools_linked_objects:

                        row = layout.row(align=True)
                        row.operator("object.make_local", icon='MAKE_LOCAL', text="")
                        row.operator("object.make_override_library", text="", icon = "LIBRARY_DATA_OVERRIDE")

                    if addon_prefs.topbar_tools_join:

                        obj_type = obj.type

                        row = layout.row(align=True)
                        if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE'}:
                            row.operator("object.join", icon ='JOIN', text= "" )

                    if addon_prefs.topbar_tools_origin:

                        obj_type = obj.type

                        if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'FONT', 'LATTICE'}:

                            row = layout.row(align=True)
                            row.operator("object.origin_set", icon ='GEOMETRY_TO_ORIGIN', text="").type='GEOMETRY_ORIGIN'
                            row.operator("object.origin_set", icon ='ORIGIN_TO_GEOMETRY', text="").type='ORIGIN_GEOMETRY'
                            row.operator("object.origin_set", icon ='ORIGIN_TO_CURSOR', text="").type='ORIGIN_CURSOR'
                            row.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text="").type='ORIGIN_CENTER_OF_MASS'
                            row.operator("object.origin_set", icon ='ORIGIN_TO_VOLUME', text = "").type='ORIGIN_CENTER_OF_VOLUME'

                    if addon_prefs.topbar_tools_shading:

                        obj_type = obj.type

                        if obj_type in {'MESH', 'CURVE', 'SURFACE'}:

                            row = layout.row(align=True)
                            row.operator("object.shade_smooth", icon ='SHADING_SMOOTH', text="")
                            row.operator("object.shade_smooth_by_angle", icon="NORMAL_SMOOTH", text="")
                            row.operator("object.shade_flat", icon ='SHADING_FLAT', text="")

                    if addon_prefs.topbar_tools_datatransfer:

                        obj_type = obj.type

                        if obj_type == 'MESH':

                            row = layout.row(align=True)
                            row.operator("object.data_transfer", icon ='TRANSFER_DATA', text="")
                            row.operator("object.datalayout_transfer", icon ='TRANSFER_DATA_LAYOUT', text="")
                            row.operator("object.join_uvs", icon ='TRANSFER_UV', text = "")

                if mode == 'EDIT':

                    if addon_prefs.topbar_tools_relations:

                        row = layout.row(align=True)

                        row.operator("object.vertex_parent_set", text = "", icon = "VERTEX_PARENT" )

                        if obj.type == 'ARMATURE':

                            row = layout.row(align=True)
                            row.operator("armature.parent_set", icon='PARENT_SET', text="")
                            row.operator("armature.parent_clear", icon='PARENT_CLEAR', text="")


######################################## Tools Panel ########################################
class TOPBAR_PT_tools(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Topbar Tools"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        col = layout.column(align = True)
        col.label(text = "Tools Options:", icon="NONE")
        col.prop(addon_prefs, "topbar_tools_parent",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_objectdata",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_link_to_scn",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_linked_objects",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_join",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_origin",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_shading",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_datatransfer",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_tools_relations",toggle=addon_prefs.bfa_button_style)


######################################## Autosmooth Panel ########################################
class TOPBAR_PT_normals_autosmooth(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Auto Smooth"

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            return False

        if context.active_object.type != "MESH":
            return False

        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        if context.active_object is None:
            return

        if context.active_object.type != "MESH":
            return

        mesh = context.active_object.data

        split = layout.split()
        split.active = not mesh.has_custom_normals
        split.use_property_split = False
        col = split.column()
        col.prop(mesh, "use_auto_smooth", text="Auto Smooth")
        col = split.column()
        row = col.row(align = True)
        row.prop(mesh, "auto_smooth_angle", text="")
        row.prop_decorator(mesh, "auto_smooth_angle")

        col = layout.column()
        if mesh.has_custom_normals:
            col.label(text = "No Autosmooth. Custom normals", icon = 'INFO')

        col = layout.column()

        if mesh.has_custom_normals:
            col.operator("mesh.customdata_custom_splitnormals_clear", icon='X')
        else:
            col.operator("mesh.customdata_custom_splitnormals_add", icon='ADD')


######################################## Animation Menu ########################################
class TOPBAR_MT_animation(Menu):
    bl_idname = "TOPBAR_MT_animation"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        screen = context.screen
        toolsettings = context.tool_settings
        userprefs = context.preferences

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_animation_cbox:

            layout.popover(panel = "TOPBAR_PT_animation", text="", icon = "NONE")

            if addon_prefs.topbar_animation_keyframes:

                obj = context.object

                if obj is not None:

                    mode = obj.mode

                    if mode == 'OBJECT':

                        row = layout.row(align=True)
                        row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text="")
                        row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="")
                        row.operator("nla.bake", icon= 'BAKE_ACTION',text="")
                        row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="")

                        row = layout.row(align=True)
                        row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text="")
                        row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="")

                    if mode == 'POSE':

                        row = layout.row(align=True)
                        row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text="")
                        row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="")
                        row.operator("nla.bake", icon= 'BAKE_ACTION',text="")
                        row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="")

                        row = layout.row(align=True)

                        row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text="")
                        row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="")

            if addon_prefs.topbar_animation_play:

                row = layout.row(align=True)
                row.operator("screen.frame_jump", text="", icon='REW').end = False
                row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False

                if not screen.is_animation_playing:
                    # if using JACK and A/V sync:
                    #   hide the play-reversed button
                    #   since JACK transport doesn't support reversed playback
                    if scene.sync_mode == 'AUDIO_SYNC' and context.preferences.system.audio_device == 'JACK':
                        sub = row.row(align=True)
                        sub.scale_x = 1.4
                        sub.operator("screen.animation_play", text="", icon='PLAY')
                    else:
                        row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                        row.operator("screen.animation_play", text="", icon='PLAY')
                else:
                    sub = row.row(align=True)
                    sub.scale_x = 1.4
                    sub.operator("screen.animation_play", text="", icon='PAUSE')
                row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
                row.operator("screen.frame_jump", text="", icon='FF').end = True

                row = layout.row(align=True)
                row.prop(scene, "frame_current", text="")

            if addon_prefs.topbar_animation_range:

                row = layout.row(align=True)
                row.prop(scene, "use_preview_range", text="", toggle=True)
                row.prop(scene, "lock_frame_selection_to_range", text="", icon = "LOCKED", toggle=True)

                row = layout.row(align=True)
                if not scene.use_preview_range:
                    row.prop(scene, "frame_start", text="Start")
                    row.prop(scene, "frame_end", text="End")
                else:
                    row.prop(scene, "frame_preview_start", text="Start")
                    row.prop(scene, "frame_preview_end", text="End")

            if addon_prefs.topbar_animation_keyingset:

                row = layout.row(align=True)
                row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
                row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')

                row = layout.row(align=True)
                row.prop(toolsettings, "use_keyframe_insert_auto", text="", toggle=True)
                row.prop_search(scene.keying_sets_all, "active", scene, "keying_sets_all", text="")


            if addon_prefs.topbar_animation_sync:

                row = layout.row(align=True)
                layout.prop(scene, "sync_mode", text="")

            if addon_prefs.topbar_animation_keyframetype:

                row = layout.row(align=True)
                layout.prop(toolsettings, "keyframe_type", text="", icon_only=True)

######################################## Animation Panel ########################################

class TOPBAR_PT_animation(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Topbar Animation"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        col = layout.column(align = True)
        row = col.row()
        col.label(text = "Animation Options:", icon="NONE")
        col.prop(addon_prefs, "topbar_animation_keyframes",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_animation_range",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_animation_play",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_animation_sync",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_animation_keyframetype",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_animation_keyingset",toggle=addon_prefs.bfa_button_style)

# BFA - removed as redundant, operators exist in space_toolbar.py
'''
######################################## Edit Apply Ops ########################################
class VIEW3D_MT_topbar_object_apply_location(bpy.types.Operator):
    """Applies the current location"""
    bl_idname = "view3d.topbar_apply_location"
    bl_label = "Apply Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        return {'FINISHED'}


class VIEW3D_MT_topbar_object_apply_rotate(bpy.types.Operator):
    """Applies the current rotation"""
    bl_idname = "view3d.topbar_apply_rotate"
    bl_label = "Apply Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return {'FINISHED'}


class VIEW3D_MT_topbar_object_apply_scale(bpy.types.Operator):
    """Applies the current scale"""
    bl_idname = "view3d.topbar_apply_scale"
    bl_label = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return {'FINISHED'}


class VIEW3D_MT_topbar_object_apply_all(bpy.types.Operator):
    """Applies the current location, rotation and scale"""
    bl_idname = "view3d.topbar_apply_all"
    bl_label = "Apply All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}


class VIEW3D_MT_topbar_object_apply_rotscale(bpy.types.Operator):
    """Applies the current rotation and scale"""
    bl_idname = "view3d.topbar_apply_rotscale"
    bl_label = "Apply Rotation & Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        return {'FINISHED'}
'''

######################################## Edit Menu ########################################
class TOPBAR_MT_edit(Menu):
    bl_idname = "TOPBAR_MT_edit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        obj = context.object

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_edit_cbox:

            layout.popover(panel = "TOPBAR_PT_edit", text="", icon = "NONE")

            if obj is not None:

                if addon_prefs.topbar_edit_edit:

                    mode = obj.mode

                    if mode == 'EDIT':
                        if context.mode == "EDIT_GREASE_PENCIL":
                            row = layout.row(align=True)
                            props = row.operator("grease_pencil.stroke_simplify", text="", icon="MOD_SIMPLIFY")
                            props.mode = 'FIXED'
                            props = row.operator("grease_pencil.stroke_simplify", text="", icon="SIMPLIFY_ADAPTIVE")
                            props.mode = 'ADAPTIVE'            
                            props = row.operator("grease_pencil.stroke_simplify", text="", icon="SIMPLIFY_SAMPLE")
                            props.mode = 'SAMPLE'            
                            props = row.operator("grease_pencil.stroke_simplify", text="", icon="MERGE")
                            props.mode = 'MERGE'
                        
                        row = layout.row(align=True)
                        row.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS', text="")
                        row.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES', text="")
                        row.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES', text="")
                        row.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED', text="")
                        row.operator("mesh.dissolve_mode", icon='DISSOLVE_SELECTION', text="")
                        row.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE', text="")

                        row = layout.row(align=True)
                        row.operator("mesh.remove_doubles", icon='REMOVE_DOUBLES', text="")

                        row = layout.row(align=True)
                        row.operator_menu_enum("mesh.merge", "type", text = "", icon = "MERGE")
                        row.operator_menu_enum("mesh.separate", "type", text = "", icon = "SEPARATE")

                if addon_prefs.topbar_edit_weightinedit:

                    mode = obj.mode

                    if mode in ( 'EDIT', 'WEIGHT_PAINT'):

                        row = layout.row(align=True)
                        row.operator("object.vertex_group_normalize_all", icon='WEIGHT_NORMALIZE_ALL', text="")
                        row.operator("object.vertex_group_normalize",icon='WEIGHT_NORMALIZE', text="")
                        row.operator("object.vertex_group_mirror",icon='WEIGHT_MIRROR', text="")
                        row.operator("object.vertex_group_invert", icon='WEIGHT_INVERT',text="")
                        row.operator("object.vertex_group_clean", icon='WEIGHT_CLEAN',text="")
                        row.operator("object.vertex_group_quantize", icon='WEIGHT_QUANTIZE',text="")
                        row.operator("object.vertex_group_levels", icon='WEIGHT_LEVELS',text="")
                        row.operator("object.vertex_group_smooth", icon='WEIGHT_SMOOTH',text="")
                        row.operator("object.vertex_group_limit_total", icon='WEIGHT_LIMIT_TOTAL',text="")

                if addon_prefs.topbar_edit_objectapply:

                    mode = obj.mode

                    if mode == 'OBJECT':

                        row = layout.row(align=True)
                        row.operator("view3d.tb_apply_location", text="", icon = "APPLYMOVE") # needed a tooltip, so see above ...
                        row.operator("view3d.tb_apply_rotate", text="", icon = "APPLYROTATE")
                        row.operator("view3d.tb_apply_scale", text="", icon = "APPLYSCALE")
                        row.operator("view3d.tb_apply_all", text="", icon = "APPLYALL")
                        row.operator("view3d.tb_apply_rotscale", text="", icon = "APPLY_ROTSCALE")

                if addon_prefs.topbar_edit_objectapply2:

                    mode = obj.mode

                    if mode == 'OBJECT':

                        row = layout.row(align=True)
                        row.operator("object.visual_transform_apply", text = "", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
                        row.operator("object.duplicates_make_real", text = "", icon = "MAKEDUPLIREAL")
                        row.operator("object.parent_inverse_apply", text="", icon = "APPLY_PARENT_INVERSE")
                        row.operator("object.visual_geometry_to_objects", text="", icon="VISUAL_GEOMETRY_TO_OBJECTS")

                if addon_prefs.topbar_edit_objectapplydeltas:

                    if mode == 'OBJECT':

                        row = layout.row(align=True)

                        myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYMOVEDELTA")
                        myvar.mode = 'LOC'

                        myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYROTATEDELTA")
                        myvar.mode = 'ROT'

                        myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYSCALEDELTA")
                        myvar.mode = 'SCALE'

                        myvar = row.operator("object.transforms_to_deltas", text="", icon = "APPLYALLDELTA")
                        myvar.mode = 'ALL'

                        row.operator("object.anim_transforms_to_deltas", text = "", icon = "APPLYANIDELTA")

                if addon_prefs.topbar_edit_objectclear:

                    mode = obj.mode

                    if mode == 'OBJECT':

                        row = layout.row(align=True)
                        row.operator("object.location_clear", text="", icon = "CLEARMOVE")
                        row.operator("object.rotation_clear", text="", icon = "CLEARROTATE")
                        row.operator("object.scale_clear", text="", icon = "CLEARSCALE")
                        row.operator("object.origin_clear", text="", icon = "CLEARORIGIN")


######################################## Edit Panel ########################################
class TOPBAR_PT_edit(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Topbar Edit"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        obj = context.object

        col = layout.column(align = True)
        col.label(text="Topbar Edit:")

        if obj is None:

                col = layout.row()
                col.alert=True
                col.label(text = "No Active Mesh", icon="INFO")

        if obj is not None:

                col = layout.column(align = True)
                row = col.row()
                col.alert=True
                col.label(text="Edit Mode",icon="EDIT")
                col.alert=False
                col.prop(addon_prefs, "topbar_edit_edit",toggle=addon_prefs.bfa_button_style)
                col.prop(addon_prefs, "topbar_edit_weightinedit",toggle=addon_prefs.bfa_button_style)
                col.alert=True
                col.label(text="Object Mode", icon="OBJECT_DATAMODE")
                col.alert=False
                col.prop(addon_prefs, "topbar_edit_objectapply",toggle=addon_prefs.bfa_button_style)
                col.prop(addon_prefs, "topbar_edit_objectapply2",toggle=addon_prefs.bfa_button_style)
                col.prop(addon_prefs, "topbar_edit_objectapplydeltas",toggle=addon_prefs.bfa_button_style)
                col.prop(addon_prefs, "topbar_edit_objectclear",toggle=addon_prefs.bfa_button_style)


######################################## Misc Menu ########################################
class TOPBAR_MT_misc(Menu):
    bl_idname = "TOPBAR_MT_misc"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        window = context.window
        scene = window.scene
        obj = context.object

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        if addon_prefs.topbar_misc_cbox:

            layout.popover(panel = "TOPBAR_PT_misc", text="", icon = "NONE")

            if addon_prefs.topbar_misc_viewport:

                if obj is not None:
                    row = layout.row(align=True)
                    row.popover(panel="OBJECT_PT_display", text="", icon = "VIEW")

            if addon_prefs.topbar_misc_undoredo:

                row = layout.row(align=True)
                row.operator("ed.undo", icon='UNDO',text="")
                row.operator("ed.redo", icon='REDO',text="")

            if addon_prefs.topbar_misc_undohistory:

                row = layout.row(align=True)
                row.operator("ed.undo_history", icon='UNDO_HISTORY',text="")

            if addon_prefs.topbar_misc_repeat:

                row = layout.row(align=True)
                row.operator("screen.repeat_last", icon='REPEAT', text="")
                row.operator("screen.repeat_history", icon='REDO_HISTORY', text="")

            if addon_prefs.topbar_misc_scene:

                row = layout.row(align=True)

                layout.template_ID(window, "scene", new="scene.new", unlink="scene.delete") # bfa - the scene drodpown box from the info menu bar

            if addon_prefs.topbar_misc_viewlayer:

                window = context.window
                screen = context.screen
                scene = window.scene

                row = layout.row(align=True)
                layout.template_search(window, "view_layer", scene, "view_layers", new="scene.view_layer_add", unlink="scene.view_layer_remove")

            if addon_prefs.topbar_misc_last:

                row = layout.row(align=True)
                row.operator("screen.redo_last", text="Last", icon = "LASTOPERATOR")

            if addon_prefs.topbar_misc_operatorsearch:

                row = layout.row(align=True)
                row.operator("wm.search_menu", text="", icon='SEARCH_MENU')
                row.operator("wm.search_operator", text="", icon='VIEWZOOM')

            if addon_prefs.topbar_misc_info:

                row = layout.row(align=True)

                # messages
                row.template_reports_banner()
                row.template_running_jobs()

                # stats
                scene = context.scene
                view_layer = context.view_layer

                row.label(text=scene.statistics(view_layer), translate=False)


######################################## Misc Panel ########################################
class TOPBAR_PT_misc(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Topbar Misc"

    def draw(self, context):
        layout = self.layout

        preferences = context.preferences
        addon_prefs = preferences.addons["bforartists_toolbar_settings"].preferences

        col = layout.column(align = True)
        col.label(text="Topbar Misc:")
        col = layout.column(align = True)
        col.prop(addon_prefs, "topbar_misc_viewport",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_undoredo",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_undohistory",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_repeat",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_scene",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_viewlayer",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_last",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_operatorsearch",toggle=addon_prefs.bfa_button_style)
        col.prop(addon_prefs, "topbar_misc_info",toggle=addon_prefs.bfa_button_style)


classes = [
    TOPBAR_HT_tool_bar,
    TOPBAR_PT_main,
    TOPBAR_MT_toolbar_type,
    TOPBAR_PT_file,
    TOPBAR_PT_meshedit,
    TOPBAR_PT_primitives,
    TOPBAR_PT_tools,
    TOPBAR_PT_animation,
    TOPBAR_PT_edit,
    TOPBAR_PT_misc,
    TOPBAR_PT_normals_autosmooth,
    TOPBAR_PT_menu_image,
    #VIEW3D_MT_topbar_object_apply_location,
    #VIEW3D_MT_topbar_object_apply_rotate,
    #VIEW3D_MT_topbar_object_apply_scale,
    #VIEW3D_MT_topbar_object_apply_all,
    #VIEW3D_MT_topbar_object_apply_rotscale,
]

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
