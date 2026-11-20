# --- TRANSFORM OFFSET CONTROLS ---
"""Space conversion for offset offset deltas.

Converts a user-facing :class:`OffsetDelta` (expressed in the chosen
space: local, parent, world, visual, gimbal) into a per-component delta
that can be composed with the target's basis transform at a specific
frame.

Translation conversion uses the parent-to-world rotation only (scale is
never folded into the translation conversion because it would distort
uniform offsets). Rotation conversion composes on the left for world /
parent spaces and on the right for local space, matching Blender's
built-in transform operators.

Scale is always applied in the target's own basis because scale has no
well-defined world-space equivalent for a bone that lives inside an
armature's local hierarchy.

``p4_space`` is the only offset module that imports ``bpy`` for
mathutils — everything else is pure data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

try:
    import bpy  # noqa: F401
    from mathutils import Matrix, Vector, Quaternion, Euler
except Exception:  # pragma: no cover - mathutils always available in Blender
    Matrix = Vector = Quaternion = Euler = None  # type: ignore[assignment]

from .p4_offset_math import OffsetDelta

if TYPE_CHECKING:
    from .p4_targets import OffsetTarget

__all__ = [
    "SPACE_ITEMS",
    "space_enum_items",
    "ResolvedDelta",
    "delta_to_basis",
]


# ---------------------------------------------------------------------------
# Basis resolution
# ---------------------------------------------------------------------------

SPACE_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("LOCAL", "Local",
     "Interpret the offset amounts directly in the target's own basis."),
    ("PARENT", "Parent",
     "Interpret the offset amounts in the target's parent space."),
    ("WORLD", "World",
     "Interpret the offset amounts in world coordinates."),
    ("VISUAL", "Visual",
     (
        "Interpret the offset amounts in world coordinates using the "
        "depsgraph-evaluated pose, respecting constraints."
     )),
    ("GIMBAL", "Gimbal",
     (
        "Rotation-only mode that applies axis-aligned rotation in the "
        "target's current rotation order."
     )),
)


def space_enum_items(self, context) -> tuple[tuple[str, str, str], ...]:  # noqa: ARG001
    """Return space enum items for EnumProperty."""
    return SPACE_ITEMS


# ---------------------------------------------------------------------------
# Conversion core
# ---------------------------------------------------------------------------

@dataclass
class ResolvedDelta:
    """A delta already expressed in the target's basis space.

    ``translation`` and ``scale`` are plain 3-tuples. ``rotation`` is a
    ``Quaternion`` so the caller can compose it with the current basis
    rotation regardless of the target's rotation mode.
    """

    translation: tuple[float, float, float]
    rotation: object  # mathutils.Quaternion in practice
    scale: tuple[float, float, float]
    channel_mask: str


def _euler_to_quat(rx: float, ry: float, rz: float, order: str = "XYZ"):
    if Euler is None or Quaternion is None:  # pragma: no cover
        return None
    return Euler((rx, ry, rz), order).to_quaternion()


def _identity_quat():
    if Quaternion is None:  # pragma: no cover
        return None
    return Quaternion((1.0, 0.0, 0.0, 0.0))


def delta_to_basis(
    target: "OffsetTarget",
    delta: OffsetDelta,
    space: str,
) -> ResolvedDelta:
    """Convert ``delta`` from ``space`` into the target's basis space.

    The returned ``ResolvedDelta`` can be added to / composed with the
    target's current T/R/S at a specific frame in a single pass.
    """
    # Fast path: local space needs no conversion.
    if space == "LOCAL":
        return ResolvedDelta(
            translation=delta.translation,
            rotation=_euler_to_quat(*delta.rotation_euler, order=target.rotation_order),
            scale=delta.scale,
            channel_mask=delta.channel_mask,
        )

    if Matrix is None or Vector is None or Quaternion is None:  # pragma: no cover
        return ResolvedDelta(
            translation=delta.translation,
            rotation=None,
            scale=delta.scale,
            channel_mask=delta.channel_mask,
        )

    # Gimbal mode: rotate axis-aligned inside the current rotation order.
    # For quaternion-mode targets, the caller is expected to fall back
    # to LOCAL via the pipeline before reaching here; we still handle it
    # defensively.
    if space == "GIMBAL":
        rx, ry, rz = delta.rotation_euler
        q = _euler_to_quat(rx, ry, rz, order=target.rotation_order or "XYZ")
        return ResolvedDelta(
            translation=delta.translation,
            rotation=q,
            scale=delta.scale,
            channel_mask=delta.channel_mask,
        )

    # For WORLD / VISUAL / PARENT we need a matrix that transforms a
    # world-space (or parent-space) vector into the target's local basis
    # space. The *rotation component* of that matrix is what we use to
    # rotate the translation delta; the pure rotation is also what we
    # compose with the current basis rotation.
    if space == "WORLD" or space == "VISUAL":
        # World → basis: invert the parent-world × rest matrix. For
        # VISUAL we use the depsgraph-evaluated world matrix so
        # constraints contribute.
        world_to_basis = target.world_to_basis_matrix(visual=(space == "VISUAL"))
    else:  # PARENT
        world_to_basis = target.parent_to_basis_matrix()

    if world_to_basis is None:
        # Degenerate: fall back to local interpretation.
        return ResolvedDelta(
            translation=delta.translation,
            rotation=_euler_to_quat(*delta.rotation_euler, order=target.rotation_order),
            scale=delta.scale,
            channel_mask=delta.channel_mask,
        )

    rot_only = world_to_basis.to_3x3()

    # Translation: rotate the vector by the rotation part of the
    # conversion matrix. We intentionally drop any scale from the matrix
    # so uniform translations don't warp.
    t_vec = rot_only @ Vector(delta.translation)
    t_out = (t_vec.x, t_vec.y, t_vec.z)

    # Rotation: convert the delta euler to a quaternion expressed in the
    # source space, then rebase it into the target's basis space via
    # ``q_basis = R * q_src * R^-1`` where R is the rotation component
    # of the conversion matrix.
    q_src = _euler_to_quat(*delta.rotation_euler, order="XYZ")
    if q_src is None:
        q_basis = _identity_quat()
    else:
        r = rot_only.to_quaternion()
        q_basis = r @ q_src @ r.inverted()

    # Scale: scale has no meaningful rotation, so the components stay
    # as-entered. The target's basis applies them directly.
    return ResolvedDelta(
        translation=t_out,
        rotation=q_basis,
        scale=delta.scale,
        channel_mask=delta.channel_mask,
    )


__all__ = [
    "SPACE_ITEMS",
    "space_enum_items",
    "ResolvedDelta",
    "delta_to_basis",
]
