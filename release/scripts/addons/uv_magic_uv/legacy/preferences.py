# <pep8-80 compliant>

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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "5.2"
__date__ = "17 Nov 2018"

import bpy
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
)
from bpy.types import AddonPreferences

from . import op
from . import ui
from .. import addon_updater_ops
from ..utils.bl_class_registry import BlClassRegistry

__all__ = [
    'add_builtin_menu',
    'remove_builtin_menu',
    'Preferences'
]


def view3d_uvmap_menu_fn(self, context):
    layout = self.layout
    sc = context.scene

    layout.separator()
    layout.label(text="Copy/Paste UV", icon='IMAGE_COL')
    # Copy/Paste UV
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_CopyPasteUV.bl_idname,
                text="Copy/Paste UV")
    # Transfer UV
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_TransferUV.bl_idname,
                text="Transfer UV")

    layout.separator()
    layout.label("UV Manipulation", icon='IMAGE_COL')
    # Flip/Rotate UV
    ops = layout.operator(op.flip_rotate_uv.MUV_OT_FlipRotate.bl_idname,
                          text="Flip/Rotate UV")
    ops.seams = sc.muv_flip_rotate_uv_seams
    # Mirror UV
    ops = layout.operator(op.mirror_uv.MUV_OT_MirrorUV.bl_idname,
                          text="Mirror UV")
    ops.axis = sc.muv_mirror_uv_axis
    # Move UV
    layout.operator(op.move_uv.MUV_OT_MoveUV.bl_idname, text="Move UV")
    # World Scale UV
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_WorldScaleUV.bl_idname,
                text="World Scale UV")
    # Preserve UV
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_PreserveUVAspect.bl_idname,
                text="Preserve UV")
    # Texture Lock
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_TextureLock.bl_idname,
                text="Texture Lock")
    # Texture Wrap
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_TextureWrap.bl_idname,
                text="Texture Wrap")
    # UV Sculpt
    layout.prop(sc, "muv_uv_sculpt_enable", text="UV Sculpt")

    layout.separator()
    layout.label("UV Mapping", icon='IMAGE_COL')
    # Unwrap Constraint
    ops = layout.operator(
        op.unwrap_constraint.MUV_OT_UnwrapConstraint.bl_idname,
        text="Unwrap Constraint")
    ops.u_const = sc.muv_unwrap_constraint_u_const
    ops.v_const = sc.muv_unwrap_constraint_v_const
    # Texture Projection
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_TextureProjection.bl_idname,
                text="Texture Projection")
    # UVW
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_UVW.bl_idname, text="UVW")


def view3d_object_menu_fn(self, _):
    layout = self.layout

    layout.separator()
    # Copy/Paste UV (Among Objecct)
    layout.menu(ui.VIEW3D_MT_object.MUV_MT_CopyPasteUV_Object.bl_idname,
                text="Copy/Paste UV")
    layout.label("Copy/Paste UV", icon='IMAGE_COL')


def image_uvs_menu_fn(self, context):
    layout = self.layout
    sc = context.scene

    layout.separator()
    # Align UV Cursor
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_AlignUVCursor.bl_idname,
                text="Align UV Cursor")
    # UV Bounding Box
    layout.prop(sc, "muv_uv_bounding_box_show", text="UV Bounding Box")
    # UV Inspection
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_UVInspection.bl_idname,
                text="UV Inspection")
    layout.label("Editor Enhancement", icon='IMAGE_COL')

    layout.separator()
    # Align UV
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_AlignUV.bl_idname, text="Align UV")
    # Smooth UV
    ops = layout.operator(op.smooth_uv.MUV_OT_SmoothUV.bl_idname,
                          text="Smooth")
    ops.transmission = sc.muv_smooth_uv_transmission
    ops.select = sc.muv_smooth_uv_select
    ops.mesh_infl = sc.muv_smooth_uv_mesh_infl
    # Select UV
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_SelectUV.bl_idname, text="Select UV")
    # Pack UV
    ops = layout.operator(op.pack_uv.MUV_OT_PackUV.bl_idname, text="Pack UV")
    ops.allowable_center_deviation = sc.muv_pack_uv_allowable_center_deviation
    ops.allowable_size_deviation = sc.muv_pack_uv_allowable_size_deviation
    layout.label("UV Manipulation", icon='IMAGE_COL')

    layout.separator()
    # Copy/Paste UV (on UV/Image Editor)
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_CopyPasteUV_UVEdit.bl_idname,
                text="Copy/Paste UV")
    layout.label("Copy/Paste UV", icon='IMAGE_COL')


def add_builtin_menu():
    bpy.types.VIEW3D_MT_uv_map.append(view3d_uvmap_menu_fn)
    bpy.types.VIEW3D_MT_object.append(view3d_object_menu_fn)
    bpy.types.IMAGE_MT_uvs.append(image_uvs_menu_fn)


def remove_builtin_menu():
    bpy.types.IMAGE_MT_uvs.remove(image_uvs_menu_fn)
    bpy.types.VIEW3D_MT_uv_map.remove(view3d_uvmap_menu_fn)
    bpy.types.VIEW3D_MT_object.remove(view3d_object_menu_fn)


@BlClassRegistry(legacy=True)
class Preferences(AddonPreferences):
    """Preferences class: Preferences for this add-on"""

    bl_idname = "uv_magic_uv"

    def update_enable_builtin_menu(self, _):
        if self['enable_builtin_menu']:
            add_builtin_menu()
        else:
            remove_builtin_menu()

    # enable to add features to built-in menu
    enable_builtin_menu = BoolProperty(
        name="Built-in Menu",
        description="Enable built-in menu",
        default=True,
        update=update_enable_builtin_menu
    )

    # for UV Sculpt
    uv_sculpt_brush_color = FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0, 0.4, 0.4, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # for Overlapped UV
    uv_inspection_overlapped_color = FloatVectorProperty(
        name="Color",
        description="Color",
        default=(0.0, 0.0, 1.0, 0.3),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # for Flipped UV
    uv_inspection_flipped_color = FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0, 0.0, 0.0, 0.3),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # for Texture Projection
    texture_projection_canvas_padding = FloatVectorProperty(
        name="Canvas Padding",
        description="Canvas Padding",
        size=2,
        max=50.0,
        min=0.0,
        default=(20.0, 20.0))

    # for UV Bounding Box
    uv_bounding_box_cp_size = FloatProperty(
        name="Size",
        description="Control Point Size",
        default=6.0,
        min=3.0,
        max=100.0)
    uv_bounding_box_cp_react_size = FloatProperty(
        name="React Size",
        description="Size event fired",
        default=10.0,
        min=3.0,
        max=100.0)

    # for UI
    category = EnumProperty(
        name="Category",
        description="Preferences Category",
        items=[
            ('INFO', "Information", "Information about this add-on"),
            ('CONFIG', "Configuration", "Configuration about this add-on"),
            ('UPDATE', "Update", "Update this add-on"),
        ],
        default='INFO'
    )
    info_desc_expanded = BoolProperty(
        name="Description",
        description="Description",
        default=False
    )
    info_loc_expanded = BoolProperty(
        name="Location",
        description="Location",
        default=False
    )
    conf_uv_sculpt_expanded = BoolProperty(
        name="UV Sculpt",
        description="UV Sculpt",
        default=False
    )
    conf_uv_inspection_expanded = BoolProperty(
        name="UV Inspection",
        description="UV Inspection",
        default=False
    )
    conf_texture_projection_expanded = BoolProperty(
        name="Texture Projection",
        description="Texture Projection",
        default=False
    )
    conf_uv_bounding_box_expanded = BoolProperty(
        name="UV Bounding Box",
        description="UV Bounding Box",
        default=False
    )

    # for add-on updater
    auto_check_update = BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False
    )
    updater_intrval_months = IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days = IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0
    )
    updater_intrval_hours = IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes = IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        layout = self.layout

        layout.row().prop(self, "category", expand=True)

        if self.category == 'INFO':
            layout.prop(
                self, "info_desc_expanded", text="Description",
                icon='DISCLOSURE_TRI_DOWN' if self.info_desc_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.info_desc_expanded:
                column = layout.column(align=True)
                column.label("Magic UV is composed of many UV editing" +
                             " features.")
                column.label("See tutorial page if you are new to this" +
                             " add-on.")
                column.label("https://github.com/nutti/Magic-UV/wiki/Tutorial")

            layout.prop(
                self, "info_loc_expanded", text="Location",
                icon='DISCLOSURE_TRI_DOWN' if self.info_loc_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.info_loc_expanded:
                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("3D View > Tool shelf > Copy/Paste UV (Object mode)")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Copy/Paste UV (Among objects)")

                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("3D View > Tool shelf > Copy/Paste UV (Edit mode)")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Copy/Paste UV (Among faces in 3D View)")
                col.label("Transfer UV")

                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("3D View > Tool shelf > UV Manipulation (Edit mode)")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Flip/Rotate UV")
                col.label("Mirror UV")
                col.label("Move UV")
                col.label("World Scale UV")
                col.label("Preserve UV Aspect")
                col.label("Texture Lock")
                col.label("Texture Wrap")
                col.label("UV Sculpt")

                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("3D View > Tool shelf > UV Manipulation (Edit mode)")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Unwrap Constraint")
                col.label("Texture Projection")
                col.label("UVW")

                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("UV/Image Editor > Tool shelf > Copy/Paste UV")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Copy/Paste UV (Among faces in UV/Image Editor)")

                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("UV/Image Editor > Tool shelf > UV Manipulation")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Align UV")
                col.label("Smooth UV")
                col.label("Select UV")
                col.label("Pack UV (Extension)")

                row = layout.row(align=True)
                sp = row.split(percentage=0.5)
                sp.label("UV/Image Editor > Tool shelf > Editor Enhancement")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("Align UV Cursor")
                col.label("UV Cursor Location")
                col.label("UV Bounding Box")
                col.label("UV Inspection")

        elif self.category == 'CONFIG':
            layout.prop(self, "enable_builtin_menu", text="Built-in Menu")

            layout.separator()

            layout.prop(
                self, "conf_uv_sculpt_expanded", text="UV Sculpt",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_uv_sculpt_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_sculpt_expanded:
                sp = layout.split(percentage=0.05)
                col = sp.column()  # spacer
                sp = sp.split(percentage=0.3)
                col = sp.column()
                col.label("Brush Color:")
                col.prop(self, "uv_sculpt_brush_color", text="")
                layout.separator()

            layout.prop(
                self, "conf_uv_inspection_expanded", text="UV Inspection",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_uv_inspection_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_inspection_expanded:
                sp = layout.split(percentage=0.05)
                col = sp.column()  # spacer
                sp = sp.split(percentage=0.3)
                col = sp.column()
                col.label("Overlapped UV Color:")
                col.prop(self, "uv_inspection_overlapped_color", text="")
                sp = sp.split(percentage=0.45)
                col = sp.column()
                col.label("Flipped UV Color:")
                col.prop(self, "uv_inspection_flipped_color", text="")
                layout.separator()

            layout.prop(
                self, "conf_texture_projection_expanded",
                text="Texture Projection",
                icon='DISCLOSURE_TRI_DOWN'
                if self.conf_texture_projection_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_texture_projection_expanded:
                sp = layout.split(percentage=0.05)
                col = sp.column()       # spacer
                sp = sp.split(percentage=0.3)
                col = sp.column()
                col.prop(self, "texture_projection_canvas_padding")
                layout.separator()

            layout.prop(
                self, "conf_uv_bounding_box_expanded", text="UV Bounding Box",
                icon='DISCLOSURE_TRI_DOWN'
                if self.conf_uv_bounding_box_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_bounding_box_expanded:
                sp = layout.split(percentage=0.05)
                col = sp.column()       # spacer
                sp = sp.split(percentage=0.3)
                col = sp.column()
                col.label("Control Point:")
                col.prop(self, "uv_bounding_box_cp_size")
                col.prop(self, "uv_bounding_box_cp_react_size")
                layout.separator()

        elif self.category == 'UPDATE':
            addon_updater_ops.update_settings_ui(self, context)
