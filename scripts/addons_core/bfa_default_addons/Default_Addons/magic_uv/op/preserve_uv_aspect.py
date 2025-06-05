# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.6"
__date__ = "22 Apr 2022"

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
import bmesh
from mathutils import Vector

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat


def _is_valid_context(context):
    # only 'VIEW_3D' space is allowed to execute
    if not common.is_valid_space(context, ['VIEW_3D']):
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
    idname = "preserve_uv_aspect"

    @classmethod
    def init_props(cls, scene):
        def get_loaded_texture_name(_, __):
            items = [(key, key, "") for key in bpy.data.images.keys()]
            items.append(("None", "None", ""))
            return items

        scene.muv_preserve_uv_aspect_enabled = BoolProperty(
            name="Preserve UV Aspect Enabled",
            description="Preserve UV Aspect is enabled",
            default=False
        )
        scene.muv_preserve_uv_aspect_tex_image = EnumProperty(
            name="Image",
            description="Texture Image",
            items=get_loaded_texture_name
        )
        scene.muv_preserve_uv_aspect_origin = EnumProperty(
            name="Origin",
            description="Aspect Origin",
            items=[
                ('CENTER', 'Center', 'Center'),
                ('LEFT_TOP', 'Left Top', 'Left Bottom'),
                ('LEFT_CENTER', 'Left Center', 'Left Center'),
                ('LEFT_BOTTOM', 'Left Bottom', 'Left Bottom'),
                ('CENTER_TOP', 'Center Top', 'Center Top'),
                ('CENTER_BOTTOM', 'Center Bottom', 'Center Bottom'),
                ('RIGHT_TOP', 'Right Top', 'Right Top'),
                ('RIGHT_CENTER', 'Right Center', 'Right Center'),
                ('RIGHT_BOTTOM', 'Right Bottom', 'Right Bottom')

            ],
            default="CENTER"
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_preserve_uv_aspect_enabled
        del scene.muv_preserve_uv_aspect_tex_image
        del scene.muv_preserve_uv_aspect_origin


@BlClassRegistry()
@compat.make_annotations
class MUV_OT_PreserveUVAspect(bpy.types.Operator):
    """
    Operation class: Preserve UV Aspect
    """

    bl_idname = "uv.muv_preserve_uv_aspect"
    bl_label = "Preserve UV Aspect"
    bl_description = "Choose Image"
    bl_options = {'REGISTER', 'UNDO'}

    dest_img_name = StringProperty(options={'HIDDEN'})
    origin = EnumProperty(
        name="Origin",
        description="Aspect Origin",
        items=[
            ('CENTER', 'Center', 'Center'),
            ('LEFT_TOP', 'Left Top', 'Left Bottom'),
            ('LEFT_CENTER', 'Left Center', 'Left Center'),
            ('LEFT_BOTTOM', 'Left Bottom', 'Left Bottom'),
            ('CENTER_TOP', 'Center Top', 'Center Top'),
            ('CENTER_BOTTOM', 'Center Bottom', 'Center Bottom'),
            ('RIGHT_TOP', 'Right Top', 'Right Top'),
            ('RIGHT_CENTER', 'Right Center', 'Right Center'),
            ('RIGHT_BOTTOM', 'Right Bottom', 'Right Bottom')

        ],
        default="CENTER"
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def execute(self, context):
        # Note: the current system only works if the
        # f[tex_layer].image doesn't return None
        # which will happen in certain cases
        objs = common.get_uv_editable_objects(context)

        obj_list = {}   # { Material: Object }
        for obj in objs:
            if common.check_version(2, 80, 0) >= 0:
                # If more than two selected objects shares same
                # material, we need to calculate new UV coordinates
                # before image on texture node is overwritten.
                material_to_rewrite = []
                for slot in obj.material_slots:
                    if not slot.material:
                        continue
                    nodes = common.find_texture_nodes_from_material(
                        slot.material)
                    if len(nodes) >= 2:
                        self.report(
                            {'WARNING'},
                            "Object {} must not have more than 2 "
                            "shader nodes with image texture"
                            .format(obj.name))
                        return {'CANCELLED'}
                    if not nodes:
                        continue
                    material_to_rewrite.append(slot.material)

                if len(material_to_rewrite) >= 2:
                    self.report(
                        {'WARNING'},
                        "Object {} must not have more than 2 "
                        "materials with image texture"
                        .format(obj.name))
                    return {'CANCELLED'}
                if len(material_to_rewrite) == 0:
                    self.report(
                        {'WARNING'},
                        "Object {} must not have more than 1 "
                        "material with image texture"
                        .format(obj.name))
                    return {'CANCELLED'}
                if material_to_rewrite[0] not in obj_list.keys():
                    obj_list[material_to_rewrite[0]] = []
                obj_list[material_to_rewrite[0]].append(obj)
            else:
                # If blender version is < (2, 79), multiple objects editing
                # mode is not supported. So, we add dummy key to obj_list.
                obj_list["Dummy"] = [obj]

        # pylint: disable=R1702
        for mtrl, o in obj_list.items():
            for obj in o:
                bm = bmesh.from_edit_mesh(obj.data)

                if common.check_version(2, 73, 0) >= 0:
                    bm.faces.ensure_lookup_table()

                if not bm.loops.layers.uv:
                    self.report({'WARNING'},
                                "Object must have more than one UV map")
                    return {'CANCELLED'}

                uv_layer = bm.loops.layers.uv.verify()

                sel_faces = [f for f in bm.faces if f.select]
                dest_img = bpy.data.images[self.dest_img_name]

                info = {}

                if compat.check_version(2, 80, 0) >= 0:
                    tex_image = common.find_image(obj)
                    for f in sel_faces:
                        if tex_image not in info.keys():
                            info[tex_image] = {}
                            info[tex_image]['faces'] = []
                        info[tex_image]['faces'].append(f)
                else:
                    tex_layer = bm.faces.layers.tex.verify()
                    for f in sel_faces:
                        if not f[tex_layer].image in info.keys():
                            info[f[tex_layer].image] = {}
                            info[f[tex_layer].image]['faces'] = []
                        info[f[tex_layer].image]['faces'].append(f)

                for img in info:
                    if img is None:
                        continue

                    src_img = img
                    ratio = Vector((
                        dest_img.size[0] / src_img.size[0],
                        dest_img.size[1] / src_img.size[1]))

                    if self.origin == 'CENTER':
                        origin = Vector((0.0, 0.0))
                        num = 0
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin = origin + uv
                                num = num + 1
                        origin = origin / num
                    elif self.origin == 'LEFT_TOP':
                        origin = Vector((100000.0, -100000.0))
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = min(origin.x, uv.x)
                                origin.y = max(origin.y, uv.y)
                    elif self.origin == 'LEFT_CENTER':
                        origin = Vector((100000.0, 0.0))
                        num = 0
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = min(origin.x, uv.x)
                                origin.y = origin.y + uv.y
                                num = num + 1
                        origin.y = origin.y / num
                    elif self.origin == 'LEFT_BOTTOM':
                        origin = Vector((100000.0, 100000.0))
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = min(origin.x, uv.x)
                                origin.y = min(origin.y, uv.y)
                    elif self.origin == 'CENTER_TOP':
                        origin = Vector((0.0, -100000.0))
                        num = 0
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = origin.x + uv.x
                                origin.y = max(origin.y, uv.y)
                                num = num + 1
                        origin.x = origin.x / num
                    elif self.origin == 'CENTER_BOTTOM':
                        origin = Vector((0.0, 100000.0))
                        num = 0
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = origin.x + uv.x
                                origin.y = min(origin.y, uv.y)
                                num = num + 1
                        origin.x = origin.x / num
                    elif self.origin == 'RIGHT_TOP':
                        origin = Vector((-100000.0, -100000.0))
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = max(origin.x, uv.x)
                                origin.y = max(origin.y, uv.y)
                    elif self.origin == 'RIGHT_CENTER':
                        origin = Vector((-100000.0, 0.0))
                        num = 0
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = max(origin.x, uv.x)
                                origin.y = origin.y + uv.y
                                num = num + 1
                        origin.y = origin.y / num
                    elif self.origin == 'RIGHT_BOTTOM':
                        origin = Vector((-100000.0, 100000.0))
                        for f in info[img]['faces']:
                            for l in f.loops:
                                uv = l[uv_layer].uv
                                origin.x = max(origin.x, uv.x)
                                origin.y = min(origin.y, uv.y)
                    else:
                        self.report({'ERROR'}, "Unknown Operation")
                        return {'CANCELLED'}

                    info[img]['ratio'] = ratio
                    info[img]['origin'] = origin

                for img in info:
                    if img is None:
                        continue

                    for f in info[img]['faces']:
                        if compat.check_version(2, 80, 0) < 0:
                            tex_layer = bm.faces.layers.tex.verify()
                            f[tex_layer].image = dest_img
                        for l in f.loops:
                            uv = l[uv_layer].uv
                            origin = info[img]['origin']
                            ratio = info[img]['ratio']
                            diff = uv - origin
                            diff.x = diff.x / ratio.x
                            diff.y = diff.y / ratio.y
                            uv.x = origin.x + diff.x
                            uv.y = origin.y + diff.y
                            l[uv_layer].uv = uv

                bmesh.update_edit_mesh(obj.data)

            if compat.check_version(2, 80, 0) >= 0:
                nodes = common.find_texture_nodes_from_material(mtrl)
                nodes[0].image = dest_img

        return {'FINISHED'}
