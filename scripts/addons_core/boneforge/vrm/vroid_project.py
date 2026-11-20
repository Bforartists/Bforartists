"""VRoid Studio ``.vroid`` project inspection and hand-off.

A ``.vroid`` is a ZIP wrapper:

    meta.json                 plain JSON — VRoid Studio version, category
    v1model/meta.json         model encoding version
    v1model/data.bin          the model itself
    thumbnails/thumbnail.jpg  preview render

The wrapper is fully readable, which is what this module uses. The model
payload is **not**: ``data.bin`` is Protocol Buffers with an undocumented
schema wrapping zlib-compressed raw buffers. It is not encrypted, but
without the schema there is no way to tell a vertex buffer from a weight
table, a humanoid bone map, or a blendshape set — and the encoding is
versioned in three independent places, so anything inferred would break
across VRoid Studio releases.

So BoneCraft does not convert ``.vroid``. It reads the wrapper to confirm
the file and show a preview, then hands off to VRoid Studio, whose
Export → VRM produces something the VRM add-on can actually read.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import zipfile

import bpy
from bpy.types import Operator

logger = logging.getLogger(__name__)

# Populated in register(); holds the extracted project thumbnail so the
# panel can draw it with ``template_icon``.
_previews = None
_PREVIEW_KEY = "boneforge_vroid_thumb"

_META_NAME = "meta.json"
_THUMB_NAME = "thumbnails/thumbnail.jpg"


def read_project_meta(filepath):
    """Return a summary dict for a ``.vroid``, or ``None`` if unreadable.

    Keys: ``version`` (VRoid Studio version string), ``category``,
    ``size_mb``, ``has_thumbnail``.
    """
    try:
        with zipfile.ZipFile(filepath) as archive:
            names = set(archive.namelist())
            if _META_NAME not in names:
                return None
            raw = json.loads(archive.read(_META_NAME).decode("utf-8"))
            parts = [
                raw.get("updateVroidVersionMajor"),
                raw.get("updateVroidVersionMinor"),
                raw.get("updateVroidVersionPatch"),
            ]
            version = (
                ".".join(str(p) for p in parts)
                if all(p is not None for p in parts)
                else "unknown"
            )
            return {
                "version": version,
                "category": raw.get("avatarCategory") or "unknown",
                "size_mb": os.path.getsize(filepath) / (1024.0 * 1024.0),
                "has_thumbnail": _THUMB_NAME in names,
            }
    except (zipfile.BadZipFile, KeyError, ValueError, OSError) as exc:
        logger.warning("[BoneCraft] could not read .vroid wrapper: %s", exc)
        return None


def extract_thumbnail(filepath):
    """Extract the project thumbnail to a temp file; return its path.

    Returns ``None`` when the archive has no thumbnail or cannot be read.
    """
    try:
        with zipfile.ZipFile(filepath) as archive:
            if _THUMB_NAME not in archive.namelist():
                return None
            data = archive.read(_THUMB_NAME)
    except (zipfile.BadZipFile, KeyError, OSError) as exc:
        logger.warning("[BoneCraft] could not extract .vroid thumbnail: %s", exc)
        return None

    handle, out_path = tempfile.mkstemp(
        prefix="boneforge_vroid_thumb_", suffix=".jpg"
    )
    try:
        with os.fdopen(handle, "wb") as fh:
            fh.write(data)
    except OSError as exc:
        logger.warning("[BoneCraft] could not write thumbnail: %s", exc)
        return None
    return out_path


def load_thumbnail_preview(filepath):
    """Load ``filepath`` into the preview collection; return its icon id.

    Returns ``0`` when previews are unavailable, which callers treat as
    "draw no image".
    """
    if _previews is None:
        return 0
    # A preview is cached by key, so drop any earlier project's image
    # before loading the new one.
    if _PREVIEW_KEY in _previews:
        del _previews[_PREVIEW_KEY]
    try:
        preview = _previews.load(_PREVIEW_KEY, filepath, "IMAGE")
        return preview.icon_id
    except (KeyError, RuntimeError) as exc:
        logger.warning("[BoneCraft] could not load thumbnail preview: %s", exc)
        return 0


def open_in_default_app(filepath):
    """Open ``filepath`` with the OS-associated application.

    Raises ``OSError`` when no association exists or the launch fails.
    """
    if sys.platform.startswith("win"):
        os.startfile(filepath)  # noqa: S606 — user-selected path
    elif sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])


class BF_OT_VRoidOpenInStudio(Operator):
    """Open the inspected .vroid project in VRoid Studio."""

    bl_idname = "boneforge.vroid_open_in_studio"
    bl_label = "Open in VRoid Studio"
    bl_description = (
        "Open this .vroid project in VRoid Studio using the system file "
        "association, so you can run Export to VRM. BoneCraft cannot "
        "convert .vroid directly — the model payload format is not public"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "boneforge_vrm_settings", None)
        return bool(settings and settings.vroid_project_path)

    def execute(self, context):
        settings = context.scene.boneforge_vrm_settings
        path = bpy.path.abspath(settings.vroid_project_path)
        if not os.path.exists(path):
            self.report({"ERROR"}, f"Project file no longer exists: {path}")
            return {"CANCELLED"}
        try:
            open_in_default_app(path)
        except OSError as exc:
            self.report(
                {"ERROR"},
                "Could not open the project. Install VRoid Studio, or "
                f"associate .vroid files with it first ({exc}).",
            )
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            "Opened in VRoid Studio. Use Export -> VRM, then click "
            "'Import Exported VRM…' here.",
        )
        return {"FINISHED"}


class BF_OT_VRoidClearProject(Operator):
    """Dismiss the inspected VRoid project card."""

    bl_idname = "boneforge.vroid_clear_project"
    bl_label = "Dismiss"
    bl_description = "Clear the inspected VRoid project from the panel"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.boneforge_vrm_settings
        settings.vroid_project_path = ""
        settings.vroid_project_version = ""
        settings.vroid_project_summary = ""
        settings.vroid_thumbnail_icon = 0
        return {"FINISHED"}


def register_previews():
    global _previews
    if _previews is not None:
        return
    try:
        import bpy.utils.previews as _p
        _previews = _p.new()
    except Exception as exc:  # pragma: no cover - host-dependent
        logger.warning("[BoneCraft] preview collection unavailable: %s", exc)
        _previews = None


def unregister_previews():
    global _previews
    if _previews is None:
        return
    try:
        import bpy.utils.previews as _p
        _p.remove(_previews)
    except Exception:  # pragma: no cover - host-dependent
        pass
    _previews = None
