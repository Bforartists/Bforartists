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
__version__ = "5.1"
__date__ = "24 Feb 2018"

import bpy

from ..op import flip_rotate_uv
from ..op import mirror_uv
from ..op import move_uv
from ..op import preserve_uv_aspect
from ..op import texture_lock
from ..op import texture_wrap
from ..op import uv_sculpt
from ..op import world_scale_uv


class OBJECT_PT_MUV_UVManip(bpy.types.Panel):
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
        props = sc.muv_props
        layout = self.layout

        box = layout.box()
        box.prop(sc, "muv_fliprot_enabled", text="Flip/Rotate UV")
        if sc.muv_fliprot_enabled:
            row = box.row()
            ops = row.operator(flip_rotate_uv.MUV_FlipRot.bl_idname,
                               text="Flip/Rotate")
            ops.seams = sc.muv_fliprot_seams
            row.prop(sc, "muv_fliprot_seams", text="Seams")

        box = layout.box()
        box.prop(sc, "muv_mirroruv_enabled", text="Mirror UV")
        if sc.muv_mirroruv_enabled:
            row = box.row()
            ops = row.operator(mirror_uv.MUV_MirrorUV.bl_idname, text="Mirror")
            ops.axis = sc.muv_mirroruv_axis
            row.prop(sc, "muv_mirroruv_axis", text="")

        box = layout.box()
        box.prop(sc, "muv_mvuv_enabled", text="Move UV")
        if sc.muv_mvuv_enabled:
            col = box.column()
            col.operator(move_uv.MUV_MVUV.bl_idname, icon='PLAY', text="Start")
            if props.mvuv.running:
                col.enabled = False
            else:
                col.enabled = True

        box = layout.box()
        box.prop(sc, "muv_wsuv_enabled", text="World Scale UV")
        if sc.muv_wsuv_enabled:
            row = box.row(align=True)
            row.operator(world_scale_uv.MUV_WSUVMeasure.bl_idname,
                         text="Measure")
            ops = row.operator(world_scale_uv.MUV_WSUVApply.bl_idname,
                               text="Apply")
            ops.origin = sc.muv_wsuv_origin
            box.label("Source:")
            sp = box.split(percentage=0.7)
            col = sp.column(align=True)
            col.prop(sc, "muv_wsuv_src_mesh_area", text="Mesh Area")
            col.prop(sc, "muv_wsuv_src_uv_area", text="UV Area")
            col.prop(sc, "muv_wsuv_src_density", text="Density")
            col.enabled = False
            sp = sp.split(percentage=1.0)
            col = sp.column(align=True)
            col.label("cm x cm")
            col.label("px x px")
            col.label("px/cm")
            col.enabled = False
            sp = box.split(percentage=0.3)
            sp.label("Mode:")
            sp = sp.split(percentage=1.0)
            col = sp.column()
            col.prop(sc, "muv_wsuv_mode", text="")
            if sc.muv_wsuv_mode == 'USER':
                col.prop(sc, "muv_wsuv_tgt_density", text="Density")
            if sc.muv_wsuv_mode == 'SCALING':
                col.prop(sc, "muv_wsuv_scaling_factor", text="Scaling Factor")
            box.prop(sc, "muv_wsuv_origin", text="Origin")

        box = layout.box()
        box.prop(sc, "muv_preserve_uv_enabled", text="Preserve UV Aspect")
        if sc.muv_preserve_uv_enabled:
            row = box.row()
            ops = row.operator(
                preserve_uv_aspect.MUV_PreserveUVAspect.bl_idname,
                text="Change Image")
            ops.dest_img_name = sc.muv_preserve_uv_tex_image
            ops.origin = sc.muv_preserve_uv_origin
            row.prop(sc, "muv_preserve_uv_tex_image", text="")
            box.prop(sc, "muv_preserve_uv_origin", text="Origin")

        box = layout.box()
        box.prop(sc, "muv_texlock_enabled", text="Texture Lock")
        if sc.muv_texlock_enabled:
            row = box.row(align=True)
            col = row.column(align=True)
            col.label("Normal Mode:")
            col = row.column(align=True)
            col.operator(texture_lock.MUV_TexLockStart.bl_idname, text="Lock")
            ops = col.operator(texture_lock.MUV_TexLockStop.bl_idname,
                               text="Unlock")
            ops.connect = sc.muv_texlock_connect
            col.prop(sc, "muv_texlock_connect", text="Connect")

            row = box.row(align=True)
            row.label("Interactive Mode:")
            if not props.texlock.intr_running:
                row.operator(texture_lock.MUV_TexLockIntrStart.bl_idname,
                             icon='PLAY', text="Start")
            else:
                row.operator(texture_lock.MUV_TexLockIntrStop.bl_idname,
                             icon="PAUSE", text="Stop")

        box = layout.box()
        box.prop(sc, "muv_texwrap_enabled", text="Texture Wrap")
        if sc.muv_texwrap_enabled:
            row = box.row(align=True)
            row.operator(texture_wrap.MUV_TexWrapRefer.bl_idname, text="Refer")
            row.operator(texture_wrap.MUV_TexWrapSet.bl_idname, text="Set")
            box.prop(sc, "muv_texwrap_set_and_refer")
            box.prop(sc, "muv_texwrap_selseq")

        box = layout.box()
        box.prop(sc, "muv_uvsculpt_enabled", text="UV Sculpt")
        if sc.muv_uvsculpt_enabled:
            if not props.uvsculpt.running:
                box.operator(uv_sculpt.MUV_UVSculptOps.bl_idname,
                             icon='PLAY', text="Start")
            else:
                box.operator(uv_sculpt.MUV_UVSculptOps.bl_idname,
                             icon='PAUSE', text="Stop")
            col = box.column()
            col.label("Brush:")
            col.prop(sc, "muv_uvsculpt_radius")
            col.prop(sc, "muv_uvsculpt_strength")
            box.prop(sc, "muv_uvsculpt_tools")
            if sc.muv_uvsculpt_tools == 'PINCH':
                box.prop(sc, "muv_uvsculpt_pinch_invert")
            elif sc.muv_uvsculpt_tools == 'RELAX':
                box.prop(sc, "muv_uvsculpt_relax_method")
            box.prop(sc, "muv_uvsculpt_show_brush")
