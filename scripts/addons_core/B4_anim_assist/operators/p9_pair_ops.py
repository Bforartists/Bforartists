import json
import bpy
from ..core.p9_properties import get_p9
from ..core import p9_pair_detect as det
from ..core import p9_pair_cache as cache
from ..core.logging import get_logger
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected
from ..core.helpers import confirm_dialog

_log = get_logger(__name__)


def _armature_poll(context):
    """Shared poll helper for armature-based operators."""
    obj = context.active_object
    return obj is not None and obj.type == "ARMATURE"


def _build_overrides_dict(p9):
    """Build a dict of bone pair overrides from p9 properties."""
    overrides = {}
    for override in p9.pair_overrides:
        if override.bone_a and override.bone_b:
            overrides[override.bone_a] = override.bone_b
    return overrides


def _build_exceptions_dict(p9):
    """Build a dict of naming exceptions from p9 properties."""
    exceptions = {}
    for exc in p9.naming_exceptions:
        if exc.original and exc.opposite:
            exceptions[exc.original] = exc.opposite
    return exceptions


class AA_OT_p9_build_cache(bpy.types.Operator):
    """Scan all bones in the active armature and build the opposite-side pair cache."""
    bl_idname = "animassist.p9_build_cache"
    bl_label = "Build Pair Cache"
    bl_description = "Scan all bones in the active armature and build the opposite-side pair cache."

    @classmethod
    def poll(cls, context):
        return _armature_poll(context)

    def execute(self, context):
        armature = context.active_object
        bone_names = [bone.name for bone in armature.data.bones]

        pair_map = cache.build_pair_map(armature.data.name, bone_names)

        paired_count = sum(1 for v in pair_map.values() if v is not None)
        total = len(bone_names)

        self.report(
            {'INFO'},
            f"Pair cache built: {paired_count}/{total} bones paired"
        )
        return {'FINISHED'}


class AA_OT_p9_add_pair_override(bpy.types.Operator):
    """Add a manual bone pair mapping that overrides auto-detection."""
    bl_idname = "animassist.p9_add_pair_override"
    bl_label = "Add Pair Override"
    bl_description = "Add a manual bone pair mapping that overrides auto-detection."

    @classmethod
    def poll(cls, context):
        return _armature_poll(context)

    def execute(self, context):
        p9 = get_p9(context)
        p9.pair_overrides.add()
        cache.invalidate()
        self.report({'INFO'}, "Pair override added")
        return {'FINISHED'}


class AA_OT_p9_remove_pair_override(bpy.types.Operator):
    """Remove the selected manual pair override."""
    bl_idname = "animassist.p9_remove_pair_override"
    bl_label = "Remove Pair Override"
    bl_description = "Remove the selected manual pair override."
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(
        name="Index",
        description="Index of the pair override to remove",
        default=0,
        min=0
    )

    @classmethod
    def poll(cls, context):
        p9 = get_p9(context)
        if p9 is None:
            return False
        return len(p9.pair_overrides) > 0 and p9.pair_overrides_index < len(p9.pair_overrides)

    def execute(self, context):
        p9 = get_p9(context)
        idx = self.index if self.index < len(p9.pair_overrides) else p9.pair_overrides_index
        p9.pair_overrides.remove(idx)
        cache.invalidate()
        self.report({'INFO'}, "Pair override removed")
        return {'FINISHED'}


class AA_OT_p9_add_naming_exception(bpy.types.Operator):
    """Add a naming exception for bones that do not follow standard naming conventions."""
    bl_idname = "animassist.p9_add_naming_exception"
    bl_label = "Add Naming Exception"
    bl_description = "Add a naming exception for bones that do not follow standard naming conventions."

    @classmethod
    def poll(cls, context):
        return _armature_poll(context)

    def execute(self, context):
        p9 = get_p9(context)
        p9.naming_exceptions.add()
        self.report({'INFO'}, "Naming exception added")
        return {'FINISHED'}


class AA_OT_p9_remove_naming_exception(bpy.types.Operator):
    """Remove the selected naming exception."""
    bl_idname = "animassist.p9_remove_naming_exception"
    bl_label = "Remove Naming Exception"
    bl_description = "Remove the selected naming exception."
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(
        name="Index",
        description="Index of the naming exception to remove",
        default=0,
        min=0
    )

    @classmethod
    def poll(cls, context):
        p9 = get_p9(context)
        if p9 is None:
            return False
        return len(p9.naming_exceptions) > 0 and p9.naming_exceptions_index < len(p9.naming_exceptions)

    def execute(self, context):
        p9 = get_p9(context)
        idx = self.index if self.index < len(p9.naming_exceptions) else p9.naming_exceptions_index
        p9.naming_exceptions.remove(idx)
        self.report({'INFO'}, "Naming exception removed")
        return {'FINISHED'}


class AA_OT_p9_save_pair_preset(bpy.types.Operator):
    """Save the current pair overrides and naming exceptions as a JSON preset on the scene."""
    bl_idname = "animassist.p9_save_pair_preset"
    bl_label = "Save Pair Preset"
    bl_description = "Save the current pair overrides and naming exceptions as a JSON preset on the scene."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _armature_poll(context)

    def execute(self, context):
        p9 = get_p9(context)

        # Serialize pair overrides
        overrides = []
        for override in p9.pair_overrides:
            overrides.append({
                "bone_a": override.bone_a,
                "bone_b": override.bone_b
            })

        # Serialize naming exceptions
        exceptions = []
        for exc in p9.naming_exceptions:
            exceptions.append({
                "original": exc.original,
                "opposite": exc.opposite
            })

        preset_data = {
            "pair_overrides": overrides,
            "naming_exceptions": exceptions
        }

        preset_json = json.dumps(preset_data, indent=2)
        context.scene["anim_assist_p9_pair_presets"] = preset_json

        self.report({'INFO'}, "Pair preset saved")
        return {'FINISHED'}


class AA_OT_p9_load_pair_preset(bpy.types.Operator):
    """Load pair overrides and naming exceptions from the saved JSON preset."""
    bl_idname = "animassist.p9_load_pair_preset"
    bl_label = "Load Pair Preset"
    bl_description = "Load pair overrides and naming exceptions from the saved JSON preset."
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):  # type: ignore[no-untyped-def]
        return confirm_dialog(self, context, event, 'Replace the current pair overrides and naming exceptions with the saved preset?')

    @classmethod
    def poll(cls, context):
        return "anim_assist_p9_pair_presets" in context.scene

    def execute(self, context):
        p9 = get_p9(context)
        preset_json = context.scene["anim_assist_p9_pair_presets"]

        try:
            preset_data = json.loads(preset_json)
        except json.JSONDecodeError:
            self.report({'ERROR'}, "The saved pair preset is damaged. Save the pair preset again")
            return {'CANCELLED'}

        # Clear existing collections
        p9.pair_overrides.clear()
        p9.naming_exceptions.clear()

        # Load pair overrides
        for override_data in preset_data.get("pair_overrides", []):
            override = p9.pair_overrides.add()
            override.bone_a = override_data.get("bone_a", "")
            override.bone_b = override_data.get("bone_b", "")

        # Load naming exceptions
        for exc_data in preset_data.get("naming_exceptions", []):
            exc = p9.naming_exceptions.add()
            exc.original = exc_data.get("original", "")
            exc.opposite = exc_data.get("opposite", "")

        cache.invalidate()
        self.report({'INFO'}, "Pair preset loaded")
        return {'FINISHED'}


class AA_OT_p9_mirror_switch_targets(bpy.types.Operator):
    """Find the opposite-side equivalent of detected switch patterns by name."""
    bl_idname = "animassist.p9_mirror_switch_targets"
    bl_label = "Mirror Switch Targets"
    bl_description = "Find the opposite-side equivalent of detected switch patterns by name."

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "ARMATURE" and
                context.mode == "POSE")

    def execute(self, context):
        armature = context.active_object
        selected_bones = [bone for bone in context.selected_pose_bones]

        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        p9 = get_p9(context)
        overrides = _build_overrides_dict(p9)
        exceptions = _build_exceptions_dict(p9)

        matches_found = 0

        for bone in selected_bones:
            # Find opposite-side bone
            opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
            if opposite_name:
                matches_found += 1
                _log.info(f"Opposite for {bone.name}: {opposite_name}")

        self.report({'INFO'}, f"Found {matches_found} opposite-side matches")
        return {'FINISHED'}


class AA_OT_p9_mirror_proxy_helpers(bpy.types.Operator):
    """Mirror proxy helper bone naming to find opposite-side proxy targets."""
    bl_idname = "animassist.p9_mirror_proxy_helpers"
    bl_label = "Mirror Proxy Helpers"
    bl_description = "Mirror proxy helper bone naming to find opposite-side proxy targets."

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "ARMATURE" and
                context.mode == "POSE")

    def execute(self, context):
        armature = context.active_object
        selected_bones = [bone for bone in context.selected_pose_bones]

        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        p9 = get_p9(context)
        overrides = _build_overrides_dict(p9)
        exceptions = _build_exceptions_dict(p9)

        matches_found = 0

        for bone in selected_bones:
            # Find opposite-side bone by proxy naming pattern
            opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
            if opposite_name and opposite_name in armature.data.bones:
                matches_found += 1
                _log.info(f"Proxy helper opposite for {bone.name}: {opposite_name}")

        self.report({'INFO'}, f"Found {matches_found} proxy helper opposites")
        return {'FINISHED'}


class AA_OT_p9_mirror_selection_sets(bpy.types.Operator):
    """Create a mirrored selection set from the current bone selection."""
    bl_idname = "animassist.p9_mirror_selection_sets"
    bl_label = "Mirror Selection Sets"
    bl_description = "Create a mirrored selection set from the current bone selection."

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "ARMATURE" and
                context.mode == "POSE")

    def execute(self, context):
        armature = context.active_object
        selected_bones = [bone for bone in context.selected_pose_bones]

        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        p9 = get_p9(context)
        overrides = _build_overrides_dict(p9)
        exceptions = _build_exceptions_dict(p9)

        # Deselect all
        bpy.ops.pose.select_all(action='DESELECT')

        mirrored_count = 0

        for bone in selected_bones:
            # Find opposite-side bone
            opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
            if opposite_name and opposite_name in armature.data.bones:
                opposite_bone = armature.pose.bones[opposite_name]
                set_pose_bone_selected(opposite_bone, True)
                mirrored_count += 1

        self.report({'INFO'}, f"Selected {mirrored_count} mirrored bones")
        return {'FINISHED'}


class AA_OT_p9_nav_next_unpaired(bpy.types.Operator):
    """Navigate to the next bone that has no detected opposite-side pair."""
    bl_idname = "animassist.p9_nav_next_unpaired"
    bl_label = "Next Unpaired"
    bl_description = "Navigate to the next bone that has no detected opposite-side pair."

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "ARMATURE" and
                context.mode == "POSE")

    def execute(self, context):
        armature = context.active_object
        p9 = get_p9(context)

        # Get unpaired bones
        unpaired = cache.get_unpaired(armature.data.name)

        if not unpaired:
            self.report({'INFO'}, "All bones are paired")
            return {'FINISHED'}

        current_active = context.active_pose_bone
        current_name = current_active.name if current_active else None

        # Find next unpaired after current
        next_unpaired = None
        found_current = False

        for bone_name in unpaired:
            if found_current:
                next_unpaired = bone_name
                break
            if bone_name == current_name:
                found_current = True

        # If not found after current, wrap to first
        if not next_unpaired:
            next_unpaired = unpaired[0]

        # Select and make active
        bpy.ops.pose.select_all(action='DESELECT')
        target_bone = armature.pose.bones[next_unpaired]
        set_pose_bone_selected(target_bone, True)
        armature.data.bones.active = target_bone.bone

        self.report({'INFO'}, f"Selected unpaired bone: {next_unpaired}")
        return {'FINISHED'}


class AA_OT_p9_validate_pairs(bpy.types.Operator):
    """Run pair-map validation diagnostics on all bones in the armature."""
    bl_idname = "animassist.p9_validate_pairs"
    bl_label = "Validate Pairs"
    bl_description = "Run pair-map validation diagnostics on all bones in the armature."

    @classmethod
    def poll(cls, context):
        return _armature_poll(context)

    def execute(self, context):
        armature = context.active_object
        bone_names = [bone.name for bone in armature.data.bones]

        # Build pair map
        pair_map = cache.build_pair_map(armature.data.name, bone_names)

        # Get unpaired and ambiguous
        unpaired = cache.get_unpaired(armature.data.name)
        ambiguous = det.find_ambiguous([b.name for b in armature.data.bones])

        paired_count = sum(1 for v in pair_map.values() if v is not None)
        unpaired_count = len(unpaired)
        ambiguous_count = len(ambiguous)

        self.report(
            {'INFO'},
            f"Pairs: {paired_count}, Unpaired: {unpaired_count}, Ambiguous: {ambiguous_count}"
        )

        return {'FINISHED'}


CLASSES = (
    AA_OT_p9_build_cache,
    AA_OT_p9_add_pair_override,
    AA_OT_p9_remove_pair_override,
    AA_OT_p9_add_naming_exception,
    AA_OT_p9_remove_naming_exception,
    AA_OT_p9_save_pair_preset,
    AA_OT_p9_load_pair_preset,
    AA_OT_p9_mirror_switch_targets,
    AA_OT_p9_mirror_proxy_helpers,
    AA_OT_p9_mirror_selection_sets,
    AA_OT_p9_nav_next_unpaired,
    AA_OT_p9_validate_pairs,
)
