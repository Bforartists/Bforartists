"""BoneCraft VRChat — Sidecar JSON Generation.

Generate .bfvrc JSON sidecar files containing avatar metadata,
humanoid mappings, physbone chains, colliders, viseme mappings,
and performance snapshots for VRChat imports.

Category: VRChat Export.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

import bpy
from bpy.types import Operator

from boneforge.core import active_armature
from boneforge.vrchat.performance.rank import calculate_overall_rank, count_avatar_stats
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Add-on Version
# ─────────────────────────────────────────────────────────────────

BONEFORGE_VERSION = "9.2.18"


# ─────────────────────────────────────────────────────────────────
# Sidecar Generation
# ─────────────────────────────────────────────────────────────────

def _calculate_performance_snapshot(armature) -> Dict[str, Any]:
    """Calculate comprehensive performance snapshot for the avatar.

    Uses the real rank calculator to get all 6 performance categories
    and determines overall rank.

    Args:
        armature: The armature object

    Returns:
        Dictionary with rank, polygon_count, material_count, skinned_mesh_count,
        bone_count, physbone_count, and contact_count
    """
    overall_rank, category_details = calculate_overall_rank(armature)
    stats = count_avatar_stats(armature)

    return {
        "rank": overall_rank,
        "polygon_count": stats["polygon_count"],
        "material_count": stats["material_count"],
        "skinned_mesh_count": stats["skinned_mesh_count"],
        "bone_count": stats["bone_count"],
        "physbone_count": stats["physbone_count"],
        "contact_count": stats["contact_count"],
    }


def _collect_humanoid_mapping(armature) -> Dict[str, Any]:
    """Collect Humanoid mapping from armature bones.

    First tries reading stored mapping from custom property 'boneforge_humanoid_mapping'.
    Falls back to auto-detecting bone roles based on naming conventions.
    Returns data in the format expected by the C# importer:
    {"slots": [{"slot_name": "...", "bone_name": "..."}, ...]}

    Args:
        armature: The armature object

    Returns:
        Dict with "slots" key containing array of slot/bone mappings
    """
    arm_data = armature.data

    # S-04: Try reading stored mapping first
    stored = arm_data.get("boneforge_humanoid_mapping")
    if stored:
        try:
            mapping = json.loads(stored) if isinstance(stored, str) else dict(stored)
            if mapping:
                # Convert dict format to slots array format
                slots = []
                for slot_name, bone_name in mapping.items():
                    if bone_name:
                        slots.append({
                            "slot_name": slot_name,
                            "bone_name": bone_name
                        })
                return {"slots": slots}
        except (json.JSONDecodeError, TypeError) as exc:
            logger.debug("./vrchat/export/sidecar.py suppressed (json.JSONDecodeError, TypeError): %s", exc)

    # Fall back to auto-detection
    slots = []

    # Try to find common humanoid bones by name
    # Using slot names from mapper.py REQUIRED_SLOTS
    humanoid_bones = {
        "Hips": ["Hips", "hips", "root", "Root"],
        "Spine": ["Spine", "spine", "Body", "body"],
        "Chest": ["Chest", "chest", "Upper Body", "upper_body"],
        "UpperChest": ["Upper Chest", "upper_chest", "UpperChest"],
        "Neck": ["Neck", "neck"],
        "Head": ["Head", "head"],
        "LeftShoulder": ["Left Shoulder", "LeftShoulder", "left_shoulder"],
        "RightShoulder": ["Right Shoulder", "RightShoulder", "right_shoulder"],
        "LeftUpperArm": ["Left Arm", "LeftArm", "left_arm", "Left Upper Arm", "LeftUpperArm"],
        "RightUpperArm": ["Right Arm", "RightArm", "right_arm", "Right Upper Arm", "RightUpperArm"],
        "LeftLowerArm": ["Left Forearm", "LeftForeArm", "left_forearm", "Left Lower Arm", "LeftLowerArm"],
        "RightLowerArm": ["Right Forearm", "RightForeArm", "right_forearm", "Right Lower Arm", "RightLowerArm"],
        "LeftHand": ["Left Hand", "LeftHand", "left_hand"],
        "RightHand": ["Right Hand", "RightHand", "right_hand"],
        "LeftUpperLeg": ["Left Leg", "LeftUpLeg", "left_leg", "Left Upper Leg", "LeftUpperLeg"],
        "RightUpperLeg": ["Right Leg", "RightUpLeg", "right_leg", "Right Upper Leg", "RightUpperLeg"],
        "LeftLowerLeg": ["Left Knee", "LeftLeg", "left_knee", "Left Lower Leg", "LeftLowerLeg"],
        "RightLowerLeg": ["Right Knee", "RightLeg", "right_knee", "Right Lower Leg", "RightLowerLeg"],
        "LeftFoot": ["Left Ankle", "LeftFoot", "left_ankle"],
        "RightFoot": ["Right Ankle", "RightFoot", "right_ankle"],
        "LeftEye": ["Left Eye", "LeftEye", "left_eye"],
        "RightEye": ["Right Eye", "RightEye", "right_eye"],
    }

    for slot, candidates in humanoid_bones.items():
        for candidate in candidates:
            if candidate in arm_data.bones:
                slots.append({
                    "slot_name": slot,
                    "bone_name": candidate
                })
                break

    return {"slots": slots}


def _collect_physbone_chains(armature) -> List[Dict[str, Any]]:
    """Collect physbone chain definitions from armature.

    Scans all bones in the armature for the custom property
    'boneforge_vrchat_physbone' which contains PhysBone parameters as JSON.
    Returns chains in the format expected by the C# importer.

    Args:
        armature: The armature object

    Returns:
        List of physbone chain dictionaries with root_bone, parameters, and collider_bones
    """
    chains = []
    arm_data = armature.data

    for bone in arm_data.bones:
        if "boneforge_vrchat_physbone" not in bone:
            continue

        try:
            # Parse the JSON custom property
            physbone_json = bone["boneforge_vrchat_physbone"]
            if isinstance(physbone_json, str):
                physbone_data = json.loads(physbone_json)
            else:
                physbone_data = physbone_json

            # Build the chain entry
            chain = {
                "root_bone": bone.name,
                "parameters": {
                    "pull": physbone_data.get("pull", 0.5),
                    "spring": physbone_data.get("spring", 0.5),
                    "stiffness": physbone_data.get("stiffness", 0.5),
                    "gravity": physbone_data.get("gravity", 0.0),
                    "gravity_falloff": physbone_data.get("gravity_falloff", 0.0),
                    "immobile_type": physbone_data.get("immobile_type", "AllMotion"),
                    "immobile": physbone_data.get("immobile", 0.0),
                    "max_angle": physbone_data.get("max_angle", 0.0),
                    "radius": physbone_data.get("radius", 0.1),
                    "grab_permission": physbone_data.get("grab_permission", True),
                    "pose_permission": physbone_data.get("pose_permission", True),
                },
                "collider_bones": physbone_data.get("collider_bones", []),
            }
            chains.append(chain)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[BoneCraft] Warning: Failed to parse physbone data on bone {bone.name}: {e}")
            continue

    return chains


def _collect_colliders(armature) -> List[Dict[str, Any]]:
    """Collect collider definitions from armature.

    Scans all bones and child objects for the custom property
    'boneforge_vrchat_collider' containing collider configuration as JSON.
    Returns colliders in the format expected by the C# importer.

    Args:
        armature: The armature object

    Returns:
        List of collider dictionaries with type, parent_bone, radius, height, and position_offset
    """
    colliders = []
    arm_data = armature.data

    # Scan bones for collider definitions
    for bone in arm_data.bones:
        if "boneforge_vrchat_collider" not in bone:
            continue

        try:
            # Parse the JSON custom property
            collider_json = bone["boneforge_vrchat_collider"]
            if isinstance(collider_json, str):
                collider_data = json.loads(collider_json)
            else:
                collider_data = collider_json

            # Build the collider entry
            collider = {
                "type": collider_data.get("type", "sphere"),
                "parent_bone": bone.name,
                "radius": collider_data.get("radius", 0.1),
            }

            # Optional fields
            if "height" in collider_data:
                collider["height"] = collider_data["height"]
            if "position_offset" in collider_data:
                collider["position_offset"] = collider_data["position_offset"]

            colliders.append(collider)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[BoneCraft] Warning: Failed to parse collider data on bone {bone.name}: {e}")
            continue

    # Scan child objects for collider definitions
    for child in armature.children:
        if "boneforge_vrchat_collider" not in child:
            continue

        try:
            # Parse the JSON custom property
            collider_json = child["boneforge_vrchat_collider"]
            if isinstance(collider_json, str):
                collider_data = json.loads(collider_json)
            else:
                collider_data = collider_json

            # Build the collider entry
            collider = {
                "type": collider_data.get("type", "sphere"),
                "parent_bone": collider_data.get("parent_bone", ""),
                "radius": collider_data.get("radius", 0.1),
            }

            # Optional fields
            if "height" in collider_data:
                collider["height"] = collider_data["height"]
            if "position_offset" in collider_data:
                collider["position_offset"] = collider_data["position_offset"]

            colliders.append(collider)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[BoneCraft] Warning: Failed to parse collider data on object {child.name}: {e}")
            continue

    return colliders


def _collect_viseme_mapping(armature) -> Dict[str, Any]:
    """Collect viseme-to-shape-key mapping.

    First checks for the 'boneforge_vrchat_visemes' custom property on the
    armature (a JSON dict mapping viseme names to shape key names).
    Falls back to auto-detecting VRChat viseme shape keys on mesh children.
    Returns data in the format expected by the C# importer:
    {"entries": [{"viseme_name": "...", "shape_key_name": "..."}, ...]}

    VRChat viseme names (both short and long forms):
    aa, ch, dd, e, ff, ih, oh, ou, pp, r, ss, t, th, sil, PP, FF, TH, DD, kk, CH, SS, nn, RR, E, I, O, U

    Args:
        armature: The armature object

    Returns:
        Dict with "entries" key containing array of viseme/shape_key mappings
    """
    entries = []

    # Check for explicit viseme mapping on armature
    if "boneforge_vrchat_visemes" in armature:
        try:
            viseme_json = armature["boneforge_vrchat_visemes"]
            if isinstance(viseme_json, str):
                viseme_data = json.loads(viseme_json)
            else:
                viseme_data = viseme_json

            # Convert dict to entries array
            for viseme_name, shape_key_name in viseme_data.items():
                entries.append({
                    "viseme_name": viseme_name,
                    "shape_key_name": shape_key_name,
                })
            return {"entries": entries}
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[BoneCraft] Warning: Failed to parse viseme mapping on armature: {e}")

    # Fall back to auto-detection: scan mesh children for VRChat viseme shape keys
    vrc_viseme_patterns = [
        "vrc.v_aa", "vrc.v_ch", "vrc.v_dd", "vrc.v_e", "vrc.v_ff",
        "vrc.v_ih", "vrc.v_oh", "vrc.v_ou", "vrc.v_pp", "vrc.v_r",
        "vrc.v_ss", "vrc.v_t", "vrc.v_th",
    ]

    for child in armature.children:
        if child.type != 'MESH':
            continue

        mesh = child.data
        if mesh.shape_keys is None:
            continue

        for shape_key in mesh.shape_keys.key_blocks:
            key_name = shape_key.name.lower()
            # Check if this is a VRChat viseme shape key
            for pattern in vrc_viseme_patterns:
                if pattern.lower() in key_name:
                    # Extract viseme name from the shape key name
                    # e.g., "vrc.v_aa" -> "aa"
                    viseme_name = pattern.replace("vrc.v_", "")
                    entries.append({
                        "viseme_name": viseme_name,
                        "shape_key_name": shape_key.name,
                    })
                    break

    return {"entries": entries}


def generate_sidecar(armature, export_settings) -> Dict[str, Any]:
    """Generate a complete sidecar data structure.

    Gathers all avatar metadata including humanoid mappings, physbone chains,
    colliders, viseme mappings, and a comprehensive performance snapshot.
    The output matches the C# BoneForgeImporter.cs schema exactly.

    Args:
        armature: The armature object being exported
        export_settings: BF_VRCExportSettings instance

    Returns:
        Dictionary with sidecar schema (ready for JSON serialization)
    """
    sidecar = {
        "boneforge_version": BONEFORGE_VERSION,
        "avatar_name": export_settings.avatar_name or "Avatar",
        "export_timestamp": datetime.utcnow().isoformat() + "Z",
        "humanoid_mapping": _collect_humanoid_mapping(armature),
        "physbone_chains": _collect_physbone_chains(armature),
        "colliders": _collect_colliders(armature),
        "viseme_mapping": _collect_viseme_mapping(armature),
        "performance_snapshot": _calculate_performance_snapshot(armature),
    }

    return sidecar


def write_sidecar(sidecar_data: Dict[str, Any], filepath: str) -> None:
    """Write sidecar data to a JSON file.

    Args:
        sidecar_data: Dictionary with sidecar schema
        filepath: Path to write the .bfvrc file to
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(sidecar_data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────
# Operators
# ─────────────────────────────────────────────────────────────────

class BF_OT_VRC_GenerateSidecar(Operator):
    """Generate a .bfvrc sidecar file for the active armature"""

    bl_idname = "boneforge.vrc_generate_sidecar"
    bl_label = "Generate VRChat Sidecar"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Generate and write sidecar file."""
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        settings = context.scene.boneforge_vrc_export_settings

        # Generate sidecar
        sidecar_data = generate_sidecar(arm, settings)

        # Determine output path (use export_path if set, otherwise use blend directory)
        export_dir = bpy.path.abspath(settings.export_path) if settings.export_path else ""
        if not export_dir or not os.path.isdir(export_dir):
            if bpy.data.filepath:
                export_dir = os.path.dirname(bpy.data.filepath)
            else:
                self.report({'ERROR'}, "No export directory or blend file location")
                return {'CANCELLED'}

        avatar_name = settings.avatar_name or "Avatar"
        sidecar_path = os.path.join(export_dir, f"{avatar_name}.bfvrc")

        # Write file
        try:
            write_sidecar(sidecar_data, sidecar_path)
            self.report({'INFO'}, f"Sidecar written to {sidecar_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write sidecar: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


class BF_OT_VRC_CopyUnityScriptPath(Operator):
    """Copy path to BoneForgeImporter.cs to clipboard"""

    bl_idname = "boneforge.vrc_copy_unity_script_path"
    bl_label = "Copy Unity Importer Path"
    bl_options = {'REGISTER'}

    def execute(self, context):
        """Copy the standard Unity importer script path to clipboard."""
        # Standard path where BoneForgeImporter.cs would be placed
        importer_path = "Assets/BoneForge/Editor/BoneForgeImporter.cs"

        # Use bpy.ops.wm.path_open to get clipboard (limited functionality)
        # In practice, this would need a proper clipboard API
        # For now, we'll just report the path
        self.report({'INFO'}, f"Importer path: {importer_path}")

        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

def register():
    """Register sidecar classes."""
    bpy.utils.register_class(BF_OT_VRC_GenerateSidecar)
    bpy.utils.register_class(BF_OT_VRC_CopyUnityScriptPath)


def unregister():
    """Unregister sidecar classes."""
    bpy.utils.unregister_class(BF_OT_VRC_CopyUnityScriptPath)
    bpy.utils.unregister_class(BF_OT_VRC_GenerateSidecar)
