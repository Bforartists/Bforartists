# --- SPACE-SWITCH HISTORY ---
"""In-memory switch-event history stack.

Tracks every space-switch operation performed during the session so the
user can navigate between switch frames and undo/restore.  Lost on
Blender shutdown (intentional — switch history is ephemeral working
state, not project data).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .logging import get_logger

_log = get_logger(__name__)

__all__ = [
    "SwitchEvent",
    "push_event",
    "get_last_event",
    "get_history",
    "clear_history",
    "find_next_event",
    "find_prev_event",
    "events_at_frame",
    "get_unique_frames",
    "MAX_HISTORY",
]

# Maximum events kept before oldest are pruned.
MAX_HISTORY = 200


# ---------------------------------------------------------------------------
# Event record
# ---------------------------------------------------------------------------

@dataclass
class SwitchEvent:
    """A single recorded switch operation."""

    frame: int
    obj_name: str
    bone_name: str  # Empty for object-level switches.
    prop_path: str
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=time.time)

    def display_label(self) -> str:
        """Format the switch event for display in the history UI panel.

        Returns a human-readable string like "F45: Hand.L IK_FK 0→1"
        showing the frame, target bone/object, property, and value change.
        """
        target = self.bone_name or self.obj_name
        return f"F{self.frame}: {target} {self.prop_path} {self.old_value}→{self.new_value}"


# ---------------------------------------------------------------------------
# Module-level history stack
# ---------------------------------------------------------------------------

_history: list[SwitchEvent] = []
_last_event: SwitchEvent | None = None


def push_event(event: SwitchEvent) -> None:
    """Record a switch event.  Prunes oldest when over MAX_HISTORY."""
    global _last_event
    _history.append(event)
    _last_event = event
    if len(_history) > MAX_HISTORY:
        _history[:] = _history[-MAX_HISTORY:]
    _log.debug("Switch history: pushed %s (total=%d)", event.display_label(), len(_history))


def get_last_event() -> SwitchEvent | None:
    """Return the most recent switch event, or None."""
    return _last_event


def get_history() -> list[SwitchEvent]:
    """Return a copy of the full history list (oldest first)."""
    return list(_history)


def clear_history() -> None:
    """Drop all switch history."""
    global _last_event
    _history.clear()
    _last_event = None
    _log.debug("Switch history cleared")


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

def find_next_event(current_frame: int) -> SwitchEvent | None:
    """Return the first event after *current_frame*, or None."""
    future = [e for e in _history if e.frame > current_frame]
    if not future:
        return None
    return min(future, key=lambda e: e.frame)


def find_prev_event(current_frame: int) -> SwitchEvent | None:
    """Return the last event before *current_frame*, or None."""
    past = [e for e in _history if e.frame < current_frame]
    if not past:
        return None
    return max(past, key=lambda e: e.frame)


def events_at_frame(frame: int) -> list[SwitchEvent]:
    """Return all events that occurred at *frame*."""
    return [e for e in _history if e.frame == frame]


def get_unique_frames() -> list[int]:
    """Return sorted list of unique frames that have switch events."""
    return sorted(set(e.frame for e in _history))
