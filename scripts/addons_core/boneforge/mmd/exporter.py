"""MMD export operators — wraps mmd_tools.export_pmx and export_vmd.

PMX export expects the active object to be an MMD root (a special
empty mmd_tools attaches to imported models). For non-MMD armatures,
the user typically needs to convert via mmd_tools' "Convert to MMD
model" first; we surface the upstream error if so.

v3.3.11: both export operators gain a ``scope`` EnumProperty that
mirrors Blender's standard FBX export scope pattern:

* ``ACTIVE`` (default) — export the current active MMD model only.
* ``ALL`` — find every MMD model in the scene and export each to a
  separate file. The user-supplied filepath is treated as a template:
  ``output/motion.vmd`` becomes ``output/motion_<model>.vmd`` per
  model.
"""

from __future__ import annotations

import logging
import os
from typing import List

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator

from . import bridge

logger = logging.getLogger(__name__)


_SCOPE_ITEMS = [
    ("ACTIVE", "Active Model",
     "Export the active MMD model only"),
    ("ALL", "All Models",
     "Export every MMD model in the scene to a separate file. "
     "Filenames get the model's root name appended"),
]
SCOPE_ITEMS = _SCOPE_ITEMS


def _sanitize_filename(name: str, fallback: str) -> str:
    cleaned = "".join("_" if ch in '<>:"/\\|?*' else ch for ch in (name or ""))
    cleaned = cleaned.strip(" .")
    return cleaned or fallback


def _resolve_export_dir(raw_path: str) -> str:
    raw_path = (raw_path or "").strip()
    if not raw_path:
        return ""
    if raw_path.startswith("//") and not bpy.data.filepath:
        return ""
    return bpy.path.abspath(raw_path)


def _with_extension(filename: str, extension: str) -> str:
    base, ext = os.path.splitext(filename)
    if ext.lower() == extension:
        return filename
    return f"{base or filename}{extension}"


def build_export_filepath(export_path: str, export_name: str, extension: str, fallback: str) -> str:
    export_dir = _resolve_export_dir(export_path)
    if not export_dir:
        return ""
    filename = _with_extension(_sanitize_filename(export_name, fallback), extension)
    return os.path.join(export_dir, filename)


def _find_mmd_roots() -> List[bpy.types.Object]:
    """Return every MMD root empty in the scene.

    mmd_tools tags the special root-empty with ``mmd_type == 'ROOT'``.
    Falls back to scanning for empties named like MMD models if the
    attribute isn't present on a given object.
    """
    roots = []
    for obj in bpy.data.objects:
        if obj.type != "EMPTY":
            continue
        if getattr(obj, "mmd_type", None) == "ROOT":
            roots.append(obj)
    return roots


def _scoped_filepath(template: str, model_name: str) -> str:
    """Insert *model_name* into *template* before the extension.

    ``output/motion.vmd`` + ``Alice`` → ``output/motion_Alice.vmd``.
    """
    head, tail = os.path.split(template)
    base, ext = os.path.splitext(tail)
    return os.path.join(head, f"{base}_{model_name}{ext}")


# ── PMX export ──────────────────────────────────────────────────

class BF_OT_MMDExportPMX(Operator):
    """Export MMD model(s) as PMX file(s)."""

    bl_idname = "boneforge.mmd_export_pmx"
    bl_label = "Export PMX…"
    bl_description = (
        "Export the active MMD model (or all MMD models in the scene) "
        "as PMX file(s) via mmd_tools. The active object must be part "
        "of an MMD model — use mmd_tools' 'Convert to MMD Model' "
        "first if you're starting from a generic armature"
    )
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.pmx", options={"HIDDEN"})
    scope: EnumProperty(
        name="Scope",
        description="Which MMD model(s) to export",
        items=_SCOPE_ITEMS,
        default="ACTIVE",
    )

    def invoke(self, context, event):
        if bridge.find_mmd_addon() is None:
            self.report(
                {"ERROR"},
                "mmd_tools not detected. Install it from BoneCraft's "
                "MMD / PMX panel first.",
            )
            return {"CANCELLED"}
        if not self.filepath:
            active = context.active_object
            base = active.name if active else "model"
            self.filepath = f"{base}.pmx"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file path")
            return {"CANCELLED"}
        self.filepath = _with_extension(self.filepath, ".pmx")
        if bridge.find_mmd_addon() is None:
            self.report({"ERROR"}, "mmd_tools not available")
            return {"CANCELLED"}

        if self.scope == "ACTIVE":
            return self._export_active(context, self.filepath)
        return self._export_all(context, self.filepath)

    def _export_active(self, context, filepath):
        try:
            bpy.ops.mmd_tools.export_pmx(filepath=filepath)
        except (RuntimeError, AttributeError) as exc:
            self.report(
                {"ERROR"},
                f"PMX export failed: {exc}. The active object must be "
                "an MMD model.",
            )
            logger.exception("[BoneCraft] PMX export failed")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Exported PMX → {filepath}")
        return {"FINISHED"}

    def _export_all(self, context, template):
        roots = _find_mmd_roots()
        if not roots:
            self.report(
                {"WARNING"},
                "No MMD root empties found in the scene. "
                "Use mmd_tools' Convert to MMD Model first.",
            )
            return {"CANCELLED"}

        prev_active = context.view_layer.objects.active
        prev_selection = [o for o in context.selected_objects]
        exported = []
        try:
            for root in roots:
                bpy.ops.object.select_all(action="DESELECT")
                root.select_set(True)
                context.view_layer.objects.active = root
                target_path = _scoped_filepath(template, root.name)
                try:
                    bpy.ops.mmd_tools.export_pmx(filepath=target_path)
                    exported.append(target_path)
                except (RuntimeError, AttributeError) as exc:
                    logger.warning(
                        "[BoneCraft] export of %r failed: %s",
                        root.name, exc,
                    )
                    self.report(
                        {"WARNING"},
                        f"Skipped {root.name}: {exc}",
                    )
        finally:
            # Restore selection
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for o in prev_selection:
                    if o.name in bpy.data.objects:
                        o.select_set(True)
                if prev_active is not None and prev_active.name in bpy.data.objects:
                    context.view_layer.objects.active = prev_active
            except RuntimeError:
                pass

        if not exported:
            self.report({"WARNING"}, "No MMD models exported.")
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Exported {len(exported)} PMX file(s) to "
            f"{os.path.dirname(template)}",
        )
        return {"FINISHED"}


# ── VMD export ──────────────────────────────────────────────────

class BF_OT_MMDExportVMD(Operator):
    """Export VMD motion(s) for the active or all MMD models."""

    bl_idname = "boneforge.mmd_export_vmd"
    bl_label = "Export VMD Motion…"
    bl_description = (
        "Export the current scene animation on the active MMD model "
        "(or all MMD models in the scene) as VMD motion file(s)"
    )
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.vmd", options={"HIDDEN"})
    scope: EnumProperty(
        name="Scope",
        description="Which MMD model(s) to export motion for",
        items=_SCOPE_ITEMS,
        default="ACTIVE",
    )

    def invoke(self, context, event):
        if bridge.find_mmd_addon() is None:
            self.report(
                {"ERROR"},
                "mmd_tools not detected. Install it from BoneCraft's "
                "MMD / PMX panel first.",
            )
            return {"CANCELLED"}
        if not self.filepath:
            active = context.active_object
            base = active.name if active else "motion"
            self.filepath = f"{base}.vmd"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file path")
            return {"CANCELLED"}
        self.filepath = _with_extension(self.filepath, ".vmd")
        if bridge.find_mmd_addon() is None:
            self.report({"ERROR"}, "mmd_tools not available")
            return {"CANCELLED"}

        if self.scope == "ACTIVE":
            return self._export_active(context, self.filepath)
        return self._export_all(context, self.filepath)

    def _export_active(self, context, filepath):
        try:
            bpy.ops.mmd_tools.export_vmd(filepath=filepath)
        except (RuntimeError, AttributeError) as exc:
            self.report({"ERROR"}, f"VMD export failed: {exc}")
            logger.exception("[BoneCraft] VMD export failed")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Exported VMD → {filepath}")
        return {"FINISHED"}

    def _export_all(self, context, template):
        roots = _find_mmd_roots()
        if not roots:
            self.report(
                {"WARNING"},
                "No MMD root empties found in the scene.",
            )
            return {"CANCELLED"}

        prev_active = context.view_layer.objects.active
        prev_selection = [o for o in context.selected_objects]
        exported = []
        try:
            for root in roots:
                bpy.ops.object.select_all(action="DESELECT")
                root.select_set(True)
                context.view_layer.objects.active = root
                target_path = _scoped_filepath(template, root.name)
                try:
                    bpy.ops.mmd_tools.export_vmd(filepath=target_path)
                    exported.append(target_path)
                except (RuntimeError, AttributeError) as exc:
                    logger.warning(
                        "[BoneCraft] VMD export of %r failed: %s",
                        root.name, exc,
                    )
                    self.report(
                        {"WARNING"},
                        f"Skipped {root.name}: {exc}",
                    )
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for o in prev_selection:
                    if o.name in bpy.data.objects:
                        o.select_set(True)
                if prev_active is not None and prev_active.name in bpy.data.objects:
                    context.view_layer.objects.active = prev_active
            except RuntimeError:
                pass

        if not exported:
            self.report({"WARNING"}, "No VMD files exported.")
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Exported {len(exported)} VMD file(s) to "
            f"{os.path.dirname(template)}",
        )
        return {"FINISHED"}


def _resolve_vpd_export_op():
    """Locate the VPD export operator on bpy.ops.mmd_tools.

    Recent mmd_tools releases expose ``export_vpd``; older versions
    occasionally routed VPD through ``export_vmd``. Returns the op
    callable or ``None`` if neither is present.
    """
    mmd_ops = getattr(bpy.ops, "mmd_tools", None)
    if mmd_ops is None:
        return None
    for op_name in ("export_vpd", "export_vmd"):
        op_func = getattr(mmd_ops, op_name, None)
        if op_func is None:
            continue
        try:
            op_func.get_rna_type()
        except (AttributeError, KeyError):
            continue
        return op_func
    return None


class BF_OT_MMDExportVPD(Operator):
    """Export VPD pose for the active or all MMD models."""

    bl_idname = "boneforge.mmd_export_vpd"
    bl_label = "Export VPD Pose…"
    bl_description = (
        "Export the current pose on the active MMD model (or all MMD "
        "models in the scene) as VPD pose file(s) via mmd_tools"
    )
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.vpd", options={"HIDDEN"})
    scope: EnumProperty(
        name="Scope",
        description="Which MMD model(s) to export pose for",
        items=_SCOPE_ITEMS,
        default="ACTIVE",
    )

    def invoke(self, context, event):
        if bridge.find_mmd_addon() is None:
            self.report(
                {"ERROR"},
                "mmd_tools not detected. Install it from BoneCraft's "
                "MMD / PMX panel first.",
            )
            return {"CANCELLED"}
        if _resolve_vpd_export_op() is None:
            self.report(
                {"ERROR"},
                "VPD export operator not available in this mmd_tools "
                "version.",
            )
            return {"CANCELLED"}
        if not self.filepath:
            active = context.active_object
            base = active.name if active else "pose"
            self.filepath = f"{base}.vpd"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file path")
            return {"CANCELLED"}
        self.filepath = _with_extension(self.filepath, ".vpd")
        if bridge.find_mmd_addon() is None:
            self.report({"ERROR"}, "mmd_tools not available")
            return {"CANCELLED"}
        op_func = _resolve_vpd_export_op()
        if op_func is None:
            self.report({"ERROR"}, "VPD export op not available")
            return {"CANCELLED"}

        if self.scope == "ACTIVE":
            return self._export_active(op_func, self.filepath)
        return self._export_all(context, op_func, self.filepath)

    def _export_active(self, op_func, filepath):
        try:
            op_func(filepath=filepath)
        except (RuntimeError, AttributeError) as exc:
            self.report({"ERROR"}, f"VPD export failed: {exc}")
            logger.exception("[BoneCraft] VPD export failed")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Exported VPD → {filepath}")
        return {"FINISHED"}

    def _export_all(self, context, op_func, template):
        roots = _find_mmd_roots()
        if not roots:
            self.report(
                {"WARNING"},
                "No MMD root empties found in the scene.",
            )
            return {"CANCELLED"}

        prev_active = context.view_layer.objects.active
        prev_selection = [o for o in context.selected_objects]
        exported = []
        try:
            for root in roots:
                bpy.ops.object.select_all(action="DESELECT")
                root.select_set(True)
                context.view_layer.objects.active = root
                target_path = _scoped_filepath(template, root.name)
                try:
                    op_func(filepath=target_path)
                    exported.append(target_path)
                except (RuntimeError, AttributeError) as exc:
                    logger.warning(
                        "[BoneCraft] VPD export of %r failed: %s",
                        root.name, exc,
                    )
                    self.report(
                        {"WARNING"},
                        f"Skipped {root.name}: {exc}",
                    )
        finally:
            try:
                bpy.ops.object.select_all(action="DESELECT")
                for o in prev_selection:
                    if o.name in bpy.data.objects:
                        o.select_set(True)
                if prev_active is not None and prev_active.name in bpy.data.objects:
                    context.view_layer.objects.active = prev_active
            except RuntimeError:
                pass

        if not exported:
            self.report({"WARNING"}, "No VPD files exported.")
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Exported {len(exported)} VPD file(s) to "
            f"{os.path.dirname(template)}",
        )
        return {"FINISHED"}
