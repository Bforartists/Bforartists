"""BoneCraft Task Board — Debounced analysis engine.

The analyzer maintains a per-armature result cache keyed by a lightweight
state fingerprint (bone count + deform-bone count + child mesh count).
Re-analysis is triggered only when the fingerprint changes, preventing
viewport stutter on every draw call.

Public API
----------
get_tasks(armature_obj) -> list[BF_Task]
    Return the cached (or freshly computed) task list for the armature.

get_quick_wins(armature_obj, n=3) -> list[BF_Task]
    Return the top-n tasks ranked by quick_win_score.

get_health_score(armature_obj) -> tuple[int, str]
    Return (0-100 score, label) summarising overall rig health.

invalidate(armature_name)
    Force the next get_tasks() call to re-run analysis.
"""

import bpy
import logging
from .tasks import ALL_CHECKS, CATEGORY_ORDER

logger = logging.getLogger(__name__)

# ── Cache ─────────────────────────────────────────────────────
# Maps armature_obj.name → (_Fingerprint, list[BF_Task])

_cache: dict = {}


class _Fingerprint:
    """Lightweight snapshot of the facts that matter for analysis."""

    __slots__ = ("bone_count", "deform_count", "child_mesh_count")

    def __init__(self, armature_obj):
        self.bone_count = len(armature_obj.data.bones)
        self.deform_count = sum(
            1 for b in armature_obj.data.bones if b.use_deform
        )
        # Count mesh children via armature_obj.children (faster than bpy.data.objects).
        self.child_mesh_count = sum(
            1 for obj in armature_obj.children
            if obj.type == 'MESH'
        )

    def __eq__(self, other):
        if not isinstance(other, _Fingerprint):
            return False
        return (
            self.bone_count      == other.bone_count
            and self.deform_count    == other.deform_count
            and self.child_mesh_count == other.child_mesh_count
        )


# ── Internal analysis runner ──────────────────────────────────

def _run_analysis(armature_obj) -> list:
    """Run all check functions and return a merged, sorted task list."""
    tasks = []
    for check_fn in ALL_CHECKS:
        try:
            results = check_fn(armature_obj)
            tasks.extend(results)
        except Exception as exc:
            logger.debug(f"[BoneCraft Analyzer] {check_fn.__name__} raised: {exc}")

    # Sort: errors first, then warnings, then suggestions.
    # Within each status group sort by impact descending.
    status_order = {"error": 0, "warning": 1, "suggestion": 2}
    tasks.sort(
        key=lambda t: (status_order.get(t.status, 9), -t.impact)
    )
    return tasks


# ── Public API ────────────────────────────────────────────────

def get_tasks(armature_obj) -> list:
    """Return the task list for *armature_obj*, running analysis if stale.

    Safe to call on every panel draw — returns the cached result when
    the rig fingerprint has not changed.
    """
    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return []

    name = armature_obj.name
    fp   = _Fingerprint(armature_obj)

    cached = _cache.get(name)
    if cached is not None and cached[0] == fp:
        return cached[1]

    tasks = _run_analysis(armature_obj)
    _cache[name] = (fp, tasks)
    logger.debug(f"[BoneCraft Analyzer] {name}: {len(tasks)} task(s) found")
    return tasks


def get_quick_wins(armature_obj, n: int = 3) -> list:
    """Return the top-n tasks ranked by quick_win_score (impact / effort)."""
    tasks = get_tasks(armature_obj)
    sorted_tasks = sorted(tasks, key=lambda t: t.quick_win_score, reverse=True)
    return sorted_tasks[:n]


def get_health_score(armature_obj) -> tuple:
    """Compute a 0–100 health score and a label from the current task list.

    Scoring heuristic:
        Start at 100.
        Subtract 15 per ERROR task (capped at -60).
        Subtract 7  per WARNING task (capped at -35).
        Subtract 2  per SUGGESTION task (capped at -10).

    Returns (score, label) where label is one of:
        "Excellent", "Good", "Needs work", "Critical"
    """
    tasks = get_tasks(armature_obj)
    if not tasks:
        return (100, "Excellent")

    errors      = sum(1 for t in tasks if t.status == "error")
    warnings    = sum(1 for t in tasks if t.status == "warning")
    suggestions = sum(1 for t in tasks if t.status == "suggestion")

    penalty = (
        min(errors      * 15, 60)
        + min(warnings  *  7, 35)
        + min(suggestions * 2, 10)
    )
    score = max(0, 100 - penalty)

    if score >= 90:
        label = "Excellent"
    elif score >= 70:
        label = "Good"
    elif score >= 40:
        label = "Needs work"
    else:
        label = "Critical"

    return (score, label)


def get_tasks_by_category(armature_obj) -> dict:
    """Return tasks grouped by category in display order.

    Returns an OrderedDict-like list of (category, [tasks]) pairs.
    """
    tasks = get_tasks(armature_obj)
    grouped: dict = {}
    for task in tasks:
        grouped.setdefault(task.category, []).append(task)

    # Return in canonical CATEGORY_ORDER, skipping empty categories.
    return [
        (cat, grouped[cat])
        for cat in CATEGORY_ORDER
        if cat in grouped
    ]


def invalidate(armature_name: str) -> None:
    """Remove the cached result for *armature_name*, forcing re-analysis."""
    _cache.pop(armature_name, None)


def invalidate_all() -> None:
    """Clear the entire cache (e.g., after a major rig operation)."""
    _cache.clear()
