"""BoneCraft VRChat — PhysBone Collider Setup.

Places and manages collider objects for hair physics interaction.
Includes 4 default colliders (Head, Chest, Left Hand, Right Hand).

Category: Hair Physics.
"""

import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty, FloatProperty, EnumProperty
from typing import Optional
from dataclasses import dataclass, asdict
from boneforge.core import active_armature, read_custom_json, write_custom_json
from boneforge.i18n import T

import logging

logger = logging.getLogger(__name__)


# ── Bone name variants ─────────────────────────────────────────
# Support multiple naming conventions: Blender, MMD, VRoid, Mixamo, Rigify

HEAD_NAMES = ["Head", "head", "頭", "J_Bip_C_Head", "mixamorig:Head", "DEF-spine.006"]
CHEST_NAMES = ["Chest", "chest", "上半身", "J_Bip_C_Chest", "J_Bip_C_UpperBody", "mixamorig:Spine2", "DEF-spine.003", "Upper Body"]
LEFT_HAND_NAMES = ["LeftHand", "Left Hand", "left_hand", "左手首", "J_Bip_L_Hand", "mixamorig:LeftHand", "DEF-hand.L"]
RIGHT_HAND_NAMES = ["RightHand", "Right Hand", "right_hand", "右手首", "J_Bip_R_Hand", "mixamorig:RightHand", "DEF-hand.R"]


def _find_bone_by_names(armature: bpy.types.Armature, name_list: list) -> Optional[bpy.types.Bone]:
    """Find a bone by trying multiple name variants.

    Args:
        armature: The armature to search in
        name_list: List of possible bone names to try

    Returns:
        First matching bone or None if no match found
    """
    for bone in armature.bones:
        if bone.name in name_list:
            return bone

    # Fallback: try case-insensitive matching
    for bone in armature.bones:
        if bone.name.lower() in [n.lower() for n in name_list]:
            return bone

    return None


# ── Collider configuration ─────────────────────────────────────

@dataclass
class ColliderConfig:
    """PhysBone collider configuration."""
    collider_type: str = "SPHERE"  # SPHERE or CAPSULE
    radius: float = 0.1
    height: float = 0.2
    parent_bone: str = "head"

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> 'ColliderConfig':
        """Create instance from dict."""
        defaults = ColliderConfig().__dict__
        merged = {**defaults, **{k: v for k, v in data.items() if k in defaults}}
        return ColliderConfig(**merged)


# ── Default colliders ──────────────────────────────────────────

DEFAULT_COLLIDERS = {
    "Head": {
        "config": ColliderConfig(
            collider_type="SPHERE",
            radius=0.12,
            height=0.0,
            parent_bone="head",
        ),
        "bone_names": HEAD_NAMES,
    },
    "Chest": {
        "config": ColliderConfig(
            collider_type="CAPSULE",
            radius=0.15,
            height=0.3,
            parent_bone="chest",
        ),
        "bone_names": CHEST_NAMES,
    },
    "Left Hand": {
        "config": ColliderConfig(
            collider_type="SPHERE",
            radius=0.08,
            height=0.0,
            parent_bone="hand.L",
        ),
        "bone_names": LEFT_HAND_NAMES,
    },
    "Right Hand": {
        "config": ColliderConfig(
            collider_type="SPHERE",
            radius=0.08,
            height=0.0,
            parent_bone="hand.R",
        ),
        "bone_names": RIGHT_HAND_NAMES,
    },
}


# ── Collider management functions ──────────────────────────────

def _get_collider_obj_name(collider_name: str) -> str:
    """Get the Blender object name for a collider."""
    return f"VRC_Collider_{collider_name.replace(' ', '_')}"


def place_default_colliders(armature: bpy.types.Armature,
                             arm_obj: bpy.types.Object,
                             report_func=None) -> list[str]:
    """Create and place all default collider objects.

    Creates sphere/capsule objects positioned at bone locations.
    Supports multiple bone naming conventions (Blender, MMD, VRoid, Mixamo, Rigify).

    Args:
        armature: The armature to place colliders on
        arm_obj: The armature object
        report_func: Optional function to call for warnings (e.g., operator.report)

    Returns:
        List of created collider object names.
    """
    created = []
    scene = bpy.context.scene
    collection = bpy.context.collection

    for collider_name, collider_data in DEFAULT_COLLIDERS.items():
        config = collider_data["config"]
        bone_names = collider_data["bone_names"]

        # Find the target bone using multi-convention lookup
        target_bone = _find_bone_by_names(armature, bone_names)

        if target_bone is None:
            # Log warning instead of silently skipping
            msg = f"Could not find {collider_name.lower()} bone for collider placement (tried: {', '.join(bone_names)})"
            if report_func:
                report_func({'WARNING'}, msg)
            else:
                logger.warning(f"[BoneCraft] {msg}")
            continue

        # Create collider object
        obj_name = _get_collider_obj_name(collider_name)

        # Remove old collider if it exists
        old_obj = bpy.data.objects.get(obj_name)
        if old_obj is not None:
            bpy.data.objects.remove(old_obj, do_unlink=True)

        # Create mesh
        if config.collider_type == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=config.radius)
        else:  # CAPSULE
            bpy.ops.mesh.primitive_cylinder_add(radius=config.radius, depth=config.height)

        collider_obj = bpy.context.active_object
        collider_obj.name = obj_name
        collider_obj.display_type = 'WIRE'
        collider_obj.hide_render = True

        # C-14: Position at bone using proper matrix transform to account for armature rotation/scale
        collider_obj.location = arm_obj.matrix_world @ target_bone.head_local

        # Add to collection
        if obj_name not in collection.objects:
            collection.objects.link(collider_obj)

        # Store metadata
        write_custom_json(collider_obj, "boneforge_vrchat_collider", config.to_dict())

        created.append(obj_name)

    return created


def read_collider_config(obj: bpy.types.Object) -> Optional[ColliderConfig]:
    """Read collider configuration from object.

    Returns ColliderConfig or None if not a collider.
    """
    data = read_custom_json(obj, "boneforge_vrchat_collider", None)
    if data is None:
        return None
    return ColliderConfig.from_dict(data)


def write_collider_config(obj: bpy.types.Object, config: ColliderConfig) -> None:
    """Write collider configuration to object."""
    write_custom_json(obj, "boneforge_vrchat_collider", config.to_dict())


def is_collider_object(obj: bpy.types.Object) -> bool:
    """Check if an object is a VRChat collider."""
    return read_collider_config(obj) is not None


# ── Operators ──────────────────────────────────────────────────

class BF_OT_VRC_PlaceDefaultColliders(Operator):
    """Place all default colliders in the scene."""

    bl_idname = "boneforge.vrc_place_default_colliders"
    bl_label = "Place Default Colliders"
    bl_description = "Create default collider objects for hair physics"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        created = place_default_colliders(arm_obj.data, arm_obj, self.report)

        if created:
            self.report({'INFO'}, f"Created {len(created)} colliders")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Could not create colliders (no bones matched)")
            return {'CANCELLED'}


class BF_OT_VRC_AddCollider(Operator):
    """Add a custom collider to a bone."""

    bl_idname = "boneforge.vrc_add_collider"
    bl_label = "Add Collider"
    bl_description = "Add a collider for hair physics interaction"
    bl_options = {"REGISTER", "UNDO"}

    collider_type: EnumProperty(
        name="Type",
        description="Collider shape type",
        items=[
            ("SPHERE", "Sphere", "Spherical collider"),
            ("CAPSULE", "Capsule", "Capsule collider"),
        ],
        default="SPHERE",
    )

    parent_bone: StringProperty(
        name="Parent Bone",
        description="Bone to attach collider to",
        default="head",
    )

    radius: FloatProperty(
        name="Radius",
        description="Collider radius in scene units",
        default=0.1,
        min=0.01,
    )

    height: FloatProperty(
        name="Height",
        description="Capsule height (0 for sphere)",
        default=0.2,
        min=0.0,
    )

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        arm_data = arm_obj.data

        # Find target bone
        target_bone = None
        for bone in arm_data.bones:
            if bone.name == self.parent_bone:
                target_bone = bone
                break

        if target_bone is None:
            self.report({'ERROR'}, f"Bone '{self.parent_bone}' not found")
            return {'CANCELLED'}

        # Create collider object
        if self.collider_type == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=self.radius)
        else:  # CAPSULE
            bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=self.height)

        collider_obj = bpy.context.active_object
        collider_obj.name = f"Collider_{self.parent_bone}"
        collider_obj.display_type = 'WIRE'
        collider_obj.hide_render = True

        # C-14: Position at bone using proper matrix transform to account for armature rotation/scale
        collider_obj.location = arm_obj.matrix_world @ target_bone.head_local

        # Store config
        config = ColliderConfig(
            collider_type=self.collider_type,
            radius=self.radius,
            height=self.height,
            parent_bone=self.parent_bone,
        )
        write_collider_config(collider_obj, config)

        self.report({'INFO'}, f"Created collider for '{self.parent_bone}'")
        return {'FINISHED'}


class BF_OT_VRC_RemoveCollider(Operator):
    """Remove a collider object."""

    bl_idname = "boneforge.vrc_remove_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove a collider object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object

        if obj is None or not is_collider_object(obj):
            self.report({'ERROR'}, "Select a collider object")
            return {'CANCELLED'}

        obj_name = obj.name
        bpy.data.objects.remove(obj, do_unlink=True)

        self.report({'INFO'}, f"Removed collider '{obj_name}'")
        return {'FINISHED'}


# ── Panels ─────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_colliders(Panel):
    """Hair Physics Collider Panel."""

    # M-12: Explicit bl_idname for panel registration
    bl_idname = "BONEFORGE_PT_vrc_colliders"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = " "
    bl_parent_id = "BONEFORGE_PT_vrc_hair"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Hair Physics Colliders"))

    @classmethod
    def poll(cls, context):
        """Show panel only when active object is an armature."""
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout

        # Default colliders section
        layout.label(text=T("Default Colliders:"))
        row = layout.row()
        row.operator("boneforge.vrc_place_default_colliders", icon='SPHERE')

        # List existing colliders
        colliders = [obj for obj in bpy.context.scene.objects if is_collider_object(obj)]

        if colliders:
            layout.separator()
            layout.label(text=T("Placed Colliders:"))
            col = layout.column(align=True)
            for collider_obj in colliders:
                row = col.row(align=True)
                row.label(text=f"  {collider_obj.name}", icon='SPHERE')

        # Add custom collider section
        layout.separator()
        layout.label(text=T("Add Custom Collider:"))

        op = layout.operator("boneforge.vrc_add_collider", icon='ADD')
        op.collider_type = "SPHERE"
        op.parent_bone = "head"
        op.radius = 0.1

        # Remove collider
        if context.active_object and is_collider_object(context.active_object):
            layout.separator()
            layout.operator("boneforge.vrc_remove_collider", icon='X')


def register():
    """Register collider operators and panels."""
    bpy.utils.register_class(BF_OT_VRC_PlaceDefaultColliders)
    bpy.utils.register_class(BF_OT_VRC_AddCollider)
    bpy.utils.register_class(BF_OT_VRC_RemoveCollider)
    bpy.utils.register_class(BONEFORGE_PT_vrc_colliders)


def unregister():
    """Unregister collider operators and panels."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_colliders)
    bpy.utils.unregister_class(BF_OT_VRC_RemoveCollider)
    bpy.utils.unregister_class(BF_OT_VRC_AddCollider)
    bpy.utils.unregister_class(BF_OT_VRC_PlaceDefaultColliders)
