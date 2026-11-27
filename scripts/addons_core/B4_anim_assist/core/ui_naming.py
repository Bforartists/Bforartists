# --- UI/UX FOUNDATION ---
"""Animator-facing label vocabulary for Anim Assist panels.

Future phases must source UI strings from this module rather than literal
strings so that:

* Terminology stays consistent across panels (e.g. always "Selected Keys",
  never "Active Keys" / "Current Keys" / "Sel Keys").
* Translations and copy editing happen in one place.
* Static analysis can grep ``LABEL_*`` references to verify coverage.

The vocabulary distinguishes between SCOPE nouns (the *what*), VERB nouns
(the *do*), AXIS nouns (time vs value), and SECTION headings (the *where*
in a panel). All strings use sentence case and are deliberately short.
"""

from __future__ import annotations

__all__ = [
    # Scope nouns
    "LABEL_SCOPE_SELECTED_KEYS",
    "LABEL_SCOPE_VISIBLE_KEYS",
    "LABEL_SCOPE_CURRENT_FRAME",
    "LABEL_SCOPE_FRAME_RANGE",
    "LABEL_SCOPE_PLAYBACK_RANGE",
    "LABEL_SCOPE_PREVIEW_RANGE",
    "LABEL_SCOPE_SELECTED_CHANNELS",
    "LABEL_SCOPE_VISIBLE_CHANNELS",
    "LABEL_SCOPE_ALL_CHANNELS",
    "LABEL_SCOPE_SELECTED_OBJECTS",
    "LABEL_SCOPE_SELECTED_BONES",
    "LABEL_SCOPE_MATCHING_TARGETS",
    # Verb nouns
    "VERB_SELECT",
    "VERB_DESELECT",
    "VERB_ISOLATE",
    "VERB_SHOW",
    "VERB_HIDE",
    "VERB_MUTE",
    "VERB_TAG",
    "VERB_NOTE",
    "VERB_PROTECT",
    "VERB_UNPROTECT",
    "VERB_COPY",
    "VERB_PASTE",
    "VERB_OFFSET",
    "VERB_SNAP",
    "VERB_MIRROR",
    "VERB_DELETE",
    "VERB_SCAN",
    "VERB_REPORT",
    "VERB_JUMP",
    "VERB_BOOKMARK",
    # Axis nouns
    "AXIS_TIME",
    "AXIS_VALUE",
    "AXIS_FRAME",
    "AXIS_HANDLE",
    "AXIS_INTERPOLATION",
    "AXIS_SLOPE",
    # Section headings
    "SECTION_PRIMARY",
    "SECTION_SCOPE",
    "SECTION_ADVANCED",
    "SECTION_ANALYSIS",
    "SECTION_DESTRUCTIVE",
    "SECTION_HELP",
    # Helpers
    "format_count",
    "format_scope_summary",
]


# ---------------------------------------------------------------------------
# Scope nouns — describe the data the operation acts on
# ---------------------------------------------------------------------------

LABEL_SCOPE_SELECTED_KEYS: str = "Selected Keys"
LABEL_SCOPE_VISIBLE_KEYS: str = "Visible Keys"
LABEL_SCOPE_CURRENT_FRAME: str = "Current Frame"
LABEL_SCOPE_FRAME_RANGE: str = "Frame Range"
LABEL_SCOPE_PLAYBACK_RANGE: str = "Playback Range"
LABEL_SCOPE_PREVIEW_RANGE: str = "Preview Range"
LABEL_SCOPE_SELECTED_CHANNELS: str = "Selected Channels"
LABEL_SCOPE_VISIBLE_CHANNELS: str = "Visible Channels"
LABEL_SCOPE_ALL_CHANNELS: str = "All Animated Channels"
LABEL_SCOPE_SELECTED_OBJECTS: str = "Selected Objects"
LABEL_SCOPE_SELECTED_BONES: str = "Selected Bones"
LABEL_SCOPE_MATCHING_TARGETS: str = "Matching Channels Across Targets"


# ---------------------------------------------------------------------------
# Verb nouns — describe the action a button performs
# ---------------------------------------------------------------------------

VERB_SELECT: str = "Select"
VERB_DESELECT: str = "Deselect"
VERB_ISOLATE: str = "Isolate"
VERB_SHOW: str = "Show"
VERB_HIDE: str = "Hide"
VERB_MUTE: str = "Mute"
VERB_TAG: str = "Tag"
VERB_NOTE: str = "Note"
VERB_PROTECT: str = "Protect"
VERB_UNPROTECT: str = "Unprotect"
VERB_COPY: str = "Copy"
VERB_PASTE: str = "Paste"
VERB_OFFSET: str = "Offset"
VERB_SNAP: str = "Snap"
VERB_MIRROR: str = "Mirror"
VERB_DELETE: str = "Delete"
VERB_SCAN: str = "Scan"
VERB_REPORT: str = "Report"
VERB_JUMP: str = "Jump To"
VERB_BOOKMARK: str = "Bookmark"


# ---------------------------------------------------------------------------
# Axis nouns — make time vs value distinctions explicit
# ---------------------------------------------------------------------------

AXIS_TIME: str = "Time"
AXIS_VALUE: str = "Value"
AXIS_FRAME: str = "Frame"
AXIS_HANDLE: str = "Handle"
AXIS_INTERPOLATION: str = "Interpolation"
AXIS_SLOPE: str = "Slope"


# ---------------------------------------------------------------------------
# Section headings — drive ``panel_anatomy.STANDARD_SECTIONS``
# ---------------------------------------------------------------------------

SECTION_PRIMARY: str = "Primary Actions"
SECTION_SCOPE: str = "Scope"
SECTION_ADVANCED: str = "Advanced"
SECTION_ANALYSIS: str = "Analysis"
SECTION_DESTRUCTIVE: str = "Destructive Actions"
SECTION_HELP: str = "Help & Notes"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def format_count(count: int, singular: str, plural: str | None = None) -> str:
    """Return a count-aware noun phrase: ``"3 keys"`` / ``"1 key"``."""
    if count == 1:
        return f"1 {singular}"
    return f"{count} {plural or singular + 's'}"


def format_scope_summary(scope_label: str, count: int | None = None) -> str:
    """Return a one-line scope summary, e.g. ``"Selected Keys (12)"``."""
    if count is None:
        return scope_label
    return f"{scope_label} ({count})"
