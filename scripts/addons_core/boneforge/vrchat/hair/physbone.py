"""BoneCraft VRChat — PhysBone Parameter System.

Manages PhysBone presets, parameters, and storage as JSON on root bones.
Presets include Hair, Skirt/Cape, and Tail/Rope with sensible defaults.
Full parameter set stored in boneforge_vrchat_physbone namespace.

Category: Hair Physics.
"""

import json
import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
from typing import Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from boneforge.core import active_armature, read_custom_json, write_custom_json
from boneforge.i18n import T


# ── PhysBone Configuration ─────────────────────────────────────

@dataclass
class PhysBoneConfig:
    """Complete PhysBone parameter configuration."""
    # M-05: Version field for schema evolution
    version: int = 1
    pull: float = 0.2
    spring: float = 0.4
    stiffness: float = 0.2
    gravity: float = 0.3
    gravity_falloff: float = 1.0
    immobile_type: str = "ALL_MOTION"
    immobile: float = 0.0
    max_angle: float = 60.0
    radius: float = 0.02
    grab_permission: bool = True
    pose_permission: bool = True

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> 'PhysBoneConfig':
        """Create instance from dict, filling missing keys with defaults."""
        defaults = PhysBoneConfig().__dict__
        merged = {**defaults, **{k: v for k, v in data.items() if k in defaults}}
        return PhysBoneConfig(**merged)


# ── Built-in presets ──────────────────────────────────────────

PHYSBONE_PRESETS = {
    "Hair": PhysBoneConfig(
        pull=0.2,
        spring=0.4,
        stiffness=0.2,
        gravity=0.3,
        gravity_falloff=1.0,
        immobile_type="ALL_MOTION",
        immobile=0.0,
        max_angle=60.0,
        radius=0.02,
        grab_permission=True,
        pose_permission=True,
    ),
    "Skirt/Cape": PhysBoneConfig(
        pull=0.15,
        spring=0.3,
        stiffness=0.1,
        gravity=0.5,
        gravity_falloff=1.0,
        immobile_type="ALL_MOTION",
        immobile=0.0,
        max_angle=90.0,
        radius=0.03,
        grab_permission=True,
        pose_permission=True,
    ),
    "Tail/Rope": PhysBoneConfig(
        pull=0.1,
        spring=0.2,
        stiffness=0.05,
        gravity=0.6,
        gravity_falloff=1.0,
        immobile_type="ALL_MOTION",
        immobile=0.0,
        max_angle=120.0,
        radius=0.02,
        grab_permission=True,
        pose_permission=True,
    ),
}


# ── PhysBone storage functions ─────────────────────────────────

def apply_preset(bone: bpy.types.Bone, preset_name: str) -> bool:
    """Apply a named preset to a bone.

    Stores the PhysBone configuration as JSON in boneforge_vrchat_physbone.
    Returns True if successful, False if preset not found.
    """
    if preset_name not in PHYSBONE_PRESETS:
        return False

    config = PHYSBONE_PRESETS[preset_name]
    write_custom_json(bone, "boneforge_vrchat_physbone", config.to_dict())
    return True


def read_physbone(bone: bpy.types.Bone) -> Optional[PhysBoneConfig]:
    """Read PhysBone configuration from bone.

    Returns PhysBoneConfig or None if not configured.
    """
    data = read_custom_json(bone, "boneforge_vrchat_physbone", None)
    if data is None:
        return None
    return PhysBoneConfig.from_dict(data)


def write_physbone(bone: bpy.types.Bone, config: PhysBoneConfig) -> None:
    """Write PhysBone configuration to bone."""
    write_custom_json(bone, "boneforge_vrchat_physbone", config.to_dict())


# ── Custom presets ────────────────────────────────────────────

def _get_presets_dir() -> Path:
    """Get or create the custom presets directory."""
    presets_dir = Path(__file__).parent / "data" / "presets"
    presets_dir.mkdir(parents=True, exist_ok=True)
    return presets_dir


def load_custom_preset(preset_name: str) -> Optional[PhysBoneConfig]:
    """Load a custom preset from disk by name."""
    presets_dir = _get_presets_dir()
    preset_file = presets_dir / f"{preset_name}.json"

    if not preset_file.exists():
        return None

    try:
        with open(preset_file, 'r') as f:
            data = json.load(f)
        return PhysBoneConfig.from_dict(data)
    except (json.JSONDecodeError, IOError):
        return None


def save_custom_preset(preset_name: str, config: PhysBoneConfig) -> bool:
    """Save a custom preset to disk.

    Returns True on success, False on error.
    """
    presets_dir = _get_presets_dir()
    preset_file = presets_dir / f"{preset_name}.json"

    try:
        with open(preset_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        return True
    except IOError:
        return False


def list_custom_presets() -> list[str]:
    """List all available custom preset names."""
    presets_dir = _get_presets_dir()
    if not presets_dir.exists():
        return []
    return [f.stem for f in presets_dir.glob("*.json")]


# ── Operators ──────────────────────────────────────────────────

class BF_OT_VRC_ApplyPhysBonePreset(Operator):
    """Apply a PhysBone preset to selected bones."""

    bl_idname = "boneforge.vrc_apply_physbone_preset"
    bl_label = "Apply PhysBone Preset"
    bl_description = "Apply a preset configuration to the selected bone chain root"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: EnumProperty(
        name="Preset",
        description="PhysBone preset to apply",
        items=[
            ("Hair", "Hair", "Typical hair settings"),
            ("Skirt/Cape", "Skirt/Cape", "Skirt or cape settings"),
            ("Tail/Rope", "Tail/Rope", "Tail or rope settings"),
        ],
        default="Hair",
    )

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        arm_data = arm_obj.data
        selected_bones = [b for b in arm_data.bones if b.select]

        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        applied_count = 0
        for bone in selected_bones:
            if apply_preset(bone, self.preset_name):
                applied_count += 1

        if applied_count > 0:
            self.report({'INFO'}, f"Applied preset to {applied_count} bone(s)")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Could not apply preset")
            return {'CANCELLED'}


class BF_OT_VRC_SetPhysBoneParams(Operator):
    """Edit full PhysBone parameters on selected bone."""

    bl_idname = "boneforge.vrc_set_physbone_params"
    bl_label = "Edit PhysBone Parameters"
    bl_description = "Edit all PhysBone parameters for the selected bone"
    bl_options = {"REGISTER", "UNDO"}

    pull: FloatProperty(description='How strongly the chain pulls back to its rest shape', min=0.0, max=1.0, default=0.2)
    spring: FloatProperty(description='How much the chain bounces and overshoots', min=0.0, max=1.0, default=0.4)
    stiffness: FloatProperty(description='How much the chain keeps its rest shape while moving', min=0.0, max=1.0, default=0.2)
    gravity: FloatProperty(description='How strongly gravity pulls the chain down', min=0.0, max=1.0, default=0.3)
    gravity_falloff: FloatProperty(description='How much less gravity acts when the chain hangs at rest', min=0.0, max=1.0, default=1.0)
    max_angle: FloatProperty(description='Largest angle, in degrees, the chain may bend from rest', min=0.0, max=180.0, default=60.0)
    radius: FloatProperty(description='Collision radius of each bone', min=0.0, default=0.02)
    immobile: FloatProperty(description="How much the chain ignores the avatar's own movement", min=0.0, max=1.0, default=0.0)
    grab_permission: BoolProperty(description='Let other players grab the chain', default=True)
    pose_permission: BoolProperty(description='Let other players leave the chain posed after grabbing it', default=True)

    immobile_type: EnumProperty(description="Which movement Immobile ignores: all motion, world movement or local movement",
        name="Immobile Type",
        items=[
            ("ALL_MOTION", "All Motion", ""),
            ("WORLD", "World", ""),
            ("LOCAL", "Local", ""),
        ],
        default="ALL_MOTION",
    )

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        arm_data = arm_obj.data
        selected_bones = [b for b in arm_data.bones if b.select]

        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        config = PhysBoneConfig(
            pull=self.pull,
            spring=self.spring,
            stiffness=self.stiffness,
            gravity=self.gravity,
            gravity_falloff=self.gravity_falloff,
            immobile_type=self.immobile_type,
            immobile=self.immobile,
            max_angle=self.max_angle,
            radius=self.radius,
            grab_permission=self.grab_permission,
            pose_permission=self.pose_permission,
        )

        for bone in selected_bones:
            write_physbone(bone, config)

        self.report({'INFO'}, f"Updated {len(selected_bones)} bone(s)")
        return {'FINISHED'}


class BF_OT_VRC_SaveCustomPreset(Operator):
    """Save current bone's parameters as a custom preset."""

    bl_idname = "boneforge.vrc_save_custom_preset"
    bl_label = "Save Custom Preset"
    bl_description = "Save the current PhysBone configuration as a custom preset"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(
        name="Preset Name",
        description="Name for the custom preset",
        default="MyPreset",
    )

    def execute(self, context):
        arm_obj = active_armature(context)
        if arm_obj is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        arm_data = arm_obj.data
        selected_bones = [b for b in arm_data.bones if b.select]

        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        bone = selected_bones[0]
        config = read_physbone(bone)

        if config is None:
            self.report({'ERROR'}, "Selected bone has no PhysBone configuration")
            return {'CANCELLED'}

        if save_custom_preset(self.preset_name, config):
            self.report({'INFO'}, f"Saved preset '{self.preset_name}'")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to save preset")
            return {'CANCELLED'}


class BF_OT_VRC_AddPhysBoneChain(Operator):
    """Add PhysBone physics to the selected bone chain."""

    bl_idname = "boneforge.vrc_add_physbone_chain"
    bl_label = "Add PhysBone Chain"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        from boneforge.core import active_armature
        return active_armature(context) is not None

    def execute(self, context):
        from boneforge.core import active_armature, write_custom_json
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        # Get selected bones in pose mode, or fall back to active bone
        if context.mode == 'POSE' and context.selected_pose_bones:
            root_bone_name = context.selected_pose_bones[0].name
        elif arm.data.bones.active:
            root_bone_name = arm.data.bones.active.name
        else:
            self.report({'ERROR'}, "Select a bone to use as chain root")
            return {'CANCELLED'}

        # Create default PhysBone config
        config = {
            "version": 1,
            "pull": 0.2,
            "spring": 0.2,
            "stiffness": 0.2,
            "gravity": 0.0,
            "gravity_falloff": 0.0,
            "immobile_type": "All",
            "immobile": 0.0,
            "radius": 0.0,
            "allow_collision": True,
            "allow_grabbing": True,
            "allow_posing": True,
        }

        # Store on the root bone
        bone = arm.data.bones.get(root_bone_name)
        if bone is None:
            self.report({'ERROR'}, f"Bone '{root_bone_name}' not found")
            return {'CANCELLED'}

        write_custom_json(bone, "boneforge_vrchat_physbone", config)
        self.report({'INFO'}, f"Added PhysBone config to '{root_bone_name}'")
        return {'FINISHED'}


class BF_OT_VRC_RemovePhysBoneChain(Operator):
    """Remove PhysBone physics from the selected bone chain."""

    bl_idname = "boneforge.vrc_remove_physbone_chain"
    bl_label = "Remove PhysBone Chain"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        from boneforge.core import active_armature
        return active_armature(context) is not None

    def execute(self, context):
        from boneforge.core import active_armature
        arm = active_armature(context)
        if arm is None:
            self.report({'ERROR'}, "No active armature")
            return {'CANCELLED'}

        if arm.data.bones.active:
            root_bone_name = arm.data.bones.active.name
        else:
            self.report({'ERROR'}, "Select a bone chain root")
            return {'CANCELLED'}

        bone = arm.data.bones.get(root_bone_name)
        if bone is None or 'boneforge_vrchat_physbone' not in bone:
            self.report({'WARNING'}, f"No PhysBone config on '{root_bone_name}'")
            return {'CANCELLED'}

        del bone['boneforge_vrchat_physbone']
        self.report({'INFO'}, f"Removed PhysBone config from '{root_bone_name}'")
        return {'FINISHED'}


# ── Panels ─────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_physbone(Panel):
    """PhysBone Configuration Panel."""

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = " "
    bl_parent_id = "BONEFORGE_PT_vrc_hair"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("PhysBone Configuration"))

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
        selected_bones = [b for b in arm_data.bones if b.select]

        if not selected_bones:
            layout.label(text=T("Select a bone to configure"))
            return

        bone = selected_bones[0]
        config = read_physbone(bone)

        layout.label(text=f"Bone: {bone.name}")

        # Preset buttons
        row = layout.row()
        row.operator("boneforge.vrc_apply_physbone_preset", text=T("Hair")).preset_name = "Hair"
        row.operator("boneforge.vrc_apply_physbone_preset", text=T("Skirt")).preset_name = "Skirt/Cape"
        row.operator("boneforge.vrc_apply_physbone_preset", text=T("Tail")).preset_name = "Tail/Rope"

        if config is not None:
            layout.separator()
            layout.label(text=T("Parameters:"))
            col = layout.column()
            col.label(text=f"Pull: {config.pull:.2f}")
            col.label(text=f"Spring: {config.spring:.2f}")
            col.label(text=f"Stiffness: {config.stiffness:.2f}")
            col.label(text=f"Gravity: {config.gravity:.2f}")
            col.label(text=f"Max Angle: {config.max_angle:.1f}°")


def register():
    """Register PhysBone operators and panels."""
    bpy.utils.register_class(BF_OT_VRC_ApplyPhysBonePreset)
    bpy.utils.register_class(BF_OT_VRC_SetPhysBoneParams)
    bpy.utils.register_class(BF_OT_VRC_SaveCustomPreset)
    bpy.utils.register_class(BF_OT_VRC_AddPhysBoneChain)
    bpy.utils.register_class(BF_OT_VRC_RemovePhysBoneChain)
    bpy.utils.register_class(BONEFORGE_PT_vrc_physbone)


def unregister():
    """Unregister PhysBone operators and panels."""
    bpy.utils.unregister_class(BONEFORGE_PT_vrc_physbone)
    bpy.utils.unregister_class(BF_OT_VRC_RemovePhysBoneChain)
    bpy.utils.unregister_class(BF_OT_VRC_AddPhysBoneChain)
    bpy.utils.unregister_class(BF_OT_VRC_SaveCustomPreset)
    bpy.utils.unregister_class(BF_OT_VRC_SetPhysBoneParams)
    bpy.utils.unregister_class(BF_OT_VRC_ApplyPhysBonePreset)
