"""BoneCraft VRChat — Humanoid Bone Mapper.

Map armature bones to Unity Humanoid bone slots (21 required, many optional).
Store and retrieve mappings from armature custom properties.
Category: VRChat Setup.
"""

import json

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel

from boneforge.core import active_armature

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────

# Unity's minimum humanoid body slots required for export.
REQUIRED_SLOTS = [
    "Hips",
    "Spine",
    "Head",
    "LeftUpperArm",
    "RightUpperArm",
    "LeftLowerArm",
    "RightLowerArm",
    "LeftHand",
    "RightHand",
    "LeftUpperLeg",
    "RightUpperLeg",
    "LeftLowerLeg",
    "RightLowerLeg",
    "LeftFoot",
    "RightFoot",
]

# Useful for VRChat tracking quality, but not required by the export gate.
RECOMMENDED_SLOTS = [
    "Chest",
    "UpperChest",
    "Neck",
    "LeftShoulder",
    "RightShoulder",
]

# Optional slots beyond the required body set.
OPTIONAL_SLOTS = [
    *RECOMMENDED_SLOTS,
    "Jaw",
    "LeftEye",
    "RightEye",
    "LeftThumbProximal",
    "LeftThumbIntermediate",
    "LeftThumbDistal",
    "LeftIndexProximal",
    "LeftIndexIntermediate",
    "LeftIndexDistal",
    "LeftMiddleProximal",
    "LeftMiddleIntermediate",
    "LeftMiddleDistal",
    "LeftRingProximal",
    "LeftRingIntermediate",
    "LeftRingDistal",
    "LeftLittleProximal",
    "LeftLittleIntermediate",
    "LeftLittleDistal",
    "RightThumbProximal",
    "RightThumbIntermediate",
    "RightThumbDistal",
    "RightIndexProximal",
    "RightIndexIntermediate",
    "RightIndexDistal",
    "RightMiddleProximal",
    "RightMiddleIntermediate",
    "RightMiddleDistal",
    "RightRingProximal",
    "RightRingIntermediate",
    "RightRingDistal",
    "RightLittleProximal",
    "RightLittleIntermediate",
    "RightLittleDistal",
    "LeftToes",
    "RightToes",
]

ALL_SLOTS = REQUIRED_SLOTS + OPTIONAL_SLOTS


# ── HumanoidMapping class ────────────────────────────────────────────

class HumanoidMapping:
    """Stores slot → bone_name mappings for a humanoid avatar."""

    def __init__(self, mapping_dict=None):
        """Initialize from dict or empty."""
        self.mapping = mapping_dict or {}

    def set_slot(self, slot_name, bone_name):
        """Map a slot to a bone name."""
        if bone_name:
            self.mapping[slot_name] = bone_name
        else:
            self.mapping.pop(slot_name, None)

    def get_slot(self, slot_name):
        """Get bone name for a slot, or None."""
        return self.mapping.get(slot_name)

    def to_dict(self):
        """Export as dict."""
        return dict(self.mapping)

    def validate_required(self, armature=None):
        """Check which required slots are missing or point to absent bones."""
        bone_names = None
        if armature is not None and getattr(armature, "type", None) == "ARMATURE":
            bone_names = {bone.name for bone in armature.data.bones}

        missing = []
        for slot in REQUIRED_SLOTS:
            bone_name = self.mapping.get(slot)
            if not bone_name or (bone_names is not None and bone_name not in bone_names):
                missing.append(slot)
        return missing

    def completion_percent(self, armature=None):
        """Return percentage of required slots mapped (0-100)."""
        bone_names = None
        if armature is not None and getattr(armature, "type", None) == "ARMATURE":
            bone_names = {bone.name for bone in armature.data.bones}
        mapped = sum(
            1
            for slot in REQUIRED_SLOTS
            if self.mapping.get(slot)
            and (bone_names is None or self.mapping[slot] in bone_names)
        )
        return int((mapped / len(REQUIRED_SLOTS)) * 100)


# ── Utility functions ────────────────────────────────────────────────

def _get_armature_bones(armature):
    """Get all bone names in an armature."""
    if not armature or armature.type != "ARMATURE":
        return []
    return [b.name for b in armature.data.bones]


def _normalize_bone_name(name):
    """Normalize separators/case so common rig names match consistently."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _bone_path_between(armature, start_name, end_name):
    """Return the parent-chain path from start to end, or [] when unrelated."""
    if not start_name or not end_name:
        return []
    bones = armature.data.bones
    if start_name not in bones or end_name not in bones:
        return []

    path = []
    bone = bones[end_name]
    while bone is not None:
        path.append(bone.name)
        if bone.name == start_name:
            return list(reversed(path))
        bone = bone.parent
    return []


def _infer_lower_leg_from_chain(armature, mapping_dict, side):
    """Infer lower leg as the parent-chain bone between upper leg and foot."""
    slot = f"{side}LowerLeg"
    if mapping_dict.get(slot):
        return

    path = _bone_path_between(
        armature,
        mapping_dict.get(f"{side}UpperLeg"),
        mapping_dict.get(f"{side}Foot"),
    )
    if len(path) >= 3:
        mapping_dict[slot] = path[-2]


def _meshes_using_armature(armature):
    meshes = {child for child in armature.children if child.type == "MESH"}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and getattr(mod, "object", None) is armature:
                meshes.add(obj)
                break
    return meshes


def _merge_vertex_group(mesh_obj, old_name, new_name):
    old_group = mesh_obj.vertex_groups.get(old_name)
    if old_group is None:
        return False

    new_group = mesh_obj.vertex_groups.get(new_name)
    if new_group is None:
        old_group.name = new_name
        return True

    for vert in mesh_obj.data.vertices:
        for group in vert.groups:
            if group.group == old_group.index:
                new_group.add([vert.index], group.weight, "ADD")
                break
    mesh_obj.vertex_groups.remove(old_group)
    return True


def _retarget_subtargets(armature, old_name, new_name):
    changed = 0

    def retarget_constraints(constraints):
        nonlocal changed
        for constraint in constraints:
            if getattr(constraint, "target", None) is armature and getattr(constraint, "subtarget", "") == old_name:
                constraint.subtarget = new_name
                changed += 1

    for obj in bpy.data.objects:
        retarget_constraints(getattr(obj, "constraints", ()))
        pose = getattr(obj, "pose", None)
        if pose is not None:
            for pose_bone in pose.bones:
                retarget_constraints(pose_bone.constraints)

    return changed


def _iter_action_fcurves(action):
    """Yield f-curves from legacy and layered action data APIs."""
    stack = [action]
    seen = set()

    while stack:
        item = stack.pop()
        if item is None:
            continue

        item_id = id(item)
        if item_id in seen:
            continue
        seen.add(item_id)

        fcurves = getattr(item, "fcurves", None)
        if fcurves is not None:
            try:
                for fcurve in fcurves:
                    yield fcurve
            except TypeError:
                pass

        for attr in ("layers", "strips", "channelbags", "channels", "groups", "slots"):
            collection = getattr(item, attr, None)
            if collection is None:
                continue
            try:
                stack.extend(collection)
            except TypeError:
                pass


def _retarget_action_paths(old_name, new_name):
    old_token = f'pose.bones["{old_name}"]'
    new_token = f'pose.bones["{new_name}"]'
    changed = 0
    for action in bpy.data.actions:
        for fcurve in _iter_action_fcurves(action):
            data_path = getattr(fcurve, "data_path", "")
            if old_token in data_path:
                fcurve.data_path = data_path.replace(old_token, new_token)
                changed += 1
    return changed


def _rename_humanoid_bone(armature, old_name, new_name):
    """Rename a mapped humanoid bone and matching mesh/animation references."""
    if not old_name or old_name == new_name:
        return False, ""
    if old_name not in armature.data.bones:
        return False, f"{old_name} not found"
    if new_name in armature.data.bones and new_name != old_name:
        return False, f"{new_name} already exists"

    armature.data.bones[old_name].name = new_name
    for mesh_obj in _meshes_using_armature(armature):
        _merge_vertex_group(mesh_obj, old_name, new_name)
    _retarget_subtargets(armature, old_name, new_name)
    _retarget_action_paths(old_name, new_name)
    return True, ""


def auto_map_humanoid(armature):
    """Auto-map humanoid slots using naming convention detection.

    Looks for common bone naming patterns (e.g. "Armature|Spine|chest" patterns).
    Returns HumanoidMapping object.
    """
    bones = _get_armature_bones(armature)
    bones_by_key = {}
    for bone in bones:
        bones_by_key.setdefault(_normalize_bone_name(bone), bone)

    mapping_dict = {}

    def find_bone(pattern_list):
        normalized_patterns = [
            _normalize_bone_name(pattern)
            for pattern in pattern_list
            if pattern
        ]

        for pattern in normalized_patterns:
            if pattern in bones_by_key:
                return bones_by_key[pattern]

        for pattern in normalized_patterns:
            for bone_key, bone_name in bones_by_key.items():
                if pattern and pattern in bone_key:
                    return bone_name
        return None

    # Common naming patterns for each slot
    patterns = {
        "Hips": ["Hips", "hips", "hip", "pelvis", "root", "J_Bip_C_Hips", "mixamorig:Hips", "DEF-hips", "DEF-spine"],
        "Spine": ["Spine", "spine", "spine1", "spine.001", "J_Bip_C_Spine", "mixamorig:Spine", "DEF-spine.001"],
        "Chest": ["Chest", "chest", "spine2", "spine.002", "J_Bip_C_Chest", "mixamorig:Spine1", "mixamorig:Spine2", "DEF-spine.002"],
        "UpperChest": ["UpperChest", "upperchest", "upper_chest", "spine3", "spine.003", "J_Bip_C_UpperChest", "DEF-spine.003"],
        "Neck": ["Neck", "neck", "J_Bip_C_Neck", "mixamorig:Neck", "DEF-neck"],
        "Head": ["Head", "head", "J_Bip_C_Head", "mixamorig:Head", "DEF-head"],
        "LeftShoulder": ["LeftShoulder", "left_shoulder", "l_shoulder", "shoulder_l", "shoulder.L", "J_Bip_L_Shoulder", "mixamorig:LeftShoulder", "DEF-shoulder.L"],
        "RightShoulder": ["RightShoulder", "right_shoulder", "r_shoulder", "shoulder_r", "shoulder.R", "J_Bip_R_Shoulder", "mixamorig:RightShoulder", "DEF-shoulder.R"],
        "LeftUpperArm": ["LeftUpperArm", "left_upperarm", "l_upperarm", "upper_arm_l", "upper_arm.L", "leftarm", "J_Bip_L_UpperArm", "mixamorig:LeftArm", "DEF-upper_arm.L"],
        "RightUpperArm": ["RightUpperArm", "right_upperarm", "r_upperarm", "upper_arm_r", "upper_arm.R", "rightarm", "J_Bip_R_UpperArm", "mixamorig:RightArm", "DEF-upper_arm.R"],
        "LeftLowerArm": ["LeftLowerArm", "left_lowerarm", "l_lowerarm", "lower_arm_l", "lower_arm.L", "left_forearm", "l_forearm", "forearm.L", "J_Bip_L_LowerArm", "mixamorig:LeftForeArm", "DEF-forearm.L"],
        "RightLowerArm": ["RightLowerArm", "right_lowerarm", "r_lowerarm", "lower_arm_r", "lower_arm.R", "right_forearm", "r_forearm", "forearm.R", "J_Bip_R_LowerArm", "mixamorig:RightForeArm", "DEF-forearm.R"],
        "LeftHand": ["LeftHand", "left_hand", "l_hand", "hand_l", "hand.L", "J_Bip_L_Hand", "mixamorig:LeftHand", "DEF-hand.L"],
        "RightHand": ["RightHand", "right_hand", "r_hand", "hand_r", "hand.R", "J_Bip_R_Hand", "mixamorig:RightHand", "DEF-hand.R"],
        "LeftUpperLeg": ["LeftUpperLeg", "left_upperleg", "l_upperleg", "upper_leg_l", "upper_leg.L", "left_thigh", "l_thigh", "thigh.L", "leftupleg", "J_Bip_L_UpperLeg", "mixamorig:LeftUpLeg", "DEF-thigh.L", "DEF-upper_leg.L"],
        "RightUpperLeg": ["RightUpperLeg", "right_upperleg", "r_upperleg", "upper_leg_r", "upper_leg.R", "right_thigh", "r_thigh", "thigh.R", "rightupleg", "J_Bip_R_UpperLeg", "mixamorig:RightUpLeg", "DEF-thigh.R", "DEF-upper_leg.R"],
        "LeftLowerLeg": ["LeftLowerLeg", "left_lowerleg", "l_lowerleg", "lower_leg_l", "lower_leg.L", "left_calf", "l_calf", "left_shin", "shin.L", "J_Bip_L_LowerLeg", "mixamorig:LeftLeg", "DEF-shin.L"],
        "RightLowerLeg": ["RightLowerLeg", "right_lowerleg", "r_lowerleg", "lower_leg_r", "lower_leg.R", "right_calf", "r_calf", "right_shin", "shin.R", "J_Bip_R_LowerLeg", "mixamorig:RightLeg", "DEF-shin.R"],
        "LeftFoot": ["LeftFoot", "left_foot", "l_foot", "foot_l", "foot.L", "J_Bip_L_Foot", "mixamorig:LeftFoot", "DEF-foot.L"],
        "RightFoot": ["RightFoot", "right_foot", "r_foot", "foot_r", "foot.R", "J_Bip_R_Foot", "mixamorig:RightFoot", "DEF-foot.R"],
        "Jaw": ["jaw"],
        "LeftEye": ["left_eye", "l_eye", "eye_l"],
        "RightEye": ["right_eye", "r_eye", "eye_r"],
    }

    for slot, pattern_list in patterns.items():
        match = find_bone(pattern_list)
        if match:
            mapping_dict[slot] = match

    _infer_lower_leg_from_chain(armature, mapping_dict, "Left")
    _infer_lower_leg_from_chain(armature, mapping_dict, "Right")

    return HumanoidMapping(mapping_dict)


def get_mapping(armature):
    """Retrieve stored mapping from armature custom property.

    ``save_mapping`` writes with ``armature[key]``, which is a Blender
    *custom property* — a different namespace from Python attributes.
    Reading it back with ``getattr``/``hasattr`` always missed, so every
    saved mapping read as empty and the exporter reported all required
    slots missing no matter how often Auto-Map ran. Item access is the
    matching read, and is what ``core.read_custom_json`` already uses.
    """
    key = "boneforge_vrchat_humanoid"
    raw = armature.get(key) if armature is not None else None
    if raw is not None:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return HumanoidMapping(data)
            logger.error(
                "[BoneCraft] humanoid mapping is %s, expected object",
                type(data).__name__,
            )
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # M-07: Log JSON parse errors for debugging
            logger.error(f"[BoneCraft] JSON parse error loading humanoid mapping: {e}")
    return HumanoidMapping()


def save_mapping(armature, mapping):
    """Save mapping to armature custom property."""
    key = "boneforge_vrchat_humanoid"
    armature[key] = json.dumps(mapping.to_dict())


# ── Operators ────────────────────────────────────────────────────────

class BF_OT_VRC_AutoMapHumanoid(Operator):
    """Auto-map humanoid slots based on naming conventions."""

    bl_idname = "boneforge.vrc_auto_map_humanoid"
    bl_label = "Auto-Map Humanoid"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        mapping = auto_map_humanoid(arm)
        save_mapping(arm, mapping)

        missing = mapping.validate_required(arm)
        if missing:
            self.report(
                {"WARNING"},
                f"Mapped {len(REQUIRED_SLOTS) - len(missing)}/{len(REQUIRED_SLOTS)} "
                f"required slots. Missing: {', '.join(missing[:5])}"
            )
        else:
            self.report({"INFO"}, "Successfully mapped all required humanoid slots")

        return {"FINISHED"}


class BF_OT_VRC_NormalizeHumanoidNames(Operator):
    """Rename mapped required humanoid bones to Unity slot names."""

    bl_idname = "boneforge.vrc_normalize_humanoid_names"
    bl_label = "Normalize Humanoid Names"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        current = get_mapping(arm).to_dict()
        detected = auto_map_humanoid(arm).to_dict()
        bone_names = {bone.name for bone in arm.data.bones}
        merged = dict(detected)
        merged.update({slot: bone for slot, bone in current.items() if bone and bone in bone_names})
        mapping = HumanoidMapping(merged)

        missing = mapping.validate_required(arm)
        if missing:
            save_mapping(arm, mapping)
            self.report(
                {"WARNING"},
                f"Mapped {len(REQUIRED_SLOTS) - len(missing)}/{len(REQUIRED_SLOTS)} "
                f"required slots. Missing: {', '.join(missing[:5])}"
            )
            return {"CANCELLED"}

        renamed = 0
        skipped = []
        for slot in REQUIRED_SLOTS:
            old_name = mapping.get_slot(slot)
            did_rename, reason = _rename_humanoid_bone(arm, old_name, slot)
            if did_rename:
                mapping.set_slot(slot, slot)
                renamed += 1
            elif old_name == slot:
                mapping.set_slot(slot, slot)
            elif reason:
                skipped.append(f"{old_name}->{slot}: {reason}")

        save_mapping(arm, mapping)

        if skipped:
            self.report(
                {"WARNING"},
                f"Renamed {renamed} bone(s); skipped {len(skipped)} conflict(s)"
            )
        else:
            self.report({"INFO"}, f"Renamed {renamed} humanoid bone(s); mapped all required slots")

        return {"FINISHED"}


class BF_OT_VRC_SetHumanoidSlot(Operator):
    """Set a single humanoid bone slot."""

    bl_idname = "boneforge.vrc_set_humanoid_slot"
    bl_label = "Set Humanoid Slot"
    bl_options = {"REGISTER", "UNDO"}

    slot_name: StringProperty(
        name="Slot",
        description="Humanoid slot name"
    )
    bone_name: StringProperty(
        name="Bone",
        description="Target bone name"
    )

    def invoke(self, context, event):
        arm = active_armature(context)
        if not arm:
            return {"CANCELLED"}

        if not self.bone_name:
            self.bone_name = get_mapping(arm).get_slot(self.slot_name) or ""

        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        layout.label(text=self.slot_name, icon="BONE_DATA")
        if arm and arm.pose:
            layout.prop_search(self, "bone_name", arm.pose, "bones", text="Bone")
        else:
            layout.prop(self, "bone_name", text="Bone")

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            return {"CANCELLED"}

        # Validate bone exists
        bones = _get_armature_bones(arm)
        if self.bone_name and self.bone_name not in bones:
            self.report({"ERROR"}, f"Bone '{self.bone_name}' not found")
            return {"CANCELLED"}

        mapping = get_mapping(arm)
        mapping.set_slot(self.slot_name, self.bone_name)
        save_mapping(arm, mapping)

        return {"FINISHED"}


class BF_OT_VRC_ValidateMapping(Operator):
    """Validate humanoid mapping completeness."""

    bl_idname = "boneforge.vrc_validate_humanoid_mapping"
    bl_label = "Validate Mapping"
    bl_options = {"REGISTER"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            return {"CANCELLED"}

        mapping = get_mapping(arm)
        missing = mapping.validate_required(arm)

        # A never-mapped armature reports every required slot missing,
        # which reads as "my rig is broken" when it only means "nothing
        # has been detected yet". Detect first, then judge.
        if len(missing) == len(REQUIRED_SLOTS):
            detected = auto_map_humanoid(arm)
            detected_missing = detected.validate_required(arm)
            if len(detected_missing) < len(missing):
                save_mapping(arm, detected)
                mapping, missing = detected, detected_missing
                if not missing:
                    self.report(
                        {"INFO"},
                        "Nothing was mapped yet — auto-mapped all "
                        f"{len(REQUIRED_SLOTS)} required slots from bone "
                        "names. Ready to export.",
                    )
                    return {"FINISHED"}
                self.report(
                    {"WARNING"},
                    f"Nothing was mapped yet — auto-mapped "
                    f"{len(REQUIRED_SLOTS) - len(missing)}/"
                    f"{len(REQUIRED_SLOTS)} slots. Still missing: "
                    f"{', '.join(missing[:8])}. Set these by hand in the "
                    "Humanoid Mapping panel.",
                )
                return {"FINISHED"}

        if missing:
            self.report(
                {"WARNING"},
                f"Missing or invalid {len(missing)} required slots: "
                f"{', '.join(missing[:8])}. Click 'Auto-Map Humanoid', "
                "then set any leftovers by hand.",
            )
        else:
            self.report({"INFO"}, "All required humanoid slots are mapped!")

        return {"FINISHED"}


class BF_OT_VRC_TPosePreview(Operator):
    """Apply T-pose to the armature for preview."""

    bl_idname = "boneforge.vrc_t_pose_preview"
    bl_label = "T-Pose Preview"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from mathutils import Quaternion

        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        if not arm.pose:
            self.report({'ERROR'}, "No pose data available")
            return {'CANCELLED'}

        # Reset all pose bone rotations to identity (rest pose = T-pose assumption)
        reset_count = 0
        for pose_bone in arm.pose.bones:
            # Reset rotation
            pose_bone.rotation_quaternion = Quaternion((1, 0, 0, 0))
            pose_bone.rotation_euler = (0, 0, 0)
            pose_bone.rotation_axis_angle = (0, 0, 1, 0)
            # Reset location offset
            pose_bone.location = (0, 0, 0)
            # Reset scale
            pose_bone.scale = (1, 1, 1)
            reset_count += 1

        # Force viewport update
        context.view_layer.update()

        self.report({'INFO'}, f"Reset {reset_count} bones to rest pose (T-pose)")
        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_humanoid(Panel):
    """Humanoid mapper panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_humanoid"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"

    def draw_header(self, context):
        self.layout.label(text=T("Humanoid Mapper"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        arm = active_armature(context)
        layout = self.layout

        if not arm:
            return

        mapping = get_mapping(arm)
        bones = _get_armature_bones(arm)

        # Progress indicator
        completion = mapping.completion_percent()
        row = layout.row()
        row.label(text=f"Required Slots: {completion}%")

        # Auto-map button
        row = layout.row(align=True)
        row.operator(
            "boneforge.vrc_auto_map_humanoid",
            text=T("Auto-Map All")
        )
        row.operator(
            "boneforge.vrc_normalize_humanoid_names",
            text=T("Normalize Names")
        )

        # Validate button
        layout.operator(
            "boneforge.vrc_validate_humanoid_mapping",
            text=T("Validate")
        )

        layout.separator()

        # Required slots section
        box = layout.box()
        row = box.row()
        row.label(text=f"Required Slots ({len(REQUIRED_SLOTS)})")

        for slot in REQUIRED_SLOTS:
            row = box.row()
            row.label(text=slot, icon="BONE_DATA")

            current_bone = mapping.get_slot(slot)
            op = row.operator(
                "boneforge.vrc_set_humanoid_slot",
                text=current_bone or "(click to map)",
                icon="BONE_DATA" if current_bone else "ERROR",
            )
            op.slot_name = slot
            op.bone_name = current_bone or ""

        layout.separator()

        # Optional slots section (collapsed)
        box = layout.box()
        row = box.row(align=True)
        row.label(text=T("Optional Slots"))

        for slot in OPTIONAL_SLOTS[:5]:
            row = box.row()
            row.label(text=slot, icon="BONE_DATA")
            current_bone = mapping.get_slot(slot)
            op = row.operator(
                "boneforge.vrc_set_humanoid_slot",
                text=current_bone or "(click to map)",
                icon="BONE_DATA" if current_bone else "BLANK1",
            )
            op.slot_name = slot
            op.bone_name = current_bone or ""

        layout.separator()
        layout.label(text=T("Also configure visemes in Face Tracking panel"), icon="INFO")


# ── Registration ─────────────────────────────────────────────────────

classes = (
    BF_OT_VRC_AutoMapHumanoid,
    BF_OT_VRC_NormalizeHumanoidNames,
    BF_OT_VRC_SetHumanoidSlot,
    BF_OT_VRC_ValidateMapping,
    BF_OT_VRC_TPosePreview,
    BONEFORGE_PT_vrc_humanoid,
)


def register():
    """Register humanoid mapper classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister humanoid mapper classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
