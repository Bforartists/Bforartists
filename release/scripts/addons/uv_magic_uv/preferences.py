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
    StringProperty,
)
from bpy.types import AddonPreferences

from . import op
from . import ui
from .utils.bl_class_registry import BlClassRegistry
from .utils.addon_updator import AddonUpdatorManager


def view3d_uvmap_menu_fn(self, context):
    layout = self.layout
    sc = context.scene

    layout.separator()
    layout.label(text="Copy/Paste UV", icon='IMAGE')
    # Copy/Paste UV
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_CopyPasteUV.bl_idname,
                text="Copy/Paste UV")
    # Transfer UV
    layout.menu(ui.VIEW3D_MT_uv_map.MUV_MT_TransferUV.bl_idname,
                text="Transfer UV")

    layout.separator()
    layout.label(text="UV Manipulation", icon='IMAGE')
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
    layout.label(text="UV Mapping", icon='IMAGE')
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
    layout.label(text="Copy/Paste UV", icon='IMAGE')
    # Copy/Paste UV (Among Object)
    layout.menu(ui.VIEW3D_MT_object.MUV_MT_CopyPasteUV_Object.bl_idname,
                text="Copy/Paste UV")


def image_uvs_menu_fn(self, context):
    layout = self.layout
    sc = context.scene

    layout.separator()
    # Copy/Paste UV (on UV/Image Editor)
    layout.label(text="Copy/Paste UV", icon='IMAGE')
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_CopyPasteUV_UVEdit.bl_idname,
                text="Copy/Paste UV")

    layout.separator()
    # Pack UV
    layout.label(text="UV Manipulation", icon='IMAGE')
    ops = layout.operator(op.pack_uv.MUV_OT_PackUV.bl_idname, text="Pack UV")
    ops.allowable_center_deviation = sc.muv_pack_uv_allowable_center_deviation
    ops.allowable_size_deviation = sc.muv_pack_uv_allowable_size_deviation
    # Select UV
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_SelectUV.bl_idname, text="Select UV")
    # Smooth UV
    ops = layout.operator(op.smooth_uv.MUV_OT_SmoothUV.bl_idname,
                          text="Smooth")
    ops.transmission = sc.muv_smooth_uv_transmission
    ops.select = sc.muv_smooth_uv_select
    ops.mesh_infl = sc.muv_smooth_uv_mesh_infl
    # Align UV
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_AlignUV.bl_idname, text="Align UV")

    layout.separator()
    # Align UV Cursor
    layout.label(text="Editor Enhancement", icon='IMAGE')
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_AlignUVCursor.bl_idname,
                text="Align UV Cursor")
    # UV Bounding Box
    layout.prop(sc, "muv_uv_bounding_box_show", text="UV Bounding Box")
    # UV Inspection
    layout.menu(ui.IMAGE_MT_uvs.MUV_MT_UVInspection.bl_idname,
                text="UV Inspection")


def add_builtin_menu():
    bpy.types.VIEW3D_MT_uv_map.append(view3d_uvmap_menu_fn)
    bpy.types.VIEW3D_MT_object.append(view3d_object_menu_fn)
    bpy.types.IMAGE_MT_uvs.append(image_uvs_menu_fn)


def remove_builtin_menu():
    bpy.types.IMAGE_MT_uvs.remove(image_uvs_menu_fn)
    bpy.types.VIEW3D_MT_object.append(view3d_object_menu_fn)
    bpy.types.VIEW3D_MT_uv_map.remove(view3d_uvmap_menu_fn)


@BlClassRegistry()
class MUV_OT_CheckAddonUpdate(bpy.types.Operator):
    bl_idname = "uv.muv_check_addon_update"
    bl_label = "Check Update"
    bl_description = "Check Add-on Update"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        updater = AddonUpdatorManager.get_instance()
        updater.check_update_candidate()

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_UpdateAddon(bpy.types.Operator):
    bl_idname = "uv.muv_update_addon"
    bl_label = "Update"
    bl_description = "Update Add-on"
    bl_options = {'REGISTER', 'UNDO'}

    branch_name: StringProperty(
        name="Branch Name",
        description="Branch name to update",
        default="",
    )

    def execute(self, context):
        updater = AddonUpdatorManager.get_instance()
        updater.update(self.branch_name)

        return {'FINISHED'}


def get_update_candidate_branches(_, __):
    updater = AddonUpdatorManager.get_instance()
    if not updater.candidate_checked():
        return []

    return [(name, name, "") for name in updater.get_candidate_branch_names()]


@BlClassRegistry()
class Preferences(AddonPreferences):
    """Preferences class: Preferences for this add-on"""

    bl_idname = "uv_magic_uv"

    def update_enable_builtin_menu(self, _):
        if self['enable_builtin_menu']:
            add_builtin_menu()
        else:
            remove_builtin_menu()

    # enable to add features to built-in menu
    enable_builtin_menu: BoolProperty(
        name="Built-in Menu",
        description="Enable built-in menu",
        default=True,
        update=update_enable_builtin_menu,
    )

    # for UV Sculpt
    uv_sculpt_brush_color: FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0, 0.4, 0.4, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # for Overlapped UV
    uv_inspection_overlapped_color: FloatVectorProperty(
        name="Color",
        description="Color",
        default=(0.0, 0.0, 1.0, 0.3),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # for Flipped UV
    uv_inspection_flipped_color: FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0, 0.0, 0.0, 0.3),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    # for Texture Projection
    texture_projection_canvas_padding: FloatVectorProperty(
        name="Canvas Padding",
        description="Canvas Padding",
        size=2,
        max=50.0,
        min=0.0,
        default=(20.0, 20.0))

    # for UV Bounding Box
    uv_bounding_box_cp_size: FloatProperty(
        name="Size",
        description="Control Point Size",
        default=6.0,
        min=3.0,
        max=100.0)
    uv_bounding_box_cp_react_size: FloatProperty(
        name="React Size",
        description="Size event fired",
        default=10.0,
        min=3.0,
        max=100.0)

    # for UI
    category: EnumProperty(
        name="Category",
        description="Preferences Category",
        items=[
            ('INFO', "Information", "Information about this add-on"),
            ('CONFIG', "Configuration", "Configuration about this add-on"),
            ('UPDATE', "Update", "Update this add-on"),
        ],
        default='INFO'
    )
    info_desc_expanded: BoolProperty(
        name="Description",
        description="Description",
        default=False
    )
    info_loc_expanded: BoolProperty(
        name="Location",
        description="Location",
        default=False
    )
    conf_uv_sculpt_expanded: BoolProperty(
        name="UV Sculpt",
        description="UV Sculpt",
        default=False
    )
    conf_uv_inspection_expanded: BoolProperty(
        name="UV Inspection",
        description="UV Inspection",
        default=False
    )
    conf_texture_projection_expanded: BoolProperty(
        name="Texture Projection",
        description="Texture Projection",
        default=False
    )
    conf_uv_bounding_box_expanded: BoolProperty(
        name="UV Bounding Box",
        description="UV Bounding Box",
        default=False
    )

    # for add-on updater
    updater_branch_to_update: EnumProperty(
        name="branch",
        description="Target branch to update add-on",
        items=get_update_candidate_branches
    )

    def draw(self, context):
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
                sp = row.split(factor=0.5)
                sp.label(text="3D View > Tool shelf > " +
                              "Copy/Paste UV (Object mode)")
                sp = sp.split(factor=1.0)
                col = sp.column(align=True)
                col.label(text="Copy/Paste UV (Among objects)")

                row = layout.row(align=True)
                sp = row.split(factor=0.5)
                sp.label(text="3D View > Tool shelf > " +
                              "Copy/Paste UV (Edit mode)")
                sp = sp.split(factor=1.0)
                col = sp.column(align=True)
                col.label(text="Copy/Paste UV (Among faces in 3D View)")
                col.label(text="Transfer UV")

                row = layout.row(align=True)
                sp = row.split(factor=0.5)
                sp.label(text="3D View > Tool shelf > " +
                              "UV Manipulation (Edit mode)")
                sp = sp.split(factor=1.0)
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
                sp = row.split(factor=0.5)
                sp.label(text="3D View > Tool shelf > " +
                              "UV Manipulation (Edit mode)")
                sp = sp.split(factor=1.0)
                col = sp.column(align=True)
                col.label(text="Unwrap Constraint")
                col.label(text="Texture Projection")
                col.label(text="UVW")

                row = layout.row(align=True)
                sp = row.split(factor=0.5)
                sp.label(text="UV/Image Editor > Tool shelf > Copy/Paste UV")
                sp = sp.split(factor=1.0)
                col = sp.column(align=True)
                col.label(text="Copy/Paste UV (Among faces in UV/Image Editor)")

                row = layout.row(align=True)
                sp = row.split(factor=0.5)
                sp.label(text="UV/Image Editor > Tool shelf > UV Manipulation")
                sp = sp.split(factor=1.0)
                col = sp.column(align=True)
                col.label(text="Align UV")
                col.label(text="Smooth UV")
                col.label(text="Select UV")
                col.label(text="Pack UV (Extension)")

                row = layout.row(align=True)
                sp = row.split(factor=0.5)
                sp.label(text="UV/Image Editor > Tool shelf > " +
                              "Editor Enhancement")
                sp = sp.split(factor=1.0)
                col = sp.column(align=True)
                col.label(text="Align UV Cursor")
                col.label(text="UV Cursor Location")
                col.label(text="UV Bounding Box")
                col.label(text="UV Inspection")

        elif self.category == 'CONFIG':
            layout.separator()

            layout.prop(self, "enable_builtin_menu", text="Built-in Menu")

            layout.separator()

            layout.prop(
                self, "conf_uv_sculpt_expanded", text="UV Sculpt",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_uv_sculpt_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_sculpt_expanded:
                sp = layout.split(factor=0.05)
                col = sp.column()  # spacer
                sp = sp.split(factor=0.3)
                col = sp.column()
                col.label(text="Brush Color:")
                col.prop(self, "uv_sculpt_brush_color", text="")
                layout.separator()

            layout.prop(
                self, "conf_uv_inspection_expanded", text="UV Inspection",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_uv_inspection_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_inspection_expanded:
                sp = layout.split(factor=0.05)
                col = sp.column()  # spacer
                sp = sp.split(factor=0.3)
                col = sp.column()
                col.label(text="Overlapped UV Color:")
                col.prop(self, "uv_inspection_overlapped_color", text="")
                sp = sp.split(factor=0.45)
                col = sp.column()
                col.label(text="Flipped UV Color:")
                col.prop(self, "uv_inspection_flipped_color", text="")
                layout.separator()

            layout.prop(
                self, "conf_texture_projection_expanded",
                text="Texture Projection",
                icon='DISCLOSURE_TRI_DOWN'
                if self.conf_texture_projection_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_texture_projection_expanded:
                sp = layout.split(factor=0.05)
                col = sp.column()       # spacer
                sp = sp.split(factor=0.3)
                col = sp.column()
                col.prop(self, "texture_projection_canvas_padding")
                layout.separator()

            layout.prop(
                self, "conf_uv_bounding_box_expanded", text="UV Bounding Box",
                icon='DISCLOSURE_TRI_DOWN'
                if self.conf_uv_bounding_box_expanded
                else 'DISCLOSURE_TRI_RIGHT')
            if self.conf_uv_bounding_box_expanded:
                sp = layout.split(factor=0.05)
                col = sp.column()       # spacer
                sp = sp.split(factor=0.3)
                col = sp.column()
                col.label(text="Control Point:")
                col.prop(self, "uv_bounding_box_cp_size")
                col.prop(self, "uv_bounding_box_cp_react_size")
                layout.separator()

        elif self.category == 'UPDATE':
            updater = AddonUpdatorManager.get_instance()

            layout.separator()

            if not updater.candidate_checked():
                col = layout.column()
                col.scale_y = 2
                row = col.row()
                row.operator(MUV_OT_CheckAddonUpdate.bl_idname,
                             text="Check 'Magic UV' add-on update",
                             icon='FILE_REFRESH')
            else:
                row = layout.row(align=True)
                row.scale_y = 2
                col = row.column()
                col.operator(MUV_OT_CheckAddonUpdate.bl_idname,
                             text="Check 'Magic UV' add-on update",
                             icon='FILE_REFRESH')
                col = row.column()
                if updater.latest_version() != "":
                    col.enabled = True
                    ops = col.operator(
                        MUV_OT_UpdateAddon.bl_idname,
                        text="Update to the latest release version (version: {})"
                             .format(updater.latest_version()),
                        icon='TRIA_DOWN_BAR')
                    ops.branch_name = updater.latest_version()
                else:
                    col.enabled = False
                    col.operator(MUV_OT_UpdateAddon.bl_idname,
                                text="No updates are available.")

                layout.separator()
                layout.label(text="Manual Update:")
                row = layout.row(align=True)
                row.prop(self, "updater_branch_to_update", text="Target")
                ops = row.operator(
                    MUV_OT_UpdateAddon.bl_idname, text="Update",
                    icon='TRIA_DOWN_BAR')
                ops.branch_name = self.updater_branch_to_update

                layout.separator()
                if updater.has_error():
                    box = layout.box()
                    box.label(text=updater.error(), icon='CANCEL')
                elif updater.has_info():
                    box = layout.box()
                    box.label(text=updater.info(), icon='ERROR')
