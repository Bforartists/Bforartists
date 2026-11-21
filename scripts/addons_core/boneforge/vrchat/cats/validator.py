"""BoneCraft VRChat CATS — Pre-flight Phase Dependency Validator.

Pure-Python module: no bpy types, no register/unregister.

Validates that required upstream pipeline phases have been completed before
a downstream phase is allowed to run. Callers receive a list of unmet
dependency phase IDs and optional human-readable warning text. All checks
are non-blocking — callers decide whether to abort or warn-and-continue.
"""

from boneforge.vrchat.cats.pipeline import is_phase_complete

# ── Phase dependency map ────────────────────────────────────────────────────

# Maps each phase_id to the list of phase_ids that should be completed first
# for best results. An empty list means the phase has no hard dependencies.
PHASE_DEPS: dict[str, list[str]] = {
    "fix_model": [],
    "visemes": ["fix_model"],
    "eye_tracking": ["fix_model"],
    "pose_to_shape": [],
    "apply_transforms": [],
    "merge_armatures": [],
}

# ── Human-readable phase names ──────────────────────────────────────────────

_PHASE_DISPLAY_NAMES: dict[str, str] = {
    "fix_model": "Fix Model",
    "visemes": "Visemes",
    "eye_tracking": "Eye Tracking",
    "pose_to_shape": "Pose to Shape",
    "apply_transforms": "Apply Transforms",
    "merge_armatures": "Merge Armatures",
}


def phase_display_name(phase_id: str) -> str:
    """Return a human-readable name for *phase_id*.

    Falls back to a title-cased version of the ID when the phase is not
    in the known-names table (e.g. future phases added without updating
    this module).
    """
    return _PHASE_DISPLAY_NAMES.get(phase_id, phase_id.replace("_", " ").title())


# ── Validation logic ────────────────────────────────────────────────────────

def validate_phase(scene, phase_id: str) -> list[str]:
    """Return a list of dependency phase_ids that have not yet been completed.

    An empty list means all dependencies are satisfied (or the phase has
    none). The caller can use this to decide whether to block or warn.

    Args:
        scene:    The active bpy.types.Scene (or any object that supports
                  scene.get() for custom properties).
        phase_id: The phase about to be executed.

    Returns:
        List of unmet dependency phase_ids (may be empty).
    """
    deps = PHASE_DEPS.get(phase_id, [])
    return [dep for dep in deps if not is_phase_complete(scene, dep)]


def get_warning_message(scene, phase_id: str):
    """Return a formatted warning string if any dependencies are unmet.

    Returns None when all dependencies are satisfied so callers can use a
    simple ``if msg:`` guard without checking for empty strings.

    Example output: "Tip: Run Fix Model first for best results"
    """
    unmet = validate_phase(scene, phase_id)
    if not unmet:
        return None

    if len(unmet) == 1:
        dep_name = phase_display_name(unmet[0])
        return f"Tip: Run {dep_name} first for best results"

    dep_names = ", ".join(phase_display_name(d) for d in unmet)
    return f"Tip: Run {dep_names} first for best results"
