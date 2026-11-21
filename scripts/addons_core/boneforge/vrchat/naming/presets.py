"""BoneCraft VRChat — Preset Naming Application.

Load JSON preset files that map source bone names to target names.
Apply presets to rename bones with before/after preview.

Category: VRChat Naming.
"""

import json
import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.i18n import T


# ── Preset Paths ─────────────────────────────────────────────────

def _get_data_dir():
    """Return the absolute path to the naming/data directory."""
    addon_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(addon_dir, "vrchat", "naming", "data")


# ── Preset Loading ───────────────────────────────────────────────

def get_available_presets():
    """Return a list of available preset filenames (without .json extension)."""
    data_dir = _get_data_dir()
    if not os.path.isdir(data_dir):
        return []

    presets = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            presets.append(filename[:-5])  # Remove .json

    return sorted(presets)


def load_preset(preset_name: str):
    """
    Load a preset file by name (without .json extension).
    Returns a list of mapping entries, or empty list if not found.

    Each entry is a dict with keys: source, target, confidence, slot.
    """
    data_dir = _get_data_dir()
    preset_path = os.path.join(data_dir, f"{preset_name}.json")

    if not os.path.isfile(preset_path):
        return []

    try:
        with open(preset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(data, list):
        return data
    return []


def _find_bone_by_name(armature_data, name: str):
    """Find a bone by exact name match."""
    for bone in armature_data.bones:
        if bone.name == name:
            return bone
    return None


# ── Preset Application ──────────────────────────────────────────

def apply_preset(armature, preset_name: str):
    """
    Apply a preset to rename bones in the armature.

    Returns:
        tuple: (renamed_count, unmatched_list)
        - renamed_count: int, number of bones successfully renamed
        - unmatched_list: list of source bone names not found
    """
    entries = load_preset(preset_name)
    if not entries:
        return 0, []

    renamed_count = 0
    unmatched = []

    for entry in entries:
        source = entry.get("source")
        target = entry.get("target")

        if not source or not target:
            continue

        bone = _find_bone_by_name(armature.data, source)
        if bone is None:
            unmatched.append(source)
        else:
            bone.name = target
            renamed_count += 1

    return renamed_count, unmatched


def preview_preset(armature, preset_name: str):
    """
    Preview what a preset would do without applying it.

    Returns:
        dict: {
            "matches": [(source, target), ...],
            "unmatched": [source_name, ...],
        }
    """
    entries = load_preset(preset_name)
    matches = []
    unmatched = []

    for entry in entries:
        source = entry.get("source")
        target = entry.get("target")

        if not source or not target:
            continue

        bone = _find_bone_by_name(armature.data, source)
        if bone is None:
            unmatched.append(source)
        else:
            matches.append((source, target))

    return {
        "matches": matches,
        "unmatched": unmatched,
    }


# ── Operator ─────────────────────────────────────────────────────

class BF_OT_VRC_ApplyNamingPreset(Operator):
    """Apply a naming preset to the active armature"""
    bl_idname = "boneforge.vrc_apply_naming_preset"
    bl_label = "Apply Naming Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(
        name="Preset",
        description="Name of the preset to apply",
        default="",
    )

    def invoke(self, context, event):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        # Get available presets for user selection
        presets = get_available_presets()
        if not presets:
            self.report({'INFO'}, "No presets available")
            return {'CANCELLED'}

        # If no preset selected, default to first
        if not self.preset_name:
            self.preset_name = presets[0]

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        arm = active_armature(context)
        if arm is None:
            return

        # Preset selector
        presets = get_available_presets()
        col = layout.column(align=True)
        col.label(text=T("Select Preset:"))

        row = col.row(align=True)
        row.prop(self, "preset_name", text="", icon='PRESET')

        # Preview
        if self.preset_name:
            preview = preview_preset(arm, self.preset_name)
            matches = preview["matches"]
            unmatched = preview["unmatched"]

            col.separator()
            col.label(text=f"Preview: {len(matches)} matches, {len(unmatched)} unmatched")

            if matches:
                box = col.box()
                box.label(text=T("Will rename:"), icon='CHECKMARK')
                for source, target in matches[:5]:  # Show first 5
                    box.label(text=f"  {source} → {target}", icon='NONE')
                if len(matches) > 5:
                    box.label(text=f"  ... and {len(matches) - 5} more")

            if unmatched:
                box = col.box()
                box.label(text=T("Not found:"), icon='INFO')
                for name in unmatched[:3]:  # Show first 3
                    box.label(text=f"  {name}", icon='NONE')
                if len(unmatched) > 3:
                    box.label(text=f"  ... and {len(unmatched) - 3} more")

    def execute(self, context):
        arm = active_armature(context)
        if arm is None:
            self.report({'WARNING'}, "No active armature")
            return {'CANCELLED'}

        renamed_count, unmatched = apply_preset(arm, self.preset_name)

        msg = f"Renamed {renamed_count} bones"
        if unmatched:
            msg += f" ({len(unmatched)} not found)"
        self.report({'INFO'}, msg)

        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_naming_presets(Panel):
    """Preset application panel"""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_naming_presets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Apply Preset"))

    @classmethod
    def poll(cls, context):
        # Suppressed from Tool tab — displayed via BoneForge tab VRChat hub.
        return False

    def draw(self, context):
        layout = self.layout
        presets = get_available_presets()

        if not presets:
            layout.label(text=T("No presets available"), icon='INFO')
            return

        col = layout.column(align=True)
        for preset_name in presets:
            op = col.operator("boneforge.vrc_apply_naming_preset",
                             text=preset_name, icon='PRESET')
            op.preset_name = preset_name


# ── Registration ─────────────────────────────────────────────────

_classes = [
    BF_OT_VRC_ApplyNamingPreset,
    BONEFORGE_PT_vrc_naming_presets,
]


def register():
    """Register presets module."""
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister presets module."""
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
