"""BoneCraft VRChat CATS — Viseme Generator.

Generates 15 VRChat standard viseme shape keys by blending three user-supplied
base mouth shapes (A, O, CH) with per-viseme coefficients.

Category: VRChat Cats Tools.
"""

import logging

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline
from boneforge.vrchat.cats.validator import get_warning_message

logger = logging.getLogger(__name__)


# ── Viseme blend coefficients ────────────────────────────────────────────────
# (A_weight, O_weight, CH_weight) for each VRChat viseme key.

VISEME_COEFFICIENTS = {
    "vrc.v_sil": (0.0, 0.0, 0.0),
    "vrc.v_PP":  (0.0, 0.0, 0.0),
    "vrc.v_FF":  (0.2, 0.0, 0.0),
    "vrc.v_TH":  (0.4, 0.0, 0.0),
    "vrc.v_DD":  (0.3, 0.7, 0.0),
    "vrc.v_kk":  (0.7, 0.4, 0.0),
    "vrc.v_CH":  (0.0, 0.0, 1.0),
    "vrc.v_SS":  (0.0, 0.0, 0.8),
    "vrc.v_nn":  (0.2, 0.0, 0.0),
    "vrc.v_RR":  (0.0, 0.5, 0.3),
    "vrc.v_aa":  (1.0, 0.0, 0.0),
    "vrc.v_E":   (0.7, 0.0, 0.3),
    "vrc.v_I":   (0.4, 0.0, 0.7),
    "vrc.v_O":   (0.0, 1.0, 0.0),
    "vrc.v_U":   (0.0, 0.8, 0.0),
}

# ── Auto-detect candidate name lists ────────────────────────────────────────

_A_PATTERNS = [
    "mouth_a", "mth_a", "fcl_mth_a", "あ", "a_mouth", "a", "ah", "mouth_open",
]
_O_PATTERNS = [
    "mouth_o", "mth_o", "fcl_mth_o", "お", "o_mouth", "o", "oh", "mouth_round",
]
_CH_PATTERNS = [
    "mouth_ch", "mth_ch", "fcl_mth_ch", "chi", "ch_mouth", "ch", "smile", "teeth",
]


# ── Settings PropertyGroup ───────────────────────────────────────────────────

class BF_VisemeGenSettings(PropertyGroup):
    """Per-scene settings for the Viseme Generator."""

    a_shape: StringProperty(
        name="A Shape",
        description="Shape key for open mouth (A/AA)",
        default="",
    )
    o_shape: StringProperty(
        name="O Shape",
        description="Shape key for rounded mouth (O/OH)",
        default="",
    )
    ch_shape: StringProperty(
        name="CH Shape",
        description="Shape key for teeth/CH",
        default="",
    )
    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        description="Replace existing vrc.v_ shape keys",
        default=False,
    )


# ── Private helpers ──────────────────────────────────────────────────────────

def _get_mesh_with_shape_keys(context):
    """Return (obj, shape_keys) for the first mesh child with shape keys.

    Searches mesh children of the active armature. Returns (None, None) when
    no suitable mesh is found.
    """
    arm = active_armature(context)
    if arm is None:
        return None, None

    for child in arm.children:
        if child.type != 'MESH':
            continue
        sk = child.data.shape_keys
        if sk and sk.key_blocks:
            return child, sk

    return None, None


def _auto_detect_shapes(mesh_obj):
    """Search shape key names for common A/O/CH pattern matches.

    Returns:
        dict with keys "a", "o", "ch" each mapping to a matched name or None.
    """
    if mesh_obj is None or mesh_obj.data.shape_keys is None:
        return {"a": None, "o": None, "ch": None}

    sk_names = [kb.name for kb in mesh_obj.data.shape_keys.key_blocks]
    sk_lower = {name.lower(): name for name in sk_names}

    def _match(patterns):
        for pat in patterns:
            if pat in sk_lower:
                return sk_lower[pat]
        return None

    return {
        "a": _match(_A_PATTERNS),
        "o": _match(_O_PATTERNS),
        "ch": _match(_CH_PATTERNS),
    }


# ── Operators ────────────────────────────────────────────────────────────────

class BF_OT_CATS_AutoDetectShapes(Operator):
    """Auto-detect A, O, and CH base mouth shape keys from the avatar mesh"""

    bl_idname = "boneforge.cats_auto_detect_shapes"
    bl_label = "Auto-Detect Shapes"
    bl_options = {'REGISTER'}

    def execute(self, context):
        mesh_obj, _ = _get_mesh_with_shape_keys(context)
        if mesh_obj is None:
            self.report({'ERROR'}, "No mesh with shape keys found under active armature")
            return {'CANCELLED'}

        detected = _auto_detect_shapes(mesh_obj)
        settings = context.scene.boneforge_cats_viseme_settings

        found = []
        missing = []

        if detected["a"]:
            settings.a_shape = detected["a"]
            found.append(f"A='{detected['a']}'")
        else:
            missing.append("A")

        if detected["o"]:
            settings.o_shape = detected["o"]
            found.append(f"O='{detected['o']}'")
        else:
            missing.append("O")

        if detected["ch"]:
            settings.ch_shape = detected["ch"]
            found.append(f"CH='{detected['ch']}'")
        else:
            missing.append("CH")

        if found:
            self.report({'INFO'}, f"Detected: {', '.join(found)}" + (
                f" | Not found: {', '.join(missing)}" if missing else ""
            ))
        else:
            self.report({'WARNING'}, "Could not auto-detect any base mouth shapes")

        return {'FINISHED'}


class BF_OT_CATS_GenerateVisemes(Operator):
    """Generate 15 VRChat viseme shape keys from A, O, and CH base shapes"""

    bl_idname = "boneforge.cats_generate_visemes"
    bl_label = "Generate Visemes"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        warning = get_warning_message(context.scene, "visemes")
        if warning:
            self.report({'WARNING'}, warning)
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        settings = scene.boneforge_cats_viseme_settings

        a_name = settings.a_shape.strip()
        o_name = settings.o_shape.strip()
        ch_name = settings.ch_shape.strip()

        # Validate shape names are set
        if not a_name or not o_name or not ch_name:
            self.report({'ERROR'}, "A, O, and CH shape keys must all be set")
            return {'CANCELLED'}

        mesh_obj, shape_keys = _get_mesh_with_shape_keys(context)
        if mesh_obj is None:
            self.report({'ERROR'}, "No mesh with shape keys found under active armature")
            return {'CANCELLED'}

        sk_block_names = {kb.name for kb in shape_keys.key_blocks}

        # Validate all three base shapes exist
        missing = [n for n in (a_name, o_name, ch_name) if n not in sk_block_names]
        if missing:
            self.report({'ERROR'}, f"Shape key(s) not found: {', '.join(missing)}")
            return {'CANCELLED'}

        n_verts = len(mesh_obj.data.vertices)
        n_coords = n_verts * 3

        # Pre-read basis coordinates
        basis_cos = [0.0] * n_coords
        shape_keys.key_blocks["Basis"].data.foreach_get("co", basis_cos)

        # Pre-read A/O/CH coordinates and compute deltas once
        a_cos = [0.0] * n_coords
        shape_keys.key_blocks[a_name].data.foreach_get("co", a_cos)
        a_delta = [a_cos[i] - basis_cos[i] for i in range(n_coords)]

        o_cos = [0.0] * n_coords
        shape_keys.key_blocks[o_name].data.foreach_get("co", o_cos)
        o_delta = [o_cos[i] - basis_cos[i] for i in range(n_coords)]

        ch_cos = [0.0] * n_coords
        shape_keys.key_blocks[ch_name].data.foreach_get("co", ch_cos)
        ch_delta = [ch_cos[i] - basis_cos[i] for i in range(n_coords)]

        overwrite = settings.overwrite_existing
        generated = 0
        skipped = 0

        for viseme_name, (a_w, o_w, ch_w) in VISEME_COEFFICIENTS.items():
            key_exists = viseme_name in sk_block_names

            if key_exists and not overwrite:
                skipped += 1
                pipeline.append_ledger(
                    scene, "visemes", pipeline.OUTCOME_CLEAN,
                    f"Skipped existing key '{viseme_name}'"
                )
                continue

            if key_exists and overwrite:
                # Remove the existing key
                existing_key = shape_keys.key_blocks.get(viseme_name)
                if existing_key is not None:
                    mesh_obj.shape_key_remove(existing_key)

            # Create new shape key
            new_key = mesh_obj.shape_key_add(name=viseme_name, from_mix=False)

            # Compute blended vertex positions
            result_cos = [
                basis_cos[i] + a_w * a_delta[i] + o_w * o_delta[i] + ch_w * ch_delta[i]
                for i in range(n_coords)
            ]
            new_key.data.foreach_set("co", result_cos)
            new_key.value = 0.0

            generated += 1

        msg = f"Generated {generated} vrc.v_ visemes from A/O/CH"
        if skipped:
            msg += f" ({skipped} skipped, enable Overwrite to replace)"

        self.report({'INFO'}, msg)
        pipeline.append_ledger(scene, "visemes", pipeline.OUTCOME_CHANGED, msg)
        pipeline.set_phase_complete(scene, "visemes", pipeline.OUTCOME_CHANGED)

        return {'FINISHED'}


# ── Panel ────────────────────────────────────────────────────────────────────

class CATS_PT_viseme_generator(Panel):
    """Viseme Generator panel in the CATS sidebar tab."""

    bl_label = " "
    bl_idname = "CATS_PT_viseme_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CATS"

    def draw_header(self, context):
        self.layout.label(text=T("Viseme Generator"))

    @classmethod
    def poll(cls, context):
        return False  # Displayed via CATS_PT_visemes in cats_panel.py

    def draw(self, context):
        layout = self.layout
        settings = context.scene.boneforge_cats_viseme_settings

        # Base shape inputs
        col = layout.column(align=True)
        col.label(text=T("Base Mouth Shapes:"))
        col.prop(settings, "a_shape", text=T("A Shape"))
        col.prop(settings, "o_shape", text=T("O Shape"))
        col.prop(settings, "ch_shape", text=T("CH Shape"))

        layout.operator(
            "boneforge.cats_auto_detect_shapes",
            text=T("Auto-Detect Shapes"),
            icon='VIEWZOOM',
        )

        layout.separator()
        layout.prop(settings, "overwrite_existing", toggle=True)

        layout.separator()
        layout.operator(
            "boneforge.cats_generate_visemes",
            text=T("Generate Visemes"),
            icon='SHAPEKEY_DATA',
        )

        layout.separator()
        box = layout.box()
        box.label(text=T("Note: Run Fix Model first for best results."), icon='INFO')


# ── Registration ─────────────────────────────────────────────────────────────

_classes = (
    BF_VisemeGenSettings,
    BF_OT_CATS_AutoDetectShapes,
    BF_OT_CATS_GenerateVisemes,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.boneforge_cats_viseme_settings = bpy.props.PointerProperty(
        type=BF_VisemeGenSettings
    )


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "boneforge_cats_viseme_settings"):
        del bpy.types.Scene.boneforge_cats_viseme_settings
