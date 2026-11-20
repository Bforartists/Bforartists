"""Pure math logic for Curve Tools operators (no bpy)."""

from __future__ import annotations

from .utils import EPSILON, KeyData, find_neighbors, lerp, smoothstep

__all__ = [
    "blend_toward_value",
    "blend_offset",
    "ease_to_ease",
    "blend_to_neighbor",
    "push_pull",
    "smooth_keys",
]


def blend_toward_value(
    selected_keys: list[KeyData],
    reference_value: float,
    factor: float,
) -> list[float]:
    """Blend selected keys toward a reference frame's value for Blend-to-Reference.

    At factor=0 keys stay unchanged; at factor=1 all keys match reference_value.
    """
    return [lerp(k.value, reference_value, factor) for k in selected_keys]


def blend_offset(
    all_keys: list[KeyData],
    selected_indices: list[int],
    factor: float,
) -> float:
    """Shift selected keys toward a neighboring unselected key's value.

    Positive factor moves toward right neighbor, negative toward left. Used by
    Blend Offset operator to slide keys toward surrounding pose keys.
    """
    if not selected_indices:
        return 0.0

    left_neighbor, right_neighbor = find_neighbors(all_keys, selected_indices)
    selected_values = [all_keys[i].value for i in selected_indices]

    if factor > 0.0 and right_neighbor is not None:
        last_val = selected_values[-1]
        max_offset = right_neighbor.value - last_val
        return max_offset * factor

    if factor < 0.0 and left_neighbor is not None:
        first_val = selected_values[0]
        max_offset = left_neighbor.value - first_val
        return max_offset * abs(factor)

    return 0.0


def ease_to_ease(
    selected_keys: list[KeyData],
    factor: float,
) -> list[float]:
    """Apply smoothstep interpolation between first and last key for smooth ease-in/ease-out.

    Animator's primary tool for adding ease to linear timing. At factor=0 keys
    unchanged; at factor=1 keys follow smooth spline from first to last keyframe.
    """
    if len(selected_keys) < 2:
        return [k.value for k in selected_keys]

    first = selected_keys[0]
    last = selected_keys[-1]
    frame_span = last.frame - first.frame

    new_values: list[float] = []
    for i, key in enumerate(selected_keys):
        if i == 0 or i == len(selected_keys) - 1:
            new_values.append(key.value)
            continue

        if abs(frame_span) < EPSILON:
            new_values.append(key.value)
            continue

        t = (key.frame - first.frame) / frame_span
        s = smoothstep(t)
        eased = lerp(first.value, last.value, s)
        new_values.append(lerp(key.value, eased, factor))

    return new_values


# ---------------------------------------------------------------------------
# Foundation supplement: Blend to Neighbor, Push/Pull, Smooth Keys
# ---------------------------------------------------------------------------


def blend_to_neighbor(
    all_keys: list[KeyData],
    selected_indices: list[int],
    factor: float,
) -> list[float]:
    """Blend each selected key toward the linear interpolation between its
    surrounding unselected neighbors.  factor 0 = original, 1 = on the line."""
    sel_set = set(selected_indices)
    results: list[float] = []

    for idx in selected_indices:
        key = all_keys[idx]

        left = None
        for i in range(idx - 1, -1, -1):
            if i not in sel_set:
                left = all_keys[i]
                break

        right = None
        for i in range(idx + 1, len(all_keys)):
            if i not in sel_set:
                right = all_keys[i]
                break

        if left is not None and right is not None:
            span = right.frame - left.frame
            if abs(span) < EPSILON:
                target = left.value
            else:
                t = (key.frame - left.frame) / span
                target = lerp(left.value, right.value, t)
        elif left is not None:
            target = left.value
        elif right is not None:
            target = right.value
        else:
            target = key.value

        results.append(lerp(key.value, target, factor))

    return results


def push_pull(
    selected_keys: list[KeyData],
    reference_value: float,
    factor: float,
) -> list[float]:
    """Scale selected keys away from (*factor* > 0) or toward (*factor* < 0)
    a reference value.  At factor 0 the keys are unchanged."""
    scale = 1.0 + factor
    return [reference_value + (k.value - reference_value) * scale for k in selected_keys]


def smooth_keys(
    all_keys: list[KeyData],
    selected_indices: list[int],
    factor: float,
) -> list[float]:
    """Blend each selected key toward the average of its immediate timeline
    neighbors (selected or not).  Endpoints use one-sided averaging."""
    results: list[float] = []

    for idx in selected_indices:
        key = all_keys[idx]

        if idx > 0 and idx < len(all_keys) - 1:
            avg = (all_keys[idx - 1].value + all_keys[idx + 1].value) / 2.0
        elif idx > 0:
            avg = all_keys[idx - 1].value
        elif idx < len(all_keys) - 1:
            avg = all_keys[idx + 1].value
        else:
            avg = key.value

        results.append(lerp(key.value, avg, factor))

    return results