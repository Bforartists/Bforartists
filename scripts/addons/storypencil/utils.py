# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import math


def redraw_areas_by_type(window, area_type, region_type='WINDOW'):
    """Redraw `window`'s areas matching the given `area_type` and optionnal `region_type`."""
    for area in window.screen.areas:
        if area.type == area_type:
            for region in area.regions:
                if region.type == region_type:
                    region.tag_redraw()


def redraw_all_areas_by_type(context, area_type, region_type='WINDOW'):
    """Redraw areas in all windows matching the given `area_type` and optionnal `region_type`."""
    for window in context.window_manager.windows:
        redraw_areas_by_type(window, area_type, region_type)


def get_selected_keyframes(context):
    """Get list of selected keyframes for any object in the scene. """
    keys = []

    for ob in context.scene.objects:
        if ob.type == 'GPENCIL':
            for gpl in ob.data.layers:
                for gpf in gpl.frames:
                    if gpf.select:
                        keys.append(gpf.frame_number)

        elif ob.animation_data is not None and ob.animation_data.action is not None:
            action = ob.animation_data.action
            for fcu in action.fcurves:
                for kp in fcu.keyframe_points:
                    if kp.select_control_point:
                        keys.append(int(kp.co[0]))

    keys.sort()
    unique_keys = list(set(keys))
    return unique_keys


def find_collections_recursive(root, collections=None):
    # Initialize the result once
    if collections is None:
        collections = []

    def recurse(parent, result):
        result.append(parent)
        # Look over children at next level
        for child in parent.children:
            recurse(child, result)

    recurse(root, collections)

    return collections


def get_keyframe_list(scene, frame_start, frame_end):
    """Get list of frames for any gpencil object in the scene and meshes. """
    keys = []
    root = scene.view_layers[0].layer_collection
    collections = find_collections_recursive(root)

    for laycol in collections:
        if laycol.exclude is True or laycol.collection.hide_render is True:
            continue
        for ob in laycol.collection.objects:
            if ob.hide_render:
                continue
            if ob.type == 'GPENCIL':
                for gpl in ob.data.layers:
                    if gpl.hide:
                        continue
                    for gpf in gpl.frames:
                        if frame_start <= gpf.frame_number <= frame_end:
                            keys.append(gpf.frame_number)

            # Animation at object level
            if ob.animation_data is not None and ob.animation_data.action is not None:
                action = ob.animation_data.action
                for fcu in action.fcurves:
                    for kp in fcu.keyframe_points:
                        if frame_start <= int(kp.co[0]) <= frame_end:
                            keys.append(int(kp.co[0]))

            # Animation at datablock level
            if ob.type != 'GPENCIL':
                data = ob.data
                if data and data.animation_data is not None and data.animation_data.action is not None:
                    action = data.animation_data.action
                    for fcu in action.fcurves:
                        for kp in fcu.keyframe_points:
                            if frame_start <= int(kp.co[0]) <= frame_end:
                                keys.append(int(kp.co[0]))

    # Scene Markers
    for m in scene.timeline_markers:
        if frame_start <= m.frame <= frame_end and m.camera is not None:
            keys.append(int(m.frame))

    # If no animation or markers, must add first frame
    if len(keys) == 0:
        keys.append(int(frame_start))

    unique_keys = list(set(keys))
    unique_keys.sort()
    return unique_keys
