"""Pair Detection Engine for opposite-side bone pairs in mirroring.

Detects and manages mirror pairs of bones using naming conventions.
All functions are pure Python and testable without bpy.

Key concepts
------------

*Side*
    A bone is classified as "L" (left), "R" (right), or "C" (center/unknown)
    based on naming patterns.

*Pair*
    Two bones on opposite sides that follow a symmetrical naming convention.
    e.g., ``Arm.L`` ↔ ``Arm.R`` or ``arm_left`` ↔ ``arm_right``.

*Pattern*
    A naming convention rule (regex-based) for matching L/R sides.
    Patterns can be built-in or custom.

*Ambiguity*
    A name that matches multiple patterns with conflicting results.
"""

from __future__ import annotations

import re
from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from typing import Callable

from .logging import get_logger

__all__ = [
    "MirrorPattern",
    "BUILTIN_PATTERNS",
    "detect_side",
    "find_opposite",
    "find_all_pairs",
    "find_unpaired",
    "find_ambiguous",
    "detect_active_side",
    "compile_custom_pattern",
]

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# MirrorPattern dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MirrorPattern:
    """A naming pattern for detecting and swapping L/R sides.

    Attributes
    ----------
    name : str
        Human-readable name (e.g., ``"dot_LR"`` for ``.L`` / ``.R``).
    left_re : re.Pattern
        Compiled regex that matches the left-side variant.
    right_re : re.Pattern
        Compiled regex that matches the right-side variant.
    swap_func : Callable[[str], str]
        Function to swap a name from one side to the other.
        If name matches left_re, should produce right version (and vice versa).
    """

    name: str
    left_re: re.Pattern
    right_re: re.Pattern
    swap_func: Callable[[str], str]


# ---------------------------------------------------------------------------
# Built-in patterns
# ---------------------------------------------------------------------------


def _make_dot_LR_swap(name: str) -> str:
    """Swap .L (with optional .NNN suffix) to .R or vice versa."""
    result = re.sub(r"\.L(\.\d+)?(\b|$)", r".R\1\2", name)
    if result != name:
        return result
    return re.sub(r"\.R(\.\d+)?(\b|$)", r".L\1\2", name)


def _make_dot_lr_swap(name: str) -> str:
    """Swap .l to .r or vice versa."""
    result = re.sub(r"\.l(\b|$)", ".r", name)
    if result != name:
        return result
    return re.sub(r"\.r(\b|$)", ".l", name)


def _make_under_LR_swap(name: str) -> str:
    """Swap _L (with optional _NNN suffix) to _R or vice versa."""
    result = re.sub(r"_L(_\d+)?(\b|$)", r"_R\1\2", name)
    if result != name:
        return result
    return re.sub(r"_R(_\d+)?(\b|$)", r"_L\1\2", name)


def _make_under_lr_swap(name: str) -> str:
    """Swap _l to _r or vice versa."""
    result = re.sub(r"_l(\b|$)", "_r", name)
    if result != name:
        return result
    return re.sub(r"_r(\b|$)", "_l", name)


def _make_word_LeftRight_swap(name: str) -> str:
    """Swap Left to Right or vice versa (case-sensitive Title Case)."""
    result = re.sub(r"Left", "Right", name)
    if result != name:
        return result
    return re.sub(r"Right", "Left", name)


def _make_word_leftright_swap(name: str) -> str:
    """Swap left to right or vice versa (lowercase)."""
    result = re.sub(r"left", "right", name)
    if result != name:
        return result
    return re.sub(r"right", "left", name)


BUILTIN_PATTERNS: tuple[MirrorPattern, ...] = (
    MirrorPattern(
        name="dot_LR",
        left_re=re.compile(r"\.L(\.\d+)?(\b|$)"),
        right_re=re.compile(r"\.R(\.\d+)?(\b|$)"),
        swap_func=_make_dot_LR_swap,
    ),
    MirrorPattern(
        name="dot_lr",
        left_re=re.compile(r"\.l(\b|$)"),
        right_re=re.compile(r"\.r(\b|$)"),
        swap_func=_make_dot_lr_swap,
    ),
    MirrorPattern(
        name="under_LR",
        left_re=re.compile(r"_L(_\d+)?(\b|$)"),
        right_re=re.compile(r"_R(_\d+)?(\b|$)"),
        swap_func=_make_under_LR_swap,
    ),
    MirrorPattern(
        name="under_lr",
        left_re=re.compile(r"_l(\b|$)"),
        right_re=re.compile(r"_r(\b|$)"),
        swap_func=_make_under_lr_swap,
    ),
    MirrorPattern(
        name="word_LeftRight",
        left_re=re.compile(r"Left"),
        right_re=re.compile(r"Right"),
        swap_func=_make_word_LeftRight_swap,
    ),
    MirrorPattern(
        name="word_leftright",
        left_re=re.compile(r"(?<![a-zA-Z])left"),
        right_re=re.compile(r"(?<![a-zA-Z])right"),
        swap_func=_make_word_leftright_swap,
    ),
)


# ---------------------------------------------------------------------------
# Side detection
# ---------------------------------------------------------------------------


def detect_side(name: str) -> str:
    """Detect the side (L, R, or C) of a bone by name.

    Parameters
    ----------
    name : str
        The bone name to check.

    Returns
    -------
    str
        ``"L"`` if the name matches a left pattern,
        ``"R"`` if the name matches a right pattern,
        ``"C"`` if no pattern matches (center/unknown).
    """
    for pattern in BUILTIN_PATTERNS:
        if pattern.left_re.search(name):
            return "L"
        if pattern.right_re.search(name):
            return "R"
    return "C"


# ---------------------------------------------------------------------------
# Pair finding
# ---------------------------------------------------------------------------


def find_opposite(
    name: str,
    *,
    overrides: dict[str, str] | None = None,
    exceptions: dict[str, str] | None = None,
    custom_patterns: tuple[MirrorPattern, ...] | None = None,
) -> str | None:
    """Find the opposite-side name for a given bone name.

    Tries in order:
      1. Manual override map
      2. Naming exceptions
      3. Built-in patterns
      4. Custom patterns

    Parameters
    ----------
    name : str
        The bone name to find a pair for.
    overrides : dict[str, str], optional
        Manual pair mapping: ``{bone_a: bone_b, ...}``.
        These take highest priority.
    exceptions : dict[str, str], optional
        Naming exceptions: ``{original_name: opposite_name}``.
        For bones that don't follow standard patterns.
    custom_patterns : tuple[MirrorPattern, ...], optional
        Additional custom patterns to try after built-in ones.

    Returns
    -------
    str | None
        The opposite-side name, or None if no pair is found.
    """
    # Check overrides first
    if overrides and name in overrides:
        return overrides[name]

    # Check exceptions
    if exceptions and name in exceptions:
        return exceptions[name]

    # Try built-in patterns
    for pattern in BUILTIN_PATTERNS:
        swapped = pattern.swap_func(name)
        if swapped != name:
            return swapped

    # Try custom patterns
    if custom_patterns:
        for pattern in custom_patterns:
            swapped = pattern.swap_func(name)
            if swapped != name:
                return swapped

    return None


def find_all_pairs(
    bone_names: IterableABC[str],
    *,
    overrides: dict[str, str] | None = None,
    exceptions: dict[str, str] | None = None,
    custom_patterns: tuple[MirrorPattern, ...] | None = None,
) -> dict[str, str]:
    """Build a complete pair map for all bone names.

    Only includes bones that have a detected pair.

    Parameters
    ----------
    bone_names : Iterable[str]
        All bone names to process.
    overrides : dict[str, str], optional
        Manual pair mapping.
    exceptions : dict[str, str], optional
        Naming exceptions.
    custom_patterns : tuple[MirrorPattern, ...], optional
        Custom patterns.

    Returns
    -------
    dict[str, str]
        ``{bone_name: opposite_name}`` for every bone with a pair.
    """
    bone_set = set(bone_names)
    pairs = {}

    for name in bone_set:
        opposite = find_opposite(
            name,
            overrides=overrides,
            exceptions=exceptions,
            custom_patterns=custom_patterns,
        )
        if opposite and opposite in bone_set:
            pairs[name] = opposite

    return pairs


def find_unpaired(bone_names: IterableABC[str], pair_map: dict[str, str]) -> list[str]:
    """Return names that are not in the pair map.

    Parameters
    ----------
    bone_names : Iterable[str]
        All bone names to check.
    pair_map : dict[str, str]
        The pair map from ``find_all_pairs()``.

    Returns
    -------
    list[str]
        Names not present in pair_map.
    """
    return [name for name in bone_names if name not in pair_map]


def find_ambiguous(
    bone_names: IterableABC[str],
    *,
    overrides: dict[str, str] | None = None,
    exceptions: dict[str, str] | None = None,
    custom_patterns: tuple[MirrorPattern, ...] | None = None,
) -> dict[str, list[str]]:
    """Find names that match multiple patterns with different results.

    A name is ambiguous if different patterns produce different opposite names.

    Parameters
    ----------
    bone_names : Iterable[str]
        All bone names to check.
    overrides : dict[str, str], optional
        Manual pair mapping.
    exceptions : dict[str, str], optional
        Naming exceptions.
    custom_patterns : tuple[MirrorPattern, ...], optional
        Custom patterns.

    Returns
    -------
    dict[str, list[str]]
        ``{ambiguous_name: [possible_opposite1, possible_opposite2, ...]}``.
        Only includes names with multiple different results.
    """
    ambiguous = {}

    for name in bone_names:
        # Skip if overridden or excepted
        if overrides and name in overrides:
            continue
        if exceptions and name in exceptions:
            continue

        results = []

        # Collect all possible results from built-in patterns
        for pattern in BUILTIN_PATTERNS:
            swapped = pattern.swap_func(name)
            if swapped != name and swapped not in results:
                results.append(swapped)

        # Collect from custom patterns
        if custom_patterns:
            for pattern in custom_patterns:
                swapped = pattern.swap_func(name)
                if swapped != name and swapped not in results:
                    results.append(swapped)

        # Record if multiple different results
        if len(results) > 1:
            ambiguous[name] = results

    return ambiguous


# ---------------------------------------------------------------------------
# Side detection across a collection
# ---------------------------------------------------------------------------


def detect_active_side(bone_names: IterableABC[str]) -> str:
    """Detect which side (L or R) is more prevalent in the bone names.

    Parameters
    ----------
    bone_names : Iterable[str]
        The bone names to analyze.

    Returns
    -------
    str
        ``"L"`` if more bones are detected as left-side,
        ``"R"`` if more bones are detected as right-side.
        If equal or no sides detected, defaults to ``"L"``.
    """
    l_count = 0
    r_count = 0

    for name in bone_names:
        side = detect_side(name)
        if side == "L":
            l_count += 1
        elif side == "R":
            r_count += 1

    if r_count > l_count:
        return "R"
    return "L"


# ---------------------------------------------------------------------------
# Custom pattern creation
# ---------------------------------------------------------------------------


def compile_custom_pattern(
    name: str,
    left_pattern: str,
    right_pattern: str,
) -> MirrorPattern:
    """Create a MirrorPattern from user-provided regex strings.

    Parameters
    ----------
    name : str
        Human-readable name for the pattern (e.g., ``"custom_wings"``).
    left_pattern : str
        Regex string that matches the left-side variant.
    right_pattern : str
        Regex string that matches the right-side variant.

    Returns
    -------
    MirrorPattern
        A compiled pattern with auto-generated swap function.

    Raises
    ------
    re.error
        If either regex string is invalid.
    """
    left_re = re.compile(left_pattern)
    right_re = re.compile(right_pattern)

    def swap_func(test_name: str) -> str:
        """Swap using the custom patterns."""
        result = left_re.sub(right_pattern, test_name)
        if result != test_name:
            return result
        return right_re.sub(left_pattern, test_name)

    return MirrorPattern(
        name=name,
        left_re=left_re,
        right_re=right_re,
        swap_func=swap_func,
    )
