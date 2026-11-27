"""Lightweight diagnostic heuristics for FCurve key quality."""

from __future__ import annotations

from typing import Iterable

import bpy

from .context_utils import iter_visible_fcurves

__all__ = [
    "scan_density",
    "scan_redundant",
    "scan_spikes",
    "summarise",
]


def _make_diag_result(
    obj_name: str,
    fc: bpy.types.FCurve,
    frame: float,
    kind: str,
) -> dict:
    """Helper to create a diagnostic result dict with consistent structure."""
    return {
        "obj": obj_name,
        "data_path": fc.data_path,
        "array_index": fc.array_index,
        "frame": float(frame),
        "kind": kind,
    }


def scan_density(context: bpy.types.Context, min_gap: float = 1.0) -> list[dict]:
    """Detect keyframes that are closer together than *min_gap* frames (default 1.0).

    Over-keying causes jittery playback and makes cleanup operators slower.
    Reports locations where consecutive keys violate the minimum spacing threshold.
    """
    results: list[dict] = []
    for obj, action, fc in iter_visible_fcurves(context):
        kps = fc.keyframe_points
        for i in range(1, len(kps)):
            gap = kps[i].co.x - kps[i - 1].co.x
            if gap < min_gap:
                results.append(_make_diag_result(
                    obj.name, fc, kps[i].co.x, "DENSE"
                ))
    return results


def scan_redundant(context: bpy.types.Context, tol: float = 1e-4) -> list[dict]:
    """Detect keys that lie on a straight line between neighbours."""
    results: list[dict] = []
    for obj, action, fc in iter_visible_fcurves(context):
        kps = fc.keyframe_points
        for i in range(1, len(kps) - 1):
            a, b, c = kps[i - 1], kps[i], kps[i + 1]
            dx = c.co.x - a.co.x
            if abs(dx) < 1e-9:
                continue
            t = (b.co.x - a.co.x) / dx
            expected = a.co.y + t * (c.co.y - a.co.y)
            if abs(b.co.y - expected) <= tol:
                results.append(_make_diag_result(
                    obj.name, fc, b.co.x, "REDUNDANT"
                ))
    return results


def scan_spikes(context: bpy.types.Context, ratio: float = 4.0) -> list[dict]:
    """Detect keyframes with anomalous value jumps (broken motion capture artifacts).

    A keyframe is flagged as a SPIKE if the sum of distances to neighbors exceeds
    *ratio* times the baseline (the direct distance between neighbors). Typical
    spikes from bad tracking or noise have ratio >= 4.0.
    """
    results: list[dict] = []
    for obj, action, fc in iter_visible_fcurves(context):
        kps = fc.keyframe_points
        for i in range(1, len(kps) - 1):
            a, b, c = kps[i - 1], kps[i], kps[i + 1]
            d_left = abs(b.co.y - a.co.y)
            d_right = abs(c.co.y - b.co.y)
            base = max(abs(c.co.y - a.co.y), 1e-6)
            if (d_left + d_right) / base >= ratio:
                results.append(_make_diag_result(
                    obj.name, fc, b.co.x, "SPIKE"
                ))
    return results


def summarise(results: Iterable[dict]) -> dict:
    """Aggregate diagnostic results into a count breakdown by kind (DENSE, REDUNDANT, SPIKE, TOTAL).

    Useful for generating animation quality reports before cleanup batch operations.
    """
    out = {"DENSE": 0, "REDUNDANT": 0, "SPIKE": 0, "TOTAL": 0}
    for r in results:
        out[r["kind"]] = out.get(r["kind"], 0) + 1
        out["TOTAL"] += 1
    return out
