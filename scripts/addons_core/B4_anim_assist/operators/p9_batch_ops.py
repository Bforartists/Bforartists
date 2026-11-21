"""
Batch mirror and reporting operators.

Provides batch mirroring capabilities, pair detection warnings, and
reporting utilities.
"""

import bpy
from ..core.p9_properties import get_p9
from ..core import p9_pair_detect as det
from ..core import p9_pair_cache as cache
from ..core import p9_mirror_math as mm
from ..core import p8_match_math as p8mm
from ..core.logging import get_logger
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected
from ..core.helpers import report_failure

_log = get_logger(__name__)

# Module-level state for repeat-last-mirror and reporting
_last_mirror_op: str = ""
_last_mirror_side: str = ""
_last_results: list = []


def _get_overrides(p9):
    """Extract manual pair overrides from P9 properties."""
    overrides = {}
    if p9 and p9.pair_overrides:
        for item in p9.pair_overrides:
            if item.bone_a and item.bone_b:
                overrides[item.bone_a] = item.bone_b
                overrides[item.bone_b] = item.bone_a
    return overrides


def _get_exceptions(p9):
    """Extract naming exceptions from P9 properties."""
    exceptions = {}
    if p9 and p9.naming_exceptions:
        for item in p9.naming_exceptions:
            if item.original and item.opposite:
                exceptions[item.original] = item.opposite
                exceptions[item.opposite] = item.original
    return exceptions


def _build_channel_filter(p9):
    """Build a ChannelFilter from P9 mirror properties."""
    if p9 is None:
        return p8mm.ChannelFilter.all()
    return p8mm.ChannelFilter(
        location=p8mm.AxisMask(x=p9.mirror_location and p9.axis_mask[0],
                                y=p9.mirror_location and p9.axis_mask[1],
                                z=p9.mirror_location and p9.axis_mask[2]),
        rotation=p8mm.AxisMask(x=p9.mirror_rotation and p9.axis_mask[0],
                                y=p9.mirror_rotation and p9.axis_mask[1],
                                z=p9.mirror_rotation and p9.axis_mask[2]),
        scale=p8mm.AxisMask(x=p9.mirror_scale and p9.axis_mask[0],
                             y=p9.mirror_scale and p9.axis_mask[1],
                             z=p9.mirror_scale and p9.axis_mask[2]),
    )


def _pose_poll(context):
    """Check if context is in armature pose mode."""
    obj = context.active_object
    return (obj is not None and obj.type == "ARMATURE"
            and context.mode == "POSE")


def clear_last_mirror():
    """Clear module-level mirror state."""
    global _last_mirror_op, _last_mirror_side, _last_results
    _last_mirror_op = ""
    _last_mirror_side = ""
    _last_results = []


class AA_OT_p9_batch_mirror(bpy.types.Operator):
    """Mirror transforms of all selected bones to their opposite-side pairs."""
    bl_idname = "animassist.p9_batch_mirror"
    bl_label = "Batch Mirror Selected"
    bl_description = "Mirror transforms of all selected bones to their opposite-side pairs."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        global _last_mirror_op, _last_results

        obj = context.active_object
        p9 = get_p9(context)
        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'CANCELLED'}

        results = []
        mirrored_count = 0
        skipped_count = 0

        for bone in selected_bones:
            opposite_name = det.find_opposite(
                bone.name,
                overrides=overrides,
                exceptions=exceptions
            )

            if opposite_name is None:
                skipped_count += 1
                results.append({
                    'source': bone.name,
                    'target': None,
                    'success': False
                })
                continue

            opposite_bone = obj.pose.bones.get(opposite_name)
            if opposite_bone is None:
                skipped_count += 1
                results.append({
                    'source': bone.name,
                    'target': opposite_name,
                    'success': False
                })
                continue

            try:
                mirror_result = mm.mirror_bone_pose(
                    bone,
                    opposite_bone,
                    axis=p9.mirror_axis if p9 else "X",
                    channel_filter=_build_channel_filter(p9)
                )
                results.append({
                    'source': bone.name,
                    'target': opposite_name,
                    'success': True,
                    'result': mirror_result
                })
                mirrored_count += 1
            except Exception as e:
                _log.error(f"Failed to mirror {bone.name}: {e}")
                skipped_count += 1
                results.append({
                    'source': bone.name,
                    'target': opposite_name,
                    'success': False
                })

        # Auto-key if enabled
        if p9.auto_key_mirror and context.scene.tool_settings.use_keyframe_insert_auto:
            for bone in selected_bones:
                bone.keyframe_insert(data_path="location")
                bone.keyframe_insert(data_path="rotation_euler")
                bone.keyframe_insert(data_path="scale")

        _last_mirror_op = "batch_mirror"
        _last_results = results

        self.report({'INFO'}, f"Mirrored {mirrored_count} bones, {skipped_count} skipped (no pair)")
        return {'FINISHED'}


class AA_OT_p9_batch_mirror_active_side(bpy.types.Operator):
    """Mirror all bones from the active bone's side to the opposite side."""
    bl_idname = "animassist.p9_batch_mirror_active_side"
    bl_label = "Mirror Active Side"
    bl_description = "Mirror all bones from the active bone's side to the opposite side."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (_pose_poll(context) and obj is not None
                and context.active_pose_bone is not None)

    def execute(self, context):
        global _last_mirror_op, _last_mirror_side, _last_results

        obj = context.active_object
        active_bone = context.active_pose_bone
        p9 = get_p9(context)

        if not p9 or active_bone is None:
            self.report({'ERROR'}, "No active bone. Select a bone in Pose mode")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        # Detect active bone's side
        active_side = det.detect_side(active_bone.name)
        if active_side not in ('L', 'R'):
            self.report({'ERROR'}, "Cannot tell which side the active bone is on. Use .L/.R naming or add a naming exception under Mirror & Symmetry")
            return {'CANCELLED'}

        # Collect all bones on that side
        source_bones = [b for b in obj.pose.bones
                       if det.detect_side(b.name) == active_side]

        if not source_bones:
            self.report({'WARNING'}, "No bones found on active side")
            return {'CANCELLED'}

        results = []
        mirrored_count = 0
        skipped_count = 0

        for bone in source_bones:
            opposite_name = det.find_opposite(
                bone.name,
                overrides=overrides,
                exceptions=exceptions
            )

            if opposite_name is None:
                skipped_count += 1
                results.append({
                    'source': bone.name,
                    'target': None,
                    'success': False
                })
                continue

            opposite_bone = obj.pose.bones.get(opposite_name)
            if opposite_bone is None:
                skipped_count += 1
                results.append({
                    'source': bone.name,
                    'target': opposite_name,
                    'success': False
                })
                continue

            try:
                mirror_result = mm.mirror_bone_pose(
                    bone,
                    opposite_bone,
                    axis=p9.mirror_axis if p9 else "X",
                    channel_filter=_build_channel_filter(p9)
                )
                results.append({
                    'source': bone.name,
                    'target': opposite_name,
                    'success': True,
                    'result': mirror_result
                })
                mirrored_count += 1
            except Exception as e:
                _log.error(f"Failed to mirror {bone.name}: {e}")
                skipped_count += 1
                results.append({
                    'source': bone.name,
                    'target': opposite_name,
                    'success': False
                })

        # Auto-key if enabled
        if p9.auto_key_mirror and context.scene.tool_settings.use_keyframe_insert_auto:
            for bone in source_bones:
                bone.keyframe_insert(data_path="location")
                bone.keyframe_insert(data_path="rotation_euler")
                bone.keyframe_insert(data_path="scale")

        _last_mirror_op = "batch_mirror_active_side"
        _last_mirror_side = active_side
        _last_results = results

        self.report({'INFO'}, f"Mirrored {mirrored_count} bones from side {active_side}")
        return {'FINISHED'}


class AA_OT_p9_mirror_report(bpy.types.Operator):
    """Generate a per-target summary of the last mirror operation."""
    bl_idname = "animassist.p9_mirror_report"
    bl_label = "Mirror Report"
    bl_description = "Generate a per-target summary of the last mirror operation showing what was changed."
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context) and len(_last_results) > 0

    def execute(self, context):
        if not _last_results:
            self.report({'WARNING'}, "No mirror results to report")
            return {'CANCELLED'}

        success_count = sum(1 for r in _last_results if r.get('success', False))
        failed_count = len(_last_results) - success_count

        report_lines = [
            f"Mirror Report: {success_count} successful, {failed_count} failed",
            ""
        ]

        for result in _last_results:
            source = result.get('source', 'unknown')
            target = result.get('target', 'no pair')
            success = result.get('success', False)

            if success:
                report_lines.append(f"✓ {source} → {target}")
            else:
                report_lines.append(f"✗ {source} → {target}")

        report_text = "\n".join(report_lines)
        _log.info(report_text)

        self.report({'INFO'}, f"Report: {success_count} mirrored, {failed_count} failed")
        return {'FINISHED'}


class AA_OT_p9_missing_warning(bpy.types.Operator):
    """List all bones in the armature that have no detected opposite-side pair."""
    bl_idname = "animassist.p9_missing_warning"
    bl_label = "Missing Opposite Warning"
    bl_description = "List all bones in the armature that have no detected opposite-side pair."
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        missing_pairs = []

        for bone in obj.pose.bones:
            opposite_name = det.find_opposite(
                bone.name,
                overrides=overrides,
                exceptions=exceptions
            )

            if opposite_name is None:
                missing_pairs.append(bone.name)

        if not missing_pairs:
            self.report({'INFO'}, "All bones have detected opposite-side pairs")
            return {'FINISHED'}

        report_text = f"Bones with no detected opposite ({len(missing_pairs)}):\n"
        report_text += "\n".join(f"  - {name}" for name in missing_pairs)
        _log.warning(report_text)

        self.report({'WARNING'}, f"{len(missing_pairs)} bones have no opposite pair")
        return {'FINISHED'}


class AA_OT_p9_ambiguous_warning(bpy.types.Operator):
    """List bones where multiple naming patterns produce different opposite names."""
    bl_idname = "animassist.p9_ambiguous_warning"
    bl_label = "Ambiguous Pair Warning"
    bl_description = "List bones where multiple naming patterns produce different opposite names."
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        try:
            ambiguous = det.find_ambiguous(
                [b.name for b in obj.data.bones],
                overrides=overrides,
                exceptions=exceptions
            )
        except Exception as e:
            report_failure(self, "Could not detect bone pairs", "Check that bone names follow a .L/.R style convention", e)
            return {'CANCELLED'}

        if not ambiguous:
            self.report({'INFO'}, "No ambiguous bone pairs detected")
            return {'FINISHED'}

        report_text = f"Ambiguous bone pairs ({len(ambiguous)}):\n"
        for bone_name, candidates in ambiguous.items():
            candidates_str = ", ".join(candidates)
            report_text += f"  {bone_name}: [{candidates_str}]\n"

        _log.warning(report_text)
        self.report({'WARNING'}, f"{len(ambiguous)} ambiguous pairs found")
        return {'FINISHED'}


class AA_OT_p9_channel_resolver(bpy.types.Operator):
    """Resolve and display opposite-side channel mappings for selected bones."""
    bl_idname = "animassist.p9_channel_resolver"
    bl_label = "Channel Resolver"
    bl_description = "Resolve and display opposite-side channel mappings for selected bones."
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (_pose_poll(context) and obj is not None
                and any(pose_bone_selected(b) for b in obj.pose.bones))

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        channel_filter = _build_channel_filter(p9)

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        report_lines = ["Channel Mapping Resolution:"]

        for bone in selected_bones:
            opposite_name = det.find_opposite(
                bone.name,
                overrides=overrides,
                exceptions=exceptions
            )

            if opposite_name is None:
                report_lines.append(f"  {bone.name}: NO PAIR")
                continue

            channels = []
            if channel_filter.location.x or channel_filter.location.y or channel_filter.location.z:
                channels.append("location(XYZ)")
            if channel_filter.rotation.x or channel_filter.rotation.y or channel_filter.rotation.z:
                channels.append("rotation(XYZ)")
            if channel_filter.scale.x or channel_filter.scale.y or channel_filter.scale.z:
                channels.append("scale(XYZ)")

            channels_str = ", ".join(channels) if channels else "none"
            report_lines.append(
                f"  {bone.name} → {opposite_name} [{channels_str}]"
            )

        report_text = "\n".join(report_lines)
        _log.info(report_text)

        self.report({'INFO'}, f"Mapped {len(selected_bones)} bones")
        return {'FINISHED'}


class AA_OT_p9_mirror_metadata(bpy.types.Operator):
    """Mirror bone custom properties and constraint settings alongside transforms."""
    bl_idname = "animassist.p9_mirror_metadata"
    bl_label = "Mirror Metadata"
    bl_description = "Mirror bone custom properties and constraint settings alongside transforms."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (_pose_poll(context) and obj is not None
                and any(pose_bone_selected(b) for b in obj.pose.bones))

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        mirrored_count = 0

        for source_bone in selected_bones:
            opposite_name = det.find_opposite(
                source_bone.name,
                overrides=overrides,
                exceptions=exceptions
            )

            if opposite_name is None:
                continue

            target_bone = obj.pose.bones.get(opposite_name)
            if target_bone is None:
                continue

            try:
                # Copy custom properties
                for key, value in source_bone.items():
                    if not key.startswith("_"):
                        try:
                            target_bone[key] = value
                        except Exception as e:
                            _log.warning(f"Could not copy property {key}: {e}")

                mirrored_count += 1
            except Exception as e:
                _log.error(f"Failed to mirror metadata for {source_bone.name}: {e}")

        self.report({'INFO'}, f"Mirrored metadata for {mirrored_count} bones")
        return {'FINISHED'}


class AA_OT_p9_mirror_preset_values(bpy.types.Operator):
    """Mirror stored transform preset values to the opposite side."""
    bl_idname = "animassist.p9_mirror_preset_values"
    bl_label = "Mirror Preset Values"
    bl_description = "Mirror stored transform preset values to the opposite side."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        # Check if presets exist on the armature data
        arm = obj.data
        presets = {}

        # Attempt to retrieve any stored presets
        if hasattr(arm, 'p8_presets'):
            try:
                presets = arm.p8_presets
            except Exception as e:
                _log.warning(f"Could not retrieve presets: {e}")

        if not presets:
            self.report({'INFO'}, "No stored presets found to mirror")
            return {'FINISHED'}

        mirrored_count = 0

        for preset_name, preset_data in presets.items():
            for bone_name, bone_preset in preset_data.items():
                opposite_name = det.find_opposite(
                    bone_name,
                    overrides=overrides,
                    exceptions=exceptions
                )

                if opposite_name is None:
                    continue

                try:
                    if opposite_name not in preset_data:
                        preset_data[opposite_name] = {}

                    # Mirror the transform values
                    if 'loc' in bone_preset:
                        loc = bone_preset['loc']
                        preset_data[opposite_name]['loc'] = [
                            -loc[0], loc[1], loc[2]
                        ]
                    if 'rot' in bone_preset:
                        preset_data[opposite_name]['rot'] = bone_preset['rot']
                    if 'scale' in bone_preset:
                        preset_data[opposite_name]['scale'] = bone_preset['scale']

                    mirrored_count += 1
                except Exception as e:
                    _log.error(f"Failed to mirror preset for {bone_name}: {e}")

        self.report({'INFO'}, f"Mirrored {mirrored_count} preset values")
        return {'FINISHED'}


class AA_OT_p9_repeat_mirror(bpy.types.Operator):
    """Repeat the most recent mirror operation using the same settings."""
    bl_idname = "animassist.p9_repeat_mirror"
    bl_label = "Repeat Last Mirror"
    bl_description = "Repeat the most recent mirror operation using the same settings."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context) and _last_mirror_op != ""

    def execute(self, context):
        if _last_mirror_op == "batch_mirror":
            return bpy.ops.animassist.p9_batch_mirror('INVOKE_DEFAULT')
        elif _last_mirror_op == "batch_mirror_active_side":
            return bpy.ops.animassist.p9_batch_mirror_active_side('INVOKE_DEFAULT')
        else:
            self.report({'WARNING'}, "Cannot repeat unknown mirror operation")
            return {'CANCELLED'}


class AA_OT_p9_custom_pattern(bpy.types.Operator):
    """Apply the user-defined custom naming pattern for pair detection."""
    bl_idname = "animassist.p9_custom_pattern"
    bl_label = "Apply Custom Pattern"
    bl_description = "Apply the user-defined custom naming pattern for pair detection and rebuild the cache."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        if not p9:
            self.report({'ERROR'}, "Mirroring settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {'CANCELLED'}

        left_pattern = p9.custom_left_pattern
        right_pattern = p9.custom_right_pattern

        if not left_pattern or not right_pattern:
            self.report({'ERROR'}, "No custom patterns set. Add them in the mirroring settings first")
            return {'CANCELLED'}

        try:
            # Compile and apply custom patterns
            det.compile_custom_pattern("custom", left_pattern, right_pattern)

            # Rebuild cache with new patterns
            cache.build_pair_map(obj.data.name, [b.name for b in obj.data.bones])
            cache.invalidate()

            self.report({'INFO'}, "Custom pattern applied and cache rebuilt")
            return {'FINISHED'}
        except Exception as e:
            report_failure(self, "The pattern is not a valid regular expression", "Fix the pattern and try again", e, detail=str(e))
            _log.error(f"Custom pattern error: {e}")
            return {'CANCELLED'}


# Register all operators
CLASSES = (
    AA_OT_p9_batch_mirror,
    AA_OT_p9_batch_mirror_active_side,
    AA_OT_p9_mirror_report,
    AA_OT_p9_missing_warning,
    AA_OT_p9_ambiguous_warning,
    AA_OT_p9_channel_resolver,
    AA_OT_p9_mirror_metadata,
    AA_OT_p9_mirror_preset_values,
    AA_OT_p9_repeat_mirror,
    AA_OT_p9_custom_pattern,
)
