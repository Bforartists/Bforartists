# --- SPACE-SWITCH DETECTION ---
"""Rig-agnostic space-switch pattern detection.

Scans objects (typically armature pose bones) for custom properties,
constraint configurations, and driver setups that look like space-switch
controls.  Returns ranked ``SwitchPattern`` results that the UI and
operators can present to the user.

Detection heuristics are intentionally generous — false positives are
preferable to missed patterns because the user can easily dismiss a
suggestion but cannot discover a hidden switch control.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .logging import get_logger

_log = get_logger(__name__)

__all__ = [
    "SwitchKind",
    "SwitchPattern",
    "detect_space_enums",
    "detect_bool_patterns",
    "detect_influence_patterns",
    "detect_custom_props",
    "detect_all_patterns",
    "validate_pattern",
]

# ---------------------------------------------------------------------------
# Pattern result dataclass
# ---------------------------------------------------------------------------

SwitchKind = Literal["ENUM", "BOOL", "INFLUENCE", "CUSTOM_PROP"]


@dataclass
class SwitchPattern:
    """A detected space-switch control on a rig."""

    obj_name: str
    bone_name: str  # Empty string for object-level properties.
    prop_path: str  # RNA or custom-prop path (e.g. '["space_switch"]').
    kind: SwitchKind
    current_value: object = None
    values: list | None = None  # Possible enum/bool values.
    labels: list[str] | None = None  # Human labels for values.
    confidence: float = 0.0  # 0.0–1.0 heuristic score.
    constraint_name: str = ""  # If tied to a constraint.
    description: str = ""

    def display_label(self) -> str:
        """Short label for UI lists."""
        base = self.bone_name or self.obj_name
        return f"{base} → {self.prop_path}"


# ---------------------------------------------------------------------------
# Keyword dictionaries (scored by relevance)
# ---------------------------------------------------------------------------

_SPACE_KEYWORDS: dict[str, float] = {
    "space": 0.9,
    "switch": 0.85,
    "parent": 0.7,
    "follow": 0.7,
    "ik_fk": 0.6,
    "ikfk": 0.6,
    "fk_ik": 0.6,
    "orient": 0.5,
    "world": 0.5,
    "local": 0.4,
    "snap": 0.3,
    "pole": 0.3,
}

_CONSTRAINT_TYPES_SPACE = {
    "CHILD_OF",
    "COPY_TRANSFORMS",
    "COPY_LOCATION",
    "COPY_ROTATION",
    "ARMATURE",
}


def _keyword_score(name: str) -> float:
    """Score a property/constraint name against known space-switch keywords."""
    lower = name.lower()
    best = 0.0
    for kw, score in _SPACE_KEYWORDS.items():
        if kw in lower:
            best = max(best, score)
    return best


# ---------------------------------------------------------------------------
# Detection: custom enum / integer properties
# ---------------------------------------------------------------------------

def detect_space_enums(obj) -> list[SwitchPattern]:  # type: ignore[no-untyped-def]
    """Scan *obj* (and its pose bones) for custom integer/enum properties
    whose names suggest a space-switch control.
    """
    results: list[SwitchPattern] = []

    # Object-level custom properties.
    _collect_enum_patterns(results, obj.name, "", obj)

    # Pose-bone custom properties.
    if hasattr(obj, "pose") and obj.pose:
        for bone in obj.pose.bones:
            _collect_enum_patterns(results, obj.name, bone.name, bone)

    results.sort(key=lambda p: p.confidence, reverse=True)
    return results


def _collect_enum_patterns(
    results: list[SwitchPattern],
    obj_name: str,
    bone_name: str,
    source,  # type: ignore[no-untyped-def]
) -> None:
    """Helper: collect enum patterns from object or bone."""
    for key in source.keys():
        if key.startswith("_"):
            continue
        score = _keyword_score(key)
        # Boost score if bone name also matches.
        if bone_name:
            bone_score = _keyword_score(bone_name)
            score = min(1.0, score + bone_score * 0.2)
        if score < 0.3:
            continue
        val = source[key]
        if not isinstance(val, (int, float)):
            continue
        results.append(SwitchPattern(
            obj_name=obj_name,
            bone_name=bone_name,
            prop_path=f'["{key}"]',
            kind="ENUM",
            current_value=val,
            confidence=score,
            description=(
                f"{'Bone' if bone_name else 'Custom property'} "
                f"{bone_name or obj_name!r} '{key}' (value={val})"
            ),
        ))


# ---------------------------------------------------------------------------
# Detection: boolean switch properties
# ---------------------------------------------------------------------------

def detect_bool_patterns(obj) -> list[SwitchPattern]:  # type: ignore[no-untyped-def]
    """Scan for boolean (0/1) custom properties that look like toggles."""
    results: list[SwitchPattern] = []

    _collect_bool_patterns(results, obj.name, "", obj)

    if hasattr(obj, "pose") and obj.pose:
        for bone in obj.pose.bones:
            _collect_bool_patterns(results, obj.name, bone.name, bone)

    results.sort(key=lambda p: p.confidence, reverse=True)
    return results


def _collect_bool_patterns(
    results: list[SwitchPattern],
    obj_name: str,
    bone_name: str,
    source,  # type: ignore[no-untyped-def]
) -> None:
    """Helper: collect boolean patterns from object or bone."""
    for key in source.keys():
        if key.startswith("_"):
            continue
        val = source[key]
        if not isinstance(val, (int, float)):
            continue
        if val not in (0, 1, 0.0, 1.0):
            continue
        score = _keyword_score(key)
        if score < 0.25:
            continue
        results.append(SwitchPattern(
            obj_name=obj_name,
            bone_name=bone_name,
            prop_path=f'["{key}"]',
            kind="BOOL",
            current_value=bool(val),
            values=[False, True],
            labels=["Off", "On"],
            confidence=score,
            description=f"Boolean toggle '{key}' on {bone_name or obj_name}",
        ))


# ---------------------------------------------------------------------------
# Detection: constraint influence switches
# ---------------------------------------------------------------------------

def detect_influence_patterns(obj) -> list[SwitchPattern]:  # type: ignore[no-untyped-def]
    """Scan constraints whose type suggests space-switching and whose
    influence is keyframed or driven.
    """
    results: list[SwitchPattern] = []

    # Object-level constraints.
    _scan_constraints(results, obj.name, "", obj.constraints)

    # Pose-bone constraints.
    if hasattr(obj, "pose") and obj.pose:
        for bone in obj.pose.bones:
            _scan_constraints(results, obj.name, bone.name, bone.constraints)

    results.sort(key=lambda p: p.confidence, reverse=True)
    return results


def _scan_constraints(
    results: list[SwitchPattern],
    obj_name: str,
    bone_name: str,
    constraints,  # type: ignore[no-untyped-def]
) -> None:
    """Helper: scan constraints for influence patterns."""
    for con in constraints:
        if con.type not in _CONSTRAINT_TYPES_SPACE:
            continue
        score = 0.5
        name_score = _keyword_score(con.name)
        score = min(1.0, score + name_score)
        results.append(SwitchPattern(
            obj_name=obj_name,
            bone_name=bone_name,
            prop_path=f'constraints["{con.name}"].influence',
            kind="INFLUENCE",
            current_value=con.influence,
            values=[0.0, 1.0],
            labels=["Off", "On"],
            confidence=score,
            constraint_name=con.name,
            description=(
                f"{con.type} constraint '{con.name}' on "
                f"{bone_name or obj_name} (influence={con.influence:.2f})"
            ),
        ))


# ---------------------------------------------------------------------------
# Detection: generic custom property (catch-all)
# ---------------------------------------------------------------------------

def detect_custom_props(obj) -> list[SwitchPattern]:  # type: ignore[no-untyped-def]
    """Broad scan for any numeric custom property.  Low confidence unless
    name matches keywords.
    """
    results: list[SwitchPattern] = []

    _scan_custom_props(results, obj.name, "", obj)
    if hasattr(obj, "pose") and obj.pose:
        for bone in obj.pose.bones:
            _scan_custom_props(results, obj.name, bone.name, bone)

    results.sort(key=lambda p: p.confidence, reverse=True)
    return results


def _scan_custom_props(
    results: list[SwitchPattern],
    obj_name: str,
    bone_name: str,
    source,  # type: ignore[no-untyped-def]
) -> None:
    """Helper: scan for generic custom properties."""
    for key in source.keys():
        if key.startswith("_"):
            continue
        val = source[key]
        if not isinstance(val, (int, float)):
            continue
        score = _keyword_score(key)
        if score < 0.15:
            # Still include if it looks numeric and user-created.
            score = 0.15
        results.append(SwitchPattern(
            obj_name=obj_name,
            bone_name=bone_name,
            prop_path=f'["{key}"]',
            kind="CUSTOM_PROP",
            current_value=val,
            confidence=score,
            description=f"Custom property '{key}' = {val}",
        ))


# ---------------------------------------------------------------------------
# Combined detection
# ---------------------------------------------------------------------------

def detect_all_patterns(obj) -> list[SwitchPattern]:
    """Run all detectors and return a merged, deduplicated list sorted by
    confidence.  Higher-specificity detectors override the generic one.
    """
    seen: set[tuple[str, str, str]] = set()
    merged: list[SwitchPattern] = []

    # Higher-specificity first.
    for detector in (detect_space_enums, detect_bool_patterns,
                     detect_influence_patterns):
        for pat in detector(obj):
            key = (pat.obj_name, pat.bone_name, pat.prop_path)
            if key not in seen:
                seen.add(key)
                merged.append(pat)

    # Generic catch-all last (only add unseen).
    for pat in detect_custom_props(obj):
        key = (pat.obj_name, pat.bone_name, pat.prop_path)
        if key not in seen:
            seen.add(key)
            merged.append(pat)

    merged.sort(key=lambda p: p.confidence, reverse=True)
    return merged


# ---------------------------------------------------------------------------
# Validation: check if a pattern is still valid on the current rig
# ---------------------------------------------------------------------------

def validate_pattern(pattern: SwitchPattern) -> bool:
    """Return True if the pattern's target still exists in the scene."""
    import bpy

    obj = bpy.data.objects.get(pattern.obj_name)
    if obj is None:
        return False

    # If pattern is for a bone, check it exists.
    if not pattern.bone_name:
        return True

    if not (hasattr(obj, "pose") and obj.pose):
        return False
    return obj.pose.bones.get(pattern.bone_name) is not None
