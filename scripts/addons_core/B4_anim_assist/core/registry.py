"""Safe class registration / unregistration manager."""

from __future__ import annotations

import bpy

from . import explainers
from .logging import get_logger

__all__ = ["ClassRegistry"]

_log = get_logger(__name__)


class ClassRegistry:
    """Register Blender classes in order with rollback on failure."""

    def __init__(self) -> None:
        self._classes: list[type] = []
        self._registered: list[type] = []

    def add(self, cls: type) -> None:
        """Add a Blender class to the registration queue."""
        if cls not in self._classes:
            self._classes.append(cls)

    def extend(self, classes: tuple[type, ...] | list[type]) -> None:
        """Add multiple Blender classes to the registration queue."""
        for cls in classes:
            self.add(cls)

    def register(self) -> None:
        """Register all queued classes with Blender. On failure, roll back all previously registered classes to avoid partial addon state."""
        for cls in self._classes:
            try:
                explainers.register_class(cls)
                self._registered.append(cls)
            except ValueError as exc:
                if "already registered" in str(exc):
                    _log.debug("Class %s already registered; skipping", cls.__name__)
                    self._registered.append(cls)
                else:
                    _log.exception("Failed to register %s; rolling back", cls)
                    self.unregister()
                    raise
            except Exception:
                _log.exception("Failed to register %s; rolling back", cls)
                self.unregister()
                raise

    def unregister(self) -> None:
        """Unregister all registered classes from Blender in reverse order."""
        for cls in reversed(self._registered):
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                _log.debug("Failed to unregister %s", cls, exc_info=True)
        self._registered.clear()

    @property
    def registered_count(self) -> int:
        """Return the number of successfully registered classes."""
        return len(self._registered)