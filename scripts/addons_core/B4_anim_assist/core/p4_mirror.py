# --- TRANSFORM OFFSET CONTROLS ---
"""Mirror-sign helpers for offset.

Given a target name (object or pose bone), detect which side of the rig
it lives on using common Blender naming conventions, and return a
``+1`` / ``-1`` sign that can be used to flip an offset on the configured
axis for the mirrored side.

Supported side tokens (case-insensitive):

* ``.L`` / ``.R``
* ``_L`` / ``_R``
* ``-L`` / ``-R``
* ``Left`` / ``Right`` (prefix or suffix, whole-word match)

Left-side names return ``+1``; right-side names return ``-1``. Names
with no recognised token return ``+1``.

Pure Python. No ``bpy`` imports.
"""

from __future__ import annotations

import re
from typing import Literal

Side = Literal["LEFT", "RIGHT", "NONE"]

__all__ = [
    "Side",
    "detect_side",
    "mirror_sign",
]

# Ordered so earlier patterns win.
_SIDE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?:^|[._\-])([lL])(?:$|[._\-\d])"), "L"),
    (re.compile(r"(?:^|[._\-])([rR])(?:$|[._\-\d])"), "R"),
    (re.compile(r"(?:^|[._\-])left(?:$|[._\-\d])", re.IGNORECASE), "LEFT"),
    (re.compile(r"(?:^|[._\-])right(?:$|[._\-\d])", re.IGNORECASE), "RIGHT"),
)


def detect_side(name: str) -> Side:
    """Return ``"LEFT"``, ``"RIGHT"``, or ``"NONE"`` for the given name."""
    if not name:
        return "NONE"
    # Whole-word Left / Right is highest priority because "Left" happens
    # to contain a trailing "t" that the .L short form cannot match.
    if _SIDE_PATTERNS[2][0].search(name):
        return "LEFT"
    if _SIDE_PATTERNS[3][0].search(name):
        return "RIGHT"
    if _SIDE_PATTERNS[0][0].search(name):
        return "LEFT"
    if _SIDE_PATTERNS[1][0].search(name):
        return "RIGHT"
    return "NONE"


def mirror_sign(
    name: str,
    *,
    mirror_side: Side = "RIGHT",
) -> int:
    """Return ``-1`` if the given name lives on ``mirror_side``, else ``+1``.

    ``mirror_side`` controls which side receives the negated delta. The
    default ``"RIGHT"`` means right-side targets have their delta flipped,
    matching Blender's X-Axis Mirror convention.
    """
    side = detect_side(name)
    if side == "NONE":
        return 1
    if side == mirror_side:
        return -1
    return 1


__all__ = [
    "Side",
    "detect_side",
    "mirror_sign",
]
