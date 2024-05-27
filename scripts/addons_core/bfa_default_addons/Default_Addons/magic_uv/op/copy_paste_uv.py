# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>, Jace Priester"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bmesh
import bpy.utils
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
)

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


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


def get_copy_uv_layers(ops_obj, bm, uv_map):
    uv_layers = []
    if uv_map == "__default":
        if not bm.loops.layers.uv:
            ops_obj.report(
                {'WARNING'}, "Object must have more than one UV map")
            return None
        uv_layers.append(bm.loops.layers.uv.verify())
        ops_obj.report({'INFO'}, "Copy UV coordinate")
    elif uv_map == "__all":
        for uv in bm.loops.layers.uv.keys():
            uv_layers.append(bm.loops.layers.uv[uv])
        ops_obj.report({'INFO'}, "Copy UV coordinate (UV map: ALL)")
    else:
        uv_layers.append(bm.loops.layers.uv[uv_map])
        ops_obj.report(
            {'INFO'}, "Copy UV coordinate (UV map: {})".format(uv_map))

    return uv_layers


def get_paste_uv_layers(ops_obj, obj, bm, src_info, uv_map):
    uv_layers = []
    if uv_map == "__default":
        if not bm.loops.layers.uv:
            ops_obj.report(
                {'WARNING'}, "Object must have more than one UV map")
            return None
        uv_layers.append(bm.loops.layers.uv.verify())
        ops_obj.report({'INFO'}, "Paste UV coordinate")
    elif uv_map == "__new":
        new_uv_map = common.create_new_uv_map(obj)
        if not new_uv_map:
            ops_obj.report({'WARNING'},
                           "Reached to the maximum number of UV map")
            return None
        uv_layers.append(bm.loops.layers.uv[new_uv_map.name])
        ops_obj.report(
            {'INFO'},
            "Paste UV coordinate (UV map: {})".format(new_uv_map.name))
    elif uv_map == "__all":
        for src_layer in src_info.keys():
            if src_layer not in bm.loops.layers.uv.keys():
                new_uv_map = common.create_new_uv_map(obj, src_layer)
                if not new_uv_map:
                    ops_obj.report({'WARNING'},
                                   "Reached to the maximum number of UV map")
                    return None
            uv_layers.append(bm.loops.layers.uv[src_layer])
        ops_obj.report({'INFO'}, "Paste UV coordinate (UV map: ALL)")
    else:
        uv_layers.append(bm.loops.layers.uv[uv_map])
        ops_obj.report(
            {'INFO'}, "Paste UV coordinate (UV map: {})".format(uv_map))

    return uv_layers


def get_src_face_info(ops_obj, bm, uv_layers, only_select=False):
    src_info = {}
    for layer in uv_layers:
        face_info = []
        for face in bm.faces:
            if not only_select or face.select:
                info = {
                    "index": face.index,
                    "uvs": [l[layer].uv.copy() for l in face.loops],
                    "pin_uvs": [l[layer].pin_uv for l in face.loops],
                    "seams": [l.edge.seam for l in face.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        src_info[layer.name] = face_info

    return src_info


def get_dest_face_info(ops_obj, bm, uv_layers, src_info, strategy,
                       only_select=False):
    dest_info = {}
    for layer in uv_layers:
        face_info = []
        for face in bm.faces:
            if not only_select or face.select:
                info = {
                    "index": face.index,
                    "uvs": [l[layer].uv.copy() for l in face.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        key = list(src_info.keys())[0]
        src_face_count = len(src_info[key])
        dest_face_count = len(face_info)
        if strategy == 'N_N' and src_face_count != dest_face_count:
            ops_obj.report(
                {'WARNING'},
                "Number of selected faces is different from copied" +
                "(src:{}, dest:{})"
                .format(src_face_count, dest_face_count))
            return None
        dest_info[layer.name] = face_info

    return dest_info


def _get_select_history_src_face_info(ops_obj, bm, uv_layers):
    src_info = {}
    for layer in uv_layers:
        face_info = []
        for hist in bm.select_history:
            if isinstance(hist, bmesh.types.BMFace) and hist.select:
                info = {
                    "index": hist.index,
                    "uvs": [l[layer].uv.copy() for l in hist.loops],
                    "pin_uvs": [l[layer].pin_uv for l in hist.loops],
                    "seams": [l.edge.seam for l in hist.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        src_info[layer.name] = face_info

    return src_info


def _get_select_history_dest_face_info(ops_obj, bm, uv_layers, src_info,
                                       strategy):
    dest_info = {}
    for layer in uv_layers:
        face_info = []
        for hist in bm.select_history:
            if isinstance(hist, bmesh.types.BMFace) and hist.select:
                info = {
                    "index": hist.index,
                    "uvs": [l[layer].uv.copy() for l in hist.loops],
                }
                face_info.append(info)
        if not face_info:
            ops_obj.report({'WARNING'}, "No faces are selected")
            return None
        key = list(src_info.keys())[0]
        src_face_count = len(src_info[key])
        dest_face_count = len(face_info)
        if strategy == 'N_N' and src_face_count != dest_face_count:
            ops_obj.report(
                {'WARNING'},
                "Number of selected faces is different from copied" +
                "(src:{}, dest:{})"
                .format(src_face_count, dest_face_count))
            return None
        dest_info[layer.name] = face_info

    return dest_info


def paste_uv(ops_obj, bm, src_info, dest_info, uv_layers, strategy, flip,
             rotate, copy_seams):
    for slayer_name, dlayer in zip(src_info.keys(), uv_layers):
        src_faces = src_info[slayer_name]
        dest_faces = dest_info[dlayer.name]

        for idx, dinfo in enumerate(dest_faces):
            sinfo = None
            if strategy == 'N_N':
                sinfo = src_faces[idx]
            elif strategy == 'N_M':
                sinfo = src_faces[idx % len(src_faces)]

            suv = sinfo["uvs"]
            spuv = sinfo["pin_uvs"]
            ss = sinfo["seams"]
            if len(sinfo["uvs"]) != len(dinfo["uvs"]):
                ops_obj.report({'WARNING'}, "Some faces are different size")
                return -1

            suvs_fr = [uv for uv in suv]
            spuvs_fr = [pin_uv for pin_uv in spuv]
            ss_fr = [s for s in ss]

            # flip UVs
            if flip is True:
                suvs_fr.reverse()
                spuvs_fr.reverse()
                ss_fr.reverse()

            # rotate UVs
            for _ in range(rotate):
                uv = suvs_fr.pop()
                pin_uv = spuvs_fr.pop()
                s = ss_fr.pop()
                suvs_fr.insert(0, uv)
                spuvs_fr.insert(0, pin_uv)
                ss_fr.insert(0, s)

            # paste UVs
            for l, suv, spuv, ss in zip(bm.faces[dinfo["index"]].loops,
                                        suvs_fr, spuvs_fr, ss_fr):
                l[dlayer].uv = suv
                l[dlayer].pin_uv = spuv
                if copy_seams is True:
                    l.edge.seam = ss

    return 0


@PropertyClassRegistry()
class _Properties:
    idname = "copy_paste_uv"

    @classmethod
    def init_props(cls, scene):
        class Props():
            src_info = None

        scene.muv_props.copy_paste_uv = Props()
        scene.muv_props.copy_paste_uv_selseq = Props()

        scene.muv_copy_paste_uv_enabled = BoolProperty(
            name="Copy/Paste UV Enabled",
            description="Copy/Paste UV is enabled",
            default=False
        )
        scene.muv_copy_paste_uv_copy_seams = BoolProperty(
            name="Seams",
            description="Copy Seams",
            default=True
        )
        scene.muv_copy_paste_uv_mode = EnumProperty(
            items=[
                ('DEFAULT', "Default", "Default Mode"),
                ('SEL_SEQ', "Selection Sequence", "Selection Sequence Mode")
            ],
            name="Copy/Paste UV Mode",
            description="Copy/Paste UV Mode",
            default='DEFAULT'
        )
        scene.muv_copy_paste_uv_strategy = EnumProperty(
            name="Strategy",
            description="Paste Strategy",
            items=[
                ('N_N', 'N:N', 'Number of faces must be equal to source'),
                ('N_M', 'N:M', 'Number of faces must not be equal to source')
            ],
            default='N_M'
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.copy_paste_uv
        del scene.muv_props.copy_paste_uv_selseq
        del scene.muv_copy_paste_uv_enabled
        del scene.muv_copy_paste_uv_copy_seams
        del scene.muv_copy_paste_uv_mode
        del scene.muv_copy_paste_uv_strategy


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUV_CopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_copy_uv"
    bl_label = "Copy UV"
    bl_description = "Copy UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map = StringProperty(default="__default", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = get_copy_uv_layers(self, bm, self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        src_info = get_src_face_info(self, bm, uv_layers, True)
        if src_info is None:
            return {'CANCELLED'}
        props.src_info = src_info

        face_count = len(props.src_info[list(props.src_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are copied".format(face_count))

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_CopyUV(bpy.types.Menu):
    """
    Menu class: Copy UV coordinate
    """

    bl_idname = "MUV_MT_CopyPasteUV_CopyUV"
    bl_label = "Copy UV (Menu)"
    bl_description = "Menu of Copy UV coordinate"

    @classmethod
    def poll(cls, context):
        return _is_valid_context(context)

    def draw(self, context):
        layout = self.layout
        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]

        # create sub menu
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_CopyUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"

        ops = layout.operator(MUV_OT_CopyPasteUV_CopyUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_CopyUV.bl_idname, text=m)
            ops.uv_map = m


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUV_PasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate
    """

    bl_idname = "uv.muv_copy_paste_uv_paste_uv"
    bl_label = "Paste UV"
    bl_description = "Paste UV coordinate"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map = StringProperty(default="__default", options={'HIDDEN'})
    strategy = EnumProperty(
        name="Strategy",
        description="Paste Strategy",
        items=[
            ('N_N', 'N:N', 'Number of faces must be equal to source'),
            ('N_M', 'N:M', 'Number of faces must not be equal to source')
        ],
        default="N_M"
    )
    flip_copied_uv = BoolProperty(
        name="Flip Copied UV",
        description="Flip Copied UV...",
        default=False
    )
    rotate_copied_uv = IntProperty(
        default=0,
        name="Rotate Copied UV",
        min=0,
        max=30
    )
    copy_seams = BoolProperty(
        name="Seams",
        description="Copy Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.copy_paste_uv
        if not props.src_info:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv
        if not props.src_info:
            self.report({'WARNING'}, "Need copy UV at first")
            return {'CANCELLED'}

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = get_paste_uv_layers(self, obj, bm, props.src_info,
                                        self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        dest_info = get_dest_face_info(self, bm, uv_layers,
                                       props.src_info, self.strategy, True)
        if dest_info is None:
            return {'CANCELLED'}

        # paste
        ret = paste_uv(self, bm, props.src_info, dest_info, uv_layers,
                       self.strategy, self.flip_copied_uv,
                       self.rotate_copied_uv, self.copy_seams)
        if ret:
            return {'CANCELLED'}

        face_count = len(props.src_info[list(dest_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are pasted".format(face_count))

        bmesh.update_edit_mesh(obj.data)

        if compat.check_version(2, 80, 0) < 0:
            if self.copy_seams is True:
                obj.data.show_edge_seams = True

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_PasteUV(bpy.types.Menu):
    """
    Menu class: Paste UV coordinate
    """

    bl_idname = "MUV_MT_CopyPasteUV_PasteUV"
    bl_label = "Paste UV (Menu)"
    bl_description = "Menu of Paste UV coordinate"

    @classmethod
    def poll(cls, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv
        if not props.src_info:
            return False
        return _is_valid_context(context)

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]

        # create sub menu
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname,
                              text="[New]")
        ops.uv_map = "__new"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_PasteUV.bl_idname, text=m)
            ops.uv_map = m
            ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
            ops.strategy = sc.muv_copy_paste_uv_strategy


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUV_SelSeqCopyUV(bpy.types.Operator):
    """
    Operation class: Copy UV coordinate by selection sequence
    """

    bl_idname = "uv.muv_copy_paste_uv_selseq_copy_uv"
    bl_label = "Copy UV (Selection Sequence)"
    bl_description = "Copy UV data by selection sequence"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map = StringProperty(default="__default", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_selseq

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = get_copy_uv_layers(self, bm, self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        src_info = _get_select_history_src_face_info(self, bm, uv_layers)
        if src_info is None:
            return {'CANCELLED'}
        props.src_info = src_info

        face_count = len(props.src_info[list(props.src_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are selected".format(face_count))

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_SelSeqCopyUV(bpy.types.Menu):
    """
    Menu class: Copy UV coordinate by selection sequence
    """

    bl_idname = "MUV_MT_CopyPasteUV_SelSeqCopyUV"
    bl_label = "Copy UV (Selection Sequence) (Menu)"
    bl_description = "Menu of Copy UV coordinate by selection sequence"

    @classmethod
    def poll(cls, context):
        return _is_valid_context(context)

    def draw(self, context):
        layout = self.layout
        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]

        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqCopyUV.bl_idname,
                                  text=m)
            ops.uv_map = m


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_CopyPasteUV_SelSeqPasteUV(bpy.types.Operator):
    """
    Operation class: Paste UV coordinate by selection sequence
    """

    bl_idname = "uv.muv_copy_paste_uv_selseq_paste_uv"
    bl_label = "Paste UV (Selection Sequence)"
    bl_description = "Paste UV coordinate by selection sequence"
    bl_options = {'REGISTER', 'UNDO'}

    uv_map = StringProperty(default="__default", options={'HIDDEN'})
    strategy = EnumProperty(
        name="Strategy",
        description="Paste Strategy",
        items=[
            ('N_N', 'N:N', 'Number of faces must be equal to source'),
            ('N_M', 'N:M', 'Number of faces must not be equal to source')
        ],
        default="N_M"
    )
    flip_copied_uv = BoolProperty(
        name="Flip Copied UV",
        description="Flip Copied UV...",
        default=False
    )
    rotate_copied_uv = IntProperty(
        default=0,
        name="Rotate Copied UV",
        min=0,
        max=30
    )
    copy_seams = BoolProperty(
        name="Seams",
        description="Copy Seams",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_selseq
        if not props.src_info:
            return False
        return _is_valid_context(context)

    def execute(self, context):
        props = context.scene.muv_props.copy_paste_uv_selseq
        if not props.src_info:
            self.report({'WARNING'}, "Need copy UV at first")
            return {'CANCELLED'}

        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]
        bm = common.create_bmesh(obj)

        # get UV layer
        uv_layers = get_paste_uv_layers(self, obj, bm, props.src_info,
                                        self.uv_map)
        if not uv_layers:
            return {'CANCELLED'}

        # get selected face
        dest_info = _get_select_history_dest_face_info(self, bm, uv_layers,
                                                       props.src_info,
                                                       self.strategy)
        if dest_info is None:
            return {'CANCELLED'}

        # paste
        ret = paste_uv(self, bm, props.src_info, dest_info, uv_layers,
                       self.strategy, self.flip_copied_uv,
                       self.rotate_copied_uv, self.copy_seams)
        if ret:
            return {'CANCELLED'}

        face_count = len(props.src_info[list(dest_info.keys())[0]])
        self.report({'INFO'}, "{} face(s) are pasted".format(face_count))

        bmesh.update_edit_mesh(obj.data)

        if compat.check_version(2, 80, 0) < 0:
            if self.copy_seams is True:
                obj.data.show_edge_seams = True

        return {'FINISHED'}


@BlClassRegistry()
class MUV_MT_CopyPasteUV_SelSeqPasteUV(bpy.types.Menu):
    """
    Menu class: Paste UV coordinate by selection sequence
    """

    bl_idname = "MUV_MT_CopyPasteUV_SelSeqPasteUV"
    bl_label = "Paste UV (Selection Sequence) (Menu)"
    bl_description = "Menu of Paste UV coordinate by selection sequence"

    @classmethod
    def poll(cls, context):
        sc = context.scene
        props = sc.muv_props.copy_paste_uv_selseq
        if not props.src_info:
            return False
        return _is_valid_context(context)

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        objs = common.get_uv_editable_objects(context)
        # poll() method ensures that only one object is selected.
        obj = objs[0]

        # create sub menu
        bm = common.create_bmesh(obj)
        uv_maps = bm.loops.layers.uv.keys()

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                              text="[Default]")
        ops.uv_map = "__default"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                              text="[New]")
        ops.uv_map = "__new"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                              text="[All]")
        ops.uv_map = "__all"
        ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
        ops.strategy = sc.muv_copy_paste_uv_strategy

        for m in uv_maps:
            ops = layout.operator(MUV_OT_CopyPasteUV_SelSeqPasteUV.bl_idname,
                                  text=m)
            ops.uv_map = m
            ops.copy_seams = sc.muv_copy_paste_uv_copy_seams
            ops.strategy = sc.muv_copy_paste_uv_strategy
