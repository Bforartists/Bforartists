# --- TRANSFORM OFFSET CONTROLS ---
"""Pure-math offset delta construction and last-operation memory.

Defines :class:`OffsetDelta`, a plain dataclass holding the T/R/S
components of a single offset request, plus helpers to build it from
user-entered amounts, scale it by a frame weight, negate it, and
remember the most recent delta for "reapply last" / "invert last"
operators.

The only Blender-specific import is ``mathutils`` — this module stays
free of ``bpy`` so the math can be tested in a headless Python
interpreter using the ``mathutils`` companion package, or mocked out
entirely.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

try:
    from mathutils import Vector
except Exception:  # pragma: no cover - mathutils is always present in Blender
    Vector = None  # type: ignore[assignment]

__all__ = [
    "OffsetDelta",
    "LastOffsetRecord",
    "build_delta",
    "push_pull_delta",
    "remember_last",
    "get_last",
    "clear_last",
]


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class OffsetDelta:
    """A single offset request.

    ``translation``, ``rotation_euler`` (radians), and ``scale`` are all
    three-tuples so this class is safe to copy and compare without
    mathutils. Callers that need mathutils types convert at the edges.

    ``channel_mask`` is a string from ``{"T", "R", "S", "TRS"}`` and
    constrains which components are written even when non-zero values
    appear in unused fields.
    """

    translation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_euler: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: tuple[float, float, float] = (0.0, 0.0, 0.0)
    channel_mask: str = "TRS"

    def is_zero(self, eps: float = 1e-9) -> bool:
        """Return True when every masked component is below ``eps``."""
        if "T" in self.channel_mask:
            if any(abs(v) > eps for v in self.translation):
                return False
        if "R" in self.channel_mask:
            if any(abs(v) > eps for v in self.rotation_euler):
                return False
        if "S" in self.channel_mask:
            if any(abs(v) > eps for v in self.scale):
                return False
        return True

    def scaled(self, weight: float) -> "OffsetDelta":
        """Return a copy with every component multiplied by ``weight``.

        Scale uses an "add delta around 1.0" convention: the entered
        amounts are the *delta from 1.0*, so scaling the weight still
        makes sense as a linear interpolation toward 0 = no effect.
        """
        w = float(weight)
        return OffsetDelta(
            translation=tuple(v * w for v in self.translation),  # type: ignore[arg-type]
            rotation_euler=tuple(v * w for v in self.rotation_euler),  # type: ignore[arg-type]
            scale=tuple(v * w for v in self.scale),  # type: ignore[arg-type]
            channel_mask=self.channel_mask,
        )

    def negated(self) -> "OffsetDelta":
        """Return a copy with every component negated. Used by Invert Last."""
        return OffsetDelta(
            translation=tuple(-v for v in self.translation),  # type: ignore[arg-type]
            rotation_euler=tuple(-v for v in self.rotation_euler),  # type: ignore[arg-type]
            scale=tuple(-v for v in self.scale),  # type: ignore[arg-type]
            channel_mask=self.channel_mask,
        )

    def masked_for_axis(self, preserve_axis: str) -> "OffsetDelta":
        """Return a copy with the preserve-contact axis zeroed.

        ``preserve_axis`` is one of ``{"NONE", "X", "Y", "Z"}``. When
        non-NONE the translation component on that axis is forced to
        zero before the delta enters the basis-conversion pipeline, so
        foot contacts stay glued to their current position even if the
        user dragged a 3D offset.
        """
        if preserve_axis == "NONE" or preserve_axis not in ("X", "Y", "Z"):
            return self
        idx = {"X": 0, "Y": 1, "Z": 2}[preserve_axis]
        t = list(self.translation)
        t[idx] = 0.0
        return replace(self, translation=(t[0], t[1], t[2]))


# ---------------------------------------------------------------------------
# Construction helpers
# ---------------------------------------------------------------------------

def build_delta(
    *,
    translation: tuple[float, float, float],
    rotation_euler: tuple[float, float, float],
    scale: tuple[float, float, float],
    channel_mask: str,
    fine_step: bool,
    multiplier: float,
) -> OffsetDelta:
    """Combine the user-entered amounts into an ``OffsetDelta``.

    ``fine_step`` halves the entered values (finer nudges) before the
    preset multiplier applies. The preset multiplier is the scalar from
    :mod:`p4_presets` and defaults to ``1.0``.
    """
    step = 0.1 if fine_step else 1.0
    k = step * float(multiplier)
    return OffsetDelta(
        translation=tuple(v * k for v in translation),  # type: ignore[arg-type]
        rotation_euler=tuple(v * k for v in rotation_euler),  # type: ignore[arg-type]
        scale=tuple(v * k for v in scale),  # type: ignore[arg-type]
        channel_mask=channel_mask,
    )


def push_pull_delta(
    axis: str,
    amount: float,
    sign: float,
    *,
    channel_mask: str = "T",
    fine_step: bool = False,
    multiplier: float = 1.0,
) -> OffsetDelta:
    """Return a single-axis translation delta for push/pull operators.

    ``axis`` is one of ``{"X", "Y", "Z"}``. ``sign`` is ``+1`` for push
    and ``-1`` for pull. ``amount`` is always a positive magnitude.
    """
    mag = abs(float(amount)) * float(sign)
    if fine_step:
        mag *= 0.1
    mag *= float(multiplier)
    tx = mag if axis == "X" else 0.0
    ty = mag if axis == "Y" else 0.0
    tz = mag if axis == "Z" else 0.0
    return OffsetDelta(
        translation=(tx, ty, tz),
        rotation_euler=(0.0, 0.0, 0.0),
        scale=(0.0, 0.0, 0.0),
        channel_mask=channel_mask,
    )


# ---------------------------------------------------------------------------
# Last-operation memory
# ---------------------------------------------------------------------------

@dataclass
class LastOffsetRecord:
    """Snapshot of the most recent offset request for Reapply / Invert."""

    delta: OffsetDelta
    space: str
    pivot_mode: str
    scope: str
    falloff_shape: str

    def as_inverted(self) -> "LastOffsetRecord":
        """Return a new record with the delta negated so the same apply logic can undo the offset.

        Used by the Invert Last offset operator: instead of a separate undo code path,
        we negate the delta and reapply it.
        """
        return LastOffsetRecord(
            delta=self.delta.negated(),
            space=self.space,
            pivot_mode=self.pivot_mode,
            scope=self.scope,
            falloff_shape=self.falloff_shape,
        )


_LAST_OFFSET: LastOffsetRecord | None = None


def remember_last(record: LastOffsetRecord) -> None:
    """Store ``record`` as the most recent offset request."""
    global _LAST_OFFSET
    _LAST_OFFSET = record


def get_last() -> LastOffsetRecord | None:
    """Return the most recent offset record, or *None* if none has run."""
    return _LAST_OFFSET


def clear_last() -> None:
    """Wipe the last-offset memory. Called on addon unregister."""
    global _LAST_OFFSET
    _LAST_OFFSET = None
