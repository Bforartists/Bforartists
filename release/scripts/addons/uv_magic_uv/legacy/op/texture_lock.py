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

import math
from math import atan2, cos, sqrt, sin, fabs

import bpy
import bmesh
from mathutils import Vector
from bpy.props import BoolProperty

from ... import common
from ...utils.bl_class_registry import BlClassRegistry
from ...utils.property_class_registry import PropertyClassRegistry


__all__ = [
    'Properties',
    'MUV_OT_TextureLock_Lock',
    'MUV_OT_TextureLock_Unlock',
    'MUV_OT_TextureLock_Intr',
]


def get_vco(verts_orig, loop):
    """
    Get vertex original coordinate from loop
    """
    for vo in verts_orig:
        if vo["vidx"] == loop.vert.index and vo["moved"] is False:
            return vo["vco"]
    return loop.vert.co


def get_link_loops(vert):
    """
    Get loop linked to vertex
    """
    link_loops = []
    for f in vert.link_faces:
        adj_loops = []
        for loop in f.loops:
            # self loop
            if loop.vert == vert:
                l = loop
            # linked loop
            else:
                for e in loop.vert.link_edges:
                    if e.other_vert(loop.vert) == vert:
                        adj_loops.append(loop)
        if len(adj_loops) < 2:
            return None

        link_loops.append({"l": l, "l0": adj_loops[0], "l1": adj_loops[1]})
    return link_loops


def get_ini_geom(link_loop, uv_layer, verts_orig, v_orig):
    """
    Get initial geometory
    (Get interior angle of face in vertex/UV space)
    """
    u = link_loop["l"][uv_layer].uv
    v0 = get_vco(verts_orig, link_loop["l0"])
    u0 = link_loop["l0"][uv_layer].uv
    v1 = get_vco(verts_orig, link_loop["l1"])
    u1 = link_loop["l1"][uv_layer].uv

    # get interior angle of face in vertex space
    v0v1 = v1 - v0
    v0v = v_orig["vco"] - v0
    v1v = v_orig["vco"] - v1
    theta0 = v0v1.angle(v0v)
    theta1 = v0v1.angle(-v1v)
    if (theta0 + theta1) > math.pi:
        theta0 = v0v1.angle(-v0v)
        theta1 = v0v1.angle(v1v)

    # get interior angle of face in UV space
    u0u1 = u1 - u0
    u0u = u - u0
    u1u = u - u1
    phi0 = u0u1.angle(u0u)
    phi1 = u0u1.angle(-u1u)
    if (phi0 + phi1) > math.pi:
        phi0 = u0u1.angle(-u0u)
        phi1 = u0u1.angle(u1u)

    # get direction of linked UV coordinate
    # this will be used to judge whether angle is more or less than 180 degree
    dir0 = u0u1.cross(u0u) > 0
    dir1 = u0u1.cross(u1u) > 0

    return {
        "theta0": theta0,
        "theta1": theta1,
        "phi0": phi0,
        "phi1": phi1,
        "dir0": dir0,
        "dir1": dir1}


def get_target_uv(link_loop, uv_layer, verts_orig, v, ini_geom):
    """
    Get target UV coordinate
    """
    v0 = get_vco(verts_orig, link_loop["l0"])
    lo0 = link_loop["l0"]
    v1 = get_vco(verts_orig, link_loop["l1"])
    lo1 = link_loop["l1"]

    # get interior angle of face in vertex space
    v0v1 = v1 - v0
    v0v = v.co - v0
    v1v = v.co - v1
    theta0 = v0v1.angle(v0v)
    theta1 = v0v1.angle(-v1v)
    if (theta0 + theta1) > math.pi:
        theta0 = v0v1.angle(-v0v)
        theta1 = v0v1.angle(v1v)

    # calculate target interior angle in UV space
    phi0 = theta0 * ini_geom["phi0"] / ini_geom["theta0"]
    phi1 = theta1 * ini_geom["phi1"] / ini_geom["theta1"]

    uv0 = lo0[uv_layer].uv
    uv1 = lo1[uv_layer].uv

    # calculate target vertex coordinate from target interior angle
    tuv0, tuv1 = calc_tri_vert(uv0, uv1, phi0, phi1)

    # target UV coordinate depends on direction, so judge using direction of
    # linked UV coordinate
    u0u1 = uv1 - uv0
    u0u = tuv0 - uv0
    u1u = tuv0 - uv1
    dir0 = u0u1.cross(u0u) > 0
    dir1 = u0u1.cross(u1u) > 0
    if (ini_geom["dir0"] != dir0) or (ini_geom["dir1"] != dir1):
        return tuv1

    return tuv0


def calc_tri_vert(v0, v1, angle0, angle1):
    """
    Calculate rest coordinate from other coordinates and angle of end
    """
    angle = math.pi - angle0 - angle1

    alpha = atan2(v1.y - v0.y, v1.x - v0.x)
    d = (v1.x - v0.x) / cos(alpha)
    a = d * sin(angle0) / sin(angle)
    b = d * sin(angle1) / sin(angle)
    s = (a + b + d) / 2.0
    if fabs(d) < 0.0000001:
        xd = 0
        yd = 0
    else:
        r = s * (s - a) * (s - b) * (s - d)
        if r < 0:
            xd = 0
            yd = 0
        else:
            xd = (b * b - a * a + d * d) / (2 * d)
            yd = 2 * sqrt(r) / d
    x1 = xd * cos(alpha) - yd * sin(alpha) + v0.x
    y1 = xd * sin(alpha) + yd * cos(alpha) + v0.y
    x2 = xd * cos(alpha) + yd * sin(alpha) + v0.x
    y2 = xd * sin(alpha) - yd * cos(alpha) + v0.y

    return Vector((x1, y1)), Vector((x2, y2))


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
    idname = "texture_lock"

    @classmethod
    def init_props(cls, scene):
        class Props():
            verts_orig = None

        scene.muv_props.texture_lock = Props()

        def get_func(_):
            return MUV_OT_TextureLock_Intr.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_texture_lock_operator_intr('INVOKE_REGION_WIN')

        scene.muv_texture_lock_enabled = BoolProperty(
            name="Texture Lock Enabled",
            description="Texture Lock is enabled",
            default=False
        )
        scene.muv_texture_lock_lock = BoolProperty(
            name="Texture Lock Locked",
            description="Texture Lock is locked",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_texture_lock_connect = BoolProperty(
            name="Connect UV",
            default=True
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.texture_lock
        del scene.muv_texture_lock_enabled
        del scene.muv_texture_lock_lock
        del scene.muv_texture_lock_connect


@BlClassRegistry(legacy=True)
class MUV_OT_TextureLock_Lock(bpy.types.Operator):
    """
    Operation class: Lock Texture
    """

    bl_idname = "uv.muv_texture_lock_operator_lock"
    bl_label = "Lock Texture"
    bl_description = "Lock Texture"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return is_valid_context(context)

    @classmethod
    def is_ready(cls, context):
        sc = context.scene
        props = sc.muv_props.texture_lock
        if props.verts_orig:
            return True
        return False

    def execute(self, context):
        props = context.scene.muv_props.texture_lock
        obj = bpy.context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        if not bm.loops.layers.uv:
            self.report(
                {'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}

        props.verts_orig = [
            {"vidx": v.index, "vco": v.co.copy(), "moved": False}
            for v in bm.verts if v.select]

        return {'FINISHED'}


@BlClassRegistry(legacy=True)
class MUV_OT_TextureLock_Unlock(bpy.types.Operator):
    """
    Operation class: Unlock Texture
    """

    bl_idname = "uv.muv_texture_lock_operator_unlock"
    bl_label = "Unlock Texture"
    bl_description = "Unlock Texture"
    bl_options = {'REGISTER', 'UNDO'}

    connect = BoolProperty(
        name="Connect UV",
        default=True
    )

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        sc = context.scene
        props = sc.muv_props.texture_lock
        if not props.verts_orig:
            return False
        if not MUV_OT_TextureLock_Lock.is_ready(context):
            return False
        if not is_valid_context(context):
            return False
        return True

    def execute(self, context):
        sc = context.scene
        props = sc.muv_props.texture_lock
        obj = bpy.context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        if not bm.loops.layers.uv:
            self.report(
                {'WARNING'}, "Object must have more than one UV map")
            return {'CANCELLED'}
        uv_layer = bm.loops.layers.uv.verify()

        verts = [v.index for v in bm.verts if v.select]
        verts_orig = props.verts_orig

        # move UV followed by vertex coordinate
        for vidx, v_orig in zip(verts, verts_orig):
            if vidx != v_orig["vidx"]:
                self.report({'ERROR'}, "Internal Error")
                return {"CANCELLED"}

            v = bm.verts[vidx]
            link_loops = get_link_loops(v)

            result = []

            for ll in link_loops:
                ini_geom = get_ini_geom(ll, uv_layer, verts_orig, v_orig)
                target_uv = get_target_uv(
                    ll, uv_layer, verts_orig, v, ini_geom)
                result.append({"l": ll["l"], "uv": target_uv})

            # connect other face's UV
            if self.connect:
                ave = Vector((0.0, 0.0))
                for r in result:
                    ave = ave + r["uv"]
                ave = ave / len(result)
                for r in result:
                    r["l"][uv_layer].uv = ave
            else:
                for r in result:
                    r["l"][uv_layer].uv = r["uv"]
            v_orig["moved"] = True
            bmesh.update_edit_mesh(obj.data)

        props.verts_orig = None

        return {'FINISHED'}


@BlClassRegistry(legacy=True)
class MUV_OT_TextureLock_Intr(bpy.types.Operator):
    """
    Operation class: Texture Lock (Interactive mode)
    """

    bl_idname = "uv.muv_texture_lock_operator_intr"
    bl_label = "Texture Lock (Interactive mode)"
    bl_description = "Internal operation for Texture Lock (Interactive mode)"

    __timer = None

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return False
        return is_valid_context(context)

    @classmethod
    def is_running(cls, _):
        return 1 if cls.__timer else 0

    @classmethod
    def handle_add(cls, self_, context):
        if cls.__timer is None:
            cls.__timer = context.window_manager.event_timer_add(
                0.10, context.window)
            context.window_manager.modal_handler_add(self_)

    @classmethod
    def handle_remove(cls, context):
        if cls.__timer is not None:
            context.window_manager.event_timer_remove(cls.__timer)
            cls.__timer = None

    def __init__(self):
        self.__intr_verts_orig = []
        self.__intr_verts = []

    def __sel_verts_changed(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        prev = set(self.__intr_verts)
        now = set([v.index for v in bm.verts if v.select])

        return prev != now

    def __reinit_verts(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        self.__intr_verts_orig = [
            {"vidx": v.index, "vco": v.co.copy(), "moved": False}
            for v in bm.verts if v.select]
        self.__intr_verts = [v.index for v in bm.verts if v.select]

    def __update_uv(self, context):
        """
        Update UV when vertex coordinates are changed
        """
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        if not bm.loops.layers.uv:
            self.report({'WARNING'}, "Object must have more than one UV map")
            return
        uv_layer = bm.loops.layers.uv.verify()

        verts = [v.index for v in bm.verts if v.select]
        verts_orig = self.__intr_verts_orig

        for vidx, v_orig in zip(verts, verts_orig):
            if vidx != v_orig["vidx"]:
                self.report({'ERROR'}, "Internal Error")
                return

            v = bm.verts[vidx]
            link_loops = get_link_loops(v)

            result = []
            for ll in link_loops:
                ini_geom = get_ini_geom(ll, uv_layer, verts_orig, v_orig)
                target_uv = get_target_uv(
                    ll, uv_layer, verts_orig, v, ini_geom)
                result.append({"l": ll["l"], "uv": target_uv})

            # UV connect option is always true, because it raises
            # unexpected behavior
            ave = Vector((0.0, 0.0))
            for r in result:
                ave = ave + r["uv"]
            ave = ave / len(result)
            for r in result:
                r["l"][uv_layer].uv = ave
            v_orig["moved"] = True
            bmesh.update_edit_mesh(obj.data)

        common.redraw_all_areas()
        self.__intr_verts_orig = [
            {"vidx": v.index, "vco": v.co.copy(), "moved": False}
            for v in bm.verts if v.select]

    def modal(self, context, event):
        if not is_valid_context(context):
            MUV_OT_TextureLock_Intr.handle_remove(context)
            return {'FINISHED'}

        if not MUV_OT_TextureLock_Intr.is_running(context):
            return {'FINISHED'}

        if context.area:
            context.area.tag_redraw()

        if event.type == 'TIMER':
            if self.__sel_verts_changed(context):
                self.__reinit_verts(context)
            else:
                self.__update_uv(context)

        return {'PASS_THROUGH'}

    def invoke(self, context, _):
        if not is_valid_context(context):
            return {'CANCELLED'}

        if not MUV_OT_TextureLock_Intr.is_running(context):
            MUV_OT_TextureLock_Intr.handle_add(self, context)
            return {'RUNNING_MODAL'}
        else:
            MUV_OT_TextureLock_Intr.handle_remove(context)

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}
