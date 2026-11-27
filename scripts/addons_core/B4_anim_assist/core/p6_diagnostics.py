# --- RETIMING AND TIMING DIAGNOSTICS ---
"""Timing diagnostics: gap detection, cluster detection, spacing analysis.

All public functions are pure-Python with no bpy side-effects so they can
be called from operators, tests, and draw callbacks without risk of
triggering undo events.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = [
    "TimingGap",
    "KeyCluster",
    "TimingDiagnostics",
    "collect_unique_frames",
    "collect_frames_in_range",
    "detect_timing_gaps",
    "detect_key_clusters",
    "score_timing",
    "run_diagnostics",
    "format_diagnostics_report",
]


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TimingGap:
    """A gap between two consecutive keyframe groups wider than the threshold."""

    start_frame: float
    end_frame: float

    @property
    def size(self) -> float:
        """Return the gap's frame span — how many frames of dead time exist."""
        return self.end_frame - self.start_frame

    @property
    def mid_frame(self) -> float:
        """Return the gap's midpoint frame for UI label placement."""
        return (self.start_frame + self.end_frame) / 2.0

    def __str__(self) -> str:
        return f"Gap {self.start_frame:.0f}→{self.end_frame:.0f} ({self.size:.0f}f)"


@dataclass
class KeyCluster:
    """A group of two or more keys within a short frame radius."""

    frames: list[float] = field(default_factory=list)

    @property
    def size(self) -> int:
        """Return the number of frames in the cluster."""
        return len(self.frames)

    @property
    def mid_frame(self) -> float:
        """Return the average frame position of all keys in the cluster."""
        return sum(self.frames) / len(self.frames) if self.frames else 0.0

    @property
    def center(self) -> float:
        """Return the average frame position of all keys in the cluster."""
        return sum(self.frames) / len(self.frames) if self.frames else 0.0

    @property
    def spread(self) -> float:
        """Return the frame span from minimum to maximum key in the cluster."""
        if len(self.frames) < 2:
            return 0.0
        return max(self.frames) - min(self.frames)

    def __str__(self) -> str:
        return (
            f"Cluster {len(self.frames)} keys @ ~{self.center:.0f}f "
            f"(spread {self.spread:.1f}f)"
        )


@dataclass
class TimingDiagnostics:
    """Full diagnostics result for one pass over an FCurve set."""

    gaps: list[TimingGap] = field(default_factory=list)
    clusters: list[KeyCluster] = field(default_factory=list)
    score: float = -1.0
    key_count: int = 0
    frame_span: float = 0.0
    avg_spacing: float = 0.0
    spacing_variance: float = 0.0

    @property
    def has_issues(self) -> bool:
        """Return True when either gaps or clusters violate the timing thresholds."""
        return bool(self.gaps) or bool(self.clusters)

    @property
    def result_enum(self) -> str:
        """Return the matching ``DIAG_RESULT_ITEMS`` enum identifier."""
        if self.score < 0:
            return "NONE"
        if not self.has_issues:
            return "CLEAN"
        if self.gaps and self.clusters:
            return "BOTH"
        if self.gaps:
            return "GAPS"
        return "CLUSTERS"


# ---------------------------------------------------------------------------
# Frame collection helpers
# ---------------------------------------------------------------------------

def collect_unique_frames(fcurves) -> list[float]:
    """Return sorted unique keyframe x values across all FCurves."""
    frames: set[float] = set()
    for fc in fcurves:
        for kp in fc.keyframe_points:
            frames.add(kp.co.x)
    return sorted(frames)


def collect_frames_in_range(
    fcurves,
    lo: float,
    hi: float,
) -> list[float]:
    """Return sorted unique keyframe x values within [lo, hi]."""
    frames: set[float] = set()
    for fc in fcurves:
        for kp in fc.keyframe_points:
            if lo <= kp.co.x <= hi:
                frames.add(kp.co.x)
    return sorted(frames)


# ---------------------------------------------------------------------------
# Detection algorithms
# ---------------------------------------------------------------------------

def detect_timing_gaps(
    fcurves,
    threshold: float = 4.0,
) -> list[TimingGap]:
    """Return inter-keyframe gaps wider than *threshold* frames.

    Only considers the *combined* set of unique frames across all FCurves,
    so a gap is reported only when no FCurve has a key in that window.
    """
    frames = collect_unique_frames(fcurves)
    if len(frames) < 2:
        return []

    gaps: list[TimingGap] = []
    for a, b in zip(frames[:-1], frames[1:]):
        if b - a >= threshold:
            gaps.append(TimingGap(start_frame=a, end_frame=b))
    return gaps


def detect_key_clusters(
    fcurves,
    radius: float = 2.0,
) -> list[KeyCluster]:
    """Return groups of 2+ consecutive unique frame values within *radius*.

    Uses a simple single-pass sweep: when the next frame is ≤ radius from
    the last accumulated frame, it joins the current cluster; otherwise the
    cluster is closed and a new one begins.
    """
    frames = collect_unique_frames(fcurves)
    if not frames:
        return []

    clusters: list[KeyCluster] = []
    current: list[float] = [frames[0]]

    for f in frames[1:]:
        if f - current[-1] <= radius:
            current.append(f)
        else:
            if len(current) >= 2:
                clusters.append(KeyCluster(frames=list(current)))
            current = [f]

    if len(current) >= 2:
        clusters.append(KeyCluster(frames=list(current)))

    return clusters


# ---------------------------------------------------------------------------
# Timing score
# ---------------------------------------------------------------------------

def score_timing(frames: list[float]) -> float:
    """Return a regularity score from 0 to 100.

    100 means perfectly even spacing; lower scores indicate increasing
    irregularity.  The score is based on the coefficient of variation (CV)
    of inter-key spacings: CV = σ / μ.  A CV of 0 maps to 100; a CV ≥ 1
    (100 % standard deviation) maps to 0.
    """
    if len(frames) < 2:
        return 100.0

    spacings = [b - a for a, b in zip(frames[:-1], frames[1:])]
    avg = sum(spacings) / len(spacings)
    if avg <= 0.0:
        return 0.0

    variance = sum((s - avg) ** 2 for s in spacings) / len(spacings)
    cv = math.sqrt(variance) / avg
    score = max(0.0, 100.0 * (1.0 - min(cv, 1.0)))
    return round(score, 1)


# ---------------------------------------------------------------------------
# Unified runner
# ---------------------------------------------------------------------------

def run_diagnostics(
    fcurves,
    gap_threshold: float = 4.0,
    cluster_radius: float = 2.0,
) -> TimingDiagnostics:
    """Run a full timing diagnostic pass and return a :class:`TimingDiagnostics`.

    All three sub-algorithms (gap detection, cluster detection, timing score)
    are run in a single pass over the unique frame list.
    """
    frames = collect_unique_frames(fcurves)
    diag = TimingDiagnostics()
    diag.key_count = len(frames)

    if frames:
        diag.frame_span = frames[-1] - frames[0]
        if len(frames) >= 2:
            spacings = [b - a for a, b in zip(frames[:-1], frames[1:])]
            diag.avg_spacing = sum(spacings) / len(spacings)
            diag.spacing_variance = (
                sum((s - diag.avg_spacing) ** 2 for s in spacings) / len(spacings)
            )

    diag.gaps     = detect_timing_gaps(fcurves, threshold=gap_threshold)
    diag.clusters = detect_key_clusters(fcurves, radius=cluster_radius)
    diag.score    = score_timing(frames)
    return diag


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_diagnostics_report(diag: TimingDiagnostics, label: str = "") -> str:
    """Return a multi-line human-readable diagnostics report."""
    lines: list[str] = []
    if label:
        lines.append(f"=== {label} ===")
    lines.append(
        f"Keys: {diag.key_count}  |  Span: {diag.frame_span:.0f}f  "
        f"|  Avg spacing: {diag.avg_spacing:.1f}f"
    )
    lines.append(f"Timing Score: {diag.score:.0f}/100")

    # Gaps section
    if diag.gaps:
        lines.append(f"Gaps ({len(diag.gaps)}):")
        for g in diag.gaps:
            lines.append(
                f"  {g.start_frame:.0f} → {g.end_frame:.0f}  ({g.size:.0f}f gap)"
            )
    else:
        lines.append("No significant gaps.")

    # Clusters section
    if diag.clusters:
        lines.append(f"Clusters ({len(diag.clusters)}):")
        for c in diag.clusters:
            lines.append(
                f"  {len(c.frames)} keys near frame {c.center:.0f} "
                f"(spread {c.spread:.1f}f)"
            )
    else:
        lines.append("No key clusters.")

    return "\n".join(lines)
