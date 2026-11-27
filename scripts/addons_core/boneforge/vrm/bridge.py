"""Detect ``vrm-addon-for-blender`` and offer multiple ways to install it.

Three install paths are exposed (v3.2.1):

* :class:`BF_OT_VRMInstallAuto` — fetch the latest release from the
  upstream GitHub and install it via Blender's add-on installer. Network
  required. The user sees the source URL before any bytes leave their
  machine.
* :class:`BF_OT_VRMInstallFromDisk` — opens Blender's standard "Install
  from Disk" file browser pointed at any ``.zip`` the user downloaded
  themselves. No network access; full user control over the bytes.
* :class:`BF_OT_VRMOpenWebsite` — opens the official Blender Extensions
  page for the VRM Add-on in the user's default browser, so they can
  read about it / pin a specific version before installing.

The original :class:`BF_OT_InstallVRMAddon` (open Blender's Add-ons
preferences pre-filtered for "VRM") is preserved as a fallback for users
on Blender versions where the new flow doesn't apply.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import urllib.error
import urllib.request
from typing import Optional

import bpy

from boneforge.i18n import T

logger = logging.getLogger(__name__)


# ── Detection ────────────────────────────────────────────────────

_KNOWN_MODULE_NAMES = (
    "VRM_Addon_for_Blender-release",
    "VRM_Addon_for_Blender",
    "io_scene_vrm",
)


def _op_registered(group_name: str, op_name: str) -> bool:
    op_group = getattr(bpy.ops, group_name, None)
    if op_group is None:
        return False
    op_func = getattr(op_group, op_name, None)
    if op_func is None:
        return False
    try:
        op_func.get_rna_type()
    except (AttributeError, KeyError):
        return False
    return True


def is_vrm_import_op_available() -> bool:
    return _op_registered("import_scene", "vrm")


def is_vrm_export_op_available() -> bool:
    return _op_registered("export_scene", "vrm")


def find_vrm_addon() -> Optional[object]:
    """Return the addon_utils module object if installed AND enabled."""
    import addon_utils

    enabled_names = {a.module for a in bpy.context.preferences.addons}

    for name in _KNOWN_MODULE_NAMES:
        if name not in enabled_names:
            continue
        for mod in addon_utils.modules():
            if getattr(mod, "__name__", "").endswith(name):
                return mod

    for mod in addon_utils.modules():
        info = addon_utils.module_bl_info(mod)
        bl_name = (info.get("name") or "").strip()
        if bl_name.startswith("VRM") and mod.__name__ in enabled_names:
            return mod

    return None


def vrm_addon_status() -> dict:
    """Structured snapshot for UI display."""
    import addon_utils

    status = {
        "installed": False,
        "enabled": False,
        "import_op_available": False,
        "export_op_available": False,
        "version": None,
        "module_name": None,
    }
    enabled_names = {a.module for a in bpy.context.preferences.addons}

    for mod in addon_utils.modules():
        info = addon_utils.module_bl_info(mod)
        bl_name = (info.get("name") or "").strip()
        if bl_name.startswith("VRM"):
            status["installed"] = True
            status["module_name"] = mod.__name__
            status["version"] = info.get("version")
            status["enabled"] = mod.__name__ in enabled_names
            break

    if status["installed"] and status["enabled"]:
        status["import_op_available"] = is_vrm_import_op_available()
        status["export_op_available"] = is_vrm_export_op_available()

    return status


def _enable_first_vrm_addon() -> Optional[str]:
    """Find a VRM addon module that's installed but disabled and enable it.

    Returns the module name on success, ``None`` if nothing matched.
    """
    import addon_utils
    addon_utils.modules(refresh=True)

    for mod in addon_utils.modules():
        info = addon_utils.module_bl_info(mod)
        bl_name = (info.get("name") or "").strip()
        if not bl_name.startswith("VRM"):
            continue
        try:
            bpy.ops.preferences.addon_enable(module=mod.__name__)
            return mod.__name__
        except RuntimeError as exc:
            logger.warning(
                "[BoneCraft] could not enable %s: %s", mod.__name__, exc,
            )
    return None


# ── Install operators ────────────────────────────────────────────

# Where to take users for a manual install / read-up.
_VRM_EXTENSIONS_URL = "https://extensions.blender.org/add-ons/vrm/"
_VRM_GITHUB_URL = "https://github.com/saturday06/VRM-Addon-for-Blender"

# GitHub releases API for the auto-installer.
_VRM_GITHUB_API_LATEST = (
    "https://api.github.com/repos/saturday06/"
    "VRM-Addon-for-Blender/releases/latest"
)


class BF_OT_InstallVRMAddon(bpy.types.Operator):
    """Open Blender's Add-on preferences pre-filtered for VRM (fallback)."""

    bl_idname = "boneforge.install_vrm_addon"
    bl_label = "Open Add-on Preferences"
    bl_description = (
        "Open Edit > Preferences > Add-ons with the search pre-filled "
        "with 'VRM' so you can install or enable the add-on yourself"
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
            context.preferences.active_section = "ADDONS"
            try:
                bpy.context.window_manager.addon_search = "VRM"
            except (AttributeError, TypeError) as exc:
                logger.debug("[BoneCraft] addon_search unavailable: %s", exc)
        except RuntimeError as exc:
            self.report(
                {"ERROR"},
                f"Could not open Preferences: {exc}. "
                "Open Edit > Preferences > Add-ons manually and search 'VRM'.",
            )
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            "Install / enable 'VRM Add-on for Blender' from the list, "
            "then close Preferences.",
        )
        return {"FINISHED"}


class BF_OT_VRMInstallFromDisk(bpy.types.Operator):
    """Install VRM Add-on for Blender from a .zip you downloaded."""

    bl_idname = "boneforge.vrm_install_from_disk"
    bl_label = "Install from .zip on Disk…"
    bl_description = (
        "Browse for a VRM Add-on .zip you've already downloaded and "
        "install + enable it via Blender's add-on installer"
    )
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.zip", options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}
        if not os.path.isfile(self.filepath):
            self.report({"ERROR"}, f"Not a file: {self.filepath}")
            return {"CANCELLED"}
        if not self.filepath.lower().endswith(".zip"):
            self.report(
                {"ERROR"},
                "VRM Add-on installs from a .zip — pick the release "
                "zip you downloaded, not an extracted folder.",
            )
            return {"CANCELLED"}

        # v3.3.13: smart_install_zip handles flat-zip repackage.
        try:
            from boneforge.core.addon_installer import smart_install_zip
            result = smart_install_zip(
                self.filepath,
                fallback_folder_name="VRM_Addon_for_Blender",
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Install failed: {exc}")
            logger.exception("[BoneCraft] smart_install_zip raised")
            return {"CANCELLED"}

        if not result.success:
            self.report(
                {"ERROR"},
                f"Install failed: {result.message}",
            )
            return {"CANCELLED"}

        enabled_module = _enable_first_vrm_addon()
        if enabled_module is None:
            self.report(
                {"WARNING"},
                "VRM Add-on installed but could not be auto-enabled. "
                "Open Preferences > Add-ons, search 'VRM', and tick the "
                "checkbox.",
            )
            return {"FINISHED"}

        self.report(
            {"INFO"},
            f"Installed and enabled: {enabled_module}",
        )
        return {"FINISHED"}


class BF_OT_VRMOpenWebsite(bpy.types.Operator):
    """Open the official VRM Add-on page in the user's browser."""

    bl_idname = "boneforge.vrm_open_website"
    bl_label = "Open VRM Add-on Website"
    bl_description = (
        "Open the official 'VRM Add-on for Blender' page on Blender's "
        "Extensions site in your default browser"
    )
    bl_options = {"REGISTER"}

    target: bpy.props.EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Site",
        items=[
            ("EXTENSIONS", "Blender Extensions",
             "Official Blender Extensions platform"),
            ("GITHUB", "GitHub Releases",
             "Source releases on GitHub (saturday06)"),
        ],
        default="EXTENSIONS",
    )

    def execute(self, context):
        url = (_VRM_EXTENSIONS_URL if self.target == "EXTENSIONS"
               else _VRM_GITHUB_URL)
        try:
            bpy.ops.wm.url_open(url=url)
        except RuntimeError as exc:
            self.report({"ERROR"}, f"Could not open browser: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Opened {url}")
        return {"FINISHED"}


class BF_OT_VRMInstallAuto(bpy.types.Operator):
    """Download the latest VRM Add-on release from GitHub and install it.

    Network required. The operator displays the source URL in a confirm
    dialog before any download starts so the user can see exactly what
    they're agreeing to.
    """

    bl_idname = "boneforge.vrm_install_auto"
    bl_label = "Auto-Install Latest from GitHub"
    bl_description = (
        "Download the latest VRM Add-on release from saturday06's "
        "GitHub and install + enable it. Requires internet access"
    )
    bl_options = {"REGISTER"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def draw(self, context):
        layout = self.layout
        layout.label(text=T("BoneCraft will download the latest release from:"))
        layout.label(text=_VRM_GITHUB_URL, icon="URL")
        layout.label(text=T("and install it via Blender's add-on installer."))
        layout.label(text=T("Approximate download size: 3–6 MB."))

    def execute(self, context):
        wm = context.window_manager
        wm.progress_begin(0, 100)
        try:
            wm.progress_update(5)

            # ── 1. Look up the latest release ────────────────────
            try:
                req = urllib.request.Request(
                    _VRM_GITHUB_API_LATEST,
                    headers={"Accept": "application/vnd.github+json",
                             "User-Agent": "BoneForge/3.2.1"},
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as exc:
                self.report(
                    {"ERROR"},
                    "Could not reach GitHub — check your internet "
                    f"connection. ({exc})",
                )
                return {"CANCELLED"}
            except json.JSONDecodeError as exc:
                self.report({"ERROR"}, f"GitHub API response malformed: {exc}")
                return {"CANCELLED"}

            tag = data.get("tag_name", "?")
            wm.progress_update(15)

            # ── 2. Pick the asset ────────────────────────────────
            asset_url = None
            asset_name = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                # Prefer the canonical release zip; skip source-archive zips
                # ('Source code (zip)' is auto-attached and won't install).
                if name.lower().endswith(".zip") and "source" not in name.lower():
                    asset_url = asset.get("browser_download_url")
                    asset_name = name
                    break

            if asset_url is None:
                self.report(
                    {"ERROR"},
                    "Latest release has no installable .zip asset. "
                    "Try 'Open VRM Add-on Website' and install manually.",
                )
                return {"CANCELLED"}
            wm.progress_update(25)

            # ── 3. Download to a temp file ───────────────────────
            tmp_path = None
            try:
                fd, tmp_path = tempfile.mkstemp(
                    prefix="boneforge_vrm_", suffix=".zip",
                )
                os.close(fd)
                req = urllib.request.Request(
                    asset_url,
                    headers={"User-Agent": "BoneForge/3.2.1"},
                )
                with urllib.request.urlopen(req, timeout=120) as resp, \
                        open(tmp_path, "wb") as out:
                    # Stream the download with progress updates.
                    total = int(resp.headers.get("Content-Length") or 0)
                    read = 0
                    chunk = 64 * 1024
                    while True:
                        buf = resp.read(chunk)
                        if not buf:
                            break
                        out.write(buf)
                        read += len(buf)
                        if total > 0:
                            pct = 25 + int(60 * read / total)
                            wm.progress_update(min(pct, 85))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                self.report({"ERROR"}, f"Download failed: {exc}")
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                return {"CANCELLED"}

            wm.progress_update(85)

            # ── 4. Install via Blender (with auto-repackage on flat zips) ─
            # v3.3.13: use smart_install_zip — if the GitHub zip has
            # __init__.py at root (legacy addon_install rejects), the
            # helper extracts + wraps in a folder + retries.
            try:
                from boneforge.core.addon_installer import smart_install_zip
                result = smart_install_zip(
                    tmp_path,
                    fallback_folder_name="VRM_Addon_for_Blender",
                )
            except Exception as exc:
                result = None
                self.report({"ERROR"}, f"Install failed: {exc}")
                logger.exception("[BoneCraft] smart_install_zip raised")
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            if result is None or not result.success:
                if result is not None:
                    msg = result.message
                else:
                    msg = "internal install error"
                self.report(
                    {"ERROR"},
                    f"Install failed: {msg}. Try 'Install from .zip on "
                    "Disk' with a known-good release, or follow the "
                    "manual install instructions on the website.",
                )
                return {"CANCELLED"}

            wm.progress_update(95)

            # ── 5. Enable ────────────────────────────────────────
            enabled_module = _enable_first_vrm_addon()
            if enabled_module is None:
                self.report(
                    {"WARNING"},
                    f"Downloaded {asset_name} ({tag}) and installed, but "
                    "could not auto-enable. Open Preferences > Add-ons, "
                    "search 'VRM', and tick the checkbox.",
                )
                return {"FINISHED"}

            self.report(
                {"INFO"},
                f"Installed and enabled VRM Add-on {tag} "
                f"({enabled_module})",
            )
            return {"FINISHED"}
        finally:
            wm.progress_end()
