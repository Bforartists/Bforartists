"""MMD import operators — wraps mmd_tools.import_model and import_vmd.

Two BoneCraft operators surface the most common MMD import flows:

* :class:`BF_OT_MMDImportPMX` — wraps ``mmd_tools.import_model``
  (handles .pmx, .pmd, .x).
* :class:`BF_OT_MMDImportVMD` — wraps ``mmd_tools.import_vmd``
  (handles .vmd motion files; targets the active MMD model).

Both fail-fast if the upstream addon isn't enabled, with a clear
error message that points at BoneCraft's MMD bridge install panel.
"""

from __future__ import annotations

import logging

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from . import bridge

logger = logging.getLogger(__name__)


# v3.3.11: scope items shared across BoneForge MMD ops.
_VMD_SCOPE_ITEMS = [
    ("ACTIVE", "Active Model",
     "Apply the imported VMD motion to the active MMD model only"),
    ("ALL", "All Models in Scene",
     "Apply the imported VMD motion to every MMD model in the scene "
     "(useful for multi-character cuts)"),
]


def _find_mmd_roots() -> list:
    """Return every MMD root empty in the scene."""
    return [
        obj for obj in bpy.data.objects
        if obj.type == "EMPTY"
        and getattr(obj, "mmd_type", None) == "ROOT"
    ]


class BF_OT_MMDImportPMX(Operator):
    """Import a PMX / PMD / X model via mmd_tools."""

    bl_idname = "boneforge.mmd_import_pmx"
    bl_label = "Import PMX / PMD…"
    bl_description = (
        "Import a PMX, PMD, or X model via mmd_tools. The imported "
        "model becomes the active object — use mmd_tools' own panel "
        "for further configuration of bones / morphs / rigid bodies"
    )
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.pmx;*.pmd;*.x",
        options={"HIDDEN"},
    )

    def invoke(self, context, event):
        if bridge.find_mmd_addon() is None:
            self.report(
                {"ERROR"},
                "mmd_tools not detected. Install it from BoneCraft's "
                "MMD / PMX panel first.",
            )
            return {"CANCELLED"}
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}
        if bridge.find_mmd_addon() is None:
            self.report({"ERROR"}, "mmd_tools not available")
            return {"CANCELLED"}

        try:
            # Snapshot armatures so we can identify what was added
            before = {o.name for o in bpy.data.objects
                      if o.type == "ARMATURE"}
            outcome = bpy.ops.mmd_tools.import_model(filepath=self.filepath)
            if "FINISHED" not in outcome:
                self.report({"WARNING"}, "PMX import was cancelled or did not finish")
                return {"CANCELLED"}
            after = {o.name for o in bpy.data.objects
                     if o.type == "ARMATURE"}
            new_count = len(after - before)
        except (RuntimeError, AttributeError) as exc:
            self.report({"ERROR"}, f"PMX import failed: {exc}")
            logger.exception("[BoneCraft] PMX import failed")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Imported PMX/PMD/X — {new_count} new armature(s) added",
        )
        return {"FINISHED"}


class BF_OT_MMDImportVMD(Operator):
    """Import a VMD motion onto the active or all MMD models."""

    bl_idname = "boneforge.mmd_import_vmd"
    bl_label = "Import VMD Motion…"
    bl_description = (
        "Import a VMD motion file via mmd_tools and apply it to the "
        "active MMD model — or to every MMD model in the scene"
    )
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.vmd", options={"HIDDEN"})

    # v3.3.11: scope determines whether the motion lands on the active
    # MMD model only, or every MMD model in the scene. Useful for
    # multi-character VMD captures where the same motion should drive
    # multiple avatars.
    scope: bpy.props.EnumProperty(
        name="Scope",
        description="Which MMD model(s) to apply the VMD motion to",
        items=_VMD_SCOPE_ITEMS,
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
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}
        if bridge.find_mmd_addon() is None:
            self.report({"ERROR"}, "mmd_tools not available")
            return {"CANCELLED"}

        if self.scope == "ACTIVE":
            return self._import_active(context)
        return self._import_all(context)

    def _import_active(self, context):
        try:
            bpy.ops.mmd_tools.import_vmd(filepath=self.filepath)
        except (RuntimeError, AttributeError) as exc:
            self.report({"ERROR"}, f"VMD import failed: {exc}")
            logger.exception("[BoneCraft] VMD import failed")
            return {"CANCELLED"}
        self.report({"INFO"}, "VMD motion imported onto active MMD model")
        return {"FINISHED"}

    def _import_all(self, context):
        roots = _find_mmd_roots()
        if not roots:
            self.report(
                {"WARNING"},
                "No MMD root empties found in the scene.",
            )
            return {"CANCELLED"}

        prev_active = context.view_layer.objects.active
        prev_selection = [o for o in context.selected_objects]
        applied = 0
        try:
            for root in roots:
                bpy.ops.object.select_all(action="DESELECT")
                root.select_set(True)
                context.view_layer.objects.active = root
                try:
                    bpy.ops.mmd_tools.import_vmd(filepath=self.filepath)
                    applied += 1
                except (RuntimeError, AttributeError) as exc:
                    logger.warning(
                        "[BoneCraft] VMD apply to %r failed: %s",
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

        if applied == 0:
            self.report({"WARNING"}, "No VMD applications succeeded.")
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Applied VMD to {applied} MMD model(s)",
        )
        return {"FINISHED"}


def _resolve_vpd_import_op():
    """Locate the VPD import operator on bpy.ops.mmd_tools.

    mmd_tools versions vary — recent releases expose ``import_vpd``;
    older ones routed VPD through ``import_vmd``. Returns the op
    callable or ``None`` if neither is present.
    """
    mmd_ops = getattr(bpy.ops, "mmd_tools", None)
    if mmd_ops is None:
        return None
    for op_name in ("import_vpd", "import_vmd"):
        op_func = getattr(mmd_ops, op_name, None)
        if op_func is None:
            continue
        try:
            op_func.get_rna_type()
        except (AttributeError, KeyError):
            continue
        return op_func
    return None


class BF_OT_MMDImportVPD(Operator):
    """Import a VPD pose onto the active or all MMD models."""

    bl_idname = "boneforge.mmd_import_vpd"
    bl_label = "Import VPD Pose…"
    bl_description = (
        "Import a VPD pose file via mmd_tools and apply it to the "
        "active MMD model — or to every MMD model in the scene"
    )
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.vpd", options={"HIDDEN"})

    scope: bpy.props.EnumProperty(
        name="Scope",
        description="Which MMD model(s) to apply the VPD pose to",
        items=_VMD_SCOPE_ITEMS,
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
        if _resolve_vpd_import_op() is None:
            self.report(
                {"ERROR"},
                "VPD import operator not available in this mmd_tools "
                "version.",
            )
            return {"CANCELLED"}
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}
        if bridge.find_mmd_addon() is None:
            self.report({"ERROR"}, "mmd_tools not available")
            return {"CANCELLED"}
        op_func = _resolve_vpd_import_op()
        if op_func is None:
            self.report({"ERROR"}, "VPD import op not available")
            return {"CANCELLED"}

        if self.scope == "ACTIVE":
            return self._import_active(context, op_func)
        return self._import_all(context, op_func)

    def _import_active(self, context, op_func):
        try:
            op_func(filepath=self.filepath)
        except (RuntimeError, AttributeError) as exc:
            self.report({"ERROR"}, f"VPD import failed: {exc}")
            logger.exception("[BoneCraft] VPD import failed")
            return {"CANCELLED"}
        self.report({"INFO"}, "VPD pose imported onto active MMD model")
        return {"FINISHED"}

    def _import_all(self, context, op_func):
        roots = _find_mmd_roots()
        if not roots:
            self.report(
                {"WARNING"},
                "No MMD root empties found in the scene.",
            )
            return {"CANCELLED"}

        prev_active = context.view_layer.objects.active
        prev_selection = [o for o in context.selected_objects]
        applied = 0
        try:
            for root in roots:
                bpy.ops.object.select_all(action="DESELECT")
                root.select_set(True)
                context.view_layer.objects.active = root
                try:
                    op_func(filepath=self.filepath)
                    applied += 1
                except (RuntimeError, AttributeError) as exc:
                    logger.warning(
                        "[BoneCraft] VPD apply to %r failed: %s",
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

        if applied == 0:
            self.report({"WARNING"}, "No VPD applications succeeded.")
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Applied VPD pose to {applied} MMD model(s)",
        )
        return {"FINISHED"}
