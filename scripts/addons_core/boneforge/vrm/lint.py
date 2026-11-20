"""Per-target lint for VRM exports.

The Phase-1 Shadow remix from Team B-Shadow contributes here: instead
of papering over the differences between targets, surface them.

Each ``LintIssue`` carries a severity (``ERROR`` blocks export by
default, ``WARNING`` informs but does not block), a target id (so the
same rig can be lint'd against multiple pipelines), and a human-readable
message. The list is consumed by the export operator and the standalone
lint operator.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator

from boneforge.core import active_armature

from . import meta as meta_mod

logger = logging.getLogger(__name__)

_HUMANOID_ALIAS_PROP = "boneforge_humanoid_alias"

_TARGET_ITEMS = [
    ("VRM_1_0", "VRM 1.0", "Modern VRM spec"),
    ("VRM_0_X", "VRM 0.x", "Legacy VRM spec"),
    ("VRCHAT_FBX", "VRChat FBX", "VRChat Avatar 3.0"),
    ("VSEEFACE", "VSeeFace", "VSeeFace VTuber host"),
    ("WARUDO", "Warudo", "Warudo VTuber host"),
    ("RESONITE", "Resonite", "Resonite social VR"),
]


@dataclass(frozen=True)
class LintIssue:
    target: str
    severity: str  # "ERROR" or "WARNING"
    message: str
    fix_hint: str = ""


# ── Helpers ──────────────────────────────────────────────────────

def _has_humanoid_alias(armature_obj, alias_name: str) -> bool:
    """True if any bone has ``boneforge_humanoid_alias == alias_name``."""
    for bone in armature_obj.data.bones:
        if bone.get("boneforge_humanoid_alias") == alias_name:
            return True
    return False


def _has_viseme(armature_obj, viseme: str) -> bool:
    """True if any mesh child has the viseme custom property surfaced."""
    key = f"boneforge_viseme_{viseme}"
    for child in armature_obj.children:
        if child.type == "MESH" and key in child:
            return True
    return False


# ── Per-target lint passes ───────────────────────────────────────

_REQUIRED_HUMANOID_FOR_VRM = (
    "Hips", "Spine", "Chest", "Head",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot",
)

_RECOMMENDED_VISEMES = ("a", "i", "u", "e", "o")


def _store_lint_results(context, issues: List[LintIssue]) -> None:
    context.scene["boneforge_vrm_lint_results"] = [
        {"target": i.target, "severity": i.severity,
         "message": i.message, "fix_hint": i.fix_hint}
        for i in issues
    ]


def _known_humanoid_slots() -> set:
    slots = set(_REQUIRED_HUMANOID_FOR_VRM)
    try:
        from boneforge.vrchat.humanoid import mapper as humanoid_mapper
        slots.update(humanoid_mapper.ALL_SLOTS)
    except Exception as exc:
        logger.debug("[BoneCraft] VRChat humanoid mapper unavailable: %s", exc)
    return slots


def _detect_humanoid_mapping(armature_obj) -> Dict[str, str]:
    """Return slot -> bone name using current mapping, auto-detect, and aliases."""
    bone_names = {bone.name for bone in armature_obj.data.bones}
    mapping: Dict[str, str] = {}
    humanoid_mapper = None

    try:
        from boneforge.vrchat.humanoid import mapper as humanoid_mapper
        detected = humanoid_mapper.auto_map_humanoid(armature_obj).to_dict()
        current = humanoid_mapper.get_mapping(armature_obj).to_dict()
        mapping.update({
            slot: bone for slot, bone in detected.items()
            if bone in bone_names
        })
        mapping.update({
            slot: bone for slot, bone in current.items()
            if bone in bone_names
        })
    except Exception as exc:
        logger.debug("[BoneCraft] humanoid auto-map unavailable: %s", exc)

    for bone in armature_obj.data.bones:
        alias = bone.get(_HUMANOID_ALIAS_PROP)
        if alias and alias not in mapping:
            mapping[alias] = bone.name

    for slot in _REQUIRED_HUMANOID_FOR_VRM:
        if slot not in mapping and slot in bone_names:
            mapping[slot] = slot

    known_slots = _known_humanoid_slots()
    mapping = {
        slot: bone for slot, bone in mapping.items()
        if slot in known_slots and bone in bone_names
    }

    if humanoid_mapper is not None and mapping:
        try:
            humanoid_mapper.save_mapping(
                armature_obj,
                humanoid_mapper.HumanoidMapping(mapping),
            )
        except Exception as exc:
            logger.debug("[BoneCraft] could not save humanoid mapping: %s", exc)

    return mapping


def fix_humanoid_aliases(armature_obj) -> Dict[str, str]:
    """Auto-detect humanoid bones and stamp aliases consumed by VRM lint."""
    mapping = _detect_humanoid_mapping(armature_obj)

    for slot, bone_name in mapping.items():
        target = armature_obj.data.bones.get(bone_name)
        if target is None:
            continue
        for bone in armature_obj.data.bones:
            if bone.name != target.name and bone.get(_HUMANOID_ALIAS_PROP) == slot:
                try:
                    del bone[_HUMANOID_ALIAS_PROP]
                except Exception:
                    pass
        target[_HUMANOID_ALIAS_PROP] = slot

    return mapping


def _lint_vrm_common(arm) -> List[LintIssue]:
    """Lint shared by every VRM target."""
    issues: List[LintIssue] = []

    # Required humanoid bones
    for alias in _REQUIRED_HUMANOID_FOR_VRM:
        if not _has_humanoid_alias(arm, alias):
            issues.append(LintIssue(
                target="VRM",
                severity="ERROR",
                message=f"Required humanoid bone missing: {alias}",
                fix_hint="Run BoneCraft › VRChat › Detect Convention "
                         "and remap, or stamp boneforge_humanoid_alias "
                         "manually on the correct bone.",
            ))

    # Mandatory meta block (VRM 1.0 spec requires it)
    preserved_meta = meta_mod.read_preserved_meta(arm)
    if preserved_meta is None:
        issues.append(LintIssue(
            target="VRM",
            severity="ERROR",
            message="No VRM meta/license block found on armature.",
            fix_hint="VRM 1.0 mandates author + license. Edit the "
                     "VRM Add-on's meta panel, or re-import from a "
                     ".vrm that has meta.",
        ))
    else:
        # Spot-check fields that exporters typically reject when blank.
        author_keys = ("authors", "author", "vrm_name", "title")
        if not any(preserved_meta.get(k) for k in author_keys):
            issues.append(LintIssue(
                target="VRM",
                severity="WARNING",
                message="VRM meta has no author / title field.",
                fix_hint="Set ``authors`` (VRM 1.0) or ``author`` "
                         "(VRM 0.x) in the upstream VRM panel.",
            ))

    return issues


def _lint_vsf(arm) -> List[LintIssue]:
    """VSeeFace-specific lint."""
    issues = []
    # VSeeFace eye tracking: needs LeftEye + RightEye humanoid mapping
    for eye in ("LeftEye", "RightEye"):
        if not _has_humanoid_alias(arm, eye):
            issues.append(LintIssue(
                target="VSEEFACE",
                severity="WARNING",
                message=f"{eye} humanoid bone missing — VSeeFace eye "
                        "tracking will fall back to head-tracked.",
                fix_hint=f"Stamp boneforge_humanoid_alias = '{eye}' "
                         "on the correct bone.",
            ))

    # VSeeFace strongly prefers all five visemes
    missing_visemes = [v for v in _RECOMMENDED_VISEMES if not _has_viseme(arm, v)]
    if missing_visemes:
        issues.append(LintIssue(
            target="VSEEFACE",
            severity="WARNING",
            message=f"Missing visemes for VSeeFace lipsync: "
                    f"{', '.join(missing_visemes)}",
            fix_hint="Add shape keys with names matching VRM viseme "
                     "presets ('a', 'i', 'u', 'e', 'o') and re-import, "
                     "or stamp boneforge_viseme_* on the mesh.",
        ))
    return issues


def _lint_warudo(arm) -> List[LintIssue]:
    """Warudo-specific lint (lighter than VSeeFace; mostly a stub)."""
    # Warudo is generally tolerant; just nag on missing visemes as info.
    issues = []
    if not _has_viseme(arm, "a"):
        issues.append(LintIssue(
            target="WARUDO",
            severity="WARNING",
            message="No 'a' viseme found — basic mouth tracking will be flat.",
        ))
    return issues


def _lint_resonite(arm) -> List[LintIssue]:
    """Resonite-specific lint.

    Resonite imports VRM but applies its own materials, so MToon
    parameters are decorative there. The thing it cares about most is
    bone hierarchy completeness.
    """
    issues = []
    if not _has_humanoid_alias(arm, "Neck"):
        issues.append(LintIssue(
            target="RESONITE",
            severity="WARNING",
            message="Neck humanoid bone missing — Resonite IK may snap.",
        ))
    return issues


def _lint_vrchat_fbx(arm) -> List[LintIssue]:
    """VRChat FBX target lint (delegate to existing rig validator).

    Soft-imported so this module stays standalone if advanced_rigging is unavailable.
    """
    issues = []
    try:
        from boneforge.advanced_rigging import rig_validator
        # rig_validator returns a list of dict-like results in BoneForge 3.x.
        results = rig_validator.run_all_checks(arm) if hasattr(rig_validator, "run_all_checks") else []
        for r in results:
            sev = "ERROR" if r.get("severity") in ("ERROR", "CRITICAL") else "WARNING"
            issues.append(LintIssue(
                target="VRCHAT_FBX",
                severity=sev,
                message=r.get("message", "rig validator finding"),
            ))
    except (ImportError, AttributeError) as exc:
        logger.debug("[BoneCraft] rig_validator unavailable: %s", exc)
    return issues


# ── Public API ───────────────────────────────────────────────────

def lint_for_target(armature_obj, target_id: str) -> List[LintIssue]:
    """Run all lint passes relevant to ``target_id`` and return issues."""
    issues: List[LintIssue] = []

    # All VRM targets share the common pass
    if target_id in ("VRM_1_0", "VRM_0_X", "VSEEFACE", "WARUDO", "RESONITE"):
        issues.extend(_lint_vrm_common(armature_obj))

    if target_id == "VSEEFACE":
        issues.extend(_lint_vsf(armature_obj))
    elif target_id == "WARUDO":
        issues.extend(_lint_warudo(armature_obj))
    elif target_id == "RESONITE":
        issues.extend(_lint_resonite(armature_obj))
    elif target_id == "VRCHAT_FBX":
        issues.extend(_lint_vrchat_fbx(armature_obj))

    return issues


# ── Operator (standalone lint, usable without exporting) ─────────

class BF_OT_VRMLint(Operator):
    """Lint the active armature against a chosen target."""

    bl_idname = "boneforge.vrm_lint"
    bl_label = "Lint for Target"
    bl_description = (
        "Validate the active armature against a chosen VTuber / VRChat "
        "target and report blockers + warnings without exporting"
    )
    bl_options = {"REGISTER"}

    target: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Target",
        items=[
            ("VRM_1_0", "VRM 1.0", "Modern VRM spec"),
            ("VRM_0_X", "VRM 0.x", "Legacy VRM spec"),
            ("VRCHAT_FBX", "VRChat FBX", "VRChat Avatar 3.0"),
            ("VSEEFACE", "VSeeFace", "VSeeFace VTuber host"),
            ("WARUDO", "Warudo", "Warudo VTuber host"),
            ("RESONITE", "Resonite", "Resonite social VR"),
        ],
        default="VRM_1_0",
    )

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({"ERROR"}, "No active armature")
            return {"CANCELLED"}

        issues = lint_for_target(arm, self.target)
        if not issues:
            _store_lint_results(context, [])
            self.report({"INFO"}, f"{self.target}: no issues found")
            return {"FINISHED"}

        errors = [i for i in issues if i.severity == "ERROR"]
        warns = [i for i in issues if i.severity == "WARNING"]
        for i in errors[:5]:
            self.report({"ERROR"}, f"[{i.target}] {i.message}")
        for i in warns[:5]:
            self.report({"WARNING"}, f"[{i.target}] {i.message}")

        # Stash full results on the scene so the panel can show them.
        context.scene["boneforge_vrm_lint_results"] = [
            {"target": i.target, "severity": i.severity,
             "message": i.message, "fix_hint": i.fix_hint}
            for i in issues
        ]
        self.report(
            {"INFO" if not errors else "WARNING"},
            f"{self.target}: {len(errors)} error(s), {len(warns)} warning(s)",
        )
        return {"FINISHED"}


class BF_OT_VRMFixHumanoidAliases(Operator):
    """Auto-map the active armature and stamp VRM lint humanoid aliases."""

    bl_idname = "boneforge.vrm_fix_humanoid_aliases"
    bl_label = "Fix VRM Humanoid Map"
    bl_description = (
        "Auto-detect humanoid bones, save the BoneCraft mapping, stamp "
        "VRM lint aliases, and rerun lint"
    )
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Target",
        items=_TARGET_ITEMS,
        default="VRM_1_0",
    )

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({"ERROR"}, "No active armature")
            return {"CANCELLED"}

        mapping = fix_humanoid_aliases(arm)
        if not mapping:
            self.report({"ERROR"}, "Could not detect humanoid bones")
            return {"CANCELLED"}

        issues = lint_for_target(arm, self.target)
        _store_lint_results(context, issues)
        missing = [
            i.message.rsplit(": ", 1)[-1]
            for i in issues
            if i.severity == "ERROR"
            and i.message.startswith("Required humanoid bone missing:")
        ]
        if missing:
            self.report(
                {"WARNING"},
                f"Stamped {len(mapping)} humanoid alias(es); still missing: "
                f"{', '.join(missing[:6])}",
            )
        else:
            self.report(
                {"INFO"},
                f"Stamped {len(mapping)} humanoid alias(es); humanoid lint passed",
            )
        return {"FINISHED"}
