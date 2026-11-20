"""Non-persistent transient runtime state (pure Python, no RNA)."""

from __future__ import annotations

from typing import Any

from .logging import get_logger

__all__ = ["RuntimeState", "init", "get_state", "shutdown"]

_log = get_logger(__name__)


class RuntimeState:
    """Addon-wide transient state that does **not** survive file load."""

    def __init__(self) -> None:
        self.is_batch_processing: bool = False
        self.active_tool_id: str = ""
        self.suppress_updates: bool = False
        self._custom: dict[str, Any] = {}
        # --- TRAJECTORY VISUALIZATION PREP ---
        # Master overlay toggle — operators and panels read this to know
        # whether any viewport overlay is currently drawing.  Costs zero
        # if no overlay phase is active.
        self.overlay_enabled: bool = False
        #: Tags of overlays that are currently live, e.g.
        #: ``{"p5_trajectory_overlay"}``.  Lets operators detect which
        #: specific overlays are active (e.g. offset modal can skip
        #: drawing if its data is being snapshot/restored).
        self.active_overlay_tags: set[str] = set()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a transient runtime value by key."""
        return self._custom.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store a transient runtime value by key."""
        self._custom[key] = value

    def pop(self, key: str, default: Any = None) -> Any:
        """Remove and return a transient runtime value by key."""
        return self._custom.pop(key, default)

    def clear(self) -> None:
        """Reset all transient runtime state to defaults."""
        self.is_batch_processing = False
        self.active_tool_id = ""
        self.suppress_updates = False
        self._custom.clear()
        self.overlay_enabled = False
        self.active_overlay_tags.clear()


_state: RuntimeState | None = None


def init() -> None:
    """Initialize the module-level runtime state singleton."""
    global _state
    _state = RuntimeState()


def get_state() -> RuntimeState:
    """Retrieve the runtime state singleton, lazily initializing if needed."""
    if _state is None:
        init()
    return _state


def shutdown() -> None:
    """Clear and destroy the runtime state singleton."""
    global _state
    if _state is not None:
        _state.clear()
        _state = None