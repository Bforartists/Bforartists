# --- MOTION MATCHING IK CHAIN RESOLUTION OPERATORS ---
"""Operators for IK chain detection, inspection, and selection.

Provides a rig-agnostic workflow for discovering IK chains, navigating
their members, selecting chain bones, and feeding chain data into the
matching and switch-compensation pipeline.
"""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, IntProperty

from ..core.logging import get_logger
from ..core.p8_properties import get_p8
from ..core import p8_chain_resolver as cr
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Module-level state for chain results (mirrors detect_ops pattern)
# ---------------------------------------------------------------------------

_cached_chains: list[cr.IKChain] = []


def get_cached_chains() -> list[cr.IKChain]:
    """Return the most recently detected chains for panel display."""
    return _cached_chains


def clear_cached_chains() -> None:
    """Clear the cached chain results."""
    global _cached_chains
    _cached_chains = []


# ---------------------------------------------------------------------------
# Poll helpers
# ---------------------------------------------------------------------------

def _has_armature(context: bpy.types.Context) -> bool:
    obj = context.active_object
    return obj is not None and obj.type == "ARMATURE"


def _has_chains(context: bpy.types.Context) -> bool:
    return _has_armature(context) and len(_cached_chains) > 0


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class AA_OT_p8_detect_chains(bpy.types.Operator):
    """Scan the active armature for all IK chains."""

    bl_idname = "animassist.p8_detect_chains"
    bl_label = "Detect IK Chains"
    bl_description = (
        "Scan every pose bone on the active armature for IK constraints "
        "and resolve the full chain hierarchy from tip to root"
    )
    bl_options = {"REGISTER", "UNDO"}

    include_muted: BoolProperty(  # type: ignore[valid-type]
        name="Include Muted",
        description="Also detect chains whose IK constraint is currently muted",
        default=False,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_armature(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _cached_chains
        obj = context.active_object
        p8 = get_p8(context)

        include_muted = self.include_muted
        if p8 is not None:
            include_muted = include_muted or p8.chain_include_muted

        chains = cr.detect_ik_chains(
            obj,
            include_muted=include_muted,
            use_cache=False,
        )
        _cached_chains = chains

        if p8 is not None:
            p8.chain_last_armature = obj.name
            p8.chain_last_count = len(chains)
            p8.chain_selected_index = 0

        self.report(
            {"INFO"},
            f"Found {len(chains)} IK chain(s) on '{obj.name}'",
        )
        return {"FINISHED"}


class AA_OT_p8_detect_chain_for_bone(bpy.types.Operator):
    """Detect IK chains originating from the active bone."""

    bl_idname = "animassist.p8_detect_chain_for_bone"
    bl_label = "Detect Chain for Bone"
    bl_description = (
        "Find IK chains where the active bone is the constraint tip"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not _has_armature(context):
            return False
        return context.active_pose_bone is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _cached_chains
        obj = context.active_object
        bone = context.active_pose_bone
        p8 = get_p8(context)
        include_muted = p8.chain_include_muted if p8 else False

        chains = cr.detect_ik_chains_for_bone(
            obj, bone.name,
            include_muted=include_muted,
        )
        _cached_chains = chains

        if p8 is not None:
            p8.chain_last_armature = obj.name
            p8.chain_last_count = len(chains)
            p8.chain_selected_index = 0

        if chains:
            self.report(
                {"INFO"},
                f"Found {len(chains)} chain(s) from '{bone.name}'",
            )
        else:
            self.report(
                {"WARNING"},
                f"No IK chain originates from '{bone.name}'",
            )
        return {"FINISHED"}


class AA_OT_p8_select_chain_bones(bpy.types.Operator):
    """Select all bones belonging to the currently inspected IK chain."""

    bl_idname = "animassist.p8_select_chain_bones"
    bl_label = "Select Chain Bones"
    bl_description = (
        "Select every pose bone in the active IK chain, making it easy "
        "to key, match, or batch-process the whole chain at once"
    )
    bl_options = {"REGISTER", "UNDO"}

    chain_index: IntProperty(  # type: ignore[valid-type]
        name="Chain Index",
        description="Index into the cached chains list",
        default=0,
        min=0,
    )

    extend: BoolProperty(  # type: ignore[valid-type]
        name="Extend Selection",
        description="Add chain bones to existing selection instead of replacing",
        default=False,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_chains(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        p8 = get_p8(context)
        idx = self.chain_index
        if p8 is not None:
            idx = p8.chain_selected_index

        if idx >= len(_cached_chains):
            self.report({"WARNING"}, "Chain index out of range")
            return {"CANCELLED"}

        chain = _cached_chains[idx]
        pose = obj.pose
        if pose is None:
            self.report({"WARNING"}, "No pose data")
            return {"CANCELLED"}

        if not self.extend:
            for pbone in pose.bones:
                set_pose_bone_selected(pbone, False)

        selected_count = 0
        for name in chain.bone_names:
            pbone = pose.bones.get(name)
            if pbone is not None:
                set_pose_bone_selected(pbone, True)
                selected_count += 1

        tip = pose.bones.get(chain.tip_bone)
        if tip is not None:
            obj.data.bones.active = tip.bone

        self.report(
            {"INFO"},
            f"Selected {selected_count} bone(s) in chain "
            f"'{chain.tip_bone}' → '{chain.root_bone}'",
        )
        return {"FINISHED"}


class AA_OT_p8_chain_nav(bpy.types.Operator):
    """Navigate between detected IK chains."""

    bl_idname = "animassist.p8_chain_nav"
    bl_label = "Navigate Chains"
    bl_description = "Cycle through detected IK chains"
    bl_options = {"REGISTER", "UNDO"}

    direction: IntProperty(  # type: ignore[valid-type]
        name="Direction",
        description="+1 for next chain, -1 for previous",
        default=1,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_chains(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        p8 = get_p8(context)
        if p8 is None:
            return {"CANCELLED"}

        total = len(_cached_chains)
        new_idx = (p8.chain_selected_index + self.direction) % total
        p8.chain_selected_index = new_idx

        chain = _cached_chains[new_idx]
        self.report(
            {"INFO"},
            f"Chain {new_idx + 1}/{total}: "
            f"'{chain.tip_bone}' → '{chain.root_bone}' ({chain.length} bones)",
        )
        return {"FINISHED"}


class AA_OT_p8_chain_to_match(bpy.types.Operator):
    """Feed the selected chain's tip into the match tool.

    Copies the chain tip bone into the switch bone field so the match
    and compensation operators know which bone to operate on.
    """

    bl_idname = "animassist.p8_chain_to_match"
    bl_label = "Chain → Match"
    bl_description = (
        "Set the selected chain's tip bone as the active match target, "
        "bridging chain detection into the switch compensation workflow"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_chains(context) and get_p8(context) is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        p8 = get_p8(context)
        idx = p8.chain_selected_index
        if idx >= len(_cached_chains):
            self.report({"WARNING"}, "Chain index out of range")
            return {"CANCELLED"}

        chain = _cached_chains[idx]
        p8.switch_bone_name = chain.tip_bone
        self.report(
            {"INFO"},
            f"Match target set to '{chain.tip_bone}'",
        )
        return {"FINISHED"}


class AA_OT_p8_find_bone_chains(bpy.types.Operator):
    """Find all IK chains that pass through a specific bone."""

    bl_idname = "animassist.p8_find_bone_chains"
    bl_label = "Find Chains for Bone"
    bl_description = (
        "Find every IK chain that the active bone participates in, "
        "whether as tip, root, or intermediate member"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not _has_armature(context):
            return False
        return context.active_pose_bone is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _cached_chains
        obj = context.active_object
        bone = context.active_pose_bone
        p8 = get_p8(context)
        include_muted = p8.chain_include_muted if p8 else False

        chains = cr.find_chains_involving_bone(
            obj, bone.name,
            include_muted=include_muted,
        )
        _cached_chains = chains

        if p8 is not None:
            p8.chain_last_armature = obj.name
            p8.chain_last_count = len(chains)
            p8.chain_selected_index = 0

        if chains:
            self.report(
                {"INFO"},
                f"'{bone.name}' participates in {len(chains)} chain(s)",
            )
        else:
            self.report(
                {"WARNING"},
                f"'{bone.name}' is not part of any IK chain",
            )
        return {"FINISHED"}


class AA_OT_p8_chain_summary(bpy.types.Operator):
    """Print a diagnostic summary of all IK chains to the info area."""

    bl_idname = "animassist.p8_chain_summary"
    bl_label = "Chain Summary"
    bl_description = (
        "Generate a diagnostic report of all IK chains on the active "
        "armature and display it in the info header"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _has_armature(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        p8 = get_p8(context)
        include_muted = p8.chain_include_muted if p8 else False

        summary = cr.get_chain_summary(obj, include_muted=include_muted)
        self.report(
            {"INFO"},
            f"{summary['total_chains']} chain(s) "
            f"({summary['active_chains']} active, "
            f"{summary['muted_chains']} muted) — "
            f"longest: {summary['longest_chain']} bones",
        )
        _log.info("Chain summary for %s: %s", obj.name, summary)
        return {"FINISHED"}


class AA_OT_p8_invalidate_chain_cache(bpy.types.Operator):
    """Clear the IK chain detection cache to force a fresh scan."""

    bl_idname = "animassist.p8_invalidate_chain_cache"
    bl_label = "Clear Chain Cache"
    bl_description = (
        "Clear cached chain detection results so the next scan "
        "performs a fresh hierarchy walk"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        cr.invalidate_chain_cache()
        clear_cached_chains()
        p8 = get_p8(context)
        if p8 is not None:
            p8.chain_last_count = 0
            p8.chain_selected_index = 0
        self.report({"INFO"}, "Chain cache cleared")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p8_detect_chains,
    AA_OT_p8_detect_chain_for_bone,
    AA_OT_p8_select_chain_bones,
    AA_OT_p8_chain_nav,
    AA_OT_p8_chain_to_match,
    AA_OT_p8_find_bone_chains,
    AA_OT_p8_chain_summary,
    AA_OT_p8_invalidate_chain_cache,
)
