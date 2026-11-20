"""Material atlas quality helpers.

This module is intentionally independent from bpy so the classification and
preflight rules can be tested outside Blender, then wired into material_atlas.py
after any UV-tooling integration work has settled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


ROLE_ALBEDO = "ALBEDO"
ROLE_NORMAL = "NORMAL"
ROLE_EMISSION = "EMISSION"
ROLE_METALLIC = "METALLIC"
ROLE_ROUGHNESS = "ROUGHNESS"
ROLE_SPECULAR = "SPECULAR"
ROLE_ALPHA = "ALPHA"
ROLE_AO = "AMBIENT_OCCLUSION"
ROLE_UNKNOWN = "UNKNOWN"

ROLE_LABELS = {
    ROLE_ALBEDO: "Albedo / Base Color",
    ROLE_NORMAL: "Normal",
    ROLE_EMISSION: "Emission",
    ROLE_METALLIC: "Metallic",
    ROLE_ROUGHNESS: "Roughness",
    ROLE_SPECULAR: "Specular",
    ROLE_ALPHA: "Alpha",
    ROLE_AO: "Ambient Occlusion",
    ROLE_UNKNOWN: "Unknown",
}

PASS_SUFFIXES = {
    ROLE_ALBEDO: "_albedo",
    ROLE_NORMAL: "_normal",
    ROLE_EMISSION: "_emission",
    ROLE_METALLIC: "_metallic",
    ROLE_ROUGHNESS: "_roughness",
}

PASS_COLOR_SPACE = {
    ROLE_ALBEDO: "sRGB",
    ROLE_EMISSION: "sRGB",
    ROLE_NORMAL: "Non-Color",
    ROLE_METALLIC: "Non-Color",
    ROLE_ROUGHNESS: "Non-Color",
    ROLE_SPECULAR: "Non-Color",
    ROLE_ALPHA: "Non-Color",
    ROLE_AO: "Non-Color",
    ROLE_UNKNOWN: "Unknown",
}

SIZE_PRESETS = ("SOURCE", "512", "1024", "2048", "4096", "CUSTOM")
MIN_TEXTURE_SIZE = 16
MAX_TEXTURE_SIZE = 8192

PACKING_PRESETS = {
    "SAFE_DEFAULT": {
        "label": "Safe Default",
        "uv_margin": 0.02,
        "padding_pixels": 4,
        "pixel_art_no_bleed": False,
        "preserve_island_orientation": True,
        "deterministic_seed": 1337,
    },
    "TIGHT": {
        "label": "Tight",
        "uv_margin": 0.008,
        "padding_pixels": 2,
        "pixel_art_no_bleed": False,
        "preserve_island_orientation": True,
        "deterministic_seed": 1337,
    },
    "PIXEL_ART": {
        "label": "Pixel Art",
        "uv_margin": 0.004,
        "padding_pixels": 1,
        "pixel_art_no_bleed": True,
        "preserve_island_orientation": True,
        "deterministic_seed": 1337,
    },
    "HIGH_MARGIN": {
        "label": "High Margin",
        "uv_margin": 0.04,
        "padding_pixels": 16,
        "pixel_art_no_bleed": False,
        "preserve_island_orientation": True,
        "deterministic_seed": 1337,
    },
}

CHANNEL_PACK_CONVENTION = {
    "R": {"role": ROLE_METALLIC, "fallback": 0.0, "label": "Metallic"},
    "G": {"role": ROLE_ROUGHNESS, "fallback": 1.0, "label": "Roughness"},
    "B": {"role": ROLE_AO, "fallback": 0.0, "label": "Ambient Occlusion or unused black"},
    "A": {"role": ROLE_ALPHA, "fallback": 1.0, "label": "Alpha or unused opaque"},
}


@dataclass(frozen=True)
class TextureSource:
    """Serializable source texture description used by diagnostics."""

    material_name: str = ""
    node_name: str = ""
    image_name: str = ""
    image_path: str = ""
    width: int = 0
    height: int = 0
    colorspace: str = ""
    packed: bool = False
    missing: bool = False
    socket_name: str = ""
    output_name: str = ""
    via_node_type: str = ""
    role: str = ROLE_UNKNOWN
    enabled: bool = True


@dataclass(frozen=True)
class MaterialSource:
    """Serializable material description used by diagnostics."""

    material_name: str
    object_name: str = ""
    slot_index: int = 0
    shader_type: str = ""
    use_nodes: bool = True
    has_node_tree: bool = True
    textures: Sequence[TextureSource] = field(default_factory=tuple)
    alpha_mode: str = ""
    blend_method: str = ""
    emission_strength: float = 0.0
    warnings: Sequence[str] = field(default_factory=tuple)


def _clean(value: object) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _field(source: Mapping[str, object] | object, *names: str, default: object = "") -> object:
    for name in names:
        if isinstance(source, Mapping) and name in source:
            return source[name]
        if not isinstance(source, Mapping) and hasattr(source, name):
            return getattr(source, name)
    return default


def _as_texture(source: TextureSource | Mapping[str, object] | object) -> TextureSource:
    if isinstance(source, TextureSource):
        return source
    return TextureSource(
        material_name=str(_field(source, "material_name", "material") or ""),
        node_name=str(_field(source, "node_name", "node") or ""),
        image_name=str(_field(source, "image_name", "image") or ""),
        image_path=str(_field(source, "image_path", "path") or ""),
        width=int(_field(source, "width", default=0) or 0),
        height=int(_field(source, "height", default=0) or 0),
        colorspace=str(_field(source, "colorspace", "color_space") or ""),
        packed=bool(_field(source, "packed", default=False)),
        missing=bool(_field(source, "missing", default=False)),
        socket_name=str(_field(source, "socket_name", "socket") or ""),
        output_name=str(_field(source, "output_name", "output") or ""),
        via_node_type=str(_field(source, "via_node_type", "via_node") or ""),
        role=str(_field(source, "role", default=ROLE_UNKNOWN) or ROLE_UNKNOWN),
        enabled=bool(_field(source, "enabled", default=True)),
    )


def _as_material(source: MaterialSource | Mapping[str, object] | object) -> MaterialSource:
    if isinstance(source, MaterialSource):
        return source
    return MaterialSource(
        material_name=str(_field(source, "material_name", "material", "name") or ""),
        object_name=str(_field(source, "object_name", "object") or ""),
        slot_index=int(_field(source, "slot_index", "slot", default=0) or 0),
        shader_type=str(_field(source, "shader_type", "shader") or ""),
        use_nodes=bool(_field(source, "use_nodes", default=True)),
        has_node_tree=bool(_field(source, "has_node_tree", default=True)),
        textures=tuple(_as_texture(t) for t in (_field(source, "textures", default=()) or ())),
        alpha_mode=str(_field(source, "alpha_mode") or ""),
        blend_method=str(_field(source, "blend_method") or ""),
        emission_strength=float(_field(source, "emission_strength", default=0.0) or 0.0),
        warnings=tuple(str(w) for w in (_field(source, "warnings", default=()) or ())),
    )


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, ROLE_LABELS[ROLE_UNKNOWN])


def role_color_space(role: str) -> str:
    return PASS_COLOR_SPACE.get(role, "Unknown")


def detect_texture_role(
    socket_name: str = "",
    *,
    node_name: str = "",
    output_name: str = "",
    via_node_type: str = "",
) -> str:
    """Infer a texture role from a shader socket/link description."""

    socket_key = _clean(socket_name)
    via_key = _clean(via_node_type)
    node_key = _clean(node_name)
    output_key = _clean(output_name)
    combined = " ".join((socket_key, via_key, node_key, output_key))

    if "alpha" in combined or "opacity" in combined or "transparent" in combined:
        return ROLE_ALPHA
    if "normal" in combined or "bump" in combined:
        return ROLE_NORMAL
    if "emission" in combined or "emissive" in combined:
        return ROLE_EMISSION
    if "metallic" in combined or "metalness" in combined:
        return ROLE_METALLIC
    if "roughness" in combined or "rough" in combined:
        return ROLE_ROUGHNESS
    if "specular" in combined or "spec" in combined:
        return ROLE_SPECULAR
    if "ambientocclusion" in combined or socket_key == "ao" or "occlusion" in combined:
        return ROLE_AO
    if (
        "basecolor" in combined
        or "diffuse" in combined
        or socket_key in {"color", "basecolour", "basecol"}
    ):
        return ROLE_ALBEDO
    return ROLE_UNKNOWN


def texture_with_detected_role(source: TextureSource | Mapping[str, object] | object) -> TextureSource:
    tex = _as_texture(source)
    role = tex.role if tex.role and tex.role != ROLE_UNKNOWN else detect_texture_role(
        tex.socket_name,
        node_name=tex.node_name,
        output_name=tex.output_name,
        via_node_type=tex.via_node_type,
    )
    return TextureSource(
        material_name=tex.material_name,
        node_name=tex.node_name,
        image_name=tex.image_name,
        image_path=tex.image_path,
        width=tex.width,
        height=tex.height,
        colorspace=tex.colorspace,
        packed=tex.packed,
        missing=tex.missing,
        socket_name=tex.socket_name,
        output_name=tex.output_name,
        via_node_type=tex.via_node_type,
        role=role,
        enabled=tex.enabled,
    )


def _is_non_color_name(colorspace: str) -> bool:
    return _clean(colorspace) in {"noncolor", "noncolour", "raw", "linear"}


def diagnose_texture(source: TextureSource | Mapping[str, object] | object) -> dict[str, object]:
    tex = texture_with_detected_role(source)
    warnings: list[str] = []

    if tex.missing or not tex.image_name:
        warnings.append("missing image")
    if not tex.packed and not tex.image_path:
        warnings.append("missing image path")
    if tex.width <= 0 or tex.height <= 0:
        warnings.append("missing or invalid dimensions")
    if tex.packed:
        warnings.append("packed image")

    expected_space = role_color_space(tex.role)
    if expected_space == "Non-Color" and tex.colorspace and not _is_non_color_name(tex.colorspace):
        warnings.append(f"{role_label(tex.role)} should usually use Non-Color data")
    if expected_space == "sRGB" and tex.colorspace and _is_non_color_name(tex.colorspace):
        warnings.append(f"{role_label(tex.role)} should usually use color data")

    status = "ok" if not warnings else "warning"
    if "missing image" in warnings:
        status = "missing_image"

    return {
        "status": status,
        "role": tex.role,
        "role_label": role_label(tex.role),
        "colorspace_expected": expected_space,
        "warnings": warnings,
    }


def _shader_supported_state(shader_type: str) -> str:
    shader = _clean(shader_type)
    if not shader:
        return "supported_with_warnings"
    if any(key in shader for key in ("principled", "bsdfprincipled", "diffuse", "mtoon", "vrm", "mmd")):
        return "supported_directly"
    if any(key in shader for key in ("transparent", "emission", "glass", "toon")):
        return "supported_with_warnings"
    return "unsupported_shader"


def diagnose_material(source: MaterialSource | Mapping[str, object] | object) -> dict[str, object]:
    mat = _as_material(source)
    textures = [texture_with_detected_role(t) for t in mat.textures]
    texture_reports = [diagnose_texture(t) for t in textures]
    warnings = list(mat.warnings)

    if not mat.use_nodes or not mat.has_node_tree:
        warnings.append("material has no node tree; fallback color bake only")

    shader_state = _shader_supported_state(mat.shader_type)
    if shader_state == "unsupported_shader":
        warnings.append(f"unsupported shader: {mat.shader_type or 'unknown'}")
    elif shader_state == "supported_with_warnings":
        warnings.append(f"shader may require visual verification: {mat.shader_type or 'unknown'}")

    if not textures:
        warnings.append("no image texture nodes; use color-only fallback size")

    color_spaces = sorted({t.colorspace for t in textures if t.colorspace})
    if len(color_spaces) > 1:
        warnings.append("mixed color space")

    if any(report["status"] == "missing_image" for report in texture_reports):
        warnings.append("one or more image nodes are missing an image")
    if any("missing image path" in report["warnings"] for report in texture_reports):
        warnings.append("one or more image textures have no external path")
    if any("packed image" in report["warnings"] for report in texture_reports):
        warnings.append("one or more images are packed into the blend file")
    if any(t.role == ROLE_UNKNOWN for t in textures):
        warnings.append("one or more texture roles are unknown")

    alpha_like = _clean(mat.alpha_mode or mat.blend_method) not in {"", "opaque"}
    if alpha_like or any(t.role == ROLE_ALPHA for t in textures):
        warnings.append("likely alpha/special-case material")
    if mat.emission_strength > 0.0 or any(t.role == ROLE_EMISSION for t in textures):
        warnings.append("likely emissive/special-case material")

    if not textures:
        status = "no_image_color_only"
    elif shader_state == "unsupported_shader":
        status = "unsupported_shader"
    elif warnings:
        status = "supported_with_warnings"
    else:
        status = "supported_directly"

    return {
        "material_name": mat.material_name,
        "status": status,
        "shader_state": shader_state,
        "texture_count": len(textures),
        "roles": sorted({t.role for t in textures}),
        "warnings": sorted(dict.fromkeys(warnings)),
        "textures": texture_reports,
    }


def duplicate_texture_key(source: TextureSource | Mapping[str, object] | object) -> tuple[str, str, int, int, str, bool]:
    tex = texture_with_detected_role(source)
    identity = _clean(tex.image_path) or f"image:{_clean(tex.image_name)}"
    return (tex.role, identity, tex.width, tex.height, _clean(tex.colorspace), tex.packed)


def role_is_safe_for_duplicate_suggestion(role: str) -> bool:
    return role not in {ROLE_ALPHA, ROLE_EMISSION, ROLE_UNKNOWN}


def find_duplicate_texture_groups(
    sources: Iterable[TextureSource | Mapping[str, object] | object],
    *,
    include_special_cases: bool = False,
) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, int, int, str, bool], list[TextureSource]] = {}
    for source in sources:
        tex = texture_with_detected_role(source)
        if not tex.enabled:
            continue
        if not include_special_cases and not role_is_safe_for_duplicate_suggestion(tex.role):
            continue
        groups.setdefault(duplicate_texture_key(tex), []).append(tex)

    duplicates = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        duplicates.append({
            "key": key,
            "role": key[0],
            "canonical": items[0].image_name or items[0].image_path,
            "members": [item.image_name or item.image_path for item in items],
            "materials": sorted({item.material_name for item in items if item.material_name}),
        })
    return duplicates


def find_shared_material_groups(
    sources: Iterable[MaterialSource | Mapping[str, object] | object],
) -> list[dict[str, object]]:
    buckets: dict[tuple[str, str, int, int, str, bool], list[str]] = {}
    for source in sources:
        report = diagnose_material(source)
        if report["status"] == "unsupported_shader":
            continue
        mat = _as_material(source)
        primary = next(
            (t for t in (texture_with_detected_role(t) for t in mat.textures) if t.role == ROLE_ALBEDO),
            None,
        )
        if primary is None:
            continue
        buckets.setdefault(duplicate_texture_key(primary), []).append(mat.material_name)

    return [
        {"key": key, "role": key[0], "materials": sorted(names), "canonical": sorted(names)[0]}
        for key, names in buckets.items()
        if len(set(names)) > 1
    ]


def is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def validate_texture_size(width: int, height: int) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if width < MIN_TEXTURE_SIZE or height < MIN_TEXTURE_SIZE:
        return False, [f"size must be at least {MIN_TEXTURE_SIZE}px"]
    if width > MAX_TEXTURE_SIZE or height > MAX_TEXTURE_SIZE:
        return False, [f"size must be no larger than {MAX_TEXTURE_SIZE}px"]
    if not is_power_of_two(width) or not is_power_of_two(height):
        warnings.append("non-power-of-two size; verify target engine support")
    return True, warnings


def resolve_size_preset(
    preset: str,
    *,
    source_width: int = 0,
    source_height: int = 0,
    custom_width: int = 1024,
    custom_height: int = 1024,
    fallback_size: int = 512,
) -> dict[str, object]:
    preset_key = str(preset or "SOURCE").upper()
    if preset_key == "SOURCE":
        width = source_width if source_width > 0 else fallback_size
        height = source_height if source_height > 0 else fallback_size
    elif preset_key == "CUSTOM":
        width = custom_width
        height = custom_height
    elif preset_key in {"512", "1024", "2048", "4096"}:
        width = height = int(preset_key)
    else:
        raise ValueError(f"Unknown texture size preset: {preset}")

    valid, warnings = validate_texture_size(int(width), int(height))
    return {
        "preset": preset_key,
        "width": int(width),
        "height": int(height),
        "valid": valid,
        "warnings": warnings,
    }


def packing_preset_settings(preset: str) -> dict[str, object]:
    preset_key = str(preset or "SAFE_DEFAULT").upper()
    if preset_key not in PACKING_PRESETS:
        raise ValueError(f"Unknown atlas packing preset: {preset}")
    settings = dict(PACKING_PRESETS[preset_key])
    settings["preset"] = preset_key
    return settings


def build_multipass_output_plan(
    enabled_passes: Iterable[str],
    textures: Iterable[TextureSource | Mapping[str, object] | object],
    *,
    base_name: str = "atlas",
    allow_unknown_roles: bool = False,
) -> dict[str, object]:
    wanted = {str(role).upper() for role in enabled_passes}
    sources = [texture_with_detected_role(t) for t in textures if _as_texture(t).enabled]
    by_role: dict[str, list[TextureSource]] = {}
    for tex in sources:
        by_role.setdefault(tex.role, []).append(tex)

    outputs = []
    skipped = []
    errors = []

    if ROLE_UNKNOWN in by_role and not allow_unknown_roles and len(wanted - {ROLE_ALBEDO}) > 0:
        errors.append("Unknown texture roles must be labeled or disabled before multi-pass bake.")

    for role in (ROLE_ALBEDO, ROLE_NORMAL, ROLE_EMISSION, ROLE_METALLIC, ROLE_ROUGHNESS):
        if role not in wanted:
            continue
        matches = by_role.get(role, [])
        if not matches and role != ROLE_ALBEDO:
            skipped.append({"role": role, "reason": f"No {role_label(role)} source textures found"})
            continue
        outputs.append({
            "role": role,
            "label": role_label(role),
            "image_name": f"{base_name}{PASS_SUFFIXES[role]}",
            "colorspace": role_color_space(role),
            "source_count": len(matches),
            "fallback": role == ROLE_ALBEDO and not matches,
        })

    return {"outputs": outputs, "skipped": skipped, "errors": errors}


def build_channel_pack_plan(
    textures: Iterable[TextureSource | Mapping[str, object] | object],
    *,
    base_name: str = "atlas",
    allow_unknown_roles: bool = False,
) -> dict[str, object]:
    sources = [texture_with_detected_role(t) for t in textures if _as_texture(t).enabled]
    errors = []
    if any(t.role == ROLE_UNKNOWN for t in sources) and not allow_unknown_roles:
        errors.append("Unknown texture roles must be labeled or disabled before channel packing.")

    role_sources: dict[str, list[TextureSource]] = {}
    for tex in sources:
        role_sources.setdefault(tex.role, []).append(tex)

    channels = {}
    for channel, spec in CHANNEL_PACK_CONVENTION.items():
        role = spec["role"]
        matches = role_sources.get(role, [])
        channels[channel] = {
            "role": role,
            "label": spec["label"],
            "source": (matches[0].image_name or matches[0].image_path) if matches else None,
            "fallback": spec["fallback"] if not matches else None,
        }

    return {
        "image_name": f"{base_name}_orm",
        "colorspace": "Non-Color",
        "channels": channels,
        "errors": errors,
    }


def format_quality_debug_report(
    materials: Iterable[MaterialSource | Mapping[str, object] | object],
    textures: Iterable[TextureSource | Mapping[str, object] | object],
    *,
    size_preset: str = "SOURCE",
    packing_preset: str = "SAFE_DEFAULT",
    enabled_passes: Iterable[str] = (ROLE_ALBEDO,),
    channel_pack: bool = False,
) -> str:
    material_reports = [diagnose_material(mat) for mat in materials]
    texture_sources = [texture_with_detected_role(tex) for tex in textures]
    texture_reports = [diagnose_texture(tex) for tex in texture_sources]
    duplicates = find_duplicate_texture_groups(texture_sources)
    pass_plan = build_multipass_output_plan(enabled_passes, texture_sources)
    packing = packing_preset_settings(packing_preset)

    lines = [
        "Material Combiner Quality Report",
        f"Materials scanned: {len(material_reports)}",
        f"Textures scanned: {len(texture_reports)}",
        f"Size preset: {size_preset}",
        f"Packing preset: {packing['label']} (margin={packing['uv_margin']}, padding={packing['padding_pixels']}px)",
        "",
        "Material diagnostics:",
    ]
    for report in material_reports:
        warning_text = "; ".join(report["warnings"]) if report["warnings"] else "none"
        lines.append(f"- {report['material_name']}: {report['status']} | warnings: {warning_text}")

    lines.append("")
    lines.append("Texture roles:")
    for tex, report in zip(texture_sources, texture_reports):
        warning_text = "; ".join(report["warnings"]) if report["warnings"] else "none"
        lines.append(f"- {tex.image_name or '<missing>'}: {report['role_label']} | warnings: {warning_text}")

    lines.append("")
    lines.append(f"Duplicate texture groups: {len(duplicates)}")
    for group in duplicates:
        lines.append(f"- {role_label(group['role'])}: {', '.join(group['members'])}")

    lines.append("")
    lines.append("Pass outputs:")
    for output in pass_plan["outputs"]:
        lines.append(f"- {output['image_name']} ({output['label']}, {output['colorspace']})")
    for skipped in pass_plan["skipped"]:
        lines.append(f"- skipped {role_label(skipped['role'])}: {skipped['reason']}")
    for error in pass_plan["errors"]:
        lines.append(f"- error: {error}")

    if channel_pack:
        channel_plan = build_channel_pack_plan(texture_sources)
        lines.append("")
        lines.append(f"Channel-packed output: {channel_plan['image_name']} ({channel_plan['colorspace']})")
        for channel, info in channel_plan["channels"].items():
            source = info["source"] if info["source"] is not None else f"fallback {info['fallback']}"
            lines.append(f"- {channel}: {info['label']} -> {source}")
        for error in channel_plan["errors"]:
            lines.append(f"- error: {error}")

    return "\n".join(lines)
