"""BoneCraft core — draw function registry.

Phase modules register their panel-drawing functions here at
registration time. Other modules retrieve them by key, avoiding
any direct cross-module imports within a phase.

This keeps the architectural rule intact: modules never import
from each other's internals, only from boneforge.core.
"""

from typing import Callable, Optional

# Registry: maps string keys to draw callables.
# Populated during register(), cleared during unregister().
_draw_functions: dict[str, Callable] = {}


def register_draw(key: str, func: Callable) -> None:
    """Register a draw function under *key*.

    Intended to be called inside a module's register().
    """
    _draw_functions[key] = func


def unregister_draw(key: str) -> None:
    """Remove a draw function by *key*.

    Intended to be called inside a module's unregister().
    Silent if *key* was never registered.
    """
    _draw_functions.pop(key, None)


def get_draw(key: str) -> Optional[Callable]:
    """Retrieve a registered draw function by *key*.

    Returns None if *key* is not registered, allowing callers
    to degrade gracefully when a module is disabled.
    """
    return _draw_functions.get(key)


def clear_all() -> None:
    """Remove all registered draw functions.

    Called during full addon unregister.
    """
    _draw_functions.clear()
