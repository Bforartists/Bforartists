"""Detect ``mmd_tools`` and offer four install paths.

mmd_tools is the canonical PMX/PMD/VMD I/O addon for Blender —
maintained by MMD-Blender, free, GPL. Detect both legacy module
names and namespaced Blender Extensions; modern extensions need no bl_info.

Same install-path pattern as the v3.2.1 VRM bridge:

* :class:`BF_OT_MMDInstallAuto` — fetch latest release from GitHub
  and install via Blender's add-on installer.
* :class:`BF_OT_MMDInstallFromDisk` — open Blender's standard file
  browser to install a .zip you already downloaded.
* :class:`BF_OT_MMDOpenWebsite` — open the official Extensions page
  or the upstream GitHub releases page in the user's browser.
* :class:`BF_OT_InstallMMDAddon` — open Blender's Add-on preferences
  pre-filtered for "MMD" as a fallback.
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


# Module names mmd_tools has shipped under, in order of preference.
_KNOWN_MODULE_NAMES = (
    "mmd_tools",
    "blender_mmd_tools",
    "blender_mmd_tools-master",
    "blender_mmd_tools-blender-v3.0",
)


def is_mmd_op_available(op_name: str) -> bool:
    mmd_ops = getattr(bpy.ops, "mmd_tools", None)
    if mmd_ops is None:
        return False
    op_func = getattr(mmd_ops, op_name, None)
    if op_func is None:
        return False
    try:
        op_func.get_rna_type()
    except (AttributeError, KeyError, RuntimeError):
        return False
    return True


def _mmd_modules(*, refresh=False):
    """Recognize legacy packages and namespaced extensions without bl_info."""
    import addon_utils

    modules = addon_utils.modules(refresh=refresh)
    enabled = {a.module for a in bpy.context.preferences.addons}
    candidates = []
    for mod in modules:
        name = mod.__name__
        leaf = name.rsplit(".", 1)[-1]
        info = addon_utils.module_bl_info(mod)
        if leaf in _KNOWN_MODULE_NAMES or "mmd" in (info.get("name") or "").lower():
            candidates.append(mod)
    # A disabled legacy copy must not mask an enabled extension.
    return sorted(candidates, key=lambda mod: mod.__name__ not in enabled)


def find_mmd_addon() -> Optional[object]:
    """Return the addon_utils module object if installed AND enabled."""
    enabled_names = {a.module for a in bpy.context.preferences.addons}
    for mod in _mmd_modules():
        if mod.__name__ in enabled_names:
            return mod

    return None


def mmd_addon_status() -> dict:
    """Structured snapshot for UI display."""
    import addon_utils

    status = {
        "installed": False,
        "enabled": False,
        "import_pmx_available": False,
        "import_vmd_available": False,
        "import_vpd_available": False,
        "export_pmx_available": False,
        "export_vmd_available": False,
        "export_vpd_available": False,
        "version": None,
        "module_name": None,
    }
    enabled_names = {a.module for a in bpy.context.preferences.addons}

    for mod in _mmd_modules():
        info = addon_utils.module_bl_info(mod)
        status["installed"] = True
        status["module_name"] = mod.__name__
        status["version"] = info.get("version")
        status["enabled"] = mod.__name__ in enabled_names
        break

    if status["installed"] and status["enabled"]:
        status["import_pmx_available"] = is_mmd_op_available("import_model")
        status["import_vmd_available"] = is_mmd_op_available("import_vmd")
        status["export_pmx_available"] = is_mmd_op_available("export_pmx")
        status["export_vmd_available"] = is_mmd_op_available("export_vmd")
        # VPD ops: probe both possible names (varies by mmd_tools
        # version). Either being present satisfies VPD support.
        status["import_vpd_available"] = (
            is_mmd_op_available("import_vpd")
            or is_mmd_op_available("import_vmd")  # legacy fallback
        )
        status["export_vpd_available"] = (
            is_mmd_op_available("export_vpd")
            or is_mmd_op_available("export_vmd")  # legacy fallback
        )

    return status


def _enable_first_mmd_addon() -> Optional[str]:
    """Find an MMD addon that's installed but disabled and enable it."""
    for mod in _mmd_modules(refresh=True):
        if (mod.__name__ in {a.module for a in bpy.context.preferences.addons}
                and is_mmd_op_available("import_model")):
            return mod.__name__
        try:
            outcome = bpy.ops.preferences.addon_enable(module=mod.__name__)
            if ("FINISHED" in outcome
                    and mod.__name__ in {a.module for a in bpy.context.preferences.addons}
                    and is_mmd_op_available("import_model")):
                return mod.__name__
        except RuntimeError as exc:
            logger.warning(
                "[BoneCraft] could not enable %s: %s", mod.__name__, exc,
            )
    return None


# ── Install URLs ────────────────────────────────────────────────

_MMD_EXTENSIONS_URL = "https://extensions.blender.org/add-ons/mmd-tools/"
_MMD_GITHUB_URL = "https://github.com/MMD-Blender/blender_mmd_tools"
_MMD_GITHUB_API_LATEST = (
    "https://api.github.com/repos/MMD-Blender/"
    "blender_mmd_tools/releases/latest"
)


# ── Install operators ───────────────────────────────────────────

class BF_OT_InstallMMDAddon(bpy.types.Operator):
    """Open Blender's Add-on preferences pre-filtered for MMD (fallback)."""

    bl_idname = "boneforge.install_mmd_addon"
    bl_label = "Open Add-on Preferences"
    bl_description = (
        "Open Edit > Preferences > Add-ons with the search pre-filled "
        "with 'MMD' so you can install or enable the addon yourself"
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
            context.preferences.active_section = "ADDONS"
            try:
                bpy.context.window_manager.addon_search = "MMD"
            except (AttributeError, TypeError) as exc:
                logger.debug("[BoneCraft] addon_search unavailable: %s", exc)
        except RuntimeError as exc:
            self.report(
                {"ERROR"},
                f"Could not open Preferences: {exc}. "
                "Open Edit > Preferences > Add-ons manually and search 'MMD'.",
            )
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            "Install / enable 'mmd_tools' from the list, then close Preferences.",
        )
        return {"FINISHED"}


class BF_OT_MMDInstallFromDisk(bpy.types.Operator):
    """Install mmd_tools from a .zip you downloaded."""

    bl_idname = "boneforge.mmd_install_from_disk"
    bl_label = "Install from .zip on Disk…"
    bl_description = (
        "Browse for an mmd_tools .zip you've already downloaded and "
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
                "Pick the .zip release file, not an extracted folder.",
            )
            return {"CANCELLED"}

        try:
            from boneforge.core.addon_installer import smart_install_zip
            result = smart_install_zip(
                self.filepath,
                fallback_folder_name="mmd_tools",
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Install failed: {exc}")
            return {"CANCELLED"}

        if not result.success:
            self.report({"ERROR"}, f"Install failed: {result.message}")
            return {"CANCELLED"}

        enabled_module = _enable_first_mmd_addon()
        if enabled_module is None:
            self.report(
                {"ERROR"},
                "mmd_tools installed but could not auto-enable. "
                "Open Preferences > Add-ons, search 'MMD', tick the checkbox.",
            )
            return {"CANCELLED"}

        self.report({"INFO"}, f"Installed and enabled: {enabled_module}")
        return {"FINISHED"}


class BF_OT_MMDOpenWebsite(bpy.types.Operator):
    """Open the official mmd_tools page in the browser."""

    bl_idname = "boneforge.mmd_open_website"
    bl_label = "Open mmd_tools Website"
    bl_options = {"REGISTER"}

    target: bpy.props.EnumProperty(options={'HIDDEN', 'SKIP_SAVE'},
        name="Site",
        items=[
            ("EXTENSIONS", "Blender Extensions",
             "Official Blender Extensions platform"),
            ("GITHUB", "GitHub Releases",
             "Source releases on GitHub (MMD-Blender)"),
        ],
        default="EXTENSIONS",
    )

    def execute(self, context):
        url = (_MMD_EXTENSIONS_URL if self.target == "EXTENSIONS"
               else _MMD_GITHUB_URL)
        try:
            bpy.ops.wm.url_open(url=url)
        except RuntimeError as exc:
            self.report({"ERROR"}, f"Could not open browser: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Opened {url}")
        return {"FINISHED"}


class BF_OT_MMDInstallAuto(bpy.types.Operator):
    """Download the latest mmd_tools release from GitHub and install."""

    bl_idname = "boneforge.mmd_install_auto"
    bl_label = "Auto-Install Latest from GitHub"
    bl_description = (
        "Download the latest mmd_tools release from MMD-Blender's GitHub "
        "and install + enable it. Requires internet access"
    )
    bl_options = {"REGISTER"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def draw(self, context):
        layout = self.layout
        layout.label(text=T("BoneCraft will download the latest release from:"))
        layout.label(text=_MMD_GITHUB_URL, icon="URL")
        layout.label(text=T("and install it via Blender's add-on installer."))
        layout.label(text=T("Approximate download size: 2–5 MB."))

    def execute(self, context):
        wm = context.window_manager
        wm.progress_begin(0, 100)
        try:
            wm.progress_update(5)
            try:
                req = urllib.request.Request(
                    _MMD_GITHUB_API_LATEST,
                    headers={"Accept": "application/vnd.github+json",
                             "User-Agent": "BoneForge/3.3.10"},
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as exc:
                self.report(
                    {"ERROR"},
                    f"Could not reach GitHub — check your internet "
                    f"connection. ({exc})",
                )
                return {"CANCELLED"}
            except json.JSONDecodeError as exc:
                self.report({"ERROR"}, f"GitHub API response malformed: {exc}")
                return {"CANCELLED"}

            tag = data.get("tag_name", "?")
            wm.progress_update(15)

            asset_url, asset_name = None, None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if (name.lower().endswith(".zip")
                        and "source" not in name.lower()):
                    asset_url = asset.get("browser_download_url")
                    asset_name = name
                    break

            if asset_url is None:
                self.report(
                    {"ERROR"},
                    "Latest release has no installable .zip. "
                    "Try 'Open Website' to install manually.",
                )
                return {"CANCELLED"}
            wm.progress_update(25)

            tmp_path = None
            try:
                fd, tmp_path = tempfile.mkstemp(
                    prefix="boneforge_mmd_", suffix=".zip",
                )
                os.close(fd)
                req = urllib.request.Request(
                    asset_url,
                    headers={"User-Agent": "BoneForge/3.3.10"},
                )
                with urllib.request.urlopen(req, timeout=120) as resp, \
                        open(tmp_path, "wb") as out:
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
                    try: os.unlink(tmp_path)
                    except OSError: pass
                return {"CANCELLED"}

            wm.progress_update(85)

            # v3.3.13: use smart_install_zip — handles flat-zip repackage.
            try:
                from boneforge.core.addon_installer import smart_install_zip
                result = smart_install_zip(
                    tmp_path,
                    fallback_folder_name="mmd_tools",
                )
            except Exception as exc:
                result = None
                self.report({"ERROR"}, f"Install failed: {exc}")
                logger.exception("[BoneCraft] smart_install_zip raised")
            finally:
                try: os.unlink(tmp_path)
                except OSError: pass

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

            # Verify activation for both legacy and extension installations.
            enabled_module = _enable_first_mmd_addon()
            if enabled_module is None:
                self.report(
                    {"ERROR"},
                    f"Downloaded {asset_name} ({tag}) and installed, but "
                    "could not auto-enable. Open Preferences > Add-ons, "
                    "search 'MMD', tick the checkbox.",
                )
                return {"CANCELLED"}

            self.report(
                {"INFO"},
                f"Installed and enabled mmd_tools {tag} ({enabled_module})",
            )
            return {"FINISHED"}
        finally:
            wm.progress_end()
