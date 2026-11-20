# --- ANIMATION LAYER BLEND MATH ---
"""Layer blending mathematics for animation layer stack evaluation.

Provides pure-Python blend mode implementations that combine two sets of
transform values (location, rotation, scale) according to a blend mode
and a weight factor.  Inspired by:

    Maya Animation Layers  -- Override and Additive blending
    Blender NLA            -- Combine mode (loc add, rot concat, scale mul)
    After Effects          -- Layer compositing with opacity/weight

Key concepts
------------

*Base values*
    The accumulated result from all layers below the current one.

*Layer values*
    The transform values stored in the current layer's Action.

*Weight*
    A 0..1 factor that scales the current layer's contribution.
    At weight=0 the layer has no effect; at weight=1 it has full effect.

*Blend mode*
    Determines HOW the layer values combine with the base:
    - OVERRIDE  : lerp(base, layer, weight)
    - ADDITIVE  : base + (layer - rest_pose) * weight
    - MULTIPLY  : base * lerp(1.0, layer/base, weight)
    - COMBINE   : loc adds, rot concatenates, scale multiplies

*Rest pose*
    For Additive mode the layer stores deltas from the bone's rest pose.
    The rest pose is identity for location (0,0,0), identity rotation,
    and (1,1,1) for scale.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .logging import get_logger

if TYPE_CHECKING:
    pass

__all__ = [
    "REST_LOCATION",
    "REST_ROTATION",
    "REST_SCALE",
    "REST_QUATERNION",
    "BlendResult",
    "BLEND_FUNCTIONS",
    "blend_override",
    "blend_additive",
    "blend_multiply",
    "blend_combine",
    "blend_transforms",
    "interpolate_layers",
]

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Rest pose defaults (identity transforms).
REST_LOCATION: tuple[float, float, float] = (0.0, 0.0, 0.0)
REST_ROTATION: tuple[float, float, float] = (0.0, 0.0, 0.0)
REST_SCALE: tuple[float, float, float] = (1.0, 1.0, 1.0)
REST_QUATERNION: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# Scalar helpers
# ---------------------------------------------------------------------------

def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between *a* and *b* at factor *t*."""
    return a + (b - a) * t


def _clamp01(v: float) -> float:
    """Clamp *v* to the 0.0–1.0 range (used for weights and factors)."""
    return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# Tuple helpers
# ---------------------------------------------------------------------------

def _lerp3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    """Component-wise lerp for 3-tuples."""
    return (
        _lerp(a[0], b[0], t),
        _lerp(a[1], b[1], t),
        _lerp(a[2], b[2], t),
    )


def _add3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Component-wise addition of two 3-tuples."""
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Component-wise subtraction of two 3-tuples."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Component-wise multiplication of two 3-tuples."""
    return (a[0] * b[0], a[1] * b[1], a[2] * b[2])


def _scale3(
    v: tuple[float, float, float],
    s: float,
) -> tuple[float, float, float]:
    """Multiply every component of *v* by scalar *s*."""
    return (v[0] * s, v[1] * s, v[2] * s)


def _safe_div3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    fallback: float = 1.0,
) -> tuple[float, float, float]:
    """Component-wise division with zero-safe fallback."""
    return (
        a[0] / b[0] if abs(b[0]) > 1e-9 else fallback,
        a[1] / b[1] if abs(b[1]) > 1e-9 else fallback,
        a[2] / b[2] if abs(b[2]) > 1e-9 else fallback,
    )


# ---------------------------------------------------------------------------
# Quaternion helpers (for rotation blending)
# ---------------------------------------------------------------------------

def _quat_normalize(
    q: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Normalize a quaternion (w, x, y, z)."""
    mag = math.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2 + q[3] ** 2)
    if mag < 1e-12:
        return REST_QUATERNION
    return (q[0] / mag, q[1] / mag, q[2] / mag, q[3] / mag)


def _quat_slerp(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    """Spherical linear interpolation between quaternions *a* and *b*.

    Handles antipodal quaternions by flipping if the dot product is negative.
    """
    # Compute the dot product to determine angular distance.
    dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]

    # Ensure shortest path by flipping b if dot product is negative
    # (quaternions q and -q represent the same rotation).
    if dot < 0.0:
        b = (-b[0], -b[1], -b[2], -b[3])
        dot = -dot

    # Clamp for numerical stability (floating-point rounding).
    dot = min(dot, 1.0)

    if dot > 0.9995:
        # Quaternions are nearly aligned; use linear interpolation and renormalize.
        result = (
            _lerp(a[0], b[0], t),
            _lerp(a[1], b[1], t),
            _lerp(a[2], b[2], t),
            _lerp(a[3], b[3], t),
        )
        return _quat_normalize(result)

    # Compute the angle between the quaternions.
    theta = math.acos(dot)
    sin_theta = math.sin(theta)
    # Compute blend weights using sine weights (constant angular velocity).
    wa = math.sin((1.0 - t) * theta) / sin_theta
    wb = math.sin(t * theta) / sin_theta
    return _quat_normalize((
        wa * a[0] + wb * b[0],
        wa * a[1] + wb * b[1],
        wa * a[2] + wb * b[2],
        wa * a[3] + wb * b[3],
    ))


def _quat_multiply(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Hamilton product of two quaternions (w, x, y, z)."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _euler_to_quat(
    euler: tuple[float, float, float],
) -> tuple[float, float, float, float]:
    """Convert XYZ Euler angles (radians) to quaternion (w, x, y, z).

    Uses XYZ rotation order: apply X (roll) first, then Y (pitch), then Z (yaw).
    """
    cx = math.cos(euler[0] * 0.5)
    sx = math.sin(euler[0] * 0.5)
    cy = math.cos(euler[1] * 0.5)
    sy = math.sin(euler[1] * 0.5)
    cz = math.cos(euler[2] * 0.5)
    sz = math.sin(euler[2] * 0.5)

    w = cx * cy * cz + sx * sy * sz
    x = sx * cy * cz - cx * sy * sz
    y = cx * sy * cz + sx * cy * sz
    z = cx * cy * sz - sx * sy * cz
    return (w, x, y, z)


def _quat_to_euler(
    q: tuple[float, float, float, float],
) -> tuple[float, float, float]:
    """Convert quaternion (w, x, y, z) to XYZ Euler angles (radians)."""
    w, x, y, z = q
    # Roll (X).
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    # Pitch (Y).
    sinp = 2.0 * (w * y - z * x)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.asin(sinp)
    # Yaw (Z).
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return (roll, pitch, yaw)


# ---------------------------------------------------------------------------
# Blend result container
# ---------------------------------------------------------------------------

@dataclass
class BlendResult:
    """Output of a single-bone layer blend evaluation."""
    location: tuple[float, float, float] = REST_LOCATION
    rotation: tuple[float, float, float] = REST_ROTATION
    scale: tuple[float, float, float] = REST_SCALE
    channels_blended: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Blend mode implementations
# ---------------------------------------------------------------------------

def blend_override(
    base_loc: tuple[float, float, float],
    base_rot: tuple[float, float, float],
    base_sca: tuple[float, float, float],
    layer_loc: tuple[float, float, float],
    layer_rot: tuple[float, float, float],
    layer_sca: tuple[float, float, float],
    weight: float,
    loc_weight: float = 1.0,
    rot_weight: float = 1.0,
    sca_weight: float = 1.0,
) -> BlendResult:
    """Override blend: lerp between base and layer at *weight*.

    This is the standard Maya Override mode.  At weight=1 the layer
    completely replaces the base.  Per-channel weight overrides allow
    different blend ratios for location, rotation, and scale.
    """
    # w = master weight, lw/rw/sw = per-channel effective weights.
    w = _clamp01(weight)
    lw = _clamp01(loc_weight) * w
    rw = _clamp01(rot_weight) * w
    sw = _clamp01(sca_weight) * w

    channels = []

    out_loc = _lerp3(base_loc, layer_loc, lw)
    if lw > 0.0:
        channels.append("location")

    # Use quaternion slerp for smooth rotation blending.
    base_q = _euler_to_quat(base_rot)
    layer_q = _euler_to_quat(layer_rot)
    out_q = _quat_slerp(base_q, layer_q, rw)
    out_rot = _quat_to_euler(out_q)
    if rw > 0.0:
        channels.append("rotation")

    out_sca = _lerp3(base_sca, layer_sca, sw)
    if sw > 0.0:
        channels.append("scale")

    return BlendResult(
        location=out_loc,
        rotation=out_rot,
        scale=out_sca,
        channels_blended=channels,
    )


def blend_additive(
    base_loc: tuple[float, float, float],
    base_rot: tuple[float, float, float],
    base_sca: tuple[float, float, float],
    layer_loc: tuple[float, float, float],
    layer_rot: tuple[float, float, float],
    layer_sca: tuple[float, float, float],
    weight: float,
    loc_weight: float = 1.0,
    rot_weight: float = 1.0,
    sca_weight: float = 1.0,
) -> BlendResult:
    """Additive blend: add layer delta (from rest) onto base.

    This is the standard Maya Additive mode.  The layer stores deltas
    relative to the rest pose.  Those deltas are scaled by *weight* and
    added on top of the base.

    Ideal for breathing, secondary motion, overlap, and additive tweaks
    that should combine regardless of what the base animation is doing.
    """
    # w = master weight, lw/rw/sw = per-channel effective weights.
    w = _clamp01(weight)
    lw = _clamp01(loc_weight) * w
    rw = _clamp01(rot_weight) * w
    sw = _clamp01(sca_weight) * w

    channels = []

    # Location: base + (layer - rest) * weight.
    loc_delta = _sub3(layer_loc, REST_LOCATION)
    out_loc = _add3(base_loc, _scale3(loc_delta, lw))
    if lw > 0.0:
        channels.append("location")

    # Rotation: concatenate quaternions (additive rotation).
    layer_q = _euler_to_quat(layer_rot)
    rest_q = REST_QUATERNION
    # Slerp from identity to the layer rotation by weight.
    delta_q = _quat_slerp(rest_q, layer_q, rw)
    base_q = _euler_to_quat(base_rot)
    out_q = _quat_multiply(delta_q, base_q)
    out_rot = _quat_to_euler(out_q)
    if rw > 0.0:
        channels.append("rotation")

    # Scale: base * lerp(1.0, layer, weight) — multiplicative additive.
    sca_factor = _lerp3(REST_SCALE, layer_sca, sw)
    out_sca = _mul3(base_sca, sca_factor)
    if sw > 0.0:
        channels.append("scale")

    return BlendResult(
        location=out_loc,
        rotation=out_rot,
        scale=out_sca,
        channels_blended=channels,
    )


def blend_multiply(
    base_loc: tuple[float, float, float],
    base_rot: tuple[float, float, float],
    base_sca: tuple[float, float, float],
    layer_loc: tuple[float, float, float],
    layer_rot: tuple[float, float, float],
    layer_sca: tuple[float, float, float],
    weight: float,
    loc_weight: float = 1.0,
    rot_weight: float = 1.0,
    sca_weight: float = 1.0,
) -> BlendResult:
    """Multiply blend: scale base values by the layer.

    Useful for scaling existing animation intensities — e.g. dampen
    arm swing by putting a 0.5 multiplier on the arm layer.

    Location is multiplied component-wise.  Rotation is slerped toward
    the layer rotation proportionally.  Scale is multiplied.
    """
    # w = master weight, lw/rw/sw = per-channel effective weights.
    w = _clamp01(weight)
    lw = _clamp01(loc_weight) * w
    rw = _clamp01(rot_weight) * w
    sw = _clamp01(sca_weight) * w

    channels = []

    # Location: base * lerp(1, layer_ratio, weight).
    # Using layer values directly as multipliers is unusual; treat
    # layer location as a factor offset from (0,0,0).
    # base + base * (layer - rest) * weight
    loc_delta = _sub3(layer_loc, REST_LOCATION)
    multiplied_delta = _mul3(base_loc, _scale3(loc_delta, lw))
    out_loc = _add3(base_loc, multiplied_delta)
    if lw > 0.0:
        channels.append("location")

    # Rotation: slerp base toward (base * layer) at weight.
    base_q = _euler_to_quat(base_rot)
    layer_q = _euler_to_quat(layer_rot)
    target_q = _quat_multiply(base_q, layer_q)
    out_q = _quat_slerp(base_q, target_q, rw)
    out_rot = _quat_to_euler(out_q)
    if rw > 0.0:
        channels.append("rotation")

    # Scale: base * lerp(1, layer, weight).
    sca_factor = _lerp3(REST_SCALE, layer_sca, sw)
    out_sca = _mul3(base_sca, sca_factor)
    if sw > 0.0:
        channels.append("scale")

    return BlendResult(
        location=out_loc,
        rotation=out_rot,
        scale=out_sca,
        channels_blended=channels,
    )


def blend_combine(
    base_loc: tuple[float, float, float],
    base_rot: tuple[float, float, float],
    base_sca: tuple[float, float, float],
    layer_loc: tuple[float, float, float],
    layer_rot: tuple[float, float, float],
    layer_sca: tuple[float, float, float],
    weight: float,
    loc_weight: float = 1.0,
    rot_weight: float = 1.0,
    sca_weight: float = 1.0,
) -> BlendResult:
    """Combine blend: NLA-style mixing.

    Location: additive (base + layer * weight).
    Rotation: quaternion concatenation (layer * weight applied to base).
    Scale: multiplicative (base * layer^weight).

    This mirrors Blender's NLA Combine strip blend type.
    """
    # w = master weight, lw/rw/sw = per-channel effective weights.
    w = _clamp01(weight)
    lw = _clamp01(loc_weight) * w
    rw = _clamp01(rot_weight) * w
    sw = _clamp01(sca_weight) * w

    channels = []

    # Location: additive.
    out_loc = _add3(base_loc, _scale3(layer_loc, lw))
    if lw > 0.0:
        channels.append("location")

    # Rotation: concatenation at weight.
    rest_q = REST_QUATERNION
    layer_q = _euler_to_quat(layer_rot)
    delta_q = _quat_slerp(rest_q, layer_q, rw)
    base_q = _euler_to_quat(base_rot)
    out_q = _quat_multiply(delta_q, base_q)
    out_rot = _quat_to_euler(out_q)
    if rw > 0.0:
        channels.append("rotation")

    # Scale: multiplicative.
    sca_factor = _lerp3(REST_SCALE, layer_sca, sw)
    out_sca = _mul3(base_sca, sca_factor)
    if sw > 0.0:
        channels.append("scale")

    return BlendResult(
        location=out_loc,
        rotation=out_rot,
        scale=out_sca,
        channels_blended=channels,
    )


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

BLEND_FUNCTIONS = {
    "OVERRIDE": blend_override,
    "ADDITIVE": blend_additive,
    "MULTIPLY": blend_multiply,
    "COMBINE": blend_combine,
}


def blend_transforms(
    blend_mode: str,
    base_loc: tuple[float, float, float],
    base_rot: tuple[float, float, float],
    base_sca: tuple[float, float, float],
    layer_loc: tuple[float, float, float],
    layer_rot: tuple[float, float, float],
    layer_sca: tuple[float, float, float],
    weight: float,
    loc_weight: float = 1.0,
    rot_weight: float = 1.0,
    sca_weight: float = 1.0,
) -> BlendResult:
    """Dispatch to the appropriate blend function by *blend_mode*.

    Parameters
    ----------
    blend_mode : str
        One of "OVERRIDE", "ADDITIVE", "MULTIPLY", "COMBINE".
    base_loc, base_rot, base_sca : 3-tuples
        Accumulated transforms from layers below.
    layer_loc, layer_rot, layer_sca : 3-tuples
        This layer's transform values.
    weight : float
        Layer weight (0..1).
    loc_weight, rot_weight, sca_weight : float
        Per-channel weight overrides (default 1.0).

    Returns
    -------
    BlendResult
        The blended transforms.
    """
    blend_func = BLEND_FUNCTIONS.get(blend_mode)
    if blend_func is None:
        logger.warning(
            "Unknown blend mode '%s', falling back to OVERRIDE", blend_mode
        )
        blend_func = blend_override

    return blend_func(
        base_loc, base_rot, base_sca,
        layer_loc, layer_rot, layer_sca,
        weight,
        loc_weight, rot_weight, sca_weight,
    )


# ---------------------------------------------------------------------------
# Two-layer interactive blend
# ---------------------------------------------------------------------------

def interpolate_layers(
    source_loc: tuple[float, float, float],
    source_rot: tuple[float, float, float],
    source_sca: tuple[float, float, float],
    target_loc: tuple[float, float, float],
    target_rot: tuple[float, float, float],
    target_sca: tuple[float, float, float],
    factor: float,
) -> BlendResult:
    """Interpolate between two layer snapshots at *factor*.

    Used by the interactive Blend Between Layers slider.
    factor=0 yields full source, factor=1 yields full target.
    Rotation uses quaternion slerp for smooth interpolation.
    """
    t = _clamp01(factor)

    out_loc = _lerp3(source_loc, target_loc, t)

    src_q = _euler_to_quat(source_rot)
    tgt_q = _euler_to_quat(target_rot)
    out_q = _quat_slerp(src_q, tgt_q, t)
    out_rot = _quat_to_euler(out_q)

    out_sca = _lerp3(source_sca, target_sca, t)

    return BlendResult(
        location=out_loc,
        rotation=out_rot,
        scale=out_sca,
        channels_blended=["location", "rotation", "scale"],
    )
