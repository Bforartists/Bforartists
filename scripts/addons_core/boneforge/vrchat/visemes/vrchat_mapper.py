"""BoneCraft VRChat — Viseme Mapper.

Auto-map shape keys to VRChat's 14 required visemes with support for
common alternates and VRoid naming conventions. Manual per-viseme mapping
and live preview also supported.
Category: VRChat Setup.
"""

import json
from pathlib import Path

import bpy
from bpy.props import EnumProperty, StringProperty, IntProperty
from bpy.types import Operator, Panel

from boneforge.core import active_armature
from boneforge.vrchat.visemes.utils import collect_shape_key_names, find_shape_key, get_mesh_objects

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────

VRCHAT_VISEMES = [
    "sil", "PP", "FF", "TH", "DD", "kk", "CH", "SS",
    "nn", "RR", "aa", "E", "I", "O", "U"
]

# Mapping of VRChat viseme names to known alternates
ALTERNATE_NAMES = {
    "sil": ["silence", "rest", "neutral", "mouth_closed"],
    "PP": ["plosive", "p", "b", "mouth_p"],
    "FF": ["labiodental", "f", "v", "mouth_f"],
    "TH": ["dental", "th", "mouth_th"],
    "DD": ["alveolar", "d", "t", "mouth_d"],
    "kk": ["velar", "k", "g", "mouth_k"],
    "CH": ["postalveolar", "ch", "j", "sh", "zh", "mouth_ch"],
    "SS": ["fricative", "s", "z", "mouth_s"],
    "nn": ["nasal", "n", "ng", "m", "mouth_n"],
    "RR": ["approximant", "r", "l", "mouth_r"],
    "aa": ["vowel_a", "a", "mouth_a", "mouth_open", "A"],
    "E": ["vowel_e", "e", "mouth_e"],
    "I": ["vowel_i", "i", "y", "mouth_i"],
    "O": ["vowel_o", "o", "mouth_o"],
    "U": ["vowel_u", "u", "mouth_u"],
}

# VRoid naming convention: Fcl_MTH_* → VRChat visemes
VROID_MAPPING = {
    "Fcl_MTH_A": "aa",
    "Fcl_MTH_I": "I",
    "Fcl_MTH_U": "U",
    "Fcl_MTH_E": "E",
    "Fcl_MTH_O": "O",
    "Fcl_MTH_CH": "CH",
    "Fcl_MTH_SS": "SS",
    "Fcl_MTH_TH": "TH",
}


# ── Utility functions ────────────────────────────────────────────────

def _load_viseme_data():
    """Load viseme definitions from JSON file."""
    data_dir = Path(__file__).parent / "data"
    viseme_file = data_dir / "vrchat_visemes.json"
    if viseme_file.exists():
        with open(viseme_file, "r") as f:
            return json.load(f)
    return {"visemes": []}


def has_vroid_shape_keys(mesh_objects):
    """Check if any mesh has VRoid-style shape keys (Fcl_MTH_*)."""
    for mesh in mesh_objects:
        if mesh.data.shape_keys:
            for key in mesh.data.shape_keys.key_blocks:
                if key.name.startswith("Fcl_MTH_"):
                    return True
    return False


def auto_map_visemes(mesh_objects):
    """Auto-map shape keys to VRChat visemes.

    Returns dict mapping vrchat_viseme -> shape_key_name.
    Tries exact match first, then alternates, then VRoid naming.
    """
    mapping = {}
    all_shape_keys = collect_shape_key_names(mesh_objects)

    for viseme in VRCHAT_VISEMES:
        # Try standard matching (exact, case-insensitive, alternates)
        alternates = ALTERNATE_NAMES.get(viseme, [])
        match = find_shape_key(viseme, all_shape_keys, alternates)
        if match:
            mapping[viseme] = match
            continue

        # Try VRoid naming convention
        for vroid_name, vroid_viseme in VROID_MAPPING.items():
            if vroid_viseme == viseme and vroid_name in all_shape_keys:
                mapping[viseme] = vroid_name
                break

    return mapping


def get_viseme_mapping(armature):
    """Retrieve stored viseme mapping from armature custom properties."""
    key = "boneforge_vrchat_visemes"
    # set_viseme_mapping stores an ID custom property, which getattr never
    # sees: read it by key (the slot list showed every slot "(unmapped)").
    raw = armature.get(key)
    if raw is not None:
        try:
            data = json.loads(raw)
            return data
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # M-07: Log JSON parse errors for debugging
            logger.error(f"[BoneCraft] JSON parse error loading viseme mapping: {e}")
    return {}


def set_viseme_mapping(armature, mapping):
    """Store viseme mapping in armature custom properties."""
    key = "boneforge_vrchat_visemes"
    armature[key] = json.dumps(mapping)


# ── Operators ────────────────────────────────────────────────────────

class BF_OT_VRC_AutoMapVisemes(Operator):
    """Auto-map all 15 VRChat visemes."""

    bl_idname = "boneforge.vrc_auto_map_visemes"
    bl_label = "Auto-Map Visemes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        meshes = get_mesh_objects(arm)
        if not meshes:
            self.report({"ERROR"}, "No mesh objects found on armature")
            return {"CANCELLED"}

        mapping = auto_map_visemes(meshes)
        set_viseme_mapping(arm, mapping)

        unmapped = [v for v in VRCHAT_VISEMES if v not in mapping]
        if unmapped:
            self.report(
                {"WARNING"},
                f"Mapped {len(mapping)}/15 visemes. Unmapped: {', '.join(unmapped)}"
            )
        else:
            self.report({"INFO"}, "Successfully mapped all 15 visemes")

        return {"FINISHED"}


CLEAR_SLOT = "__clear__"
_SHAPE_KEY_ITEMS = []  # Blender needs the enum strings to stay referenced


def _shape_key_items(self, context):
    """Search items for a viseme slot: (unmapped) plus every shape key."""
    names = set()
    arm = active_armature(context) if context is not None else None
    if arm is not None:
        for mesh in get_mesh_objects(arm):
            if mesh.data.shape_keys:
                names.update(k.name for k in mesh.data.shape_keys.key_blocks)
    _SHAPE_KEY_ITEMS[:] = [(CLEAR_SLOT, "(unmapped)", "Clear this slot")] + [
        (name, name, "") for name in sorted(names)]
    return _SHAPE_KEY_ITEMS


class BF_OT_VRC_MapSingleViseme(Operator):
    """Choose the shape key for this viseme slot"""

    bl_idname = "boneforge.vrc_map_single_viseme"
    bl_label = "Map Viseme"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "shape_key_choice"

    viseme_name: StringProperty(
        name="Viseme",
        description="VRChat viseme name"
    )
    shape_key_name: StringProperty(
        name="Shape Key",
        description="Target shape key name"
    )
    shape_key_choice: EnumProperty(
        name="Shape Key",
        description="Shape key for this viseme slot",
        items=_shape_key_items,
        options={'SKIP_SAVE'},
    )

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if self.properties.is_property_set("shape_key_choice"):
            choice = self.shape_key_choice
            self.shape_key_name = "" if choice == CLEAR_SLOT else choice
        if self.viseme_name not in VRCHAT_VISEMES:
            self.report({"ERROR"}, f"Not a VRChat viseme slot: '{self.viseme_name}'")
            return {"CANCELLED"}
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        # Validate that shape key exists
        meshes = get_mesh_objects(arm)
        all_keys = set()
        for mesh in meshes:
            if mesh.data.shape_keys:
                for key in mesh.data.shape_keys.key_blocks:
                    all_keys.add(key.name)

        if self.shape_key_name and self.shape_key_name not in all_keys:
            self.report(
                {"ERROR"},
                f"Shape key '{self.shape_key_name}' not found"
            )
            return {"CANCELLED"}

        mapping = get_viseme_mapping(arm)
        if self.shape_key_name:
            mapping[self.viseme_name] = self.shape_key_name
            message = f"Mapped {self.viseme_name} to {self.shape_key_name}"
        else:
            mapping.pop(self.viseme_name, None)
            message = f"Cleared {self.viseme_name}"

        set_viseme_mapping(arm, mapping)
        self.report({"INFO"}, message)
        return {"FINISHED"}


class BF_OT_VRC_PreviewViseme(Operator):
    """Preview a viseme by setting shape key to full value."""

    bl_idname = "boneforge.vrc_preview_viseme"
    bl_label = "Preview Viseme"
    bl_options = {"UNDO"}

    viseme_name: StringProperty(
        name="Viseme",
        description="VRChat viseme name"
    )
    preview_value: IntProperty(
        name="Value",
        description="Shape key value (0-100)",
        default=100,
        min=0,
        max=100
    )

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            return {"CANCELLED"}

        mapping = get_viseme_mapping(arm)
        shape_key_name = mapping.get(self.viseme_name)
        if not shape_key_name:
            self.report(
                {"WARNING"},
                f"Viseme '{self.viseme_name}' is not mapped"
            )
            return {"CANCELLED"}

        meshes = get_mesh_objects(arm)
        value = self.preview_value / 100.0

        for mesh in meshes:
            if mesh.data.shape_keys and shape_key_name in mesh.data.shape_keys.key_blocks:
                mesh.data.shape_keys.key_blocks[shape_key_name].value = value

        return {"FINISHED"}


# ── Panel ────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_viseme_mapper(Panel):
    """VRChat Viseme Mapper panel."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_viseme_mapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "BONEFORGE_PT_vrc_main"

    def draw_header(self, context):
        self.layout.label(text=T("VRChat Visemes"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        arm = active_armature(context)
        layout = self.layout

        if not arm:
            return

        # Check for VRoid
        meshes = get_mesh_objects(arm)
        if has_vroid_shape_keys(meshes):
            row = layout.row()
            row.alert = True
            row.label(
                text=T("VRoid shape keys detected — click Auto-Map"),
                icon="INFO"
            )

        # Auto-map button
        layout.operator(
            "boneforge.vrc_auto_map_visemes",
            text=T("Auto-Map All Visemes")
        )

        # Mapping table header
        row = layout.row()
        row.label(text=T("Viseme"))
        row.label(text=T("Mapped Shape Key"))

        mapping = get_viseme_mapping(arm)

        # Draw 15-row table
        for viseme in VRCHAT_VISEMES:
            row = layout.row()
            row.label(text=viseme)

            # Shape key selector enum
            current_key = mapping.get(viseme, "")
            op = row.operator(
                "boneforge.vrc_map_single_viseme",
                text=current_key or "(unmapped)"
            )
            op.viseme_name = viseme

        layout.separator()


# ── Registration ─────────────────────────────────────────────────────

classes = (
    BF_OT_VRC_AutoMapVisemes,
    BF_OT_VRC_MapSingleViseme,
    BF_OT_VRC_PreviewViseme,
    BONEFORGE_PT_vrc_viseme_mapper,
)


def register():
    """Register viseme mapper classes."""
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """Unregister viseme mapper classes."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
