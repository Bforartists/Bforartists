# --- VISEME LIBRARY OPERATORS (Phase 12) ---
"""Viseme capture / wiring operators.

The viseme library indirection lets one library drive any rig: built-in
poses are deltas keyed by *role* names ("jaw", "lip_upper"...). The user
maps each role to a concrete bone via the rig wiring table (handled in
the panel), and can override any built-in viseme by posing the face and
running ``Capture Viseme``.

The capture is stored as compact JSON on the scene's
``AA_P12_Properties.viseme_poses`` collection — survives file save/load.
"""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..core import p12_properties as p12_props
from ..core import p12_viseme_library as vl
from ..core.logging import get_logger

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_pose_for_roles(arm_obj: bpy.types.Object, wiring: dict[str, str]) -> vl.VisemePose:
    """Read current pose values for every wired role on the active armature."""
    pose = arm_obj.pose
    out: vl.VisemePose = {}
    for role, bone_name in wiring.items():
        if not bone_name:
            continue
        bone = pose.bones.get(bone_name)
        if bone is None:
            continue
        loc = tuple(bone.location)
        rot = tuple(bone.rotation_euler)
        scale = tuple(bone.scale)
        out[role] = (loc, rot, scale)  # type: ignore[assignment]
    return out


def _wiring_dict(p12) -> dict[str, str]:
    return {entry.role: entry.bone_name for entry in p12.rig_wiring if entry.bone_name}


# ---------------------------------------------------------------------------
# Capture viseme
# ---------------------------------------------------------------------------

class AA_OT_p12_capture_viseme(Operator):
    """Save the current pose as the named viseme, overriding the built-in."""

    bl_idname = "animassist.p12_capture_viseme"
    bl_label = "Capture Viseme"
    bl_options = {"REGISTER", "UNDO"}

    viseme_name: StringProperty(  # type: ignore[valid-type]
        name="Viseme Name",
        description="Logical viseme name; matches an entry in the active library",
        default="rest",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE":
            return False
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        if p12 is None:
            return {"CANCELLED"}
        wiring = _wiring_dict(p12)
        if not wiring:
            self.report({"ERROR"}, "No rig wiring set — fill the Rig Wiring panel first.")
            return {"CANCELLED"}
        pose = _read_pose_for_roles(context.active_object, wiring)
        if not pose:
            self.report({"WARNING"}, "No bones matched the wiring — nothing captured.")
            return {"CANCELLED"}
        payload = vl.pose_to_json(pose)

        # Replace existing capture with the same name, if any.
        for existing in p12.viseme_poses:
            if existing.viseme_name == self.viseme_name:
                existing.pose_json = payload
                existing.is_builtin = False
                self.report({"INFO"}, f"Updated capture for viseme '{self.viseme_name}'")
                return {"FINISHED"}

        entry = p12.viseme_poses.add()
        entry.viseme_name = self.viseme_name
        entry.pose_json = payload
        entry.is_builtin = False
        p12.active_viseme_index = len(p12.viseme_poses) - 1
        self.report({"INFO"}, f"Captured viseme '{self.viseme_name}'")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Reset viseme to built-in
# ---------------------------------------------------------------------------

class AA_OT_p12_reset_viseme(Operator):
    """Discard the user capture for the named viseme; revert to the library default."""

    bl_idname = "animassist.p12_reset_viseme"
    bl_label = "Reset to Built-in"
    bl_options = {"REGISTER", "UNDO"}

    viseme_name: StringProperty(  # type: ignore[valid-type]
        name="Viseme Name",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        if p12 is None:
            return {"CANCELLED"}
        for i, entry in enumerate(p12.viseme_poses):
            if entry.viseme_name == self.viseme_name:
                p12.viseme_poses.remove(i)
                self.report({"INFO"}, f"Reset viseme '{self.viseme_name}' to built-in")
                return {"FINISHED"}
        self.report({"INFO"}, f"No user capture for viseme '{self.viseme_name}' — already built-in")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Auto-fill rig wiring from library
# ---------------------------------------------------------------------------

class AA_OT_p12_autofill_wiring(Operator):
    """Pre-fill rig wiring entries by name-matching face roles to bones.

    Adds rows for any roles required by the active library that aren't yet
    in the wiring table. Best-guess only — animator confirms in the panel.
    """

    bl_idname = "animassist.p12_autofill_wiring"
    bl_label = "Autofill Rig Wiring"
    bl_options = {"REGISTER", "UNDO"}

    library_id: StringProperty(  # type: ignore[valid-type]
        name="Library",
        default="CARTOON_5",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE":
            return False
        return p12_props.get_p12(context) is not None

    def execute(self, context):
        p12 = p12_props.get_p12(context)
        arm = context.active_object
        required = vl.library_role_set(self.library_id)
        existing = {entry.role for entry in p12.rig_wiring}
        bone_names = [b.name for b in arm.data.bones]
        added = 0
        for role in sorted(required - existing):
            target = role.lower()
            match = next((b for b in bone_names if target in b.lower()), "")
            entry = p12.rig_wiring.add()
            entry.role = role
            entry.bone_name = match
            added += 1
        self.report({"INFO"}, f"Autofilled {added} rig wiring rows for {self.library_id}")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p12_capture_viseme,
    AA_OT_p12_reset_viseme,
    AA_OT_p12_autofill_wiring,
)
