"""BoneCraft core -- public API surface for feature packages.

Every feature package (``ui_panels``, ``animation``, ``weights``,
``advanced_rigging``, ``autorig``, ``vrchat``, ``vrm``, ``mmd``,
``taskboard``, ``io_hub``, ``bone_merge``) imports only from this
package, never from a sibling. This keeps the dependency graph a
shallow tree -- features depend on core, never on each other.

Re-exports (stable, version-pinned)
-----------------------------------
``armature``       Armature / collection / vertex-group helpers --
                   the only place that touches ``bpy.data`` directly
                   for armature lookup. Keeps each feature module
                   from re-implementing "find the active armature
                   even if the user has a child mesh selected".
``prefs``          Addon preferences and the ``addon_prefs(context)``
                   accessor that handles missing-prefs gracefully.
``draw_registry``  Indirection layer for ``Panel.draw`` callbacks.
                   Lets one panel be authored once and rendered into
                   multiple ``bl_parent_id`` locations without
                   copying class definitions.

Custom-validation registry
--------------------------
Studios can register a check function via
:func:`register_custom_check` -- the function is called by
``advanced_rigging.rig_validator`` during a validate run and its
returned findings appear in the Task Board alongside built-in
checks.

Handler-chain registry
----------------------
:func:`register_handler_chain` lets a feature package install a
named, priority-sorted callback chain. Used by Phase 4 hooks to
inject pre/post-merge work without amending the wizard's own code.

This file contains *no* heavy logic. ``register()`` /
``unregister()`` only wire up ``prefs``, ``lifecycle_operators``,
and ``tool_toggle_operator``.
"""

from .armature import (
    active_armature,
    armature_data,
    bone_collections,
    collection_by_name,
    collection_bone_names,
    set_collection_visibility,
    snapshot_visibility,
    restore_visibility,
    read_custom_json,
    write_custom_json,
    select_bones_in_collection,
    is_rigify_human,
    vertex_weights_by_group_index,
    vertex_weights_by_group_name,
    find_avatar_armature,
)

from .prefs import (
    addon_prefs,
    BoneForgePreferences,
)

from .draw_registry import (
    register_draw,
    unregister_draw,
    get_draw,
)


# -- Custom-validation registry --------------------------------------
# Studios can plug in their own per-armature checks by calling
# register_custom_check(fn). The Rig Validator (advanced_rigging
# package) calls each registered fn during a validate run and merges
# the returned findings into the Task Board view.
_custom_validation_checks: list = []


def register_custom_check(check_fn):
    """Register a studio-custom validation check function.

    ``check_fn`` must accept a Blender armature object and return a
    list of dicts shaped like ``ValidationResult`` (see
    ``advanced_rigging/rig_validator.py``).
    """
    _custom_validation_checks.append(check_fn)


def unregister_custom_check(check_fn):
    """Remove a previously registered custom validation check."""
    _custom_validation_checks.remove(check_fn)


def get_custom_checks():
    """Return a fresh list of all registered custom check fns."""
    return list(_custom_validation_checks)


# -- Handler-chain registry ------------------------------------------
# A named chain is a priority-sorted list of callbacks. Feature
# packages register hooks; the autorig wizard / merge pipeline
# invokes them at known points so studios can inject pre- or
# post-step work without touching wizard code.
_handler_chains: dict = {}


def register_handler_chain(chain_name, handler_fn, priority=50):
    """Add ``handler_fn`` to ``chain_name``. Lower priority runs first."""
    if chain_name not in _handler_chains:
        _handler_chains[chain_name] = []
    _handler_chains[chain_name].append((priority, handler_fn))
    _handler_chains[chain_name].sort(key=lambda entry: entry[0])


def unregister_handler_chain(chain_name, handler_fn):
    """Remove a previously registered chain handler."""
    if chain_name in _handler_chains:
        _handler_chains[chain_name] = [
            (priority, registered_fn)
            for priority, registered_fn in _handler_chains[chain_name]
            if registered_fn is not handler_fn
        ]


def run_handler_chain(chain_name, *args, **kwargs):
    """Run every handler in ``chain_name`` in priority order."""
    for _priority, handler_fn in _handler_chains.get(chain_name, []):
        handler_fn(*args, **kwargs)


__all__ = [
    "active_armature",
    "armature_data",
    "bone_collections",
    "collection_by_name",
    "collection_bone_names",
    "set_collection_visibility",
    "snapshot_visibility",
    "restore_visibility",
    "read_custom_json",
    "write_custom_json",
    "select_bones_in_collection",
    "is_rigify_human",
    "vertex_weights_by_group_index",
    "vertex_weights_by_group_name",
    "find_avatar_armature",
    "addon_prefs",
    "BoneForgePreferences",
    "register_draw",
    "unregister_draw",
    "get_draw",
    "register_custom_check",
    "unregister_custom_check",
    "get_custom_checks",
    "register_handler_chain",
    "unregister_handler_chain",
    "run_handler_chain",
]


def _require_bfa_host():
    """Validate that this exclusive build is running in Bforartists."""
    import sys
    try:
        import bpy
    except ImportError:
        return  # outside any Blender host (tests / tooling)
    app = bpy.app
    try:
        if getattr(app, "bforartists_version", None):
            return
    except Exception:
        pass
    try:
        if "bforartists" in (getattr(app, "binary_path", "") or "").lower():
            return
    except Exception:
        pass
    try:
        if "bforartists" in (sys.executable or "").lower():
            return
    except Exception:
        pass
    for resource_kind in ("USER", "LOCAL", "SYSTEM"):
        try:
            if "bforartists" in (
                bpy.utils.resource_path(resource_kind) or ""
            ).lower():
                return
        except Exception:
            continue
    raise RuntimeError(
        "[boneforge.core] BoneCraft is exclusive to Bforartists "
        "and cannot run in standard Blender."
    )


def register():
    """Register the always-on core sub-modules.

    Order: ``prefs`` (BoneForgePreferences must exist before any
    package reads it), ``lifecycle_operators`` (teardown helpers),
    ``tool_toggle_operator`` (UI for enabling / disabling features).
    """
    _require_bfa_host()
    from . import prefs, lifecycle_operators, tool_toggle_operator
    prefs.register()
    lifecycle_operators.register()
    tool_toggle_operator.register()


def unregister():
    """Unregister core in reverse-of-registration order.

    ``draw_registry.clear_all()`` runs last so any feature package
    that re-registers in the same Blender session starts with a
    clean draw-callback slate.
    """
    from . import (
        prefs, draw_registry, lifecycle_operators, tool_toggle_operator,
    )
    tool_toggle_operator.unregister()
    lifecycle_operators.unregister()
    prefs.unregister()
    draw_registry.clear_all()
