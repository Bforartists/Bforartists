"""BoneCraft VRChat — Physics Workshop operators.

Standalone workspace panels removed — they duplicated the VRChat sidebar
hub's Hair Physics subtab.  Operators and UIList kept so other modules
can invoke physics preview without re-importing from a panel file.
"""

import bpy
from bpy.types import UIList, Operator
from bpy.props import IntProperty
import math

from boneforge.core import active_armature
from boneforge.i18n import T

import logging

logger = logging.getLogger(__name__)


class BF_OT_VRC_PlayPhysPreview(Operator):
    """Start a simple spring-damper simulation preview on the selected PhysBone chain."""

    bl_idname = "boneforge.vrc_play_simulation"
    bl_label = "Play Physics Preview"
    bl_description = "Start physics simulation preview"

    _timer = None
    _handler = None
    _frame_count = 0
    _bone_rest_poses = {}

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def modal(self, context, event):
        if event.type == "TIMER":
            self._frame_count += 1
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        arm = active_armature(context)
        if not arm or not arm.pose:
            self.report({'ERROR'}, "No armature or pose available")
            return {'CANCELLED'}

        self._frame_count = 0
        self._bone_rest_poses = {}

        bones = arm.pose.bones
        if not bones:
            self.report({'ERROR'}, "Armature has no bones")
            return {'CANCELLED'}

        for bone in bones:
            self._bone_rest_poses[bone.name] = {
                'rotation': bone.rotation_quaternion.copy(),
                'location': bone.location.copy(),
            }

        def frame_change_handler(scene):
            frame = scene.frame_current
            time = frame / 24.0

            for bone in bones:
                if bone.name not in self._bone_rest_poses:
                    continue

                rest = self._bone_rest_poses[bone.name]
                frequency = 2.0
                damping = 0.1
                amplitude = 0.3

                decay = math.exp(-damping * time)
                oscillation = amplitude * decay * math.sin(2 * math.pi * frequency * time)

                from mathutils import Quaternion
                try:
                    rot_offset = Quaternion((math.cos(oscillation/2), 0, math.sin(oscillation/2), 0))
                    bone.rotation_quaternion = rest['rotation'] @ rot_offset
                except (ValueError, RuntimeError):
                    pass

        bpy.app.handlers.frame_change_pre.append(frame_change_handler)
        self._handler = frame_change_handler

        context.scene['_bf_phys_preview_handler'] = self._handler
        context.scene['_bf_phys_preview_bones'] = self._bone_rest_poses

        self.report({'INFO'}, "Preview started — approximate simulation only")
        return {'FINISHED'}


class BF_OT_VRC_StopPhysPreview(Operator):
    """Stop the physics preview and reset bones to rest pose."""

    bl_idname = "boneforge.vrc_stop_simulation"
    bl_label = "Stop Physics Preview"
    bl_description = "Stop physics simulation preview"

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def execute(self, context):
        arm = active_armature(context)
        if not arm or not arm.pose:
            self.report({'ERROR'}, "No armature or pose available")
            return {'CANCELLED'}

        handler = context.scene.get('_bf_phys_preview_handler')
        if handler:
            if handler in bpy.app.handlers.frame_change_pre:
                bpy.app.handlers.frame_change_pre.remove(handler)

        bone_poses = context.scene.get('_bf_phys_preview_bones', {})
        for bone in arm.pose.bones:
            if bone.name in bone_poses:
                rest = bone_poses[bone.name]
                bone.rotation_quaternion = rest['rotation']
                bone.location = rest['location']

        if '_bf_phys_preview_handler' in context.scene:
            del context.scene['_bf_phys_preview_handler']
        if '_bf_phys_preview_bones' in context.scene:
            del context.scene['_bf_phys_preview_bones']

        self.report({'INFO'}, "Preview stopped")
        return {'FINISHED'}


class BF_UL_VRC_PhysBoneChainList(UIList):
    """UIList for displaying VRChat physics bone chains."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if hasattr(item, "root_bone"):
            row.label(text=item.root_bone if item.root_bone else "(unnamed)", icon="BONE_DATA")
        else:
            row.label(text=T("Chain"))

        if hasattr(item, "length"):
            row.label(text=f"L:{item.length}")

        if hasattr(item, "preset"):
            row.label(text=item.preset or "Custom", icon="PREFERENCES")

        row.label(text="", icon="CHECKMARK")


def register_scene_properties():
    if not hasattr(bpy.types.Scene, "boneforge_vrchat_active_chain_index"):
        bpy.types.Scene.boneforge_vrchat_active_chain_index = IntProperty(
            name="Active Chain Index",
            description="Index of the selected physics chain",
            default=0,
            min=0,
        )


def unregister_scene_properties():
    if hasattr(bpy.types.Scene, "boneforge_vrchat_active_chain_index"):
        del bpy.types.Scene.boneforge_vrchat_active_chain_index


classes = (
    BF_OT_VRC_PlayPhysPreview,
    BF_OT_VRC_StopPhysPreview,
    BF_UL_VRC_PhysBoneChainList,
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft] Failed to register {cls.__name__}: {e}")
    register_scene_properties()


def unregister():
    unregister_scene_properties()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft] Failed to unregister {cls.__name__}: {e}")
