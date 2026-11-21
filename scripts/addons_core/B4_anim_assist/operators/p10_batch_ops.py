"""Batch operations: apply operators across multiple targets."""

from __future__ import annotations

import time

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

from ..core import runtime as rts_mod
from ..core.logging import get_logger
from ..core.p10_audit import log_operation
from ..core.p10_properties import get_p10
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected
from ..core.helpers import report_failure

_log = get_logger(__name__)


# ============================================================================
# Helper Function: Operator Execution
# ============================================================================


def _run_operator(op_id: str) -> bool:
    """Execute a Blender operator by its bl_idname.

    Splits the op_id on "." and uses getattr chain on bpy.ops to locate
    and call the operator with EXEC_DEFAULT context.

    Args:
        op_id: Operator bl_idname (e.g., "wm.save_as_mainfile")

    Returns:
        True if the operator returned FINISHED, False otherwise.
    """
    try:
        parts = op_id.split(".")
        if len(parts) != 2:
            _log.warning(f"Invalid op_id format: {op_id}")
            return False

        module_name, op_name = parts
        ops_module = getattr(bpy.ops, module_name, None)
        if ops_module is None:
            _log.warning(f"Unknown operator module: {module_name}")
            return False

        operator_func = getattr(ops_module, op_name, None)
        if operator_func is None:
            _log.warning(f"Unknown operator: {op_id}")
            return False

        result = operator_func("EXEC_DEFAULT")
        return "FINISHED" in result
    except Exception as e:
        _log.warning(f"Error running operator {op_id}: {e}")
        return False


# ============================================================================
# Batch Operators
# ============================================================================


class AA_OT_p10_batch_selected(Operator):
    """Batch-apply an operator to all selected pose bones."""

    bl_idname = "animassist.p10_batch_selected"
    bl_label = "Batch: Selected Targets"
    bl_description = "Apply an operator to each selected pose bone"
    bl_options = {"REGISTER", "UNDO"}

    op_id: StringProperty(  # type: ignore[valid-type]
        name="Operator ID",
        description="Operator bl_idname to run on each selected bone",
        default="",
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Require active armature in pose mode with at least one selected bone."""
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE":
            return False
        if context.mode != "POSE":
            return False
        if not context.selected_pose_bones:
            return False
        return True

    def execute(self, context: Context):
        """Run operator on each selected pose bone."""
        if not self.op_id:
            self.report({"ERROR"}, "No tool selected. Pick a tool for this shelf slot first")
            return {"CANCELLED"}

        state = rts_mod.get_state()
        state.is_batch_processing = True

        try:
            selected_bones = list(context.selected_pose_bones)
            success_count = 0
            failure_count = 0
            start_time = time.time()

            for bone in selected_bones:
                # Select this bone exclusively
                bpy.ops.pose.select_all(action="DESELECT")
                set_pose_bone_selected(bone, True)
                context.view_layer.update()

                # Run the operator
                if _run_operator(self.op_id):
                    success_count += 1
                else:
                    failure_count += 1

            elapsed_ms = (time.time() - start_time) * 1000

            # Restore original selection
            bpy.ops.pose.select_all(action="DESELECT")
            for bone in selected_bones:
                set_pose_bone_selected(bone, True)
            context.view_layer.update()

            # Log the batch operation
            detail = f"Selected bones: {len(selected_bones)}, success: {success_count}, failure: {failure_count}"
            log_operation(self.op_id, success=True, detail=detail, elapsed_ms=elapsed_ms)

            # Report summary
            msg = f"Batch applied to {len(selected_bones)} bones: {success_count} success, {failure_count} failure"
            self.report({"INFO"}, msg)
            return {"FINISHED"}

        except Exception as e:
            _log.exception(f"Error in batch_selected: {e}")
            report_failure(self, "Batch operation failed", "Undo (Ctrl+Z), check the selected targets, and run the batch again", e)
            return {"CANCELLED"}
        finally:
            state.is_batch_processing = False


class AA_OT_p10_batch_bookmarked(Operator):
    """Batch-apply an operator at each bookmarked frame."""

    bl_idname = "animassist.p10_batch_bookmarked"
    bl_label = "Batch: Bookmarked Frames"
    bl_description = "Apply an operator at each bookmarked frame"
    bl_options = {"REGISTER", "UNDO"}

    op_id: StringProperty(  # type: ignore[valid-type]
        name="Operator ID",
        description="Operator bl_idname to run at each bookmark",
        default="",
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Require a scene with bookmarks."""
        if not hasattr(context, "scene") or context.scene is None:
            return False
        if not hasattr(context.scene, "anim_assist"):
            return False
        return True

    def execute(self, context: Context):
        """Run operator at each bookmarked frame."""
        if not self.op_id:
            self.report({"ERROR"}, "No tool selected. Pick a tool for this shelf slot first")
            return {"CANCELLED"}

        state = rts_mod.get_state()
        state.is_batch_processing = True

        try:
            scene = context.scene
            bookmarks = getattr(scene.anim_assist, "bookmarks", [])

            if not bookmarks:
                self.report({"WARNING"}, "No bookmarks found")
                return {"CANCELLED"}

            original_frame = scene.frame_current
            success_count = 0
            failure_count = 0
            start_time = time.time()

            for bookmark in bookmarks:
                # Set frame to bookmark
                scene.frame_current = bookmark.frame
                context.view_layer.update()

                # Run the operator
                if _run_operator(self.op_id):
                    success_count += 1
                else:
                    failure_count += 1

            elapsed_ms = (time.time() - start_time) * 1000

            # Return to original frame
            scene.frame_current = original_frame
            context.view_layer.update()

            # Log the batch operation
            detail = f"Bookmarks: {len(bookmarks)}, success: {success_count}, failure: {failure_count}"
            log_operation(self.op_id, success=True, detail=detail, elapsed_ms=elapsed_ms)

            # Report summary
            msg = f"Batch applied at {len(bookmarks)} bookmarks: {success_count} success, {failure_count} failure"
            self.report({"INFO"}, msg)
            return {"FINISHED"}

        except Exception as e:
            _log.exception(f"Error in batch_bookmarked: {e}")
            report_failure(self, "Batch operation failed", "Undo (Ctrl+Z), check the selected targets, and run the batch again", e)
            return {"CANCELLED"}
        finally:
            state.is_batch_processing = False


class AA_OT_p10_batch_frame_steps(Operator):
    """Batch-apply an operator at regular frame intervals."""

    bl_idname = "animassist.p10_batch_frame_steps"
    bl_label = "Batch: Frame Steps"
    bl_description = "Apply an operator at regular frame intervals"
    bl_options = {"REGISTER", "UNDO"}

    op_id: StringProperty(  # type: ignore[valid-type]
        name="Operator ID",
        description="Operator bl_idname to run at each frame step",
        default="",
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Require a scene with batch operation properties."""
        if not hasattr(context, "scene") or context.scene is None:
            return False
        p10 = get_p10(context)
        return p10 is not None

    def execute(self, context: Context):
        """Run operator at frame intervals."""
        if not self.op_id:
            self.report({"ERROR"}, "No tool selected. Pick a tool for this shelf slot first")
            return {"CANCELLED"}

        p10 = get_p10(context)
        if p10 is None:
            self.report({"ERROR"}, "Workspace settings are not initialised. Run First Run Setup from Properties > Scene > Anim Assist > Setup")
            return {"CANCELLED"}

        state = rts_mod.get_state()
        state.is_batch_processing = True

        try:
            scene = context.scene
            frame_start = p10.batch_frame_start
            frame_end = p10.batch_frame_end
            frame_step = p10.batch_frame_step

            # Validate step
            if frame_step <= 0:
                self.report({"ERROR"}, "Frame step must be greater than 0")
                return {"CANCELLED"}

            # Ensure start <= end
            if frame_start > frame_end:
                frame_start, frame_end = frame_end, frame_start

            original_frame = scene.frame_current
            success_count = 0
            failure_count = 0
            frame_count = 0
            start_time = time.time()

            # Iterate through frame range with step
            current_frame = frame_start
            while current_frame <= frame_end:
                scene.frame_current = current_frame
                context.view_layer.update()
                frame_count += 1

                # Run the operator
                if _run_operator(self.op_id):
                    success_count += 1
                else:
                    failure_count += 1

                current_frame += frame_step

            elapsed_ms = (time.time() - start_time) * 1000

            # Return to original frame
            scene.frame_current = original_frame
            context.view_layer.update()

            # Log the batch operation
            detail = f"Frame range: {frame_start}-{frame_end} step {frame_step}, frames: {frame_count}, success: {success_count}, failure: {failure_count}"
            log_operation(self.op_id, success=True, detail=detail, elapsed_ms=elapsed_ms)

            # Report summary
            msg = f"Batch applied at {frame_count} frames: {success_count} success, {failure_count} failure"
            self.report({"INFO"}, msg)
            return {"FINISHED"}

        except Exception as e:
            _log.exception(f"Error in batch_frame_steps: {e}")
            report_failure(self, "Batch operation failed", "Undo (Ctrl+Z), check the selected targets, and run the batch again", e)
            return {"CANCELLED"}
        finally:
            state.is_batch_processing = False


# ============================================================================
# Registration
# ============================================================================

CLASSES = (
    AA_OT_p10_batch_selected,
    AA_OT_p10_batch_bookmarked,
    AA_OT_p10_batch_frame_steps,
)
