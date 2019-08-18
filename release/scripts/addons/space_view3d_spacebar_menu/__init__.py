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
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #

bl_info = {
    "name": "Dynamic Context Menu",
    "author": "meta-androcto",
    "version": (1, 9, 4),
    "blender": (2, 80, 0),
    "location": "View3D > Spacebar",
    "description": "Object Mode Context Sensitive Spacebar Menu",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Dynamic_Spacebar_Menu",
    "category": "3D View",
}

if "bpy" in locals():
    import importlib
    importlib.reload(object_menus)
    importlib.reload(edit_mesh)
    importlib.reload(transform_menus)
    importlib.reload(select_menus)
    importlib.reload(view_menus)
    importlib.reload(armature_menus)
    importlib.reload(curve_menus)
    importlib.reload(snap_origin_cursor)
    importlib.reload(sculpt_brush_paint)

else:
    from . import object_menus
    from . import edit_mesh
    from . import transform_menus
    from . import select_menus
    from . import view_menus
    from . import armature_menus
    from . import curve_menus
    from . import snap_origin_cursor
    from . import sculpt_brush_paint

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

from bl_ui.properties_paint_common import UnifiedPaintPanel


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
            layout.menu("VIEW3D_MT_View_Directions", icon='ZOOM_ALL')
            layout.menu("VIEW3D_MT_View_Navigation", icon='PIVOT_BOUNDBOX')
            UseSeparator(self, context)
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
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
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
#                if context.gpencil_data and context.gpencil_data.use_stroke_edit_mode:
#                    layout.menu("VIEW3D_MT_Edit_Gpencil", icon='GREASEPENCIL')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Mesh Edit Mode #
            if obj and obj.type == 'MESH' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Edit_Mesh", icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_Edit_Multi", icon='VERTEXSEL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_mesh_add", text="Add Mesh", icon='OUTLINER_OB_MESH')
                layout.menu("VIEW3D_MT_Edit_Mesh", text="Mesh", icon='MESH_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuEdit", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenuEM", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_EditCursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UV_Map", icon='MOD_UVPROJECT')
                layout.menu("VIEW3D_MT_edit_mesh_context_menu",  text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_edit_mesh_extrude", icon='XRAY')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_edit_mesh_delete", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Sculpt Mode #
            if obj and obj.type == 'MESH' and obj.mode in {'SCULPT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Sculpts", icon='SCULPTMODE_HLT')
                layout.menu("VIEW3D_MT_Angle_Control", text="Angle Control", icon='BRUSH_SCULPT_DRAW')
                layout.menu("VIEW3D_MT_Brush_Settings", icon='BRUSH_DATA')
                layout.menu("VIEW3D_MT_Hide_Masks", icon='RESTRICT_VIEW_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Sculpt_Specials", icon='SOLO_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Vertex Paint #
            if obj and obj.type == 'MESH' and obj.mode in {'VERTEX_PAINT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                UseSeparator(self, context)
    #            layout.menu("VIEW3D_MT_Brush_Settings", icon='BRUSH_DATA')
                layout.menu("VIEW3D_MT_Brush_Selection",
                            text="Vertex Paint Tool")
                layout.menu("VIEW3D_MT_Vertex_Colors", icon='GROUP_VCOL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Weight Paint Menu #
            if obj and obj.type == 'MESH' and obj.mode in {'WEIGHT_PAINT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Paint_Weights", icon='WPAINT_HLT')
    #            layout.menu("VIEW3D_MT_Brush_Settings", icon='BRUSH_DATA')
                layout.menu("VIEW3D_MT_Brush_Selection",
                            text="Weight Paint Tool", icon='BRUSH_TEXMASK')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Texture Paint #
            if obj and obj.type == 'MESH' and obj.mode in {'TEXTURE_PAINT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
    #            layout.menu("VIEW3D_MT_Brush_Settings", icon='BRUSH_DATA')
                layout.menu("VIEW3D_MT_Brush_Selection",
                            text="Texture Paint Tool", icon='SCULPTMODE_HLT')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Curve Object Mode #
            if obj and obj.type == 'CURVE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Edit Curve #
            if obj and obj.type == 'CURVE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Edit_Curve",
                            icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_curve_add", text="Add Curve",
                            icon='OUTLINER_OB_CURVE')
                layout.menu("VIEW3D_MT_Edit_Curve", icon='CURVE_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_EditCurveCtrlpoints",
                            icon='CURVE_BEZCURVE')
                layout.menu("VIEW3D_MT_EditCurveSpecials",
                            icon='SOLO_OFF')
                UseSeparator(self, context)
                layout.operator("curve.delete", text="Delete Object",
                                icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Surface Object Mode #
            if obj and obj.type == 'SURFACE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Edit Surface #
            if obj and obj.type == 'SURFACE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Edit_Surface", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_surface_add", text="Add Surface",
                            icon='OUTLINER_OB_SURFACE')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.prop_menu_enum(settings, "proportional_edit",
                                      icon="PROP_CON")
                layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                      icon="SMOOTHCURVE")
                layout.menu("VIEW3D_MT_EditCurveSpecials",
                            icon='SOLO_OFF')
                UseSeparator(self, context)
                layout.operator("curve.delete", text="Delete Object",
                                icon='CANCEL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Metaball Object Mode #
            if obj and obj.type == 'META' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Edit Metaball #
            if obj and obj.type == 'META' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_SelectMetaball", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.metaball_add", "type",
                                          text="Add Metaball",
                                          icon='OUTLINER_OB_META')
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.prop_menu_enum(settings, "proportional_edit",
                                      icon="PROP_CON")
                layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                      icon="SMOOTHCURVE")
                UseSeparator(self, context)
                layout.operator("mball.delete_metaelems", text="Delete Object",
                                icon='CANCEL')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Text Object Mode #
            if obj and obj.type == 'FONT' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.operator("view3d.interactive_mode_text", icon='VIEW3D')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Text Edit Mode #
            # To Do: Space is already reserved for the typing tool
            if obj and obj.type == 'FONT' and obj.mode in {'EDIT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.operator("object.editmode_toggle", text="Enter Object Mode",
                                icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_select_edit_text", icon='VIEW3D')
                layout.menu("VIEW3D_MT_edit_font", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Camera Object Mode #
            if obj and obj.type == 'CAMERA' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Lamp Object Mode #
            if obj and obj.type == 'LIGHT' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Armature Object Mode #
            if obj and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuArmature", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Armature Edit #
            if obj and obj.type == 'ARMATURE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Edit_Armature",
                            icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_armature_add", text="Add Armature",
                            icon='ARMATURE_DATA')
                layout.menu("VIEW3D_MT_Edit_Armature", text="Armature",
                            icon='OUTLINER_DATA_ARMATURE')
                layout.menu("VIEW3D_MT_EditArmatureTK",
                            icon='ARMATURE_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuArmatureEdit", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_armature_context_menu", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_edit_armature_roll",
                            icon='BONE_DATA')
                UseSeparator(self, context)
                layout.operator("armature.delete", text="Delete Object",
                                icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Armature Pose #
            if obj and obj.type == 'ARMATURE' and obj.mode in {'POSE'}:

                arm = context.active_object.data

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Armature", icon='VIEW3D')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Pose", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Pose", icon='ARMATURE_DATA')
                layout.menu("VIEW3D_MT_TransformMenuArmaturePose", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_pose_transform", icon='EMPTY_DATA')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                layout.menu("VIEW3D_MT_PoseCopy", icon='FILE')

                if arm.display_type in {'BBONE', 'ENVELOPE'}:
                    layout.operator("transform.transform",
                                    text="Scale Envelope Distance").mode = 'BONE_SIZE'

                layout.menu("VIEW3D_MT_pose_apply", icon='AUTO')
                layout.operator("pose.relax", icon='ARMATURE_DATA')
                layout.menu("VIEW3D_MT_KeyframeMenu", icon='KEY_HLT')
                layout.menu("VIEW3D_MT_pose_context_menu", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_pose_group", icon='GROUP_BONE')
                UseSeparator(self, context)
                layout.operator_menu_enum("pose.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT_BONE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')

                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Lattice Object Mode #
            if obj and obj.type == 'LATTICE' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Edit Lattice #
            if obj and obj.type == 'LATTICE' and obj.mode in {'EDIT'}:

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_Object_Interactive_Other", icon='OBJECT_DATA')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Edit_Lattice",
                            icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.prop_menu_enum(settings, "proportional_edit",
                                      icon="PROP_CON")
                layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                      icon="SMOOTHCURVE")
                UseSeparator(self, context)
                layout.operator("lattice.make_regular")
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Empty Object Mode #
            if obj and obj.type == 'EMPTY' and obj.mode in {'OBJECT'}:

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

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
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenuLite", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_CursorMenuLite", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Particle Menu #
            if obj and context.mode == 'PARTICLE':

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_InteractiveMode", icon='VIEW3D')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Particle",
                            icon='RESTRICT_SELECT_OFF')
                layout.menu("VIEW3D_MT_Selection_Mode_Particle",
                            text="Select and Display Mode", icon='PARTICLE_PATH')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
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
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Grease Pencil Object Mode #
            if obj and obj.type == 'GPENCIL' and obj.mode in {'OBJECT'}:
                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_interactive_mode_gpencil", icon='EDITMODE_HLT')
                layout.menu("VIEW3D_MT_View_Menu", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_Select_Object", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                layout.menu("VIEW3D_MT_Object", icon='VIEW3D')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_TransformMenu", icon='EMPTY_ARROWS')
                layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')
                layout.menu("VIEW3D_MT_CursorMenu", icon='PIVOT_CURSOR')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_ParentMenu", icon='PIVOT_ACTIVE')
                layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_object_context_menu", text="Specials", icon='SOLO_OFF')
                layout.menu("VIEW3D_MT_Camera_Options", icon='OUTLINER_OB_CAMERA')
                UseSeparator(self, context)
                layout.operator_menu_enum("object.gpencil_modifier_add", "type", icon='MODIFIER')
                layout.operator_menu_enum("object.shaderfx_add", "type", icon ='SHADERFX')
                layout.operator_menu_enum("object.constraint_add",
                                          "type", text="Add Constraint", icon='CONSTRAINT')
                UseSeparator(self, context)
                layout.operator("object.delete", text="Delete Object", icon='X')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

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
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

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
                layout.menu("VIEW3D_MT_select_gpencil", icon='RESTRICT_SELECT_OFF')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

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
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

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
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')

    # Light Probe Menu #
            if obj and obj.type == 'LIGHT_PROBE':
                layout.operator_context = 'INVOKE_REGION_WIN'

                layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
                layout.menu("VIEW3D_MT_Animation_Player",
                            text="Animation", icon='PLAY')
                layout.operator("wm.toolbar", text="Tools", icon='TOOL_SETTINGS')
                layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon='HEART')
                UseSeparator(self, context)
                layout.menu("INFO_MT_area", icon='WORKSPACE')
                layout.menu("VIEW3D_MT_View_Directions", icon='ZOOM_ALL')
                layout.menu("VIEW3D_MT_View_Navigation", icon='PIVOT_BOUNDBOX')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')
                UseSeparator(self, context)
                layout.operator("view3d.snap_cursor_to_center",
                                text="Cursor to World Origin", icon='CURSOR')
                layout.operator("view3d.snap_cursor_to_grid",
                                text="Cursor to Grid", icon='SNAP_GRID')
                UseSeparator(self, context)
                layout.menu("VIEW3D_MT_UndoS", icon='ARROW_LEFTRIGHT')
                UseSeparator(self, context)
                layout.prop(view, "show_region_toolbar", icon='MENU_PANEL')
                layout.prop(view, "show_region_ui", icon='MENU_PANEL')


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

    object_menus.register()
    edit_mesh.register()
    transform_menus.register()
    select_menus.register()
    view_menus.register()
    armature_menus.register()
    curve_menus.register()
    snap_origin_cursor.register()
    sculpt_brush_paint.register()

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
    select_menus.unregister()
    view_menus.unregister()
    armature_menus.unregister()
    curve_menus.unregister()
    snap_origin_cursor.unregister()
    sculpt_brush_paint.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
