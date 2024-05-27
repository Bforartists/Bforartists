# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Dynamic Context Menu",
    "author": "meta-androcto",
    "version": (1, 9, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Spacebar",
    "description": "Object Mode Context Sensitive Spacebar Menu",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/context_menu.html",
    "category": "Interface",
}

if "bpy" in locals():
    import importlib
    importlib.reload(object_menus)
    importlib.reload(edit_mesh)
    importlib.reload(transform_menus)
    importlib.reload(view_menus)
    importlib.reload(armature_menus)
    importlib.reload(curve_menus)
    importlib.reload(snap_origin_cursor)
    importlib.reload(animation_menus)

else:
    from . import object_menus
    from . import edit_mesh
    from . import transform_menus
    from . import view_menus
    from . import armature_menus
    from . import curve_menus
    from . import snap_origin_cursor
    from . import animation_menus


import bpy
from bpy.types import (
        Operator,
        Menu,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )


# Dynamic Context Sensitive Menu #
# Main Menu based on Object Type & 3d View Editor Mode #

class VIEW3D_MT_Space_Dynamic_Menu(Menu):
    bl_label = "Dynamic Context Menu"

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'
        obj = context.active_object
        view = context.space_data

# No Object Selected #
        ob = bpy.context.object
        if not ob or not ob.select_get():

            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
            layout.menu("VIEW3D_MT_Animation_Player",
                        text="Animation", icon='PLAY')
            layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
            UseSeparator(self, context)
            layout.menu("INFO_MT_area", icon='WORKSPACE')
            layout.menu("VIEW3D_MT_view_viewpoint", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_view_navigation", icon='PIVOT_BOUNDBOX')
            layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
            UseSeparator(self, context)
            layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
            UseSeparator(self, context)
            layout.operator("view3d.snap_cursor_to_center",
                            text="Cursor to World Origin")
            layout.operator("view3d.snap_cursor_to_grid",
                            text="Cursor to Grid")
            layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
            UseSeparator(self, context)
            layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
            layout.prop(view, "show_region_ui", icon='MENU_PANEL')

        else:
# Mesh Object Mode #

            if obj and obj.type == 'MESH' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Mesh Edit Mode #
            if obj and obj.type == 'MESH' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_Edit_Multi", icon='VERTEXSEL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_mesh", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_mesh_add", text="Add Mesh", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_edit_mesh", text="Mesh", icon='MESH_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_edit_mesh_vertices", icon='VERTEXSEL')
                layout.menu("VIEW3D_MT_edit_mesh_edges", icon='EDGESEL')
                layout.menu("VIEW3D_MT_edit_mesh_faces", icon='FACESEL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_uv_map", icon='MOD_UVPROJECT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_EditCursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_edit_mesh_delete", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Sculpt Mode #
            if obj and obj.type == 'MESH' and obj.mode in {'SCULPT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_view", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_sculpt", icon='SCULPTMODE_HLT')
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Vertex Paint #
            if obj and obj.type == 'MESH' and obj.mode in {'VERTEX_PAINT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_view", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_paint_vertex", icon='VPAINT_HLT')
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Weight Paint Menu #
            if obj and obj.type == 'MESH' and obj.mode in {'WEIGHT_PAINT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_view", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_paint_weight", icon='WPAINT_HLT')
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Texture Paint #
            if obj and obj.type == 'MESH' and obj.mode in {'TEXTURE_PAINT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_view", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Curve Object Mode #
            if obj and obj.type == 'CURVE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Edit Curve #
            if obj and obj.type == 'CURVE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_curve",
                            icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_curve_add", text="Add Curve",
                            icon='OUTLINER_OB_CURVE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Edit_Curve", icon='CURVE_DATA')
                layout.menu("VIEW3D_MT_transform", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_edit_curve_ctrlpoints",
                            icon='CURVE_BEZCURVE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_edit_curve_delete", text="Delete",
                                icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Surface Object Mode #
            if obj and obj.type == 'SURFACE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Edit Surface #
            if obj and obj.type == 'SURFACE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_surface", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_surface_add", text="Add Surface",
                            icon='OUTLINER_OB_SURFACE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Edit_Curve", icon='CURVE_DATA')
                layout.menu("VIEW3D_MT_transform", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_edit_curve_ctrlpoints",
                            icon='CURVE_BEZCURVE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_edit_curve_delete", text="Delete",
                                icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')


# Metaball Object Mode #
            if obj and obj.type == 'META' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Edit Metaball #
            if obj and obj.type == 'META' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_metaball", icon='RESTRICT_SELECT_OFF')
                layout.operator_menu_enum("object.metaball_add", "type",
                                          text="Add Metaball",
                                          icon='OUTLINER_OB_META')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_transform", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_mirror", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                layout.operator("mball.duplicate_metaelems", icon='OUTLINER_DATA_META')
                layout.menu("VIEW3D_MT_edit_meta_showhide", icon='HIDE_OFF')
                UseSeparator(self, context)
                layout.operator("mball.delete_metaelems", text="Delete", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Camera Object Mode #
            if obj and obj.type == 'CAMERA' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenuCamera", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Lamp Object Mode #
            if obj and obj.type == 'LIGHT' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Armature Object Mode #
            if obj and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Armature Edit #
            if obj and obj.type == 'ARMATURE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_armature",
                            icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_armature_add", text="Add Armature",
                            icon='ARMATURE_DATA')
                layout.menu("VIEW3D_MT_Edit_Armature", text="Armature",
                            icon='OUTLINER_DATA_ARMATURE')
                layout.menu("VIEW3D_MT_EditArmatureTK",
                            icon='ARMATURE_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_transform_armature", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_mirror", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_object_parent")
                layout.menu("VIEW3D_MT_edit_armature_roll",
                            icon='BONE_DATA')
                UseSeparator(self, context)
                layout.operator("armature.delete", text="Delete Object",
                                icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Armature Pose #
            if obj and obj.type == 'ARMATURE' and obj.mode in {'POSE'}:

                arm = context.active_object.data

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_pose", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Pose", icon='ARMATURE_DATA')
                layout.menu("VIEW3D_MT_transform_armature", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_pose_transform", icon='EMPTY_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_PoseCopy", icon='FILE')

                if arm.display_type in {'BBONE', 'ENVELOPE'}:
                    layout.operator("transform.transform",
                                    text="Scale Envelope Distance").mode = 'BONE_SIZE'

                layout.menu("VIEW3D_MT_pose_apply", icon='AUTO')
                layout.operator("pose.relax", icon='ARMATURE_DATA')
                layout.menu("VIEW3D_MT_pose_group", icon='GROUP_BONE')
                UseSeparator(self, context)
                layout.operator_menu_enum("pose.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT_BONE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Lattice Object Mode #
            if obj and obj.type == 'LATTICE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Edit Lattice #
            if obj and obj.type == 'LATTICE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_lattice",
                            icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_mirror", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.operator("lattice.make_regular")
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Empty Object Mode #
            if obj and obj.type == 'EMPTY' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Speaker Object Mode #
            if obj and obj.type == 'SPEAKER' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Particle Menu #
            if obj and context.mode == 'PARTICLE':

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_InteractiveMode", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_particle",
                            text="Select", icon='PARTICLE_PATH')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_mirror", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
#                layout.prop_menu_enum(settings, "proportional_edit",
#                                      icon="PROP_CON")
                layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                      icon="SMOOTHCURVE")
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_particle", icon='PARTICLEMODE')
                layout.menu("VIEW3D_MT_particle_context_menu", text="Hair Specials", icon='HAIR')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Grease Pencil Object Mode #
            if obj and obj.type == 'GPENCIL' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_interactive_mode_gpencil", icon='EDITMODE_HLT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Grease Pencil Edit Mode #
            if obj and obj.type == 'GPENCIL' and obj.mode in {'EDIT_GPENCIL'}:
                layout.operator_context = 'INVOKE_REGION_WIN'

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_interactive_mode_gpencil", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_gpencil", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_edit_gpencil", icon='GREASEPENCIL')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Grease Pencil Sculpt Mode #
            if obj and obj.type == 'GPENCIL' and obj.mode in {'SCULPT_GPENCIL'}:
                layout.operator_context = 'INVOKE_REGION_WIN'

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_interactive_mode_gpencil", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Grease Pencil Paint Mode #
            if obj and obj.type == 'GPENCIL' and obj.mode in {'PAINT_GPENCIL'}:
                layout.operator_context = 'INVOKE_REGION_WIN'

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_interactive_mode_gpencil", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_paint_gpencil", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Grease Pencil Weight Mode #
            if obj and obj.type == 'GPENCIL' and obj.mode in {'WEIGHT_GPENCIL'}:
                layout.operator_context = 'INVOKE_REGION_WIN'

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_interactive_mode_gpencil", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_weight_gpencil", icon="GPBRUSH_WEIGHT")
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

# Light Probe Menu #
            if obj and obj.type == 'LIGHT_PROBE':
                layout.operator_context = 'INVOKE_REGION_WIN'

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

# Text Object Mode #
            if obj and obj.type == 'FONT' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_object", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_add", icon='MESH_CUBE')
                layout.menu("VIEW3D_MT_Camera_Options", icon='CAMERA_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_collection", text = "Collections", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')


# Text Edit Mode
def menu_func(self, context):
    layout = self.layout

    layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
    layout.menu("VIEW3D_MT_select_edit_text", icon='VIEW3D')
    layout.separator()
    layout.operator_context = 'INVOKE_REGION_WIN'
    layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
    layout.menu("VIEW3D_MT_Animation_Player",
                text="Animation", icon='PLAY')
    layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
    layout.operator("object.editmode_toggle", text="Enter Object Mode",
                    icon='OBJECT_DATA')
    layout.separator()
    layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')


# Preferences utility functions

# Draw Separator #
def UseSeparator(operator, context):
    useSep = bpy.context.preferences.addons[__name__].preferences.use_separators
    if useSep:
        operator.layout.separator()


# Use compact brushes menus #
def UseBrushesLists():
    # separate function just for more convenience
    useLists = bpy.context.preferences.addons[__name__].preferences.use_brushes_lists

    return bool(useLists)


# Addon Preferences #
class VIEW3D_MT_Space_Dynamic_Menu_Pref(AddonPreferences):
    bl_idname = __name__

    use_separators: BoolProperty(
                    name="Use Separators in the menus",
                    default=True,
                    description=("Use separators in the menus, a trade-off between \n"
                                 "readability vs. using more space for displaying items")
                    )
    use_brushes_lists: BoolProperty(
                    name="Use compact menus for brushes",
                    default=False,
                    description=("Use more compact menus instead  \n"
                                 "of thumbnails for displaying brushes")
                    )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "use_separators", toggle=True)
        row.prop(self, "use_brushes_lists", toggle=True)


# List The Classes #

classes = (
    VIEW3D_MT_Space_Dynamic_Menu,
    VIEW3D_MT_Space_Dynamic_Menu_Pref
)


# Register Classes & Hotkeys #
def register():
    from bpy.utils import register_class
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_edit_font_context_menu.append(menu_func)

    object_menus.register()
    edit_mesh.register()
    transform_menus.register()
    view_menus.register()
    armature_menus.register()
    curve_menus.register()
    snap_origin_cursor.register()
    animation_menus.register()


    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
        kmi.properties.name = "VIEW3D_MT_Space_Dynamic_Menu"


# Unregister Classes & Hotkeys #
def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "VIEW3D_MT_Space_Dynamic_Menu":
                    km.keymap_items.remove(kmi)
                    break

    object_menus.unregister()
    edit_mesh.unregister()
    transform_menus.unregister()
    view_menus.unregister()
    armature_menus.unregister()
    curve_menus.unregister()
    snap_origin_cursor.unregister()
    animation_menus.unregister()


    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_edit_font_context_menu.remove(menu_func)

if __name__ == "__main__":
    register()
