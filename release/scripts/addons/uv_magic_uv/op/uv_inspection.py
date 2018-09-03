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
import bmesh
import bgl
from mathutils import Vector

from .. import common


def is_polygon_same(points1, points2):
    if len(points1) != len(points2):
        return False

    pts1 = points1.as_list()
    pts2 = points2.as_list()

    for p1 in pts1:
        for p2 in pts2:
            diff = p2 - p1
            if diff.length < 0.0000001:
                pts2.remove(p2)
                break
        else:
            return False

    return True


def is_segment_intersect(start1, end1, start2, end2):
    seg1 = end1 - start1
    seg2 = end2 - start2

    a1 = -seg1.y
    b1 = seg1.x
    d1 = -(a1 * start1.x + b1 * start1.y)

    a2 = -seg2.y
    b2 = seg2.x
    d2 = -(a2 * start2.x + b2 * start2.y)

    seg1_line2_start = a2 * start1.x + b2 * start1.y + d2
    seg1_line2_end = a2 * end1.x + b2 * end1.y + d2

    seg2_line1_start = a1 * start2.x + b1 * start2.y + d1
    seg2_line1_end = a1 * end2.x + b1 * end2.y + d1

    if (seg1_line2_start * seg1_line2_end >= 0) or \
            (seg2_line1_start * seg2_line1_end >= 0):
        return False, None

    u = seg1_line2_start / (seg1_line2_start - seg1_line2_end)
    out = start1 + u * seg1

    return True, out


class RingBuffer:
    def __init__(self, arr):
        self.__buffer = arr.copy()
        self.__pointer = 0

    def __repr__(self):
        return repr(self.__buffer)

    def __len__(self):
        return len(self.__buffer)

    def insert(self, val, offset=0):
        self.__buffer.insert(self.__pointer + offset, val)

    def head(self):
        return self.__buffer[0]

    def tail(self):
        return self.__buffer[-1]

    def get(self, offset=0):
        size = len(self.__buffer)
        val = self.__buffer[(self.__pointer + offset) % size]
        return val

    def next(self):
        size = len(self.__buffer)
        self.__pointer = (self.__pointer + 1) % size

    def reset(self):
        self.__pointer = 0

    def find(self, obj):
        try:
            idx = self.__buffer.index(obj)
        except ValueError:
            return None
        return self.__buffer[idx]

    def find_and_next(self, obj):
        size = len(self.__buffer)
        idx = self.__buffer.index(obj)
        self.__pointer = (idx + 1) % size

    def find_and_set(self, obj):
        idx = self.__buffer.index(obj)
        self.__pointer = idx

    def as_list(self):
        return self.__buffer.copy()

    def reverse(self):
        self.__buffer.reverse()
        self.reset()


# clip: reference polygon
# subject: tested polygon
def do_weiler_atherton_cliping(clip, subject, uv_layer, mode):

    clip_uvs = RingBuffer([l[uv_layer].uv.copy() for l in clip.loops])
    if is_polygon_flipped(clip_uvs):
        clip_uvs.reverse()
    subject_uvs = RingBuffer([l[uv_layer].uv.copy() for l in subject.loops])
    if is_polygon_flipped(subject_uvs):
        subject_uvs.reverse()

    common.debug_print("===== Clip UV List =====")
    common.debug_print(clip_uvs)
    common.debug_print("===== Subject UV List =====")
    common.debug_print(subject_uvs)

    # check if clip and subject is overlapped completely
    if is_polygon_same(clip_uvs, subject_uvs):
        polygons = [subject_uvs.as_list()]
        common.debug_print("===== Polygons Overlapped Completely =====")
        common.debug_print(polygons)
        return True, polygons

    # check if subject is in clip
    if is_points_in_polygon(subject_uvs, clip_uvs):
        polygons = [subject_uvs.as_list()]
        return True, polygons

    # check if clip is in subject
    if is_points_in_polygon(clip_uvs, subject_uvs):
        polygons = [subject_uvs.as_list()]
        return True, polygons

    # check if clip and subject is overlapped partially
    intersections = []
    while True:
        subject_uvs.reset()
        while True:
            uv_start1 = clip_uvs.get()
            uv_end1 = clip_uvs.get(1)
            uv_start2 = subject_uvs.get()
            uv_end2 = subject_uvs.get(1)
            intersected, point = is_segment_intersect(uv_start1, uv_end1,
                                                      uv_start2, uv_end2)
            if intersected:
                clip_uvs.insert(point, 1)
                subject_uvs.insert(point, 1)
                intersections.append([point,
                                      [clip_uvs.get(), clip_uvs.get(1)]])
            subject_uvs.next()
            if subject_uvs.get() == subject_uvs.head():
                break
        clip_uvs.next()
        if clip_uvs.get() == clip_uvs.head():
            break

    common.debug_print("===== Intersection List =====")
    common.debug_print(intersections)

    # no intersection, so subject and clip is not overlapped
    if not intersections:
        return False, None

    def get_intersection_pair(intersections, key):
        for sect in intersections:
            if sect[0] == key:
                return sect[1]

        return None

    # make enter/exit pair
    subject_uvs.reset()
    subject_entering = []
    subject_exiting = []
    clip_entering = []
    clip_exiting = []
    intersect_uv_list = []
    while True:
        pair = get_intersection_pair(intersections, subject_uvs.get())
        if pair:
            sub = subject_uvs.get(1) - subject_uvs.get(-1)
            inter = pair[1] - pair[0]
            cross = sub.x * inter.y - inter.x * sub.y
            if cross < 0:
                subject_entering.append(subject_uvs.get())
                clip_exiting.append(subject_uvs.get())
            else:
                subject_exiting.append(subject_uvs.get())
                clip_entering.append(subject_uvs.get())
            intersect_uv_list.append(subject_uvs.get())

        subject_uvs.next()
        if subject_uvs.get() == subject_uvs.head():
            break

    common.debug_print("===== Enter List =====")
    common.debug_print(clip_entering)
    common.debug_print(subject_entering)
    common.debug_print("===== Exit List =====")
    common.debug_print(clip_exiting)
    common.debug_print(subject_exiting)

    # for now, can't handle the situation when fulfill all below conditions
    #        * two faces have common edge
    #        * each face is intersected
    #        * Show Mode is "Part"
    #       so for now, ignore this situation
    if len(subject_entering) != len(subject_exiting):
        if mode == 'FACE':
            polygons = [subject_uvs.as_list()]
            return True, polygons
        return False, None

    def traverse(current_list, entering, exiting, poly, current, other_list):
        result = current_list.find(current)
        if not result:
            return None
        if result != current:
            print("Internal Error")
            return None

        # enter
        if entering.count(current) >= 1:
            entering.remove(current)

        current_list.find_and_next(current)
        current = current_list.get()

        while exiting.count(current) == 0:
            poly.append(current.copy())
            current_list.find_and_next(current)
            current = current_list.get()

        # exit
        poly.append(current.copy())
        exiting.remove(current)

        other_list.find_and_set(current)
        return other_list.get()

    # Traverse
    polygons = []
    current_uv_list = subject_uvs
    other_uv_list = clip_uvs
    current_entering = subject_entering
    current_exiting = subject_exiting

    poly = []
    current_uv = current_entering[0]

    while True:
        current_uv = traverse(current_uv_list, current_entering,
                              current_exiting, poly, current_uv, other_uv_list)

        if current_uv_list == subject_uvs:
            current_uv_list = clip_uvs
            other_uv_list = subject_uvs
            current_entering = clip_entering
            current_exiting = clip_exiting
            common.debug_print("-- Next: Clip --")
        else:
            current_uv_list = subject_uvs
            other_uv_list = clip_uvs
            current_entering = subject_entering
            current_exiting = subject_exiting
            common.debug_print("-- Next: Subject --")

        common.debug_print(clip_entering)
        common.debug_print(clip_exiting)
        common.debug_print(subject_entering)
        common.debug_print(subject_exiting)

        if not clip_entering and not clip_exiting \
                and not subject_entering and not subject_exiting:
            break

    polygons.append(poly)

    common.debug_print("===== Polygons Overlapped Partially =====")
    common.debug_print(polygons)

    return True, polygons


class MUV_UVInspRenderer(bpy.types.Operator):
    """
    Operation class: Render UV Inspection
    No operation (only rendering)
    """

    bl_idname = "uv.muv_uvinsp_renderer"
    bl_description = "Render overlapped/flipped UVs"
    bl_label = "Overlapped/Flipped UV renderer"

    __handle = None

    @staticmethod
    def handle_add(obj, context):
        sie = bpy.types.SpaceImageEditor
        MUV_UVInspRenderer.__handle = sie.draw_handler_add(
            MUV_UVInspRenderer.draw, (obj, context), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_remove():
        if MUV_UVInspRenderer.__handle is not None:
            bpy.types.SpaceImageEditor.draw_handler_remove(
                MUV_UVInspRenderer.__handle, 'WINDOW')
            MUV_UVInspRenderer.__handle = None

    @staticmethod
    def draw(_, context):
        sc = context.scene
        props = sc.muv_props.uvinsp
        prefs = context.user_preferences.addons["uv_magic_uv"].preferences

        # OpenGL configuration
        bgl.glEnable(bgl.GL_BLEND)

        # render overlapped UV
        if sc.muv_uvinsp_show_overlapped:
            color = prefs.uvinsp_overlapped_color
            for info in props.overlapped_info:
                if sc.muv_uvinsp_show_mode == 'PART':
                    for poly in info["polygons"]:
                        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                        bgl.glColor4f(color[0], color[1], color[2], color[3])
                        for uv in poly:
                            x, y = context.region.view2d.view_to_region(
                                uv.x, uv.y)
                            bgl.glVertex2f(x, y)
                        bgl.glEnd()
                elif sc.muv_uvinsp_show_mode == 'FACE':
                    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                    bgl.glColor4f(color[0], color[1], color[2], color[3])
                    for uv in info["subject_uvs"]:
                        x, y = context.region.view2d.view_to_region(uv.x, uv.y)
                        bgl.glVertex2f(x, y)
                    bgl.glEnd()

        # render flipped UV
        if sc.muv_uvinsp_show_flipped:
            color = prefs.uvinsp_flipped_color
            for info in props.flipped_info:
                if sc.muv_uvinsp_show_mode == 'PART':
                    for poly in info["polygons"]:
                        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                        bgl.glColor4f(color[0], color[1], color[2], color[3])
                        for uv in poly:
                            x, y = context.region.view2d.view_to_region(
                                uv.x, uv.y)
                            bgl.glVertex2f(x, y)
                        bgl.glEnd()
                elif sc.muv_uvinsp_show_mode == 'FACE':
                    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
                    bgl.glColor4f(color[0], color[1], color[2], color[3])
                    for uv in info["uvs"]:
                        x, y = context.region.view2d.view_to_region(uv.x, uv.y)
                        bgl.glVertex2f(x, y)
                    bgl.glEnd()


def is_polygon_flipped(points):
    area = 0.0
    for i in range(len(points)):
        uv1 = points.get(i)
        uv2 = points.get(i + 1)
        a = uv1.x * uv2.y - uv1.y * uv2.x
        area = area + a
    if area < 0:
        # clock-wise
        return True
    return False


def is_point_in_polygon(point, subject_points):
    count = 0
    for i in range(len(subject_points)):
        uv_start1 = subject_points.get(i)
        uv_end1 = subject_points.get(i + 1)
        uv_start2 = point
        uv_end2 = Vector((1000000.0, point.y))
        intersected, _ = is_segment_intersect(uv_start1, uv_end1,
                                              uv_start2, uv_end2)
        if intersected:
            count = count + 1

    return count % 2


def is_points_in_polygon(points, subject_points):
    for i in range(len(points)):
        internal = is_point_in_polygon(points.get(i), subject_points)
        if not internal:
            return False

    return True


def get_overlapped_uv_info(bm, faces, uv_layer, mode):
    # at first, check island overlapped
    isl = common.get_island_info_from_faces(bm, faces, uv_layer)
    overlapped_isl_pairs = []
    for i, i1 in enumerate(isl):
        for i2 in isl[i + 1:]:
            if (i1["max"].x < i2["min"].x) or (i2["max"].x < i1["min"].x) or \
               (i1["max"].y < i2["min"].y) or (i2["max"].y < i1["min"].y):
                continue
            overlapped_isl_pairs.append([i1, i2])

    # next, check polygon overlapped
    overlapped_uvs = []
    for oip in overlapped_isl_pairs:
        for clip in oip[0]["faces"]:
            f_clip = clip["face"]
            for subject in oip[1]["faces"]:
                f_subject = subject["face"]

                # fast operation, apply bounding box algorithm
                if (clip["max_uv"].x < subject["min_uv"].x) or \
                   (subject["max_uv"].x < clip["min_uv"].x) or \
                   (clip["max_uv"].y < subject["min_uv"].y) or \
                   (subject["max_uv"].y < clip["min_uv"].y):
                    continue

                # slow operation, apply Weiler-Atherton cliping algorithm
                result, polygons = do_weiler_atherton_cliping(f_clip,
                                                              f_subject,
                                                              uv_layer, mode)
                if result:
                    subject_uvs = [l[uv_layer].uv.copy()
                                   for l in f_subject.loops]
                    overlapped_uvs.append({"clip_face": f_clip,
                                           "subject_face": f_subject,
                                           "subject_uvs": subject_uvs,
                                           "polygons": polygons})

    return overlapped_uvs


def get_flipped_uv_info(faces, uv_layer):
    flipped_uvs = []
    for f in faces:
        polygon = RingBuffer([l[uv_layer].uv.copy() for l in f.loops])
        if is_polygon_flipped(polygon):
            uvs = [l[uv_layer].uv.copy() for l in f.loops]
            flipped_uvs.append({"face": f, "uvs": uvs,
                                "polygons": [polygon.as_list()]})

    return flipped_uvs


def update_uvinsp_info(context):
    sc = context.scene
    props = sc.muv_props.uvinsp

    obj = context.active_object
    bm = bmesh.from_edit_mesh(obj.data)
    if common.check_version(2, 73, 0) >= 0:
        bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    if context.tool_settings.use_uv_select_sync:
        sel_faces = [f for f in bm.faces]
    else:
        sel_faces = [f for f in bm.faces if f.select]
    props.overlapped_info = get_overlapped_uv_info(bm, sel_faces, uv_layer,
                                                   sc.muv_uvinsp_show_mode)
    props.flipped_info = get_flipped_uv_info(sel_faces, uv_layer)


class MUV_UVInspUpdate(bpy.types.Operator):
    """
    Operation class: Update
    """

    bl_idname = "uv.muv_uvinsp_update"
    bl_label = "Update"
    bl_description = "Update Overlapped/Flipped UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_uvinsp_info(context)

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


class MUV_UVInspDisplay(bpy.types.Operator):
    """
    Operation class: Display
    """

    bl_idname = "uv.muv_uvinsp_display"
    bl_label = "Display"
    bl_description = "Display Overlapped/Flipped UV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sc = context.scene
        props = sc.muv_props.uvinsp
        if not props.display_running:
            update_uvinsp_info(context)
            MUV_UVInspRenderer.handle_add(self, context)
            props.display_running = True
        else:
            MUV_UVInspRenderer.handle_remove()
            props.display_running = False

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


class MUV_UVInspSelectOverlapped(bpy.types.Operator):
    """
    Operation class: Select faces which have overlapped UVs
    """

    bl_idname = "uv.muv_uvinsp_select_overlapped"
    bl_label = "Overlapped"
    bl_description = "Select faces which have overlapped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()

        if context.tool_settings.use_uv_select_sync:
            sel_faces = [f for f in bm.faces]
        else:
            sel_faces = [f for f in bm.faces if f.select]

        overlapped_info = get_overlapped_uv_info(bm, sel_faces, uv_layer,
                                                 'FACE')

        for info in overlapped_info:
            if context.tool_settings.use_uv_select_sync:
                info["subject_face"].select = True
            else:
                for l in info["subject_face"].loops:
                    l[uv_layer].select = True

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


class MUV_UVInspSelectFlipped(bpy.types.Operator):
    """
    Operation class: Select faces which have flipped UVs
    """

    bl_idname = "uv.muv_uvinsp_select_flipped"
    bl_label = "Flipped"
    bl_description = "Select faces which have flipped UVs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()

        if context.tool_settings.use_uv_select_sync:
            sel_faces = [f for f in bm.faces]
        else:
            sel_faces = [f for f in bm.faces if f.select]

        flipped_info = get_flipped_uv_info(sel_faces, uv_layer)

        for info in flipped_info:
            if context.tool_settings.use_uv_select_sync:
                info["face"].select = True
            else:
                for l in info["face"].loops:
                    l[uv_layer].select = True

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
