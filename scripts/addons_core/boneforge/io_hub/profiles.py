"""BoneCraft — export profiles (Task 9, BF-GAP-05).

Per-target export profile definitions (pure data) plus the list of
rig-validator checks each profile runs. The actual FBX/GLB export call and
fix-application live in the operator layer (deferred to in-host); this
module is import-safe without bpy so it can be validated headlessly.

Clean-room: settings derive from public engine/format documentation.
"""

# Validator check ids (must match boneforge.advanced_rigging.rig_validator).
_ALL_CHECKS = ("naming", "structure", "weights")

EXPORT_PROFILES = {
    "unreal_humanoid": {
        "name": "Unreal Engine (Humanoid)",
        "container": "FBX",
        "axis_forward": "-Y", "axis_up": "Z",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": True, "add_leaf_bones": False,
        "root_motion": True, "custom_root": "root",
        "checks": ("naming", "structure", "weights"),
    },
    "unreal_universal": {
        "name": "Unreal Engine (Universal)",
        "container": "FBX",
        "axis_forward": "-Y", "axis_up": "Z",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": False, "add_leaf_bones": False,
        "root_motion": True, "custom_root": "root",
        "checks": ("structure", "weights"),
    },
    "unity_humanoid": {
        "name": "Unity (Humanoid)",
        "container": "FBX",
        "axis_forward": "-Z", "axis_up": "Y",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": True, "add_leaf_bones": False,
        "root_motion": True, "custom_root": "root",
        "t_pose": True,
        "checks": ("naming", "structure", "weights"),
    },
    "godot_humanoid": {
        "name": "Godot (Humanoid)",
        "container": "GLB",
        "axis_forward": "-Z", "axis_up": "Y",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": True, "add_leaf_bones": False,
        "root_motion": False, "custom_root": "root",
        "checks": ("structure", "weights"),
    },
    "vrchat": {
        "name": "VRChat Avatar",
        "container": "FBX",
        "axis_forward": "-Z", "axis_up": "Y",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": True, "add_leaf_bones": False,
        "root_motion": False, "custom_root": None,
        "t_pose": True,
        "checks": ("naming", "structure", "weights"),
    },
    "generic_fbx": {
        "name": "Generic FBX",
        "container": "FBX",
        "axis_forward": "-Z", "axis_up": "Y",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": False, "add_leaf_bones": True,
        "root_motion": False, "custom_root": None,
        "checks": ("structure",),
    },
    "generic_glb": {
        "name": "Generic glTF (GLB)",
        "container": "GLB",
        "axis_forward": "-Z", "axis_up": "Y",
        "primary_bone_axis": "Y", "secondary_bone_axis": "X",
        "deform_only": False, "add_leaf_bones": False,
        "root_motion": False, "custom_root": None,
        "checks": ("structure",),
    },
}

_REQUIRED_KEYS = {
    "name", "container", "axis_forward", "axis_up", "primary_bone_axis",
    "secondary_bone_axis", "deform_only", "add_leaf_bones", "root_motion",
    "custom_root", "checks",
}
_VALID_CONTAINERS = {"FBX", "GLB"}
_VALID_AXES = {"X", "-X", "Y", "-Y", "Z", "-Z"}


def available_profiles():
    return sorted(EXPORT_PROFILES)


def get_profile(name):
    return EXPORT_PROFILES[name]


def checks_for(name):
    return EXPORT_PROFILES[name]["checks"]


def validate_profiles():
    """Return list of problems across all profiles ([] == valid)."""
    problems = []
    for pid, prof in EXPORT_PROFILES.items():
        missing = _REQUIRED_KEYS - set(prof)
        if missing:
            problems.append("%s: missing keys %s" % (pid, sorted(missing)))
            continue
        if prof["container"] not in _VALID_CONTAINERS:
            problems.append("%s: bad container %r" % (pid, prof["container"]))
        for ax in ("axis_forward", "axis_up", "primary_bone_axis",
                   "secondary_bone_axis"):
            if prof[ax] not in _VALID_AXES:
                problems.append("%s: bad %s %r" % (pid, ax, prof[ax]))
        for chk in prof["checks"]:
            if chk not in _ALL_CHECKS:
                problems.append("%s: unknown check %r" % (pid, chk))
    return problems
