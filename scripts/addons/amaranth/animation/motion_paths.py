# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Bone Motion Paths:

Match Frame Range + Clear All Paths

* Clear All Paths:
Silly operator to loop through all bones and clear their paths, useful
when having hidden bones (othrewise you have to go through each one of
them and clear manually)

*Match Current Frame Range:
Set the current frame range as motion path range.

Both requests by Hjalti from Project Pampa
Thanks to Bassam Kurdali for helping finding out the weirdness behind
Motion Paths bpy.

Developed during Caminandes Open Movie Project
"""

import bpy


class AMTH_POSE_OT_paths_clear_all(bpy.types.Operator):

    """Clear motion paths from all bones"""
    bl_idname = "pose.paths_clear_all"
    bl_label = "Clear All Motion Paths"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "POSE"

    def execute(self, context):
        # silly but works
        for b in context.object.data.bones:
            b.select = True
            bpy.ops.pose.paths_clear()
            b.select = False
        return {"FINISHED"}


class AMTH_POSE_OT_paths_frame_match(bpy.types.Operator):

    """Match Start/End frame of scene to motion path range"""
    bl_idname = "pose.paths_frame_match"
    bl_label = "Match Frame Range"
    bl_options = {"UNDO"}

    def execute(self, context):
        avs = context.object.pose.animation_visualization
        scene = context.scene

        if avs.motion_path.type == "RANGE":
            if scene.use_preview_range:
                avs.motion_path.frame_start = scene.frame_preview_start
                avs.motion_path.frame_end = scene.frame_preview_end
            else:
                avs.motion_path.frame_start = scene.frame_start
                avs.motion_path.frame_end = scene.frame_end

        else:
            if scene.use_preview_range:
                avs.motion_path.frame_before = scene.frame_preview_start
                avs.motion_path.frame_after = scene.frame_preview_end
            else:
                avs.motion_path.frame_before = scene.frame_start
                avs.motion_path.frame_after = scene.frame_end

        return {"FINISHED"}


def pose_motion_paths_ui(self, context):

    layout = self.layout
    scene = context.scene
    avs = context.object.pose.animation_visualization
    if context.active_pose_bone:
        mpath = context.active_pose_bone.motion_path
    layout.separator()
    layout.label(text="Motion Paths Extras:")

    split = layout.split()

    col = split.column(align=True)

    if context.selected_pose_bones:
        if mpath:
            sub = col.row(align=True)
            sub.operator(
                "pose.paths_update", text="Update Path", icon="BONE_DATA")
            sub.operator("pose.paths_clear", text="", icon="X")
        else:
            col.operator(
                "pose.paths_calculate",
                text="Calculate Path",
                icon="BONE_DATA")
    else:
        col.label(text="Select Bones First", icon="ERROR")

    col = split.column(align=True)
    col.operator(
        AMTH_POSE_OT_paths_frame_match.bl_idname,
        text="Set Preview Frame Range" if scene.use_preview_range else "Set Frame Range",
        icon="PREVIEW_RANGE" if scene.use_preview_range else "TIME")

    col = layout.column()
    row = col.row(align=True)

    if avs.motion_path.type == "RANGE":
        row.prop(avs.motion_path, "frame_start", text="Start")
        row.prop(avs.motion_path, "frame_end", text="End")
    else:
        row.prop(avs.motion_path, "frame_before", text="Before")
        row.prop(avs.motion_path, "frame_after", text="After")

    layout.separator()
    layout.operator(AMTH_POSE_OT_paths_clear_all.bl_idname, icon="X")


def register():
    bpy.utils.register_class(AMTH_POSE_OT_paths_clear_all)
    bpy.utils.register_class(AMTH_POSE_OT_paths_frame_match)
    bpy.types.DATA_PT_display.append(pose_motion_paths_ui)


def unregister():
    bpy.utils.unregister_class(AMTH_POSE_OT_paths_clear_all)
    bpy.utils.unregister_class(AMTH_POSE_OT_paths_frame_match)
    bpy.types.DATA_PT_display.remove(pose_motion_paths_ui)
