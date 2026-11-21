# --- ANIMATION LAYER PART ASSIGNMENT OPERATORS ---
"""Operators for assigning and managing bones/parts on animation layers.

Provides workflows for:
    - Assigning selected pose bones to the active layer
    - Removing bone assignments
    - Assigning bones by pattern/naming convention
    - Auto-partitioning by rig hierarchy (upper/lower body, etc.)
    - Viewing which bones are assigned to which layers
"""

from __future__ import annotations

import re

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty

from ..core.logging import get_logger
from ..core.p11_properties import get_p11, PRESET_ITEMS
from ..core import p11_layer_engine as engine
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected
from ..core.helpers import report_failure

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Poll helpers
# ---------------------------------------------------------------------------

def _active_layer_valid(context: bpy.types.Context) -> bool:
    p11 = get_p11(context)
    if p11 is None:
        return False
    return 0 <= p11.active_layer_index < len(p11.layers)


def _in_pose_mode(context: bpy.types.Context) -> bool:
    obj = context.active_object
    return (
        obj is not None
        and obj.type == "ARMATURE"
        and context.mode == "POSE"
    )


# ---------------------------------------------------------------------------
# Assign Selected Bones
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_assign_selected(bpy.types.Operator):
    """Assign currently selected pose bones to the active layer"""

    bl_idname = "animassist.p11_assign_selected"
    bl_label = "Assign Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context) and _in_pose_mode(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if layer.locked:
            self.report({'WARNING'}, "Layer is locked")
            return {'CANCELLED'}

        selected = context.selected_pose_bones or []
        if not selected:
            self.report({'WARNING'}, "No pose bones selected")
            return {'CANCELLED'}

        added = 0
        for bone in selected:
            if not engine.is_bone_on_layer(layer, bone.name) or len(layer.assigned_bones) == 0:
                # Check if already explicitly assigned.
                existing = {b.bone_name for b in layer.assigned_bones}
                if bone.name not in existing:
                    ba = layer.assigned_bones.add()
                    ba.bone_name = bone.name
                    added += 1

        p11.eval_generation += 1
        self.report({'INFO'}, f"Assigned {added} bones to '{layer.name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Remove Bone from Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_remove_bone(bpy.types.Operator):
    """Remove a bone from the active layer's assignment"""

    bl_idname = "animassist.p11_remove_bone"
    bl_label = "Remove Bone"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(  # type: ignore[valid-type]
        name="Bone Index",
        description="Index of the bone assignment to remove",
        default=0,
        min=0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if layer.locked:
            self.report({'WARNING'}, "Layer is locked")
            return {'CANCELLED'}

        if 0 <= self.index < len(layer.assigned_bones):
            name = layer.assigned_bones[self.index].bone_name
            layer.assigned_bones.remove(self.index)
            p11.eval_generation += 1
            self.report({'INFO'}, f"Removed '{name}' from '{layer.name}'")
            return {'FINISHED'}

        return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Remove Selected Bones from Layer
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_remove_selected(bpy.types.Operator):
    """Remove currently selected pose bones from the active layer"""

    bl_idname = "animassist.p11_remove_selected"
    bl_label = "Remove Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context) and _in_pose_mode(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if layer.locked:
            self.report({'WARNING'}, "Layer is locked")
            return {'CANCELLED'}

        selected_names = {b.name for b in (context.selected_pose_bones or [])}
        removed = 0
        # Iterate backwards for safe removal.
        for i in range(len(layer.assigned_bones) - 1, -1, -1):
            if layer.assigned_bones[i].bone_name in selected_names:
                layer.assigned_bones.remove(i)
                removed += 1

        p11.eval_generation += 1
        self.report({'INFO'}, f"Removed {removed} bones from '{layer.name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Clear All Assignments
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_clear_assignments(bpy.types.Operator):
    """Clear all bone assignments (make layer affect all bones)"""

    bl_idname = "animassist.p11_clear_assignments"
    bl_label = "Clear Assignments"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p11 = get_p11(context)
        if not _active_layer_valid(context):
            return False
        layer = p11.layers[p11.active_layer_index]
        return len(layer.assigned_bones) > 0

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if layer.locked:
            self.report({'WARNING'}, "Layer is locked")
            return {'CANCELLED'}

        layer.assigned_bones.clear()
        p11.eval_generation += 1
        self.report({'INFO'}, f"Cleared all assignments on '{layer.name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Assign by Pattern
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_assign_by_pattern(bpy.types.Operator):
    """Assign bones matching a name pattern to the active layer"""

    bl_idname = "animassist.p11_assign_by_pattern"
    bl_label = "Assign by Pattern"
    bl_options = {'REGISTER', 'UNDO'}

    pattern: StringProperty(  # type: ignore[valid-type]
        name="Pattern",
        description=(
            "Regex pattern to match bone names "
            "(e.g. 'arm|hand|finger' for arm bones, "
            "'spine|chest|neck|head' for upper body)"
        ),
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context) and _in_pose_mode(context)

    def invoke(self, context: bpy.types.Context, event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if layer.locked:
            self.report({'WARNING'}, "Layer is locked")
            return {'CANCELLED'}

        if not self.pattern:
            self.report({'WARNING'}, "No pattern specified")
            return {'CANCELLED'}

        obj = context.active_object
        try:
            regex = re.compile(self.pattern, re.IGNORECASE)
        except re.error as e:
            report_failure(self, "The pattern is not a valid regular expression", "Fix the pattern and try again", e, detail=str(e))
            return {'CANCELLED'}

        existing = {b.bone_name for b in layer.assigned_bones}
        added = 0
        for bone in obj.pose.bones:
            if regex.search(bone.name) and bone.name not in existing:
                ba = layer.assigned_bones.add()
                ba.bone_name = bone.name
                added += 1

        p11.eval_generation += 1
        self.report({'INFO'}, f"Assigned {added} bones matching '{self.pattern}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Auto-Partition Preset (Upper/Lower, Face/Body, Left/Right, etc.)
# ---------------------------------------------------------------------------

# Bone name heuristics for auto-partitioning.
_UPPER_BODY_PATTERNS = re.compile(
    r"(spine|chest|neck|head|shoulder|arm|elbow|wrist|hand|finger|thumb|"
    r"clavicle|collar|breast|pec|torso|upper_body)",
    re.IGNORECASE,
)
_LOWER_BODY_PATTERNS = re.compile(
    r"(hip|pelvis|thigh|knee|shin|calf|ankle|foot|toe|leg|lower_body|"
    r"buttock|glute)",
    re.IGNORECASE,
)
_FACE_PATTERNS = re.compile(
    r"(eye|brow|lid|nose|cheek|jaw|lip|mouth|tongue|chin|ear|face|"
    r"teeth|gum|forehead)",
    re.IGNORECASE,
)
_LEFT_PATTERNS = re.compile(
    r"(\.L$|_L$|\.l$|_l$|Left|\.left$|_left$|^L_)",
    re.IGNORECASE,
)
_RIGHT_PATTERNS = re.compile(
    r"(\.R$|_R$|\.r$|_r$|Right|\.right$|_right$|^R_)",
    re.IGNORECASE,
)
_FINGER_PATTERNS = re.compile(
    r"(finger|thumb|index|middle|ring|pinky|pinkie)",
    re.IGNORECASE,
)
_HAND_PATTERNS = re.compile(
    r"(hand|wrist|palm)",
    re.IGNORECASE,
)
_ARM_PATTERNS = re.compile(
    r"(arm|elbow|forearm|upper_arm|shoulder|clavicle|collar)",
    re.IGNORECASE,
)


def _preset_items_fn(self, context):  # noqa: ARG001
    return PRESET_ITEMS


class ANIMASSIST_OT_p11_auto_partition(bpy.types.Operator):
    """Automatically create layers for body part groups"""

    bl_idname = "animassist.p11_auto_partition"
    bl_label = "Auto-Partition Layers"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(  # type: ignore[valid-type]
        name="Preset",
        description="Partitioning scheme",
        items=_preset_items_fn,
        default=0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p11 = get_p11(context)
        if p11 is None:
            return False
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        obj = context.active_object
        engine.ensure_base_layer(p11)

        bone_names = [b.name for b in obj.pose.bones]

        if self.preset == "UPPER_LOWER":
            self._partition_upper_lower(p11, bone_names)
        elif self.preset == "FACE_BODY":
            self._partition_face_body(p11, bone_names)
        elif self.preset == "LEFT_RIGHT":
            self._partition_left_right(p11, bone_names)
        elif self.preset == "FINGERS_HANDS":
            self._partition_fingers_hands(p11, bone_names)
        else:
            self.report({'INFO'}, "Use 'Assign by Pattern' for custom partitions")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Applied '{self.preset}' partition preset")
        return {'FINISHED'}

    def _create_assigned_layer(
        self, p11, name: str, bone_names: list[str],
        blend_mode: str = "OVERRIDE",
    ) -> None:
        idx = engine.add_layer(p11, name=name, blend_mode=blend_mode)
        layer = p11.layers[idx]
        engine.get_layer_action(layer, create=True)
        for bn in bone_names:
            ba = layer.assigned_bones.add()
            ba.bone_name = bn

    def _partition_upper_lower(self, p11, bone_names: list[str]) -> None:
        upper = [n for n in bone_names if _UPPER_BODY_PATTERNS.search(n)]
        lower = [n for n in bone_names if _LOWER_BODY_PATTERNS.search(n)]
        remainder = [n for n in bone_names if n not in upper and n not in lower]

        if upper:
            self._create_assigned_layer(p11, "Upper Body", upper)
        if lower:
            self._create_assigned_layer(p11, "Lower Body", lower)
        if remainder:
            self._create_assigned_layer(p11, "Other", remainder)

    def _partition_face_body(self, p11, bone_names: list[str]) -> None:
        face = [n for n in bone_names if _FACE_PATTERNS.search(n)]
        body = [n for n in bone_names if n not in face]

        if face:
            self._create_assigned_layer(p11, "Face", face)
        if body:
            self._create_assigned_layer(p11, "Body", body)

    def _partition_left_right(self, p11, bone_names: list[str]) -> None:
        left = [n for n in bone_names if _LEFT_PATTERNS.search(n)]
        right = [n for n in bone_names if _RIGHT_PATTERNS.search(n)]
        center = [n for n in bone_names if n not in left and n not in right]

        if left:
            self._create_assigned_layer(p11, "Left Side", left)
        if right:
            self._create_assigned_layer(p11, "Right Side", right)
        if center:
            self._create_assigned_layer(p11, "Center", center)

    def _partition_fingers_hands(self, p11, bone_names: list[str]) -> None:
        fingers = [n for n in bone_names if _FINGER_PATTERNS.search(n)]
        hands = [n for n in bone_names
                 if _HAND_PATTERNS.search(n) and n not in fingers]
        arms = [n for n in bone_names
                if _ARM_PATTERNS.search(n) and n not in fingers and n not in hands]
        other = [n for n in bone_names
                 if n not in fingers and n not in hands and n not in arms]

        if fingers:
            self._create_assigned_layer(p11, "Fingers", fingers)
        if hands:
            self._create_assigned_layer(p11, "Hands", hands)
        if arms:
            self._create_assigned_layer(p11, "Arms", arms)
        if other:
            self._create_assigned_layer(p11, "Other", other)


# ---------------------------------------------------------------------------
# Select Assigned Bones (in viewport)
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_select_assigned(bpy.types.Operator):
    """Select all pose bones assigned to the active layer"""

    bl_idname = "animassist.p11_select_assigned"
    bl_label = "Select Assigned Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context) and _in_pose_mode(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]
        obj = context.active_object

        # Deselect all first.
        bpy.ops.pose.select_all(action='DESELECT')

        if len(layer.assigned_bones) == 0:
            # Whole-body layer: select all.
            bpy.ops.pose.select_all(action='SELECT')
            self.report({'INFO'}, "Selected all bones (whole-body layer)")
            return {'FINISHED'}

        assigned_names = {b.bone_name for b in layer.assigned_bones}
        selected = 0
        for bone in obj.pose.bones:
            if bone.name in assigned_names:
                set_pose_bone_selected(bone, True)
                selected += 1

        self.report({'INFO'}, f"Selected {selected} assigned bones")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Add Channel Override
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_add_channel_override(bpy.types.Operator):
    """Add a per-channel weight override for a bone on the active layer"""

    bl_idname = "animassist.p11_add_channel_override"
    bl_label = "Add Channel Override"
    bl_options = {'REGISTER', 'UNDO'}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone to add override for",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def invoke(self, context: bpy.types.Context, event) -> set[str]:
        # Default to active bone name.
        obj = context.active_object
        if obj and obj.type == "ARMATURE" and context.mode == "POSE":
            active_bone = context.active_pose_bone
            if active_bone:
                self.bone_name = active_bone.name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if not self.bone_name:
            self.report({'WARNING'}, "No bone name specified")
            return {'CANCELLED'}

        # Check if override already exists.
        for ovr in layer.channel_overrides:
            if ovr.bone_name == self.bone_name:
                self.report({'WARNING'}, f"Override already exists for '{self.bone_name}'")
                return {'CANCELLED'}

        ovr = layer.channel_overrides.add()
        ovr.bone_name = self.bone_name
        p11.eval_generation += 1
        self.report({'INFO'}, f"Added channel override for '{self.bone_name}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Remove Channel Override
# ---------------------------------------------------------------------------

class ANIMASSIST_OT_p11_remove_channel_override(bpy.types.Operator):
    """Remove a per-channel weight override"""

    bl_idname = "animassist.p11_remove_channel_override"
    bl_label = "Remove Channel Override"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(  # type: ignore[valid-type]
        name="Override Index",
        default=0,
        min=0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _active_layer_valid(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p11 = get_p11(context)
        layer = p11.layers[p11.active_layer_index]

        if 0 <= self.index < len(layer.channel_overrides):
            name = layer.channel_overrides[self.index].bone_name
            layer.channel_overrides.remove(self.index)
            p11.eval_generation += 1
            self.report({'INFO'}, f"Removed override for '{name}'")
            return {'FINISHED'}

        return {'CANCELLED'}


# ---------------------------------------------------------------------------
# Class collection
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    ANIMASSIST_OT_p11_assign_selected,
    ANIMASSIST_OT_p11_remove_bone,
    ANIMASSIST_OT_p11_remove_selected,
    ANIMASSIST_OT_p11_clear_assignments,
    ANIMASSIST_OT_p11_assign_by_pattern,
    ANIMASSIST_OT_p11_auto_partition,
    ANIMASSIST_OT_p11_select_assigned,
    ANIMASSIST_OT_p11_add_channel_override,
    ANIMASSIST_OT_p11_remove_channel_override,
)
