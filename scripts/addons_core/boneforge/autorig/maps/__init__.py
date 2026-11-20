"""BoneCraft — source-skeleton mapping presets (Task 8, BF-DATA-02).

Maps source bone names (public engine/format naming standards) to the
BoneCraft control rig's target bones. Tables are original JSON authored
from publicly documented conventions — no third-party rig's preset files
are copied. Used by the retargeting workflow (Task 7).

Pure Python (json only); no bpy.
"""
import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

# BoneForge target bones a source map may legally point at (FK controls +
# spine). Kept in sync with rig_build via tests/test_maps.py.
TARGET_BONES = {
    "hips", "spine.01", "spine.02", "chest", "neck", "head",
    "clavicle.fk-L", "clavicle.fk-R",
    "upperarm.fk-L", "upperarm.fk-R",
    "forearm.fk-L", "forearm.fk-R",
    "hand.fk-L", "hand.fk-R",
    "thigh.fk-L", "thigh.fk-R",
    "shin.fk-L", "shin.fk-R",
    "foot.fk-L", "foot.fk-R",
}


def available_maps():
    return sorted(f[:-5] for f in os.listdir(_DIR) if f.endswith(".json"))


def load_map(name):
    path = os.path.join(_DIR, name + ".json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_map(data):
    """Return list of problems ([] == valid)."""
    problems = []
    if "name" not in data or "bones" not in data:
        problems.append("missing 'name' or 'bones'")
        return problems
    if not isinstance(data["bones"], dict) or not data["bones"]:
        problems.append("'bones' must be a non-empty object")
        return problems
    for src, tgt in data["bones"].items():
        if tgt not in TARGET_BONES:
            problems.append("unknown target bone: %r (from source %r)"
                            % (tgt, src))
    return problems
