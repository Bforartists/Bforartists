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

from ..op import (
    move_uv,
    flip_rotate_uv,
    mirror_uv,
    preserve_uv_aspect,
    texture_lock,
    texture_wrap,
    uv_sculpt,
    world_scale_uv,
)
from ..op.world_scale_uv import (
    MUV_OT_WorldScaleUV_ApplyProportionalToMesh,
    MUV_OT_WorldScaleUV_ApplyScalingDensity
)
from ...utils.bl_class_registry import BlClassRegistry

__all__ = [
    'MUV_PT_View3D_UVManipulation',
]


@BlClassRegistry(legacy=True)
class MUV_PT_View3D_UVManipulation(bpy.types.Panel):
    """
    Panel class: UV Manipulation on Property Panel on View3D
    """

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "UV Manipulation"
    bl_category = "Magic UV"
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='IMAGE_COL')

    def draw(self, context):
        sc = context.scene
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_flip_rotate_uv_enabled", text="Flip/Rotate UV")
        if sc.muv_flip_rotate_uv_enabled:
            row = box.row()
            ops = row.operator(flip_rotate_uv.MUV_OT_FlipRotate.bl_idname,
                               text="Flip/Rotate")
            ops.seams = sc.muv_flip_rotate_uv_seams
            row.prop(sc, "muv_flip_rotate_uv_seams", text="Seams")

        box = layout.box()
        box.prop(sc, "muv_mirror_uv_enabled", text="Mirror UV")
        if sc.muv_mirror_uv_enabled:
            row = box.row()
            ops = row.operator(mirror_uv.MUV_OT_MirrorUV.bl_idname,
                               text="Mirror")
            ops.axis = sc.muv_mirror_uv_axis
            row.prop(sc, "muv_mirror_uv_axis", text="")

        box = layout.box()
        box.prop(sc, "muv_move_uv_enabled", text="Move UV")
        if sc.muv_move_uv_enabled:
            col = box.column()
            if not move_uv.MUV_OT_MoveUV.is_running(context):
                col.operator(move_uv.MUV_OT_MoveUV.bl_idname, icon='PLAY',
                             text="Start")
            else:
                col.operator(move_uv.MUV_OT_MoveUV.bl_idname, icon='PAUSE',
                             text="Stop")

        box = layout.box()
        box.prop(sc, "muv_world_scale_uv_enabled", text="World Scale UV")
        if sc.muv_world_scale_uv_enabled:
            box.prop(sc, "muv_world_scale_uv_mode", text="")

            if sc.muv_world_scale_uv_mode == 'MANUAL':
                sp = box.split(percentage=0.5)
                col = sp.column()
                col.prop(sc, "muv_world_scale_uv_tgt_texture_size",
                         text="Texture Size")
                sp = sp.split(percentage=1.0)
                col = sp.column()
                col.label("Density:")
                col.prop(sc, "muv_world_scale_uv_tgt_density", text="")
                box.prop(sc, "muv_world_scale_uv_origin", text="Origin")
                ops = box.operator(
                    world_scale_uv.MUV_OT_WorldScaleUV_ApplyManual.bl_idname,
                    text="Apply")
                ops.tgt_density = sc.muv_world_scale_uv_tgt_density
                ops.tgt_texture_size = sc.muv_world_scale_uv_tgt_texture_size
                ops.origin = sc.muv_world_scale_uv_origin
                ops.show_dialog = False

            elif sc.muv_world_scale_uv_mode == 'SAME_DENSITY':
                sp = box.split(percentage=0.4)
                col = sp.column(align=True)
                col.label("Source:")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.operator(
                    world_scale_uv.MUV_OT_WorldScaleUV_Measure.bl_idname,
                    text="Measure")

                sp = box.split(percentage=0.7)
                col = sp.column(align=True)
                col.prop(sc, "muv_world_scale_uv_src_density", text="Density")
                col.enabled = False
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("px2/cm2")

                box.separator()
                box.prop(sc, "muv_world_scale_uv_origin", text="Origin")
                ops = box.operator(
                    MUV_OT_WorldScaleUV_ApplyScalingDensity.bl_idname,
                    text="Apply")
                ops.src_density = sc.muv_world_scale_uv_src_density
                ops.origin = sc.muv_world_scale_uv_origin
                ops.same_density = True
                ops.show_dialog = False

            elif sc.muv_world_scale_uv_mode == 'SCALING_DENSITY':
                sp = box.split(percentage=0.4)
                col = sp.column(align=True)
                col.label("Source:")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.operator(
                    world_scale_uv.MUV_OT_WorldScaleUV_Measure.bl_idname,
                    text="Measure")

                sp = box.split(percentage=0.7)
                col = sp.column(align=True)
                col.prop(sc, "muv_world_scale_uv_src_density", text="Density")
                col.enabled = False
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("px2/cm2")

                box.separator()
                box.prop(sc, "muv_world_scale_uv_tgt_scaling_factor",
                         text="Scaling Factor")
                box.prop(sc, "muv_world_scale_uv_origin", text="Origin")
                ops = box.operator(
                    MUV_OT_WorldScaleUV_ApplyScalingDensity.bl_idname,
                    text="Apply")
                ops.src_density = sc.muv_world_scale_uv_src_density
                ops.origin = sc.muv_world_scale_uv_origin
                ops.same_density = False
                ops.show_dialog = False
                ops.tgt_scaling_factor = \
                    sc.muv_world_scale_uv_tgt_scaling_factor

            elif sc.muv_world_scale_uv_mode == 'PROPORTIONAL_TO_MESH':
                sp = box.split(percentage=0.4)
                col = sp.column(align=True)
                col.label("Source:")
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.operator(
                    world_scale_uv.MUV_OT_WorldScaleUV_Measure.bl_idname,
                    text="Measure")

                sp = box.split(percentage=0.7)
                col = sp.column(align=True)
                col.prop(sc, "muv_world_scale_uv_src_mesh_area",
                         text="Mesh Area")
                col.prop(sc, "muv_world_scale_uv_src_uv_area", text="UV Area")
                col.prop(sc, "muv_world_scale_uv_src_density", text="Density")
                col.enabled = False
                sp = sp.split(percentage=1.0)
                col = sp.column(align=True)
                col.label("cm2")
                col.label("px2")
                col.label("px2/cm2")
                col.enabled = False

                box.separator()
                box.prop(sc, "muv_world_scale_uv_origin", text="Origin")
                ops = box.operator(
                    MUV_OT_WorldScaleUV_ApplyProportionalToMesh.bl_idname,
                    text="Apply")
                ops.src_density = sc.muv_world_scale_uv_src_density
                ops.src_uv_area = sc.muv_world_scale_uv_src_uv_area
                ops.src_mesh_area = sc.muv_world_scale_uv_src_mesh_area
                ops.origin = sc.muv_world_scale_uv_origin
                ops.show_dialog = False

        box = layout.box()
        box.prop(sc, "muv_preserve_uv_aspect_enabled",
                 text="Preserve UV Aspect")
        if sc.muv_preserve_uv_aspect_enabled:
            row = box.row()
            ops = row.operator(
                preserve_uv_aspect.MUV_OT_PreserveUVAspect.bl_idname,
                text="Change Image")
            ops.dest_img_name = sc.muv_preserve_uv_aspect_tex_image
            ops.origin = sc.muv_preserve_uv_aspect_origin
            row.prop(sc, "muv_preserve_uv_aspect_tex_image", text="")
            box.prop(sc, "muv_preserve_uv_aspect_origin", text="Origin")

        box = layout.box()
        box.prop(sc, "muv_texture_lock_enabled", text="Texture Lock")
        if sc.muv_texture_lock_enabled:
            row = box.row(align=True)
            col = row.column(align=True)
            col.label("Normal Mode:")
            col = row.column(align=True)
            col.operator(
                texture_lock.MUV_OT_TextureLock_Lock.bl_idname,
                text="Lock"
                if not texture_lock.MUV_OT_TextureLock_Lock.is_ready(context)
                else "ReLock")
            ops = col.operator(
                texture_lock.MUV_OT_TextureLock_Unlock.bl_idname,
                text="Unlock")
            ops.connect = sc.muv_texture_lock_connect
            col.prop(sc, "muv_texture_lock_connect", text="Connect")

            row = box.row(align=True)
            row.label("Interactive Mode:")
            box.prop(
                sc, "muv_texture_lock_lock",
                text="Unlock"
                if texture_lock.MUV_OT_TextureLock_Intr.is_running(context)
                else "Lock",
                icon='RESTRICT_VIEW_OFF'
                if texture_lock.MUV_OT_TextureLock_Intr.is_running(context)
                else 'RESTRICT_VIEW_ON')

        box = layout.box()
        box.prop(sc, "muv_texture_wrap_enabled", text="Texture Wrap")
        if sc.muv_texture_wrap_enabled:
            row = box.row(align=True)
            row.operator(texture_wrap.MUV_OT_TextureWrap_Refer.bl_idname,
                         text="Refer")
            row.operator(texture_wrap.MUV_OT_TextureWrap_Set.bl_idname,
                         text="Set")
            box.prop(sc, "muv_texture_wrap_set_and_refer")
            box.prop(sc, "muv_texture_wrap_selseq")

        box = layout.box()
        box.prop(sc, "muv_uv_sculpt_enabled", text="UV Sculpt")
        if sc.muv_uv_sculpt_enabled:
            box.prop(
                sc, "muv_uv_sculpt_enable",
                text="Disable"if uv_sculpt.MUV_OT_UVSculpt.is_running(context)
                else "Enable",
                icon='RESTRICT_VIEW_OFF'
                if uv_sculpt.MUV_OT_UVSculpt.is_running(context)
                else 'RESTRICT_VIEW_ON')
            col = box.column()
            col.label("Brush:")
            col.prop(sc, "muv_uv_sculpt_radius")
            col.prop(sc, "muv_uv_sculpt_strength")
            box.prop(sc, "muv_uv_sculpt_tools")
            if sc.muv_uv_sculpt_tools == 'PINCH':
                box.prop(sc, "muv_uv_sculpt_pinch_invert")
            elif sc.muv_uv_sculpt_tools == 'RELAX':
                box.prop(sc, "muv_uv_sculpt_relax_method")
            box.prop(sc, "muv_uv_sculpt_show_brush")
