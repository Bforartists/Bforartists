"""MMD rigid body joints → VRC PhysBone chain conversion.

Heuristic pass that detects which armature bones are driven by MMD
physics (via mmd_tools rigid body objects) and writes VRC PhysBone
parameter JSON onto the chain root bones so the VRChat SDK can pick
them up in Unity.

Requires mmd_tools to be enabled. Requires the active object to be
an armature that is part of an MMD model (parent empty with
mmd_type == 'ROOT', or rigid body objects in the scene referencing
this armature's bones).

Receipt stored under ``boneforge_mmd_physics_receipt`` on the armature.
"""

import bpy
from bpy.types import Operator

import logging

logger = logging.getLogger(__name__)

# Default PhysBone parameters used for converted MMD physics chains.
# These are the same as the Hair preset in vrchat/hair/physbone.py.
_DEFAULT_PHYSBONE = {
    "version":        1,
    "pull":           0.2,
    "spring":         0.4,
    "stiffness":      0.2,
    "gravity":        0.3,
    "gravity_falloff": 1.0,
    "immobile_type":  "ALL_MOTION",
    "immobile":       0.0,
    "max_angle":      60.0,
    "radius":         0.02,
    "grab_permission": True,
    "pose_permission": True,
    "source":         "mmd_converted",
}


def _find_physics_bones(arm_obj: bpy.types.Object) -> list[str]:
    """Return bone names that are driven by MMD rigid bodies.

    Walks all objects in the scene looking for MESH/EMPTY objects that
    have ``mmd_type == 'RIGID_BODY'`` and whose ``mmd_rigid.bone``
    references a bone in *arm_obj*.  Falls back to looking at rigid
    bodies parented anywhere in the scene if the parent chain doesn't
    resolve to our armature.
    """
    arm_bone_names = {b.name for b in arm_obj.data.bones}
    physics_bones: set[str] = set()

    for obj in bpy.data.objects:
        mmd_type = getattr(obj, "mmd_type", None)
        if mmd_type != "RIGID_BODY":
            continue
        rigid = getattr(obj, "mmd_rigid", None)
        if rigid is None:
            continue
        bone_name = getattr(rigid, "bone", None)
        if not bone_name:
            continue
        rb_type = getattr(rigid, "type", 0)
        # Only physics (1) and physics+bone (2) types move bones.
        if rb_type not in (1, 2):
            continue
        if bone_name in arm_bone_names:
            physics_bones.add(bone_name)

    return list(physics_bones)


def _find_chain_roots(arm_obj: bpy.types.Object,
                      physics_set: set[str]) -> list[str]:
    """Return the root bone name of each contiguous physics chain.

    A chain root is a physics bone whose parent is NOT also a physics
    bone (or has no parent).
    """
    roots = []
    for bone in arm_obj.data.bones:
        if bone.name not in physics_set:
            continue
        parent_is_physics = (
            bone.parent is not None and bone.parent.name in physics_set
        )
        if not parent_is_physics:
            roots.append(bone.name)
    return roots


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_MMDConvertPhysics(Operator):
    """Convert MMD rigid body chains to VRC PhysBone parameters."""

    bl_idname  = "boneforge.mmd_convert_physics"
    bl_label   = "Convert MMD Physics → PhysBones"
    bl_description = (
        "Detect MMD rigid body physics chains on the active armature "
        "and write VRC PhysBone parameters on each chain root bone. "
        "Requires mmd_tools and an imported MMD model."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context):
        arm_obj = context.active_object

        physics_bones = _find_physics_bones(arm_obj)
        if not physics_bones:
            self.report(
                {"WARNING"},
                "No MMD physics bones found on this armature. "
                "Make sure mmd_tools is enabled and the model was "
                "imported via BoneCraft or mmd_tools.",
            )
            return {"CANCELLED"}

        physics_set = set(physics_bones)
        roots = _find_chain_roots(arm_obj, physics_set)
        if not roots:
            roots = physics_bones[:1]  # fallback: treat first as root

        import json
        chains_created = []
        for root_name in roots:
            bone = arm_obj.data.bones.get(root_name)
            if bone is None:
                continue
            chain = _collect_chain(arm_obj, root_name, physics_set)
            config = dict(_DEFAULT_PHYSBONE)
            config["chain_length"] = len(chain)
            bone["boneforge_vrchat_physbone"] = json.dumps(config)
            chains_created.append({"root": root_name, "length": len(chain)})
            logger.info(
                "[BoneCraft] MMD→PhysBone chain root=%s length=%d",
                root_name, len(chain),
            )

        from boneforge.core import write_custom_json
        receipt = {
            "physics_bones":  physics_bones,
            "chains_created": chains_created,
            "total_physics":  len(physics_bones),
        }
        write_custom_json(arm_obj, "boneforge_mmd_physics_receipt", receipt)

        self.report(
            {"INFO"},
            f"MMD physics: {len(physics_bones)} physics bones → "
            f"{len(chains_created)} PhysBone chain(s) created",
        )
        return {"FINISHED"}


def _collect_chain(arm_obj: bpy.types.Object,
                   root_name: str,
                   physics_set: set[str]) -> list[str]:
    """Return all bone names in the physics chain starting at *root_name*."""
    chain = []
    stack = [root_name]
    while stack:
        name = stack.pop()
        if name not in physics_set:
            continue
        chain.append(name)
        bone = arm_obj.data.bones.get(name)
        if bone is None:
            continue
        for child in bone.children:
            stack.append(child.name)
    return chain
