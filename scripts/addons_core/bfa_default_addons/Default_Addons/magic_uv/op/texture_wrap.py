# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import (
    BoolProperty,
)
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
        return False

    # Multiple objects editing mode is not supported in this feature.
    objs = common.get_uv_editable_objects(context)
    if len(objs) != 1:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "texture_wrap"

    @classmethod
    def init_props(cls, scene):
        class Props():
            ref_face_index = -1
            ref_obj = None

        scene.muv_props.texture_wrap = Props()

        scene.muv_texture_wrap_enabled = BoolProperty(
            name="Texture Wrap",
            description="Texture Wrap is enabled",
            default=False
        )
        scene.muv_texture_wrap_set_and_refer = BoolProperty(
            name="Set and Refer",
            description="Refer and set UV",
            default=True
        )
        scene.muv_texture_wrap_selseq = BoolProperty(
            name="Selection Sequence",
            description="Set UV sequentially",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.texture_wrap
        del scene.muv_texture_wrap_enabled
        del scene.muv_texture_wrap_set_and_refer
        del scene.muv_texture_wrap_selseq


@BlClassRegistry()
class MUV_OT_TextureWrap_Refer(bpy.types.Operator):
    """
    Operation class: Refer UV
    """

    bl_idname = "uv.muv_texture_wrap_refer"
    bl_label = "Refer"
    bl_description = "Refer UV"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.texture_wrap

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        if not bm.loops.layers.uv:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}

        sel_faces = [f for f in bm.faces if f.select]
        if len(sel_faces) != 1:
            self.report({'WARNING'}, "Must select only one face")
            return {'CANCELLED'}

        props.ref_face_index = sel_faces[0].index
        props.ref_obj = obj

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_TextureWrap_Set(bpy.types.Operator):
    """
    Operation class: Set UV
    """

    bl_idname = "uv.muv_texture_wrap_set"
    bl_label = "Set"
    bl_description = "Set UV"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.texture_wrap
        if not props.ref_obj:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        sc = context.scene
        props = sc.muv_props.texture_wrap

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        if not bm.loops.layers.uv:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        if sc.muv_texture_wrap_selseq:
            sel_faces = []
            for hist in bm.select_history:
                if isinstance(hist, bmesh.types.BMFace) and hist.select:
                    sel_faces.append(hist)
            if not sel_faces:
                self.report({'WARNING'}, "Must select more than one face")
                return {'CANCELLED'}
        else:
            sel_faces = [f for f in bm.faces if f.select]
            if len(sel_faces) != 1:
                self.report({'WARNING'}, "Must select only one face")
                return {'CANCELLED'}

        ref_face_index = props.ref_face_index
        for face in sel_faces:
            tgt_face_index = face.index
            if ref_face_index == tgt_face_index:
                self.report({'WARNING'}, "Must select different face")
                return {'CANCELLED'}

            if props.ref_obj != obj:
                self.report({'WARNING'}, "Object must be same")
                return {'CANCELLED'}

            ref_face = bm.faces[ref_face_index]
            tgt_face = bm.faces[tgt_face_index]

            # get common vertices info
            common_verts = []
            for sl in ref_face.loops:
                for dl in tgt_face.loops:
                    if sl.vert == dl.vert:
                        info = {"vert": sl.vert, "ref_loop": sl,
                                "tgt_loop": dl}
                        common_verts.append(info)
                        break

            if len(common_verts) != 2:
                self.report({'WARNING'},
                            "2 vertices must be shared among faces")
                return {'CANCELLED'}

            # get reference other vertices info
            ref_other_verts = []
            for sl in ref_face.loops:
                for ci in common_verts:
                    if sl.vert == ci["vert"]:
                        break
                else:
                    info = {"vert": sl.vert, "loop": sl}
                    ref_other_verts.append(info)

            if not ref_other_verts:
                self.report({'WARNING'}, "More than 1 vertex must be unshared")
                return {'CANCELLED'}

            # get reference info
            ref_info = {}
            cv0 = common_verts[0]["vert"].co
            cv1 = common_verts[1]["vert"].co
            cuv0 = common_verts[0]["ref_loop"][uv_layer].uv
            cuv1 = common_verts[1]["ref_loop"][uv_layer].uv
            ov0 = ref_other_verts[0]["vert"].co
            ouv0 = ref_other_verts[0]["loop"][uv_layer].uv
            ref_info["vert_vdiff"] = cv1 - cv0
            ref_info["uv_vdiff"] = cuv1 - cuv0
            ref_info["vert_hdiff"], _ = common.diff_point_to_segment(
                cv0, cv1, ov0)
            ref_info["uv_hdiff"], _ = common.diff_point_to_segment(
                cuv0, cuv1, ouv0)

            # get target other vertices info
            tgt_other_verts = []
            for dl in tgt_face.loops:
                for ci in common_verts:
                    if dl.vert == ci["vert"]:
                        break
                else:
                    info = {"vert": dl.vert, "loop": dl}
                    tgt_other_verts.append(info)

            if not tgt_other_verts:
                self.report({'WARNING'}, "More than 1 vertex must be unshared")
                return {'CANCELLED'}

            # get target info
            for info in tgt_other_verts:
                cv0 = common_verts[0]["vert"].co
                cv1 = common_verts[1]["vert"].co
                cuv0 = common_verts[0]["ref_loop"][uv_layer].uv
                ov = info["vert"].co
                info["vert_hdiff"], x = common.diff_point_to_segment(
                    cv0, cv1, ov)
                info["vert_vdiff"] = x - common_verts[0]["vert"].co

                # calculate factor
                fact_h = -info["vert_hdiff"].length / \
                    ref_info["vert_hdiff"].length
                fact_v = info["vert_vdiff"].length / \
                    ref_info["vert_vdiff"].length
                duv_h = ref_info["uv_hdiff"] * fact_h
                duv_v = ref_info["uv_vdiff"] * fact_v

                # get target UV
                info["target_uv"] = cuv0 + duv_h + duv_v

            # apply to common UVs
            for info in common_verts:
                info["tgt_loop"][uv_layer].uv = \
                    info["ref_loop"][uv_layer].uv.copy()
            # apply to other UVs
            for info in tgt_other_verts:
                info["loop"][uv_layer].uv = info["target_uv"]

            common.debug_print("===== Target Other Vertices =====")
            common.debug_print(tgt_other_verts)

            bmesh.update_edit_mesh(obj.data)

            ref_face_index = tgt_face_index

        if sc.muv_texture_wrap_set_and_refer:
            props.ref_face_index = tgt_face_index

        return {'FINISHED'}
