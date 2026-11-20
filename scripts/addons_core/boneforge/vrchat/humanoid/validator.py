"""BoneCraft VRChat — Humanoid Validator.

Validate humanoid mappings and armature completeness for VRChat export.
Custom validation checks are registered through boneforge.core.
Category: VRChat Setup.
"""

import bpy
from bpy.types import Operator, Panel

from boneforge.core import active_armature, register_custom_check, unregister_custom_check
from boneforge.i18n import T
from .mapper import get_mapping, REQUIRED_SLOTS


# ── Validation functions ─────────────────────────────────────────────

def validate_humanoid(armature):
    """Validate humanoid completeness.

    Returns list of validation issues (dicts with 'type', 'message' keys).
    """
    issues = []

    if not armature or armature.type != "ARMATURE":
        return issues

    mapping = get_mapping(armature)
    missing = mapping.validate_required()

    # Check for missing required slots
    if missing:
        issues.append({
            "type": "error",
            "message": f"Missing {len(missing)} required humanoid slots: "
                       f"{', '.join(missing)}"
        })

    # Check for zero bones
    if not armature.data.bones:
        issues.append({
            "type": "error",
            "message": "Armature has no bones"
        })

    # Check for non-deforming bones
    deforming_bones = sum(1 for b in armature.data.bones if not b.use_deform)
    if deforming_bones > 0:
        issues.append({
            "type": "warning",
            "message": f"{deforming_bones} non-deforming bones found (may affect export)"
        })

    # Check for missing bone parents (except root)
    orphan_bones = []
    for bone in armature.data.bones:
        if bone.parent is None and bone != armature.data.bones[0]:
            orphan_bones.append(bone.name)

    if orphan_bones:
        issues.append({
            "type": "warning",
            "message": f"{len(orphan_bones)} bones with no parent (detached from rig)"
        })

    return issues


def custom_humanoid_check(armature):
    """Custom check function for validation registry.

    Returns list of validation result dicts compatible with validator.
    """
    return validate_humanoid(armature)


# ── Operators ────────────────────────────────────────────────────────

class BF_OT_VRC_ValidateHumanoid(Operator):
    """Run full humanoid validation checks."""

    bl_idname = "boneforge.vrc_validate_humanoid"
    bl_label = "Validate Humanoid"
    bl_options = {"REGISTER"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        issues = validate_humanoid(arm)

        if not issues:
            self.report({"INFO"}, "Humanoid validation passed!")
            return {"FINISHED"}

        # Report first issue
        first_issue = issues[0]
        level = "ERROR" if first_issue["type"] == "error" else "WARNING"
        self.report({level}, f"{first_issue['message']}")

        return {"FINISHED"}


# ── Panel ────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_humanoid_validator(Panel):
    """Humanoid validator panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_humanoid_validator"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"

    def draw_header(self, context):
        self.layout.label(text=T("Humanoid Validator"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        arm = active_armature(context)
        layout = self.layout

        if not arm:
            return

        # Validate button
        layout.operator(
            "boneforge.vrc_validate_humanoid",
            text=T("Run Validation")
        )

        layout.separator()

        # Issues display
        issues = validate_humanoid(arm)

        if not issues:
            box = layout.box()
            row = box.row()
            row.label(text=T("All checks passed!"), icon="CHECKMARK")
        else:
            for issue in issues:
                box = layout.box()
                icon = "ERROR" if issue["type"] == "error" else "INFO"
                row = box.row()
                row.label(text=issue["message"], icon=icon)

        layout.separator()

        # Summary
        mapping = get_mapping(arm)
        missing = mapping.validate_required()

        row = layout.row()
        row.label(
            text=f"Required Slots: {len(REQUIRED_SLOTS) - len(missing)}/{len(REQUIRED_SLOTS)}"
        )


# ── Registration ─────────────────────────────────────────────────────

classes = (
    BF_OT_VRC_ValidateHumanoid,
    BONEFORGE_PT_vrc_humanoid_validator,
)


def register():
    """Register humanoid validator classes and custom check."""
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register custom validation check
    register_custom_check(custom_humanoid_check)


def unregister():
    """Unregister humanoid validator classes and custom check."""
    unregister_custom_check(custom_humanoid_check)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
