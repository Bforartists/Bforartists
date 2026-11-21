"""Centralised logging configuration for the addon."""

from __future__ import annotations

import logging

__all__ = ["get_logger", "set_level"]

_ADDON_LOGGER_NAME = "anim_assist"
_root_logger = logging.getLogger(_ADDON_LOGGER_NAME)

# Ensure at least one handler exists so messages are not silently dropped.
if not _root_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("[%(name)s %(levelname)s] %(message)s")
    )
    _root_logger.addHandler(_handler)

_root_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger scoped under the addon root logger."""
    if name.startswith(_ADDON_LOGGER_NAME):
        return logging.getLogger(name)
    short = name.rsplit(".", 1)[-1]
    return _root_logger.getChild(short)


def set_level(debug: bool) -> None:
    """Toggle between DEBUG and WARNING based on the debug flag."""
    _root_logger.setLevel(logging.DEBUG if debug else logging.WARNING)