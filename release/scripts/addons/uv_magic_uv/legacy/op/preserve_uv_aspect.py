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
import bmesh
from bpy.props import StringProperty, EnumProperty, BoolProperty
from mathutils import Vector

from ... import common
from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry


__all__ = [
    'Properties',
    'MUV_OT_PreserveUVAspect',
]


def is_valid_context(context):
    obj = context.object

    # only edit mode is allowed to execute
    if obj is None:
        return False
    if obj.type != 'MESH':
        return False
    if context.object.mode != 'EDIT':
        return False

    # only 'VIEW_3D' space is allowed to execute
    for space in context.area.spaces:
        if space.type == 'VIEW_3D':
            break
    else:
        return False

    return True


@PropertyClassRegistry(legacy=True)
class Properties:
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


@BlClassRegistry(legacy=True)
class MUV_OT_PreserveUVAspect(bpy.types.Operator):
    """
    Operation class: Preserve UV Aspect
    """

    bl_idname = "uv.muv_preserve_uv_aspect_operator"
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
        return is_valid_context(context)

    def execute(self, context):
        # Note: the current system only works if the
        # f[tex_layer].image doesn't return None
        # which will happen in certain cases
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()

        if not bm.loops.layers.uv:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}

        uv_layer = bm.loops.layers.uv.verify()
        tex_layer = bm.faces.layers.tex.verify()

        sel_faces = [f for f in bm.faces if f.select]
        dest_img = bpy.data.images[self.dest_img_name]

        info = {}

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

            info[img]['ratio'] = ratio
            info[img]['origin'] = origin

        for img in info:
            if img is None:
                continue

            for f in info[img]['faces']:
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

        return {'FINISHED'}
