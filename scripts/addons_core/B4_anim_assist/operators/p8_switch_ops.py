"""
Space-switching, compensation, and property keying operators.
Features 13-16, 21-25: compensation (single/multi/range), enum/bool/influence switching,
history restore, and preview toggle.
"""

import bpy
from ..core.p8_properties import get_p8
from ..core import p8_match_math as mm
from ..core import p8_switch_history as hist
from ..core.logging import get_logger
from ..core.fcurve_compat import get_fcurves
from ..core.helpers import report_failure

_log = get_logger(__name__)

# Module-level state for preview/cancel restore
_preview_state: dict | None = None
_preview_obj_name: str = ""


def clear_preview_state() -> None:
    """Reset module-level preview globals (called on file load)."""
    global _preview_state, _preview_obj_name
    _preview_state = None
    _preview_obj_name = ""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _resolve_prop_owner(obj, bone_name: str):
    """Return the pose bone or object that owns the switch property."""
    if bone_name and hasattr(obj, "pose") and obj.pose:
        return obj.pose.bones.get(bone_name)
    return obj


def _get_prop_value(owner, prop_path: str):
    """Read a property value via path. Handles custom props and RNA paths."""
    try:
        # Custom property: ["prop_name"]
        if prop_path.startswith('["') and prop_path.endswith('"]'):
            key = prop_path[2:-2]
            return owner[key]
        # RNA path like constraints["name"].influence
        return owner.path_resolve(prop_path)
    except Exception:
        return None


def _set_prop_value(owner, prop_path: str, value) -> bool:
    """Write a property value via path."""
    try:
        if prop_path.startswith('["') and prop_path.endswith('"]'):
            key = prop_path[2:-2]
            owner[key] = value
            return True
        # For RNA paths, need to split into parent + attribute
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
    """Insert a keyframe for the property at the given frame."""
    try:
        if prop_path.startswith('["') and prop_path.endswith('"]'):
            key = prop_path[2:-2]
            owner.keyframe_insert(data_path=f'["{key}"]', frame=frame)
        else:
            owner.keyframe_insert(data_path=prop_path, frame=frame)
        return True
    except Exception:
        return False


def _resolve_comp_range(p8, context) -> tuple[int, int]:
    """Resolve compensation frame range from PropertyGroup settings."""
    scene = context.scene
    if p8 is None or p8.comp_range == "SINGLE":
        f = scene.frame_current
        return (f, f)
    elif p8.comp_range == "CUSTOM":
        return (int(p8.comp_range_start), int(p8.comp_range_end))
    elif p8.comp_range == "PREVIEW":
        if scene.use_preview_range:
            return (scene.frame_preview_start, scene.frame_preview_end)
        return (scene.frame_start, scene.frame_end)
    elif p8.comp_range == "SELECTION":
        # Find selected keyframe range
        obj = context.active_object
        if obj and obj.animation_data and obj.animation_data.action:
            frames = []
            for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
                for kp in fc.keyframe_points:
                    if kp.select_control_point:
                        frames.append(int(kp.co.x))
            if frames:
                return (min(frames), max(frames))
        return (scene.frame_start, scene.frame_end)
    return (scene.frame_current, scene.frame_current)


# ============================================================================
# FEATURE 13: Single-frame space switch compensation
# ============================================================================


class AA_OT_p8_compensate_single(bpy.types.Operator):
    """Compensate one frame after a space switch."""

    bl_idname = "animassist.p8_compensate_single"
    bl_label = "Compensate Single"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        # Resolve property owner (object or pose bone)
        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Record visual state BEFORE switch
        state = mm.record_visual_state(owner)

        # Read old value and set new value
        old_value = _get_prop_value(owner, prop_path)
        new_value = p8.switch_new_value if p8 else 0.0
        if not _set_prop_value(owner, prop_path, new_value):
            report_failure(self, "Failed to set property", "Undo (Ctrl+Z) and try again", prop_path)
            return {"CANCELLED"}

        # Force depsgraph update
        context.view_layer.update()

        # Compensate
        cf = mm.ChannelFilter.all()
        result = mm.compensate_after_switch(
            owner,
            state,
            cf,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(owner, result)

        # Auto-key
        if p8 and p8.auto_key_switch:
            frame = context.scene.frame_current
            mm.key_match_result(owner, result, frame)
            # Also key the switch property itself
            _key_prop(owner, prop_path, frame)

        # History
        hist.push_event(
            hist.SwitchEvent(
                frame=context.scene.frame_current,
                obj_name=obj.name,
                bone_name=p8.switch_bone_name if p8 else "",
                prop_path=prop_path,
                old_value=old_value,
                new_value=new_value,
            )
        )

        self.report(
            {"INFO"},
            f"Compensated switch on '{obj.name}' ({len(result.channels_written)} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 14: Multi-frame compensation
# ============================================================================


class AA_OT_p8_compensate_multi(bpy.types.Operator):
    """Compensate multiple frames after a space switch."""

    bl_idname = "animassist.p8_compensate_multi"
    bl_label = "Compensate Multi"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        # Resolve property owner
        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Get frame range
        start_frame, end_frame = _resolve_comp_range(p8, context)
        original_frame = context.scene.frame_current

        try:
            total_channels = 0
            old_value = _get_prop_value(owner, prop_path)
            new_value = p8.switch_new_value if p8 else 0.0

            for frame in range(start_frame, end_frame + 1):
                context.scene.frame_set(frame)
                context.view_layer.update()

                # Once the property is keyed (by the previous iteration),
                # frame_set() evaluates the NEW value here and the recorded
                # baseline would already be the switched pose.  Restore the
                # old value first so compensation targets the true pre-switch
                # placement at this frame.
                _set_prop_value(owner, prop_path, old_value)
                context.view_layer.update()

                # Record state at this frame
                state = mm.record_visual_state(owner)

                # Apply switch
                if not _set_prop_value(owner, prop_path, new_value):
                    continue
                context.view_layer.update()

                # Compensate
                cf = mm.ChannelFilter.all()
                result = mm.compensate_after_switch(
                    owner,
                    state,
                    cf,
                    respect_locks=p8.respect_locks if p8 else True,
                    respect_drivers=p8.respect_drivers if p8 else True,
                )
                mm.apply_match_result(owner, result)
                total_channels += len(result.channels_written)

                # Auto-key
                # A range compensation only persists through keys: the next
                # frame_set() re-evaluates the animated channels and discards
                # this frame's compensation.  Key regardless of auto-key.
                mm.key_match_result(owner, result, frame)
                _key_prop(owner, prop_path, frame)

            # Record history event once for the range
            hist.push_event(
                hist.SwitchEvent(
                    frame=original_frame,
                    obj_name=obj.name,
                    bone_name=p8.switch_bone_name if p8 else "",
                    prop_path=prop_path,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

        finally:
            # Restore playhead
            context.scene.frame_set(original_frame)

        self.report(
            {"INFO"},
            f"Compensated {end_frame - start_frame + 1} frames ({total_channels} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 15: Bake switch across selected keyframe range
# ============================================================================


class AA_OT_p8_bake_switch_range(bpy.types.Operator):
    """Bake compensation across selected keyframe range."""

    bl_idname = "animassist.p8_bake_switch_range"
    bl_label = "Bake Switch Range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        # Resolve property owner
        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Get selected keyframe range
        if not obj.animation_data or not obj.animation_data.action:
            self.report({"ERROR"}, "This object has no animation. Key it first")
            return {"CANCELLED"}

        frames = []
        for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
            for kp in fc.keyframe_points:
                if kp.select_control_point:
                    frames.append(int(kp.co.x))

        if not frames:
            self.report({"ERROR"}, "No keyframes selected. Select keyframes in the Dope Sheet or Graph Editor first")
            return {"CANCELLED"}

        start_frame = min(frames)
        end_frame = max(frames)
        original_frame = context.scene.frame_current

        try:
            total_channels = 0
            old_value = _get_prop_value(owner, prop_path)
            new_value = p8.switch_new_value if p8 else 0.0

            for frame in range(start_frame, end_frame + 1):
                context.scene.frame_set(frame)
                context.view_layer.update()

                # Once the property is keyed (by the previous iteration),
                # frame_set() evaluates the NEW value here and the recorded
                # baseline would already be the switched pose.  Restore the
                # old value first so compensation targets the true pre-switch
                # placement at this frame.
                _set_prop_value(owner, prop_path, old_value)
                context.view_layer.update()

                state = mm.record_visual_state(owner)

                if not _set_prop_value(owner, prop_path, new_value):
                    continue
                context.view_layer.update()

                cf = mm.ChannelFilter.all()
                result = mm.compensate_after_switch(
                    owner,
                    state,
                    cf,
                    respect_locks=p8.respect_locks if p8 else True,
                    respect_drivers=p8.respect_drivers if p8 else True,
                )
                mm.apply_match_result(owner, result)
                total_channels += len(result.channels_written)

                # A range compensation only persists through keys: the next
                # frame_set() re-evaluates the animated channels and discards
                # this frame's compensation.  Key regardless of auto-key.
                mm.key_match_result(owner, result, frame)
                _key_prop(owner, prop_path, frame)

            hist.push_event(
                hist.SwitchEvent(
                    frame=original_frame,
                    obj_name=obj.name,
                    bone_name=p8.switch_bone_name if p8 else "",
                    prop_path=prop_path,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

        finally:
            context.scene.frame_set(original_frame)

        self.report(
            {"INFO"},
            f"Baked switch range {start_frame}-{end_frame} ({total_channels} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 16: Bake switch across preview range
# ============================================================================


class AA_OT_p8_bake_switch_preview(bpy.types.Operator):
    """Bake compensation across the scene preview range."""

    bl_idname = "animassist.p8_bake_switch_preview"
    bl_label = "Bake Switch Preview"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        # Resolve property owner
        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Get preview range
        scene = context.scene
        if scene.use_preview_range:
            start_frame = scene.frame_preview_start
            end_frame = scene.frame_preview_end
        else:
            start_frame = scene.frame_start
            end_frame = scene.frame_end

        original_frame = scene.frame_current

        try:
            total_channels = 0
            old_value = _get_prop_value(owner, prop_path)
            new_value = p8.switch_new_value if p8 else 0.0

            for frame in range(start_frame, end_frame + 1):
                context.scene.frame_set(frame)
                context.view_layer.update()

                # Once the property is keyed (by the previous iteration),
                # frame_set() evaluates the NEW value here and the recorded
                # baseline would already be the switched pose.  Restore the
                # old value first so compensation targets the true pre-switch
                # placement at this frame.
                _set_prop_value(owner, prop_path, old_value)
                context.view_layer.update()

                state = mm.record_visual_state(owner)

                if not _set_prop_value(owner, prop_path, new_value):
                    continue
                context.view_layer.update()

                cf = mm.ChannelFilter.all()
                result = mm.compensate_after_switch(
                    owner,
                    state,
                    cf,
                    respect_locks=p8.respect_locks if p8 else True,
                    respect_drivers=p8.respect_drivers if p8 else True,
                )
                mm.apply_match_result(owner, result)
                total_channels += len(result.channels_written)

                # A range compensation only persists through keys: the next
                # frame_set() re-evaluates the animated channels and discards
                # this frame's compensation.  Key regardless of auto-key.
                mm.key_match_result(owner, result, frame)
                _key_prop(owner, prop_path, frame)

            hist.push_event(
                hist.SwitchEvent(
                    frame=original_frame,
                    obj_name=obj.name,
                    bone_name=p8.switch_bone_name if p8 else "",
                    prop_path=prop_path,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

        finally:
            context.scene.frame_set(original_frame)

        self.report(
            {"INFO"},
            f"Baked switch preview range {start_frame}-{end_frame} ({total_channels} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 21: Switch and key an enum/integer property
# ============================================================================


class AA_OT_p8_switch_enum(bpy.types.Operator):
    """Switch and key an enum or integer property."""

    bl_idname = "animassist.p8_switch_enum"
    bl_label = "Switch Enum"
    bl_options = {"REGISTER", "UNDO"}

    value: bpy.props.IntProperty(
        name="Value",
        description="Enum or integer value to set",
        default=0,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Record state before switch
        state = mm.record_visual_state(owner)

        # Set the enum value
        old_value = _get_prop_value(owner, prop_path)
        if not _set_prop_value(owner, prop_path, self.value):
            report_failure(self, "Failed to set property", "Undo (Ctrl+Z) and try again", prop_path)
            return {"CANCELLED"}

        context.view_layer.update()

        # Compensate
        cf = mm.ChannelFilter.all()
        result = mm.compensate_after_switch(
            owner,
            state,
            cf,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(owner, result)

        # Key result and property
        frame = context.scene.frame_current
        if p8 and p8.auto_key_switch:
            mm.key_match_result(owner, result, frame)
            _key_prop(owner, prop_path, frame)

        hist.push_event(
            hist.SwitchEvent(
                frame=frame,
                obj_name=obj.name,
                bone_name=p8.switch_bone_name if p8 else "",
                prop_path=prop_path,
                old_value=old_value,
                new_value=self.value,
            )
        )

        self.report(
            {"INFO"},
            f"Switched enum to {self.value} ({len(result.channels_written)} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 22: Switch and key a boolean property
# ============================================================================


class AA_OT_p8_switch_bool(bpy.types.Operator):
    """Toggle and compensate a boolean property."""

    bl_idname = "animassist.p8_switch_bool"
    bl_label = "Switch Bool"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Record state before switch
        state = mm.record_visual_state(owner)

        # Toggle boolean
        old_value = _get_prop_value(owner, prop_path)
        new_value = 1 if (old_value == 0 or not old_value) else 0
        if not _set_prop_value(owner, prop_path, new_value):
            report_failure(self, "Failed to set property", "Undo (Ctrl+Z) and try again", prop_path)
            return {"CANCELLED"}

        context.view_layer.update()

        # Compensate
        cf = mm.ChannelFilter.all()
        result = mm.compensate_after_switch(
            owner,
            state,
            cf,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(owner, result)

        # Key result and property
        frame = context.scene.frame_current
        if p8 and p8.auto_key_switch:
            mm.key_match_result(owner, result, frame)
            _key_prop(owner, prop_path, frame)

        hist.push_event(
            hist.SwitchEvent(
                frame=frame,
                obj_name=obj.name,
                bone_name=p8.switch_bone_name if p8 else "",
                prop_path=prop_path,
                old_value=old_value,
                new_value=new_value,
            )
        )

        self.report(
            {"INFO"},
            f"Toggled bool to {new_value} ({len(result.channels_written)} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 23: Switch and key a float influence
# ============================================================================


class AA_OT_p8_switch_influence(bpy.types.Operator):
    """Set and compensate a constraint influence."""

    bl_idname = "animassist.p8_switch_influence"
    bl_label = "Switch Influence"
    bl_options = {"REGISTER", "UNDO"}

    influence: bpy.props.FloatProperty(
        name="Influence",
        description="Influence value to set",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        owner = _resolve_prop_owner(obj, p8.switch_bone_name if p8 else "")
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        prop_path = p8.switch_prop_path if p8 else ""
        if not prop_path:
            self.report({"ERROR"}, "No switch property set. Pick the IK/FK switch property in the Match & Switch panel first")
            return {"CANCELLED"}

        # Record state before switch
        state = mm.record_visual_state(owner)

        # Set influence
        old_value = _get_prop_value(owner, prop_path)
        if not _set_prop_value(owner, prop_path, self.influence):
            report_failure(self, "Failed to set property", "Undo (Ctrl+Z) and try again", prop_path)
            return {"CANCELLED"}

        context.view_layer.update()

        # Compensate
        cf = mm.ChannelFilter.all()
        result = mm.compensate_after_switch(
            owner,
            state,
            cf,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(owner, result)

        # Key result and property
        frame = context.scene.frame_current
        if p8 and p8.auto_key_switch:
            mm.key_match_result(owner, result, frame)
            _key_prop(owner, prop_path, frame)

        hist.push_event(
            hist.SwitchEvent(
                frame=frame,
                obj_name=obj.name,
                bone_name=p8.switch_bone_name if p8 else "",
                prop_path=prop_path,
                old_value=old_value,
                new_value=self.influence,
            )
        )

        self.report(
            {"INFO"},
            f"Set influence to {self.influence:.2f} ({len(result.channels_written)} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 24: Restore previous switch value
# ============================================================================


class AA_OT_p8_restore_switch(bpy.types.Operator):
    """Restore the previous switch property value."""

    bl_idname = "animassist.p8_restore_switch"
    bl_label = "Restore Switch"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        # Get last event from history
        last_event = hist.get_last_event()
        if not last_event:
            self.report({"ERROR"}, "No switch history yet. Perform a switch first")
            return {"CANCELLED"}

        owner = _resolve_prop_owner(obj, last_event.bone_name)
        if owner is None:
            self.report({"ERROR"}, "Cannot find the object or bone that owns the switch property. Check the bone name in the Match & Switch panel")
            return {"CANCELLED"}

        # Record state for re-compensation
        state = mm.record_visual_state(owner)

        # Restore old value
        if not _set_prop_value(owner, last_event.prop_path, last_event.old_value):
            self.report({"ERROR"}, "Could not restore the switch property. Check it is not locked or driven")
            return {"CANCELLED"}

        context.view_layer.update()

        # Compensate back
        cf = mm.ChannelFilter.all()
        result = mm.compensate_after_switch(
            owner,
            state,
            cf,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(owner, result)

        # Auto-key if enabled
        if p8 and p8.auto_key_switch:
            frame = context.scene.frame_current
            mm.key_match_result(owner, result, frame)
            _key_prop(owner, last_event.prop_path, frame)

        self.report(
            {"INFO"},
            f"Restored switch value ({len(result.channels_written)} channels)",
        )
        return {"FINISHED"}


# ============================================================================
# FEATURE 25: Toggle switch preview mode
# ============================================================================


class AA_OT_p8_toggle_preview(bpy.types.Operator):
    """Toggle switch preview mode to test changes before confirming."""

    bl_idname = "animassist.p8_toggle_preview"
    bl_label = "Toggle Preview"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        global _preview_state, _preview_obj_name

        p8 = get_p8(context)
        obj = context.active_object

        if not obj:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        if not p8:
            self.report({"ERROR"}, "Matching settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        # Check if preview is currently enabled
        if p8.switch_preview:
            # Disabling preview: restore from saved state
            p8.switch_preview = False
            if _preview_state and _preview_obj_name == obj.name:
                # Restore saved transforms and keyframes
                for obj_name, transforms in _preview_state.items():
                    obj_ref = context.scene.objects.get(obj_name)
                    if obj_ref:
                        for prop, value in transforms.items():
                            if prop == "location":
                                obj_ref.location = value
                            elif prop == "rotation_euler":
                                obj_ref.rotation_euler = value
                            elif prop == "rotation_quaternion":
                                obj_ref.rotation_quaternion = value
                            elif prop == "scale":
                                obj_ref.scale = value
                _preview_state = None
                _preview_obj_name = ""
            self.report({"INFO"}, "Preview disabled, restored previous state")
        else:
            # Enabling preview: save current state
            p8.switch_preview = True
            # Keyed by object name: the restore loop iterates .items() as
            # (obj_name, transforms); a bare state dict made it look up
            # scene.objects['matrix_world'] and restore nothing.
            _preview_state = {obj.name: mm.record_visual_state(obj)}
            _preview_obj_name = obj.name
            self.report({"INFO"}, "Preview enabled, state saved")

        return {"FINISHED"}


# ============================================================================
# CLASSES TUPLE
# ============================================================================


CLASSES: tuple[type, ...] = (
    AA_OT_p8_compensate_single,
    AA_OT_p8_compensate_multi,
    AA_OT_p8_bake_switch_range,
    AA_OT_p8_bake_switch_preview,
    AA_OT_p8_switch_enum,
    AA_OT_p8_switch_bool,
    AA_OT_p8_switch_influence,
    AA_OT_p8_restore_switch,
    AA_OT_p8_toggle_preview,
)
