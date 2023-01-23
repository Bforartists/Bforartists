# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from typing import List, Sequence, Tuple
from bpy.types import (
    Operator,
)


def send_sound_strip(s, dest_scn):
    '''recreate sound strip in another scene
    :dest_scn: scene destination
    :return: newly create sound strip
    '''

    if s.type != 'SOUND':
        return
    vse = dest_scn.sequence_editor
    ns = vse.sequences.new_sound(name=s.name, filepath=s.sound.filepath, channel=s.channel, frame_start=int(s.frame_start))
    ns.sound = s.sound # reget the same sound source

    for attr in ('pitch',
                 'pan',
                 'show_waveform',
                 'speed_factor',
                 'volume',
                 'mute'):
        if hasattr(s, attr):
            setattr(ns, attr, getattr(s, attr))
    if ns.volume == 0:
        ns.volume = 1
    return ns

def get_all_overlapping_sound_strip(scn_strip, skip_mute=True):
    """return array of all sound strips for this strip"""
    if scn_strip.type != 'SCENE':
        return

    src_scn = scn_strip.id_data
    vse = src_scn.sequence_editor
    overlapping_sounds = []
    for s in vse.sequences:
        if s.type != 'SOUND':
            continue
        if skip_mute and s.mute:
            continue

        if (s.frame_final_end - 1 <  scn_strip.frame_final_start)\
            or (s.frame_final_start - 1 > scn_strip.frame_final_end):
            continue

        overlapping_sounds.append(s)

    return overlapping_sounds

def delete_sounds(scene):
    for st in reversed(scene.sequence_editor.sequences):
        if st.type == 'SOUND':
            scene.sequence_editor.sequences.remove(st)

def get_scene_frame_from_sequencer_frame(scn_strip, sound) -> float:
    """return frame in scene referential"""
    return sound.frame_start - scn_strip.frame_start + scn_strip.scene.frame_start

def send_sound_to_strip_scene(scn_strip, clear_sequencer=True, skip_mute=True):
    """Add sounds to strip scene"""
    if scn_strip.type != 'SCENE':
        return
    tgt_scene = scn_strip.scene

    sounds = get_all_overlapping_sound_strip(scn_strip, skip_mute=skip_mute)
    if not sounds:
        return

    # Clear sounds if exists in scene vse already
    if clear_sequencer:
        delete_sounds(tgt_scene)

    print(f'Duplicating sounds in {tgt_scene.name}:')
    for s in sounds:
        new_start = get_scene_frame_from_sequencer_frame(scn_strip, s)
        ns = send_sound_strip(s, tgt_scene)
        if ns:
            ns.frame_start = new_start
            ns.frame_offset_start = s.frame_offset_start
            ns.frame_final_duration = s.frame_final_duration

    return sounds


def dispatch_sounds_in_scenes(selected_scn_only=True, skip_mute=True):
    """Main function to duplicate sounds in strip scenes"""
    edit_scene = bpy.context.scene
    edit = edit_scene.sequence_editor

    ct = 0
    for strip in edit.sequences:
        if strip.type != 'SCENE':
            continue

        if selected_scn_only and not strip.select:
            continue

        sounds = send_sound_to_strip_scene(strip, skip_mute=skip_mute)
        if sounds:
            ct += 1

    if ct:
        print('INFO', f'Sound duplicated in {ct} scenes')
    else:
        print('ERROR', f'No duplication occured')


class STORYPENCIL_OT_duplicate_sound_in_edit_scene(Operator):
    bl_idname = "storypencil.duplicate_sound_in_edit_scene"
    bl_label = "Sounds To Scenes"
    bl_description = "Copy sound strips from VSE to the source scenes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != 'SEQUENCER':
            return False

        return True

    def execute(self, context):
        scene = context.scene
        dispatch_sounds_in_scenes(
            selected_scn_only=scene.storypencil_selected_scn_only,
            skip_mute=scene.storypencil_skip_sound_mute)

        bpy.ops.sequencer.reload()

        return {'FINISHED'}
