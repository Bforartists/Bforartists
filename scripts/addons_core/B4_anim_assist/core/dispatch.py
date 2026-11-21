"""Internal command dispatch table."""

from __future__ import annotations

from typing import Any, Callable

from .logging import get_logger

__all__ = [
    "register_command",
    "dispatch",
    "has_command",
    "list_commands",
    "clear",
]

_log = get_logger(__name__)

_commands: dict[str, Callable[..., Any]] = {}


def register_command(name: str, handler: Callable[..., Any]) -> None:
    """Register a named command handler so other phases can invoke it without circular imports."""
    if name in _commands:
        _log.warning("Overwriting existing command: %s", name)
    _commands[name] = handler


def dispatch(name: str, **kwargs: Any) -> Any:
    """Invoke a registered command by name, decoupling the macro engine from individual feature modules."""
    handler = _commands.get(name)
    if handler is None:
        _log.error("Unknown command: %s", name)
        return None
    try:
        return handler(**kwargs)
    except Exception:
        _log.exception("Command '%s' failed", name)
        return None


def has_command(name: str) -> bool:
    """Check if a command is registered."""
    return name in _commands


def list_commands() -> list[str]:
    """Return a sorted list of all registered command names."""
    return sorted(_commands.keys())


def clear() -> None:
    """Clear all registered commands."""
    _commands.clear()