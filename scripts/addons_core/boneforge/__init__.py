"""BoneCraft — Modular Rigging Extension, exclusive to Bforartists.

**This build runs only in Bforartists.** ``register()`` performs
internal runtime validation before loading feature packages. In
standard Blender, only an install guidance notice is registered.

Add-on entry point. Reads ``bl_info`` for the add-on browser,
registers an i18n layer, then walks every feature package in
:data:`_FEATURE_PACKAGES` and asks it for a ``ToolManifest`` describing
the panels, operators, and properties it owns.

Top-level architecture
----------------------
``core/``                Always-on infrastructure: armature helpers,
                         preferences, draw registry, tool registry,
                         lifecycle teardown sweep.
``ui_panels/``           Rig UI and viewport controls — bone-collection
                         panel, visibility bookmarks, hotkey popup.
                         (manifest id: ``phase1_panels``.)
``animation/``           Animation workflow — pose library, graph and
                         viewport tools, Rigify enhancement, corrective
                         shape keys, tween machine, animation layers.
                         (manifest id: ``phase2_animation``.)
``weights/``             Weight and deform tooling — weight mirror,
                         weight transfer, weight table, deform-bone
                         control, delta mush, proximity wrap, custom
                         shape library. (manifest id:
                         ``phase2b_weights``.)
``advanced_rigging/``    Advanced rigging systems — rig validator,
                         space switching, spline IK, ribbons, chain
                         dynamics, viseme rig, SDK driver builder, rig
                         notes. (manifest id: ``phase2c_advanced``.)
``autorig/``             Auto-rigging wizard — body / face / finger
                         generators, retarget, mannequin, skin
                         pipeline, in-viewport quick-human flow.
                         (manifest id: ``phase3_autorig``.)
``bone_merge.py``        Three-stage bone-merge workspace.
``vrchat/``              VRChat avatar tooling — CATS-style cleanup,
                         clothing merge, hair physbones, naming
                         detector, performance ranking, FBX export.
``io_hub/``              Import / Export hub — single home for VRM,
                         MMD, FBX, glTF bridges and game-ready export.
``vrm/``                 Bridge to vrm-addon-for-blender for VRoid /
                         VTuber pipelines.
``mmd/``                 PMX / VMD bridge for MMD pipelines.
``taskboard/``           Sidebar layout, Rig Builder overview hub,
                         bone inspector, task board.

Lifecycle
---------
The Tool Registry (``core/tool_registry.py``) owns *enable* / *disable*
for every package. Disabling a tool actually unregisters its classes —
functional hide, not a poll-trick hide — so it pays its full cost only
when the user wants it on. The enabled set is persisted in addon
preferences as a CSV string keyed by manifest id, NOT by package name.
That means the directory rename that landed in 7.2.1 is invisible to
existing user preferences.

Install
-------
Edit → Preferences → Add-ons → Install from Disk → choose the BoneCraft
zip → tick the BoneCraft entry. The 3D Viewport sidebar gains a Rig
Builder tab; Properties → Object Data picks up a mirror panel for the
active armature.

Version history note
--------------------
v3.3.0 introduced the Tool Registry and ``ToolManifest`` pattern.
v7.2.1 (this release) renames the historical ``phaseN`` directories
to descriptive category names (``ui_panels``, ``animation``,
``weights``, ``advanced_rigging``, ``autorig``) without changing
manifest ids, public operator bl_idnames, panel bl_idnames, or scene
property names. User saves, hotkeys, and enabled-tool prefs carry over
unchanged.
"""

bl_info = {
    "name": "BoneCraft",
    "author": "BoneCraft Team",
    "version": (9, 2, 18),
    "blender": (4, 0, 0),
    "location": "3D Viewport > Tool Shelf / Sidebar > BoneCraft, Rig Builder, CATS",
    "description": (
        "Bforartists-exclusive build. Universal rig UI, animation "
        "workflow, auto-rigging, mannequin generation, facial rig "
        "generation, and VRM/VRoid bridge for VTuber + VRChat pipelines"
    ),
    "warning": "Bforartists-only build — locked in standard Blender",
    "category": "Rigging",
    "doc_url": "",
    "tracker_url": "",
}


import logging
import traceback

logger = logging.getLogger(__name__)

# Feature packages. Order matters:
#   1. The registry registers manifests in this order.
#   2. Shared UI parents (taskboard) come first so child panels using
#      bl_parent_id can register against existing parent idnames.
#   3. The IDs inside each manifest (e.g. ``phase1_panels``) are
#      stable across the v7.2.1 rename — the package name on disk
#      changed; the manifest id on the user's preference CSV did not.
_FEATURE_PACKAGES = (
    'taskboard',
    'ui_panels',         # was phase1
    'animation',         # was phase2
    'weights',           # was phase2b
    'advanced_rigging',  # was phase2c
    'autorig',           # was phase3
    'control_ui',        # control picker / rig UI (BFA-exclusive, R7)
    'mechanisms',
    'bone_merge',
    'vrchat',
    'io_hub',
    'vrm',
    'mmd',
)

# Backwards-compat alias for any external script that imported the
# constant by its old name. Read-only — intentionally aliased, not
# duplicated, so they cannot drift apart.
_PHASE_NAMES = _FEATURE_PACKAGES


# -- Stale-module purge ------------------------------------------------

def _maybe_purge_stale_modules():
    """Drop any leftover ``boneforge.*`` modules from a previous install.

    When the user reinstalls or upgrades the add-on without restarting
    Blender, ``sys.modules`` still holds the previous package's
    classes and ``bpy.types`` still has its registered types. We:

    1. Ask the lifecycle helper to unregister any lingering classes
       and scrub leftover Scene properties.
    2. Pop every ``boneforge.*`` entry from ``sys.modules`` so
       subsequent imports re-read disk.

    Failures here are logged but never raised — a botched purge must
    not block the new install from registering.
    """
    import sys

    self_module_name = __name__
    stale_module_names = [
        name for name in list(sys.modules)
        if (name == "boneforge" or name.startswith("boneforge."))
        and name != self_module_name
    ]
    if not stale_module_names:
        return

    logger.info(
        "[BoneCraft] detected %d stale module(s) from a previous "
        "install -- purging before re-register",
        len(stale_module_names),
    )
    try:
        from boneforge.core import lifecycle as _lifecycle
        _lifecycle.unregister_lingering_classes()
        _lifecycle.scrub_scene_properties()
    except Exception:
        traceback.print_exc()

    for module_name in stale_module_names:
        try:
            del sys.modules[module_name]
        except KeyError:
            # Another thread already popped it. Harmless.
            pass


# -- Enabled-set persistence -------------------------------------------

def _load_enabled_set(context=None):
    """Return the user's enabled tool ids, or ``None`` on first run.

    The user's selection is persisted on
    ``BoneForgePreferences.enabled_tools_csv`` as a comma-separated
    list of manifest ids (e.g. ``"phase1_panels,phase2_animation,..."``).

    Returns:
        ``None`` -- preference is empty/unset; caller should fall back
        to ``registry.enable_all_default()``.
        ``set`` -- the manifest ids the user previously enabled.
    """
    try:
        if context is None:
            import bpy
            context = bpy.context
        from boneforge.core.prefs import addon_prefs
        prefs = addon_prefs(context)
        if prefs is None:
            return None
        csv_value = getattr(prefs, "enabled_tools_csv", "") or ""
        if not csv_value.strip():
            return None
        return {
            entry.strip()
            for entry in csv_value.split(",")
            if entry.strip()
        }
    except Exception:
        traceback.print_exc()
        return None


def _read_tool_csvs(context=None):
    """(enabled_tools_csv, known_tools_csv), or ("", "") when preferences are unavailable."""
    try:
        import bpy
        from boneforge.core.prefs import addon_prefs
        prefs = addon_prefs(context or bpy.context)
        return prefs.enabled_tools_csv or "", getattr(prefs, "known_tools_csv", "") or ""
    except Exception:          # add-on not installed under "boneforge" (headless tests)
        return "", ""


def _write_known_csv(value, context=None):
    try:
        import bpy
        from boneforge.core.prefs import addon_prefs
        addon_prefs(context or bpy.context).known_tools_csv = value
    except Exception:
        pass


def _save_enabled_set(context=None):
    """Persist the registry's current enabled set to addon preferences.

    Called by ``BONEFORGE_OT_toggle_tool`` after every enable/disable
    so the choice round-trips across Blender restarts. Writing the
    *resolved* set means transitively enabled dependencies are also
    saved.
    """
    try:
        if context is None:
            import bpy
            context = bpy.context
        from boneforge.core.prefs import addon_prefs
        from boneforge.core.tool_registry import get_registry
        prefs = addon_prefs(context)
        if prefs is None:
            return
        prefs.enabled_tools_csv = ",".join(get_registry().enabled_ids())
    except Exception:
        traceback.print_exc()


# -- Bforartists-exclusive runtime validation ---------------------------

# True while the notice-only stub is registered.
_lockout_active = False

# Set False by unregister() so the re-verify timer stops cleanly.
_reverify_enabled = False


def _bfa_environment_ok():
    """Return whether the current host is approved for this build."""
    import sys
    try:
        import bpy
    except ImportError:
        return True  # outside any Blender host (tests / tooling)
    app = bpy.app
    try:
        if getattr(app, "bforartists_version", None):
            return True
    except Exception:
        pass
    try:
        if "bforartists" in (getattr(app, "binary_path", "") or "").lower():
            return True
    except Exception:
        pass
    try:
        if "bforartists" in (sys.executable or "").lower():
            return True
    except Exception:
        pass
    for resource_kind in ("USER", "LOCAL", "SYSTEM"):
        try:
            if "bforartists" in (
                bpy.utils.resource_path(resource_kind) or ""
            ).lower():
                return True
        except Exception:
            continue
    return False


def _bfa_reverify():
    """Periodic validation callback for the exclusive build."""
    global _reverify_enabled, _lockout_active
    if not _reverify_enabled:
        return None  # unregistered — stop the timer
    if _bfa_environment_ok():
        return 600.0  # all good — check again in 10 minutes
    logger.error(
        "[BoneCraft] post-startup re-verification failed — "
        "host is not Bforartists. Unloading.",
    )
    _reverify_enabled = False
    try:
        unregister()
    except Exception:
        traceback.print_exc()
    try:
        from boneforge import bfa_guard
        bfa_guard.register_lockout()
        _lockout_active = True
    except Exception:
        traceback.print_exc()
    return None


# -- Top-level register / unregister -----------------------------------

# Track the manifest ids we registered so unregister() can drop them
# in reverse order.
_registered_manifest_ids: list = []


def register():
    """Register BoneCraft with the host application.

    Sequence:

    0. Validate the host before registering feature packages. If
       validation fails, register only the install guidance notice and
       return.
    1. Purge stale ``boneforge.*`` modules from a previous install.
    2. Register the i18n layer so ``T()`` is available to every panel
       label registered in subsequent steps.
    3. Register ``core`` -- preferences, lifecycle, tool toggle.
    4. Import every package in :data:`_FEATURE_PACKAGES` and ask it
       for a ``ToolManifest``. Packages that don't expose
       ``_get_manifest`` are treated as legacy and registered
       directly.
    5. Enable manifests according to the persisted user choice, or
       ``registry.enable_all_default()`` on first run.
    6. Register the Properties-editor mirror so the active armature
       gets a BoneCraft mini-panel under Object Data Properties.

    Manifests are *registered* in step 4 but only *enabled* in step
    5 so that all dependency declarations are visible before the
    registry resolves any enable order.
    """
    global _registered_manifest_ids, _lockout_active, _reverify_enabled

    # Step 0: Bforartists gate. Both the inline copy and the guard
    # module must agree the host is Bforartists.
    from boneforge import bfa_guard
    if not (_bfa_environment_ok() and bfa_guard.is_bforartists()):
        bfa_guard.register_lockout()
        _lockout_active = True
        return

    _maybe_purge_stale_modules()

    # i18n: register before core so T() is available immediately.
    from boneforge import i18n as _i18n
    _i18n.register()

    # Step 1: core (mandatory, always-on).
    from boneforge import core
    core.register()

    # Steps 2-4: import each feature package, register its manifest.
    from boneforge.core.tool_registry import get_registry
    registry = get_registry()

    discovered_manifest_ids: list = []
    discovered_defaults = set()
    for package_name in _FEATURE_PACKAGES:
        try:
            package_module = __import__(
                f'boneforge.{package_name}',
                fromlist=[package_name],
            )
        except ImportError as exc:
            logger.error(
                "[BoneCraft] could not import package %s: %s",
                package_name, exc,
            )
            continue

        if not hasattr(package_module, '_get_manifest'):
            # Legacy: register directly without the registry.
            try:
                package_module.register()
            except Exception:
                logger.error(
                    "[BoneCraft] failed to register legacy package %s",
                    package_name,
                )
                traceback.print_exc()
            continue

        try:
            manifest = package_module._get_manifest()
            registry.register_tool(manifest)
            discovered_manifest_ids.append(manifest.id)
            if manifest.default_enabled:
                discovered_defaults.add(manifest.id)
        except Exception:
            logger.error(
                "[BoneCraft] failed to read manifest for %s",
                package_name,
            )
            traceback.print_exc()

    _registered_manifest_ids = discovered_manifest_ids

    # Step 5: enable per user preferences (or defaults on first run). A tool
    # the user has never seen starts as its manifest says (tool_startup).
    from boneforge.tool_startup import startup
    enabled_csv, known_csv = _read_tool_csvs()
    to_enable, new_known = startup(discovered_manifest_ids, discovered_defaults, enabled_csv, known_csv)
    if to_enable is None:
        registry.enable_all_default()
    else:
        for manifest_id in to_enable:
            try:
                registry.enable(manifest_id)
            except Exception:
                logger.error("[BoneCraft] failed to enable %s", manifest_id)
                traceback.print_exc()
    _write_known_csv(new_known)
    # Write back the resolved set (includes transitive dependencies
    # that were also turned on).
    _save_enabled_set()

    # Step 5b: put each viewport tab on the side the preferences name (left Tool Shelf or right sidebar).
    try:
        from boneforge import tab_sides
        tab_sides.place_all()
    except Exception:
        traceback.print_exc()
        logger.error("[BoneCraft] could not place the viewport tabs")

    # Step 6: Properties-editor mirror panel.
    try:
        from boneforge.core import properties_mirror
        properties_mirror.register()
    except Exception:
        traceback.print_exc()
        logger.error(
            "[BoneCraft] Properties-editor mirror failed to register",
        )

    # Step 6b: CATS / VRChat / Import-Export copies in Properties > Scene tab.
    try:
        from boneforge.core import scene_tab_mirror
        scene_tab_mirror.register()
    except Exception:
        traceback.print_exc()
        logger.error("[BoneCraft] Scene-tab copies failed to register")

    # Step 6d: show, don't hide - a waiting section's sub-panels stay visible and say what to select.
    try:
        from boneforge.core import needs
        needs.keep_children_visible()
    except Exception:
        traceback.print_exc()
        logger.error("[BoneCraft] sub-panel notes failed")

    # Step 6e: every tab's panels wrap text to their region, on either side of the viewport.
    try:
        from boneforge.core import wrap_layout
        wrap_layout.install()
    except Exception:
        traceback.print_exc()
        logger.error("[BoneCraft] text wrapping failed to install")

    # Step 6f: the shelves holding these tabs start wide enough.
    try:
        from boneforge.core import shelf_width
        shelf_width.register()
    except Exception:
        traceback.print_exc()
        logger.error("[BoneCraft] shelf widening failed to start")

    # Step 6g: tools where Bforartists puts its own: header menus and Tool Shelf tab buttons.
    try:
        from boneforge.core import access
        access.register()
    except Exception:
        traceback.print_exc()
        logger.error("[BoneCraft] header menus and Tool Shelf buttons failed to register")

    # Step 7: arm the post-startup host validation timer.
    _reverify_enabled = True
    try:
        import bpy
        bpy.app.timers.register(_bfa_reverify, first_interval=20.0)
    except Exception:
        traceback.print_exc()


def unregister():
    """Unregister BoneCraft, scrub state, leave Blender clean.

    Sequence (reverse of register):

    1. Properties-editor mirror (depends on phase panels existing).
    2. Disable every enabled tool -- registry walks dependents-
       before-dependencies automatically when we iterate
       ``enabled_ids()`` in reverse.
    3. Drop manifests in reverse registration order.
    4. Unregister ``core``.
    5. Lifecycle teardown sweep -- unregister lingering classes,
       scrub Scene properties, clear ``__pycache__``.
    6. i18n.

    Every step is wrapped so a single failure cannot block teardown
    of subsequent steps; on a clean Blender exit a failure here
    would leak property registrations into the next install.
    """
    global _registered_manifest_ids, _lockout_active, _reverify_enabled

    # 0. Stop the host re-verification timer.
    _reverify_enabled = False
    try:
        import bpy
        if bpy.app.timers.is_registered(_bfa_reverify):
            bpy.app.timers.unregister(_bfa_reverify)
    except Exception:
        pass

    # Notice-only mode: only the stub was registered; drop it and stop.
    if _lockout_active:
        try:
            from boneforge import bfa_guard
            bfa_guard.unregister_lockout()
        except Exception:
            traceback.print_exc()
        _lockout_active = False
        return

    # 0. Header menu entries and Tool Shelf tab buttons.
    try:
        from boneforge.core import access
        access.unregister()
    except Exception:
        logger.error("[BoneCraft] header menus and Tool Shelf buttons failed to unregister")

    # 0. Shelf widening timer.
    try:
        from boneforge.core import shelf_width
        shelf_width.unregister()
    except Exception:
        logger.error("[BoneCraft] shelf widening failed to stop")

    # 0. Scene-tab copies (registered last, removed first).
    try:
        from boneforge.core import scene_tab_mirror
        scene_tab_mirror.unregister()
    except Exception:
        traceback.print_exc()

    # 1. Properties mirror.
    try:
        from boneforge.core import properties_mirror
        properties_mirror.unregister()
    except Exception:
        traceback.print_exc()

    # 2 & 3. Disable + drop manifests.
    try:
        from boneforge.core.tool_registry import get_registry
        registry = get_registry()
        for manifest_id in reversed(registry.enabled_ids()):
            try:
                registry.disable(manifest_id)
            except (ValueError, KeyError):
                # Already gone -- fine.
                pass
        for manifest_id in reversed(_registered_manifest_ids):
            registry.unregister_tool(manifest_id)
    except Exception:
        traceback.print_exc()

    _registered_manifest_ids.clear()

    # 4. Core last (because phase teardown still needs prefs).
    try:
        from boneforge import core
        core.unregister()
    except Exception:
        traceback.print_exc()

    # 5. Lifecycle teardown sweep.
    try:
        from boneforge.core import lifecycle
        teardown_summary = lifecycle.teardown(
            scrub_scene=True, clean_pycache=True,
        )
        if any(teardown_summary.values()):
            logger.info(
                "[BoneCraft] teardown swept: %s", teardown_summary,
            )
    except Exception:
        traceback.print_exc()

    # 6. i18n.
    try:
        from boneforge import i18n as _i18n
        _i18n.unregister()
    except Exception:
        pass


if __name__ == "__main__":
    register()
