# Copyright 2019 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy

def simulate_stash(obj, track_name, action, start_frame=None):
    # Simulate stash :
    # * add a track
    # * add an action on track
    # * lock & mute the track
    # * remove active action from object
    tracks = obj.animation_data.nla_tracks
    new_track = tracks.new(prev=None)
    new_track.name = track_name
    if start_frame is None:
        start_frame = bpy.context.scene.frame_start
    strip = new_track.strips.new(action.name, start_frame, action)
    new_track.lock = True
    new_track.mute = True
    obj.animation_data.action = None

def restore_animation_on_object(obj, anim_name):
    if not getattr(obj, 'animation_data', None):
        return

    for track in obj.animation_data.nla_tracks:
        if track.name != anim_name:
            continue
        if not track.strips:
            continue

        obj.animation_data.action = track.strips[0].action
        return

    obj.animation_data.action = None

def make_fcurve(action, co, data_path, index=0, group_name=None, interpolation=None):
    try:
        fcurve = action.fcurves.new(data_path=data_path, index=index)
    except:
        # Some non valid files can have multiple target path
        return None

    if group_name:
        if group_name not in action.groups:
            action.groups.new(group_name)
        group = action.groups[group_name]
        fcurve.group = group

    # Set the default keyframe type in the prefs, then make keyframes
    prefs = bpy.context.preferences.edit
    try:
        orig_interp_type = prefs.keyframe_new_interpolation_type
        orig_handle_type = prefs.keyframe_new_handle_type

        if interpolation == 'CUBICSPLINE':
            prefs.keyframe_new_interpolation_type = 'BEZIER'
            prefs.keyframe_new_handle_type = 'AUTO'
        elif interpolation == 'STEP':
            prefs.keyframe_new_interpolation_type = 'CONSTANT'
        elif interpolation == 'LINEAR':
            prefs.keyframe_new_interpolation_type = 'LINEAR'

        fcurve.keyframe_points.add(len(co) // 2)

    finally:
        # Restore original prefs
        prefs.keyframe_new_interpolation_type = orig_interp_type
        prefs.keyframe_new_handle_type = orig_handle_type

    fcurve.keyframe_points.foreach_set('co', co)
    fcurve.update() # force updating tangents (this may change when tangent will be managed)

    return fcurve

