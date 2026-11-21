"""Central registry of BoneCraft tools (v3.3.0).

Each BoneCraft tool ships a :class:`ToolManifest` declaring its identity,
dependencies, default-enabled state, and register/unregister callables.
The :class:`ToolRegistry` holds them all and is the single source of
truth for what's enabled at runtime.

The prefs panel reads ``registry.all_tools()`` to generate per-tool
toggle buttons; the user clicks them and the toggle operator dispatches
to ``registry.enable(id)`` / ``registry.disable(id)`` via the deferred
pattern. When a tool is disabled, its register/unregister callables
actually run — classes leave ``bpy.types``, properties leave
``bpy.types.Scene``, draw handlers detach. *Functional* hide, not
poll-trick hide.

The registry has no Blender-side state of its own. Side effects on
``bpy.types`` happen exclusively inside ``enable`` / ``disable``,
which call the per-tool callables. This means the registry is unit-
testable headlessly without bpy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolManifest:
    """Declarative description of a BoneCraft tool.

    Fields:

    id
        Stable machine identifier. Lowercase snake_case. Never
        reused after a tool is renamed (use a new id; the old one
        becomes a no-op).
    name
        Human-readable display name shown in prefs.
    description
        One-sentence summary shown next to the toggle.
    icon
        Blender icon name (e.g. ``"ARMATURE_DATA"``, ``"WORLD"``).
        Default ``"TOOL_SETTINGS"``.
    default_enabled
        Whether the tool is on by default for a fresh install. The
        user's preference takes precedence on subsequent launches;
        this is consulted only if no saved preference exists.
    depends_on
        Tuple of tool ids that must be enabled before this one.
        Enabling a tool transitively enables its dependencies.
        Disabling refuses if any enabled tool depends on this one.
    register_fn / unregister_fn
        Zero-arg callables that perform the actual side effects on
        ``bpy.types``. Called from ``enable`` / ``disable``. Must be
        idempotent — calling register twice should not error; calling
        unregister twice should not error.
    owns_classes / owns_scene_props / owns_handlers
        Inventory ledger for the 3.3.x audit pass. Optional in 3.3.0;
        when populated, future tooling can verify post-disable that
        the tool's claimed inventory is actually gone.
    """

    id: str
    name: str
    description: str
    icon: str = "TOOL_SETTINGS"
    default_enabled: bool = True
    depends_on: tuple = ()
    register_fn: Optional[Callable[[], None]] = None
    unregister_fn: Optional[Callable[[], None]] = None
    owns_classes: tuple = ()
    owns_scene_props: tuple = ()
    owns_handlers: tuple = ()


class ToolRegistry:
    """Holds the set of declared tools and the currently-enabled subset."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolManifest] = {}
        self._enabled: set[str] = set()

    # ── Discovery ────────────────────────────────────────────────

    def register_tool(self, manifest: ToolManifest) -> None:
        """Add or replace a tool's manifest. Does not enable the tool."""
        if manifest.id in self._tools:
            logger.warning(
                "[BoneCraft] tool %r re-registered — overwriting manifest",
                manifest.id,
            )
        self._tools[manifest.id] = manifest

    def unregister_tool(self, tool_id: str) -> None:
        """Drop a tool's manifest. Disables first if currently enabled."""
        if tool_id in self._enabled:
            try:
                self.disable(tool_id)
            except ValueError:
                # Force disable if dependents exist — caller is unloading.
                manifest = self._tools.get(tool_id)
                if manifest and manifest.unregister_fn:
                    try:
                        manifest.unregister_fn()
                    except Exception:
                        logger.exception(
                            "[BoneCraft] forced unregister failed for %s",
                            tool_id,
                        )
                self._enabled.discard(tool_id)
        self._tools.pop(tool_id, None)

    def all_tools(self) -> list[ToolManifest]:
        return list(self._tools.values())

    def get(self, tool_id: str) -> Optional[ToolManifest]:
        return self._tools.get(tool_id)

    def is_registered(self, tool_id: str) -> bool:
        return tool_id in self._tools

    def is_enabled(self, tool_id: str) -> bool:
        return tool_id in self._enabled

    def dependents_of(self, tool_id: str) -> list[str]:
        """Return ids of *enabled* tools that depend on *tool_id*."""
        return sorted(
            t.id for t in self._tools.values()
            if tool_id in t.depends_on and t.id in self._enabled
        )

    # ── Enable / disable ─────────────────────────────────────────

    def enable(self, tool_id: str) -> None:
        """Enable a tool, recursively enabling its dependencies first."""
        if tool_id in self._enabled:
            return
        manifest = self._tools.get(tool_id)
        if manifest is None:
            raise KeyError(f"unknown tool: {tool_id}")

        for dep in manifest.depends_on:
            if dep not in self._enabled:
                self.enable(dep)

        if manifest.register_fn is not None:
            try:
                manifest.register_fn()
            except Exception:
                logger.exception(
                    "[BoneCraft] register_fn for %r raised — leaving disabled",
                    tool_id,
                )
                return

        self._enabled.add(tool_id)
        logger.info("[BoneCraft] enabled tool: %s", tool_id)
        try:                                               # its new panels wrap like the rest of the tab
            from boneforge.core import wrap_layout
            wrap_layout.install()
        except Exception:
            logger.exception("[BoneCraft] text wrapping for %r failed", tool_id)

    def disable(self, tool_id: str) -> None:
        """Disable a tool. Refuses if other enabled tools depend on it."""
        if tool_id not in self._enabled:
            return
        manifest = self._tools[tool_id]

        dependents = self.dependents_of(tool_id)
        if dependents:
            raise ValueError(
                f"cannot disable {tool_id}: "
                f"{', '.join(dependents)} depend on it",
            )

        if manifest.unregister_fn is not None:
            try:
                manifest.unregister_fn()
            except Exception:
                logger.exception(
                    "[BoneCraft] unregister_fn for %r raised — "
                    "marking disabled anyway",
                    tool_id,
                )

        self._enabled.discard(tool_id)
        logger.info("[BoneCraft] disabled tool: %s", tool_id)

    # ── Bulk operations ──────────────────────────────────────────

    def enable_all_default(self) -> None:
        """Enable every tool whose manifest declares default_enabled=True.

        Honours dependencies via the recursive ``enable`` path. Useful
        on fresh installs / first-run.
        """
        for manifest in self._tools.values():
            if manifest.default_enabled and manifest.id not in self._enabled:
                try:
                    self.enable(manifest.id)
                except KeyError:
                    pass

    def enabled_ids(self) -> list[str]:
        return sorted(self._enabled)


# Module-level singleton.
_registry: Optional[ToolRegistry] = None

# BFA-exclusive build: cache the approved-host verdict for this session.
_bfa_host_verified: Optional[bool] = None


def _verify_bfa_host() -> bool:
    """Return whether the current host is approved for this build."""
    global _bfa_host_verified
    if _bfa_host_verified is not None:
        return _bfa_host_verified
    import sys
    try:
        import bpy
    except ImportError:
        _bfa_host_verified = True  # outside any Blender host (tests)
        return True
    verdict = False
    app = bpy.app
    try:
        if getattr(app, "bforartists_version", None):
            verdict = True
    except Exception:
        pass
    if not verdict:
        try:
            if "bforartists" in (
                getattr(app, "binary_path", "") or ""
            ).lower():
                verdict = True
        except Exception:
            pass
    if not verdict:
        try:
            if "bforartists" in (sys.executable or "").lower():
                verdict = True
        except Exception:
            pass
    if not verdict:
        for resource_kind in ("USER", "LOCAL", "SYSTEM"):
            try:
                if "bforartists" in (
                    bpy.utils.resource_path(resource_kind) or ""
                ).lower():
                    verdict = True
                    break
            except Exception:
                continue
    _bfa_host_verified = verdict
    return verdict


def get_registry() -> ToolRegistry:
    """Return the process-wide tool registry, lazy-initialised.

    The BFA-exclusive package exposes the registry only in Bforartists.
    """
    global _registry
    if not _verify_bfa_host():
        raise RuntimeError(
            "[boneforge.tool_registry] BoneCraft is exclusive to "
            "Bforartists and cannot run in standard Blender."
        )
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_registry() -> None:
    """For testing only — drop the singleton so a fresh one is built."""
    global _registry
    _registry = None
