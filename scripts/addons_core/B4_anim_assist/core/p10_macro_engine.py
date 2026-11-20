# --- ORCHESTRATION AND RECOVERY ---
"""Macro sequencing engine for orchestration Orchestration.

Provides runtime macro execution, validation, and pre-built macro sequences
that chain together operators across multiple phases into repeatable workflows.

Public API:
    MacroStep              — dataclass defining one operator invocation
    MacroResult            — dataclass capturing execution result
    execute_macro(steps, context) — run a macro sequence
    validate_macro(steps)  — check that all op_ids exist in Blender
    build_macro_from_property(macro_entry) — convert RNA PropertyGroup to MacroStep list

Pre-built macro sequences (return list[MacroStep]):
    macro_breakdown_offset()      — breakdown breakdown then offset offset
    macro_proxy_workflow()        — proxy create proxy, bake, cleanup
    macro_switch_compensate()     — matching and space switching switch + matching and space switching match compensate
    macro_diagnose_jump()         — trajectory trajectory diagnose + navigate to issue
    macro_mirror_match()          — mirroring mirror + matching and space switching match
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

import bpy

from .logging import get_logger
from . import runtime

if TYPE_CHECKING:
    from bpy.types import Context

__all__ = [
    "MacroStep",
    "MacroResult",
    "execute_macro",
    "validate_macro",
    "build_macro_from_property",
    "macro_breakdown_offset",
    "macro_proxy_workflow",
    "macro_switch_compensate",
    "macro_diagnose_jump",
    "macro_mirror_match",
]

_log = get_logger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class MacroStep:
    """Runtime definition of one operator invocation in a macro sequence.

    Attributes:
        op_id: Operator bl_idname (e.g., "animassist.breakdown_current_frame")
        kwargs: Dictionary of operator properties to pass during execution
        enabled: Whether this step should execute (default True)
    """

    op_id: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class MacroResult:
    """Captured result of a macro execution.

    Attributes:
        success: True if all enabled steps executed without fatal error
        steps_run: Number of steps actually executed
        steps_skipped: Number of disabled steps
        errors: List of error messages, one per failed step
        elapsed_ms: Total wall-clock time in milliseconds
    """

    success: bool = False
    steps_run: int = 0
    steps_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def execute_macro(steps: list[MacroStep], context: Context) -> MacroResult:
    """Execute a sequence of macro steps with fault tolerance and undo grouping.

    Sets is_batch_processing flag before execution and wraps all steps in a
    single undo group. Each enabled step is executed in order; if a step fails,
    the error is logged and execution continues to the next step.

    Args:
        steps: List of MacroStep objects to execute
        context: Blender context for operator dispatch

    Returns:
        MacroResult with execution summary
    """
    start_time = time.time()
    result = MacroResult(success=True, steps_run=0, steps_skipped=0, errors=[])

    state = runtime.get_state()
    state.is_batch_processing = True

    try:
        # Create an undo group for the entire macro
        macro_name = f"Macro ({len([s for s in steps if s.enabled])} steps)"
        bpy.ops.ed.undo_push(message=macro_name)

        for i, step in enumerate(steps):
            if not step.enabled:
                _log.debug("Skipping disabled step %d: %s", i, step.op_id)
                result.steps_skipped += 1
                continue

            _log.debug("Executing step %d: %s with kwargs %s", i, step.op_id, step.kwargs)

            try:
                # Parse op_id into category and operator name
                parts = step.op_id.split(".")
                if len(parts) != 2:
                    error_msg = (
                        f"Step {i}: Invalid op_id format '{step.op_id}' "
                        "(expected 'category.operator')"
                    )
                    _log.error(error_msg)
                    result.errors.append(error_msg)
                    result.success = False
                    continue

                category_name, op_name = parts

                # Retrieve the operator from bpy.ops
                category = getattr(bpy.ops, category_name, None)
                if category is None:
                    error_msg = f"Step {i}: Category '{category_name}' not found in bpy.ops"
                    _log.error(error_msg)
                    result.errors.append(error_msg)
                    result.success = False
                    continue

                op_func = getattr(category, op_name, None)
                if op_func is None:
                    error_msg = (
                        f"Step {i}: Operator '{op_name}' not found in "
                        f"bpy.ops.{category_name}"
                    )
                    _log.error(error_msg)
                    result.errors.append(error_msg)
                    result.success = False
                    continue

                # Execute the operator
                op_result = op_func("EXEC_DEFAULT", **step.kwargs)
                _log.debug("Step %d executed: %s -> %s", i, step.op_id, op_result)
                result.steps_run += 1

            except Exception as exc:
                error_msg = f"Step {i} ({step.op_id}): {exc!s}"
                _log.exception("Step %d failed with exception", i)
                result.errors.append(error_msg)
                result.success = False

    finally:
        state.is_batch_processing = False
        elapsed_ms = (time.time() - start_time) * 1000.0
        result.elapsed_ms = elapsed_ms

        _log.info(
            "Macro execution complete: %d run, %d skipped, %d errors in %.1f ms",
            result.steps_run,
            result.steps_skipped,
            len(result.errors),
            elapsed_ms,
        )

    return result


def validate_macro(steps: list[MacroStep]) -> list[str]:
    """Validate that all operator IDs in a macro exist in Blender.

    Args:
        steps: List of MacroStep objects to validate

    Returns:
        List of error messages (empty if all valid)
    """
    errors: list[str] = []

    for i, step in enumerate(steps):
        if not step.enabled:
            continue

        parts = step.op_id.split(".")
        if len(parts) != 2:
            errors.append(f"Step {i}: Invalid op_id format '{step.op_id}'")
            continue

        category_name, op_name = parts

        category = getattr(bpy.ops, category_name, None)
        if category is None:
            errors.append(f"Step {i}: Category '{category_name}' not found")
            continue

        op_func = getattr(category, op_name, None)
        if op_func is None:
            errors.append(f"Step {i}: Operator 'bpy.ops.{category_name}.{op_name}' not found")
            continue

        _log.debug("Validated step %d: %s", i, step.op_id)

    _log.info("Macro validation: %d errors out of %d steps", len(errors), len(steps))
    return errors


def build_macro_from_property(macro_entry: Any) -> list[MacroStep]:
    """Convert an RNA AA_P10_MacroEntry PropertyGroup to runtime MacroStep list.

    Reads the macro_entry.steps collection and reconstructs MacroStep objects,
    deserializing kwargs from the PropertyGroup structure.

    Args:
        macro_entry: An AA_P10_MacroEntry PropertyGroup instance

    Returns:
        List of MacroStep objects ready for execution
    """
    steps: list[MacroStep] = []

    if not hasattr(macro_entry, "steps"):
        _log.warning("macro_entry has no 'steps' attribute")
        return steps

    for entry_step in macro_entry.steps:
        # Retrieve operator ID and enabled flag
        op_id = getattr(entry_step, "op_id", "")
        enabled = getattr(entry_step, "enabled", True)

        if not op_id:
            _log.warning("Skipping step with empty op_id")
            continue

        # Deserialize kwargs from property group
        kwargs_dict: dict[str, Any] = {}
        if hasattr(entry_step, "kwargs_json"):
            import json

            try:
                kwargs_str = getattr(entry_step, "kwargs_json", "{}")
                kwargs_dict = json.loads(kwargs_str)
            except (json.JSONDecodeError, ValueError) as exc:
                _log.warning("Failed to parse kwargs_json: %s", exc)

        step = MacroStep(op_id=op_id, kwargs=kwargs_dict, enabled=enabled)
        steps.append(step)
        _log.debug("Built MacroStep from property: %s (enabled=%s)", op_id, enabled)

    _log.info("Built macro with %d steps from PropertyGroup", len(steps))
    return steps


# =============================================================================
# PRE-BUILT MACRO SEQUENCES
# =============================================================================


def macro_breakdown_offset() -> list[MacroStep]:
    """Breakdown followed by offset workflow.

    Workflow:
      1. Run breakdown at current frame
      2. Run offset on selected channels

    Returns:
        List of MacroStep for breakdown + offset
    """
    return [
        MacroStep(op_id="animassist.breakdown_current_frame", kwargs={}),
        MacroStep(op_id="animassist.p4_offset_selected", kwargs={}),
    ]


def macro_proxy_workflow() -> list[MacroStep]:
    """Proxy constraint workflow: create, bake, cleanup.

    Workflow:
      1. Create proxy control
      2. Bake selected channels to proxy
      3. Clean up the proxy session

    Returns:
        List of MacroStep for proxy creation and baking
    """
    return [
        MacroStep(op_id="animassist.p7_create_proxy", kwargs={}),
        MacroStep(op_id="animassist.p7_bake_selected", kwargs={}),
        MacroStep(op_id="animassist.p7_cleanup_session", kwargs={}),
    ]


def macro_switch_compensate() -> list[MacroStep]:
    """Space switch detection and pose compensation workflow.

    Workflow:
      1. Detect all switch patterns on active object
      2. Run single-frame compensation at the current switch

    Returns:
        List of MacroStep for switch detection and compensation
    """
    return [
        MacroStep(op_id="animassist.p8_detect_all", kwargs={}),
        MacroStep(op_id="animassist.p8_compensate_single", kwargs={}),
    ]


def macro_diagnose_jump() -> list[MacroStep]:
    """Trajectory diagnosis and navigation workflow.

    Workflow:
      1. Run trajectory diagnostics to identify arc issues
      2. Jump to the next detected issue frame

    Returns:
        List of MacroStep for diagnosis and navigation
    """
    return [
        MacroStep(op_id="animassist.p5_run_diagnostics", kwargs={}),
        MacroStep(op_id="animassist.p5_jump_next_issue", kwargs={}),
    ]


def macro_mirror_match() -> list[MacroStep]:
    """Mirror and match compensation workflow.

    Workflow:
      1. Mirror the current pose to the opposite side
      2. Run single-frame compensation to blend the result

    Returns:
        List of MacroStep for mirroring and matching
    """
    return [
        MacroStep(op_id="animassist.p9_mirror_pose", kwargs={}),
        MacroStep(op_id="animassist.p8_compensate_single", kwargs={}),
    ]
