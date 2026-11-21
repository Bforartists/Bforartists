"""BoneCraft VRChat — Material Atlas Combiner.

Combines multiple materials across meshes into texture atlases, reducing
draw calls and improving VRChat avatar performance rank.

Three-zone layout:
  Zone 1 — Status Dashboard (always visible, auto-updates)
  Zone 2 — Atlas Groups (UIList, auto-classified by render type)
  Zone 3 — Advanced Options (collapsed)

Unanimous additions from design review:
  R — Post-bake authority sentence (rank before/after, outcome language)
  S — Permanent transparency separation note beneath group list
  Q — Accept / Revert binary after bake (replaces fragile undo)
  P — Cancellable per-material bake progress with status bar

Category: VRChat Cats Tools.
"""

import json
import logging
import math
import os
import time
from array import array

import bpy
import bmesh
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty,
    FloatProperty, IntProperty, StringProperty,
)

from boneforge.i18n import T
from bpy.types import Operator, Panel, PropertyGroup, UIList, Menu

from boneforge.core import active_armature
from boneforge.vrchat.cats import pipeline
from boneforge.vrchat.cats.uv_tools import (
    apply_atlas_uv_method,
    atlas_uv_method_items,
    get_uv_method_label,
    method_uses_seed,
    summarize_atlas_uv_result,
)
from boneforge.vrchat.cats.material_atlas_planning import (
    plan_material_slot_groups,
)
from boneforge.vrchat.cats.material_atlas_quality import (
    CHANNEL_PACK_CONVENTION,
    PACKING_PRESETS,
    ROLE_ALPHA,
    ROLE_ALBEDO,
    ROLE_AO,
    ROLE_EMISSION,
    ROLE_METALLIC,
    ROLE_NORMAL,
    ROLE_ROUGHNESS,
    ROLE_UNKNOWN,
    MaterialSource,
    TextureSource,
    build_channel_pack_plan,
    build_multipass_output_plan,
    detect_texture_role,
    diagnose_material,
    diagnose_texture,
    duplicate_texture_key,
    find_duplicate_texture_groups,
    find_shared_material_groups,
    format_quality_debug_report,
    packing_preset_settings,
    resolve_size_preset,
    role_color_space,
    role_label,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Constants — VRChat performance thresholds (mirrors rank.py)
# ─────────────────────────────────────────────────────────────────

_RANK_THRESHOLDS = {"Excellent": 4, "Good": 8, "Medium": 16, "Poor": 32}
_RANK_ORDER = ["Excellent", "Good", "Medium", "Poor"]
# ── MToon / VRoid recognition ────────────────────────────────────────
# The VRM add-on names every MToon texture node "Mtoon1<Slot>Texture.Image".
_MTOON_NODE_PREFIX = "Mtoon1"
_MTOON_EMISSIVE_NODE_PREFIX = "Mtoon1EmissiveTexture"
# The MToon slot VRoid points at the *same* image as base colour. Atlasing it
# packs every albedo twice, so it is skipped when it duplicates base colour.
_MTOON_SHADE_NODE_PREFIX = "Mtoon1ShadeMultiplyTexture"
_MTOON_BASE_COLOR_NODE_PREFIX = "Mtoon1BaseColorTexture"
# VRoid's constant stub images meaning "slot unused".
_VROID_PLACEHOLDER_IMAGE_NAMES = frozenset(
    {"Shader_NoneBlack", "Shader_NoneNormal", "MatcapWarp"}
)
_VROID_PLACEHOLDER_MAX_PX = 8

# ── BoneForge's own atlas output ─────────────────────────────────────
# Generated atlas materials are named "M_bf_atlas_<type>_<res>px" and carry
# these node names. Recognising them keeps a re-atlas from reading back the
# wiring the generator itself wrote.
_ATLAS_MATERIAL_PREFIX = "M_bf_atlas"
_ATLAS_EMISSION_NODE = "Atlas Emission"
_ATLAS_NODE_NAMES = frozenset({"Atlas", "BF_ATLAS_TARGET"})
_SOURCE_POLYGON_ATTRIBUTE = "boneforge_source_polygon"
_SOURCE_OBJECT_ATTRIBUTE = "boneforge_source_object"
_OUTPUT_MATERIAL_TYPE_ITEMS = [
    ("AUTO", "Auto (Group)", "Use each atlas group's detected render type"),
    ("OPAQUE", "Opaque", "Force generated atlas materials to opaque"),
    ("ALPHA_CLIP", "Alpha Clip", "Force generated atlas materials to alpha clip"),
    ("ALPHA_BLEND", "Alpha Blend", "Force generated atlas materials to alpha blend"),
    ("EMISSIVE", "Emissive", "Force generated atlas materials to emissive output"),
]
_OUTPUT_MATERIAL_TYPE_MAP = {
    "OPAQUE": "Opaque",
    "ALPHA_CLIP": "Alpha Clip",
    "ALPHA_BLEND": "Alpha Blend",
    "EMISSIVE": "Emissive",
}
_OUTPUT_MATERIAL_TYPE_LABELS = {
    item_id: label
    for item_id, label, _description in _OUTPUT_MATERIAL_TYPE_ITEMS
}
_OUTPUT_SURFACE_SHADER_ITEMS = [
    ("AUTO", "Auto (Principled)", "Use the generated Principled BSDF surface"),
    ("PRINCIPLED", "Principled BSDF", "Connect a Principled BSDF to the material surface"),
    ("DIFFUSE", "Diffuse BSDF", "Connect a Diffuse BSDF to the material surface"),
    ("EMISSION", "Emission Shader", "Connect an Emission shader to the material surface"),
    ("TRANSPARENT", "Transparent BSDF", "Connect a Transparent BSDF to the material surface"),
]
_OUTPUT_SURFACE_SHADER_LABELS = {
    item_id: label
    for item_id, label, _description in _OUTPUT_SURFACE_SHADER_ITEMS
}

# VRAM cost per atlas (bytes): width * height * 4 channels * 1.33 mip factor
_VRAM_MIP_FACTOR = 1.33

_BACKUP_COLLECTION_PREFIX = "BF_Atlas_Backup_"

_TEXTURE_ROLE_ITEMS = [
    (ROLE_ALBEDO, role_label(ROLE_ALBEDO), "Base color / diffuse source"),
    (ROLE_NORMAL, role_label(ROLE_NORMAL), "Normal map source"),
    (ROLE_EMISSION, role_label(ROLE_EMISSION), "Emission source"),
    (ROLE_METALLIC, role_label(ROLE_METALLIC), "Metallic utility map"),
    (ROLE_ROUGHNESS, role_label(ROLE_ROUGHNESS), "Roughness utility map"),
    (ROLE_AO, role_label(ROLE_AO), "Ambient occlusion utility map"),
    (ROLE_UNKNOWN, role_label(ROLE_UNKNOWN), "Unclassified texture source"),
]

_SIZE_PRESET_ITEMS = [
    ("SOURCE", "Source", "Use the detected source texture dimensions"),
    ("512", "512", "Use 512 x 512"),
    ("1024", "1024", "Use 1024 x 1024"),
    ("2048", "2048", "Use 2048 x 2048"),
    ("4096", "4096", "Use 4096 x 4096"),
    ("CUSTOM", "Custom", "Use the material row width and height"),
]

_PACKING_PRESET_ITEMS = [
    (key, spec["label"], f"Margin {spec['uv_margin']}, padding {spec['padding_pixels']}px")
    for key, spec in PACKING_PRESETS.items()
]

_EXTRA_BAKE_PASSES = {
    ROLE_NORMAL: {"type": "NORMAL", "suffix": "_normal", "colorspace": "Non-Color"},
    ROLE_EMISSION: {"type": "EMIT", "suffix": "_emission", "colorspace": "sRGB"},
    ROLE_ROUGHNESS: {"type": "ROUGHNESS", "suffix": "_roughness", "colorspace": "Non-Color"},
}


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _get_rank(mat_count: int) -> str:
    for rank in _RANK_ORDER:
        if mat_count <= _RANK_THRESHOLDS[rank]:
            return rank
    return "Very Poor"


def _vram_mb(resolution: str) -> float:
    res = int(resolution)
    return round((res * res * 4 * _VRAM_MIP_FACTOR) / (1024 * 1024), 1)


def _material_alpha_mode(mat) -> str:
    """Return "BLEND", "CLIP" or "OPAQUE" across Blender generations.

    ``Material.blend_method`` was removed in Blender 5, so relying on it
    silently classified every transparent material Opaque there — VRoid
    decal layers then baked with no alpha and their invisible regions
    turned into solid patches on the atlas. Checks, in order:

    1. MToon's own alpha mode (authoritative for VRM materials).
    2. Legacy ``blend_method`` (Blender <= 4.x, incl. Bforartists 4).
    3. Blender 5 ``surface_render_method`` ("BLENDED" means alpha).
    4. For non-MToon node materials: an image Alpha output linked into a
       Principled Alpha socket.
    """
    if mat is None:
        return "OPAQUE"

    # Use the VRM add-on's alpha mode when the material actually carries
    # that data. Some imported/instanced MToon materials retain the MToon
    # nodes but lose ``mtoon1``; those must fall through to Blender's
    # authored HASHED/BLEND setting instead of being guessed Opaque.
    if _is_mtoon_material(mat):
        mtoon1 = getattr(
            getattr(mat, "vrm_addon_extension", None), "mtoon1", None
        )
        mode = str(getattr(mtoon1, "alpha_mode", "") or "").upper()
        if mode == "BLEND":
            return "BLEND"
        if mode == "MASK":
            return "CLIP"
        if mode == "OPAQUE":
            return "OPAQUE"

    surface_method = str(getattr(mat, "surface_render_method", "") or "").upper()
    # Modern Blender's deprecated blend_method getter maps DITHERED to
    # HASHED even for a completely opaque Principled shader. It cannot
    # determine transparency on hosts exposing surface_render_method.
    if not surface_method:
        blend = str(getattr(mat, "blend_method", "") or "").upper()
        if blend in ("BLEND", "HASHED"):
            return "BLEND"
        if blend == "CLIP":
            return "CLIP"
    if surface_method == "BLENDED":
        return "BLEND"

    # Node fallback for hand-built materials (no MToon data, no explicit
    # render-method hint): image Alpha wired into Principled Alpha.
    if not _is_mtoon_material(mat) and mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            alpha_input = node.inputs.get("Alpha")
            if alpha_input is not None:
                # Math, ramps and groups can supply alpha just as images can.
                if alpha_input.is_linked or float(alpha_input.default_value) < 0.999:
                    return "BLEND"
    return "OPAQUE"


def _set_material_alpha_output(mat, render_type) -> None:
    """Make *mat* render transparent/clipped/opaque on any Blender version.

    Never raises: each attribute is applied only where the host exposes
    it (setting an unknown attribute on a bpy struct raises).
    """
    legacy = {"Alpha Blend": "BLEND", "Alpha Clip": "CLIP"}.get(render_type, "OPAQUE")
    if hasattr(mat, "blend_method"):
        try:
            mat.blend_method = legacy
        except (AttributeError, TypeError):
            pass
    if hasattr(mat, "surface_render_method"):
        try:
            # Blender 5 has no dedicated CLIP mode; alpha-clip content
            # still needs BLENDED to honour the alpha channel at all.
            mat.surface_render_method = (
                "BLENDED" if render_type in ("Alpha Blend", "Alpha Clip") else "DITHERED"
            )
        except (AttributeError, TypeError):
            pass


def _sampled_alpha_below(image, uv_points, threshold=0.98) -> bool:
    """True when any sampled texel's alpha falls below *threshold*.

    ``uv_points`` are (u, v) pairs already restricted to texels the mesh
    actually uses — sampling the whole image would misread VRoid
    textures, whose *unused* padding regions often carry zero alpha.
    """
    if image is None or int(getattr(image, "channels", 0)) < 4:
        return False
    try:
        width, height = int(image.size[0]), int(image.size[1])
        if width <= 0 or height <= 0:
            return False
        pixels = array("f", [0.0]) * (width * height * 4)
        image.pixels.foreach_get(pixels)
        for u, v in uv_points:
            x = min(width - 1, max(0, int((u % 1.0) * width)))
            y = min(height - 1, max(0, int((v % 1.0) * height)))
            if float(pixels[(y * width + x) * 4 + 3]) < threshold:
                return True
    except (AttributeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("[BoneCraft] alpha sampling failed on %s: %s",
                       getattr(image, "name", "?"), exc)
        # Unreadable pixels: keep the authored transparency rather than
        # guessing it away.
        return True
    return False


def _material_alpha_texture_in_use(obj, slot_index, mat, max_samples=256) -> bool:
    """Does this material's base texture use alpha where the mesh samples it?

    VRoid authors nearly every MToon material as Transparent even when
    its texture alpha is solid white. Baking a whole outfit down the
    alpha path for that flag alone is what turned decals into black
    patches, so an authored-BLEND MToon material is only kept
    transparent when real sub-1 alpha shows up under its own UVs.
    """
    image = _mtoon_base_color_image(mat)
    if image is None:
        return True  # nothing to sample — trust the authored mode
    mesh = getattr(obj, "data", None)
    if mesh is None or not getattr(mesh, "uv_layers", None):
        return True
    uv_layer = mesh.uv_layers.get("UVMap_pre_atlas") or mesh.uv_layers.active
    if uv_layer is None:
        return True

    uv_points = []
    for poly in mesh.polygons:
        if poly.material_index != slot_index:
            continue
        for loop_index in poly.loop_indices:
            uv = uv_layer.data[loop_index].uv
            uv_points.append((float(uv[0]), float(uv[1])))
            break  # one corner per face is plenty at this sample count
        if len(uv_points) >= max_samples:
            break
    if not uv_points:
        return True
    return _sampled_alpha_below(image, uv_points)


def _effective_render_type(obj, slot_index, mat) -> str:
    """Classify like ``_classify_material`` but verify MToon transparency.

    An MToon material authored BLEND/MASK whose base texture alpha is
    effectively solid under its own UVs is treated as Opaque.
    """
    render_type = _classify_material(mat)
    if (
        render_type in ("Alpha Blend", "Alpha Clip")
        and _is_mtoon_material(mat)
        and not _material_alpha_texture_in_use(obj, slot_index, mat)
    ):
        logger.info(
            "[BoneCraft] %s authored %s but texture alpha is solid; "
            "treating as Opaque", getattr(mat, "name", "?"), render_type,
        )
        return "Opaque"
    return render_type


def _classify_material(mat) -> str:
    """Return render-type class for a material."""
    if mat is None:
        return "Opaque"

    alpha_mode = _material_alpha_mode(mat)
    if alpha_mode == "BLEND":
        return "Alpha Blend"
    if alpha_mode == "CLIP":
        return "Alpha Clip"

    # A material BoneForge generated itself. Re-scanning one used to read the
    # emission wiring the generator had just written and conclude "Emissive",
    # which then regenerated the same wiring — the mistake compounded on every
    # re-atlas. Judge it by whether a real emission atlas exists instead.
    if _is_generated_atlas_material(mat):
        return "Emissive" if _atlas_material_has_emission_pass(mat) else "Opaque"

    # MToon (VRM/VRoid) always links the Principled emission socket — that is
    # how it produces flat toon shading rather than lit shading. Judging it by
    # "is the socket linked" marked every VRM material Emissive, which wired
    # the atlas into Emission Color at full strength and blew bright surfaces
    # out to saturated magenta. Judge MToon by what it actually emits.
    if _is_mtoon_material(mat):
        return "Emissive" if _mtoon_actually_emits(mat) else "Opaque"

    # Detect emissive via Principled BSDF emission inputs
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type != 'BSDF_PRINCIPLED':
                continue
            # Blender 4.x uses 'Emission Color'; 3.x uses 'Emission'
            em_color = node.inputs.get("Emission Color") or node.inputs.get("Emission")
            em_strength = node.inputs.get("Emission Strength")
            if em_color and em_color.is_linked:
                # "Linked" alone is not proof of emission. A VRM material
                # rebuilt by hand keeps VRoid's 8x8 black stub wired into
                # Emission, and one such material dragged a whole atlas
                # group to Emissive. Judge the *source* of the link.
                if _emission_link_actually_emits(em_color, em_strength):
                    return "Emissive"
                continue
            if em_color and em_strength:
                col = em_color.default_value
                strength = em_strength.default_value if hasattr(em_strength, "default_value") else 0.0
                if strength > 0.0 and (col[0] > 0.01 or col[1] > 0.01 or col[2] > 0.01):
                    return "Emissive"
    return "Opaque"


def _emission_link_actually_emits(em_color, em_strength) -> bool:
    """True when a linked Emission input carries real emissive content.

    Not emissive when the strength is zero, or when every link traces back
    to an image node holding a VRoid placeholder stub or no image at all.
    A link from anything that is not a plain image node (mix, group, ramp)
    is assumed emissive — this only rules out the provably-dead cases.
    """
    if em_strength is not None and hasattr(em_strength, "default_value"):
        try:
            if float(em_strength.default_value) <= 0.0 and not em_strength.is_linked:
                return False
        except (TypeError, ValueError):
            pass
    for link in em_color.links:
        source = link.from_node
        if getattr(source, "type", "") != "TEX_IMAGE":
            return True
        image = getattr(source, "image", None)
        if image is not None and not _is_vroid_placeholder_image(image):
            return True
    return False


def _is_generated_atlas_material(mat) -> bool:
    """True when *mat* is an atlas material BoneCraft produced."""
    if not mat:
        return False
    if (mat.name or "").startswith(_ATLAS_MATERIAL_PREFIX):
        return True
    if not mat.use_nodes or not mat.node_tree:
        return False
    return any(
        node.name in _ATLAS_NODE_NAMES for node in mat.node_tree.nodes
    )


def _atlas_material_has_emission_pass(mat) -> bool:
    """True when a generated atlas material carries a real emission image.

    The dedicated emission pass writes an "Atlas Emission" node. Base colour
    being routed into Emission does not count — that is the very mistake this
    guards against.
    """
    if not mat or not mat.use_nodes or not mat.node_tree:
        return False
    for node in mat.node_tree.nodes:
        if node.name == _ATLAS_EMISSION_NODE and getattr(node, "image", None):
            return True
    return False


def _image_file_status(image) -> str:
    """Classify where an image's pixels actually live.

    Returns one of:
      ``"packed"``    pixels stored in the .blend — safe.
      ``"ok"``        external file present on disk.
      ``"missing"``   external file GONE — Blender renders this magenta
                      after the next reload. This is the classic cause of
                      a pink avatar that survives revert/undo.
      ``"temp"``      external file exists but lives in a temp directory
                      (the VRM importer unpacks there); the OS will
                      eventually delete it and the image becomes missing.
      ``"none"``      no image / no filepath to check.
    """
    if image is None:
        return "none"
    if getattr(image, "packed_file", None):
        return "packed"
    filepath = getattr(image, "filepath", "") or ""
    if not filepath:
        return "none"
    abs_path = bpy.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return "missing"
    lowered = abs_path.lower().replace("\\", "/")
    if "/temp/" in lowered or "/tmp/" in lowered or lowered.startswith("/tmp"):
        return "temp"
    return "ok"


def _is_mtoon_material(mat) -> bool:
    """True when *mat* is a VRM MToon material.

    Prefers the VRM add-on's own flag; falls back to MToon's node naming so
    detection still works when the add-on is absent (an appended or linked
    .blend, for instance).
    """
    if not mat:
        return False
    ext = getattr(mat, "vrm_addon_extension", None)
    mtoon1 = getattr(ext, "mtoon1", None)
    if mtoon1 is not None and bool(getattr(mtoon1, "enabled", False)):
        return True
    if not mat.use_nodes or not mat.node_tree:
        return False
    return any(
        node.name.startswith(_MTOON_NODE_PREFIX) for node in mat.node_tree.nodes
    )


def _is_vroid_placeholder_image(image) -> bool:
    """True for VRoid's 8x8 'this slot is unused' stub textures.

    VRoid ships ``Shader_NoneBlack`` / ``Shader_NoneNormal`` / ``MatcapWarp``
    as tiny constant images to fill MToon slots the avatar does not use.
    Baking them wastes atlas space and produces duplicate groups.
    """
    if image is None:
        return False
    name = (image.name or "").split(".")[0]
    if name not in _VROID_PLACEHOLDER_IMAGE_NAMES:
        return False
    try:
        width, height = int(image.size[0]), int(image.size[1])
    except (IndexError, TypeError, ValueError):
        return True
    # Guard the name match with the stub's tiny size so a user's real
    # texture that happens to share the name is never dropped.
    return width <= _VROID_PLACEHOLDER_MAX_PX and height <= _VROID_PLACEHOLDER_MAX_PX


def _mtoon_base_color_image(mat):
    """Return the image on MToon's base-colour node, or ``None``."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None
    for node in mat.node_tree.nodes:
        if node.name.startswith(_MTOON_BASE_COLOR_NODE_PREFIX):
            return getattr(node, "image", None)
    return None


def _mtoon_actually_emits(mat) -> bool:
    """True when an MToon material has real emissive content.

    Real means: an emissive texture that is not VRoid's black placeholder,
    or a non-black emissive factor.
    """
    ext = getattr(mat, "vrm_addon_extension", None)
    mtoon1 = getattr(ext, "mtoon1", None)
    if mtoon1 is not None:
        emissive = getattr(mtoon1, "emissive_texture", None)
        image = getattr(getattr(emissive, "index", None), "source", None)
        if image is not None and not _is_vroid_placeholder_image(image):
            return True
        factor = getattr(mtoon1, "emissive_factor", None)
        if factor is not None:
            try:
                if any(float(channel) > 0.01 for channel in factor):
                    return True
            except TypeError:
                pass
        if image is not None:
            return False

    # No add-on data reachable — fall back to the emissive node's image.
    if not mat.use_nodes or not mat.node_tree:
        return False
    for node in mat.node_tree.nodes:
        if not node.name.startswith(_MTOON_EMISSIVE_NODE_PREFIX):
            continue
        image = getattr(node, "image", None)
        if image is not None and not _is_vroid_placeholder_image(image):
            return True
    return False


def _output_material_type_label(settings) -> str:
    key = getattr(settings, "output_material_type", "AUTO") or "AUTO"
    if key == "AUTO":
        return "Auto (atlas group render type)"
    return _OUTPUT_MATERIAL_TYPE_LABELS.get(key, "Auto (atlas group render type)")


def _resolve_output_render_type(group, settings) -> str:
    detected = getattr(group, "render_type", "Opaque") or "Opaque"
    key = getattr(settings, "output_material_type", "AUTO") or "AUTO"
    if key == "AUTO":
        return detected
    return _OUTPUT_MATERIAL_TYPE_MAP.get(key, detected)


def _output_surface_shader_label(settings) -> str:
    key = getattr(settings, "output_surface_shader", "AUTO") or "AUTO"
    return _OUTPUT_SURFACE_SHADER_LABELS.get(key, "Auto (Principled)")


def _resolve_output_surface_shader(settings) -> str:
    key = getattr(settings, "output_surface_shader", "AUTO") or "AUTO"
    if key == "AUTO":
        return "PRINCIPLED"
    if key in _OUTPUT_SURFACE_SHADER_LABELS:
        return key
    return "PRINCIPLED"


def _node_input(node, *names):
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            return socket
    return None


def _node_output(node, *names):
    for name in names:
        socket = node.outputs.get(name)
        if socket is not None:
            return socket
    return None


def _socket_name_is_alpha_like(socket) -> bool:
    name = getattr(socket, "name", "")
    key = "".join(ch.lower() for ch in name if ch.isalnum())
    return "alpha" in key or "opacity" in key or "transparent" in key


def _image_has_alpha(image) -> bool:
    return bool(image and getattr(image, "channels", 0) >= 4)


def _mtoon_base_color_node(mat):
    """Return MToon's base-colour image node (with a real image), or ``None``."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None
    for node in mat.node_tree.nodes:
        if (
            node.type == "TEX_IMAGE"
            and node.name.startswith(_MTOON_BASE_COLOR_NODE_PREFIX)
            and getattr(node, "image", None) is not None
        ):
            return node
    return None


def _alpha_output_feeds_alpha_socket(alpha_output, max_depth=4) -> bool:
    """Follow *alpha_output* downstream through intermediate nodes.

    MToon and imported materials rarely wire image Alpha straight into a
    socket named "Alpha" — it often passes through a multiply/math node
    first. A direct-link name check alone misses those, so walk a few
    hops before giving up.
    """
    frontier = [alpha_output]
    visited_nodes = set()
    for _ in range(max_depth):
        next_frontier = []
        for output in frontier:
            for link in output.links:
                if _socket_name_is_alpha_like(link.to_socket):
                    return True
                to_node = link.to_node
                key = getattr(to_node, "name", None)
                if key is None or key in visited_nodes:
                    continue
                visited_nodes.add(key)
                next_frontier.extend(to_node.outputs)
        if not next_frontier:
            return False
        frontier = next_frontier
    return False


def _find_alpha_source_image_node(mat, *, allow_unlinked_alpha=False):
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None

    # MToon carries alpha in the base-colour texture by spec, but names
    # its node "Mtoon1BaseColorTexture.Image" and routes alpha through
    # its own node group — both name checks below miss it, and the miss
    # used to fall through to a constant-1.0 bake (solid black belts).
    if _is_mtoon_material(mat):
        base_node = _mtoon_base_color_node(mat)
        if base_node is not None and _image_has_alpha(base_node.image):
            return base_node

    image_nodes = [
        node for node in mat.node_tree.nodes
        if node.type == "TEX_IMAGE" and getattr(node, "image", None)
    ]
    for node in image_nodes:
        alpha_output = node.outputs.get("Alpha")
        if not alpha_output or not alpha_output.is_linked:
            continue
        if _alpha_output_feeds_alpha_socket(alpha_output):
            return node

    for node in image_nodes:
        node_label = getattr(node, "label", "") or node.name
        role = detect_texture_role(
            node_label,
            node_name=node.name,
            via_node_type=node.type,
        )
        if role == ROLE_ALPHA:
            return node

    if allow_unlinked_alpha:
        for node in image_nodes:
            if _image_has_alpha(node.image):
                return node

    return None


def _principled_alpha_input(mat):
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node.inputs.get("Alpha")
    return None


def _material_alpha_is_linked(mat) -> bool:
    """True when Principled Alpha is texture-driven rather than constant."""
    alpha_input = _principled_alpha_input(mat)
    return bool(alpha_input is not None and alpha_input.is_linked)


def _material_alpha_default(mat) -> float:
    """Constant alpha on the Principled Alpha socket, else 1.0.

    Only meaningful when the socket is UNLINKED. A linked socket keeps a
    stale ``default_value`` (usually 1.0), and trusting it is what baked
    texture-driven cutouts — belts, decals — down to solid opaque tiles.
    Callers that need the linked case use ``_material_alpha_is_linked``.
    """
    alpha_input = _principled_alpha_input(mat)
    if (
        alpha_input is not None
        and not alpha_input.is_linked
        and hasattr(alpha_input, "default_value")
    ):
        return float(alpha_input.default_value)
    return 1.0


def _material_uses_alpha(mat) -> bool:
    if not mat:
        return False
    # Texture-driven alpha: the stale default_value must not veto it.
    if _material_alpha_is_linked(mat):
        return True
    # Version-portable alpha check (blend_method is gone in Blender 5).
    alpha_like = _material_alpha_mode(mat) != "OPAQUE"
    if _find_alpha_source_image_node(mat, allow_unlinked_alpha=alpha_like) is not None:
        return True
    return _material_alpha_default(mat) < 0.999


def _group_needs_alpha_atlas(joined, output_render_type) -> bool:
    if output_render_type in ("Alpha Blend", "Alpha Clip"):
        return True
    return any(_material_uses_alpha(mat) for mat in joined.data.materials if mat)


def _copy_source_image_node_settings(source_node, target_node):
    for attr in ("extension", "interpolation", "projection"):
        if hasattr(source_node, attr) and hasattr(target_node, attr):
            try:
                setattr(target_node, attr, getattr(source_node, attr))
            except Exception:
                pass


def _find_albedo_source_image_node(mat):
    """Return the image node that supplies a material's base colour."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None

    if _is_mtoon_material(mat):
        node = _mtoon_base_color_node(mat)
        if (
            node is not None
            and getattr(node, "image", None) is not None
            and not _is_vroid_placeholder_image(node.image)
        ):
            return node

    for node, image in _iter_texture_nodes(mat):
        if image is None or _is_vroid_placeholder_image(image):
            continue
        role = _detect_texture_node_role(node)
        if role == ROLE_ALBEDO:
            return node
        node_label = getattr(node, "label", "") or node.name
        role = detect_texture_role(
            node_label, node_name=node.name, via_node_type=node.type
        )
        if role == ROLE_ALBEDO:
            return node
    return None


def _material_base_color_default(mat):
    """Return a portable constant base colour when no albedo image exists."""
    if mat and mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            color_input = node.inputs.get("Base Color")
            if color_input is not None and hasattr(color_input, "default_value"):
                return tuple(float(value) for value in color_input.default_value)
    color = getattr(mat, "diffuse_color", None) if mat else None
    if color is not None:
        return tuple(float(value) for value in color)
    return (1.0, 1.0, 1.0, 1.0)


def _build_principled_input_bake_material(source_mat, input_name, prefix):
    """Bake the actual connected input graph instead of guessing an image.

    MToon retains its dedicated Cycles-safe texture fallback. For a normal
    Principled surface, copying the graph preserves tint, math, ramps, groups,
    image settings and authored UV mapping without editing the source material.
    """
    if not source_mat or not source_mat.use_nodes or not source_mat.node_tree:
        return None
    if _is_mtoon_material(source_mat):
        return None
    output = next((node for node in source_mat.node_tree.nodes
                   if node.type == "OUTPUT_MATERIAL" and node.is_active_output), None)
    surface = output.inputs.get("Surface") if output else None
    if surface is None or not surface.is_linked:
        return None
    shader = surface.links[0].from_node
    while shader.type == "REROUTE" and shader.inputs[0].is_linked:
        shader = shader.inputs[0].links[0].from_node
    if shader.type != "BSDF_PRINCIPLED" or shader.inputs.get(input_name) is None:
        return None

    temp = source_mat.copy()
    temp.name = f"{prefix}{source_mat.name}"
    nodes, links = temp.node_tree.nodes, temp.node_tree.links
    value = nodes[shader.name].inputs[input_name]
    output = nodes.new("ShaderNodeOutputMaterial")
    output.is_active_output = True
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    if value.is_linked:
        links.new(value.links[0].from_socket, emission.inputs["Color"])
    elif input_name == "Alpha":
        alpha = float(value.default_value)
        emission.inputs["Color"].default_value = (alpha, alpha, alpha, 1.0)
    else:
        emission.inputs["Color"].default_value = value.default_value
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return temp


def _build_albedo_bake_material(source_mat):
    """Build a Cycles-safe base-colour graph for one source material."""
    evaluated = _build_principled_input_bake_material(source_mat, "Base Color", "__BF_ALBEDO_BAKE_")
    if evaluated is not None:
        return evaluated
    temp = bpy.data.materials.new(
        f"__BF_ALBEDO_BAKE_{source_mat.name if source_mat else 'blank'}"
    )
    temp.use_nodes = True
    nodes = temp.node_tree.nodes
    links = temp.node_tree.links
    nodes.clear()

    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (260, 0)
    emission_node = nodes.new("ShaderNodeEmission")
    emission_node.location = (40, 0)
    strength_input = emission_node.inputs.get("Strength")
    if strength_input is not None and hasattr(strength_input, "default_value"):
        strength_input.default_value = 1.0

    color_input = emission_node.inputs.get("Color")
    source_node = _find_albedo_source_image_node(source_mat)
    if source_node is not None and color_input is not None:
        uv_node = nodes.new("ShaderNodeUVMap")
        uv_node.uv_map = "UVMap_pre_atlas"
        uv_node.location = (-520, 0)
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.name = "Albedo Source"
        tex_node.image = source_node.image
        tex_node.location = (-260, 0)
        _copy_source_image_node_settings(source_node, tex_node)
        links.new(uv_node.outputs["UV"], tex_node.inputs["Vector"])
        links.new(tex_node.outputs["Color"], color_input)
    elif color_input is not None:
        color = _material_base_color_default(source_mat)
        color_input.default_value = color
        logger.warning(
            "[BoneCraft Atlas] %s: no albedo texture found; baking constant base colour",
            getattr(source_mat, "name", "<none>"),
        )

    links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])
    return temp


def _bake_albedo_to_atlas(context, joined, atlas_img, settings):
    """Bake base colour through temporary graphs, then restore source materials."""
    original_materials = [mat for mat in joined.data.materials]
    temp_materials = []
    try:
        for index, source_mat in enumerate(original_materials):
            temp_mat = _build_albedo_bake_material(source_mat)
            temp_materials.append(temp_mat)
            joined.data.materials[index] = temp_mat

            target = temp_mat.node_tree.nodes.new("ShaderNodeTexImage")
            target.name = "BF_ALBEDO_TARGET"
            target.image = atlas_img
            target.location = (-260, -260)
            for node in temp_mat.node_tree.nodes:
                node.select = False
            target.select = True
            temp_mat.node_tree.nodes.active = target

        context.view_layer.objects.active = joined
        _deselect_all_objects_directly(context.view_layer)
        joined.select_set(True)
        _run_with_view3d_context(
            context,
            bpy.ops.object.bake,
            "Bake atlas albedo",
            type="EMIT",
            use_selected_to_active=False,
            margin=settings.atlas_padding_pixels,
            use_clear=True,
        )
    finally:
        for index, mat in enumerate(original_materials):
            joined.data.materials[index] = mat
        for temp_mat in temp_materials:
            if temp_mat.name in bpy.data.materials:
                bpy.data.materials.remove(temp_mat)

def _fallback_alpha_image_node(mat):
    """Last-resort alpha carrier: a 4-channel, non-placeholder image node.

    Baking a constant while the material still owns an alpha-capable
    texture is what turned transparent decals into solid blocks on the
    atlas. Prefer the albedo/base-colour node; fall back to any real
    4-channel image.
    """
    if not mat or not mat.use_nodes or not mat.node_tree:
        return None
    best = None
    for node in mat.node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        image = getattr(node, "image", None)
        if (
            image is None
            or not _image_has_alpha(image)
            or _is_vroid_placeholder_image(image)
        ):
            continue
        node_label = getattr(node, "label", "") or node.name
        role = detect_texture_role(
            node_label, node_name=node.name, via_node_type=node.type
        )
        if role == ROLE_ALBEDO:
            return node
        if best is None:
            best = node
    return best


def _build_alpha_bake_material(source_mat):
    evaluated = _build_principled_input_bake_material(source_mat, "Alpha", "__BF_ALPHA_BAKE_")
    if evaluated is not None:
        return evaluated
    temp = bpy.data.materials.new(f"__BF_ALPHA_BAKE_{source_mat.name if source_mat else 'opaque'}")
    temp.use_nodes = True
    nodes = temp.node_tree.nodes
    links = temp.node_tree.links
    nodes.clear()

    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (260, 0)
    emission_node = nodes.new("ShaderNodeEmission")
    emission_node.location = (40, 0)
    strength_input = emission_node.inputs.get("Strength")
    if strength_input is not None and hasattr(strength_input, "default_value"):
        strength_input.default_value = 1.0

    alpha_like = _material_uses_alpha(source_mat)
    source_node = _find_alpha_source_image_node(source_mat, allow_unlinked_alpha=alpha_like)
    if source_node is None:
        # No explicit alpha wiring found — before flattening the tile to
        # a constant, use any real 4-channel texture the material owns.
        source_node = _fallback_alpha_image_node(source_mat)
    color_input = emission_node.inputs.get("Color")
    if source_node is not None and color_input is not None:
        uv_node = nodes.new("ShaderNodeUVMap")
        uv_node.uv_map = "UVMap_pre_atlas"
        uv_node.location = (-520, 0)
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.name = "Alpha Source"
        tex_node.image = source_node.image
        tex_node.location = (-260, 0)
        _copy_source_image_node_settings(source_node, tex_node)
        links.new(uv_node.outputs["UV"], tex_node.inputs["Vector"])
        alpha_output = tex_node.outputs.get("Alpha") or tex_node.outputs.get("Color")
        if alpha_output is not None:
            links.new(alpha_output, color_input)
    elif color_input is not None:
        alpha_value = max(0.0, min(1.0, _material_alpha_default(source_mat)))
        color_input.default_value = (alpha_value, alpha_value, alpha_value, 1.0)
        logger.warning(
            "[BoneCraft Atlas] %s: no alpha texture found anywhere; baking "
            "constant alpha %.2f for its tile",
            getattr(source_mat, "name", "<none>"), alpha_value,
        )

    links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])
    return temp


def _copy_mask_luminance_to_image_alpha(mask_img, target_img):
    pixel_count = int(target_img.size[0]) * int(target_img.size[1]) * 4
    if pixel_count <= 0:
        return
    mask_pixels = array("f", [0.0]) * pixel_count
    target_pixels = array("f", [0.0]) * pixel_count
    mask_img.pixels.foreach_get(mask_pixels)
    target_img.pixels.foreach_get(target_pixels)
    for index in range(0, pixel_count, 4):
        alpha = max(mask_pixels[index], mask_pixels[index + 1], mask_pixels[index + 2])
        target_pixels[index + 3] = max(0.0, min(1.0, alpha))
    target_img.pixels.foreach_set(target_pixels)
    target_img.update()


def _describe_alpha_source(source_mat) -> str:
    """Say where a material's baked alpha comes from, for diagnostics."""
    if source_mat is None:
        return "opaque (no material)"
    alpha_like = _material_uses_alpha(source_mat)
    node = _find_alpha_source_image_node(
        source_mat, allow_unlinked_alpha=alpha_like
    )
    if node is None:
        node = _fallback_alpha_image_node(source_mat)
    if node is not None and getattr(node, "image", None) is not None:
        linked = any(
            output.name == "Alpha" and output.is_linked
            for output in node.outputs
        )
        return "image '%s' alpha (%s)" % (
            node.image.name, "linked" if linked else "unlinked fallback",
        )
    return "constant %.2f" % _material_alpha_default(source_mat)


def _bake_alpha_mask_to_atlas(context, joined, atlas_img, settings, atlas_name, res):
    """Bake per-face alpha into the atlas. Returns per-material source info."""
    alpha_name = f"{atlas_name}_alpha_mask"
    if alpha_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[alpha_name])
    alpha_img = bpy.data.images.new(alpha_name, width=res, height=res, alpha=True)
    alpha_img.colorspace_settings.name = "Non-Color"

    original_materials = [mat for mat in joined.data.materials]
    alpha_sources = [
        _describe_alpha_source(source_mat) for source_mat in original_materials
    ]
    temp_materials = []
    try:
        for index, source_mat in enumerate(original_materials):
            temp_mat = _build_alpha_bake_material(source_mat)
            temp_materials.append(temp_mat)
            joined.data.materials[index] = temp_mat

            target = temp_mat.node_tree.nodes.new("ShaderNodeTexImage")
            target.name = "BF_ALPHA_TARGET"
            target.image = alpha_img
            target.location = (-260, -260)
            for node in temp_mat.node_tree.nodes:
                node.select = False
            target.select = True
            temp_mat.node_tree.nodes.active = target

        context.view_layer.objects.active = joined
        _deselect_all_objects_directly(context.view_layer)
        joined.select_set(True)
        _run_with_view3d_context(
            context,
            bpy.ops.object.bake,
            "Bake atlas alpha mask",
            type="EMIT",
            use_selected_to_active=False,
            margin=settings.atlas_padding_pixels,
            use_clear=True,
        )
        _copy_mask_luminance_to_image_alpha(alpha_img, atlas_img)
    finally:
        for index, mat in enumerate(original_materials):
            joined.data.materials[index] = mat
        for temp_mat in temp_materials:
            if temp_mat.name in bpy.data.materials:
                bpy.data.materials.remove(temp_mat)
        if alpha_img.name in bpy.data.images:
            bpy.data.images.remove(alpha_img)
    return alpha_sources


def _collect_atlas_tile_stats(joined, atlas_img, alpha_sources=None):
    """Sample each material's atlas tile after baking.

    Only meaningful for the SOURCE_PRESERVE layout, where every material
    owns one grid tile. Returns a list of per-material dicts with mean
    RGB and mean/min alpha, so a tile that baked invisible (alpha ~0) or
    blank-opaque names itself in the debug report instead of having to
    be eyeballed in the Image Editor.
    """
    mesh = getattr(joined, "data", None)
    if mesh is None or atlas_img is None:
        return None
    try:
        width, height = int(atlas_img.size[0]), int(atlas_img.size[1])
        if width <= 0 or height <= 0:
            return None
        pixels = array("f", [0.0]) * (width * height * 4)
        atlas_img.pixels.foreach_get(pixels)
    except (AttributeError, TypeError, ValueError) as exc:
        logger.warning("[BoneCraft] tile stats unavailable: %s", exc)
        return None

    material_indices = sorted(
        {poly.material_index for poly in mesh.polygons if poly.loop_indices}
    )
    if not material_indices:
        return None
    grid_size = max(1, math.ceil(math.sqrt(len(material_indices))))
    tile_size = 1.0 / grid_size

    stats = []
    samples = 12
    for slot, material_index in enumerate(material_indices):
        col, row = slot % grid_size, slot // grid_size
        sum_r = sum_g = sum_b = sum_a = 0.0
        min_a = 1.0
        count = 0
        # Sample the inner 50% of the tile so padding/margins don't skew it.
        for sy in range(samples):
            for sx in range(samples):
                u = (col + 0.25 + 0.5 * (sx + 0.5) / samples) * tile_size
                v = (row + 0.25 + 0.5 * (sy + 0.5) / samples) * tile_size
                x = min(width - 1, int(u * width))
                y = min(height - 1, int(v * height))
                base = (y * width + x) * 4
                sum_r += pixels[base]
                sum_g += pixels[base + 1]
                sum_b += pixels[base + 2]
                alpha = pixels[base + 3]
                sum_a += alpha
                min_a = min(min_a, alpha)
                count += 1
        mat = (
            mesh.materials[material_index]
            if material_index < len(mesh.materials) else None
        )
        entry = {
            "material": mat.name if mat else f"<slot {material_index}>",
            "tile": f"{col},{row}",
            "mean_rgb": [round(sum_r / count, 3), round(sum_g / count, 3),
                         round(sum_b / count, 3)],
            "mean_alpha": round(sum_a / count, 3),
            "min_alpha": round(min_a, 3),
        }
        if alpha_sources is not None and material_index < len(alpha_sources):
            entry["alpha_source"] = alpha_sources[material_index]
        stats.append(entry)
    return stats


def _target_meshes(context, settings=None):
    """Return meshes for the current atlas scope."""
    scope = getattr(settings, "target_scope", "ACTIVE_ARMATURE") if settings else "ACTIVE_ARMATURE"

    if scope == "SELECTED_MESHES":
        return [o for o in context.selected_objects if o.type == "MESH"]

    if scope == "VISIBLE_SCENE":
        return [
            o for o in context.scene.objects
            if o.type == "MESH" and o.visible_get()
        ]

    arm = active_armature(context)
    if arm:
        return [c for c in arm.children if c.type == "MESH"]

    active = context.view_layer.objects.active
    if active is not None and active.type == "MESH":
        return [active]

    return [
        o for o in context.scene.objects
        if o.type == "MESH" and o.visible_get()
    ]


def _find_view3d_context_override(context):
    """Return a VIEW_3D override for bpy operators that need UI context."""
    wm = getattr(context, "window_manager", None)
    if wm is None:
        return None
    for window in wm.windows:
        screen = getattr(window, "screen", None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for region in area.regions:
                if region.type == "WINDOW":
                    return {
                        "window": window,
                        "screen": screen,
                        "area": area,
                        "region": region,
                    }
    return None


def _run_with_view3d_context(context, op_call, stage: str, **kwargs):
    """Run an operator with a VIEW_3D override when one is available."""
    override = _find_view3d_context_override(context)
    try:
        if override:
            with context.temp_override(**override):
                return op_call(**kwargs)
        return op_call(**kwargs)
    except Exception as exc:
        raise RuntimeError(f"{stage} failed: {exc}") from exc


def _ensure_object_mode(context, stage: str):
    """Leave edit/pose mode before object-level atlas operations."""
    obj = getattr(context, "object", None)
    if obj is not None and getattr(obj, "mode", "OBJECT") != "OBJECT":
        _run_with_view3d_context(context, bpy.ops.object.mode_set, stage, mode="OBJECT")


def _deselect_all_objects_directly(view_layer):
    """Deselect objects without bpy.ops.object.select_all poll requirements."""
    for obj in view_layer.objects:
        try:
            obj.select_set(False)
        except RuntimeError:
            pass


def _iter_material_slots(obj):
    """Yield object material slots as (object, slot_index, material)."""
    if obj is None or getattr(obj, "type", None) != "MESH":
        return
    for slot_index, mat in enumerate(obj.data.materials):
        yield obj, slot_index, mat


def _iter_texture_nodes(mat):
    """Yield image texture nodes and image datablocks in a material."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            yield node, node.image


def _iter_texture_images(mat):
    """Yield image datablocks used by texture nodes in a material."""
    for _node, image in _iter_texture_nodes(mat):
        yield image


def _detect_texture_node_role(node) -> str:
    """Infer semantic role for an image texture node from its outgoing links."""
    if node is None:
        return ROLE_UNKNOWN
    for output in node.outputs:
        for link in output.links:
            to_node = link.to_node
            role = detect_texture_role(
                getattr(link.to_socket, "name", ""),
                node_name=getattr(to_node, "name", ""),
                output_name=getattr(output, "name", ""),
                via_node_type=getattr(to_node, "type", ""),
            )
            if role != ROLE_UNKNOWN:
                return role
            for mid_output in getattr(to_node, "outputs", []):
                for mid_link in mid_output.links:
                    role = detect_texture_role(
                        getattr(mid_link.to_socket, "name", ""),
                        node_name=getattr(mid_link.to_node, "name", ""),
                        output_name=getattr(mid_output, "name", ""),
                        via_node_type=getattr(to_node, "type", ""),
                    )
                    if role != ROLE_UNKNOWN:
                        return role
    return ROLE_UNKNOWN


def _material_shader_type(mat) -> str:
    if not mat:
        return "EMPTY_SLOT"
    if not mat.use_nodes or not mat.node_tree:
        return "NO_NODE_TREE"
    for node in mat.node_tree.nodes:
        if node.type != "OUTPUT_MATERIAL":
            continue
        surface = node.inputs.get("Surface")
        if surface and surface.is_linked:
            source = surface.links[0].from_node
            return getattr(source, "type", "") or getattr(source, "bl_idname", "")
    for node in mat.node_tree.nodes:
        if node.type.startswith("BSDF") or node.type in {"EMISSION", "GROUP"}:
            return node.type
    return "UNKNOWN_SHADER"


def _material_emission_strength(mat) -> float:
    if not mat or not mat.use_nodes or not mat.node_tree:
        return 0.0
    for node in mat.node_tree.nodes:
        if node.type != "BSDF_PRINCIPLED":
            continue
        strength = node.inputs.get("Emission Strength")
        if strength and hasattr(strength, "default_value"):
            return float(strength.default_value or 0.0)
    return 0.0


def _texture_quality_source(mat_name, node, image) -> TextureSource:
    return TextureSource(
        material_name=mat_name or "",
        node_name=node.name if node else "",
        image_name=image.name if image else "",
        image_path=bpy.path.abspath(image.filepath) if image and image.filepath else "",
        width=int(image.size[0]) if image else 0,
        height=int(image.size[1]) if image else 0,
        colorspace=(
            image.colorspace_settings.name
            if image and image.colorspace_settings
            else ""
        ),
        packed=bool(image and image.packed_file),
        missing=image is None,
        socket_name="",
        output_name="",
        via_node_type="",
        role=_detect_texture_node_role(node),
        enabled=image is not None,
    )


def _material_quality_source(obj, slot_index, mat) -> MaterialSource:
    mat_name = mat.name if mat else "<empty>"
    textures = tuple(
        _texture_quality_source(mat_name, node, image)
        for node, image in _iter_texture_nodes(mat)
    )
    return MaterialSource(
        material_name=mat_name,
        object_name=obj.name if obj else "",
        slot_index=slot_index,
        shader_type=_material_shader_type(mat),
        use_nodes=bool(mat and mat.use_nodes),
        has_node_tree=bool(mat and mat.node_tree),
        textures=textures,
        alpha_mode=getattr(mat, "alpha_method", "") if mat else "",
        blend_method=getattr(mat, "blend_method", "") if mat else "",
        emission_strength=_material_emission_strength(mat),
    )


def _group_texture_quality_sources(group):
    return [
        TextureSource(
            material_name=item.material_name,
            node_name=item.node_name,
            image_name="" if item.missing else item.image_name,
            image_path=item.image_path,
            width=item.width,
            height=item.height,
            colorspace=item.colorspace,
            packed=item.packed,
            missing=item.missing,
            role=item.role,
            enabled=item.enabled,
        )
        for item in getattr(group, "textures", [])
    ]


def _material_source_size(group, material_item):
    for tex in getattr(group, "textures", []):
        if (
            tex.object_name == material_item.object_name
            and tex.slot_index == material_item.slot_index
            and tex.material_name == material_item.material_name
            and tex.width > 0
            and tex.height > 0
        ):
            return tex.width, tex.height
    return 0, 0


def _settings_enabled_passes(settings):
    passes = []
    if settings.bake_albedo:
        passes.append(ROLE_ALBEDO)
    if settings.bake_normal:
        passes.append(ROLE_NORMAL)
    if settings.bake_emission:
        passes.append(ROLE_EMISSION)
    if getattr(settings, "bake_metallic", False):
        passes.append(ROLE_METALLIC)
    if settings.bake_roughness:
        passes.append(ROLE_ROUGHNESS)
    return passes


def _material_key(object_name, slot_index, material_name):
    return (object_name, int(slot_index), material_name or "")


def _texture_key(object_name, slot_index, material_name, node_name, image_name):
    return (
        object_name,
        int(slot_index),
        material_name or "",
        node_name or "",
        image_name or "",
    )


def _group_detected_material_count(group) -> int:
    if hasattr(group, "materials") and len(group.materials):
        return len(group.materials)
    return int(getattr(group, "mat_count", 0))


def _group_enabled_material_count(group) -> int:
    if hasattr(group, "materials") and len(group.materials):
        return sum(1 for item in group.materials if item.enabled)
    return int(getattr(group, "mat_count", 0))


def _group_enabled_texture_count(group) -> int:
    if hasattr(group, "textures") and len(group.textures):
        return sum(1 for item in group.textures if item.enabled)
    return 0


def _enabled_material_keys(group):
    if not hasattr(group, "materials") or not len(group.materials):
        return None
    return {
        _material_key(item.object_name, item.slot_index, item.material_name)
        for item in group.materials
        if item.enabled
    }


def _enabled_texture_keys(group):
    if not hasattr(group, "textures") or not len(group.textures):
        return None
    return {
        _texture_key(
            item.object_name,
            item.slot_index,
            item.material_name,
            item.node_name,
            item.image_name,
        )
        for item in group.textures
        if item.enabled and not item.missing
    }


def _enabled_slots_by_object(group):
    result = {}
    enabled_keys = _enabled_material_keys(group)
    if enabled_keys is None:
        for mesh_item in group.meshes:
            obj = bpy.data.objects.get(mesh_item.object_name)
            if obj and obj.type == "MESH":
                result[obj.name] = set(range(len(obj.data.materials)))
        return result

    for item in group.materials:
        if not item.enabled:
            continue
        result.setdefault(item.object_name, set()).add(int(item.slot_index))
    return result


def _detected_slots_by_object(group):
    result = {}
    if hasattr(group, "materials") and len(group.materials):
        for item in group.materials:
            result.setdefault(item.object_name, set()).add(int(item.slot_index))
        return result
    for mesh_item in group.meshes:
        obj = bpy.data.objects.get(mesh_item.object_name)
        if obj and obj.type == "MESH":
            result[obj.name] = set(range(len(obj.data.materials)))
    return result


def _populate_group_sources(
    group,
    objs,
    allowed_slot_keys=None,
    default_material_enabled=True,
):
    """Populate selectable material and texture rows for selected material slots."""
    group.materials.clear()
    group.textures.clear()
    material_pairs = []
    texture_pairs = []

    for obj in objs:
        for _obj, slot_index, mat in _iter_material_slots(obj):
            slot_key = (obj.name, int(slot_index))
            if allowed_slot_keys is not None and slot_key not in allowed_slot_keys:
                continue
            mat_name = mat.name if mat else "<empty>"
            tex_nodes = list(_iter_texture_nodes(mat))
            mat_source = _material_quality_source(obj, slot_index, mat)
            mat_report = diagnose_material(mat_source)
            color_spaces = {
                image.colorspace_settings.name
                for _node, image in tex_nodes
                if image and image.colorspace_settings
            }

            mat_item = group.materials.add()
            mat_item.enabled = bool(default_material_enabled)
            mat_item.object_name = obj.name
            mat_item.slot_index = slot_index
            mat_item.material_name = mat_name
            mat_item.render_type = _effective_render_type(obj, slot_index, mat)
            mat_item.texture_count = len(tex_nodes)
            mat_item.has_no_images = len(tex_nodes) == 0
            # An empty MToon slot is a declaration, not a fault — only flag
            # a genuinely missing image on non-MToon materials.
            mat_item.has_missing_image = (
                not _is_mtoon_material(mat)
                and any(image is None for _node, image in tex_nodes)
            )
            mat_item.has_mixed_colorspace = len(color_spaces) > 1
            mat_item.diagnostic_status = mat_report["status"]
            mat_item.diagnostic_warnings = "; ".join(mat_report["warnings"])
            mat_item.duplicate_group = ""
            mat_item.fallback_size = 512
            material_pairs.append((len(group.materials) - 1, mat_source))

            is_mtoon = _is_mtoon_material(mat)
            base_color_image = _mtoon_base_color_image(mat) if is_mtoon else None

            for node, image in tex_nodes:
                # MToon declares every slot it supports, so an avatar that
                # uses none of the optional ones carries a stack of empty
                # nodes. They are normal, not errors — skip them silently
                # rather than reporting one failure per unused slot.
                if is_mtoon and image is None:
                    continue

                tex_source = _texture_quality_source(mat_name, node, image)
                tex_report = diagnose_texture(tex_source)
                tex_item = group.textures.add()
                tex_item.enabled = bool(default_material_enabled and image is not None)
                if _is_vroid_placeholder_image(image):
                    # An 8x8 "unused slot" stub. Keep the row visible so the
                    # report stays honest, but never bake it.
                    tex_item.enabled = False
                elif (
                    is_mtoon
                    and base_color_image is not None
                    and node.name.startswith(_MTOON_SHADE_NODE_PREFIX)
                    and image is base_color_image
                ):
                    # VRoid points shade-multiply at the base colour image,
                    # so atlasing it packs the same texture twice. Left on
                    # when it genuinely differs.
                    tex_item.enabled = False
                tex_item.object_name = obj.name
                tex_item.slot_index = slot_index
                tex_item.material_name = mat_name
                tex_item.node_name = node.name
                tex_item.image_name = image.name if image else "<missing>"
                tex_item.image_path = bpy.path.abspath(image.filepath) if image and image.filepath else ""
                tex_item.width = int(image.size[0]) if image else 0
                tex_item.height = int(image.size[1]) if image else 0
                tex_item.colorspace = (
                    image.colorspace_settings.name
                    if image and image.colorspace_settings
                    else ""
                )
                tex_item.packed = bool(image and image.packed_file)
                tex_item.missing = image is None
                tex_item.role = tex_source.role
                tex_item.role_label = role_label(tex_source.role)
                tex_item.expected_colorspace = str(tex_report["colorspace_expected"])
                tex_item.diagnostic_status = str(tex_report["status"])
                tex_item.diagnostic_warnings = "; ".join(tex_report["warnings"])
                tex_item.duplicate_group = ""
                texture_pairs.append((len(group.textures) - 1, tex_source))

    texture_duplicates = find_duplicate_texture_groups(
        [source for _item_index, source in texture_pairs]
    )
    for duplicate_index, duplicate in enumerate(texture_duplicates, start=1):
        key = duplicate["key"]
        marker = f"T{duplicate_index}"
        for item_index, source in texture_pairs:
            if duplicate_texture_key(source) == key:
                group.textures[item_index].duplicate_group = marker

    material_duplicates = find_shared_material_groups(
        [source for _item_index, source in material_pairs]
    )
    for duplicate_index, duplicate in enumerate(material_duplicates, start=1):
        marker = f"M{duplicate_index}"
        names = set(duplicate["materials"])
        for item_index, _source in material_pairs:
            item = group.materials[item_index]
            if item.material_name in names:
                group.materials[item_index].duplicate_group = marker

    group.duplicate_count = len(texture_duplicates) + len(material_duplicates)
    group.unknown_texture_roles = sum(
        1 for item in group.textures if item.role == ROLE_UNKNOWN
    )
    material_warnings = sum(1 for item in group.materials if item.diagnostic_warnings)
    texture_warnings = sum(1 for item in group.textures if item.diagnostic_warnings)
    group.quality_summary = (
        f"{material_warnings} material warning(s), "
        f"{texture_warnings} texture warning(s), "
        f"{group.duplicate_count} duplicate/shared group(s), "
        f"{group.unknown_texture_roles} unknown role(s)"
    )
    if material_warnings or texture_warnings or group.duplicate_count or group.unknown_texture_roles:
        group.has_warnings = True


def _copy_material_slots(mesh):
    for mat_index, mat in enumerate(mesh.materials):
        if mat is not None:
            mesh.materials[mat_index] = mat.copy()


def _stamp_source_polygon_indices(mesh, source_object_index):
    """Attach stable source polygon indices before a bake partition is cut."""
    existing = mesh.attributes.get(_SOURCE_POLYGON_ATTRIBUTE)
    if existing is not None:
        mesh.attributes.remove(existing)
    attribute = mesh.attributes.new(
        name=_SOURCE_POLYGON_ATTRIBUTE,
        type="INT",
        domain="FACE",
    )
    attribute.data.foreach_set("value", list(range(len(mesh.polygons))))
    object_attribute = mesh.attributes.get(_SOURCE_OBJECT_ATTRIBUTE)
    if object_attribute is not None:
        mesh.attributes.remove(object_attribute)
    object_attribute = mesh.attributes.new(
        name=_SOURCE_OBJECT_ATTRIBUTE,
        type="INT",
        domain="FACE",
    )
    object_attribute.data.foreach_set(
        "value", [source_object_index] * len(mesh.polygons)
    )
    return attribute


def _remove_faces_by_material_slots(obj, slots_to_remove):
    """Remove faces assigned to material slots in *slots_to_remove*."""
    if not slots_to_remove:
        return len(obj.data.polygons) > 0
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        faces = [face for face in bm.faces if face.material_index in slots_to_remove]
        if faces:
            bmesh.ops.delete(bm, geom=faces, context="FACES")
            bm.to_mesh(obj.data)
            obj.data.update()
    finally:
        bm.free()
    return len(obj.data.polygons) > 0


def _disconnect_disabled_texture_nodes(mat, object_name, slot_index, material_name, enabled_texture_keys):
    if enabled_texture_keys is None or not mat or not mat.use_nodes or not mat.node_tree:
        return
    links = mat.node_tree.links
    for node, image in _iter_texture_nodes(mat):
        key = _texture_key(
            object_name,
            slot_index,
            material_name,
            node.name,
            image.name if image else "<missing>",
        )
        if key in enabled_texture_keys:
            continue
        for output in node.outputs:
            for link in list(output.links):
                links.remove(link)


def _ensure_source_uv_node(nodes, uv_map_name, location):
    uv_node = nodes.get("BF_ATLAS_SOURCE_UV")
    if uv_node is None:
        uv_node = nodes.new("ShaderNodeUVMap")
        uv_node.name = "BF_ATLAS_SOURCE_UV"
        uv_node.label = "BoneCraft Source UV"
        uv_node.location = location
    uv_node.uv_map = uv_map_name
    return uv_node


def _uses_uv_map_node(node):
    return (
        getattr(node, "type", "") == "UVMAP"
        or getattr(node, "bl_idname", "") == "ShaderNodeUVMap"
    )


def _preserve_explicit_uv_map_node(node, uv_map_name):
    if not _uses_uv_map_node(node):
        return False
    if not getattr(node, "uv_map", ""):
        node.uv_map = uv_map_name
    return True


def _route_vector_socket_to_uv(links, vector_input, uv_node):
    if vector_input is None:
        return False

    if not vector_input.is_linked:
        links.new(uv_node.outputs["UV"], vector_input)
        return True

    for link in list(vector_input.links):
        if _preserve_explicit_uv_map_node(link.from_node, uv_node.uv_map):
            return True
        upstream_input = getattr(link.from_node, "inputs", {}).get("Vector")
        if upstream_input is None:
            continue
        for old_link in list(upstream_input.links):
            if _preserve_explicit_uv_map_node(old_link.from_node, uv_node.uv_map):
                return True
        for old_link in list(upstream_input.links):
            links.remove(old_link)
        links.new(uv_node.outputs["UV"], upstream_input)
        return True

    for link in list(vector_input.links):
        links.remove(link)
    links.new(uv_node.outputs["UV"], vector_input)
    return True


def _route_source_image_nodes_to_uv(mat, uv_map_name):
    """Make copied source textures sample the original UV while baking to atlas_uv."""
    if not mat or not mat.use_nodes or not mat.node_tree:
        return 0

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    routed = 0
    for node, image in _iter_texture_nodes(mat):
        if node.name == "BF_ATLAS_TARGET" or image is None:
            continue
        vector_input = node.inputs.get("Vector")
        uv_node = _ensure_source_uv_node(
            nodes,
            uv_map_name,
            (node.location.x - 240, node.location.y),
        )
        if _route_vector_socket_to_uv(links, vector_input, uv_node):
            routed += 1
    return routed


def _compact_material_slots(mesh):
    """Remove unused slots while preserving every polygon's material."""
    used_indices = sorted({
        int(poly.material_index)
        for poly in mesh.polygons
        if 0 <= int(poly.material_index) < len(mesh.materials)
    })
    if not used_indices:
        mesh.materials.clear()
        mesh.update()
        return 0
    materials = [mesh.materials[index] for index in used_indices]
    index_map = {old_index: new_index for new_index, old_index in enumerate(used_indices)}
    for poly in mesh.polygons:
        poly.material_index = index_map[int(poly.material_index)]
    mesh.materials.clear()
    for material in materials:
        mesh.materials.append(material)
    mesh.update()
    return len(materials)

def _assign_single_atlas_material(mesh, atlas_mat):
    mesh.materials.clear()
    mesh.materials.append(atlas_mat)
    for poly in mesh.polygons:
        poly.material_index = 0
    mesh.update()


def _validate_atlas_mesh(obj, atlas_mat):
    mesh = obj.data
    errors = []
    atlas_index = next(
        (i for i, uv in enumerate(mesh.uv_layers) if uv.name == "atlas_uv"),
        None,
    )
    if atlas_index is None:
        errors.append("missing atlas_uv map")
    elif not getattr(mesh.uv_layers[atlas_index], "active_render", False):
        errors.append("atlas_uv is not the active render UV")
    if not mesh.materials or mesh.materials[0] != atlas_mat:
        errors.append("atlas material is not slot 0")
    stale_faces = sum(1 for poly in mesh.polygons if poly.material_index != 0)
    if stale_faces:
        errors.append(f"{stale_faces} face(s) still point to old material slots")
    if errors:
        raise RuntimeError("Atlas validation failed: " + "; ".join(errors))


def _mirror_active_uv_to_atlas(mesh):
    """Keep preserved faces on their authored UVs in the rebuilt atlas mesh."""
    source_uv = mesh.uv_layers.active
    if source_uv is not None and source_uv.name != "UVMap_pre_atlas":
        source_uv.name = "UVMap_pre_atlas"
    atlas_uv = mesh.uv_layers.get("atlas_uv")
    if atlas_uv is None:
        atlas_uv = mesh.uv_layers.new(name="atlas_uv")
    if source_uv is None:
        # Smart Pack can bake color-only meshes without authored UVs. The
        # rebuilt full mesh still needs a layer to receive those baked loops.
        return _activate_atlas_uv(mesh)
    for source_loop, atlas_loop in zip(source_uv.data, atlas_uv.data):
        atlas_loop.uv = source_loop.uv
    return _activate_atlas_uv(mesh)


def _activate_atlas_uv(mesh):
    for index, uv in enumerate(mesh.uv_layers):
        is_atlas = uv.name == "atlas_uv"
        uv.active_render = is_atlas
        if is_atlas:
            try:
                mesh.uv_layers.active_index = index
            except Exception:
                uv.active = True
    return "atlas_uv" in mesh.uv_layers


def _prepare_atlas_uv_for_export(mesh, keep_source_uv_maps):
    if "atlas_uv" not in mesh.uv_layers:
        return False
    if not keep_source_uv_maps:
        for uv in list(mesh.uv_layers):
            if uv.name != "atlas_uv":
                mesh.uv_layers.remove(uv)
    return _activate_atlas_uv(mesh)


def _cleanup_transient_atlas_objects():
    """Remove internal atlas work objects left by failed bake stages."""
    for obj in list(bpy.data.objects):
        if (
            obj.name.startswith("__BF_ATLAS_")
            or obj.name.startswith("__BF_ATLAS_WORK_")
            or obj.name.startswith("ATLAS_KEEP_")
        ):
            bpy.data.objects.remove(obj, do_unlink=True)


def _build_debug_report(meshes, settings) -> str:
    """Build a copyable diagnostic report for mixed material/texture atlasing."""
    lines = [
        "BoneCraft CATS Material Atlas Debug Report",
        f"Scope: {getattr(settings, 'target_scope', 'ACTIVE_ARMATURE')}",
        f"Meshes scanned: {len(meshes)}",
        f"Output: {settings.output_format} -> {bpy.path.abspath(settings.output_path)}",
        f"Output material type: {_output_material_type_label(settings)}",
        f"Output surface: {_output_surface_shader_label(settings)}",
        f"UV method: {get_uv_method_label(getattr(settings, 'pack_method', 'SOURCE_PRESERVE'))}",
        f"UV margin: {getattr(settings, 'uv_margin', 0.02)}",
        f"Packing preset: {packing_preset_settings(getattr(settings, 'packing_preset', 'SAFE_DEFAULT'))['label']}",
        f"Bake padding: {getattr(settings, 'atlas_padding_pixels', 4)} px",
        "",
    ]
    if method_uses_seed(getattr(settings, "pack_method", "")):
        lines.insert(5, f"UV seed: {getattr(settings, 'uv_random_seed', 1337)}")
        lines.insert(6, f"UV rotation step: {getattr(settings, 'uv_rotation_step', '90')}")

    if not meshes:
        lines.append("ERROR: No mesh objects were found for the current scope.")
        return "\n".join(lines)

    seen_images = {}
    total_materials = 0
    problem_count = 0
    quality_materials = []
    quality_textures = []

    for obj in meshes:
        mesh = obj.data
        uv_state = "OK" if mesh.uv_layers else "MISSING"
        if not mesh.uv_layers:
            problem_count += 1
        lines.append(f"Mesh: {obj.name} | materials={len(mesh.materials)} | uv={uv_state}")

        # Post-bake tile diagnostics, stored on the atlas result object.
        stats_raw = obj.get("boneforge_atlas_tile_stats")
        if stats_raw:
            try:
                tile_stats = json.loads(stats_raw)
            except (json.JSONDecodeError, TypeError):
                tile_stats = None
            if tile_stats:
                lines.append("  Last bake — per-material tile stats:")
                for entry in tile_stats:
                    rgb = entry.get("mean_rgb", ["?", "?", "?"])
                    verdicts = []
                    if entry.get("mean_alpha", 1.0) < 0.05:
                        verdicts.append("TILE IS INVISIBLE (alpha ~0)")
                    elif entry.get("min_alpha", 1.0) >= 0.999:
                        verdicts.append("fully opaque")
                    if all(isinstance(c, (int, float)) and c > 0.93 for c in rgb):
                        verdicts.append("baked nearly WHITE")
                    if all(isinstance(c, (int, float)) and c < 0.02 for c in rgb):
                        verdicts.append("baked nearly BLACK")
                    lines.append(
                        "    tile %s | %s | rgb=%s mean_a=%s min_a=%s | src=%s%s" % (
                            entry.get("tile", "?"),
                            entry.get("material", "?"),
                            rgb,
                            entry.get("mean_alpha", "?"),
                            entry.get("min_alpha", "?"),
                            entry.get("alpha_source", "n/a"),
                            ("  [" + "; ".join(verdicts) + "]") if verdicts else "",
                        )
                    )

        for slot_index, mat in enumerate(mesh.materials):
            total_materials += 1
            if mat is None:
                problem_count += 1
                lines.append(f"  [{slot_index}] ERROR: empty material slot")
                continue

            render_type = _effective_render_type(obj, slot_index, mat)
            authored_type = _classify_material(mat)
            if authored_type != render_type:
                lines.append(
                    f"  [{slot_index}] {mat.name} | authored {authored_type} "
                    "but texture alpha is solid under its UVs — treated as "
                    f"{render_type}"
                )
            mat_source = _material_quality_source(obj, slot_index, mat)
            mat_report = diagnose_material(mat_source)
            quality_materials.append(mat_source)
            if not mat.use_nodes or not mat.node_tree:
                problem_count += 1
                lines.append(
                    f"  [{slot_index}] {mat.name} | {render_type} | "
                    f"{mat_report['status']} | WARNING: material has no node tree"
                )
                continue

            tex_nodes = list(_iter_texture_nodes(mat))
            if not tex_nodes:
                problem_count += 1
                lines.append(
                    f"  [{slot_index}] {mat.name} | {render_type} | "
                    f"{mat_report['status']} | WARNING: no image texture nodes"
                )
                continue

            is_mtoon = _is_mtoon_material(mat)
            skipped_empty_slots = 0

            for node, img in tex_nodes:
                if is_mtoon and img is None:
                    # Unused MToon slot — expected, not a problem.
                    skipped_empty_slots += 1
                    continue
                tex_source = _texture_quality_source(mat.name, node, img)
                tex_report = diagnose_texture(tex_source)
                quality_textures.append(tex_source)
                if img is None:
                    problem_count += 1
                    lines.append(f"  [{slot_index}] {mat.name} | ERROR: image node has no image")
                    continue
                key = img.name
                seen_images[key] = img
                packed = "packed" if img.packed_file else "external"
                path = bpy.path.abspath(img.filepath) if img.filepath else "<unsaved or generated>"
                note = ""
                if _is_vroid_placeholder_image(img):
                    note = "  [VRoid unused-slot stub — not baked]"
                file_status = _image_file_status(img)
                if file_status == "missing":
                    problem_count += 1
                    note += "  [ERROR: file MISSING on disk — renders magenta]"
                elif file_status == "temp":
                    note += (
                        "  [WARNING: lives in a temp folder — pack or move "
                        "it before the OS deletes it]"
                    )
                lines.append(
                    f"  [{slot_index}] {mat.name} | {render_type} | "
                    f"role={tex_report['role_label']} | "
                    f"image={img.name} {img.size[0]}x{img.size[1]} {packed} | {path}{note}"
                )

            if skipped_empty_slots:
                lines.append(
                    f"  [{slot_index}] {mat.name} | MToon: "
                    f"{skipped_empty_slots} unused texture slot(s) skipped"
                )

    sizes = sorted({(img.size[0], img.size[1]) for img in seen_images.values() if img})
    color_spaces = sorted({
        img.colorspace_settings.name for img in seen_images.values()
        if img and img.colorspace_settings
    })

    lines.extend([
        "",
        f"Materials scanned: {total_materials}",
        f"Images scanned: {len(seen_images)}",
        f"Image sizes: {', '.join(f'{w}x{h}' for w, h in sizes) if sizes else 'none'}",
        f"Color spaces: {', '.join(color_spaces) if color_spaces else 'none'}",
        f"Warnings/errors: {problem_count}",
    ])

    if len(sizes) > 1:
        lines.append("NOTE: Mixed source image sizes are supported, but small images may soften in a large atlas.")
    if len(color_spaces) > 1:
        lines.append("NOTE: Mixed color spaces detected. Verify the baked atlas visually before Accept.")

    # ── Scene-wide image health ──────────────────────────────────
    # The per-mesh section above only covers the current scope. A magenta
    # object OUTSIDE the selection (hair, halo, accessories) still means a
    # broken image somewhere in the file, so sweep every image datablock —
    # and say which materials/objects use the broken ones.
    missing_rows = []
    temp_rows = []
    for img in bpy.data.images:
        status = _image_file_status(img)
        if status not in ("missing", "temp"):
            continue
        users = []
        for scan_mat in bpy.data.materials:
            if not scan_mat.use_nodes or not scan_mat.node_tree:
                continue
            if any(
                getattr(n, "image", None) is img
                for n in scan_mat.node_tree.nodes
                if n.type == "TEX_IMAGE"
            ):
                users.append(scan_mat.name)
        row = (
            f"- {img.name} | {bpy.path.abspath(img.filepath) if img.filepath else '<no path>'}"
            f" | used by: {', '.join(users) if users else '<no material>'}"
        )
        (missing_rows if status == "missing" else temp_rows).append(row)
    if missing_rows or temp_rows:
        lines.append("")
        lines.append("Scene-wide image health (all images in this .blend, any selection):")
        if missing_rows:
            lines.append(
                f"MISSING FILES ({len(missing_rows)}) — these render MAGENTA; "
                "relink or replace them:"
            )
            lines.extend(missing_rows)
        if temp_rows:
            lines.append(
                f"TEMP-FOLDER FILES ({len(temp_rows)}) — will go missing when "
                "the OS clears temp; use File > External Data > Pack Resources:"
            )
            lines.extend(temp_rows)

    if quality_materials or quality_textures:
        lines.extend([
            "",
            format_quality_debug_report(
                quality_materials,
                quality_textures,
                size_preset="SOURCE",
                packing_preset=getattr(settings, "packing_preset", "SAFE_DEFAULT"),
                enabled_passes=_settings_enabled_passes(settings),
                channel_pack=getattr(settings, "channel_pack_orm", False),
            ),
        ])

    if getattr(settings, "atlas_groups", None):
        lines.extend(["", "Selectable row state:"])
        for group in settings.atlas_groups:
            lines.append(
                f"- {group.name}: enabled={group.enabled}, "
                f"summary={getattr(group, 'quality_summary', '') or 'none'}"
            )
            for mat_item in getattr(group, "materials", []):
                state = "on" if mat_item.enabled else "off"
                duplicate = f", duplicate={mat_item.duplicate_group}" if mat_item.duplicate_group else ""
                lines.append(
                    f"  material {state}: {mat_item.object_name}[{mat_item.slot_index}] "
                    f"{mat_item.material_name} | {mat_item.diagnostic_status}{duplicate}"
                )
            for tex_item in getattr(group, "textures", []):
                state = "on" if tex_item.enabled else "off"
                duplicate = f", duplicate={tex_item.duplicate_group}" if tex_item.duplicate_group else ""
                lines.append(
                    f"  texture {state}: {tex_item.material_name}/{tex_item.node_name} "
                    f"{tex_item.image_name} | role={role_label(tex_item.role)}{duplicate}"
                )

    return "\n".join(lines)


def _store_debug_report(context, meshes, settings):
    if not getattr(settings, "debug_enabled", True):
        return
    settings.last_debug_report = _build_debug_report(meshes, settings)


def _has_high_emission(obj) -> bool:
    """True if any material has emission strength > 1.0."""
    for mat in obj.data.materials:
        if not mat or not mat.use_nodes or not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type != 'BSDF_PRINCIPLED':
                continue
            em_strength = node.inputs.get("Emission Strength")
            if em_strength and hasattr(em_strength, "default_value"):
                if em_strength.default_value > 1.0:
                    return True
    return False


def _has_overlapping_uvs(obj) -> bool:
    """
    Heuristic UV overlap check.
    Detects meshes where UV coordinates suggest intentional mirrored sharing
    (multiple polygons mapping to the same 0-1 UV space from different faces).
    Uses bmesh for a lightweight island count check.
    """
    if obj.type != 'MESH' or not obj.data.uv_layers:
        return False
    try:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            bm.free()
            return False

        # Collect all UV positions (rounded to avoid float noise)
        uv_set = set()
        duplicates = 0
        for face in bm.faces:
            face_uvs = tuple(
                (round(loop[uv_layer].uv[0], 3), round(loop[uv_layer].uv[1], 3))
                for loop in face.loops
            )
            for uv in face_uvs:
                if uv in uv_set:
                    duplicates += 1
                uv_set.add(uv)
        bm.free()

        # Heuristic: if >10% of UV verts are duplicates, likely intentional overlap
        if len(uv_set) > 0 and (duplicates / len(uv_set)) > 0.1:
            return True
    except Exception as e:
        logger.warning(f"[BoneCraft Atlas] UV overlap check failed on {obj.name}: {e}")
    return False


def _projected_mat_count(settings) -> int:
    """Count projected atlas material count from current group config."""
    total = 0
    for group in settings.atlas_groups:
        detected = _group_detected_material_count(group)
        enabled = _group_enabled_material_count(group)
        if not group.enabled or detected == 0:
            total += detected
            continue
        if enabled >= 2:
            total += len(_enabled_slots_by_object(group))
            total += max(0, detected - enabled)
        else:
            total += detected
    return total


def _build_status_sentence(settings) -> str:
    """D-Shadow Inheritance Protocol: declarative sentence for Zone 1."""
    groups = [
        g for g in settings.atlas_groups
        if g.enabled and _group_enabled_material_count(g) >= 2
    ]
    total_before = settings.total_mats_before
    total_after = _projected_mat_count(settings)
    rank_after = _get_rank(total_after)

    if not settings.atlas_groups:
        if total_before > 0:
            return (f"{total_before} materials detected — "
                    f"press Analyze to auto-group")
        return "Press Analyze to detect materials"

    if not groups:
        if not any(group.enabled for group in settings.atlas_groups):
            return (f"{total_before} materials detected — "
                    f"check a box under Atlas Groups to enable baking")
        return (f"{total_before} materials detected — "
                f"check 2+ materials in an enabled Atlas Group")

    shape_key_note = ""
    for group in settings.atlas_groups:
        for item in group.meshes:
            if item.has_shape_keys:
                shape_key_note = " and shape keys"
                break

    enabled_mats = sum(_group_enabled_material_count(g) for g in groups)
    return (
        f"{enabled_mats} materials across {len(groups)} groups — "
        f"estimated {rank_after} atlas — "
        f"bake will preserve UV maps by name{shape_key_note}"
    )


def _will_not_change_sentence(settings) -> str:
    """Second persistent line: what the bake guarantees not to touch."""
    guarantees = ["object hierarchy", "UV maps (saved as 'UVMap_pre_atlas')"]

    if True:
        guarantees.append("shape keys / blendshapes")
    if settings.preserve_originals:
        guarantees.append("originals (backup collection active)")

    return "Will not change: " + ", ".join(guarantees)


# ─────────────────────────────────────────────────────────────────
# Property Groups
# ─────────────────────────────────────────────────────────────────

class BF_AtlasMeshItem(PropertyGroup):
    """One mesh entry inside an atlas group."""
    object_name: StringProperty(name="Object")
    render_type: StringProperty(name="Render Type", default="Opaque")
    mat_count: IntProperty(name="Material Count", default=0)
    has_shape_keys: BoolProperty(name="Has Shape Keys", default=False)
    has_overlapping_uvs: BoolProperty(name="Overlapping UVs", default=False)
    has_high_emission: BoolProperty(name="Emission > 1.0", default=False)


class BF_AtlasMaterialItem(PropertyGroup):
    """Selectable material source row inside an atlas group."""
    enabled: BoolProperty(name="Include", default=True)
    object_name: StringProperty(name="Object")
    slot_index: IntProperty(name="Slot", default=0)
    material_name: StringProperty(name="Material")
    render_type: StringProperty(name="Render Type", default="Opaque")
    texture_count: IntProperty(name="Texture Count", default=0)
    has_no_images: BoolProperty(name="No Images", default=False)
    has_missing_image: BoolProperty(name="Missing Image", default=False)
    has_mixed_colorspace: BoolProperty(name="Mixed Color Space", default=False)
    diagnostic_status: StringProperty(name="Diagnostic Status", default="")
    diagnostic_warnings: StringProperty(name="Warnings", default="")
    duplicate_group: StringProperty(name="Duplicate Group", default="")
    size_override: BoolProperty(name="Override Size", default=False)
    size_preset: EnumProperty(
        name="Size",
        items=_SIZE_PRESET_ITEMS,
        default="SOURCE",
    )
    target_width: IntProperty(name="Width", default=1024, min=16, max=8192)
    target_height: IntProperty(name="Height", default=1024, min=16, max=8192)
    fallback_size: IntProperty(name="Fallback", default=512, min=16, max=8192)


class BF_AtlasTextureItem(PropertyGroup):
    """Selectable image texture source row inside an atlas group."""
    enabled: BoolProperty(name="Include", default=True)
    object_name: StringProperty(name="Object")
    slot_index: IntProperty(name="Slot", default=0)
    material_name: StringProperty(name="Material")
    node_name: StringProperty(name="Node")
    image_name: StringProperty(name="Image")
    image_path: StringProperty(name="Path")
    width: IntProperty(name="Width", default=0)
    height: IntProperty(name="Height", default=0)
    colorspace: StringProperty(name="Color Space")
    packed: BoolProperty(name="Packed", default=False)
    missing: BoolProperty(name="Missing", default=False)
    role: EnumProperty(
        name="Role",
        items=_TEXTURE_ROLE_ITEMS,
        default=ROLE_UNKNOWN,
    )
    role_label: StringProperty(name="Role Label", default="")
    expected_colorspace: StringProperty(name="Expected Color Space", default="")
    diagnostic_status: StringProperty(name="Diagnostic Status", default="")
    diagnostic_warnings: StringProperty(name="Warnings", default="")
    duplicate_group: StringProperty(name="Duplicate Group", default="")


class BF_AtlasGroup(PropertyGroup):
    """One atlas group (bakes into a single texture atlas)."""
    name: StringProperty(name="Group Name", default="Group")
    enabled: BoolProperty(name="Enabled", default=True)
    meshes: CollectionProperty(type=BF_AtlasMeshItem)
    materials: CollectionProperty(type=BF_AtlasMaterialItem)
    textures: CollectionProperty(type=BF_AtlasTextureItem)
    active_material_index: IntProperty(name="Active Material", default=0)
    active_texture_index: IntProperty(name="Active Texture", default=0)
    render_type: StringProperty(name="Render Type", default="Opaque")
    preserve_reason: StringProperty(name="Preserve Reason", default="")
    resolution: EnumProperty(
        name="Resolution",
        items=[
            ("1024", "1024", "1024 × 1024 px — 5.3 MB VRAM"),
            ("2048", "2048", "2048 × 2048 px — 21.3 MB VRAM"),
            ("4096", "4096", "4096 × 4096 px — 85.3 MB VRAM"),
        ],
        default="2048",
    )
    mat_count: IntProperty(name="Material Count", default=0)
    has_warnings: BoolProperty(name="Has Warnings", default=False)
    warn_overlap: BoolProperty(name="UV Overlap Warning", default=False)
    warn_emission: BoolProperty(name="High Emission Warning", default=False)
    quality_summary: StringProperty(name="Quality Summary", default="")
    duplicate_count: IntProperty(name="Duplicate Count", default=0)
    unknown_texture_roles: IntProperty(name="Unknown Texture Roles", default=0)


class BF_AtlasSettings(PropertyGroup):
    """Scene-level atlas combiner settings."""

    # Group list
    atlas_groups: CollectionProperty(type=BF_AtlasGroup)
    active_group_index: IntProperty(name="Active Group", default=0)

    # Status (populated by Analyze)
    total_mats_before: IntProperty(default=0)
    rank_before: StringProperty(default="")
    last_bake_result: StringProperty(default="")
    last_debug_report: StringProperty(default="")

    # Backup state
    has_backup: BoolProperty(default=False)
    backup_collection_name: StringProperty(default="")

    # Friendly defaults
    target_scope: EnumProperty(
        name="Target",
        description="Which meshes are included when Analyze or Smart Combine runs",
        items=[
            ("ACTIVE_ARMATURE", "Active Avatar", "Use mesh children of the active armature, or the active mesh if no armature is active"),
            ("SELECTED_MESHES", "Selected Meshes", "Use only selected mesh objects"),
            ("VISIBLE_SCENE", "Visible Scene", "Use every visible mesh in the scene"),
        ],
        default="ACTIVE_ARMATURE",
    )
    auto_analyze_before_bake: BoolProperty(
        name="Auto Analyze",
        description="Automatically rebuild atlas groups before one-click baking",
        default=True,
    )
    debug_enabled: BoolProperty(
        name="Debug Report",
        description="Build a copyable report of source meshes, material slots, texture images, UV state, image sizes, and color spaces",
        default=True,
    )
    color_fallback_size: IntProperty(
        name="Color Fallback Size",
        description="Atlas allocation size used for color-only materials with no image textures",
        default=512,
        min=16,
        max=8192,
    )
    packing_preset: EnumProperty(
        name="Packing Preset",
        description="Quality preset for atlas padding and bleed behavior",
        items=_PACKING_PRESET_ITEMS,
        default="SAFE_DEFAULT",
    )
    atlas_padding_pixels: IntProperty(
        name="Bake Padding",
        description="Pixel margin used by Blender's bake operation",
        default=4,
        min=0,
        max=128,
    )
    pixel_art_no_bleed: BoolProperty(
        name="Pixel Art No-Bleed",
        description="Keep padding conservative for crisp nearest-neighbor textures",
        default=False,
    )
    preserve_island_orientation: BoolProperty(
        name="Preserve Island Orientation",
        description="Prefer UV methods that avoid unnecessary island rotation where supported",
        default=True,
    )
    keep_source_uv_maps: BoolProperty(
        name="Keep Source UV Maps",
        description=(
            "Keep UVMap_pre_atlas on the output mesh. Off by default so "
            "atlas_uv becomes UV0 for FBX/Unity/VRChat export"
        ),
        default=False,
    )

    # Advanced options
    preserve_originals: BoolProperty(
        name="Preserve Backup Duplicate",
        description=(
            "Create and keep a visible pre-atlas duplicate for Revert. "
            "Turn off to remove originals after atlasing without a backup duplicate."
        ),
        default=True,
    )
    uv_margin: FloatProperty(
        name="UV Margin",
        description=(
            "Space between UV islands in the atlas. Higher values prevent texture "
            "bleeding at edges but reduce usable pixel space. 0.02 is safe for most avatars"
        ),
        default=0.02,
        min=0.001,
        max=0.1,
        precision=3,
    )
    pack_method: EnumProperty(
        name="UV Method",
        description="How the atlas work mesh is unwrapped and packed before baking",
        items=atlas_uv_method_items(include_advanced=True),
        default="SOURCE_PRESERVE",
    )
    uv_random_seed: IntProperty(
        name="UV Seed",
        description="Deterministic seed used by seeded UV variation methods",
        default=1337,
        min=0,
        max=999999,
    )
    uv_rotation_step: EnumProperty(
        name="Rotation Step",
        description="B4Artists advanced control for seeded atlas island rotation",
        items=[
            ("90", "90 deg", "Stable right-angle variation"),
            ("45", "45 deg", "More varied diagonal rotations"),
            ("180", "180 deg", "Flip-only variation"),
        ],
        default="90",
    )
    bake_albedo: BoolProperty(name="Albedo (Color)", default=True)
    bake_normal: BoolProperty(
        name="Normal Map",
        description="Bake a separate normal atlas using the host bake engine",
        default=False,
    )
    bake_emission: BoolProperty(
        name="Emission",
        description="Bake a separate emission atlas when the material graph provides emission data",
        default=False,
    )
    bake_metallic: BoolProperty(
        name="Metallic",
        description="Planned utility-map pass. Currently preflight-blocked unless channel packing can safely provide a fallback",
        default=False,
    )
    bake_roughness: BoolProperty(
        name="Roughness",
        description="Bake a separate roughness atlas when the host bake engine supports the pass",
        default=False,
    )
    channel_pack_orm: BoolProperty(
        name="Pack ORM Channels",
        description="Opt-in channel packing: R=Metallic, G=Roughness, B=AO/black, A=Alpha/opaque",
        default=False,
    )
    allow_unknown_channel_pack_roles: BoolProperty(
        name="Allow Unknown Roles",
        description="Permit channel-packing preflight even when some enabled texture rows are still Unknown",
        default=False,
    )
    output_format: EnumProperty(
        name="Output Format",
        items=[
            ("PNG", "PNG", "Standard format — emission values > 1.0 will clamp"),
            ("TGA", "TGA", "TGA format — emission values > 1.0 will clamp"),
            ("EXR", "EXR", "HDR format — preserves emission values > 1.0"),
        ],
        default="PNG",
    )
    output_material_type: EnumProperty(
        name="Output Material Type",
        description="Choose the generated atlas material render type. Auto matches each atlas group.",
        items=_OUTPUT_MATERIAL_TYPE_ITEMS,
        default="AUTO",
    )
    output_surface_shader: EnumProperty(
        name="Output Surface",
        description="Choose the shader node connected to the generated material output surface. Auto keeps Principled BSDF.",
        items=_OUTPUT_SURFACE_SHADER_ITEMS,
        default="AUTO",
    )
    output_path: StringProperty(
        name="Output Path",
        description="Folder where atlas textures are saved",
        default="//textures/atlas/",
        subtype="DIR_PATH",
    )
    show_source_details: BoolProperty(
        name="Source Details",
        description="Show mesh information, selected material sizing and texture roles",
        default=False,
    )
    show_advanced: BoolProperty(name="Advanced Options", default=False)


# ─────────────────────────────────────────────────────────────────
# UIList
# ─────────────────────────────────────────────────────────────────

class BF_UL_VRC_AtlasGroups(UIList):
    """Displays atlas groups with render-type badge, material count, resolution."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        # Enable toggle
        row.prop(item, "enabled", text="", emboss=False,
                 icon="CHECKBOX_HLT" if item.enabled else "CHECKBOX_DEHLT")

        # Group name (editable inline)
        sub = row.row(align=True)
        sub.enabled = item.enabled
        sub.prop(item, "name", text="", emboss=False)

        # Render type badge icon
        type_icons = {
            "Opaque": "MATERIAL",
            "Alpha Clip": "MOD_MASK",
            "Alpha Blend": "LIGHT_AREA",
            "Emissive": "LIGHT_SUN",
        }
        badge_icon = type_icons.get(item.render_type, "QUESTION")
        sub.label(text=item.render_type, icon=badge_icon)

        # Material count → 1
        mat_label = f"  {item.mat_count}→1" if item.mat_count >= 2 else f"  {item.mat_count} mat"
        sub.label(text=mat_label)

        # Resolution
        sub.prop(item, "resolution", text="")

        # Warning indicator
        if item.has_warnings:
            row.label(text="", icon="ERROR")


# ─────────────────────────────────────────────────────────────────
# Operators
# ─────────────────────────────────────────────────────────────────

class BF_UL_VRC_AtlasMaterials(UIList):
    """Displays selectable material slots found during Analyze."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(
            item,
            "enabled",
            text="",
            emboss=False,
            icon="CHECKBOX_HLT" if item.enabled else "CHECKBOX_DEHLT",
        )
        sub = row.row(align=True)
        sub.enabled = item.enabled
        warn_icon = "MATERIAL_DATA"
        if item.diagnostic_status == "unsupported_shader" or item.has_missing_image:
            warn_icon = "ERROR"
        elif item.diagnostic_warnings or item.duplicate_group or item.has_no_images or item.has_mixed_colorspace:
            warn_icon = "INFO"
        label = f"{item.object_name}[{item.slot_index}]  {item.material_name}"
        sub.label(text=label, icon=warn_icon)
        sub.label(text=item.render_type)
        sub.label(text=f"{item.texture_count} tex")
        if item.duplicate_group:
            sub.label(text=item.duplicate_group)


class BF_UL_VRC_AtlasTextures(UIList):
    """Displays selectable texture image nodes found during Analyze."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(
            item,
            "enabled",
            text="",
            emboss=False,
            icon="CHECKBOX_HLT" if item.enabled else "CHECKBOX_DEHLT",
        )
        sub = row.row(align=True)
        sub.enabled = item.enabled and not item.missing
        image_icon = "ERROR" if item.missing else "IMAGE_DATA"
        if not item.missing and item.diagnostic_warnings:
            image_icon = "INFO"
        size = f"{item.width}x{item.height}" if item.width and item.height else "missing"
        packed = "packed" if item.packed else "external"
        label = f"{item.material_name} / {item.node_name}: {item.image_name}"
        sub.label(text=label, icon=image_icon)
        sub.label(text=role_label(item.role))
        sub.label(text=size)
        sub.label(text=item.colorspace or packed)
        if item.duplicate_group:
            sub.label(text=item.duplicate_group)


class BF_OT_VRC_AtlasSelectSources(Operator):
    """Check or uncheck sources in the active atlas group; missing textures stay excluded"""
    bl_idname = "boneforge.vrc_atlas_select_sources"
    bl_label = "Select Atlas Sources"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        name="Source List",
        description="The source list in the active atlas group to change",
        items=[("MATERIALS", "Materials", "Material slots"),
               ("TEXTURES", "Textures", "Available texture images")],
        options={"HIDDEN", "SKIP_SAVE"},
    )
    select: BoolProperty(
        name="Select",
        description="Check all available sources, or uncheck the entire list",
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "boneforge_atlas_settings", None)
        if settings is None or not 0 <= settings.active_group_index < len(settings.atlas_groups):
            cls.poll_message_set("Analyze materials and choose an atlas group first")
            return False
        if settings.has_backup:
            cls.poll_message_set("Accept or Revert the current atlas preview first")
            return False
        return True

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        group = settings.atlas_groups[settings.active_group_index]
        items = group.materials if self.target == "MATERIALS" else group.textures
        for item in items:
            item.enabled = self.select and not getattr(item, "missing", False)
        return {"FINISHED"}


def _draw_source_selection(layout, target):
    row = layout.row(align=True)
    for label, select in (("Select All", True), ("Deselect All", False)):
        op = row.operator("boneforge.vrc_atlas_select_sources", text=T(label))
        op.target = target
        op.select = select


class BONEFORGE_MT_atlas_selection(Menu):
    bl_label = "Atlas Source Selection"
    bl_idname = "BONEFORGE_MT_atlas_selection"

    def draw(self, context):
        for label, target in (("Materials to Combine", "MATERIALS"), ("Texture Images", "TEXTURES")):
            self.layout.label(text=T(label))
            _draw_source_selection(self.layout, target)


def _atlas_selection_menu(self, context):
    self.layout.menu(BONEFORGE_MT_atlas_selection.bl_idname, text=T("Atlas Source Selection"))


class BF_OT_VRC_AtlasAnalyze(Operator):
    """Analyze scene materials and auto-group by render type"""
    bl_idname = "boneforge.vrc_atlas_analyze"
    bl_label = "Analyze Materials"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        settings.atlas_groups.clear()
        settings.last_bake_result = ""
        settings.last_debug_report = ""

        meshes = _target_meshes(context, settings)

        if not meshes:
            self.report({"WARNING"}, "No mesh objects found")
            _store_debug_report(context, meshes, settings)
            return {"CANCELLED"}

        # Classify used material slots independently. A mixed mesh may feed
        # more than one render-type group, but transparent Alpha Blend slots
        # stay disabled by default so their draw order is preserved.
        slot_sources = []
        mesh_by_name = {}
        for obj in meshes:
            if not obj.data.materials:
                continue
            mesh_by_name[obj.name] = obj
            used_slot_indices = sorted({
                int(poly.material_index)
                for poly in obj.data.polygons
                if 0 <= int(poly.material_index) < len(obj.data.materials)
            })
            for slot_index in used_slot_indices:
                mat = obj.data.materials[slot_index]
                slot_sources.append({
                    "object_name": obj.name,
                    "slot_index": slot_index,
                    "render_type": _effective_render_type(obj, slot_index, mat),
                    "has_faces": True,
                })

        group_plans = plan_material_slot_groups(slot_sources)
        total_mats = len(slot_sources)
        settings.total_mats_before = total_mats
        settings.rank_before = _get_rank(total_mats)

        for plan in group_plans:
            rt = plan["render_type"]
            plan_slots = plan["slots"]
            slot_keys = {
                (slot["object_name"], int(slot["slot_index"]))
                for slot in plan_slots
            }
            object_names = list(dict.fromkeys(
                slot["object_name"] for slot in plan_slots
            ))
            objs = [mesh_by_name[name] for name in object_names if name in mesh_by_name]
            if not objs:
                continue

            group = settings.atlas_groups.add()
            group.name = (
                f"Preserved \u2014 {rt} (render order)"
                if plan["preserve_reason"] == "render_order"
                else f"Group \u2014 {rt}"
            )
            group.render_type = rt
            group.preserve_reason = plan["preserve_reason"]
            group.enabled = bool(plan["enabled"])
            group.resolution = "2048"

            has_overlap = False
            has_high_em = False
            for obj in objs:
                object_slot_count = sum(
                    1 for slot in plan_slots if slot["object_name"] == obj.name
                )
                item = group.meshes.add()
                item.object_name = obj.name
                item.render_type = rt
                item.mat_count = object_slot_count
                item.has_shape_keys = bool(obj.data.shape_keys)
                item.has_overlapping_uvs = _has_overlapping_uvs(obj)
                item.has_high_emission = _has_high_emission(obj)
                has_overlap = has_overlap or item.has_overlapping_uvs
                has_high_em = has_high_em or item.has_high_emission

            group.mat_count = len(plan_slots)
            group.warn_overlap = has_overlap
            group.warn_emission = has_high_em
            group.has_warnings = (
                bool(plan["preserve_reason"])
                or rt == "Emissive"
                or has_overlap
                or has_high_em
            )
            _populate_group_sources(
                group,
                objs,
                allowed_slot_keys=slot_keys,
                default_material_enabled=group.enabled,
            )
        _store_debug_report(context, meshes, settings)
        projected = _projected_mat_count(settings)
        rank_after = _get_rank(projected)
        self.report(
            {"INFO"},
            f"Found {total_mats} materials in {len(settings.atlas_groups)} groups — "
            f"estimated result: {projected} mats ({rank_after})"
        )
        pipeline.append_ledger(
            context.scene,
            "atlas_analyze",
            pipeline.OUTCOME_CLEAN,
            f"Found {total_mats} materials in {len(settings.atlas_groups)} atlas groups",
        )
        return {"FINISHED"}


class BF_OT_VRC_AtlasAddGroup(Operator):
    """Add an empty atlas group"""
    bl_idname = "boneforge.vrc_atlas_add_group"
    bl_label = "Add Group"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        group = settings.atlas_groups.add()
        group.name = f"Group {len(settings.atlas_groups)}"
        group.enabled = True
        group.resolution = "2048"
        settings.active_group_index = len(settings.atlas_groups) - 1
        return {"FINISHED"}


class BF_OT_VRC_AtlasRemoveGroup(Operator):
    """Remove the selected atlas group"""
    bl_idname = "boneforge.vrc_atlas_remove_group"
    bl_label = "Remove Group"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        idx = settings.active_group_index
        if 0 <= idx < len(settings.atlas_groups):
            settings.atlas_groups.remove(idx)
            settings.active_group_index = max(0, idx - 1)
        return {"FINISHED"}


# ── Bake operator (with pre-flight invoke + modal progress) ──────

class BF_OT_VRC_AtlasSmartCombine(Operator):
    """Analyze and bake atlas materials with safe default settings"""
    bl_idname = "boneforge.vrc_atlas_smart_combine"
    bl_label = "Smart Combine Materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings

        if settings.auto_analyze_before_bake or not settings.atlas_groups:
            analyze_result = bpy.ops.boneforge.vrc_atlas_analyze()
            if "FINISHED" not in analyze_result:
                self.report({"ERROR"}, "Smart Combine could not find materials to combine")
                return {"CANCELLED"}

        preflight = BF_OT_VRC_AtlasBake._build_preflight(context)
        if preflight["errors"]:
            for error in preflight["errors"]:
                self.report({"ERROR"}, error)
            _store_debug_report(context, _target_meshes(context, settings), settings)
            return {"CANCELLED"}

        try:
            bake_result = bpy.ops.boneforge.vrc_atlas_bake()
        except RuntimeError as bake_err:
            message = str(bake_err).splitlines()[-1] if str(bake_err) else "Smart Combine failed during bake"
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        if "FINISHED" not in bake_result:
            self.report({"ERROR"}, "Smart Combine failed during bake. Copy the debug report for details")
            return {"CANCELLED"}

        self.report({"INFO"}, "Smart Combine finished. Review the atlas, then Accept or Revert")
        return {"FINISHED"}


class BF_OT_VRC_AtlasCopyDebugReport(Operator):
    """Copy the latest atlas diagnostic report to the clipboard"""
    bl_idname = "boneforge.vrc_atlas_copy_debug"
    bl_label = "Copy Debug Report"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        if not settings.last_debug_report:
            _store_debug_report(context, _target_meshes(context, settings), settings)

        if not settings.last_debug_report:
            self.report({"WARNING"}, "No atlas debug report available")
            return {"CANCELLED"}

        context.window_manager.clipboard = settings.last_debug_report
        self.report({"INFO"}, "Atlas debug report copied")
        return {"FINISHED"}


class BF_OT_VRC_AtlasBake(Operator):
    """Bake atlas textures for all enabled groups with pre-flight check"""
    bl_idname = "boneforge.vrc_atlas_bake"
    bl_label = "Bake Atlas"
    bl_options = {"REGISTER", "UNDO"}

    # Pre-flight dialog fields (shown in invoke dialog)
    _preflight_lines: list = []
    _groups_to_bake: list = []

    # ── Pre-flight helpers ────────────────────────────────────────

    @staticmethod
    def _build_preflight(context):
        """Collect pre-flight info lines and validate groups."""
        settings = context.scene.boneforge_atlas_settings
        lines_proceed = []
        lines_skip = []
        lines_change = []
        lines_stable = []
        errors = []

        bake_groups = []

        if settings.has_backup:
            errors.append("Accept or Revert the current atlas result before baking another atlas.")

        if not settings.bake_albedo:
            errors.append("Albedo (Color) must stay enabled so the atlas material has a base texture.")

        enabled_passes = _settings_enabled_passes(settings)
        all_texture_sources = []
        for group in settings.atlas_groups:
            all_texture_sources.extend(_group_texture_quality_sources(group))
        pass_plan = build_multipass_output_plan(
            enabled_passes,
            all_texture_sources,
            base_name="atlas",
            allow_unknown_roles=True,
        )
        for output in pass_plan["outputs"]:
            if output["role"] != ROLE_ALBEDO:
                lines_change.append(
                    f"  Extra output planned: {output['image_name']} ({output['label']})"
                )
        for skipped in pass_plan["skipped"]:
            lines_skip.append(
                f"  {skipped['reason']}; the pass will produce fallback bake data if selected"
            )
        if getattr(settings, "bake_metallic", False):
            errors.append(
                "Metallic atlas pass is not enabled yet: Blender has no direct metallic bake pass in this pipeline. "
                "Leave Metallic off until source-map channel packing is verified."
            )
        if getattr(settings, "channel_pack_orm", False):
            channel_plan = build_channel_pack_plan(
                all_texture_sources,
                allow_unknown_roles=getattr(settings, "allow_unknown_channel_pack_roles", False),
            )
            for channel, spec in CHANNEL_PACK_CONVENTION.items():
                lines_skip.append(
                    f"  ORM {channel}: {spec['label']} "
                    f"(fallback {channel_plan['channels'][channel]['fallback']})"
                )
            if channel_plan["errors"]:
                errors.extend(channel_plan["errors"])
            errors.append(
                "ORM channel packing is preflight-only in this build until the metallic source path is host-verified."
            )

        for group in settings.atlas_groups:
            if not group.enabled:
                if group.preserve_reason == "render_order":
                    lines_skip.append(
                        f"  {group.name} — preserved automatically for render order"
                    )
                else:
                    lines_skip.append(f"  {group.name} — disabled by user")
                continue
            enabled_mats = _group_enabled_material_count(group)
            detected_mats = _group_detected_material_count(group)
            disabled_mats = max(0, detected_mats - enabled_mats)
            if enabled_mats < 2:
                lines_skip.append(
                    f"  {group.name} — only {enabled_mats} material "
                    f"(single-material groups have no effect)"
                )
                continue
            for item in getattr(group, "materials", []):
                if not item.enabled:
                    continue
                obj = bpy.data.objects.get(item.object_name)
                slot = int(item.slot_index)
                valid_slot = (obj is not None and obj.type == "MESH"
                              and 0 <= slot < len(obj.data.materials))
                material = obj.data.materials[slot] if valid_slot else None
                material_name = material.name if material else "<empty>"
                if (not valid_slot or material_name != item.material_name
                        or not any(poly.material_index == slot for poly in obj.data.polygons)
                        or _effective_render_type(obj, slot, material) != item.render_type):
                    errors.append(
                        f"{group.name}: source {item.object_name} / slot {slot} changed since Analyze. "
                        "Run Analyze again before baking."
                    )
            bake_groups.append(group)

            res = group.resolution
            vram = _vram_mb(res)
            lines_proceed.append(
                f"  {group.name}: {enabled_mats} of {detected_mats} materials → "
                f"atlas_{group.render_type.lower().replace(' ', '_')}_{res}px "
                f"({vram} MB VRAM)"
            )
            if disabled_mats:
                lines_skip.append(
                    f"    [i] {group.name}: {disabled_mats} material(s) excluded and kept separate"
                )
            disabled_textures = (
                len(group.textures) - _group_enabled_texture_count(group)
                if hasattr(group, "textures") else 0
            )
            if disabled_textures > 0:
                lines_skip.append(
                    f"    [i] {group.name}: {disabled_textures} texture image(s) excluded from the bake"
                )
            if getattr(group, "quality_summary", ""):
                lines_skip.append(f"    [i] {group.name}: {group.quality_summary}")
            for material_item in getattr(group, "materials", []):
                if not material_item.enabled:
                    continue
                if material_item.size_override or material_item.has_no_images:
                    source_width, source_height = _material_source_size(group, material_item)
                    size_plan = resolve_size_preset(
                        material_item.size_preset if material_item.size_override else "SOURCE",
                        source_width=source_width,
                        source_height=source_height,
                        custom_width=material_item.target_width,
                        custom_height=material_item.target_height,
                        fallback_size=material_item.fallback_size or settings.color_fallback_size,
                    )
                    if not size_plan["valid"]:
                        errors.append(
                            f"{material_item.material_name}: invalid texture size "
                            f"{size_plan['width']}x{size_plan['height']}"
                        )
                    lines_skip.append(
                        f"    [i] {material_item.material_name}: size plan "
                        f"{size_plan['width']}x{size_plan['height']} ({size_plan['preset']})"
                    )
            if group.warn_overlap:
                lines_skip.append(
                    f"    [!] {group.name} — overlapping UVs detected. "
                    f"Atlas UV will use {get_uv_method_label(settings.pack_method)}"
                )
            if group.warn_emission and settings.output_format != "EXR":
                lines_skip.append(
                    f"    [!] {group.name} — emission > 1.0 detected. "
                    f"Values will clamp to 1.0 in {settings.output_format}. "
                    f"Switch to EXR to preserve HDR emission"
                )

        if not bake_groups:
            if not settings.atlas_groups:
                errors.append("Click Analyze to create an Atlas Group before baking.")
            elif not any(group.enabled for group in settings.atlas_groups):
                errors.append("Check the box beside a group under Atlas Groups to enable baking.")
            else:
                errors.append("Check at least two materials in an enabled Atlas Group to bake.")

        if settings.keep_source_uv_maps:
            lines_change.append(
                "  Atlas UV generated with selected UV method; source UV maps kept by advanced setting"
            )
            lines_skip.append(
                "    [!] Kept source UV maps can export atlas_uv as UV1 in FBX/Unity"
            )
        else:
            lines_change.append(
                "  Export UV set: atlas_uv becomes UV0; source UV maps removed from atlas mesh"
            )
        lines_change.append(
            "  Source textures forced to sample original UVs during bake"
        )
        lines_change.append(
            "  Atlas mesh validated before originals are hidden"
        )
        packing = packing_preset_settings(settings.packing_preset)
        lines_change.append(
            f"  Packing preset: {packing['label']} "
            f"(padding {settings.atlas_padding_pixels}px, margin {settings.uv_margin})"
        )
        lines_change.append(
            f"  Output material type: {_output_material_type_label(settings)}"
        )
        lines_change.append(
            f"  Output surface: {_output_surface_shader_label(settings)}"
        )
        after = sum(len(_enabled_slots_by_object(g)) for g in bake_groups) + sum(
            _group_detected_material_count(g) for g in settings.atlas_groups
            if not g.enabled or _group_enabled_material_count(g) < 2
        ) + sum(
            max(0, _group_detected_material_count(g) - _group_enabled_material_count(g))
            for g in bake_groups
        )
        lines_change.append(
            f"  Material slots: {settings.total_mats_before} → ~{after}"
        )
        if settings.preserve_originals:
            lines_change.append(
                f"  Backup collection: {_BACKUP_COLLECTION_PREFIX}[timestamp] (visible)"
            )

        lines_stable.append("  Mesh geometry (no vertices moved)")
        lines_stable.append("  Object hierarchy and parent relationships")
        lines_stable.append("  Shape keys / blendshapes")

        return {
            "proceed": lines_proceed,
            "skip": lines_skip,
            "change": lines_change,
            "stable": lines_stable,
            "errors": errors,
            "bake_groups": bake_groups,
        }

    # ── Invoke: pre-flight dialog ─────────────────────────────────

    def invoke(self, context, event):
        settings = context.scene.boneforge_atlas_settings
        if not settings.atlas_groups:
            self.report({"ERROR"}, "Run Analyze first to detect material groups")
            return {"CANCELLED"}

        pf = self._build_preflight(context)
        self._preflight_lines = pf
        self._groups_to_bake = pf["bake_groups"]

        if pf["errors"]:
            for e in pf["errors"]:
                self.report({"ERROR"}, e)
            return {"CANCELLED"}

        return context.window_manager.invoke_props_dialog(self, width=520)

    def draw(self, context):
        """Draw the pre-flight dialog."""
        layout = self.layout
        pf = self._preflight_lines

        layout.label(text=T("ATLAS PRE-FLIGHT CHECK"))
        layout.separator()

        if pf.get("proceed"):
            layout.label(text=T("WILL BAKE:"))
            for line in pf["proceed"]:
                layout.label(text=line)
            layout.separator()

        if pf.get("skip"):
            layout.label(text=T("NOTES / WARNINGS:"))
            for line in pf["skip"]:
                layout.label(text=line, icon="INFO")
            layout.separator()

        if pf.get("change"):
            layout.label(text=T("WHAT WILL CHANGE:"))
            for line in pf["change"]:
                layout.label(text=line)
            layout.separator()

        if pf.get("stable"):
            layout.label(text=T("WHAT WILL NOT CHANGE:"), icon="CHECKMARK")
            for line in pf["stable"]:
                layout.label(text=line)

    # ── Execute: backup + bake ────────────────────────────────────

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        pf = self._build_preflight(context)
        bake_groups = pf["bake_groups"]
        if pf["errors"]:
            for e in pf["errors"]:
                self.report({"ERROR"}, e)
            pipeline.append_ledger(
                context.scene,
                "atlas_bake",
                pipeline.OUTCOME_FAILED,
                "; ".join(pf["errors"]),
            )
            self._groups_to_bake = []
            return {"CANCELLED"}
        self._preflight_lines = pf
        self._groups_to_bake = bake_groups

        _store_debug_report(context, _target_meshes(context, settings), settings)
        wm = context.window_manager
        total_steps = len(bake_groups)
        wm.progress_begin(0, total_steps)

        try:
            # Step 1 — backup originals
            if settings.preserve_originals:
                backup_name = _BACKUP_COLLECTION_PREFIX + str(int(time.time()))
                self._create_backup(context, bake_groups, backup_name)
                settings.backup_collection_name = backup_name
                settings.has_backup = True

            # Step 2 — bake each group
            mats_before = settings.total_mats_before
            mats_after_count = mats_before
            results = []
            completed_groups = []

            for step, group in enumerate(bake_groups):
                wm.progress_update(step)
                result = self._bake_group(context, group, settings)
                if result:
                    results.append(result)
                    completed_groups.append(group)
                    mats_after_count -= (
                        _group_enabled_material_count(group)
                        - len(_enabled_slots_by_object(group))
                    )
                else:
                    raise RuntimeError(f"{group.name}: no atlas mesh was created. Run Analyze again.")

            finalized_results = self._finalize_source_partitions(
                context, completed_groups, settings, results
            )
            wm.progress_end()

            # Post-bake authority sentence (unanimous addition R)
            rank_before = _get_rank(mats_before)
            rank_after = _get_rank(mats_after_count)
            authority = (
                f"Baked {len(results)} atlas group(s). "
                f"Reduced from {mats_before} to {mats_after_count} materials — "
                f"rank: {rank_after}"
            )
            settings.last_bake_result = authority
            settings.total_mats_before = mats_after_count

            # Refresh Copy Debug from the generated atlas objects.  The report
            # captured before baking only describes the source meshes and
            # cannot include the per-tile statistics stored by _bake_group.
            result_meshes = []
            for object_name in results + finalized_results:
                result_obj = bpy.data.objects.get(object_name)
                if result_obj is not None:
                    result_meshes.append(result_obj)
            _store_debug_report(context, result_meshes, settings)

            self.report({"INFO"}, authority)
            pipeline.append_ledger(
                context.scene,
                "atlas_bake",
                pipeline.OUTCOME_CHANGED,
                authority,
                {
                    "groups": len(results),
                    "scope": settings.target_scope,
                    "format": settings.output_format,
                    "output_path": settings.output_path,
                    "uv_method": settings.pack_method,
                },
            )
            pipeline.set_phase_complete(context.scene, "material_atlas", pipeline.OUTCOME_CHANGED)
            self._groups_to_bake = []

        except Exception as e:
            wm.progress_end()
            _cleanup_transient_atlas_objects()
            logger.exception("[BoneCraft Atlas] Bake failed")
            self.report({"ERROR"}, f"Atlas bake failed: {e}")
            pipeline.append_ledger(
                context.scene,
                "atlas_bake",
                pipeline.OUTCOME_FAILED,
                f"Atlas bake failed: {e}",
            )
            pipeline.set_phase_complete(context.scene, "material_atlas", pipeline.OUTCOME_FAILED)
            return {"CANCELLED"}

        return {"FINISHED"}

    # ── Bake internals ────────────────────────────────────────────

    def _create_backup(self, context, bake_groups, backup_name):
        """Duplicate all target meshes into a visible backup collection."""
        scene = context.scene
        backup_coll = bpy.data.collections.new(backup_name)
        scene.collection.children.link(backup_coll)

        seen = set()
        for group in bake_groups:
            for item in group.meshes:
                if item.object_name in seen:
                    continue
                seen.add(item.object_name)
                obj = bpy.data.objects.get(item.object_name)
                if obj is None:
                    continue
                dup = obj.copy()
                dup.data = obj.data.copy()
                dup.name = f"PRE_ATLAS_{obj.name}"
                dup["boneforge_atlas_source_visibility"] = json.dumps({
                    "hide_render": bool(obj.hide_render),
                    "hide_viewport": bool(obj.hide_viewport),
                    "hide_set": bool(obj.hide_get()),
                })
                backup_coll.objects.link(dup)
                dup.hide_set(False)
                dup.hide_viewport = False
                dup.hide_render = False

        # Keep the backup collection visible so users can inspect the preserved duplicate.
        layer_coll = self._find_layer_collection(
            context.view_layer.layer_collection, backup_name
        )
        if layer_coll:
            layer_coll.hide_viewport = False
            layer_coll.exclude = False

    def _find_layer_collection(self, layer_coll, name):
        if layer_coll.name == name:
            return layer_coll
        for child in layer_coll.children:
            result = self._find_layer_collection(child, name)
            if result:
                return result
        return None

    def _finalize_source_partitions(
        self, context, bake_groups, settings, atlas_result_names
    ):
        """Rebuild every bake on a full copy of each original source mesh."""
        source_objects = {}
        baked_slots_by_object = {}
        for group in bake_groups:
            enabled_by_object = _enabled_slots_by_object(group)
            for item in group.meshes:
                obj = bpy.data.objects.get(item.object_name)
                if obj is None or obj.type != "MESH":
                    continue
                source_objects[obj.name] = obj
                baked_slots_by_object.setdefault(obj.name, set()).update(
                    enabled_by_object.get(obj.name, set())
                )

        atlas_by_source = {}
        for result_name in atlas_result_names:
            result_obj = bpy.data.objects.get(result_name)
            if result_obj is None:
                continue
            try:
                result_sources = json.loads(
                    result_obj.get("boneforge_atlas_sources", "[]")
                )
            except (TypeError, ValueError):
                result_sources = []
            for source_object_index, source_name in enumerate(result_sources):
                atlas_by_source.setdefault(source_name, []).append(
                    (result_obj, source_object_index)
                )

        finalized_names = []
        for object_name, obj in source_objects.items():
            used_slots = {
                int(poly.material_index)
                for poly in obj.data.polygons
                if 0 <= int(poly.material_index) < len(obj.data.materials)
            }
            baked_slots = set(baked_slots_by_object.get(object_name, set()))
            unbaked_slots = sorted(used_slots - baked_slots)
            source_atlases = atlas_by_source.get(object_name, [])

            if source_atlases:
                combined = obj.copy()
                combined.data = obj.data.copy()
                # Kept slots retain their authored material and shared identity.
                # Only the temporary bake meshes need independent materials.
                original_materials = list(combined.data.materials)
                original_polygon_slots = [
                    int(polygon.material_index)
                    for polygon in combined.data.polygons
                ]
                _mirror_active_uv_to_atlas(combined.data)
                combined.data.materials.clear()

                for atlas_obj, _source_object_index in source_atlases:
                    if not atlas_obj.data.materials:
                        raise RuntimeError(
                            f"Atlas result '{atlas_obj.name}' has no material"
                        )
                    combined.data.materials.append(atlas_obj.data.materials[0])
                for slot_index in unbaked_slots:
                    combined.data.materials.append(original_materials[slot_index])

                preserved_index = {
                    slot_index: len(source_atlases) + offset
                    for offset, slot_index in enumerate(unbaked_slots)
                }
                for polygon, source_slot in zip(
                    combined.data.polygons, original_polygon_slots
                ):
                    polygon.material_index = preserved_index.get(source_slot, 0)

                combined_uv = combined.data.uv_layers["atlas_uv"].data
                for atlas_index, (
                    atlas_obj, source_object_index
                ) in enumerate(source_atlases):
                    source_face_ids = atlas_obj.data.attributes.get(
                        _SOURCE_POLYGON_ATTRIBUTE
                    )
                    source_object_ids = atlas_obj.data.attributes.get(
                        _SOURCE_OBJECT_ATTRIBUTE
                    )
                    atlas_uv = atlas_obj.data.uv_layers.get("atlas_uv")
                    if (
                        source_face_ids is None
                        or source_object_ids is None
                        or atlas_uv is None
                    ):
                        raise RuntimeError(
                            f"Atlas result '{atlas_obj.name}' lost its source-face map"
                        )
                    for atlas_polygon in atlas_obj.data.polygons:
                        if int(
                            source_object_ids.data[atlas_polygon.index].value
                        ) != source_object_index:
                            continue
                        source_polygon_index = int(
                            source_face_ids.data[atlas_polygon.index].value
                        )
                        target_polygon = combined.data.polygons[source_polygon_index]
                        if len(target_polygon.loop_indices) != len(
                            atlas_polygon.loop_indices
                        ):
                            raise RuntimeError(
                                "Atlas/source polygon loop counts no longer match"
                            )
                        target_polygon.material_index = atlas_index
                        for target_loop, atlas_loop in zip(
                            target_polygon.loop_indices,
                            atlas_polygon.loop_indices,
                        ):
                            combined_uv[target_loop].uv = atlas_uv.data[atlas_loop].uv

                _prepare_atlas_uv_for_export(combined.data, settings.keep_source_uv_maps)
                context.scene.collection.objects.link(combined)
                first_atlas = source_atlases[0][0]
                for key in first_atlas.keys():
                    combined[key] = first_atlas[key]
                combined.name = f"ATLAS_{obj.name}"
                combined["boneforge_atlas_backup"] = settings.backup_collection_name
                combined["boneforge_atlas_sources"] = json.dumps([obj.name])
                combined["boneforge_atlas_preserved_slots"] = json.dumps(
                    unbaked_slots
                )
                finalized_names.append(combined.name)
            elif unbaked_slots:
                preserved = obj.copy()
                preserved.data = obj.data.copy()
                remove_slots = set(range(len(preserved.data.materials))) - set(
                    unbaked_slots
                )
                if _remove_faces_by_material_slots(preserved, remove_slots):
                    _compact_material_slots(preserved.data)
                    preserved.name = f"KEPT_{obj.name}"
                    context.scene.collection.objects.link(preserved)
                    preserved["boneforge_atlas_backup"] = (
                        settings.backup_collection_name
                    )
                    preserved["boneforge_atlas_sources"] = json.dumps([obj.name])
                    preserved["boneforge_atlas_preserved_slots"] = json.dumps(
                        unbaked_slots
                    )
                    finalized_names.append(preserved.name)
                else:
                    bpy.data.objects.remove(preserved, do_unlink=True)

            if settings.preserve_originals:
                obj.hide_set(True)
                obj.hide_render = True
            else:
                bpy.data.objects.remove(obj, do_unlink=True)

        for result_name in atlas_result_names:
            atlas_obj = bpy.data.objects.get(result_name)
            if atlas_obj is not None:
                bpy.data.objects.remove(atlas_obj, do_unlink=True)

        return finalized_names

    def _bake_group(self, context, group, settings):
        """
        Bake one atlas group.

        Workflow:
        1. Collect mesh objects for this group
        2. Duplicate them into a working set
        3. Join into one mesh
        4. Preserve original UV as 'UVMap_pre_atlas'
        5. Create 'atlas_uv' UV map
        6. Smart UV Project → Pack Islands on joined mesh
        7. Create atlas Image
        8. Add Image Texture node (selected, unlinked) to each material
        9. Bake DIFFUSE with Cycles → atlas image
        10. Create new atlas material with Image Texture → BSDF
        11. Assign atlas material to the working mesh
        12. Reparent working mesh to armature (if present)
        13. Hide/remove original group meshes from view
        """
        res = int(group.resolution)
        arm = active_armature(context)
        scene = context.scene
        enabled_slots_by_obj = _enabled_slots_by_object(group)
        enabled_texture_keys = _enabled_texture_keys(group)

        # Collect source objects
        source_objs = []
        for item in group.meshes:
            obj = bpy.data.objects.get(item.object_name)
            if obj and obj.type == "MESH" and enabled_slots_by_obj.get(obj.name):
                source_objs.append(obj)

        if not source_objs:
            return None
        source_names = [obj.name for obj in source_objs]

        # ── Create working duplicates ──────────────────────────
        # Source objects remain available until every render-type group has
        # baked. This lets one mesh safely feed Opaque and Emissive/Clip
        # atlases without the first group deleting the source for the next.
        _ensure_object_mode(context, "Prepare atlas bake")
        _deselect_all_objects_directly(context.view_layer)
        work_objs = []
        for source_object_index, obj in enumerate(source_objs):
            enabled_slots = set(enabled_slots_by_obj.get(obj.name, set()))
            all_slots = set(range(len(obj.data.materials)))
            disabled_slots = all_slots - enabled_slots

            dup = obj.copy()
            dup.data = obj.data.copy()
            _copy_material_slots(dup.data)
            _stamp_source_polygon_indices(dup.data, source_object_index)
            if not _remove_faces_by_material_slots(dup, disabled_slots):
                bpy.data.objects.remove(dup, do_unlink=True)
                continue
            for mat_index, mat in enumerate(dup.data.materials):
                if mat is not None:
                    original_mat = obj.data.materials[mat_index] if mat_index < len(obj.data.materials) else mat
                    original_name = original_mat.name if original_mat else mat.name
                    _disconnect_disabled_texture_nodes(
                        mat,
                        obj.name,
                        mat_index,
                        original_name,
                        enabled_texture_keys,
                    )
            dup.name = f"__BF_ATLAS_WORK_{obj.name}"
            scene.collection.objects.link(dup)
            # Bake targets must be renderable even when their source is hidden
            # from the camera. Only the temporary duplicate is made visible.
            dup.hide_viewport = False
            dup.hide_render = False
            dup.hide_set(False)
            dup.select_set(True)
            work_objs.append(dup)

        if not work_objs:
            return None
        # ── Preserve original UV map ──────────────────────────
        for obj in work_objs:
            mesh = obj.data
            if mesh.uv_layers.active:
                original_uv = mesh.uv_layers.active
                if original_uv.name != "UVMap_pre_atlas":
                    original_uv.name = "UVMap_pre_atlas"

        # ── Join into one working mesh ────────────────────────
        _ensure_object_mode(context, "Prepare atlas join")
        _deselect_all_objects_directly(context.view_layer)
        for obj in work_objs:
            obj.select_set(True)
        context.view_layer.objects.active = work_objs[0]
        try:
            if len(work_objs) > 1:
                _run_with_view3d_context(context, bpy.ops.object.join, "Join atlas work meshes")
        except Exception as join_err:
            for w in work_objs:
                if w.name in bpy.data.objects:
                    bpy.data.objects.remove(w, do_unlink=True)

            raise RuntimeError(f"Join failed — work objects cleaned up: {join_err}")
        joined = context.view_layer.objects.active
        joined.name = f"__BF_ATLAS_{group.render_type.replace(' ', '_')}"

        # ── Create atlas UV map ───────────────────────────────
        mesh = joined.data
        if "atlas_uv" in mesh.uv_layers:
            mesh.uv_layers.remove(mesh.uv_layers["atlas_uv"])
        atlas_uv = mesh.uv_layers.new(name="atlas_uv")

        # Bake into atlas_uv; copied source image nodes read UVMap_pre_atlas explicitly.
        for uv in mesh.uv_layers:
            uv.active_render = (uv.name == "atlas_uv")
        _activate_atlas_uv(mesh)

        # ── Smart UV Project → Pack Islands ───────────────────
        uv_result = apply_atlas_uv_method(context, joined, settings, _run_with_view3d_context)
        joined["boneforge_atlas_uv_method"] = uv_result["method"]
        joined["boneforge_atlas_uv_result"] = summarize_atlas_uv_result(uv_result)
        logger.info("[BoneCraft Atlas] %s", joined["boneforge_atlas_uv_result"])

        # ── Create atlas image ────────────────────────────────
        # The name carries the source mesh, not just type+res. Two meshes
        # atlased at the same type+res used to collide on one name — and
        # the collision was destructive: the old image datablock was
        # force-removed (stripping it from every material that used it)
        # and its PNG overwritten on disk.
        slug_source = (
            group.materials[0].object_name if len(group.materials) else "mesh"
        )
        slug = "".join(
            ch if (ch.isalnum() or ch == "_") else "_" for ch in slug_source
        ).strip("_").lower() or "mesh"
        atlas_name = (
            f"bf_atlas_{slug}_"
            f"{group.render_type.lower().replace(' ', '_')}_{res}px"
        )
        existing_atlas = bpy.data.images.get(atlas_name)
        if existing_atlas is not None and existing_atlas.users == 0:
            # Truly orphaned — safe to replace in place.
            bpy.data.images.remove(existing_atlas)
        # When the name is still taken by an in-use image, images.new()
        # auto-suffixes (.001), so the earlier atlas keeps working. Adopt
        # whatever name Blender granted — the disk path, material name and
        # extra pass names below all derive from it, keeping the previous
        # run's PNG safe from being overwritten too.
        atlas_img = bpy.data.images.new(atlas_name, width=res, height=res, alpha=True)
        atlas_name = atlas_img.name
        atlas_img.colorspace_settings.name = "sRGB"
        extra_images = {}
        output_render_type = _resolve_output_render_type(group, settings)

        # ── Add Image Texture node to each material ───────────
        source_uv_routes = 0
        for mat in joined.data.materials:
            if not mat or not mat.use_nodes:
                continue
            nodes = mat.node_tree.nodes
            source_uv_routes += _route_source_image_nodes_to_uv(mat, "UVMap_pre_atlas")
            # Remove any existing BF target node
            old = nodes.get("BF_ATLAS_TARGET")
            if old:
                nodes.remove(old)
            img_node = nodes.new("ShaderNodeTexImage")
            img_node.name = "BF_ATLAS_TARGET"
            img_node.image = atlas_img
            img_node.location = (-300, -400)
            # Must be selected and active — this is the bake target
            for n in nodes:
                n.select = False
            img_node.select = True
            nodes.active = img_node
        needs_alpha_atlas = _group_needs_alpha_atlas(joined, output_render_type)

        # ── Bake DIFFUSE ──────────────────────────────────────
        saved_engine = scene.render.engine
        scene.render.engine = "CYCLES"
        enabled_passes = set(_settings_enabled_passes(settings))

        try:
            context.view_layer.objects.active = joined
            _deselect_all_objects_directly(context.view_layer)
            joined.select_set(True)
            _bake_albedo_to_atlas(context, joined, atlas_img, settings)
            alpha_sources = None
            if needs_alpha_atlas:
                alpha_sources = _bake_alpha_mask_to_atlas(context, joined, atlas_img, settings, atlas_name, res)
            for role, spec in _EXTRA_BAKE_PASSES.items():
                if role not in enabled_passes:
                    continue
                pass_name = f"{atlas_name}{spec['suffix']}"
                if pass_name in bpy.data.images:
                    bpy.data.images.remove(bpy.data.images[pass_name])
                pass_img = bpy.data.images.new(pass_name, width=res, height=res, alpha=True)
                pass_img.colorspace_settings.name = spec["colorspace"]
                for mat in joined.data.materials:
                    if not mat or not mat.use_nodes:
                        continue
                    nodes = mat.node_tree.nodes
                    target = nodes.get("BF_ATLAS_TARGET")
                    if target is None:
                        continue
                    target.image = pass_img
                    for node in nodes:
                        node.select = False
                    target.select = True
                    nodes.active = target
                _run_with_view3d_context(
                    context,
                    bpy.ops.object.bake,
                    f"Bake {role_label(role)} atlas",
                    type=spec["type"],
                    use_selected_to_active=False,
                    margin=settings.atlas_padding_pixels,
                    use_clear=True,
                )
                extra_images[role] = pass_img
            for mat in joined.data.materials:
                if mat and mat.use_nodes and mat.node_tree:
                    target = mat.node_tree.nodes.get("BF_ATLAS_TARGET")
                    if target is not None:
                        target.image = atlas_img
            # Post-bake diagnostics: sample every material's tile so a
            # tile that baked invisible or blank names itself in Copy
            # Debug instead of needing an Image Editor inspection.
            if uv_result.get("method") == "SOURCE_PRESERVE":
                tile_stats = _collect_atlas_tile_stats(
                    joined, atlas_img, alpha_sources if needs_alpha_atlas else None
                )
                if tile_stats:
                    joined["boneforge_atlas_tile_stats"] = json.dumps(tile_stats)
                    for entry in tile_stats:
                        logger.info("[BoneCraft Atlas] tile %s", entry)
        except Exception as bake_err:
            scene.render.engine = saved_engine
            logger.warning("[BoneCraft Atlas] Cycles bake failed for %s: %s", group.name, bake_err)
            raise
        scene.render.engine = saved_engine

        keep_source_uv_maps = getattr(settings, "keep_source_uv_maps", False)
        _prepare_atlas_uv_for_export(joined.data, keep_source_uv_maps)

        # ── Save atlas image ──────────────────────────────────
        out_dir = bpy.path.abspath(settings.output_path)
        if out_dir and not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except OSError:
                out_dir = ""

        fmt_ext = {"PNG": ".png", "TGA": ".tga", "EXR": ".exr"}
        ext = fmt_ext.get(settings.output_format, ".png")
        if out_dir:
            img_path = os.path.join(out_dir, atlas_name + ext)
            atlas_img.filepath_raw = img_path
            atlas_img.file_format = settings.output_format
            try:
                atlas_img.save()
            except Exception as save_err:
                logger.warning(f"[BoneCraft Atlas] Could not save image: {save_err}")
            for role, image in extra_images.items():
                image.filepath_raw = os.path.join(out_dir, image.name + ext)
                image.file_format = settings.output_format
                try:
                    image.save()
                except Exception as save_err:
                    logger.warning(
                        "[BoneCraft Atlas] Could not save %s atlas: %s",
                        role_label(role),
                        save_err,
                    )

        # ── Build atlas material ──────────────────────────────
        mat_name = f"M_{atlas_name}"
        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])
        atlas_mat = bpy.data.materials.new(mat_name)
        atlas_mat.use_nodes = True
        # Set blend mode to match the selected output render type, on
        # whichever API this host has: blend_method exists through
        # Blender/Bforartists 4.x, surface_render_method from Blender 4.2's
        # EEVEE Next onward (and is the only one left in Blender 5).
        _set_material_alpha_output(atlas_mat, output_render_type)

        nodes = atlas_mat.node_tree.nodes
        links = atlas_mat.node_tree.links
        nodes.clear()
        output_node = nodes.new("ShaderNodeOutputMaterial")
        output_node.location = (520, 0)
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.name = "Atlas"
        tex_node.image = atlas_img
        tex_node.location = (-300, 0)
        uv_node = nodes.new("ShaderNodeUVMap")
        uv_node.uv_map = "atlas_uv"
        uv_node.location = (-550, 0)
        links.new(uv_node.outputs["UV"], tex_node.inputs["Vector"])

        output_surface_shader = _resolve_output_surface_shader(settings)
        if output_surface_shader == "DIFFUSE":
            surface_node = nodes.new("ShaderNodeBsdfDiffuse")
            surface_node.name = "Atlas Diffuse Surface"
            surface_shader_output = _node_output(surface_node, "BSDF")
        elif output_surface_shader == "EMISSION":
            surface_node = nodes.new("ShaderNodeEmission")
            surface_node.name = "Atlas Emission Surface"
            surface_shader_output = _node_output(surface_node, "Emission")
            strength_input = _node_input(surface_node, "Strength")
            if strength_input is not None and hasattr(strength_input, "default_value"):
                strength_input.default_value = 1.0
        elif output_surface_shader == "TRANSPARENT":
            surface_node = nodes.new("ShaderNodeBsdfTransparent")
            surface_node.name = "Atlas Transparent Surface"
            surface_shader_output = _node_output(surface_node, "BSDF")
        else:
            surface_node = nodes.new("ShaderNodeBsdfPrincipled")
            surface_node.name = "Atlas Principled Surface"
            surface_shader_output = _node_output(surface_node, "BSDF")
        surface_node.location = (0, 0)

        surface_color_input = _node_input(surface_node, "Base Color", "Color")
        if surface_color_input is not None and not (
            output_surface_shader == "EMISSION" and ROLE_EMISSION in extra_images
        ):
            links.new(tex_node.outputs["Color"], surface_color_input)

        if ROLE_NORMAL in extra_images:
            normal_input = _node_input(surface_node, "Normal")
            normal_tex = nodes.new("ShaderNodeTexImage")
            normal_tex.name = "Atlas Normal"
            normal_tex.image = extra_images[ROLE_NORMAL]
            normal_tex.location = (-300, -250)
            normal_map = nodes.new("ShaderNodeNormalMap")
            normal_map.location = (0, -250)
            links.new(uv_node.outputs["UV"], normal_tex.inputs["Vector"])
            links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
            if normal_input is not None:
                links.new(normal_map.outputs["Normal"], normal_input)
        if ROLE_EMISSION in extra_images:
            emission_tex = nodes.new("ShaderNodeTexImage")
            emission_tex.name = "Atlas Emission"
            emission_tex.image = extra_images[ROLE_EMISSION]
            emission_tex.location = (-300, -500)
            links.new(uv_node.outputs["UV"], emission_tex.inputs["Vector"])
            if output_surface_shader == "EMISSION":
                emission_input = _node_input(surface_node, "Color")
                emission_strength = _node_input(surface_node, "Strength")
            elif output_surface_shader == "PRINCIPLED":
                emission_input = _node_input(surface_node, "Emission Color", "Emission")
                emission_strength = _node_input(surface_node, "Emission Strength")
            else:
                emission_input = None
                emission_strength = None
            if emission_input is not None:
                links.new(emission_tex.outputs["Color"], emission_input)
            if emission_strength is not None and hasattr(emission_strength, "default_value"):
                emission_strength.default_value = 1.0
        elif output_render_type == "Emissive" and output_surface_shader == "PRINCIPLED":
            # Deliberately does NOT wire the albedo atlas into Emission.
            #
            # This used to link the base-colour atlas into Emission Color at
            # strength 1.0 whenever the group was flagged Emissive but had no
            # emission pass. That applies the same colour twice, so bright
            # surfaces blow out — VRoid avatars came back saturated magenta.
            # Emission must come from a real emission map (handled by the
            # ROLE_EMISSION branch above), never from base colour.
            emission_strength = _node_input(surface_node, "Emission Strength")
            if emission_strength is not None and hasattr(emission_strength, "default_value"):
                emission_strength.default_value = 0.0
            logger.info(
                "[BoneForge] atlas group '%s' is Emissive but has no emission "
                "pass; leaving Emission unwired rather than duplicating albedo",
                getattr(group, "name", "?"),
            )
        if ROLE_ROUGHNESS in extra_images:
            roughness_tex = nodes.new("ShaderNodeTexImage")
            roughness_tex.name = "Atlas Roughness"
            roughness_tex.image = extra_images[ROLE_ROUGHNESS]
            roughness_tex.location = (-300, -750)
            links.new(uv_node.outputs["UV"], roughness_tex.inputs["Vector"])
            roughness_input = _node_input(surface_node, "Roughness")
            if roughness_input is not None:
                links.new(roughness_tex.outputs["Color"], roughness_input)

        surface_output = surface_shader_output
        if output_render_type in ("Alpha Blend", "Alpha Clip"):
            alpha_input = _node_input(surface_node, "Alpha")
            if alpha_input is not None:
                links.new(tex_node.outputs["Alpha"], alpha_input)
            elif output_surface_shader != "TRANSPARENT" and surface_shader_output is not None:
                transparent_node = nodes.new("ShaderNodeBsdfTransparent")
                transparent_node.name = "Atlas Alpha Transparent"
                transparent_node.location = (0, -220)
                mix_node = nodes.new("ShaderNodeMixShader")
                mix_node.name = "Atlas Alpha Surface Mix"
                mix_node.location = (260, -80)
                links.new(tex_node.outputs["Alpha"], mix_node.inputs[0])
                links.new(transparent_node.outputs["BSDF"], mix_node.inputs[1])
                links.new(surface_shader_output, mix_node.inputs[2])
                surface_output = _node_output(mix_node, "Shader")
        if surface_output is not None:
            links.new(surface_output, output_node.inputs["Surface"])

        # ── Assign atlas material to joined mesh ──────────────
        _assign_single_atlas_material(joined.data, atlas_mat)
        _validate_atlas_mesh(joined, atlas_mat)

        # ── Reparent to armature if present ──────────────────
        if arm:
            joined.parent = arm
            armature_mod = joined.modifiers.get("Armature")
            if not armature_mod:
                armature_mod = joined.modifiers.new("Armature", "ARMATURE")
            armature_mod.object = arm

        # Clean up working name
        joined.name = (
            f"ATLAS_{group.render_type.replace(' ', '_')}_{res}px"
        )
        joined["boneforge_atlas_backup"] = settings.backup_collection_name
        joined["boneforge_atlas_sources"] = json.dumps(source_names)
        joined["boneforge_atlas_source_uv_routes"] = source_uv_routes
        joined["boneforge_atlas_uv0"] = "atlas_uv"
        joined["boneforge_atlas_source_uv_maps_kept"] = bool(keep_source_uv_maps)
        joined["boneforge_atlas_output_material_type"] = output_render_type
        joined["boneforge_atlas_output_material_mode"] = getattr(
            settings,
            "output_material_type",
            "AUTO",
        )
        joined["boneforge_atlas_output_surface_shader"] = output_surface_shader
        joined["boneforge_atlas_output_surface_mode"] = getattr(
            settings,
            "output_surface_shader",
            "AUTO",
        )
        joined["boneforge_atlas_outputs"] = json.dumps(
            {role: image.name for role, image in extra_images.items()}
        )

        return joined.name


class BF_OT_VRC_AtlasAccept(Operator):
    """Accept atlas result and permanently delete the original backup"""
    bl_idname = "boneforge.vrc_atlas_accept"
    bl_label = "Accept — Delete Backup"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self,
            event,
        )

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        if not settings.has_backup:
            self.report({"WARNING"}, "No backup to delete")
            return {"CANCELLED"}

        coll = bpy.data.collections.get(settings.backup_collection_name)
        source_names = set()
        for obj in context.scene.objects:
            if obj.get("boneforge_atlas_backup") != settings.backup_collection_name:
                continue
            raw_sources = obj.get("boneforge_atlas_sources", "[]")
            try:
                source_names.update(json.loads(raw_sources))
            except (TypeError, ValueError):
                pass

        for name in source_names:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                bpy.data.objects.remove(obj, do_unlink=True)

        if coll:
            # Remove all objects in collection
            for obj in list(coll.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(coll)

        settings.has_backup = False
        settings.backup_collection_name = ""
        self.report({"INFO"}, "Backup deleted — atlas accepted")
        return {"FINISHED"}


class BF_OT_VRC_AtlasRevert(Operator):
    """Revert to original meshes from backup, removing atlas result"""
    bl_idname = "boneforge.vrc_atlas_revert"
    bl_label = "Revert — Restore Originals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.boneforge_atlas_settings
        if not settings.has_backup:
            self.report({"WARNING"}, "No backup to restore from")
            return {"CANCELLED"}

        coll = bpy.data.collections.get(settings.backup_collection_name)
        if not coll:
            self.report({"ERROR"}, f"Backup collection not found: {settings.backup_collection_name}")
            settings.has_backup = False
            return {"CANCELLED"}

        # Remove atlas meshes created by this backup/session.
        scene = context.scene
        to_remove = [
            obj for obj in scene.objects
            if obj.get("boneforge_atlas_backup") == settings.backup_collection_name
        ]
        for obj in to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Restore originals first; backup duplicates are a fallback if a source was removed.
        for obj in list(coll.objects):
            orig_name = obj.name.replace("PRE_ATLAS_", "", 1)
            try:
                visibility = json.loads(obj.get("boneforge_atlas_source_visibility", "{}"))
            except (TypeError, ValueError):
                visibility = {}
            original = bpy.data.objects.get(orig_name)
            if original is not None:
                original.hide_viewport = bool(visibility.get("hide_viewport", False))
                original.hide_render = bool(visibility.get("hide_render", False))
                original.hide_set(bool(visibility.get("hide_set", False)))
                bpy.data.objects.remove(obj, do_unlink=True)
                continue

            obj.name = orig_name
            try:
                scene.collection.objects.link(obj)
            except RuntimeError:
                pass
            obj.hide_viewport = bool(visibility.get("hide_viewport", False))
            obj.hide_render = bool(visibility.get("hide_render", False))
            obj.hide_set(bool(visibility.get("hide_set", False)))
            if "boneforge_atlas_source_visibility" in obj:
                del obj["boneforge_atlas_source_visibility"]

        bpy.data.collections.remove(coll)

        settings.has_backup = False
        settings.backup_collection_name = ""
        settings.last_bake_result = ""
        settings.total_mats_before = sum(
            _group_detected_material_count(group) for group in settings.atlas_groups
        )
        settings.rank_before = _get_rank(settings.total_mats_before)
        self.report({"INFO"}, "Reverted to original meshes")
        return {"FINISHED"}


# ─────────────────────────────────────────────────────────────────
# Panel — Zone 1 / 2 / 3 layout
# ─────────────────────────────────────────────────────────────────

class BONEFORGE_PT_vrc_w2_atlas(Panel):
    """Material Atlas Combiner — beneath VRC Cats Tools in Rig Mapping."""

    bl_label = " "
    bl_idname = "BONEFORGE_PT_vrc_w2_atlas"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text=T("Material Atlas"))

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        settings = context.scene.boneforge_atlas_settings

        # ── ZONE 1 — Status Dashboard ─────────────────────────
        status_box = layout.box()
        col = status_box.column(align=True)

        # D-Shadow declarative sentence
        sentence = _build_status_sentence(settings)
        col.label(text=sentence, icon="INFO")

        # Second line — guarantee sentence (unanimous addition S / D-Shadow)
        if settings.atlas_groups:
            guarantee = _will_not_change_sentence(settings)
            col.label(text=guarantee, icon="CHECKMARK")

        # Post-bake authority sentence (unanimous addition R)
        if settings.last_bake_result:
            result_row = col.row()
            result_row.alert = False
            col.separator()
            col.label(text=settings.last_bake_result, icon="CHECKMARK")

        # Material count + rank display
        if settings.total_mats_before > 0:
            col.separator()
            after = _projected_mat_count(settings)
            rank_before = settings.rank_before or _get_rank(settings.total_mats_before)
            rank_after = _get_rank(after)

            row = col.row(align=True)
            row.label(text=f"Now:  {settings.total_mats_before} mats  [{rank_before}]")
            row.label(text=f"→  {after} mats  [{rank_after}]")

        col.separator()
        col.label(text=T("1. Choose Target"))
        col.prop(settings, "target_scope")
        if not settings.atlas_groups:
            smart_row = col.row()
            smart_row.scale_y = 1.35
            smart_row.operator(
                "boneforge.vrc_atlas_smart_combine",
                text=T("Smart Combine Materials"),
                icon="MATERIAL",
            )
        analyze_row = col.row()
        analyze_row.enabled = not settings.has_backup
        analyze_row.operator(
            "boneforge.vrc_atlas_analyze",
            text=T("Refresh Analysis" if settings.atlas_groups else "Analyze Materials"),
            icon="VIEWZOOM",
        )
        backup_row = col.row(align=True)
        backup_row.prop(settings, "preserve_originals", text=T("Preserve Backup Duplicate"))
        if not settings.preserve_originals:
            col.label(
                text=T("Off: no Revert backup; originals are removed after atlasing"),
                icon="ERROR",
            )
        if settings.has_backup:
            accept_row = col.row(align=True)
            accept_row.alert = True
            accept_row.operator(
                "boneforge.vrc_atlas_accept",
                text=T("Accept — Delete Backup"),
                icon='CHECKMARK',
            )
            accept_row.alert = False
            revert_row = col.row(align=True)
            revert_row.operator(
                "boneforge.vrc_atlas_revert",
                text=T("Revert — Restore Originals"),
                icon="LOOP_BACK",
            )

        layout.separator()

        # ── ZONE 2 — Grouping Control ─────────────────────────
        if settings.atlas_groups:
            layout.label(text=T("2. Choose Materials and Textures"))

            # UIList
            row = layout.row()
            row.template_list(
                "BF_UL_VRC_AtlasGroups", "",
                settings, "atlas_groups",
                settings, "active_group_index",
                rows=4,
            )

            # Group list buttons
            btn_col = row.column(align=True)
            btn_col.operator("boneforge.vrc_atlas_add_group", text="", icon="ADD")
            btn_col.operator("boneforge.vrc_atlas_remove_group", text="", icon="REMOVE")

            # Expanded group detail
            idx = settings.active_group_index
            if 0 <= idx < len(settings.atlas_groups):
                active_group = settings.atlas_groups[idx]
                detail_box = layout.box()
                dcol = detail_box.column(align=True)

                if active_group.warn_overlap:
                    dcol.label(
                        text=T("[!] Overlapping UVs detected - atlas_uv will use the selected UV method"),
                        icon="ERROR",
                    )
                    dcol.label(
                        text=T("     (original UVs preserved as 'UVMap_pre_atlas')"),
                        icon="BLANK1",
                    )

                if active_group.warn_emission and settings.output_format != "EXR":
                    dcol.label(
                        text=T("[!] Emission > 1.0 detected — values will clamp in PNG/TGA"),
                        icon='ERROR',
                    )
                    dcol.label(
                        text=T("     Switch output to EXR in Advanced to preserve HDR"),
                        icon="BLANK1",
                    )

                if active_group.preserve_reason == "render_order":
                    dcol.label(
                        text=T("[i] Alpha Blend — preserved automatically for render order"),
                        icon="INFO",
                    )
                    dcol.label(
                        text=T("     Enable manually only if draw-order changes are acceptable"),
                        icon="BLANK1",
                    )
                elif active_group.render_type in ("Alpha Blend", "Emissive"):
                    dcol.label(
                        text=f"[i] {active_group.render_type} — kept in separate group",
                        icon="INFO",
                    )
                    dcol.label(
                        text=T("     Mixing with Opaque breaks VRChat render order"),
                        icon="BLANK1",
                    )

                if not active_group.warn_overlap and not active_group.warn_emission and \
                        active_group.render_type not in ("Alpha Blend", "Emissive"):
                    dcol.label(
                        text=f"{_group_enabled_material_count(active_group)} materials → 1 atlas at {active_group.resolution}px",
                        icon="CHECKMARK",
                    )

                dcol.label(text=T("Checkboxes include sources in this group."))
                if not active_group.enabled:
                    dcol.label(text=T("Group disabled: enable its checkbox to bake."), icon="INFO")
                dcol.prop(settings, "show_source_details", text=T("Source Details"))

                # Optional information and source overrides.
                if settings.show_source_details and active_group.meshes:
                    dcol.separator()
                    dcol.label(text=T("Meshes in group:"))
                    for item in active_group.meshes:
                        mesh_row = dcol.row(align=True)
                        icon = "MESH_DATA"
                        if item.has_shape_keys:
                            icon = "SHAPEKEY_DATA"
                        mesh_row.label(text=f"  {item.object_name}", icon=icon)
                        mesh_row.label(text=f"{item.mat_count} mats")
                        if item.has_shape_keys:
                            mesh_row.label(text=T("[SK]"))
                        if item.has_overlapping_uvs:
                            mesh_row.label(text=T("[UV!]"))

                if active_group.materials:
                    dcol.separator()
                    enabled_mats = _group_enabled_material_count(active_group)
                    dcol.label(
                        text=T(
                            f"Materials to combine: {enabled_mats}/{len(active_group.materials)}"
                        ),
                    )
                    _draw_source_selection(dcol, "MATERIALS")
                    dcol.template_list(
                        "BF_UL_VRC_AtlasMaterials", "",
                        active_group, "materials",
                        active_group, "active_material_index",
                        rows=5,
                    )
                    mat_idx = active_group.active_material_index
                    if settings.show_source_details and 0 <= mat_idx < len(active_group.materials):
                        mat_item = active_group.materials[mat_idx]
                        mat_detail = dcol.box()
                        mat_detail.label(text=T("Selected Material:"))
                        mat_detail.label(text=mat_item.diagnostic_status or "supported")
                        if mat_item.diagnostic_warnings:
                            mat_detail.label(text=mat_item.diagnostic_warnings, icon="INFO")
                        if mat_item.duplicate_group:
                            mat_detail.label(text=f"Duplicate/shared group: {mat_item.duplicate_group}")
                        size_row = mat_detail.row(align=True)
                        size_row.prop(mat_item, "size_override")
                        size_row.prop(mat_item, "size_preset", text="")
                        if mat_item.size_override and mat_item.size_preset == "CUSTOM":
                            custom_row = mat_detail.row(align=True)
                            custom_row.prop(mat_item, "target_width")
                            custom_row.prop(mat_item, "target_height")
                        if mat_item.has_no_images:
                            mat_detail.prop(mat_item, "fallback_size")

                if active_group.textures:
                    dcol.separator()
                    enabled_tex = _group_enabled_texture_count(active_group)
                    dcol.label(
                        text=T(
                            f"Texture images: {enabled_tex}/{len(active_group.textures)}"
                        ),
                    )
                    _draw_source_selection(dcol, "TEXTURES")
                    dcol.template_list(
                        "BF_UL_VRC_AtlasTextures", "",
                        active_group, "textures",
                        active_group, "active_texture_index",
                        rows=5,
                    )
                    tex_idx = active_group.active_texture_index
                    if settings.show_source_details and 0 <= tex_idx < len(active_group.textures):
                        tex_item = active_group.textures[tex_idx]
                        tex_detail = dcol.box()
                        tex_detail.label(text=T("Selected Texture:"))
                        tex_detail.prop(tex_item, "role")
                        tex_detail.label(text=f"Expected: {role_color_space(tex_item.role)}")
                        if tex_item.diagnostic_warnings:
                            tex_detail.label(text=tex_item.diagnostic_warnings, icon="INFO")
                        if tex_item.duplicate_group:
                            tex_detail.label(text=f"Duplicate source group: {tex_item.duplicate_group}")

            # Permanent transparency note (unanimous addition S)
            layout.separator()
            note_row = layout.row()
            note_row.label(
                text=T("Transparent / emissive materials kept in separate groups by default."),
                icon="INFO",
            )

            layout.separator()

            # Primary action
            layout.label(text=T("3. Bake and Review"))
            bake_row = layout.row()
            bake_row.enabled = not settings.has_backup
            bake_row.scale_y = 1.4
            bake_row.operator("boneforge.vrc_atlas_bake", text=T("Bake Checked Sources"), icon="RENDER_STILL")

        # ── ZONE 3 — Advanced Options ─────────────────────────
        adv_box = layout.box()
        adv_header = adv_box.row()
        adv_header.prop(
            settings, "show_advanced",
            text=T("Advanced Options"),
            icon="TRIA_DOWN" if settings.show_advanced else "TRIA_RIGHT",
            emboss=False,
        )

        if settings.show_advanced:
            adv_col = adv_box.column(align=True)

            adv_col.label(text=T("Workflow:"))
            adv_col.prop(settings, "auto_analyze_before_bake")
            adv_col.prop(settings, "debug_enabled")
            adv_col.operator("boneforge.vrc_atlas_copy_debug", text=T("Copy Debug Report"), icon="COPYDOWN")
            adv_col.separator()

            adv_col.label(text=T("Bake Passes:"))
            adv_col.prop(settings, "bake_albedo")
            adv_col.prop(settings, "bake_normal")
            emission_row = adv_col.row()
            emission_row.prop(settings, "bake_emission")
            adv_col.prop(settings, "bake_metallic")
            adv_col.prop(settings, "bake_roughness")
            adv_col.prop(settings, "channel_pack_orm")
            if settings.channel_pack_orm:
                adv_col.prop(settings, "allow_unknown_channel_pack_roles")
                adv_col.label(text=T("ORM is blocked until metallic packing is verified."), icon="INFO")
            if settings.bake_metallic:
                adv_col.label(text=T("Metallic pass is preflight-blocked in this build."), icon="ERROR")

            adv_col.separator()
            adv_col.label(text=T("UV Packing:"))
            adv_col.prop(settings, "packing_preset")
            adv_col.prop(settings, "uv_margin")
            adv_col.prop(settings, "atlas_padding_pixels")
            adv_col.prop(settings, "pixel_art_no_bleed")
            adv_col.prop(settings, "preserve_island_orientation")
            adv_col.prop(settings, "keep_source_uv_maps")
            adv_col.prop(settings, "pack_method")
            if method_uses_seed(settings.pack_method):
                adv_col.prop(settings, "uv_random_seed")
                adv_col.prop(settings, "uv_rotation_step")

            adv_col.separator()
            adv_col.label(text=T("Output:"))
            adv_col.prop(settings, "color_fallback_size", text=T("Fallback Size"))
            adv_col.prop(settings, "output_format", text=T("Format Output"))
            adv_col.prop(settings, "output_material_type", text=T("Material Output Type"))
            adv_col.prop(settings, "output_surface_shader", text=T("Surface Output"))
            if settings.output_format == "EXR":
                adv_col.label(
                    text=T("EXR preserves HDR emission — use for glow accessories"),
                    icon="INFO",
                )
            adv_col.prop(settings, "output_path", text=T("Path Output"))



# ─────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────

_classes = (
    BF_AtlasMeshItem,
    BF_AtlasMaterialItem,
    BF_AtlasTextureItem,
    BF_AtlasGroup,
    BF_AtlasSettings,
    BF_UL_VRC_AtlasGroups,
    BF_UL_VRC_AtlasMaterials,
    BF_UL_VRC_AtlasTextures,
    BF_OT_VRC_AtlasSelectSources,
    BONEFORGE_MT_atlas_selection,
    BF_OT_VRC_AtlasAnalyze,
    BF_OT_VRC_AtlasAddGroup,
    BF_OT_VRC_AtlasRemoveGroup,
    BF_OT_VRC_AtlasSmartCombine,
    BF_OT_VRC_AtlasCopyDebugReport,
    BF_OT_VRC_AtlasBake,
    BF_OT_VRC_AtlasAccept,
    BF_OT_VRC_AtlasRevert,
)


def register():
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft Atlas] Failed to register {cls.__name__}: {e}")

    bpy.types.VIEW3D_MT_object.append(_atlas_selection_menu)

    bpy.types.Scene.boneforge_atlas_settings = bpy.props.PointerProperty(
        type=BF_AtlasSettings
    )


def unregister():
    bpy.types.VIEW3D_MT_object.remove(_atlas_selection_menu)
    if hasattr(bpy.types.Scene, "boneforge_atlas_settings"):
        del bpy.types.Scene.boneforge_atlas_settings

    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft Atlas] Failed to unregister {cls.__name__}: {e}")
