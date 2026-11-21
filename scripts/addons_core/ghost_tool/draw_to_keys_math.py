"""draw_to_keys_math.py — the geometry behind Draw to Keys (design §8 decision 15), with no bpy.

Strokes are lists of 3D points (any 3-sequence). The longest stroke is the path; every other stroke is a
timing dash. Each dash that comes within ``tolerance × path length`` of the path marks one crossing: the
path point of closest approach, reported with its arclength fraction ``t`` in [0, 1]. Crossings sorted
along the path become keys at start, start + step, start + 2·step, ...
"""

from __future__ import annotations

from typing import Optional, Sequence

Point = tuple[float, float, float]


def _sub(a, b) -> Point:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b) -> Point:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a, s: float) -> Point:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(a) -> float:
    return _dot(a, a) ** 0.5


def polyline_length(points: Sequence[Sequence[float]]) -> float:
    return sum(_length(_sub(points[i + 1], points[i])) for i in range(len(points) - 1))


def longest_stroke(strokes: Sequence[Sequence[Sequence[float]]]) -> int:
    """Index of the longest stroke (by polyline length), or -1 for none. Ties keep the first."""
    best, best_len = -1, -1.0
    for index, stroke in enumerate(strokes):
        length = polyline_length(stroke)
        if length > best_len:
            best, best_len = index, length
    return best


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def closest_points_between_segments(p1, q1, p2, q2) -> tuple[float, float, float]:
    """(s, t, distance): parameters on segment p1-q1 and p2-q2 of their closest points (Ericson, RTCD 5.1.9)."""
    d1, d2, r = _sub(q1, p1), _sub(q2, p2), _sub(p1, p2)
    a, e, f = _dot(d1, d1), _dot(d2, d2), _dot(d2, r)
    eps = 1e-12
    if a <= eps and e <= eps:
        return 0.0, 0.0, _length(r)
    if a <= eps:
        s, t = 0.0, _clamp01(f / e)
    else:
        c = _dot(d1, r)
        if e <= eps:
            t, s = 0.0, _clamp01(-c / a)
        else:
            b = _dot(d1, d2)
            denom = a * e - b * b
            s = _clamp01((b * f - c * e) / denom) if denom > eps else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, _clamp01(-c / a)
            elif t > 1.0:
                t, s = 1.0, _clamp01((b - c) / a)
    c1 = _add(p1, _scale(d1, s))
    c2 = _add(p2, _scale(d2, t))
    return s, t, _length(_sub(c1, c2))


def point_segment_distance(p, a, b) -> float:
    ab = _sub(b, a)
    denom = _dot(ab, ab)
    s = _clamp01(_dot(_sub(p, a), ab) / denom) if denom > 1e-12 else 0.0
    return _length(_sub(p, _add(a, _scale(ab, s))))


def _zone_entry(a, b, p, q, t_closest: float, max_distance: float) -> float:
    """Smallest u in [0, t_closest] where the dash point p + u (q - p) is within ``max_distance`` of segment
    a-b. The distance from a point moving on a line to a segment is convex in u, and it is within the
    tolerance at t_closest, so it only falls on [0, t_closest]: bisection finds the entry exactly."""
    def inside(u):
        return point_segment_distance(_add(p, _scale(_sub(q, p), u)), a, b) <= max_distance
    if inside(0.0):
        return 0.0
    lo, hi = 0.0, t_closest
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if inside(mid):
            hi = mid
        else:
            lo = mid
    return hi


def dash_crossing(path: Sequence[Sequence[float]], dash: Sequence[Sequence[float]],
                  max_distance: float) -> Optional[tuple[float, Point]]:
    """(arclength along the path, path point) of the path leg ``dash`` reaches first, or None.

    Walking the dash from its first point, the crossing belongs to the path segment whose tolerance zone
    (within ``max_distance``) the dash enters first; it is reported at that segment's closest approach.
    A dash that wiggles across twice counts once."""
    cumulative = [0.0]
    for i in range(len(path) - 1):
        cumulative.append(cumulative[-1] + _length(_sub(path[i + 1], path[i])))
    for j in range(len(dash) - 1):
        # Order by where the dash enters each leg's tolerance zone, not by its closest approach: a dash can be
        # inside one leg's zone before it reaches another leg's closer point (review 976236d6).
        best = None
        for i in range(len(path) - 1):
            s, t, distance = closest_points_between_segments(path[i], path[i + 1], dash[j], dash[j + 1])
            if distance > max_distance:
                continue
            entry = _zone_entry(path[i], path[i + 1], dash[j], dash[j + 1], t, max_distance)
            if best is None or (entry, distance) < best[0]:
                best = ((entry, distance), i, s)
        if best is not None:
            _order, i, s = best
            point = _add(path[i], _scale(_sub(path[i + 1], path[i]), s))
            return cumulative[i] + s * (cumulative[i + 1] - cumulative[i]), point
    return None


def crossings(path: Sequence[Sequence[float]], dashes: Sequence[Sequence[Sequence[float]]],
              tolerance: float) -> list[tuple[float, Point]]:
    """(t in [0, 1], path point) for every dash that crosses the path, sorted along the path.
    A dash counts when its closest approach is within ``tolerance × path length``."""
    length = polyline_length(path)
    if length <= 0.0 or len(path) < 2:
        return []
    found = []
    for dash in dashes:
        if len(dash) < 2:
            continue
        hit = dash_crossing(path, dash, tolerance * length)
        if hit is not None:
            found.append((hit[0] / length, hit[1]))
    return sorted(found, key=lambda item: item[0])


def frames_from_crossings(count: int, start: float, step: float) -> list[float]:
    """Key frames for ``count`` crossings: start, start + step, ..."""
    return [start + i * step for i in range(count)]
