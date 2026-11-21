# --- ORCHESTRATION AND RECOVERY ---
"""Preset export/import for orchestration workspace profiles and tool presets.

Handles serialization of addon settings to JSON files for sharing between
workstations, team standardization, and backup/restore workflows.

Public API:
    export_preset(filepath, data_dict)   — write a preset JSON file
    import_preset(filepath)              — read and return preset dict
    export_workspace_profile(context, filepath)  — full workspace export
    import_workspace_profile(context, filepath)  — full workspace import
    get_preset_directory()               — default preset folder path
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import bpy

from .logging import get_logger

__all__ = [
    "get_preset_directory",
    "export_preset",
    "import_preset",
    "collect_scene_settings",
    "apply_scene_settings",
    "export_workspace_profile",
    "import_workspace_profile",
]

_log = get_logger(__name__)

# Preset file version for forward compatibility
_PRESET_VERSION = 1
_PRESET_MAGIC = "anim_assist_preset"


def get_preset_directory() -> Path:
    """Return the default preset directory (next to the addon folder)."""
    addon_dir = Path(__file__).parent.parent
    preset_dir = addon_dir / "presets"
    preset_dir.mkdir(exist_ok=True)
    return preset_dir


def export_preset(filepath: str, data_dict: dict[str, Any]) -> bool:
    """Write a preset dict to a JSON file. Returns True on success."""
    envelope = {
        "magic": _PRESET_MAGIC,
        "version": _PRESET_VERSION,
        "created": time.time(),
        "data": data_dict,
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
        _log.info("Preset exported: %s", filepath)
        return True
    except Exception:
        _log.exception("Failed to export preset: %s", filepath)
        return False


def import_preset(filepath: str) -> dict[str, Any] | None:
    """Read a preset JSON file and return its data dict, or None on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            envelope = json.load(f)
    except Exception:
        _log.exception("Failed to read preset: %s", filepath)
        return None

    if not isinstance(envelope, dict):
        _log.error("Preset is not a dict: %s", filepath)
        return None
    if envelope.get("magic") != _PRESET_MAGIC:
        _log.error("Not an Anim Assist preset: %s", filepath)
        return None

    version = envelope.get("version", 0)
    if version > _PRESET_VERSION:
        _log.warning(
            "Preset version %d > current %d, some data may be lost",
            version, _PRESET_VERSION,
        )

    return envelope.get("data")


def collect_scene_settings(context: bpy.types.Context) -> dict[str, Any]:
    """Serialises every module's PropertyGroup into a plain dict for preset export or workspace profile snapshots."""
    scene = context.scene
    settings: dict[str, Any] = {}

    # Collect each module group's properties if present
    for attr in ("anim_assist", "anim_assist_p3", "anim_assist_p4",
                 "anim_assist_p5", "anim_assist_p6", "anim_assist_p7",
                 "anim_assist_p8", "anim_assist_p9", "anim_assist_p10"):
        pg = getattr(scene, attr, None)
        if pg is None:
            continue
        try:
            props: dict[str, Any] = {}
            for prop_name in pg.bl_rna.properties.keys():
                if prop_name == "rna_type":
                    continue
                try:
                    val = getattr(pg, prop_name)
                    # Only serialize simple types
                    if isinstance(val, (bool, int, float, str)):
                        props[prop_name] = val
                except Exception:  # noqa: BLE001
                    pass  # Property may be non-readable (e.g. PointerProperty); skip.
            if props:
                settings[attr] = props
        except Exception:
            _log.debug("Could not collect %s", attr, exc_info=True)

    return settings


def apply_scene_settings(context: bpy.types.Context, settings: dict[str, Any]) -> int:
    """Apply collected settings back to scene property groups.

    Returns the number of properties successfully restored, so the caller can report partial-apply diagnostics.
    """
    scene = context.scene
    count = 0
    for attr, props in settings.items():
        pg = getattr(scene, attr, None)
        if pg is None:
            _log.debug("Skipping missing property group: %s", attr)
            continue
        for prop_name, value in props.items():
            try:
                setattr(pg, prop_name, value)
                count += 1
            except Exception:
                _log.debug("Could not set %s.%s", attr, prop_name, exc_info=True)
    return count


def export_workspace_profile(context: bpy.types.Context, filepath: str) -> bool:
    """Export a full workspace profile including all module settings."""
    data = {
        "type": "workspace_profile",
        "scene_name": context.scene.name,
        "settings": collect_scene_settings(context),
    }
    return export_preset(filepath, data)


def import_workspace_profile(context: bpy.types.Context, filepath: str) -> int:
    """Import a workspace profile. Returns number of properties applied, or -1 on error."""
    data = import_preset(filepath)
    if data is None:
        return -1
    if data.get("type") != "workspace_profile":
        _log.error("Not a workspace profile: %s", filepath)
        return -1

    settings = data.get("settings", {})
    count = apply_scene_settings(context, settings)
    _log.info("Applied %d properties from workspace profile", count)
    return count
