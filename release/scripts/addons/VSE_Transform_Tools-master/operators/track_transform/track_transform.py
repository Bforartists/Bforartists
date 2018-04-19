import bpy
from ..utils.selection import get_input_tree
import math


class TrackTransform(bpy.types.Operator):
    """
    ![Demo](https://i.imgur.com/nWto3hH.gif)

    Use a pair of track points to pin a strip to another. The UI for
    this tool is located in the menu to the right of the sequencer in
    the "Tools" submenu.

    ![UI](https://i.imgur.com/wEZLu8a.jpg)

    To pin rotation and/or scale, you must use 2 tracking points.

    More information on [this youtube video](https://www.youtube.com/watch?v=X885Uv1dzFY)
    """
    bl_idname = "vse_transform_tools.track_transform"
    bl_label = "Track Transform"
    bl_description = "Generate a Transform Strip with Animated Position/Rotation/Scale to Match Tracker(s)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene

        if (scene.vse_transform_tools_tracker_1 != "None" and
                scene.sequence_editor and
                scene.sequence_editor.active_strip and
                scene.sequence_editor.active_strip.type == "TRANSFORM"):
            return True
        return False

    def execute(self, context):
        scene = context.scene
        res_x = scene.render.resolution_x
        res_y = scene.render.resolution_y

        tracker_names = []

        for movieclip in bpy.data.movieclips:
            for track in movieclip.tracking.tracks:
                if track.name == scene.vse_transform_tools_tracker_1:
                    pos_track = track
                    break

        start_frame = scene.frame_current

        offset_x = -1
        offset_y = -1
        for marker in pos_track.markers:
            if marker.frame == scene.frame_current:
                offset_x = marker.co.x * res_x
                offset_y = marker.co.y * res_y
                break

        if offset_x == -1 or offset_y == -1:
            offset_x = pos_track.markers[0].co.x * res_x
            offset_y = pos_track.markers[0].co.y * res_y

        active = scene.sequence_editor.active_strip

        if active.translation_unit == "PERCENT":
            active.translate_start_x = (active.translate_start_x - ((offset_x / res_x) * 100) + 50) / 2
            active.translate_start_y = (active.translate_start_y - ((offset_y / res_y) * 100) + 50) / 2

        else:
            active.translate_start_x = ((active.translate_start_x + (res_x / 2)) - offset_x) / 2
            active.translate_start_y = ((active.translate_start_y + (res_y / 2)) - offset_y) / 2

        active.scale_start_x = active.scale_start_x / 2
        active.scale_start_y = active.scale_start_y / 2

        for strip in context.selected_sequences:
            if not strip == active:
                strip.select = False

        bpy.ops.sequencer.effect_strip_add(type="TRANSFORM")

        transform_strip = context.scene.sequence_editor.active_strip
        transform_strip.name = "[TRACKED]-%s" % strip.name
        transform_strip.blend_type = 'ALPHA_OVER'
        transform_strip.use_uniform_scale = True
        transform_strip.scale_start_x = 2.0

        tree = get_input_tree(transform_strip)[1::]
        for child in tree:
            child.mute = True

        for marker in pos_track.markers:
            scene.frame_current = marker.frame
            transform_strip.translate_start_x = ((((marker.co.x * res_x) - (res_x / 2)) / res_x) * 100)
            transform_strip.translate_start_y = ((((marker.co.y * res_y) - (res_y / 2)) / res_y) * 100)

            transform_strip.keyframe_insert(
                data_path="translate_start_x", frame=scene.frame_current)
            transform_strip.keyframe_insert(
                data_path="translate_start_y", frame=scene.frame_current)

        ref_track = None
        if scene.vse_transform_tools_use_rotation or scene.vse_transform_tools_use_scale:
            for movieclip in bpy.data.movieclips:
                for track in movieclip.tracking.tracks:
                    if track.name == scene.vse_transform_tools_tracker_2:
                        ref_track = track
                        break

        if scene.vse_transform_tools_use_rotation and ref_track:
            for marker in ref_track.markers:
                if marker.frame == start_frame:

                    p1 = None
                    for pos_marker in pos_track.markers:
                        if pos_marker.frame == marker.frame:
                            p1 = (pos_marker.co.x * res_x, pos_marker.co.y * res_y)
                            break

                    if not p1:
                        return {"FINISHED"}

                    p2 = (marker.co.x * res_x, marker.co.y * res_y)
                    offset_angle = calculate_angle(p1, p2)
                    break

            for marker in ref_track.markers:
                scene.frame_current = marker.frame
                p1 = None
                for pos_marker in pos_track.markers:
                    if pos_marker.frame == marker.frame:
                        p1 = (pos_marker.co.x * res_x, pos_marker.co.y * res_y)
                        break
                if not p1:
                    break

                p2 = (marker.co.x * res_x, marker.co.y * res_y)
                angle = calculate_angle(p1, p2) - offset_angle

                transform_strip.rotation_start = angle
                transform_strip.keyframe_insert(
                    data_path="rotation_start", frame=scene.frame_current)

        if scene.vse_transform_tools_use_scale and ref_track:
            for marker in ref_track.markers:
                if marker.frame == start_frame:

                    p1 = None
                    for pos_marker in pos_track.markers:
                        if pos_marker.frame == marker.frame:
                            p1 = (pos_marker.co.x * res_x, pos_marker.co.y * res_y)
                            break

                    if not p1:
                        return {"FINISHED"}

                    p2 = (marker.co.x * res_x, marker.co.y * res_y)
                    init_distance = distance_formula(p1, p2)

            for marker in ref_track.markers:
                scene.frame_current = marker.frame
                p1 = None
                for pos_marker in pos_track.markers:
                    if pos_marker.frame == marker.frame:
                        p1 = (pos_marker.co.x * res_x, pos_marker.co.y * res_y)
                        break
                if not p1:
                    break

                p2 = (marker.co.x * res_x, marker.co.y * res_y)
                distance = distance_formula(p1, p2)
                scl = (distance / init_distance) * 2.0
                transform_strip.scale_start_x = scl
                transform_strip.keyframe_insert(
                    data_path="scale_start_x", frame=scene.frame_current)

        scene.frame_current = start_frame

        return {'FINISHED'}


def calculate_angle(p1, p2):
    """
    Calculate the angle formed by p1, p2, and the x axis

    Parameters
    ----------
    p1 : list of float
        X & Y coordinates
    p2 : list of float
        X & Y coordinates

    Returns
    -------
    angle : float
    """
    a = p2[1] - p1[1]
    b = p2[0] - p1[0]

    p1p2 = math.degrees(math.atan2(a, b))

    return p1p2


def distance_formula(p1, p2):
    """
    Calculate the distance between 2 points on a 2D Cartesian coordinate plane
    """
    x = p2[0] - p1[0]
    y = p2[1] - p1[1]

    distance = math.sqrt(x**2 + y**2)
    return distance
