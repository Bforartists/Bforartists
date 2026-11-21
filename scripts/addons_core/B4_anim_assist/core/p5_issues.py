# --- TRAJECTORY VISUALIZATION ---
"""Arc issue detection heuristics.

Each detector takes a list of :class:`SamplePoint` (and optionally
derived velocity data) and returns a list of :class:`IssueMarker`.
Detectors are pure functions — no bpy dependency, no side effects.

Issue types are string constants so the UI can filter and colour them
without importing this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .p5_sampling import SamplePoint, derive_velocity, segment_lengths

__all__ = [
    "IssueMarker",
    "ISSUE_ARC_DRIFT",
    "ISSUE_FLAT_ARC",
    "ISSUE_ZIGZAG",
    "ISSUE_POP",
    "ISSUE_OVERSPACED",
    "ISSUE_UNDERSPACED",
    "ISSUE_DIRECTION_REVERSAL",
    "ISSUE_STOP",
    "ISSUE_CONTACT",
    "ISSUE_APEX",
    "ALL_ISSUE_TYPES",
    "detect_arc_drift",
    "detect_flat_arc",
    "detect_zigzag",
    "detect_pop",
    "detect_spacing_issues",
    "detect_direction_reversal",
    "detect_stops",
    "detect_apex_and_contacts",
    "run_all_detectors",
    "arc_quality_score",
]


# ---------------------------------------------------------------------------
# Issue types
# ---------------------------------------------------------------------------

ISSUE_ARC_DRIFT = "ARC_DRIFT"
ISSUE_FLAT_ARC = "FLAT_ARC"
ISSUE_ZIGZAG = "ZIGZAG"
ISSUE_POP = "POP"
ISSUE_OVERSPACED = "OVERSPACED"
ISSUE_UNDERSPACED = "UNDERSPACED"
ISSUE_DIRECTION_REVERSAL = "DIRECTION_REVERSAL"
ISSUE_STOP = "STOP"
ISSUE_CONTACT = "CONTACT"
ISSUE_APEX = "APEX"

ALL_ISSUE_TYPES: tuple[str, ...] = (
    ISSUE_ARC_DRIFT,
    ISSUE_FLAT_ARC,
    ISSUE_ZIGZAG,
    ISSUE_POP,
    ISSUE_OVERSPACED,
    ISSUE_UNDERSPACED,
    ISSUE_DIRECTION_REVERSAL,
    ISSUE_STOP,
    ISSUE_CONTACT,
    ISSUE_APEX,
)


@dataclass
class IssueMarker:
    """One detected issue on the trajectory."""

    frame: float
    world_pos: tuple[float, float, float]
    issue_type: str
    severity: float  # 0.0–1.0
    message: str
    # Optional: index into the samples list for key-selection operators.
    sample_index: int = -1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vector_subtract(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Subtract vector b from vector a."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vector_dot_product(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> float:
    """Compute the dot product of vectors a and b."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vec_len(a: tuple[float, float, float]) -> float:
    """Compute the Euclidean length of vector a."""
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _vector_cross_product(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Compute the cross product of vectors a and b (right-hand rule)."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _median(values: list[float]) -> float:
    """Compute the median of a list of floats."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------

def detect_arc_drift(
    samples: list[SamplePoint],
    *,
    tolerance: float = 0.05,
    window: int = 5,
) -> list[IssueMarker]:
    """Detect points that deviate from a locally-fit arc.

    Uses a sliding 3-point circle fit: for each interior point, compute
    the circumradius of (p[i-w], p[i], p[i+w]).  The deviation is the
    distance of p[i] from the circumcircle centre minus the radius.
    """
    issues: list[IssueMarker] = []
    n = len(samples)
    if n < 3:
        return issues

    half = max(window // 2, 1)
    for i in range(half, n - half):
        a = samples[i - half].world_pos
        b = samples[i].world_pos
        c = samples[i + half].world_pos

        ab = _vector_subtract(b, a)
        ac = _vector_subtract(c, a)
        cross = _vector_cross_product(ab, ac)
        cross_len = _vec_len(cross)
        if cross_len < 1e-12:
            continue  # Collinear — no arc to measure against.

        ab_len = _vec_len(ab)
        bc = _vector_subtract(c, b)
        bc_len = _vec_len(bc)
        ac_len = _vec_len(ac)

        if ab_len < 1e-12 or bc_len < 1e-12:
            continue

        # Circumradius of triangle A-B-C using the formula R = |AB||BC||AC| / (2|AB×AC|).
        # This is the radius of the circle passing through all three points.
        R = (ab_len * bc_len * ac_len) / (2.0 * cross_len)

        # Compute the perpendicular distance of B from the line A→C.
        # This measures how far B deviates from a straight path A→C.
        # t is the projection parameter; proj is the closest point on line A→C.
        t = _vector_dot_product(ab, ac) / max(_vector_dot_product(ac, ac), 1e-12)
        proj = (a[0] + t * ac[0], a[1] + t * ac[1], a[2] + t * ac[2])
        deviation = _vec_len(_vector_subtract(b, proj))

        # Normalise by R so the threshold is scale-independent.
        if R > 1e-6:
            norm_dev = deviation / R
        else:
            norm_dev = deviation

        if norm_dev > tolerance:
            severity = min(norm_dev / (tolerance * 3.0), 1.0)
            issues.append(IssueMarker(
                frame=samples[i].frame,
                world_pos=samples[i].world_pos,
                issue_type=ISSUE_ARC_DRIFT,
                severity=severity,
                message=f"Arc drift {norm_dev:.3f} (threshold {tolerance:.3f})",
                sample_index=i,
            ))

    return issues


def detect_flat_arc(
    samples: list[SamplePoint],
    *,
    threshold: float = 0.01,
    window: int = 10,
) -> list[IssueMarker]:
    """Detect stretches where the path is nearly flat (no arc curvature)."""
    issues: list[IssueMarker] = []
    n = len(samples)
    if n < window:
        return issues

    for start in range(0, n - window + 1, max(window // 2, 1)):
        end = min(start + window, n)
        chunk = samples[start:end]

        # Compute variance along each axis (X, Y, Z). This measures how much
        # the trajectory spreads in each direction. Low variance on all axes
        # indicates the path is confined to a small region (flat/linear).
        means = [0.0, 0.0, 0.0]
        for s in chunk:
            means[0] += s.world_pos[0]
            means[1] += s.world_pos[1]
            means[2] += s.world_pos[2]
        chunk_count = len(chunk)
        means = [m / chunk_count for m in means]

        var = [0.0, 0.0, 0.0]
        for s in chunk:
            for ax in range(3):
                d = s.world_pos[ax] - means[ax]
                var[ax] += d * d
        var = [v / chunk_count for v in var]

        # Sort variances and check the two smallest. If both are below threshold,
        # the path is confined to a 1D line (the direction with the largest variance).
        # This indicates a flat arc with no meaningful curvature.
        sorted_var = sorted(var)
        if sorted_var[0] < threshold and sorted_var[1] < threshold:
            mid = chunk[len(chunk) // 2]
            issues.append(IssueMarker(
                frame=mid.frame,
                world_pos=mid.world_pos,
                issue_type=ISSUE_FLAT_ARC,
                severity=0.5,
                message=f"Flat arc segment (var {sorted_var[1]:.4f})",
                sample_index=start + len(chunk) // 2,
            ))

    return issues


def detect_zigzag(
    samples: list[SamplePoint],
    *,
    min_reversals: int = 3,
    window: int = 8,
) -> list[IssueMarker]:
    """Detect zig-zag patterns (frequent direction changes in a small window).

    Zigzags indicate unintended direction reversals that create visual pops or
    stuttering in motion. Commonly caused by over-correction or competing constraints
    in arcs. Detects by counting velocity dot-product sign flips within a sliding window.
    """
    issues: list[IssueMarker] = []
    vels = derive_velocity(samples)
    if len(vels) < window:
        return issues

    for start in range(0, len(vels) - window + 1):
        chunk = vels[start:start + window]
        reversals = 0
        for i in range(1, len(chunk)):
            dot = _vector_dot_product(chunk[i].velocity, chunk[i - 1].velocity)
            if dot < 0.0:
                reversals += 1
        if reversals >= min_reversals:
            mid = chunk[len(chunk) // 2]
            issues.append(IssueMarker(
                frame=mid.frame,
                world_pos=mid.world_pos,
                issue_type=ISSUE_ZIGZAG,
                severity=min(reversals / (min_reversals * 2.0), 1.0),
                message=f"Zig-zag ({reversals} reversals in {window} frames)",
                sample_index=start + len(chunk) // 2,
            ))

    return issues


def detect_pop(
    samples: list[SamplePoint],
    *,
    ratio: float = 4.0,
) -> list[IssueMarker]:
    """Detect sudden speed jumps (pops) between consecutive samples."""
    issues: list[IssueMarker] = []
    vels = derive_velocity(samples)
    if len(vels) < 3:
        return issues

    speeds = [v.speed for v in vels]
    med = _median(speeds)
    if med <= 0.0:
        return issues

    for i, v in enumerate(vels):
        if v.speed > med * ratio:
            issues.append(IssueMarker(
                frame=v.frame,
                world_pos=v.world_pos,
                issue_type=ISSUE_POP,
                severity=min(v.speed / (med * ratio * 2.0), 1.0),
                message=f"Pop: speed {v.speed:.3f} vs median {med:.3f}",
                sample_index=i + 1,
            ))

    return issues


def detect_spacing_issues(
    samples: list[SamplePoint],
    *,
    hi_ratio: float = 1.8,
    lo_ratio: float = 0.4,
) -> list[IssueMarker]:
    """Detect over-spaced and under-spaced segments."""
    issues: list[IssueMarker] = []
    lengths = segment_lengths(samples)
    if not lengths:
        return issues

    med = _median(lengths)
    if med <= 0.0:
        return issues

    for i, seg_len in enumerate(lengths):
        r = seg_len / med
        if r > hi_ratio:
            issues.append(IssueMarker(
                frame=samples[i + 1].frame,
                world_pos=samples[i + 1].world_pos,
                issue_type=ISSUE_OVERSPACED,
                severity=min((r - hi_ratio) / hi_ratio, 1.0),
                message=f"Overspaced: {r:.2f}x median",
                sample_index=i + 1,
            ))
        elif r < lo_ratio:
            issues.append(IssueMarker(
                frame=samples[i + 1].frame,
                world_pos=samples[i + 1].world_pos,
                issue_type=ISSUE_UNDERSPACED,
                severity=min((lo_ratio - r) / lo_ratio, 1.0),
                message=f"Underspaced: {r:.2f}x median",
                sample_index=i + 1,
            ))

    return issues


def detect_direction_reversal(
    samples: list[SamplePoint],
) -> list[IssueMarker]:
    """Detect points where the velocity direction reverses (dot < 0)."""
    issues: list[IssueMarker] = []
    vels = derive_velocity(samples)
    if len(vels) < 2:
        return issues

    for i in range(1, len(vels)):
        dot = _vector_dot_product(vels[i].velocity, vels[i - 1].velocity)
        if dot < 0.0:
            issues.append(IssueMarker(
                frame=vels[i].frame,
                world_pos=vels[i].world_pos,
                issue_type=ISSUE_DIRECTION_REVERSAL,
                severity=min(abs(dot) / max(_vec_len(vels[i].velocity), 1e-6), 1.0),
                message="Direction reversal",
                sample_index=i + 1,
            ))

    return issues


def detect_stops(
    samples: list[SamplePoint],
    *,
    threshold: float = 0.001,
) -> list[IssueMarker]:
    """Detect near-zero-speed holds (stops).

    Stops indicate unintended freezes where motion halts abruptly. Can represent
    unnatural hold frames or failure of continuous movement. Some holds may be
    intentional (contact, setup), but unexpected stops in arcs break smoothness.
    Detects by checking velocity magnitude against a threshold.
    """
    issues: list[IssueMarker] = []
    vels = derive_velocity(samples)
    for i, v in enumerate(vels):
        if v.speed < threshold:
            issues.append(IssueMarker(
                frame=v.frame,
                world_pos=v.world_pos,
                issue_type=ISSUE_STOP,
                severity=0.3,
                message=f"Stop (speed {v.speed:.5f})",
                sample_index=i + 1,
            ))
    return issues


def detect_apex_and_contacts(
    samples: list[SamplePoint],
    *,
    gravity_axis: int = 2,  # Z by default
) -> list[IssueMarker]:
    """Detect local maxima (apex) and minima (contact) on the gravity axis.

    Apex marks the peak of arcs where weight shifts to highest point; used for
    arc spacing review and pose refinement. Contact marks ground touches or lowest
    points; timing of contacts critical for weight distribution and step cycles.
    Useful for validating timing of weight shifts and floor interaction moments.
    """
    issues: list[IssueMarker] = []
    if len(samples) < 3:
        return issues

    for i in range(1, len(samples) - 1):
        prev_v = samples[i - 1].world_pos[gravity_axis]
        curr_v = samples[i].world_pos[gravity_axis]
        next_v = samples[i + 1].world_pos[gravity_axis]

        if curr_v > prev_v and curr_v > next_v:
            issues.append(IssueMarker(
                frame=samples[i].frame,
                world_pos=samples[i].world_pos,
                issue_type=ISSUE_APEX,
                severity=0.2,
                message="Apex (local max on gravity axis)",
                sample_index=i,
            ))
        elif curr_v < prev_v and curr_v < next_v:
            issues.append(IssueMarker(
                frame=samples[i].frame,
                world_pos=samples[i].world_pos,
                issue_type=ISSUE_CONTACT,
                severity=0.2,
                message="Contact (local min on gravity axis)",
                sample_index=i,
            ))

    return issues


# ---------------------------------------------------------------------------
# Aggregate runner
# ---------------------------------------------------------------------------

def run_all_detectors(
    samples: list[SamplePoint],
    *,
    drift_tolerance: float = 0.05,
    flat_threshold: float = 0.01,
    zigzag_count: int = 3,
    pop_ratio: float = 4.0,
    spacing_hi: float = 1.8,
    spacing_lo: float = 0.4,
    stop_threshold: float = 0.001,
    enable_drift: bool = True,
    enable_flat: bool = True,
    enable_zigzag: bool = True,
    enable_pop: bool = True,
    enable_spacing: bool = True,
    enable_reversal: bool = True,
    enable_stops: bool = True,
    enable_apex_contact: bool = True,
) -> list[IssueMarker]:
    """Run all enabled detectors and return a merged, frame-sorted issue list."""
    all_issues: list[IssueMarker] = []

    if enable_drift:
        all_issues.extend(detect_arc_drift(samples, tolerance=drift_tolerance))
    if enable_flat:
        all_issues.extend(detect_flat_arc(samples, threshold=flat_threshold))
    if enable_zigzag:
        all_issues.extend(detect_zigzag(samples, min_reversals=zigzag_count))
    if enable_pop:
        all_issues.extend(detect_pop(samples, ratio=pop_ratio))
    if enable_spacing:
        all_issues.extend(detect_spacing_issues(
            samples, hi_ratio=spacing_hi, lo_ratio=spacing_lo,
        ))
    if enable_reversal:
        all_issues.extend(detect_direction_reversal(samples))
    if enable_stops:
        all_issues.extend(detect_stops(samples, threshold=stop_threshold))
    if enable_apex_contact:
        all_issues.extend(detect_apex_and_contacts(samples))

    all_issues.sort(key=lambda m: m.frame)
    return all_issues


# ---------------------------------------------------------------------------
# Arc quality score
# ---------------------------------------------------------------------------

def arc_quality_score(
    samples: list[SamplePoint],
    issues: list[IssueMarker] | None = None,
) -> float:
    """Estimate an overall arc quality score in 0–100.

    Higher is better. Penalises by issue count and severity, weighted by
    sample count so the score is scale-independent.
    """
    if not samples:
        return 0.0

    if issues is None:
        issues = run_all_detectors(samples)

    if not issues:
        return 100.0

    total_severity = sum(m.severity for m in issues)
    penalty = total_severity / max(len(samples), 1) * 50.0
    return max(0.0, min(100.0, 100.0 - penalty))
