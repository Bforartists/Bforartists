"""Mirror BoneCraft N-panel panels into the Properties editor.

v3.0.20: All BoneCraft panels are also registered as sub-panels under
the Properties editor's Armature data tab.  The mirror appears only
when an armature is the active object, giving riggers the option to
work from the Properties editor without duplicating draw code.

How it works:
  After every phase has registered its original `BF_PT_*` panels, we
  walk `bpy.types` looking for panels whose ``bl_space_type == 'VIEW_3D'``
  and ``bl_category == 'BoneCraft'``.  For each one, we
  dynamically synthesise a sibling class that shares the original's
  ``draw`` (and ``draw_header``/``poll`` if present) but lives in the
  Properties editor's Armature-data context.  Sub-panel relationships
  (``bl_parent_id``) are remapped onto the mirror ids so children
  nest correctly.

The mirror classes are tracked in a module-level list so
``unregister`` can reverse the process cleanly.
"""

import logging

import bpy

logger = logging.getLogger(__name__)

_mirror_classes: list = []

# Suffix appended to the original panel's bl_idname to avoid collisions.
_MIRROR_SUFFIX = "_Prop"


def _iter_candidate_panels():
    """Yield every registered BoneCraft panel class that lives in VIEW_3D.

    v3.0.25: Walk ``bpy.types.Panel.__subclasses__()`` instead of
    scanning ``dir(bpy.types)``.  The latter misses dynamically
    registered panels on some Blender/Bforartists builds.  The
    subclass walk is what Blender itself uses internally to render
    panels, so anything visible to Blender is visible to us.
    """
    seen = set()
    for cls in bpy.types.Panel.__subclasses__():
        if cls in seen:
            continue
        seen.add(cls)
        name = cls.__name__
        # BoneForge panels use the BF_PT_ or BONEFORGE_PT_ prefix.
        if not (name.startswith("BF_PT_") or name.startswith("BONEFORGE_PT_")):
            continue
        if getattr(cls, "bl_space_type", None) != "VIEW_3D":
            continue
        # Any BoneForge-owned category qualifies.
        category = getattr(cls, "bl_category", None)
        # v3.2.2: all BoneForge panels live under "BoneForge" now.
        # Legacy "Tool" support kept for users with mixed installs.
        # v3.8.0: "Rig Builder" is the sibling sidebar tab for Quick
        # Rig, Auto-Rig Wizard, and Mannequin generation; mirror those
        # panels into the Properties editor too.
        if category not in ("BoneCraft", "Tool", "Rig Builder"):
            continue
        # The optional Rig Builder Tool Shelf tab is itself a copy of the
        # Scene-tab panels; Rig Builder already lives in Properties.
        if name.endswith("_Shelf"):
            continue
        # Mechanisms has its permanent copy in the Scene tab (spec D10), not in Armature data.
        if name.startswith("BF_PT_mech"):
            continue
        yield cls


def _make_armature_gated_poll(original_poll):
    """Return a (cls, context) classmethod body that gates by ARMATURE.

    The wrapped poll has exactly two parameters so signature inspection
    in Bforartists 5.2 / Blender 5.x accepts it. ``original_poll`` is
    captured via closure rather than as a default argument so it does
    not appear in the function's parameter list.
    """
    def _gated_poll(cls, context):
        active = context.active_object
        if active is None or active.type != "ARMATURE":
            return False
        try:
            # The sidebar tab switches do not hide Properties copies.
            from boneforge.core.tab_switches import tabs_on
            return original_poll(tabs_on(context))
        except Exception:
            return False
    return _gated_poll


def _default_armature_poll(cls, context):
    """Default poll for mirrors whose original had none — gate by armature."""
    active = context.active_object
    return active is not None and active.type == "ARMATURE"


def _build_mirror(orig_cls, mirror_id_map):
    """Synthesise a Properties-editor mirror of *orig_cls*.

    Args:
        orig_cls: the original N-panel class.
        mirror_id_map: dict mapping original bl_idname → mirror bl_idname,
            populated as mirrors are built so children can resolve their
            parent's mirror id.

    Returns:
        The new mirror class, or ``None`` if it couldn't be built.
    """
    orig_idname = getattr(orig_cls, "bl_idname", orig_cls.__name__)
    mirror_idname = orig_idname + _MIRROR_SUFFIX

    attrs = {
        "bl_idname": mirror_idname,
        "bl_label": getattr(orig_cls, "bl_label", orig_cls.__name__),
        "bl_space_type": "PROPERTIES",
        "bl_region_type": "WINDOW",
        "bl_context": "data",
        "bl_options": set(getattr(orig_cls, "bl_options", set()))
        | {"DEFAULT_CLOSED"},
        "bl_order": getattr(orig_cls, "bl_order", 0),
        "draw": orig_cls.draw,
    }

    # Preserve optional hooks if defined on the original.
    for hook in ("draw_header", "draw_header_preset"):
        if hasattr(orig_cls, hook):
            attrs[hook] = getattr(orig_cls, hook)

    # Poll needs an extra armature gate so the mirror hides for other
    # object types (the Armature-data tab is only shown for armatures
    # already, but defensively guarding keeps us safe in edge cases).
    original_poll = getattr(orig_cls, "poll", None)

    # v3.8.2: closure factories instead of default-arg capture so the
    # mirror's poll function has exactly (cls, context) — Bforartists 5.2
    # and Blender 5.x reject any classmethod whose signature reports
    # more than 2 parameters, even when the extras have defaults.
    if original_poll is not None:
        attrs["poll"] = classmethod(_make_armature_gated_poll(original_poll))
    else:
        attrs["poll"] = classmethod(_default_armature_poll)

    # Remap parent id to the mirror of the parent, if there is one.
    parent_id = getattr(orig_cls, "bl_parent_id", None)
    if parent_id:
        mirror_parent = mirror_id_map.get(parent_id)
        if mirror_parent:
            attrs["bl_parent_id"] = mirror_parent
        else:
            # Parent wasn't mirrored — skip to avoid a dangling child.
            return None

    mirror_cls = type(orig_cls.__name__ + "_Prop", (bpy.types.Panel,), attrs)
    return mirror_cls


def register():
    """Walk registered BF_PT_* panels and register Properties-tab mirrors.

    Called from ``boneforge.__init__.register`` after every phase has
    finished registering its own classes.  Any panel we fail to mirror
    is logged and skipped — failure here must not break the addon.
    """
    global _mirror_classes
    _mirror_classes = []

    # Order parents before children so bl_parent_id can resolve.
    candidates = list(_iter_candidate_panels())
    candidates.sort(key=lambda c: 1 if getattr(c, "bl_parent_id", None) else 0)

    # v3.1.6 (Mod-3): use the module logger so messages respect the user's
    # logging level instead of always hitting the system console.
    logger.info("[BoneCraft] Properties mirror: found %d N-panel class(es) to mirror.",
                len(candidates))

    mirror_id_map: dict = {}
    succeeded = 0

    for orig_cls in candidates:
        try:
            mirror_cls = _build_mirror(orig_cls, mirror_id_map)
            if mirror_cls is None:
                continue
            bpy.utils.register_class(mirror_cls)
            _mirror_classes.append(mirror_cls)
            mirror_id_map[
                getattr(orig_cls, "bl_idname", orig_cls.__name__)
            ] = mirror_cls.bl_idname
            succeeded += 1
        except Exception as exc:
            logger.warning(
                "BoneCraft: could not mirror %s into Properties editor: %s",
                orig_cls.__name__, exc,
            )
            logger.warning("[BoneCraft] mirror failed for %s: %s: %s",
                           orig_cls.__name__, type(exc).__name__, exc)

    logger.info("[BoneCraft] Properties mirror: registered %d mirror panel(s) under Armature data.",
                succeeded)


def unregister():
    """Unregister every mirror class built by ``register``."""
    for cls in reversed(_mirror_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            # Already-gone mirror — nothing to do.
            pass
    _mirror_classes.clear()
