"""BoneCraft VRChat — Chain Detection and State Assessment.

Scans armature for bone chains that are PhysBone candidates.
A chain candidate = 3+ bones where each has exactly one child and no IK constraints.
Chains with existing PhysBone metadata (boneforge_vrchat_physbone) are marked configured.

Category: Hair Physics.
"""

import bpy
from bpy.types import Operator, Panel
from typing import NamedTuple, Optional
from boneforge.core import active_armature, read_custom_json
from boneforge.i18n import T


# ── Data structures ────────────────────────────────────────────

class ChainInfo(NamedTuple):
    """Information about a detected bone chain."""
    root_bone: str
    length: int
    is_configured: bool
    bone_names: list[str]


# ── Detection states ────────────────────────────────────────────

STATE_CONFIGURED = 1
STATE_UNCONFIGURED_CANDIDATES = 2
STATE_NO_CHAINS = 3


# ── Chain detection logic ──────────────────────────────────────

def _is_chain_candidate(bone: bpy.types.Bone, visited: set) -> bool:
    """Check if a bone is a valid chain start (not in another chain yet)."""
    return bone.name not in visited


def _has_ik_constraints(bone: bpy.types.PoseBone) -> bool:
    """Check if a bone has any IK constraints."""
    for constraint in bone.constraints:
        if constraint.type == 'IK':
            return True
    return False


def _trace_chain(root_bone: bpy.types.Bone, pose_bones: dict) -> Optional[list[str]]:
    """Trace a chain from root_bone by following single-child lineage.

    Returns list of bone names (length 3+) or None if chain is too short.
    Stops if any bone has 0 children, multiple children, or IK constraints.
    """
    chain = [root_bone.name]
    current = root_bone

    # Check root for IK constraints
    if root_bone.name in pose_bones and _has_ik_constraints(pose_bones[root_bone.name]):
        return None

    while len(current.children) == 1:
        child = current.children[0]
        chain.append(child.name)

        # Check child for IK constraints
        if child.name in pose_bones and _has_ik_constraints(pose_bones[child.name]):
            return None

        current = child

    # Valid chain must have 3+ bones
    return chain if len(chain) >= 3 else None


def _is_physbone_configured(bone: bpy.types.Bone) -> bool:
    """Check if bone has PhysBone metadata stored."""
    metadata = read_custom_json(bone, "boneforge_vrchat_physbone", {})
    return bool(metadata)


def detect_chains(armature) -> list[ChainInfo]:
    """Scan armature for bone chain candidates.

    Args:
        armature: Either an Armature Object or Armature data block.
            If an Object is passed, pose bones are used for IK filtering.
            If a data block is passed, IK filtering is skipped.

    Returns a list of ChainInfo objects describing detected chains.
    Each chain has 3+ bones with single-child lineage and no IK constraints.
    """
    chains = []
    visited = set()

    # B-13: Handle both Object and Armature data block
    # bpy.types.Armature (data block) has no .pose — only the Object does
    if hasattr(armature, 'pose') and armature.pose:
        # armature is an Object
        arm_data = armature.data
        pose_bones = {b.name: b for b in armature.pose.bones}
    elif hasattr(armature, 'bones'):
        # armature is a data block
        arm_data = armature
        pose_bones = {}
    else:
        return []

    # Iterate through all bones, skipping those already in detected chains
    for bone in arm_data.bones:
        if not _is_chain_candidate(bone, visited):
            continue

        # Try to trace a chain from this bone
        chain_bones = _trace_chain(bone, pose_bones)
        if chain_bones is None:
            continue

        # Mark all bones in this chain as visited
        for bone_name in chain_bones:
            visited.add(bone_name)

        # Check if chain is configured
        root = arm_data.bones[chain_bones[0]]
        is_configured = _is_physbone_configured(root)

        chains.append(ChainInfo(
            root_bone=chain_bones[0],
            length=len(chain_bones),
            is_configured=is_configured,
            bone_names=chain_bones,
        ))

    return chains


def get_detection_state(armature) -> tuple[int, list[ChainInfo]]:
    """Assess armature's hair chain state.

    Returns (state_int, chain_list) where state is one of:
    - STATE_CONFIGURED: chains found with PhysBone metadata
    - STATE_UNCONFIGURED_CANDIDATES: chains found without metadata
    - STATE_NO_CHAINS: no chains found
    """
    chains = detect_chains(armature)

    if not chains:
        return STATE_NO_CHAINS, []

    configured_chains = [c for c in chains if c.is_configured]
    if configured_chains:
        return STATE_CONFIGURED, chains
    else:
        return STATE_UNCONFIGURED_CANDIDATES, chains


# ── Operators ──────────────────────────────────────────────────

class BF_OT_VRC_DetectChains(Operator):
    """Scan armature for hair physics chain candidates."""

    bl_idname = "boneforge.vrc_detect_chains"
    bl_label = "Detect Hair Physics Chains"
    bl_description = "Scan the active armature for bone chain candidates"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature found")
            return {'CANCELLED'}

        arm_data = arm_obj.data
        state, chains = get_detection_state(arm_data)

        if state == STATE_CONFIGURED:
            msg = f"Found {len(chains)} hair physics chains (configured)"
            self.report({'INFO'}, msg)
        elif state == STATE_UNCONFIGURED_CANDIDATES:
            msg = f"Found {len(chains)} bone chains — add physics?"
            self.report({'INFO'}, msg)
        else:
            self.report({'INFO'}, "No hair bones found")

        return {'FINISHED'}


# ── Panels ─────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_hair_detect(Panel):
    """Hair Physics Detection Panel."""

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = " "
    bl_parent_id = "BONEFORGE_PT_vrc_hair"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Hair Chain Detection"))

    @classmethod
    def poll(cls, context):
        """Show panel only when active object is an armature."""
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        arm_obj = active_armature(context)
        if arm_obj is None:
            return

        arm_data = arm_obj.data
        state, chains = get_detection_state(arm_data)

        # Status indicator
        if state == STATE_CONFIGURED:
            configured_count = sum(1 for c in chains if c.is_configured)
            layout.label(text=f"✓ {configured_count} chains configured", icon='CHECKMARK')
        elif state == STATE_UNCONFIGURED_CANDIDATES:
            layout.label(text=f"◇ {len(chains)} chains found", icon='QUESTION')
        else:
            layout.label(text=T("No chains detected"), icon='ERROR')

        # Chain list
        if chains:
            col = layout.column(align=True)
            for chain in chains:
                row = col.row(align=True)
                icon = 'CHECKMARK' if chain.is_configured else 'BLANK1'
                row.label(text=f"  {chain.root_bone} ({chain.length})", icon=icon)

        # Detect button
        layout.operator("boneforge.vrc_detect_chains")


def register():
    """Register chain detection operators and panels."""
    bpy.utils.register_class(BF_OT_VRC_DetectChains)
    bpy.utils.register_class(BONEFORGE_PT_vrc_hair_detect)


def unregister():
    """Unregister chain detection operators and panels."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_hair_detect)
    bpy.utils.unregister_class(BF_OT_VRC_DetectChains)
