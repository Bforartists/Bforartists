"""BoneCraft VRChat CATS — Pipeline Execution State and Operation Ledger.

Owns the CATS pipeline state machine and the append-only Operation Ledger.
All CATS operators call into this module to record outcomes and check phase
completion. No bpy operators live here except the two Ledger UI actions.

Custom scene properties used:
    scene[LEDGER_KEY]  — JSON list of ledger entry dicts (capped at 200).
    scene[STATE_KEY]   — JSON dict mapping phase_id -> status string.
"""

import json
import time

import bpy
from bpy.types import Operator

# ── Constants ───────────────────────────────────────────────────────────────

LEDGER_KEY = "boneforge_cats_ledger"
STATE_KEY = "boneforge_cats_pipeline_state"

PIPELINE_PHASES = [
    "fix_model",
    "material_atlas",
    "visemes",
    "eye_tracking",
    "pose_to_shape",
    "apply_transforms",
]

OUTCOME_CHANGED = "CHANGED"
OUTCOME_CLEAN = "CLEAN"
OUTCOME_FAILED = "FAILED"


# ── Ledger helpers ──────────────────────────────────────────────────────────

def get_ledger(scene) -> list:
    """Return the current ledger as a list of entry dicts.

    Parses the JSON stored in scene[LEDGER_KEY]. Returns [] on any error
    (missing key, invalid JSON, or unexpected type).
    """
    raw = scene.get(LEDGER_KEY)
    if raw is None:
        return []
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        return []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def append_ledger(
    scene,
    op_id: str,
    status: str,
    message: str,
    params: dict = None,
) -> None:
    """Append one entry to the Operation Ledger, capped at 200 entries.

    Entry shape:
        {
            "op_id":   str,
            "status":  str,    # one of OUTCOME_* constants
            "message": str,
            "params":  dict | None,
            "time":    str,    # "HH:MM:SS"
        }
    """
    entry = {
        "op_id": op_id,
        "status": status,
        "message": message,
        "params": params,
        "time": time.strftime("%H:%M:%S"),
    }
    ledger = get_ledger(scene)
    ledger.append(entry)
    # Cap at 200 entries — drop oldest
    if len(ledger) > 200:
        ledger = ledger[-200:]
    scene[LEDGER_KEY] = json.dumps(ledger, ensure_ascii=False)


def clear_ledger(scene) -> None:
    """Reset the ledger to an empty list."""
    scene[LEDGER_KEY] = "[]"


def get_ledger_text(scene) -> str:
    """Format all ledger entries as human-readable plaintext.

    Each line: [HH:MM:SS] OP_ID | STATUS | message
    Returns an empty string when the ledger is empty.
    """
    ledger = get_ledger(scene)
    if not ledger:
        return ""
    lines = []
    for entry in ledger:
        t = entry.get("time", "--:--:--")
        op = entry.get("op_id", "?")
        st = entry.get("status", "?")
        msg = entry.get("message", "")
        lines.append(f"[{t}] {op} | {st} | {msg}")
    return "\n".join(lines)


# ── Pipeline state helpers ──────────────────────────────────────────────────

def get_pipeline_state(scene) -> dict:
    """Return the current pipeline state as a dict.

    Parses scene[STATE_KEY]. Returns {} on any error.
    """
    raw = scene.get(STATE_KEY)
    if raw is None:
        return {}
    try:
        result = json.loads(raw)
        if isinstance(result, dict):
            return result
        return {}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}


def _write_pipeline_state(scene, state: dict) -> None:
    """Serialise *state* back to the scene custom property."""
    scene[STATE_KEY] = json.dumps(state, ensure_ascii=False)


def set_phase_complete(scene, phase_id: str, status: str) -> None:
    """Mark *phase_id* with *status* in the pipeline state dict."""
    state = get_pipeline_state(scene)
    state[phase_id] = status
    _write_pipeline_state(scene, state)


def is_phase_complete(scene, phase_id: str) -> bool:
    """Return True when *phase_id* has been run (any non-FAILED status).

    A phase is considered "complete" if its stored status is CHANGED or
    CLEAN — i.e. it ran successfully. FAILED does not count as complete.
    """
    status = get_phase_status(scene, phase_id)
    return status in (OUTCOME_CHANGED, OUTCOME_CLEAN)


def get_phase_status(scene, phase_id: str):
    """Return the stored status string for *phase_id*, or None if not run."""
    state = get_pipeline_state(scene)
    return state.get(phase_id)


def reset_pipeline_state(scene) -> None:
    """Reset all pipeline phase statuses to an empty dict."""
    scene[STATE_KEY] = "{}"


# ── Operators ───────────────────────────────────────────────────────────────

class BF_OT_CATS_ClearLedger(Operator):
    """Clear all entries from the CATS Operation Ledger"""

    bl_idname = "boneforge.cats_clear_ledger"
    bl_label = "Clear Ledger"
    bl_options = {'REGISTER'}

    def execute(self, context):
        clear_ledger(context.scene)
        self.report({'INFO'}, "Ledger cleared")
        return {'FINISHED'}


class BF_OT_CATS_CopyLedger(Operator):
    """Copy the CATS Operation Ledger to the system clipboard"""

    bl_idname = "boneforge.cats_copy_ledger"
    bl_label = "Copy Ledger"
    bl_options = {'REGISTER'}

    def execute(self, context):
        context.window_manager.clipboard = get_ledger_text(context.scene)
        self.report({'INFO'}, "Ledger copied to clipboard")
        return {'FINISHED'}


# ── Registration ────────────────────────────────────────────────────────────

_classes = (
    BF_OT_CATS_ClearLedger,
    BF_OT_CATS_CopyLedger,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
