"""Rig pattern detection, preset management, and diagnostics operators."""

from __future__ import annotations

import bpy
import json
from ..core.p8_properties import get_p8
from ..core import p8_switch_detect as det
from ..core import p8_switch_history as hist
from ..core.logging import get_logger
from ..core.helpers import report_failure

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Module-level cached detection results
# ---------------------------------------------------------------------------

_cached_patterns: list[det.SwitchPattern] = []


def get_cached_patterns() -> list[det.SwitchPattern]:
    """Return a copy of the cached patterns list."""
    return list(_cached_patterns)


def clear_cached_patterns() -> None:
    """Clear the cached patterns."""
    _cached_patterns.clear()


# ---------------------------------------------------------------------------
# Module-level switch presets (saved as JSON on scene custom property)
# ---------------------------------------------------------------------------

_PRESET_KEY = "anim_assist_p8_switch_presets"


def _get_presets(context: bpy.types.Context) -> dict[str, dict]:
    """Load presets from scene custom property."""
    scene = context.scene
    preset_json = scene.get(_PRESET_KEY, "{}")
    try:
        return json.loads(preset_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_presets(context: bpy.types.Context, presets: dict[str, dict]) -> None:
    """Save presets to scene custom property."""
    scene = context.scene
    scene[_PRESET_KEY] = json.dumps(presets)


# ---------------------------------------------------------------------------
# Operators: Detection
# ---------------------------------------------------------------------------

class AA_OT_p8_detect_space_enums(bpy.types.Operator):
    """Detect custom space enum properties on the active object."""
    bl_idname = "animassist.p8_detect_space_enums"
    bl_label = "Detect Space Enums"
    bl_description = "Detect custom space enum properties on the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            patterns = det.detect_space_enums(obj)
            _cached_patterns.clear()
            _cached_patterns.extend(patterns)
            count = len(patterns)
            self.report({"INFO"}, f"Found {count} space enum pattern(s)")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("detect_space_enums failed")
            report_failure(self, "Detection failed", "Select an armature with IK/FK constraints and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_detect_parent_patterns(bpy.types.Operator):
    """Detect common parent-switch boolean patterns on the active object."""
    bl_idname = "animassist.p8_detect_parent_patterns"
    bl_label = "Detect Parent Patterns"
    bl_description = "Detect common parent-switch boolean patterns on the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            patterns = det.detect_bool_patterns(obj)
            # Extend cache and deduplicate by (obj_name, bone_name, prop_path)
            seen = {(p.obj_name, p.bone_name, p.prop_path) for p in _cached_patterns}
            before_count = len(_cached_patterns)
            for pat in patterns:
                key = (pat.obj_name, pat.bone_name, pat.prop_path)
                if key not in seen:
                    _cached_patterns.append(pat)
                    seen.add(key)
            added = len(_cached_patterns) - before_count
            self.report({"INFO"}, f"Added {added} parent pattern(s) (total: {len(_cached_patterns)})")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("detect_parent_patterns failed")
            report_failure(self, "Detection failed", "Select an armature with IK/FK constraints and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_detect_influence_patterns(bpy.types.Operator):
    """Detect constraint influence switch patterns on the active object."""
    bl_idname = "animassist.p8_detect_influence_patterns"
    bl_label = "Detect Influence Patterns"
    bl_description = "Detect constraint influence switch patterns on the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            patterns = det.detect_influence_patterns(obj)
            # Extend cache and deduplicate
            seen = {(p.obj_name, p.bone_name, p.prop_path) for p in _cached_patterns}
            before_count = len(_cached_patterns)
            for pat in patterns:
                key = (pat.obj_name, pat.bone_name, pat.prop_path)
                if key not in seen:
                    _cached_patterns.append(pat)
                    seen.add(key)
            added = len(_cached_patterns) - before_count
            self.report({"INFO"}, f"Added {added} influence pattern(s) (total: {len(_cached_patterns)})")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("detect_influence_patterns failed")
            report_failure(self, "Detection failed", "Select an armature with IK/FK constraints and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_detect_custom_props(bpy.types.Operator):
    """Detect generic custom property switch patterns on the active object."""
    bl_idname = "animassist.p8_detect_custom_props"
    bl_label = "Detect Custom Properties"
    bl_description = "Detect generic custom property switch patterns on the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            patterns = det.detect_custom_props(obj)
            # Extend cache and deduplicate
            seen = {(p.obj_name, p.bone_name, p.prop_path) for p in _cached_patterns}
            before_count = len(_cached_patterns)
            for pat in patterns:
                key = (pat.obj_name, pat.bone_name, pat.prop_path)
                if key not in seen:
                    _cached_patterns.append(pat)
                    seen.add(key)
            added = len(_cached_patterns) - before_count
            self.report({"INFO"}, f"Added {added} custom property pattern(s) (total: {len(_cached_patterns)})")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("detect_custom_props failed")
            report_failure(self, "Detection failed", "Select an armature with IK/FK constraints and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_detect_all(bpy.types.Operator):
    """Run all rig pattern detectors at once on the active object."""
    bl_idname = "animassist.p8_detect_all"
    bl_label = "Detect All Patterns"
    bl_description = "Run all rig pattern detectors at once on the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            patterns = det.detect_all_patterns(obj)
            _cached_patterns.clear()
            _cached_patterns.extend(patterns)
            count = len(patterns)
            self.report({"INFO"}, f"Found {count} pattern(s) across all detectors")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("detect_all_patterns failed")
            report_failure(self, "Detection failed", "Select an armature with IK/FK constraints and try again", e)
            return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Operators: Apply Detected Pattern
# ---------------------------------------------------------------------------

class AA_OT_p8_apply_detected_pattern(bpy.types.Operator):
    """Apply the selected detected pattern to the switch settings."""
    bl_idname = "animassist.p8_apply_detected_pattern"
    bl_label = "Apply Detected Pattern"
    bl_description = "Apply the selected detected pattern to the switch settings."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        p8 = get_p8(context)
        return p8 is not None and len(_cached_patterns) > 0

    def execute(self, context: bpy.types.Context):
        p8 = get_p8(context)
        if p8 is None:
            self.report({"ERROR"}, "Matching settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        if not _cached_patterns:
            self.report({"ERROR"}, "No patterns detected yet. Run Detect first")
            return {"CANCELLED"}

        idx = min(p8.detected_pattern_index, len(_cached_patterns) - 1)
        if idx < 0:
            self.report({"ERROR"}, "Select a detected pattern in the list first")
            return {"CANCELLED"}

        pattern = _cached_patterns[idx]

        try:
            p8.switch_prop_path = pattern.prop_path
            p8.switch_bone_name = pattern.bone_name
            # Map detected kind to switch_kind enum
            kind_map = {
                "ENUM": "ENUM",
                "BOOL": "BOOL",
                "INFLUENCE": "INFLUENCE",
                "CUSTOM_PROP": "CUSTOM",
            }
            p8.switch_kind = kind_map.get(pattern.kind, "CUSTOM")
            self.report({"INFO"}, f"Applied pattern: {pattern.display_label()}")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("apply_detected_pattern failed")
            report_failure(self, "Failed to apply pattern", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Operators: Switch Presets
# ---------------------------------------------------------------------------

class AA_OT_p8_save_switch_preset(bpy.types.Operator):
    """Save the current switch configuration as a named preset."""
    bl_idname = "animassist.p8_save_switch_preset"
    bl_label = "Save Switch Preset"
    bl_description = "Save the current switch configuration as a named preset."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return get_p8(context) is not None

    def execute(self, context: bpy.types.Context):
        p8 = get_p8(context)
        if p8 is None:
            self.report({"ERROR"}, "Matching settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        name = p8.switch_preset_name.strip()
        if not name:
            self.report({"ERROR"}, "Enter a preset name first")
            return {"CANCELLED"}

        try:
            preset = {
                "prop_path": p8.switch_prop_path,
                "bone_name": p8.switch_bone_name,
                "kind": p8.switch_kind,
                "new_value": p8.switch_new_value,
            }
            # Load existing presets
            presets = _get_presets(context)
            presets[name] = preset
            _save_presets(context, presets)
            self.report({"INFO"}, f"Saved switch preset '{name}'")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("save_switch_preset failed")
            report_failure(self, "Failed to save preset", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_load_switch_preset(bpy.types.Operator):
    """Load a named switch preset and apply it to the current settings."""
    bl_idname = "animassist.p8_load_switch_preset"
    bl_label = "Load Switch Preset"
    bl_description = "Load a named switch preset and apply it to the current settings."
    bl_options = {"REGISTER", "UNDO"}

    preset_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Name of the preset to load",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return get_p8(context) is not None

    def execute(self, context: bpy.types.Context):
        p8 = get_p8(context)
        if p8 is None:
            self.report({"ERROR"}, "Matching settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        preset_name = self.preset_name.strip()
        if not preset_name:
            self.report({"ERROR"}, "Enter a preset name first")
            return {"CANCELLED"}

        try:
            presets = _get_presets(context)
            if preset_name not in presets:
                self.report({"ERROR"}, f"Preset '{preset_name}' not found. Pick one from the list or save it first")
                return {"CANCELLED"}

            preset = presets[preset_name]
            p8.switch_prop_path = preset.get("prop_path", "")
            p8.switch_bone_name = preset.get("bone_name", "")
            p8.switch_kind = preset.get("kind", "ENUM")
            p8.switch_new_value = float(preset.get("new_value", 0.0))
            self.report({"INFO"}, f"Loaded switch preset '{preset_name}'")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("load_switch_preset failed")
            report_failure(self, "Failed to load preset", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_delete_switch_preset(bpy.types.Operator):
    """Delete a named switch preset."""
    bl_idname = "animassist.p8_delete_switch_preset"
    bl_label = "Delete Switch Preset"
    bl_description = "Delete a named switch preset."
    bl_options = {"REGISTER", "UNDO"}

    preset_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Name of the preset to delete",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return get_p8(context) is not None

    def execute(self, context: bpy.types.Context):
        preset_name = self.preset_name.strip()
        if not preset_name:
            self.report({"ERROR"}, "Enter a preset name first")
            return {"CANCELLED"}

        try:
            presets = _get_presets(context)
            if preset_name not in presets:
                self.report({"ERROR"}, f"Preset '{preset_name}' not found. Pick one from the list or save it first")
                return {"CANCELLED"}

            del presets[preset_name]
            _save_presets(context, presets)
            self.report({"INFO"}, f"Deleted switch preset '{preset_name}'")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("delete_switch_preset failed")
            report_failure(self, "Failed to delete preset", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Operators: Reports and Diagnostics
# ---------------------------------------------------------------------------

class AA_OT_p8_compensation_report(bpy.types.Operator):
    """Generate and display a compensation operation report."""
    bl_idname = "animassist.p8_compensation_report"
    bl_label = "Compensation Report"
    bl_description = "Generate and display a compensation operation report."
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return getattr(context, "window_manager", None) is not None

    def execute(self, context: bpy.types.Context):
        wm = getattr(context, "window_manager", None)
        if wm is None:
            self.report({"ERROR"}, "Window manager not available. Run this from the Bforartists interface, not a background script")
            return {"CANCELLED"}

        try:
            # Get the last switch event from history
            last_event = hist.get_last_event()
            if last_event is None:
                self.report({"WARNING"}, "No compensation history available")
                return {"CANCELLED"}

            lines: list[str] = []
            lines.append("=== COMPENSATION REPORT ===")
            lines.append("")
            lines.append(f"Frame: {last_event.frame}")
            target = last_event.bone_name or last_event.obj_name
            lines.append(f"Target: {target}")
            lines.append(f"Property: {last_event.prop_path}")
            lines.append(f"Old Value: {last_event.old_value}")
            lines.append(f"New Value: {last_event.new_value}")
            lines.append("")

            # Add history context
            all_events = hist.get_history()
            if all_events:
                lines.append(f"Total switch events in history: {len(all_events)}")
                lines.append(f"Unique frames with switches: {len(hist.get_unique_frames())}")
            lines.append("")

            text = "\n".join(lines)
            wm.clipboard = text
            self.report({"INFO"}, "Compensation report copied to clipboard")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("compensation_report failed")
            report_failure(self, "Report generation failed", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_unsupported_warning(bpy.types.Operator):
    """Check for and report unsupported rig setups."""
    bl_idname = "animassist.p8_unsupported_warning"
    bl_label = "Unsupported Setup Warning"
    bl_description = "Check for and report unsupported rig setups."
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            warnings: list[str] = []

            # Check for animation data
            if obj.animation_data is None or obj.animation_data.action is None:
                warnings.append("• No animation data or action assigned")

            # Check for complex constraint stacks
            def _count_constraints(obj_or_bone):
                return len(obj_or_bone.constraints)

            obj_con_count = _count_constraints(obj)
            if obj_con_count > 5:
                warnings.append(f"• Object has {obj_con_count} constraints (complex stack)")

            bone_con_count = 0
            if hasattr(obj, "pose") and obj.pose:
                for bone in obj.pose.bones:
                    bone_con_count += _count_constraints(bone)
                if bone_con_count > 20:
                    warnings.append(f"• Armature bones have {bone_con_count} total constraints (very complex)")

            # Check for drivers on transform channels
            def _check_drivers(obj_or_bone, name):
                if not hasattr(obj_or_bone, "animation_data"):
                    return []
                anim_data = obj_or_bone.animation_data
                if not anim_data or not anim_data.drivers:
                    return []
                found = []
                for driver in anim_data.drivers:
                    if any(x in driver.data_path for x in ["location", "rotation", "scale"]):
                        found.append(driver.data_path)
                return found

            obj_drivers = _check_drivers(obj, obj.name)
            if obj_drivers:
                warnings.append(f"• Object has {len(obj_drivers)} driver(s) on transform channels")

            if hasattr(obj, "pose") and obj.pose:
                for bone in obj.pose.bones:
                    bone_drivers = _check_drivers(bone, bone.name)
                    if bone_drivers:
                        warnings.append(f"• Bone '{bone.name}' has driver(s) on transform channels")

            # Check for locked transforms
            def _check_locks(obj_or_bone, name):
                locks = []
                if hasattr(obj_or_bone, "lock_location"):
                    if any(obj_or_bone.lock_location):
                        locks.append("location")
                if hasattr(obj_or_bone, "lock_rotation"):
                    if any(obj_or_bone.lock_rotation):
                        locks.append("rotation")
                if hasattr(obj_or_bone, "lock_scale"):
                    if any(obj_or_bone.lock_scale):
                        locks.append("scale")
                return locks

            obj_locks = _check_locks(obj, obj.name)
            if obj_locks:
                warnings.append(f"• Object has locked channels: {', '.join(obj_locks)}")

            if hasattr(obj, "pose") and obj.pose:
                lock_count = 0
                for bone in obj.pose.bones:
                    bone_locks = _check_locks(bone, bone.name)
                    if bone_locks:
                        lock_count += 1
                if lock_count > 0:
                    warnings.append(f"• {lock_count} bone(s) have locked channels")

            if warnings:
                msg = "Potential issues found:\n" + "\n".join(warnings)
                self.report({"WARNING"}, msg)
            else:
                self.report({"INFO"}, "No obvious setup issues detected")

            return {"FINISHED"}
        except Exception as e:
            _log.exception("unsupported_warning failed")
            report_failure(self, "Check failed", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


class AA_OT_p8_debug_diagnostics(bpy.types.Operator):
    """Run detailed custom-rig debug diagnostics and copy to clipboard."""
    bl_idname = "animassist.p8_debug_diagnostics"
    bl_label = "Debug Diagnostics"
    bl_description = "Run detailed custom-rig debug diagnostics and copy to clipboard."
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (context.active_object is not None and
                getattr(context, "window_manager", None) is not None)

    def execute(self, context: bpy.types.Context):
        wm = getattr(context, "window_manager", None)
        if wm is None:
            self.report({"ERROR"}, "Window manager not available. Run this from the Bforartists interface, not a background script")
            return {"CANCELLED"}

        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object. Select an object and try again")
            return {"CANCELLED"}

        try:
            lines: list[str] = []
            lines.append("=== SWITCH DETECTION DEBUG DIAGNOSTICS ===")
            lines.append("")
            lines.append(f"Object: {obj.name}")
            lines.append(f"Type: {obj.type}")
            lines.append("")

            # Run all detectors
            patterns = det.detect_all_patterns(obj)
            lines.append(f"Detected Patterns: {len(patterns)}")
            for i, pat in enumerate(patterns):
                lines.append(f"  [{i}] {pat.display_label()} (confidence={pat.confidence:.2f})")
            lines.append("")

            # Constraint types
            def _count_constraint_types(constraints):
                counts = {}
                for con in constraints:
                    counts[con.type] = counts.get(con.type, 0) + 1
                return counts

            obj_con_types = _count_constraint_types(obj.constraints)
            if obj_con_types:
                lines.append("Object Constraint Types:")
                for ctype, count in sorted(obj_con_types.items()):
                    lines.append(f"  {ctype}: {count}")
            else:
                lines.append("Object Constraint Types: None")

            bone_con_types_total = {}
            if hasattr(obj, "pose") and obj.pose:
                for bone in obj.pose.bones:
                    for ctype, count in _count_constraint_types(bone.constraints).items():
                        bone_con_types_total[ctype] = bone_con_types_total.get(ctype, 0) + count
            if bone_con_types_total:
                lines.append("Bone Constraint Types (total):")
                for ctype, count in sorted(bone_con_types_total.items()):
                    lines.append(f"  {ctype}: {count}")
            else:
                lines.append("Bone Constraint Types: None")
            lines.append("")

            # Driver count
            driver_count = 0
            if obj.animation_data and obj.animation_data.drivers:
                driver_count += len(obj.animation_data.drivers)
            if hasattr(obj, "pose") and obj.pose:
                for bone in obj.pose.bones:
                    if bone.animation_data and bone.animation_data.drivers:
                        driver_count += len(bone.animation_data.drivers)
            lines.append(f"Total Drivers: {driver_count}")
            lines.append("")

            # Custom property count
            obj_props = len([k for k in obj.keys() if not k.startswith("_")])
            bone_props = 0
            if hasattr(obj, "pose") and obj.pose:
                for bone in obj.pose.bones:
                    bone_props += len([k for k in bone.keys() if not k.startswith("_")])
            lines.append("Custom Properties:")
            lines.append(f"  Object-level: {obj_props}")
            lines.append(f"  Bone-level: {bone_props}")
            lines.append(f"  Total: {obj_props + bone_props}")
            lines.append("")

            # Bone hierarchy info (if armature)
            if hasattr(obj, "pose") and obj.pose:
                lines.append(f"Armature Bones: {len(obj.pose.bones)}")
                lines.append("Bone Hierarchy:")
                for bone in obj.pose.bones:
                    depth = 0
                    b = bone
                    while b.parent:
                        depth += 1
                        b = b.parent
                    indent = "  " * (depth + 1)
                    con_str = f" ({len(bone.constraints)} constraints)" if bone.constraints else ""
                    lines.append(f"{indent}{bone.name}{con_str}")
            else:
                lines.append("Armature: No")

            lines.append("")
            lines.append("=== END DIAGNOSTICS ===")

            text = "\n".join(lines)
            wm.clipboard = text
            self.report({"INFO"}, "Debug diagnostics copied to clipboard")
            return {"FINISHED"}
        except Exception as e:
            _log.exception("debug_diagnostics failed")
            report_failure(self, "Diagnostics generation failed", "Undo (Ctrl+Z) and try again", e)
            return {"CANCELLED"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p8_detect_space_enums,
    AA_OT_p8_detect_parent_patterns,
    AA_OT_p8_detect_influence_patterns,
    AA_OT_p8_detect_custom_props,
    AA_OT_p8_detect_all,
    AA_OT_p8_apply_detected_pattern,
    AA_OT_p8_save_switch_preset,
    AA_OT_p8_load_switch_preset,
    AA_OT_p8_delete_switch_preset,
    AA_OT_p8_compensation_report,
    AA_OT_p8_unsupported_warning,
    AA_OT_p8_debug_diagnostics,
)
