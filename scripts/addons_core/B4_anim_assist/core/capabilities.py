"""Capability registry – tracks what features/subsystems are available."""

from __future__ import annotations

from .logging import get_logger

__all__ = ["CapabilityRegistry", "init", "get_registry", "shutdown"]

_log = get_logger(__name__)

_DEFAULT_CAPABILITIES = (
    "preferences",
    "diagnostics",
    "settings_io",
    "context_resolver",
    "fcurve_utils",
    "metadata",
    "hotkeys",
    "cache",
    "runtime",
)


class CapabilityRegistry:
    """Track which subsystems initialized successfully so operators can degrade gracefully."""
    def __init__(self) -> None:
        self._capabilities: dict[str, bool] = {}

    def register(self, name: str, available: bool = True) -> None:
        """Mark a subsystem as available or unavailable."""
        self._capabilities[name] = available

    def is_available(self, name: str) -> bool:
        """Check if a subsystem (e.g., fcurve_utils) initialized successfully."""
        return self._capabilities.get(name, False)

    def all_capabilities(self) -> dict[str, bool]:
        """Return a copy of all registered capabilities and their states."""
        return dict(self._capabilities)

    def clear(self) -> None:
        """Clear all capability registrations."""
        self._capabilities.clear()


_registry: CapabilityRegistry | None = None


def init() -> None:
    """Initialize the capability registry with defaults."""
    global _registry
    _registry = CapabilityRegistry()
    for capability in _DEFAULT_CAPABILITIES:
        _registry.register(capability, True)


def get_registry() -> CapabilityRegistry:
    """Retrieve the capability registry singleton, lazily initializing if needed."""
    if _registry is None:
        init()
    return _registry


def shutdown() -> None:
    """Clear and destroy the capability registry singleton."""
    global _registry
    if _registry is not None:
        _registry.clear()
        _registry = None