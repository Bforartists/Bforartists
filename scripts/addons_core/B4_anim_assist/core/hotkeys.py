"""Hotkey registration framework with lifecycle-safe defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import bpy

from .logging import get_logger

__all__ = [
    "HotkeyEntry",
    "HotkeyManager",
    "register_hotkey_defaults_callback",
    "get_manager",
    "shutdown",
]

_log = get_logger(__name__)


@dataclass
class HotkeyEntry:
    """A keybinding specification for an operator with modifiers and properties."""
    keymap_name: str
    space_type: str
    operator_idname: str
    key_type: str
    event_type: str = "PRESS"
    ctrl: bool = False
    shift: bool = False
    alt: bool = False
    properties: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Module-level storage: survives manager recreation across disable/enable
# cycles thanks to Python module caching.
# ---------------------------------------------------------------------------

_defaults: list[HotkeyEntry] = []
_default_callbacks: list[Callable[[], None]] = []


def register_hotkey_defaults_callback(fn: Callable[[], None]) -> None:
    """Register a callable invoked every time ``register_defaults()`` runs.

    Future phases must use this instead of calling ``add_default()`` at import
    time so that hotkeys survive disable / enable cycles.
    """
    if fn not in _default_callbacks:
        _default_callbacks.append(fn)


class HotkeyManager:
    """Register and track addon hotkeys with duplicate detection and safe teardown.

    Guards against double-registration on F8 reload by checking existing
    KeyMapItems before adding new ones.  Tracks every registered item so
    ``unregister_all()`` can cleanly remove them without leaking shortcuts.
    """

    def __init__(self) -> None:
        self._addon_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []

    # -- defaults ----------------------------------------------------------

    def add_default(self, entry: HotkeyEntry) -> None:
        """Add a hotkey entry to the module-level defaults list."""
        if entry not in _defaults:
            _defaults.append(entry)

    def register_defaults(self) -> None:
        """Register all default hotkeys, invoking callbacks so hotkeys survive disable/enable cycles."""
        for cb in list(_default_callbacks):
            try:
                cb()
            except Exception:
                _log.exception("Hotkey default callback failed: %s", cb)

        for entry in list(_defaults):
            self.register_shortcut(entry)

    # -- duplicate detection -----------------------------------------------

    @staticmethod
    def _same_binding(kmi: bpy.types.KeyMapItem, entry: HotkeyEntry) -> bool:
        """Check key + modifiers **and** operator properties."""
        if not (
            kmi.idname == entry.operator_idname
            and kmi.type == entry.key_type
            and kmi.value == entry.event_type
            and kmi.ctrl == entry.ctrl
            and kmi.shift == entry.shift
            and kmi.alt == entry.alt
        ):
            return False

        for prop_name, prop_val in entry.properties.items():
            if not hasattr(kmi.properties, prop_name):
                return False
            if getattr(kmi.properties, prop_name) != prop_val:
                return False
        return True

    # -- registration / teardown -------------------------------------------

    def register_shortcut(self, entry: HotkeyEntry) -> None:
        """Register a hotkey, guarding against duplicate binding on F8 reload."""
        wm = getattr(bpy.context, "window_manager", None)
        kc = getattr(wm, "keyconfigs", None) if wm is not None else None
        kc_addon = kc.addon if kc is not None else None

        if kc_addon is None:
            _log.warning("No addon keyconfig; skipping %s", entry.operator_idname)
            return

        km = kc_addon.keymaps.new(
            name=entry.keymap_name, space_type=entry.space_type
        )

        for existing in km.keymap_items:
            if self._same_binding(existing, entry):
                _log.debug(
                    "Skipping duplicate hotkey for %s", entry.operator_idname
                )
                return

        kmi = km.keymap_items.new(
            entry.operator_idname,
            type=entry.key_type,
            value=entry.event_type,
            ctrl=entry.ctrl,
            shift=entry.shift,
            alt=entry.alt,
        )
        for prop_name, prop_val in entry.properties.items():
            setattr(kmi.properties, prop_name, prop_val)

        self._addon_keymaps.append((km, kmi))
        _log.debug("Registered hotkey: %s -> %s", entry.key_type, entry.operator_idname)

    def unregister_all(self) -> None:
        """Unregister all tracked hotkeys from Blender."""
        for km, kmi in self._addon_keymaps:
            try:
                km.keymap_items.remove(kmi)
            except Exception:
                _log.debug("Could not remove keymap item %s", kmi, exc_info=True)
        self._addon_keymaps.clear()

    @property
    def registered_count(self) -> int:
        """Return the number of currently registered hotkeys."""
        return len(self._addon_keymaps)


# ---------------------------------------------------------------------------
# Module-level singleton access
# ---------------------------------------------------------------------------

_manager: HotkeyManager | None = None


def get_manager() -> HotkeyManager:
    """Retrieve the hotkey manager singleton, lazily initializing if needed."""
    global _manager
    if _manager is None:
        _manager = HotkeyManager()
    return _manager


def shutdown() -> None:
    """Unregister all hotkeys and destroy the hotkey manager singleton."""
    global _manager
    if _manager is not None:
        _manager.unregister_all()
        _manager = None