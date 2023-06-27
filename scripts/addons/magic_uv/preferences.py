# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    EnumProperty,
)
from bpy.types import AddonPreferences

from . import common
from .op.clip_uv import MUV_OT_ClipUV
from .op.flip_rotate_uv import MUV_OT_FlipRotateUV
from .op.mirror_uv import MUV_OT_MirrorUV
from .op.move_uv import MUV_OT_MoveUV
from .op.unwrap_constraint import MUV_OT_UnwrapConstraint
from .op.pack_uv import MUV_OT_PackUV
from .op.smooth_uv import MUV_OT_SmoothUV
from .ui.VIEW3D_MT_uv_map import (
    MUV_MT_CopyPasteUV,
    MUV_MT_TransferUV,
    MUV_MT_WorldScaleUV,
    MUV_MT_PreserveUVAspect,
    MUV_MT_TextureLock,
    MUV_MT_TextureWrap,
    MUV_MT_TextureProjection,
    MUV_MT_UVW,
)
from .ui.VIEW3D_MT_object import MUV_MT_CopyPasteUV_Object
from .ui.IMAGE_MT_uvs import (
    MUV_MT_CopyPasteUV_UVEdit,
    MUV_MT_SelectUV,
    MUV_MT_AlignUV,
    MUV_MT_AlignUVCursor,
    MUV_MT_UVInspection,
)
from .utils.bl_class_registry import BlClassRegistry
from .utils import compatibility as compat


def view3d_uvmap_menu_fn(self, context):
    layout = self.layout
    sc = context.scene

    layout.separator()
    layout.label(text="Copy/Paste UV", icon=compat.icon('IMAGE'))
    # Copy/Paste UV
    layout.menu(MUV_MT_CopyPasteUV.bl_idname, text="Copy/Paste UV")
    # Transfer UV
    layout.menu(MUV_MT_TransferUV.bl_idname, text="Transfer UV")

    layout.separator()
    layout.label(text="UV Manipulation", icon=compat.icon('IMAGE'))
    # Flip/Rotate UV
    ops = layout.operator(MUV_OT_FlipRotateUV.bl_idname, text="Flip/Rotate UV")
    ops.seams = sc.muv_flip_rotate_uv_seams
    # Mirror UV
    ops = layout.operator(MUV_OT_MirrorUV.bl_idname, text="Mirror UV")
    ops.axis = sc.muv_mirror_uv_axis
    # Move UV
    layout.operator(MUV_OT_MoveUV.bl_idname, text="Move UV")
    # World Scale UV
    layout.menu(MUV_MT_WorldScaleUV.bl_idname, text="World Scale UV")
    # Preserve UV
    layout.menu(MUV_MT_PreserveUVAspect.bl_idname, text="Preserve UV")
    # Texture Lock
    layout.menu(MUV_MT_TextureLock.bl_idname, text="Texture Lock")
    # Texture Wrap
    layout.menu(MUV_MT_TextureWrap.bl_idname, text="Texture Wrap")
    # UV Sculpt
    layout.prop(sc, "muv_uv_sculpt_enable", text="UV Sculpt")

    layout.separator()
    layout.label(text="UV Mapping", icon=compat.icon('IMAGE'))
    # Unwrap Constraint
    ops = layout.operator(MUV_OT_UnwrapConstraint.bl_idname,
                          text="Unwrap Constraint")
    ops.u_const = sc.muv_unwrap_constraint_u_const
    ops.v_const = sc.muv_unwrap_constraint_v_const
    # Texture Projection
    layout.menu(MUV_MT_TextureProjection.bl_idname, text="Texture Projection")
    # UVW
    layout.menu(MUV_MT_UVW.bl_idname, text="UVW")


def view3d_object_menu_fn(self, _):
    layout = self.layout

    layout.separator()
    layout.label(text="Copy/Paste UV", icon=compat.icon('IMAGE'))
    # Copy/Paste UV (Among Object)
    layout.menu(MUV_MT_CopyPasteUV_Object.bl_idname, text="Copy/Paste UV")


def image_uvs_menu_fn(self, context):
    layout = self.layout
    sc = context.scene

    layout.separator()
    layout.label(text="Copy/Paste UV", icon=compat.icon('IMAGE'))
    # Copy/Paste UV (on UV/Image Editor)
    layout.menu(MUV_MT_CopyPasteUV_UVEdit.bl_idname, text="Copy/Paste UV")

    layout.separator()
    layout.label(text="UV Manipulation", icon=compat.icon('IMAGE'))
    # Clip UV
    ops = layout.operator(MUV_OT_ClipUV.bl_idname, text="Clip UV")
    ops.clip_uv_range_max = sc.muv_clip_uv_range_max
    ops.clip_uv_range_min = sc.muv_clip_uv_range_min
    # Pack UV
    ops = layout.operator(MUV_OT_PackUV.bl_idname, text="Pack UV")
    ops.allowable_center_deviation = sc.muv_pack_uv_allowable_center_deviation
    ops.allowable_size_deviation = sc.muv_pack_uv_allowable_size_deviation
    ops.accurate_island_copy = sc.muv_pack_uv_accurate_island_copy
    ops.stride = sc.muv_pack_uv_stride
    ops.apply_pack_uv = sc.muv_pack_uv_apply_pack_uv
    # Select UV
    layout.menu(MUV_MT_SelectUV.bl_idname, text="Select UV")
    # Smooth UV
    ops = layout.operator(MUV_OT_SmoothUV.bl_idname, text="Smooth")
    ops.transmission = sc.muv_smooth_uv_transmission
    ops.select = sc.muv_smooth_uv_select
    ops.mesh_infl = sc.muv_smooth_uv_mesh_infl
    # Align UV
    layout.menu(MUV_MT_AlignUV.bl_idname, text="Align UV")

    layout.separator()
    layout.label(text="Editor Enhancement", icon=compat.icon('IMAGE'))
    # Align UV Cursor
    layout.menu(MUV_MT_AlignUVCursor.bl_idname, text="Align UV Cursor")
    # UV Bounding Box
    layout.prop(sc, "muv_uv_bounding_box_show", text="UV Bounding Box")
    # UV Inspection
    layout.menu(MUV_MT_UVInspection.bl_idname, text="UV Inspection")


def add_builtin_menu():
    bpy.types.VIEW3D_MT_uv_map.append(view3d_uvmap_menu_fn)
    bpy.types.VIEW3D_MT_object.append(view3d_object_menu_fn)
    bpy.types.IMAGE_MT_uvs.append(image_uvs_menu_fn)


def remove_builtin_menu():
    bpy.types.IMAGE_MT_uvs.remove(image_uvs_menu_fn)
    bpy.types.VIEW3D_MT_object.remove(view3d_object_menu_fn)
    bpy.types.VIEW3D_MT_uv_map.remove(view3d_uvmap_menu_fn)


def set_debug_mode(self, value):
    self['enable_debug_mode'] = value


def get_debug_mode(self):
    enabled = self.get('enable_debug_mode', False)
    if enabled:
        common.enable_debugg_mode()
    else:
        common.disable_debug_mode()
    return enabled


@BlClassRegistry()
@compat.make_annotations
class MUV_Preferences(AddonPreferences):
    """Preferences class: Preferences for this add-on"""

    bl_idname = "magic_uv"

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
        update=update_enable_builtin_menu,
    )

    # enable debug mode
    enable_debug_mode = BoolProperty(
        name="Debug Mode",
        description="Enable debugging mode",
        default=False,
        set=set_debug_mode,
        get=get_debug_mode,
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
    uv_inspection_overlapped_color_for_v3d = FloatVectorProperty(
        name="Color (View3D)",
        description="Color in View3D",
        default=(0.0, 0.0, 1.0, 0.5),
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
    uv_inspection_flipped_color_for_v3d = FloatVectorProperty(
        name="Color (View3D)",
        description="Color in View3D",
        default=(1.0, 0.0, 0.0, 0.5),
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

    def draw(self, _):
        layout = self.layout

        layout.row().prop(self, "category", expand=True)

        if self.category == 'INFO':
            layout.separator()

            layout.prop(
                self, "info_desc_expanded", text="Description",
                icon='DISCLOSURE_TRI_DOWN' if self.info_desc_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.info_desc_expanded:
                col = layout.column(align=True)
                col.label(text="Magic UV is composed of many UV editing" +
                          " features.")
                col.label(text="See tutorial page if you are new to this" +
                          " add-on.")
                col.label(text="https://github.com/nutti/Magic-UV" +
                          "/wiki/Tutorial")

            layout.prop(
                self, "info_loc_expanded", text="Location",
                icon='DISCLOSURE_TRI_DOWN' if self.info_loc_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.info_loc_expanded:
                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="3D View > Sidebar > " +
                         "Copy/Paste UV (Object mode)")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Copy/Paste UV (Among objects)")

                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="3D View > Sidebar > " +
                         "Copy/Paste UV (Edit mode)")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Copy/Paste UV (Among faces in 3D View)")
                col.label(text="Transfer UV")

                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="3D View > Sidebar > " +
                         "UV Manipulation (Edit mode)")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Flip/Rotate UV")
                col.label(text="Mirror UV")
                col.label(text="Move UV")
                col.label(text="World Scale UV")
                col.label(text="Preserve UV Aspect")
                col.label(text="Texture Lock")
                col.label(text="Texture Wrap")
                col.label(text="UV Sculpt")

                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="3D View > Sidebar > " +
                         "UV Manipulation (Edit mode)")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Unwrap Constraint")
                col.label(text="Texture Projection")
                col.label(text="UVW")

                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="UV/Image Editor > Sidebar > Copy/Paste UV")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Copy/Paste UV " +
                          "(Among faces in UV/Image Editor)")

                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="UV/Image Editor > Sidebar > UV Manipulation")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Align UV")
                col.label(text="Smooth UV")
                col.label(text="Select UV")
                col.label(text="Pack UV (Extension)")

                row = layout.row(align=True)
                sp = compat.layout_split(row, 0.5)
                sp.label(text="UV/Image Editor > Sidebar > " +
                         "Editor Enhancement")
                sp = compat.layout_split(sp, 1.0)
                col = sp.column(align=True)
                col.label(text="Align UV Cursor")
                col.label(text="UV Cursor Location")
                col.label(text="UV Bounding Box")
                col.label(text="UV Inspection")

        elif self.category == 'CONFIG':
            layout.separator()

            layout.prop(self, "enable_builtin_menu", text="Built-in Menu")
            layout.prop(self, "enable_debug_mode", text="Debug Mode")

            layout.separator()

            layout.prop(
                self, "conf_uv_sculpt_expanded", text="UV Sculpt",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_uv_sculpt_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_sculpt_expanded:
                sp = compat.layout_split(layout, 0.05)
                col = sp.column()  # spacer
                sp = compat.layout_split(sp, 0.3)
                col = sp.column()
                col.label(text="Brush Color:")
                col.prop(self, "uv_sculpt_brush_color", text="")
                layout.separator()

            layout.prop(
                self, "conf_uv_inspection_expanded", text="UV Inspection",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_uv_inspection_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_inspection_expanded:
                sp = compat.layout_split(layout, 0.05)
                col = sp.column()  # spacer
                sp = compat.layout_split(sp, 0.3)
                col = sp.column()
                col.label(text="Overlapped UV Color:")
                col.prop(self, "uv_inspection_overlapped_color", text="")
                sp = compat.layout_split(sp, 0.45)
                col = sp.column()
                col.label(text="Flipped UV Color:")
                col.prop(self, "uv_inspection_flipped_color", text="")

                sp = compat.layout_split(layout, 0.05)
                col = sp.column()  # spacer
                sp = compat.layout_split(sp, 0.3)
                col = sp.column()
                col.label(text="Overlapped UV Color (View3D):")
                col.prop(self, "uv_inspection_overlapped_color_for_v3d",
                         text="")
                sp = compat.layout_split(sp, 0.45)
                col = sp.column()
                col.label(text="Flipped UV Color (View3D):")
                col.prop(self, "uv_inspection_flipped_color_for_v3d",
                         text="")

                layout.separator()

            layout.prop(
                self, "conf_texture_projection_expanded",
                text="Texture Projection",
                icon='DISCLOSURE_TRI_DOWN'
                if self.conf_texture_projection_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_texture_projection_expanded:
                sp = compat.layout_split(layout, 0.05)
                col = sp.column()       # spacer
                sp = compat.layout_split(sp, 0.3)
                col = sp.column()
                col.prop(self, "texture_projection_canvas_padding")
                layout.separator()

            layout.prop(
                self, "conf_uv_bounding_box_expanded", text="UV Bounding Box",
                icon='DISCLOSURE_TRI_DOWN'
                if self.conf_uv_bounding_box_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_bounding_box_expanded:
                sp = compat.layout_split(layout, 0.05)
                col = sp.column()       # spacer
                sp = compat.layout_split(sp, 0.3)
                col = sp.column()
                col.label(text="Control Point:")
                col.prop(self, "uv_bounding_box_cp_size")
                col.prop(self, "uv_bounding_box_cp_react_size")
                layout.separator()
