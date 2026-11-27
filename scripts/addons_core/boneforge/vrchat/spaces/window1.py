"""BoneCraft VRChat — Avatar Builder operators.

Panels removed — functionality lives in the VRChat sidebar hub subtabs
(Cleanup, Humanoid Setup, Hair Physics, Naming Convention, Clothing,
Visemes, Performance, Export).  Operators kept for potential script use.
"""

import bpy
from bpy.types import Operator

from boneforge.core import active_armature

import logging

logger = logging.getLogger(__name__)


def _strip_blender_name_suffix(object_name):
    """Remove Blender's numeric duplicate suffix from an object name."""
    if len(object_name) > 4 and object_name[-4] == ".":
        suffix = object_name[-3:]
        if suffix.isdigit():
            return object_name[:-4]
    return object_name


def _rigify_base_name(object_name):
    """Return comparable base name for metarig/control-rig pairing."""
    base_name = _strip_blender_name_suffix(object_name)
    if base_name.startswith("RIG-"):
        return base_name[4:]
    return base_name


def _looks_like_rigify_metarig(armature):
    if armature.get("boneforge_is_rigify_metarig_source", 0) == 1:
        return True
    try:
        from boneforge.autorig.quick_human import _is_rigify_metarig
    except Exception:
        return False
    return _is_rigify_metarig(armature)


def _looks_like_generated_rigify_control(armature):
    if armature.get("boneforge_generated_from_metarig"):
        return True
    return armature.name.startswith("RIG-")


def _has_generated_control_for_metarig(context, metarig):
    metarig_base_name = _rigify_base_name(metarig.name)
    for view_object in context.view_layer.objects:
        if view_object.type != "ARMATURE":
            continue
        if not _looks_like_generated_rigify_control(view_object):
            continue
        source_name = view_object.get("boneforge_generated_from_metarig")
        if source_name == metarig.name:
            return True
        if _rigify_base_name(view_object.name) == metarig_base_name:
            return True
    return False


def _view_layer_object_by_name(context, object_name):
    for view_object in context.view_layer.objects:
        if view_object.name == object_name:
            return view_object
    return None


class BF_OT_VRC_SelectBaseAvatar(Operator):
    """Select an armature as the base avatar."""

    bl_idname = "boneforge.vrc_select_base_avatar"
    bl_label = "Select Base Avatar"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(
        name="Armature",
        description="Name of the armature to select"
    )

    def execute(self, context):
        obj = _view_layer_object_by_name(context, self.armature_name)
        if obj is None:
            self.report(
                {"ERROR"},
                f"Armature '{self.armature_name}' is not in the active view layer",
            )
            return {"CANCELLED"}

        if obj.type != "ARMATURE":
            self.report({"ERROR"}, f"'{self.armature_name}' is not an armature")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        context.view_layer.objects.active = obj
        obj.select_set(True)
        if _looks_like_generated_rigify_control(obj):
            try:
                from boneforge.autorig.quick_human import (
                    _prepare_generated_control_rig_for_editing,
                )
                controller_shape_count = _prepare_generated_control_rig_for_editing(
                    context,
                    obj,
                )
                obj["boneforge_rigify_custom_shape_count"] = controller_shape_count
            except Exception as exc:
                logger.debug(
                    "[BoneCraft] could not prepare generated Rigify controls: %s",
                    exc,
                )
        self.report({"INFO"}, f"Selected armature: {self.armature_name}")
        return {"FINISHED"}


class BF_OT_VRC_QuickExport(Operator):
    """Run pre-export validation and export the avatar."""

    bl_idname = "boneforge.vrc_quick_export"
    bl_label = "Quick Export"
    bl_options = {"REGISTER"}

    def execute(self, context):
        arm = active_armature(context)
        if not arm:
            self.report({"ERROR"}, "No active armature selected")
            return {"CANCELLED"}

        try:
            result = bpy.ops.boneforge.vrc_export_to_unity()
            if result == {"CANCELLED"}:
                self.report({"WARNING"}, "Export was cancelled")
                return {"CANCELLED"}
        except RuntimeError as e:
            self.report({"ERROR"}, f"Export failed: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Avatar exported successfully")
        return {"FINISHED"}


classes = (
    BF_OT_VRC_SelectBaseAvatar,
    BF_OT_VRC_QuickExport,
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft] Failed to register {cls.__name__}: {e}")


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            logger.error(f"[BoneCraft] Failed to unregister {cls.__name__}: {e}")
