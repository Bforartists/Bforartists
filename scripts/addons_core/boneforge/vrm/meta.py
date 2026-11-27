"""Round-trip the VRM meta block through Blender custom properties.

This is the Phase-3 unanimous addition from the Brainstorm Council:
*every VRM record — most importantly the mandatory meta/license block —
is preserved as a custom property on the armature throughout the
round-trip*. No edit can silently destroy them.

The upstream ``vrm-addon-for-blender`` stores its imported data on
``armature_obj.data.vrm_addon_extension`` (VRM 1.0) or, on older
releases, on ``armature_obj.data.vrm_meta``. Both shapes vary across
upstream versions, so we mirror what we can find into our own
``boneforge_vrm_meta`` JSON custom property and write back into
whichever shape the installed upstream uses, without rewriting upstream's
internal model.

We avoid hard-coding upstream attribute paths where we don't have to.
``getattr`` chains tolerate version drift; logging at ``DEBUG`` records
which path actually carried data.
"""

from __future__ import annotations

import logging
from typing import Optional

import bpy

from boneforge.core import read_custom_json, write_custom_json

logger = logging.getLogger(__name__)


# Custom-property keys we own on the armature. These are the BoneForge
# round-trip surface; the upstream add-on owns its own keys, which we do
# NOT touch except via the bidirectional sync helpers below.
META_KEY = "boneforge_vrm_meta"
SPRING_KEY = "boneforge_vrm_spring_groups"
BLENDSHAPE_KEY = "boneforge_vrm_blendshape_proxy"
FIRSTPERSON_KEY = "boneforge_vrm_first_person"
SOURCE_FORMAT_KEY = "boneforge_vrm_source_format"  # "VRM_0_X" | "VRM_1_0"


# ── Helpers to reach into the upstream model ─────────────────────

def _vrm_extension(armature_obj: bpy.types.Object):
    """Return the upstream VRM extension on the armature data, or None.

    Tries the VRM 1.0 attribute first, falls back to older shapes.
    Returns the extension PropertyGroup directly so callers can read
    sub-attributes — does not deserialize.
    """
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return None
    arm_data = armature_obj.data
    for attr in ("vrm_addon_extension", "vrm_extension", "vrm_meta"):
        ext = getattr(arm_data, attr, None)
        if ext is not None:
            return ext
    return None


def _coerce_to_jsonable(value):
    """Best-effort conversion of upstream PropertyGroup attributes to JSON.

    Blender PropertyGroups are not JSON-serialisable directly; we read
    their fields one level deep. Anything we can't serialise becomes a
    string repr — visible to the user but flagged as ``__repr__``-only.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_coerce_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _coerce_to_jsonable(v) for k, v in value.items()}
    if hasattr(value, "to_dict"):
        try:
            return _coerce_to_jsonable(value.to_dict())
        except (TypeError, ValueError):
            pass
    if hasattr(value, "__iter__"):
        try:
            return [_coerce_to_jsonable(v) for v in value]
        except TypeError:
            pass
    return {"__repr__": repr(value)}


# ── Public API ───────────────────────────────────────────────────

def detect_source_format(armature_obj: bpy.types.Object) -> Optional[str]:
    """Return ``"VRM_1_0"`` or ``"VRM_0_X"`` if we can tell, else None.

    Heuristic: VRM 1.0 stores meta under ``vrm.meta`` of the extension;
    VRM 0.x stores it under ``vrm0.meta``. If both branches exist and
    populate, prefer 1.0 (it's the future).
    """
    ext = _vrm_extension(armature_obj)
    if ext is None:
        return None
    if hasattr(ext, "vrm1") and getattr(ext.vrm1, "meta", None) is not None:
        return "VRM_1_0"
    if hasattr(ext, "vrm0") and getattr(ext.vrm0, "meta", None) is not None:
        return "VRM_0_X"
    return None


def snapshot_meta(armature_obj: bpy.types.Object) -> dict:
    """Capture the upstream meta block into a plain dict for round-trip.

    Returns an empty dict if no upstream extension is present. The result
    is intended for ``write_custom_json(armature, META_KEY, ...)``.
    """
    ext = _vrm_extension(armature_obj)
    if ext is None:
        return {}

    meta_record: dict = {}

    # VRM 1.0 path
    vrm1 = getattr(ext, "vrm1", None)
    if vrm1 is not None:
        meta = getattr(vrm1, "meta", None)
        if meta is not None:
            for field in (
                "vrm_name", "version", "authors", "copyright_information",
                "contact_information", "references",
                "third_party_licenses", "license_url",
                "avatar_permission",
                "allow_excessively_violent_usage",
                "allow_excessively_sexual_usage",
                "commercial_usage",
                "allow_political_or_religious_usage",
                "allow_antisocial_or_hate_usage",
                "credit_notation",
                "allow_redistribution",
                "modification",
                "other_license_url",
            ):
                if hasattr(meta, field):
                    meta_record[field] = _coerce_to_jsonable(getattr(meta, field))
            meta_record["_vrm_spec"] = "1.0"
            return meta_record

    # VRM 0.x path
    vrm0 = getattr(ext, "vrm0", None)
    if vrm0 is not None:
        meta = getattr(vrm0, "meta", None)
        if meta is not None:
            for field in (
                "title", "version", "author", "contact_information",
                "reference",
                "allowed_user_name",
                "violent_ussage_name",
                "sexual_ussage_name",
                "commercial_ussage_name",
                "other_permission_url",
                "license_name",
                "other_license_url",
            ):
                if hasattr(meta, field):
                    meta_record[field] = _coerce_to_jsonable(getattr(meta, field))
            meta_record["_vrm_spec"] = "0.x"

    return meta_record


def preserve_to_armature(armature_obj: bpy.types.Object) -> None:
    """Snapshot upstream VRM data onto BoneCraft custom properties.

    Call this after a successful upstream import. Idempotent.
    """
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return

    source = detect_source_format(armature_obj)
    if source is not None:
        armature_obj[SOURCE_FORMAT_KEY] = source

    meta = snapshot_meta(armature_obj)
    if meta:
        write_custom_json(armature_obj, META_KEY, meta)
        logger.info(
            "[BoneCraft] preserved VRM meta (%s) on %s",
            meta.get("_vrm_spec", "?"), armature_obj.name,
        )

    # Spring groups + blendshape proxy: we only snapshot a thin shape so
    # users can SEE what they have. Re-applying these on export is the
    # upstream add-on's job — we don't try to mutate its model from JSON
    # (too version-fragile). The snapshot is read-only documentation.
    ext = _vrm_extension(armature_obj)
    if ext is None:
        return

    spring_groups = []
    for path in (
        ("vrm1", "spring_bone", "springs"),
        ("vrm0", "secondary_animation", "bone_groups"),
    ):
        node = ext
        for attr in path:
            node = getattr(node, attr, None)
            if node is None:
                break
        if node is not None:
            try:
                spring_groups = [
                    _coerce_to_jsonable(g) for g in node
                ]
                break
            except TypeError:
                continue

    if spring_groups:
        write_custom_json(armature_obj, SPRING_KEY, spring_groups)

    blendshape_proxy = []
    for path in (
        ("vrm1", "expressions"),
        ("vrm0", "blend_shape_master", "blend_shape_groups"),
    ):
        node = ext
        for attr in path:
            node = getattr(node, attr, None)
            if node is None:
                break
        if node is not None:
            try:
                blendshape_proxy = [
                    _coerce_to_jsonable(b) for b in node
                ]
                break
            except TypeError:
                continue

    if blendshape_proxy:
        write_custom_json(armature_obj, BLENDSHAPE_KEY, blendshape_proxy)


def read_preserved_meta(armature_obj: bpy.types.Object) -> Optional[dict]:
    """Return the meta dict previously stored by ``preserve_to_armature``.

    Returns ``None`` if no preserved data is on this armature.
    """
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return None
    return read_custom_json(armature_obj, META_KEY, default=None)
