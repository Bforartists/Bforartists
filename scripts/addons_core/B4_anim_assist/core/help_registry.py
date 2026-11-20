# --- EXPLAINER SYSTEM EXTENSION ---
"""Centralised help/explainer registry.

Every operator, property, panel, or control in Anim Assist can attach a
:class:`HelpEntry` to a unique ``help_id``. The registry is a pure in-memory
structure with no Blender RNA footprint — it is therefore safe to register and
unregister repeatedly across script reloads and module toggles.

Phases 2..10 never touch the registry directly; they ship their own
``core/help_phaseN_entries.py`` with a thin ``register()`` / ``unregister()``
pair that delegates to :func:`register_phase_help` /
:func:`unregister_phase_help`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .logging import get_logger

__all__ = [
    "HelpEntry",
    "register_help",
    "unregister_help",
    "get_help",
    "get_all_help",
    "get_help_by_category",
    "register_phase_help",
    "unregister_phase_help",
    "clear_all_help",
]

_log = get_logger(__name__)


@dataclass(frozen=True)
class HelpEntry:
    """A single help/explainer record.

    Attributes:
        id: Unique, stable key. Convention: ``"pref.<name>"`` for preferences,
            ``"op.<bl_idname>"`` for operators, ``"panel.<bl_idname>"`` for
            panels. Must be globally unique across phases.
        label: Short human-readable name shown in the Help Browser.
        tooltip: One-line summary, suitable as a ``bl_description``.
        description: Long, multi-paragraph explanation rendered in the popup.
            Paragraphs are separated by blank lines.
        phase: Phase owning the entry, e.g. ``"phase1"``. Used for bulk
            teardown.
        category: Grouping key for the Help Browser, e.g. ``"Diagnostics"``.
    """

    id: str
    label: str
    tooltip: str
    description: str
    phase: str
    category: str


# Module-level state. Cleared on unregister/reload via :func:`clear_all_help`.
_REGISTRY: dict[str, HelpEntry] = {}
_BY_PHASE: dict[str, set[str]] = {}


def register_help(entry: HelpEntry) -> None:
    """Register a single entry. Replaces any existing entry with the same id."""
    if entry.id in _REGISTRY:
        _log.debug("help_registry: replacing existing entry %s", entry.id)
        # Remove from old phase bucket so the phase index stays consistent.
        old = _REGISTRY[entry.id]
        _BY_PHASE.get(old.phase, set()).discard(entry.id)
    _REGISTRY[entry.id] = entry
    _BY_PHASE.setdefault(entry.phase, set()).add(entry.id)


def unregister_help(help_id: str) -> None:
    """Remove a single entry. Silent no-op if absent."""
    entry = _REGISTRY.pop(help_id, None)
    if entry is None:
        return
    bucket = _BY_PHASE.get(entry.phase)
    if bucket is not None:
        bucket.discard(help_id)
        if not bucket:
            _BY_PHASE.pop(entry.phase, None)


def get_help(help_id: str) -> HelpEntry | None:
    """Return the entry for ``help_id`` or *None*."""
    return _REGISTRY.get(help_id)


def get_all_help() -> tuple[HelpEntry, ...]:
    """Return every registered entry, sorted by category then label."""
    return tuple(
        sorted(_REGISTRY.values(), key=lambda e: (e.category.lower(), e.label.lower()))
    )


def get_help_by_category() -> dict[str, list[HelpEntry]]:
    """Return entries grouped by category, each group sorted by label."""
    groups: dict[str, list[HelpEntry]] = {}
    for entry in _REGISTRY.values():
        groups.setdefault(entry.category, []).append(entry)
    for items in groups.values():
        items.sort(key=lambda e: e.label.lower())
    return dict(sorted(groups.items(), key=lambda kv: kv[0].lower()))


def register_phase_help(phase: str, entries: Iterable[HelpEntry]) -> int:
    """Register a batch of entries for ``phase``. Returns the number registered."""
    count = 0
    for entry in entries:
        if entry.phase != phase:
            # Keep the phase consistent with the batch key; replace with
            # a coerced copy rather than raising so a typo can't brick load.
            entry = HelpEntry(
                id=entry.id,
                label=entry.label,
                tooltip=entry.tooltip,
                description=entry.description,
                phase=phase,
                category=entry.category,
            )
        register_help(entry)
        count += 1
    _log.debug("help_registry: registered %d entries for %s", count, phase)
    return count


def unregister_phase_help(phase: str) -> int:
    """Remove every entry belonging to ``phase``. Returns the count removed."""
    ids = list(_BY_PHASE.get(phase, ()))
    for help_id in ids:
        _REGISTRY.pop(help_id, None)
    _BY_PHASE.pop(phase, None)
    _log.debug("help_registry: unregistered %d entries for %s", len(ids), phase)
    return len(ids)


def clear_all_help() -> None:
    """Wipe the entire registry. Used on addon teardown."""
    _REGISTRY.clear()
    _BY_PHASE.clear()
