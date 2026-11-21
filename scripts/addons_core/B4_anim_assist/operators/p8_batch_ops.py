"""
Batch operations, switch history navigation, markers, contact preservation, opposite-side matching, quick actions.
Features 31-33, 35-37, 40-41, 43-44
"""

import bpy
from ..core.p8_properties import get_p8
from ..core import p8_match_math as mm
from ..core import p8_switch_history as hist
from ..core.logging import get_logger
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected

_log = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _resolve_prop_owner(obj, bone_name: str):
    """Resolve property owner: bone if specified, else object."""
    if bone_name and hasattr(obj, "pose") and obj.pose:
        return obj.pose.bones.get(bone_name)
    return obj


def _get_prop_value(owner, prop_path: str):
    """Get property value from owner using path."""
    try:
        if prop_path.startswith('["') and prop_path.endswith('"]'):
            key = prop_path[2:-2]
            return owner[key]
        return owner.path_resolve(prop_path)
    except Exception:
        return None


def _set_prop_value(owner, prop_path: str, value):
    """Set property value on owner using path."""
    try:
        if prop_path.startswith('["') and prop_path.endswith('"]'):
            key = prop_path[2:-2]
            owner[key] = value
            return True
        parts = prop_path.rsplit(".", 1)
        if len(parts) == 2:
            parent = owner.path_resolve(parts[0])
            setattr(parent, parts[1], value)
        else:
            setattr(owner, prop_path, value)
        return True
    except Exception:
        return False


def _key_prop(owner, prop_path: str, frame: int) -> bool:
    """Insert a keyframe for the switch property.

    Returns ``False`` instead of raising when Blender refuses the insert (bad
    path, locked/driven property, linked data) so callers can count and report
    the miss rather than silently claiming success.
    """
    try:
        if prop_path.startswith('["') and prop_path.endswith('"]'):
            key = prop_path[2:-2]
            owner.keyframe_insert(data_path=f'["{key}"]', frame=frame)
        else:
            owner.keyframe_insert(data_path=prop_path, frame=frame)
    except Exception:
        return False
    return True


# ============================================================================
# OPERATORS
# ============================================================================

class AA_OT_p8_switch_marker(bpy.types.Operator):
    """Place a temporary marker at the current frame."""
    bl_idname = "animassist.p8_switch_marker"
    bl_label = "Switch Marker"
    bl_description = "Place a temporary marker at the current frame to mark switch events."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        frame = context.scene.frame_current
        marker_name = f"SW_{frame}"

        # Remove existing marker at this frame if present
        for marker in context.scene.timeline_markers:
            if marker.frame == frame:
                context.scene.timeline_markers.remove(marker)
                break

        # Create new marker
        marker = context.scene.timeline_markers.new(marker_name)
        marker.frame = frame

        self.report({"INFO"}, f"Marker '{marker_name}' placed at frame {frame}")
        return {"FINISHED"}


class AA_OT_p8_batch_switch(bpy.types.Operator):
    """Apply a space switch with compensation to all selected objects at once."""
    bl_idname = "animassist.p8_batch_switch"
    bl_label = "Batch Switch"
    bl_description = (
        "Apply the configured space-switch property change to all selected "
        "objects, compensating each one to maintain visual transforms."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        prop_path = p8.switch_prop_path if p8 else ""
        bone_name = p8.switch_bone_name if p8 else ""
        new_value = p8.switch_new_value if p8 else 0.0

        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        frame = context.scene.frame_current
        switched = 0
        key_failures = 0

        for obj in context.selected_objects:
            owner = _resolve_prop_owner(obj, bone_name)
            if owner is None:
                continue

            old_value = _get_prop_value(owner, prop_path)
            if old_value is None:
                continue

            # Record -> Switch -> Update -> Compensate -> Apply -> Key
            # Compensate the OWNER (the pose bone when one is set): the
            # armature object's world matrix never changes on a bone switch.
            state = mm.record_visual_state(owner)
            _set_prop_value(owner, prop_path, new_value)
            context.view_layer.update()

            result = mm.compensate_after_switch(
                owner, state,
                respect_locks=p8.respect_locks if p8 else True,
                respect_drivers=p8.respect_drivers if p8 else True,
            )
            mm.apply_match_result(owner, result)

            if p8 and p8.auto_key_switch:
                mm.key_match_result(owner, result, frame)
                if not _key_prop(owner, prop_path, frame):
                    key_failures += 1

            hist.push_event(hist.SwitchEvent(
                frame=frame, obj_name=obj.name, bone_name=bone_name,
                prop_path=prop_path, old_value=old_value, new_value=new_value,
            ))
            switched += 1

        if key_failures:
            self.report(
                {"WARNING"},
                f"Batch switched {switched} object(s); switch property could not "
                f"be keyed on {key_failures} of them",
            )
        else:
            self.report({"INFO"}, f"Batch switched {switched} object(s)")
        return {"FINISHED"}


class AA_OT_p8_nav_next_switch(bpy.types.Operator):
    """Navigate to the next switch event in the timeline."""
    bl_idname = "animassist.p8_nav_next_switch"
    bl_label = "Next Switch"
    bl_description = "Jump to the next switch event in the timeline."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        current_frame = context.scene.frame_current
        event = hist.find_next_event(current_frame)

        if event is None:
            self.report({"INFO"}, "No next switch event found")
            return {"CANCELLED"}

        context.scene.frame_set(event.frame)
        self.report(
            {"INFO"},
            f"Navigated to frame {event.frame}: {event.obj_name} "
            f"({event.prop_path} = {event.new_value})"
        )
        return {"FINISHED"}


class AA_OT_p8_nav_prev_switch(bpy.types.Operator):
    """Navigate to the previous switch event in the timeline."""
    bl_idname = "animassist.p8_nav_prev_switch"
    bl_label = "Prev Switch"
    bl_description = "Jump to the previous switch event in the timeline."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        current_frame = context.scene.frame_current
        event = hist.find_prev_event(current_frame)

        if event is None:
            self.report({"INFO"}, "No previous switch event found")
            return {"CANCELLED"}

        context.scene.frame_set(event.frame)
        self.report(
            {"INFO"},
            f"Navigated to frame {event.frame}: {event.obj_name} "
            f"({event.prop_path} = {event.new_value})"
        )
        return {"FINISHED"}


class AA_OT_p8_clear_history(bpy.types.Operator):
    """Clear the switch history stack."""
    bl_idname = "animassist.p8_clear_history"
    bl_label = "Clear Switch History"
    bl_description = "Clear the switch history stack and all recorded events."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        hist.clear_history()
        self.report({"INFO"}, "Switch history cleared")
        return {"FINISHED"}


class AA_OT_p8_contact_preserve_match(bpy.types.Operator):
    """Match with contact preservation for specified bones."""
    bl_idname = "animassist.p8_contact_preserve_match"
    bl_label = "Contact Preserve Match"
    bl_description = (
        "Match the active object to selected objects while preserving world "
        "positions of contact bones specified in the contact mask."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and len(context.selected_objects) > 1
            and context.active_object.type == "ARMATURE"
        )

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object
        frame = context.scene.frame_current

        if not active.pose:
            self.report({"ERROR"}, "Active object is not an armature. Select an armature in Pose mode")
            return {"CANCELLED"}

        # Parse contact mask
        contact_mask = set()
        if p8 and p8.contact_mask:
            contact_mask = set(
                name.strip() for name in p8.contact_mask.split(",") if name.strip()
            )

        # Record contact positions if mask is set
        contact_positions = {}
        if contact_mask:
            for bone_name in contact_mask:
                bone = active.pose.bones.get(bone_name)
                if bone:
                    contact_positions[bone_name] = bone.head.copy()

        # Perform match
        targets = [obj for obj in context.selected_objects if obj != active]
        if not targets:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        # Match active to first target's visual world matrix.
        source_world = mm.visual_world_matrix(targets[0])
        match_result = mm.compute_match(
            source_world, active,
            channel_filter=mm.ChannelFilter.all(),
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
            use_visual=True,
        )

        mm.apply_match_result(active, match_result)

        # Restore contact bone positions
        if contact_mask and contact_positions:
            for bone_name, original_pos in contact_positions.items():
                bone = active.pose.bones.get(bone_name)
                if bone:
                    current_pos = bone.head.copy()
                    offset = original_pos - current_pos

                    # Adjust root or parent bone to restore contact position
                    if active.pose.bones.active:
                        root_bone = active.pose.bones.active
                        if root_bone.parent is None:
                            root_bone.location += offset

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, match_result, frame)

        self.report({"INFO"}, "Contact-preserved match applied")
        return {"FINISHED"}


class AA_OT_p8_contact_mask_from_selection(bpy.types.Operator):
    """Set contact mask from selected bones in pose mode."""
    bl_idname = "animassist.p8_contact_mask_from_selection"
    bl_label = "Contact Mask from Selection"
    bl_description = (
        "Set the contact preservation mask to the names of selected pose bones."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return (
            active is not None
            and active.type == "ARMATURE"
            and active.mode == "POSE"
        )

    def execute(self, context):
        p8 = get_p8(context)
        if not p8:
            self.report({"ERROR"}, "Matching settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        active = context.active_object
        selected_bones = [
            bone.name for bone in active.pose.bones if pose_bone_selected(bone)
        ]

        if not selected_bones:
            self.report({"WARNING"}, "No bones selected")
            return {"CANCELLED"}

        p8.contact_mask = ", ".join(selected_bones)
        self.report({"INFO"}, f"Contact mask set: {p8.contact_mask}")
        return {"FINISHED"}


class AA_OT_p8_quick_match(bpy.types.Operator):
    """One-click match at current frame with default settings."""
    bl_idname = "animassist.p8_quick_match"
    bl_label = "Quick Match"
    bl_description = (
        "Match the active object to selected objects at the current frame "
        "using default settings (all channels, visual match, no offset)."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and len(context.selected_objects) > 1
            and context.active_object.type == "ARMATURE"
        )

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object
        frame = context.scene.frame_current

        if not active.pose:
            self.report({"ERROR"}, "Active object is not an armature. Select an armature in Pose mode")
            return {"CANCELLED"}

        targets = [obj for obj in context.selected_objects if obj != active]
        if not targets:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        # Match active to first target's visual world matrix.
        source_world = mm.visual_world_matrix(targets[0])
        match_result = mm.compute_match(
            source_world, active,
            channel_filter=mm.ChannelFilter.all(),
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
            use_visual=True,
        )

        mm.apply_match_result(active, match_result)

        # Auto-key if enabled
        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, match_result, frame)

        self.report({"INFO"}, "Quick match applied at current frame")
        return {"FINISHED"}


class AA_OT_p8_repeat_last_switch(bpy.types.Operator):
    """Repeat the last switch operation at the current frame."""
    bl_idname = "animassist.p8_repeat_last_switch"
    bl_label = "Repeat Last Switch"
    bl_description = (
        "Repeat the last switch operation on the same object, "
        "applied at the current frame."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        p8 = get_p8(context)
        event = hist.get_last_event()

        if event is None:
            self.report({"INFO"}, "No previous switch event in history")
            return {"CANCELLED"}

        # Find the object
        obj = bpy.data.objects.get(event.obj_name)
        if obj is None:
            self.report({"ERROR"}, f"Object '{event.obj_name}' was renamed or deleted. Clear the switch history and switch again")
            return {"CANCELLED"}

        frame = context.scene.frame_current

        # Resolve property owner
        owner = _resolve_prop_owner(obj, event.bone_name)
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        # Read current property value before switching (for accurate history).
        current_value = _get_prop_value(owner, event.prop_path)

        # Record visual state before switch
        state = mm.record_visual_state(obj)

        # Apply switch
        _set_prop_value(owner, event.prop_path, event.new_value)
        context.view_layer.update()

        # Compensate
        result = mm.compensate_after_switch(
            obj, state,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(obj, result)

        # Auto-key if enabled
        if p8 and p8.auto_key_switch:
            mm.key_match_result(obj, result, frame)
            _key_prop(owner, event.prop_path, frame)

        # Record in history
        hist.push_event(hist.SwitchEvent(
            frame=frame, obj_name=obj.name, bone_name=event.bone_name,
            prop_path=event.prop_path, old_value=current_value,
            new_value=event.new_value,
        ))

        self.report({"INFO"}, f"Repeated switch on {event.obj_name} at frame {frame}")
        return {"FINISHED"}


# ============================================================================
# OPERATOR REGISTRATION
# ============================================================================

CLASSES: tuple[type, ...] = (
    AA_OT_p8_switch_marker,
    AA_OT_p8_batch_switch,
    AA_OT_p8_nav_next_switch,
    AA_OT_p8_nav_prev_switch,
    AA_OT_p8_clear_history,
    AA_OT_p8_contact_preserve_match,
    AA_OT_p8_contact_mask_from_selection,
    AA_OT_p8_quick_match,
    AA_OT_p8_repeat_last_switch,
)
