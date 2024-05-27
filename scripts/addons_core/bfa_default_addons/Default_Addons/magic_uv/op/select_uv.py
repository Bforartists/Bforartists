# SPDX-FileCopyrightText: 2018-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


@PropertyClassRegistry()
class _Properties:
    idname = "select_uv"

    @classmethod
    def init_props(cls, scene):
        scene.muv_select_uv_enabled = BoolProperty(
            name="Select UV Enabled",
            description="Select UV is enabled",
            default=False
        )
        scene.muv_select_uv_same_polygon_threshold = FloatProperty(
            name="Same Polygon Threshold",
            description="Threshold to distinguish same polygons",
            default=0.00001,
            min=0.00001,
            max=0.01,
            step=0.00001
        )
        scene.muv_select_uv_selection_method = EnumProperty(
            name="Selection Method",
            description="How to select faces which have overlapped UVs",
            items=[
                ('EXTEND', "Extend",
                 "Select faces without unselecting selected faces"),
                ('RESET', "Reset", "Select faces and unselect selected faces"),
            ],
            default='RESET'
        )
        scene.muv_select_uv_sync_mesh_selection = BoolProperty(
            name="Sync Mesh Selection",
            description="Select the mesh's faces as well as UVs' faces",
            default=False
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_select_uv_enabled
        del scene.muv_select_uv_same_polygon_threshold


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_SelectUV_SelectOverlapped(bpy.types.Operator):
    """
    Operation class: Select faces which have overlapped UVs
    """

    bl_idname = "uv.muv_select_uv_select_overlapped"
    bl_label = "Overlapped"
    bl_description = "Select faces which have overlapped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    same_polygon_threshold = FloatProperty(
        name="Same Polygon Threshold",
        description="Threshold to distinguish same polygons",
        default=0.00001,
        min=0.00001,
        max=0.01,
        step=0.00001
    )
    selection_method = EnumProperty(
        name="Selection Method",
        description="How to select faces which have overlapped UVs",
        items=[
            ('EXTEND', "Extend",
             "Select faces without unselecting selected faces"),
            ('RESET', "Reset", "Select faces and unselect selected faces"),
        ],
        default='RESET'
    )
    sync_mesh_selection = BoolProperty(
        name="Sync Mesh Selection",
        description="Select the mesh's faces as well as UVs' faces",
        default=False
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    @staticmethod
    def setup_argument(ops, scene):
        ops.same_polygon_threshold = scene.muv_select_uv_same_polygon_threshold
        ops.selection_method = scene.muv_select_uv_selection_method
        ops.sync_mesh_selection = scene.muv_select_uv_sync_mesh_selection

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        bm_list = []
        uv_layer_list = []
        faces_list = []
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            if context.tool_settings.use_uv_select_sync:
                sel_faces = [f for f in bm.faces]
            else:
                sel_faces = [f for f in bm.faces if f.select]
            bm_list.append(bm)
            uv_layer_list.append(uv_layer)
            faces_list.append(sel_faces)

        overlapped_info = common.get_overlapped_uv_info(
            bm_list, faces_list, uv_layer_list, 'FACE',
            self.same_polygon_threshold)

        if self.selection_method == 'RESET':
            if context.tool_settings.use_uv_select_sync:
                for faces in faces_list:
                    for f in faces:
                        f.select = False
            else:
                for uv_layer, faces in zip(uv_layer_list, faces_list):
                    for f in faces:
                        if self.sync_mesh_selection:
                            f.select = False
                        for l in f.loops:
                            l[uv_layer].select = False

        for info in overlapped_info:
            if context.tool_settings.use_uv_select_sync:
                info["subject_face"].select = True
            else:
                if self.sync_mesh_selection:
                    info["subject_face"].select = True
                for l in info["subject_face"].loops:
                    l[info["subject_uv_layer"]].select = True

        for obj in objs:
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_SelectUV_SelectFlipped(bpy.types.Operator):
    """
    Operation class: Select faces which have flipped UVs
    """

    bl_idname = "uv.muv_select_uv_select_flipped"
    bl_label = "Flipped"
    bl_description = "Select faces which have flipped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    selection_method = EnumProperty(
        name="Selection Method",
        description="How to select faces which have overlapped UVs",
        items=[
            ('EXTEND', "Extend",
             "Select faces without unselecting selected faces"),
            ('RESET', "Reset", "Select faces and unselect selected faces"),
        ],
        default='RESET'
    )
    sync_mesh_selection = BoolProperty(
        name="Sync Mesh Selection",
        description="Select the mesh's faces as well as UVs' faces",
        default=False
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    @staticmethod
    def setup_argument(ops, scene):
        ops.selection_method = scene.muv_select_uv_selection_method
        ops.sync_mesh_selection = scene.muv_select_uv_sync_mesh_selection

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        bm_list = []
        uv_layer_list = []
        faces_list = []
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            if context.tool_settings.use_uv_select_sync:
                sel_faces = [f for f in bm.faces]
            else:
                sel_faces = [f for f in bm.faces if f.select]
            bm_list.append(bm)
            uv_layer_list.append(uv_layer)
            faces_list.append(sel_faces)

        flipped_info = common.get_flipped_uv_info(
            bm_list, faces_list, uv_layer_list)

        if self.selection_method == 'RESET':
            if context.tool_settings.use_uv_select_sync:
                for faces in faces_list:
                    for f in faces:
                        f.select = False
            else:
                for uv_layer, faces in zip(uv_layer_list, faces_list):
                    for f in faces:
                        if self.sync_mesh_selection:
                            f.select = False
                        for l in f.loops:
                            l[uv_layer].select = False

        for info in flipped_info:
            if context.tool_settings.use_uv_select_sync:
                info["face"].select = True
            else:
                if self.sync_mesh_selection:
                    info["face"].select = True
                for l in info["face"].loops:
                    l[info["uv_layer"]].select = True

        for obj in objs:
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_SelectUV_ZoomSelectedUV(bpy.types.Operator):
    """
    Operation class: Zoom selected UV in View3D space
    """

    bl_idname = "uv.muv_select_uv_zoom_selected_uv"
    bl_label = "Zoom Selected UV"
    bl_description = "Zoom selected UV in View3D space"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def _get_override_context(self, context):
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return {'window': window, 'screen': screen,
                                    'area': area, 'region': region}
        return None

    def execute(self, context):
        objs = common.get_uv_editable_objects(context)

        bm_list = []
        uv_layer_list = []
        verts_list = []
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if common.check_version(2, 73, 0) >= 0:
                bm.verts.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            sel_verts = [v for v in bm.verts if v.select]
            bm_list.append(bm)
            uv_layer_list.append(uv_layer)
            verts_list.append(sel_verts)

        # Get all selected UV vertices in UV Editor.
        sel_uv_verts = []
        for vlist, uv_layer in zip(verts_list, uv_layer_list):
            for v in vlist:
                for l in v.link_loops:
                    if l[uv_layer].select or \
                            context.tool_settings.use_uv_select_sync:
                        sel_uv_verts.append(v)
                        break

        # Select vertices only selected in UV Editor.
        for bm in bm_list:
            for v in bm.verts:
                v.select = False
        for v in sel_uv_verts:
            v.select = True
        for obj in objs:
            bmesh.update_edit_mesh(obj.data)

        # Zoom.
        context_override = self._get_override_context(context)
        if context_override is None:
            self.report({'WARNING'}, "More than one 'VIEW_3D' area must exist")
            return {'CANCELLED'}
        with context.temp_override(**context_override):
            bpy.ops.view3d.view_selected(use_all_regions=False)

        # Revert selection of vertices.
        for v in sel_verts:
            v.select = True
        for obj in objs:
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
