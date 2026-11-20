"""Quick Rig — one-click humanoid / quadruped / other premade armatures.

Replaces v3.3.6's "Quick Human Rig" with a small library of all
Rigify metarigs that ship with the user's Blender install, plus
BoneCraft's own 19-bone humanoid fallback for users who don't have
Rigify enabled.

Discovery is dynamic: :func:`discover_rigify_metarigs` probes
``bpy.ops.object`` for any operator matching ``armature_*_metarig_add``
at runtime. So whichever metarigs the installed Rigify version ships
(Human, Basic Human, Quadruped, Basic Quadruped, Wolf, Cat, Horse,
Bird, Shark — and any new ones added in future) are picked up
automatically. No hardcoded list to maintain.

The single :class:`BF_OT_AddQuickRig` operator handles all of them,
parameterised by a ``rig_op_id`` string. The special sentinel
``"boneforge.fallback_humanoid"`` invokes the built-in 19-bone
fallback skeleton instead of a Rigify metarig.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Optional

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from mathutils import Matrix, Vector
from boneforge.i18n import T

logger = logging.getLogger(__name__)


# Sentinel value for the BoneForge built-in fallback skeleton.
FALLBACK_OP_ID = "boneforge.fallback_humanoid"

# Nominal max-bbox-dimension (metres) for each Rigify metarig at
# default scale, used for "fit to mesh" scaling. Falls back to 1.7 m
# (human) when the rig name isn't in the table.
_NOMINAL_DIMENSIONS = {
    "human":            1.70,  # height
    "basic_human":      1.70,
    "quadruped":        1.30,  # length
    "basic_quadruped":  1.30,
    "wolf":             1.40,  # length
    "cat":              0.45,  # length (small cat)
    "horse":            2.30,  # length
    "bird":             0.55,  # length / wingspan
    "shark":            3.00,  # length
}

# v3.3.9: per-rig label overrides for clearer naming. Anything not
# listed falls back to the title-cased rig name.
_LABEL_OVERRIDES = {
    "human":       "Full Human",
    "basic_human": "Simple Human",
}

# Grouping for the UI. Anything not listed lands in 'Other'.
_GROUP_HUMANS = ("human", "basic_human")
_GROUP_QUADRUPEDS = (
    "quadruped", "basic_quadruped", "wolf", "cat", "horse",
)
_GROUP_OTHER = ("bird", "shark")


# ── Public discovery API ────────────────────────────────────────
# (v3.7.3 build marker)

def discover_rigify_metarigs() -> list[dict]:
    """Return a list of metarig descriptors detected on bpy.ops.object.

    Each entry: ``{"rig_name", "op_id", "label", "group"}``.
    Sorted alphabetically by rig_name within group, groups in order:
    humans → quadrupeds → other → unknown.
    """
    if not hasattr(bpy.ops, "object"):
        return []

    found = []
    for name in dir(bpy.ops.object):
        if not (name.startswith("armature_") and name.endswith("_metarig_add")):
            continue
        rig_name = name[len("armature_"):-len("_metarig_add")]
        # Friendly label: per-rig override or title-cased rig_name
        label = _LABEL_OVERRIDES.get(
            rig_name, rig_name.replace("_", " ").title(),
        )
        # Group classification
        if rig_name in _GROUP_HUMANS:
            group = "humans"
        elif rig_name in _GROUP_QUADRUPEDS:
            group = "quadrupeds"
        elif rig_name in _GROUP_OTHER:
            group = "other"
        else:
            group = "unknown"
        found.append({
            "rig_name": rig_name,
            "op_id":    f"object.{name}",
            "label":    label,
            "group":    group,
        })

    # Sort: group order then alphabetical
    group_order = {"humans": 0, "quadrupeds": 1, "other": 2, "unknown": 3}
    found.sort(key=lambda r: (group_order[r["group"]], r["rig_name"]))
    return found


def is_rigify_available() -> bool:
    """Return True if at least one Rigify metarig operator is reachable."""
    return len(discover_rigify_metarigs()) > 0


def enable_rigify_if_available() -> bool:
    """Best-effort enable for Blender's bundled Rigify add-on.

    This only enables an add-on module already shipped with the user's
    Blender install. It does not download code or save user preferences.
    BoneCraft calls it during registration so Quick Rig templates are
    available immediately after install when Rigify is present.
    """
    if is_rigify_available():
        return True

    enable_errors = []

    try:
        bpy.ops.preferences.addon_enable(module="rigify")
    except Exception as exc:
        enable_errors.append(f"preferences.addon_enable failed: {exc}")
    else:
        if is_rigify_available():
            return True

    try:
        import addon_utils

        addon_utils.enable("rigify", default_set=False, persistent=False)
    except Exception as exc:
        enable_errors.append(f"addon_utils.enable failed: {exc}")

    if not is_rigify_available():
        logger.info(
            "[BoneCraft] Rigify auto-enable skipped: %s",
            "; ".join(enable_errors) if enable_errors else "unknown reason",
        )
        return False

    return is_rigify_available()


# ── Bbox helper ─────────────────────────────────────────────────

def _mesh_world_bbox(mesh_obj) -> tuple[Vector, Vector]:
    world_corners = [
        mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box
    ]
    min_corner = Vector((
        min(corner.x for corner in world_corners),
        min(corner.y for corner in world_corners),
        min(corner.z for corner in world_corners),
    ))
    max_corner = Vector((
        max(corner.x for corner in world_corners),
        max(corner.y for corner in world_corners),
        max(corner.z for corner in world_corners),
    ))
    return min_corner, max_corner




def _is_rigify_metarig(obj) -> bool:
    """Return True if *obj* looks like a Rigify metarig.

    Used to gate the standalone Generate Control Rig button. Three
    signals: object is an armature, the rigify_generate operator is
    available, and the armature's data has a ``rigify_target_rig``
    attribute (Rigify's per-metarig generated-name slot).
    """
    if obj is None or obj.type != "ARMATURE":
        return False
    if not hasattr(bpy.ops.pose, "rigify_generate"):
        return False
    return hasattr(obj.data, "rigify_target_rig") or hasattr(
        obj.data, "rigify_layers",
    )


def _generate_rigify_control_rig(context, metarig):
    """Generate a Rigify control rig from *metarig* and return it.

    Rigify generation is context-sensitive. Keep the setup explicit:
    make the metarig active, select only it, use Pose mode when
    possible, check the operator poll, then call Rigify.
    """
    if not _is_rigify_metarig(metarig):
        raise RuntimeError("Active armature is not a Rigify metarig")

    # v3.9.8: replace bpy.ops.object.select_all with a direct
    # view_layer.objects loop. The operator's poll fails on
    # Bforartists 5.2 when called from contexts that lack a real
    # VIEW_3D area or the active object is in a non-OBJECT mode —
    # both of which can happen when this function is reached
    # through the T-Pose/A-Pose regenerate dialog. Direct .select_set
    # calls work in any context because they're property setters,
    # not operators.
    for object_in_layer in context.view_layer.objects:
        try:
            object_in_layer.select_set(False)
        except RuntimeError:
            pass
    metarig.select_set(True)
    context.view_layer.objects.active = metarig

    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="POSE")

    rigify_generate = bpy.ops.pose.rigify_generate
    if hasattr(rigify_generate, "poll") and not rigify_generate.poll():
        raise RuntimeError("Rigify generation is not available in this context")

    rigify_generate()

    generated_rig = context.active_object
    if generated_rig is None or generated_rig.type != "ARMATURE":
        raise RuntimeError("Rigify generation finished without an active rig")

    metarig["boneforge_is_rigify_metarig_source"] = 1
    generated_rig["boneforge_generated_from_metarig"] = metarig.name
    try:
        metarig.hide_set(True)
        metarig.hide_viewport = True
    except RuntimeError:
        logger.debug("[BoneCraft] could not hide generated Rigify metarig")

    controller_shape_count = _prepare_generated_control_rig_for_editing(
        context,
        generated_rig,
    )
    generated_rig["boneforge_rigify_custom_shape_count"] = controller_shape_count

    return generated_rig


def _count_custom_shape_pose_bones(armature):
    """Return how many pose bones have visible custom control shapes."""
    if armature is None or armature.type != "ARMATURE" or armature.pose is None:
        return 0
    return sum(
        1
        for pose_bone in armature.pose.bones
        if pose_bone.custom_shape is not None
    )


def _prepare_generated_control_rig_for_editing(context, generated_rig):
    """Select generated Rigify rig, show controls, and enter Pose Mode."""
    if generated_rig is None or generated_rig.type != "ARMATURE":
        return 0

    if context.mode != "OBJECT":
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except RuntimeError:
            pass

    try:
        generated_rig.hide_set(False)
        generated_rig.hide_viewport = False
    except RuntimeError:
        logger.debug("[BoneCraft] could not unhide generated Rigify rig")

    bpy.ops.object.select_all(action="DESELECT")
    generated_rig.select_set(True)
    context.view_layer.objects.active = generated_rig
    generated_rig.show_in_front = True

    # v3.7.2: don't force WIRE — in WIRE mode, DEF bones (no custom shape)
    # collapse to thin head-tail lines and get visually drowned out by
    # controller widgets, which made users think the deform skeleton was
    # missing. Only fix WIRE if the user (or Rigify) already left it that
    # way; otherwise prefer OCTAHEDRAL so DEF bones are inspectable.
    try:
        if generated_rig.data.display_type == "WIRE":
            generated_rig.data.display_type = "OCTAHEDRAL"
    except (AttributeError, TypeError):
        logger.debug("[BoneCraft] could not set generated rig display type")

    _show_all_armature_bone_collections(generated_rig)

    try:
        bpy.ops.object.mode_set(mode="POSE")
    except RuntimeError:
        logger.debug("[BoneCraft] could not enter Pose Mode on generated rig")

    return _count_custom_shape_pose_bones(generated_rig)


def _show_all_armature_bone_collections(armature):
    """Make all bone collections visible (recursively) and unhide individual bones.

    v3.7.2: previous version walked only ``armature.data.collections`` which is
    the top-level view. In Blender 4.1+ Rigify nests DEF / MCH / ORG under
    parent collections, so the nested collections were never made visible.
    Use ``collections_all`` (recursive flat view) when available, fall back
    to ``collections`` for older Blender, and additionally clear per-bone
    ``bone.hide`` since Rigify hides MCH/ORG at the bone level too.
    """
    armature_data = getattr(armature, "data", None)
    if armature_data is None:
        return

    bone_collections = getattr(armature_data, "collections_all", None)
    if bone_collections is None:
        bone_collections = getattr(armature_data, "collections", None)
    if bone_collections:
        for bone_collection in bone_collections:
            try:
                bone_collection.is_visible = True
            except (AttributeError, TypeError):
                logger.debug(
                    "[BoneCraft] could not show bone collection %s",
                    getattr(bone_collection, "name", "<unknown>"),
                )

    # Per-bone hide flag is independent of collection visibility — Rigify
    # sets it on MCH/ORG bones so they stay hidden even if the collection
    # is visible. Clear it so deform-related bones are inspectable.
    for bone in armature_data.bones:
        try:
            if bone.hide:
                bone.hide = False
        except AttributeError:
            pass

# ── Fallback 19-bone skeleton (BoneForge own asset) ─────────────

# Each bone: (name, head, tail, parent). Coordinates in metres at a
# nominal 1.7 m human scale. Original BoneForge content; not derived
# from Rigify or any other plugin's bone data.
_FALLBACK_BONES = (
    ("Hips",            (0.00, 0.00, 0.95),   (0.00, 0.00, 1.05),   None),
    ("Spine",           (0.00, 0.00, 1.05),   (0.00, 0.00, 1.20),   "Hips"),
    ("Chest",           (0.00, 0.00, 1.20),   (0.00, 0.00, 1.40),   "Spine"),
    ("Neck",            (0.00, 0.00, 1.40),   (0.00, 0.00, 1.55),   "Chest"),
    ("Head",            (0.00, 0.00, 1.55),   (0.00, 0.00, 1.70),   "Neck"),
    ("LeftShoulder",    (0.00, 0.00, 1.40),   (0.15, 0.00, 1.42),   "Chest"),
    ("LeftUpperArm",    (0.15, 0.00, 1.42),   (0.40, 0.00, 1.42),   "LeftShoulder"),
    ("LeftLowerArm",    (0.40, 0.00, 1.42),   (0.65, 0.00, 1.42),   "LeftUpperArm"),
    ("LeftHand",        (0.65, 0.00, 1.42),   (0.78, 0.00, 1.42),   "LeftLowerArm"),
    ("RightShoulder",   (0.00, 0.00, 1.40),   (-0.15, 0.00, 1.42),  "Chest"),
    ("RightUpperArm",   (-0.15, 0.00, 1.42),  (-0.40, 0.00, 1.42),  "RightShoulder"),
    ("RightLowerArm",   (-0.40, 0.00, 1.42),  (-0.65, 0.00, 1.42),  "RightUpperArm"),
    ("RightHand",       (-0.65, 0.00, 1.42),  (-0.78, 0.00, 1.42),  "RightLowerArm"),
    ("LeftUpperLeg",    (0.10, 0.00, 0.95),   (0.10, 0.00, 0.55),   "Hips"),
    ("LeftLowerLeg",    (0.10, 0.00, 0.55),   (0.10, 0.00, 0.10),   "LeftUpperLeg"),
    ("LeftFoot",        (0.10, 0.00, 0.10),   (0.10, 0.15, 0.02),   "LeftLowerLeg"),
    ("RightUpperLeg",   (-0.10, 0.00, 0.95),  (-0.10, 0.00, 0.55),  "Hips"),
    ("RightLowerLeg",   (-0.10, 0.00, 0.55),  (-0.10, 0.00, 0.10),  "RightUpperLeg"),
    ("RightFoot",       (-0.10, 0.00, 0.10),  (-0.10, 0.15, 0.02),  "RightLowerLeg"),
)


def _build_fallback_skeleton(context) -> bpy.types.Object:
    """Build BoneCraft's 19-bone humanoid skeleton at world origin."""
    arm_data = bpy.data.armatures.new(name="HumanArmature")
    arm_obj = bpy.data.objects.new(name="HumanArmature", object_data=arm_data)
    context.collection.objects.link(arm_obj)
    context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm_data.edit_bones

    # Look up tail-by-name for connection
    tail_by_name = {
        bone_name: Vector(tail)
        for bone_name, _head, tail, _parent in _FALLBACK_BONES
    }

    created: dict[str, bpy.types.EditBone] = {}
    for name, head, tail, parent in _FALLBACK_BONES:
        bone = edit_bones.new(name)
        bone.head = Vector(head)
        bone.tail = Vector(tail)
        if parent is not None and parent in created:
            bone.parent = created[parent]
            bone.use_connect = (Vector(head) == tail_by_name[parent])
        created[name] = bone

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


DROPPED_RIG_PROP = "bonecraft_dropped_rig"


def fit_armature_to_bbox(context, armature, bbox_min, bbox_max, rig_name):
    """Scale *armature* to the bbox's largest side and stand it on the bbox floor.

    *armature* must be the only selected object (``transform_apply`` acts
    on the selection).
    """
    mesh_max_dim = max(
        bbox_max.x - bbox_min.x,
        bbox_max.y - bbox_min.y,
        bbox_max.z - bbox_min.z,
        1e-3,
    )
    nominal = _NOMINAL_DIMENSIONS.get(rig_name, 1.7)
    scale = mesh_max_dim / nominal
    armature.scale = Vector((scale, scale, scale))
    # Position at mesh center, sitting on the floor (lowest Z).
    armature.location = Vector((
        (bbox_min.x + bbox_max.x) * 0.5,
        (bbox_min.y + bbox_max.y) * 0.5,
        bbox_min.z,
    ))
    # Apply the scale so edit-bone coordinates reflect actual size.
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except RuntimeError as exc:
        logger.warning("[BoneCraft] could not apply scale: %s", exc)


def parent_mesh_with_auto_weights(context, armature, mesh):
    """Parent *mesh* to *armature* with automatic weights (Object Mode)."""
    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


# ── Operator ────────────────────────────────────────────────────

# Collections", these mappings are used to populate standard
# metarig (the same collections that Rigify creates on the generated
# before generation has happened).

# Bone-name regex patterns per collection. Keys are collection names
# patterns; any bone matching any pattern joins that collection.


def _apply_initial_pose_to_quickrig(context, armature_object,
                                     pose_choice: str) -> int:
    """Apply T or A pose to *armature_object* if requested.

    Returns the number of chains modified, or 0 if no-op.
    """
    if pose_choice == "KEEP_DEFAULT":
        return 0

    target_arm_angle_below_horizontal = (
        0.0 if pose_choice == "T_POSE"
        else math.radians(A_POSE_ARM_ANGLE_BELOW_HORIZONTAL_DEGREES)
    )
    target_leg_spread = (
        0.0 if pose_choice == "T_POSE"
        else math.radians(A_POSE_LEG_SPREAD_FROM_VERTICAL_DEGREES)
    )

    target_left_arm = Vector((
        math.cos(target_arm_angle_below_horizontal),
        0.0,
        -math.sin(target_arm_angle_below_horizontal),
    ))
    target_right_arm = Vector((
        -math.cos(target_arm_angle_below_horizontal),
        0.0,
        -math.sin(target_arm_angle_below_horizontal),
    ))
    target_left_leg = Vector((
        math.sin(target_leg_spread),
        0.0,
        -math.cos(target_leg_spread),
    ))
    target_right_leg = Vector((
        -math.sin(target_leg_spread),
        0.0,
        -math.cos(target_leg_spread),
    ))

    return _apply_rest_pose_to_armature(
        armature_object,
        target_left_arm, target_right_arm,
        target_left_leg, target_right_leg,
    )



class BF_OT_AddQuickRig(Operator):
    """Add a premade armature (Rigify metarig or BoneCraft fallback)."""

    bl_idname = "boneforge.add_quick_rig"
    bl_label = "Add Quick Rig"
    bl_description = (
        "Add a premade armature, fitted to the active mesh's bounding "
        "box. Supports any Rigify metarig your Blender install ships, "
        "or BoneCraft's built-in 19-bone humanoid fallback when Rigify "
        "isn't enabled"
    )
    bl_options = {"REGISTER", "UNDO"}

    rig_op_id: StringProperty(
        name="Rigify Operator ID",
        description="The bpy.ops id of the metarig operator to invoke. "
                    "Use the special value 'boneforge.fallback_humanoid' "
                    "to invoke BoneCraft's built-in skeleton instead.",
        default="object.armature_human_metarig_add",
        options={'HIDDEN', 'SKIP_SAVE'},       # the button says which rig; not an option to tune
    )
    rig_label: StringProperty(
        name="Rig Label",
        description="Human-readable label for status messages.",
        default="Human",
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    fit_to_active_mesh: BoolProperty(
        name="Fit Rig to Active Mesh",
        description="Scale and position the rig to match the active "
                    "mesh's world-space bounding box. This does not "
                    "generate controllers; it only sizes and places the rig.",
        default=True,
    )
    parent_with_auto_weights: BoolProperty(
        name="Parent + Auto-Weight Mesh",
        description="After adding the armature, parent the active "
                    "mesh to it with automatic vertex weight skinning. "
                    "Destructive — writes vertex groups onto the mesh.",
        default=False,
    )
    generate_control_rig: BoolProperty(
        name="Add IK/FK Controllers",
        description="Off: create the bones only. On: also generate Rigify "
                    "IK/FK controllers with custom shapes. Rigify metarigs "
                    "only; the BoneCraft humanoid has none",
        default=True,
    )
    initial_pose: EnumProperty(
        name="Initial Pose",
        description=(
            "Pose the metarig before generating any control rig. "
            "Applying T or A pose at this stage means controllers, "
            "widget offsets, and IK targets are baked against the "
            "intended pose from the start — no need for the post-"
            "generation regenerate dialog later"
        ),
        items=(
            ("KEEP_DEFAULT", "Keep Default",
             "Use the metarig's shipped pose (Rigify's default is a "
             "loose T-pose for humans)"),
            ("T_POSE", "T-Pose",
             "Apply T-pose immediately after spawning"),
            ("A_POSE", "A-Pose",
             "Apply A-pose immediately after spawning (45 deg arm "
             "drop, ~8 deg leg spread)"),
        ),
        default="KEEP_DEFAULT",
    )

    def execute(self, context):
        # Snapshot target mesh + bbox before mutation
        target_mesh = context.active_object
        if target_mesh is None or target_mesh.type != "MESH":
            target_mesh = None

        bbox_min, bbox_max = (None, None)
        if target_mesh is not None and self.fit_to_active_mesh:
            bbox_min, bbox_max = _mesh_world_bbox(target_mesh)

        # Drop to OBJECT mode so we can add new objects safely.
        prev_mode = (target_mesh.mode if target_mesh
                     else context.mode)
        if context.mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass

        # ── Build the armature ──────────────────────────────────
        rig_name = "fallback"
        if self.rig_op_id == FALLBACK_OP_ID:
            _build_fallback_skeleton(context)
        else:
            try:
                # Resolve and call: bpy.ops.<op_id>()
                module_name, op_name = self.rig_op_id.split(".", 1)
                op_module = getattr(bpy.ops, module_name)
                op_func = getattr(op_module, op_name)
                op_func()
                # Extract rig_name from op_id: armature_human_metarig_add → human
                if op_name.startswith("armature_") and op_name.endswith("_metarig_add"):
                    rig_name = op_name[len("armature_"):-len("_metarig_add")]
            except (AttributeError, RuntimeError) as exc:
                self.report(
                    {"ERROR"},
                    f"Could not add metarig {self.rig_op_id!r}: {exc}",
                )
                return {"CANCELLED"}

        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Failed to create armature")
            return {"CANCELLED"}

        # Friendly name
        if armature.name.lower().startswith(("metarig", "armature")):
            armature.name = f"{self.rig_label.replace(' ', '')}Armature"

        # ── Fit to mesh ─────────────────────────────────────────
        # Scale by max bbox dimension vs the rig's nominal size.
        if bbox_min is not None and bbox_max is not None:
            fit_armature_to_bbox(context, armature, bbox_min, bbox_max, rig_name)

        # v3.8.9: apply T-pose / A-pose to the freshly-spawned metarig
        # BEFORE generating the control rig. Doing it here means
        # Rigify bakes widgets and IK targets against the intended
        # rest pose from the start; users never need the post-
        # generation regenerate dialog if they pick the pose up front.
        if self.initial_pose != "KEEP_DEFAULT":
            try:
                _apply_initial_pose_to_quickrig(
                    context, armature, self.initial_pose,
                )
            except (RuntimeError, ValueError, AttributeError) as exc:
                logger.warning(
                    "[BoneCraft] could not apply initial pose: %s", exc,
                )

        # ── Optional Rigify control rig generation ──────────────
        # v3.3.8: if requested AND we just added a Rigify metarig, run
        # bpy.ops.pose.rigify_generate. The generated control rig
        # becomes the new active object; the metarig is hidden by
        # Rigify automatically. Skin tasks (auto-weight) below should
        # then target the control rig, not the metarig.
        is_metarig = (
            self.rig_op_id != FALLBACK_OP_ID
            and _is_rigify_metarig(armature)
        )
        generated_rig = None
        controller_shape_count = 0
        if self.generate_control_rig and is_metarig:
            try:
                generated_rig = _generate_rigify_control_rig(context, armature)
                controller_shape_count = int(
                    generated_rig.get("boneforge_rigify_custom_shape_count", 0)
                )
            except (RuntimeError, AttributeError) as exc:
                self.report(
                    {"WARNING"},
                    f"Metarig added, but Rigify generation failed: "
                    f"{exc}. The metarig remains; you can run "
                    "'Generate Control Rig' manually.",
                )
        elif self.generate_control_rig and not is_metarig:
            # User asked but we couldn't honour: BoneForge fallback
            # has no Rigify generation path.
            self.report(
                {"INFO"},
                "Generate Control Rig skipped — only Rigify metarigs "
                "support generation. The BoneCraft fallback skeleton "
                "is rig-ready as-is.",
            )

        # The armature we're going to parent the mesh under
        target_arm = generated_rig if generated_rig is not None else armature

        # ── Optional auto-parent ────────────────────────────────
        if (target_mesh is not None
                and self.parent_with_auto_weights):
            try:
                parent_mesh_with_auto_weights(context, target_arm, target_mesh)
                if generated_rig is not None:
                    target_arm.select_set(True)
                    context.view_layer.objects.active = target_arm
                    bpy.ops.object.mode_set(mode="POSE")
                self.report(
                    {"INFO"},
                    f"Created {self.rig_label}"
                    f"{' + control rig' if generated_rig else ''}; "
                    f"parented '{target_mesh.name}' with auto-weights",
                )
            except RuntimeError as exc:
                self.report(
                    {"WARNING"},
                    f"Created {self.rig_label} armature, but auto-weight "
                    f"parenting failed: {exc}",
                )
        else:
            fitted = " (fitted to active mesh)" if bbox_min else ""
            generated = " (bones + controllers)" if generated_rig else " (bones only)"
            self.report(
                {"INFO"},
                f"Created {self.rig_label} armature{generated}{fitted}",
            )

        if generated_rig is not None:
            controller_shape_count = int(
                generated_rig.get(
                    "boneforge_rigify_custom_shape_count",
                    controller_shape_count,
                )
            )
            if controller_shape_count:
                self.report(
                    {"INFO"},
                    f"Rigify controls ready: {controller_shape_count} custom shapes",
                )
            else:
                self.report(
                    {"WARNING"},
                    "Rigify generated a rig, but no custom controller shapes "
                    "were detected. Check that Rigify widgets are visible.",
                )

        # Restore previous mode if applicable.
        if (
            generated_rig is None
            and target_mesh is not None
            and prev_mode
            and prev_mode != "OBJECT"
        ):
            try:
                context.view_layer.objects.active = target_mesh
                target_mesh.select_set(True)
                bpy.ops.object.mode_set(mode=prev_mode)
            except RuntimeError:
                pass

        return {"FINISHED"}




class BF_OT_GenerateRigifyControlRig(Operator):
    """Generate Rigify's full control rig from the active metarig.

    Standalone version of the option in Quick Rig. Useful when you
    already have a Rigify metarig in the scene (added previously,
    imported, or hand-built) and want to produce the IK/FK control
    rig without going through Quick Rig's metarig-add flow.

    Wraps ``bpy.ops.pose.rigify_generate``. Active object must be
    a Rigify metarig.
    """

    bl_idname = "boneforge.generate_rigify_control_rig"
    bl_label = "Generate Control Rig"
    bl_description = (
        "Generate Rigify's IK/FK control rig from the active metarig. "
        "Select a Rigify metarig first"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _is_rigify_metarig(context.active_object)

    def execute(self, context):
        try:
            generated = _generate_rigify_control_rig(
                context,
                context.active_object,
            )
        except (RuntimeError, AttributeError) as exc:
            self.report({"ERROR"}, f"Rigify generation failed: {exc}")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Generated control rig: {generated.name} "
            f"({_count_custom_shape_pose_bones(generated)} custom shapes)",
        )
        return {"FINISHED"}

# ── Registration ────────────────────────────────────────────────

class BF_OT_InspectRigifyControls(Operator):
    """Inspect the active generated Rigify control rig."""

    bl_idname = "boneforge.inspect_rigify_controls"
    bl_label = "Inspect Rigify Controls"
    bl_description = (
        "Report whether the active rig has Rigify-style custom control "
        "shapes, visible bone collections, and controller display settings"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == "ARMATURE"

    def execute(self, context):
        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Active object is not an armature")
            return {"CANCELLED"}

        controller_shape_count = _prepare_generated_control_rig_for_editing(
            context,
            armature,
        )
        pose_bone_count = len(armature.pose.bones) if armature.pose else 0
        bone_collection_count = len(getattr(armature.data, "collections", []))
        visible_collection_count = sum(
            1
            for bone_collection in getattr(armature.data, "collections", [])
            if getattr(bone_collection, "is_visible", True)
        )
        widget_object_count = sum(
            1
            for data_object in bpy.data.objects
            if data_object.name.startswith(("WGT-", "WGT_", "WGTS"))
        )
        widget_collection_count = sum(
            1
            for collection in bpy.data.collections
            if collection.name.startswith(("WGTS", "WGT"))
        )

        armature["boneforge_rigify_custom_shape_count"] = controller_shape_count
        armature["boneforge_rigify_pose_bone_count"] = pose_bone_count
        armature["boneforge_rigify_widget_object_count"] = widget_object_count
        armature["boneforge_rigify_widget_collection_count"] = widget_collection_count

        if controller_shape_count == 0:
            self.report(
                {"WARNING"},
                "Rigify inspection: 0 custom controller shapes found. "
                f"Pose bones={pose_bone_count}, widgets={widget_object_count}, "
                f"bone collections={visible_collection_count}/{bone_collection_count}.",
            )
        else:
            self.report(
                {"INFO"},
                "Rigify inspection: "
                f"{controller_shape_count}/{pose_bone_count} pose bones have "
                f"custom shapes; widgets={widget_object_count}; "
                f"collections={visible_collection_count}/{bone_collection_count}.",
            )
        return {"FINISHED"}


class BF_OT_DiagnoseQuickRig(Operator):
    """Print discover_rigify_metarigs() output for debugging.

    v3.7.3: surfaces what the discovery probe actually finds in the
    user's Blender install, so when fewer rigs render than expected we
    can see exactly which operators were detected and which group
    bucket each landed in. Output goes to the system console (stdout)
    and to a single INFO report so it shows up in the status bar's
    Info area.
    """

    bl_idname = "boneforge.diagnose_quick_rig"
    bl_label = "Diagnose Quick Rig"
    bl_description = (
        "List in the system console the Rigify metarigs BoneCraft found "
        "and how it grouped them. Use it when Quick Rig shows fewer rigs "
        "than expected"
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            rigs = discover_rigify_metarigs()
        except Exception as exc:
            self.report({"ERROR"}, f"Discovery failed: {exc}")
            return {"CANCELLED"}

        rigify_loaded = is_rigify_available()
        has_pose_op = hasattr(bpy.ops.pose, "rigify_generate")

        lines = [
            "=== BoneCraft Quick Rig diagnostic ===",
            f"  is_rigify_available     : {rigify_loaded}",
            f"  bpy.ops.pose.rigify_gen : {has_pose_op}",
            f"  metarigs discovered     : {len(rigs)}",
        ]
        counts = {"humans": 0, "quadrupeds": 0, "other": 0, "unknown": 0}
        for rig in rigs:
            counts[rig["group"]] = counts.get(rig["group"], 0) + 1
        lines.append(
            "  group counts            : "
            + ", ".join(f"{k}={v}" for k, v in counts.items())
        )
        lines.append("  per-rig detail:")
        for rig in rigs:
            lines.append(
                f"    rig_name={rig['rig_name']!r:24s} "
                f"group={rig['group']:11s} "
                f"label={rig['label']!r:18s} "
                f"op_id={rig['op_id']}"
            )
        report = "\n".join(lines)
        print(report)
        self.report({"INFO"}, report)
        return {"FINISHED"}



# ── T-Pose / A-Pose helpers ─────────────────────────────────────
# Bone name patterns ordered most-specific to most-generic. The
# first match wins. Covers Rigify (.L/.R), the BoneForge fallback
# (Left/Right prefix), Mixamo, common DCC export names, and lowercase
# variants. Add new patterns to the front of the tuple for unsupported
# rigs.

LEFT_UPPER_ARM_PATTERNS = (
    "upper_arm.L", "upper_arm.l", "upperarm.L", "upperarm.l",
    "upperarm_L", "upper_arm_L",
    "LeftUpperArm", "Left_UpperArm", "L_UpperArm", "L_upper_arm",
    "left_upper_arm", "leftUpperArm",
    "mixamorig:LeftArm", "mixamorig:LeftUpperArm",
    "shoulder.L", "arm.L", "L_Arm",
)
RIGHT_UPPER_ARM_PATTERNS = (
    "upper_arm.R", "upper_arm.r", "upperarm.R", "upperarm.r",
    "upperarm_R", "upper_arm_R",
    "RightUpperArm", "Right_UpperArm", "R_UpperArm", "R_upper_arm",
    "right_upper_arm", "rightUpperArm",
    "mixamorig:RightArm", "mixamorig:RightUpperArm",
    "shoulder.R", "arm.R", "R_Arm",
)
LEFT_UPPER_LEG_PATTERNS = (
    "thigh.L", "thigh.l", "upper_leg.L", "upper_leg.l", "upperleg.L",
    "upperleg_L", "upper_leg_L",
    "LeftUpperLeg", "Left_UpperLeg", "LeftThigh", "L_UpperLeg", "L_Thigh",
    "left_upper_leg", "leftUpperLeg",
    "mixamorig:LeftUpLeg",
    "leg.L", "L_Leg",
)
RIGHT_UPPER_LEG_PATTERNS = (
    "thigh.R", "thigh.r", "upper_leg.R", "upper_leg.r", "upperleg.R",
    "upperleg_R", "upper_leg_R",
    "RightUpperLeg", "Right_UpperLeg", "RightThigh", "R_UpperLeg", "R_Thigh",
    "right_upper_leg", "rightUpperLeg",
    "mixamorig:RightUpLeg",
    "leg.R", "R_Leg",
)

# Pose geometry tunables.
A_POSE_ARM_ANGLE_BELOW_HORIZONTAL_DEGREES = 45.0
A_POSE_LEG_SPREAD_FROM_VERTICAL_DEGREES = 8.0
ARM_CHAIN_MAX_LENGTH = 3   # upper_arm -> forearm -> hand
LEG_CHAIN_MAX_LENGTH = 3   # thigh -> shin -> foot


def _find_first_named_bone(edit_bones, name_patterns):
    """Return the first edit-bone matching one of *name_patterns*, or None."""
    for name in name_patterns:
        if name in edit_bones:
            return edit_bones[name]
    return None


def _identify_main_chain(root_bone, max_length: int):
    """Walk the longest-child chain starting at *root_bone*.

    Caps at *max_length* bones (typically 3 for upper/fore/hand or
    thigh/shin/foot). Stops early if a bone has no children.
    """
    chain = [root_bone]
    current = root_bone
    while len(chain) < max_length and current.children:
        next_in_chain = max(
            current.children,
            key=lambda candidate: (candidate.tail - candidate.head).length,
        )
        chain.append(next_in_chain)
        current = next_in_chain
    return chain


def _rotation_between_directions(source_direction: Vector,
                                 target_direction: Vector) -> Matrix:
    """Return the 4x4 rotation that maps *source_direction* to *target_direction*.

    Both inputs must already be unit vectors. Returns identity when
    they match. Handles the antiparallel case by picking +Y as the
    rotation axis.
    """
    if (source_direction - target_direction).length < 1e-6:
        return Matrix.Identity(4)

    rotation_axis = source_direction.cross(target_direction)
    if rotation_axis.length < 1e-6:
        # Antiparallel — pick any perpendicular axis. +Y works for the
        # arm/leg cases since both are roughly in the X-Z plane.
        rotation_axis = Vector((0.0, 1.0, 0.0))
    rotation_axis = rotation_axis.normalized()

    dot_clamped = max(-1.0, min(1.0,
                                source_direction.dot(target_direction)))
    rotation_angle = math.acos(dot_clamped)
    return Matrix.Rotation(rotation_angle, 4, rotation_axis)


def _set_chain_pose(root_bone, target_direction: Vector,
                    chain_length: int, world_up: Vector) -> None:
    """Straighten *root_bone*'s chain along *target_direction*.

    The main chain (root + longest descendants up to *chain_length*)
    is straightened: each bone extends from the previous bone's tail
    by its own length. Off-chain descendants (fingers off the hand,
    toes off the foot, eye sockets off the head, etc.) are rigidly
    rotated by the same rotation that takes the root's original
    direction to *target_direction*, pivoting around the root's head.

    *world_up* is the direction to align each main-chain bone's local
    Z axis to via ``edit_bone.align_roll`` so the pose preserves a
    sensible up-vector instead of inheriting whatever roll was on the
    bone before.
    """
    main_chain = _identify_main_chain(root_bone, chain_length)
    pivot = root_bone.head.copy()

    current_root_direction = (root_bone.tail - root_bone.head)
    if current_root_direction.length < 1e-6:
        return
    current_root_direction = current_root_direction.normalized()

    rigid_rotation = _rotation_between_directions(
        current_root_direction, target_direction,
    )

    main_chain_names = {bone.name for bone in main_chain}
    off_chain_descendants = [
        descendant for descendant in root_bone.children_recursive
        if descendant.name not in main_chain_names
    ]
    saved_off_chain_positions = [
        (descendant, descendant.head.copy(), descendant.tail.copy())
        for descendant in off_chain_descendants
    ]

    # Cache original bone lengths BEFORE any straightening. Once we
    # set upper_arm.tail, use_connect=True snaps forearm.head to the
    # new position; reading (forearm.tail - forearm.head).length later
    # returns the diagonal distance from the moved head to the still-
    # original tail, which is wrong and grows the chain on every click.
    # Capturing lengths up front avoids the read-back-after-mutation
    # trap entirely.
    original_chain_lengths = [
        (bone.tail - bone.head).length for bone in main_chain
    ]

    # Straighten the main chain along target_direction. Each bone
    # starts where the previous bone ended; cached lengths are used so
    # the chain neither grows nor shrinks across repeated pose toggles.
    current_position = pivot.copy()
    for bone, original_length in zip(main_chain, original_chain_lengths):
        bone.head = current_position.copy()
        bone.tail = current_position + target_direction * original_length
        current_position = bone.tail.copy()

    # Realign roll on each main-chain bone so the local Z axis points
    # toward world_up (or as close as the bone direction allows). This
    # avoids twisted finger/toe spawns when the original bone roll
    # didn't survive the rotation.
    for bone in main_chain:
        try:
            bone.align_roll(world_up)
        except (AttributeError, RuntimeError):
            pass

    # Rigidly rotate off-chain descendants around the root pivot.
    for descendant, original_head, original_tail in saved_off_chain_positions:
        descendant.head = pivot + rigid_rotation @ (original_head - pivot)
        descendant.tail = pivot + rigid_rotation @ (original_tail - pivot)


def _regenerate_mannequin_if_present(context, armature_object) -> None:
    """If a mannequin exists for *armature_object*, rebuild it with last params.

    The Armature modifier's bind to its source rest pose is captured
    when the mesh is first parented; changing the rest pose later
    leaves the mannequin geometry deformed against the *old* bind, so
    the visible result drifts away from the new pose. Regenerating
    the mannequin from scratch refits it to the current rest pose.
    """
    try:
        from boneforge.autorig.mannequin import (
            find_mannequin_for,
            restore_last_params,
            settings_from_scene,
            generate_mannequin,
            safe_remove_object,
        )
    except ImportError:
        return

    existing = find_mannequin_for(armature_object)
    if existing is None:
        return

    last_settings = restore_last_params(existing)
    settings = (last_settings if last_settings is not None
                else settings_from_scene(context.scene))
    safe_remove_object(existing)

    try:
        generate_mannequin(context, armature_object, settings)
    except (RuntimeError, TypeError, ValueError, AttributeError) as exc:
        logger.warning(
            "[BoneCraft] Could not regenerate mannequin after pose "
            "change: %s", exc,
        )


def _is_generated_rigify_control_rig(armature_object) -> bool:
    """Heuristic: is *armature_object* a Rigify-generated control rig?

    The strongest signal is the ``boneforge_generated_from_metarig``
    custom property we set when generating from inside Quick Rig. As a
    fallback we look for the conventional Rigify bone-name prefixes
    (DEF- and MCH-) which only appear together on a generated rig.
    """
    if armature_object is None or armature_object.type != "ARMATURE":
        return False
    if "boneforge_generated_from_metarig" in armature_object.keys():
        return True
    bone_names = {bone.name for bone in armature_object.data.bones}
    has_deform_prefix = any(name.startswith("DEF-") for name in bone_names)
    has_mechanism_prefix = any(name.startswith("MCH-") for name in bone_names)
    return has_deform_prefix and has_mechanism_prefix


def _find_source_metarig(generated_rig):
    """Return the metarig that *generated_rig* was generated from, or None.

    First checks the BoneCraft tag, then falls back to scanning every
    armature for one whose ``rigify_target_rig`` points at our rig
    (the standard Rigify reverse link).
    """
    metarig_name = generated_rig.get("boneforge_generated_from_metarig")
    if metarig_name:
        candidate = bpy.data.objects.get(metarig_name)
        if candidate is not None and candidate.type == "ARMATURE":
            return candidate

    for object_in_scene in bpy.data.objects:
        if object_in_scene.type != "ARMATURE":
            continue
        rigify_target = getattr(object_in_scene.data, "rigify_target_rig", None)
        if rigify_target is generated_rig:
            return object_in_scene
    return None


def _apply_rest_pose_to_armature(armature_object,
                                 target_left_arm: Vector,
                                 target_right_arm: Vector,
                                 target_left_leg: Vector,
                                 target_right_leg: Vector) -> int:
    """Apply T/A pose to *armature_object*. Returns chains modified.

    Pulled out of the operator's execute() so it can be invoked on
    either the active armature directly or on a source metarig
    discovered via _find_source_metarig.
    """
    previous_mode = armature_object.mode
    chains_modified = 0

    bpy.context.view_layer.objects.active = armature_object
    try:
        if armature_object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        edit_bones = armature_object.data.edit_bones

        for patterns, target, world_up in (
            (LEFT_UPPER_ARM_PATTERNS, target_left_arm, Vector((0, 0, 1))),
            (RIGHT_UPPER_ARM_PATTERNS, target_right_arm, Vector((0, 0, 1))),
        ):
            root = _find_first_named_bone(edit_bones, patterns)
            if root is None:
                continue
            _set_chain_pose(root, target, ARM_CHAIN_MAX_LENGTH, world_up)
            chains_modified += 1

        for patterns, target, world_up in (
            (LEFT_UPPER_LEG_PATTERNS, target_left_leg, Vector((0, 1, 0))),
            (RIGHT_UPPER_LEG_PATTERNS, target_right_leg, Vector((0, 1, 0))),
        ):
            root = _find_first_named_bone(edit_bones, patterns)
            if root is None:
                continue
            _set_chain_pose(root, target, LEG_CHAIN_MAX_LENGTH, world_up)
            chains_modified += 1

    finally:
        if armature_object.mode != previous_mode:
            try:
                bpy.ops.object.mode_set(mode=previous_mode)
            except RuntimeError:
                pass

    return chains_modified


# ── Operators ───────────────────────────────────────────────────

class BF_OT_EnableRigify(Operator):
    """Enable Blender's bundled Rigify add-on so its metarigs become
    available in Quick Rig.

    Does not download anything. Only flips the on/off switch for the
    Rigify add-on already shipped with the user's Blender install.
    """
    bl_idname = "boneforge.enable_rigify"
    bl_label = "Enable Rigify"
    bl_description = (
        "Enable Blender's built-in Rigify add-on so its premade "
        "metarigs (Human, Wolf, Cat, Horse, etc.) become selectable "
        "in this panel. Does not download anything"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if is_rigify_available():
            self.report({"INFO"}, "Rigify is already enabled.")
            return {"FINISHED"}
        if enable_rigify_if_available():
            self.report({"INFO"},
                        "Rigify enabled — metarigs are now available.")
            return {"FINISHED"}
        self.report(
            {"ERROR"},
            "Could not enable Rigify. Verify it is installed in this "
            "Blender (Edit > Preferences > Add-ons > search 'Rigify').",
        )
        return {"CANCELLED"}


def _find_view3d_context_override(context) -> Optional[dict]:
    """Locate a VIEW_3D area + WINDOW region for use with temp_override.

    invoke_props_dialog returns control to execute() in a context
    where context.area is the popup, not the 3D viewport. Operators
    like bpy.ops.object.select_all and bpy.ops.object.mode_set need a
    real 3D viewport in their poll context, so we have to scan the
    window manager for one and pass it via temp_override. Returns
    None if no 3D viewport is open (the operator should fall back to
    direct API calls in that case).
    """
    if context is None or context.window_manager is None:
        return None
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for region in area.regions:
                if region.type == "WINDOW":
                    return {
                        "window": window,
                        "screen": window.screen,
                        "area": area,
                        "region": region,
                    }
    return None


def _deselect_all_objects_directly(view_layer) -> None:
    """Deselect every object in *view_layer* without bpy.ops.

    Used in dialog-context paths where bpy.ops.object.select_all
    fails its poll because there's no VIEW_3D area in context.
    """
    for object_in_layer in view_layer.objects:
        try:
            object_in_layer.select_set(False)
        except RuntimeError:
            # Object deleted or otherwise unavailable — skip silently.
            pass


class BF_OT_SetRestPose(Operator):
    """Switch the active armature's rest pose between T-pose and A-pose.

    On a plain armature or metarig: rotates the arm and leg chains in
    place. On a generated Rigify control rig: detects the source
    metarig, applies the pose change there, and re-generates the
    control rig — controllers, custom-shape widgets, IK targets, and
    constraints all rebuild in sync. Without this regeneration step
    Rigify's baked widget offsets stay anchored to the original rest
    pose and the visible controllers don't follow the new rest.
    """
    bl_idname = "boneforge.set_rest_pose"
    bl_label = "Set Rest Pose"
    bl_description = (
        "Switch the active armature's rest pose between T-pose and "
        "A-pose. Straightens arm and leg chains; off-chain bones "
        "(fingers, toes) follow rigidly. On generated Rigify control "
        "rigs, applies the change to the source metarig and regenerates"
    )
    bl_options = {"REGISTER", "UNDO"}

    pose_type: EnumProperty(
        name="Pose Type",
        description="Target rest pose",
        items=(
            ("T_POSE", "T-Pose",
             "Arms straight horizontal to the sides, legs straight "
             "vertical"),
            ("A_POSE", "A-Pose",
             "Arms angled 45 degrees below horizontal, legs spread "
             "~8 degrees outward"),
        ),
        default="T_POSE",
    )

    apply_to_metarig_and_regenerate: BoolProperty(
        name="Apply to Source Metarig and Regenerate",
        description=(
            "Required for Rigify generated control rigs. Applies the "
            "pose change to the source metarig, then re-runs Rigify "
            "generation so controllers, widgets, and IK targets all "
            "rebuild in sync. Destroys any manual edits made to the "
            "generated rig after generation"
        ),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active is not None and active.type == "ARMATURE"

    def invoke(self, context, event):
        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            return self.execute(context)

        if not _is_generated_rigify_control_rig(armature):
            return self.execute(context)

        # Generated rig path — confirm regenerate before doing it.
        metarig = _find_source_metarig(armature)
        if metarig is None:
            self.report(
                {"WARNING"},
                "This is a Rigify generated control rig, but the "
                "source metarig is missing. Rest pose can only be "
                "changed by re-generating from a metarig. Add or "
                "restore the metarig and try again.",
            )
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        # Only invoked when on a generated Rigify control rig — explain
        # the regenerate path so the user knows what they're agreeing to.
        layout = self.layout
        layout.label(
            text=T("This is a generated Rigify control rig."),
            icon='INFO',
        )
        column = layout.column(align=True)
        column.scale_y = 0.85
        column.label(
            text=T("Rigify controllers have widget offsets and IK targets"),
        )
        column.label(
            text=T("baked into the generation — moving bones in edit mode"),
        )
        column.label(
            text=T("leaves them stranded at the old rest pose."),
        )
        layout.separator()
        layout.label(text=T("Recommended fix:"))
        column2 = layout.column(align=True)
        column2.scale_y = 0.85
        column2.label(
            text=T("Apply the pose change to the source metarig and"),
        )
        column2.label(
            text=T("regenerate the control rig in place. Custom shapes,"),
        )
        column2.label(
            text=T("IK chains, and constraints all rebuild from the new pose."),
        )
        layout.separator()
        layout.prop(self, "apply_to_metarig_and_regenerate")

    def execute(self, context):
        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            self.report({"ERROR"}, "No active armature.")
            return {"CANCELLED"}

        target_arm_angle_below_horizontal = (
            0.0 if self.pose_type == "T_POSE"
            else math.radians(A_POSE_ARM_ANGLE_BELOW_HORIZONTAL_DEGREES)
        )
        target_leg_spread = (
            0.0 if self.pose_type == "T_POSE"
            else math.radians(A_POSE_LEG_SPREAD_FROM_VERTICAL_DEGREES)
        )

        target_left_arm = Vector((
            math.cos(target_arm_angle_below_horizontal),
            0.0,
            -math.sin(target_arm_angle_below_horizontal),
        ))
        target_right_arm = Vector((
            -math.cos(target_arm_angle_below_horizontal),
            0.0,
            -math.sin(target_arm_angle_below_horizontal),
        ))
        target_left_leg = Vector((
            math.sin(target_leg_spread),
            0.0,
            -math.cos(target_leg_spread),
        ))
        target_right_leg = Vector((
            -math.sin(target_leg_spread),
            0.0,
            -math.cos(target_leg_spread),
        ))

        # Rigify generated control rig — apply to source metarig + regen.
        if (_is_generated_rigify_control_rig(armature)
                and self.apply_to_metarig_and_regenerate):
            return self._apply_to_metarig_and_regenerate(
                context, armature,
                target_left_arm, target_right_arm,
                target_left_leg, target_right_leg,
            )

        # Plain armature / metarig path — apply directly.
        chains_modified = _apply_rest_pose_to_armature(
            armature,
            target_left_arm, target_right_arm,
            target_left_leg, target_right_leg,
        )

        if chains_modified == 0:
            self.report(
                {"WARNING"},
                "No arm or leg bones found by known naming "
                "conventions. Pose unchanged.",
            )
            return {"CANCELLED"}

        _regenerate_mannequin_if_present(context, armature)

        pose_label = "T-pose" if self.pose_type == "T_POSE" else "A-pose"
        self.report(
            {"INFO"},
            f"Rest pose set to {pose_label} "
            f"({chains_modified} chain(s) updated).",
        )
        return {"FINISHED"}

    def _apply_to_metarig_and_regenerate(self, context, generated_rig,
                                         target_left_arm, target_right_arm,
                                         target_left_leg, target_right_leg):
        """Apply pose to source metarig and regenerate the control rig.

        Steps:
          1. Find source metarig (already validated in invoke()).
          2. Make metarig active and visible.
          3. Apply T/A pose to metarig's edit bones.
          4. Set rigify_target_rig = generated_rig so Rigify rebuilds
             into the existing armature instead of creating a new one
             (preserves animation data and child objects).
          5. Call _generate_rigify_control_rig(metarig).
          6. Re-hide the metarig and re-activate the regenerated rig.
        """
        metarig = _find_source_metarig(generated_rig)
        if metarig is None:
            self.report(
                {"ERROR"},
                "Source metarig vanished between invoke and execute.",
            )
            return {"CANCELLED"}

        previous_active = context.view_layer.objects.active
        metarig_was_hidden = metarig.hide_get()
        metarig_was_hidden_viewport = metarig.hide_viewport

        # Find a real VIEW_3D area to use for the bpy.ops calls below;
        # they fail with "context is incorrect" if run from the
        # invoke_props_dialog context where context.area is the popup.
        view3d_override = _find_view3d_context_override(context)

        try:
            metarig.hide_set(False)
            metarig.hide_viewport = False

            # Deselect via direct API — avoids needing VIEW_3D context
            # for bpy.ops.object.select_all(action="DESELECT").
            _deselect_all_objects_directly(context.view_layer)
            metarig.select_set(True)
            context.view_layer.objects.active = metarig

            chains_modified = _apply_rest_pose_to_armature(
                metarig,
                target_left_arm, target_right_arm,
                target_left_leg, target_right_leg,
            )
            if chains_modified == 0:
                self.report(
                    {"WARNING"},
                    "Source metarig has no recognised arm or leg "
                    "bones. Pose unchanged.",
                )
                return {"CANCELLED"}

            # Point Rigify at the existing control rig so it rebuilds
            # in place rather than creating a parallel duplicate.
            if hasattr(metarig.data, "rigify_target_rig"):
                try:
                    metarig.data.rigify_target_rig = generated_rig
                except (AttributeError, TypeError):
                    pass

            # _generate_rigify_control_rig itself runs bpy.ops calls
            # (mode_set, select_all, rigify_generate). Run them under
            # an override so they have a real viewport context to
            # poll against.
            try:
                if view3d_override is not None:
                    with context.temp_override(**view3d_override):
                        regenerated = _generate_rigify_control_rig(
                            context, metarig,
                        )
                else:
                    regenerated = _generate_rigify_control_rig(
                        context, metarig,
                    )
            except RuntimeError as exc:
                self.report({"ERROR"}, f"Rigify regenerate failed: {exc}")
                return {"CANCELLED"}

            # Refit any mannequin to the new pose.
            _regenerate_mannequin_if_present(context, regenerated)

            pose_label = ("T-pose" if self.pose_type == "T_POSE"
                          else "A-pose")
            self.report(
                {"INFO"},
                f"Source metarig set to {pose_label} and Rigify "
                f"control rig regenerated.",
            )
            return {"FINISHED"}
        finally:
            try:
                metarig.hide_set(metarig_was_hidden)
                metarig.hide_viewport = metarig_was_hidden_viewport
            except (RuntimeError, ReferenceError):
                pass
            if previous_active is not None:
                try:
                    context.view_layer.objects.active = previous_active
                except (RuntimeError, ReferenceError):
                    pass


class BF_OT_FitDroppedRig(Operator):
    """Fit a rig dragged in from the BoneCraft Rigs shelf to a mesh."""

    bl_idname = "boneforge.fit_dropped_rig"
    bl_label = "Fit Dropped Rig"
    bl_description = (
        "Fit the rig you dragged in from the BoneCraft Rigs shelf to the "
        "chosen mesh, and optionally parent the mesh with automatic weights"
    )
    bl_options = {"REGISTER", "UNDO"}

    # options, tuned after the click in Adjust Last Operation (act first, tune later)
    fit_to_mesh: BoolProperty(
        name="Fit Rig to Mesh",
        description="Scale and position the rig to match the mesh's bounding box",
        default=True,
    )
    auto_weight: BoolProperty(
        name="Parent + Auto-Weight Mesh",
        description="Parent the mesh to the rig with automatic vertex weights. "
                    "Writes vertex groups onto the mesh",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        # any armature: the fit clears the dropped-rig marker, and Adjust Last Operation must still be
        # able to re-run it (execute checks the marker; undo restores it before a re-run)
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def execute(self, context):
        armature = context.active_object
        if DROPPED_RIG_PROP not in armature:
            self.report({"ERROR"}, "This rig was not dragged in from the BoneCraft Rigs shelf")
            return {"CANCELLED"}
        mesh = getattr(context.scene, "boneforge_drop_target_mesh", None)
        try:
            usable = (mesh is not None and mesh.type == "MESH"
                      and mesh.name in context.view_layer.objects)
        except ReferenceError:
            usable = False
        if not usable:
            self.report({"ERROR"}, "Pick the mesh to fit the rig to")
            return {"CANCELLED"}
        do_fit = self.fit_to_mesh
        do_weight = self.auto_weight
        if not (do_fit or do_weight):
            self.report({"ERROR"}, "Turn on Fit Rig to Mesh or Auto-Weight in Adjust Last Operation")
            return {"CANCELLED"}
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        armature.select_set(True)
        context.view_layer.objects.active = armature
        if do_fit:
            bbox_min, bbox_max = _mesh_world_bbox(mesh)
            fit_armature_to_bbox(context, armature, bbox_min, bbox_max,
                                 str(armature.get(DROPPED_RIG_PROP, "fallback")))
        if do_weight:
            parent_mesh_with_auto_weights(context, armature, mesh)
            context.view_layer.objects.active = armature
        del armature[DROPPED_RIG_PROP]
        self.report({"INFO"}, f"Fitted '{armature.name}' to '{mesh.name}'")
        return {"FINISHED"}


_classes = (
    BF_OT_AddQuickRig,
    BF_OT_EnableRigify,
    BF_OT_SetRestPose,
    BF_OT_GenerateRigifyControlRig,
    BF_OT_InspectRigifyControls,
    BF_OT_DiagnoseQuickRig,
    BF_OT_FitDroppedRig,
)


def register():
    # v3.8.4: removed auto-enable of Rigify. Users now click an
    # explicit "Enable Rigify" button in the Quick Rig panel; this
    # makes the dependency obvious instead of magic-on-install.
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass

    bpy.types.Scene.boneforge_quick_rig_fit_to_mesh = bpy.props.BoolProperty(
        name="Fit Rig to Active Mesh",
        description="Scale and position the next rig to match the "
                    "active mesh's world-space bounding box. This does "
                    "not affect controller generation",
        default=True,
    )
    bpy.types.Scene.boneforge_quick_rig_auto_weight = bpy.props.BoolProperty(
        name="Parent + Auto-Weight Mesh",
        description="After adding the rig, parent the active mesh to "
                    "it with automatic vertex weight skinning. "
                    "Destructive — writes vertex groups onto the mesh",
        default=False,
    )
    bpy.types.Scene.boneforge_quick_rig_generate_controls = bpy.props.BoolProperty(
        name="Add IK/FK Controllers",
        description="Off: bones only. On: generate Rigify IK/FK "
                    "controllers on top of the rig. Only effective on "
                    "actual Rigify metarigs",
        default=True,
    )
    bpy.types.Scene.boneforge_quick_rig_initial_pose = bpy.props.EnumProperty(
        name="Initial Pose",
        description=(
            "Pose the metarig before generating any control rig. "
            "Choose T-Pose or A-Pose here and the controllers, widget "
            "offsets, and IK targets bake against that pose from the "
            "start — no need for the post-generation regenerate dialog"
        ),
        items=(
            ("KEEP_DEFAULT", "Keep Default",
             "Use the metarig's shipped pose"),
            ("T_POSE", "T-Pose",
             "Apply T-pose immediately after spawning"),
            ("A_POSE", "A-Pose",
             "Apply A-pose immediately after spawning"),
        ),
        default="KEEP_DEFAULT",
    )
    bpy.types.Scene.boneforge_drop_target_mesh = bpy.props.PointerProperty(
        name="Mesh",
        description="Mesh the dropped rig is fitted to",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "MESH",
    )


def unregister():
    for prop in ("boneforge_quick_rig_fit_to_mesh",
                 "boneforge_quick_rig_auto_weight",
                 "boneforge_quick_rig_generate_controls",
                 "boneforge_quick_rig_initial_pose",
                 "boneforge_drop_target_mesh"):
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
