"""Which side of the 3D viewport each BoneCraft tab sits on (spec 2026-10-08-tab-sides).

Left is the Tool Shelf (region ``TOOLS``, T key); right is the sidebar (region ``UI``, N key).
A tab is every BoneCraft ``VIEW_3D`` panel with one ``bl_category``. :func:`place` moves a tab by
unregistering its panels, changing their region and registering them again; the classes keep their
ids, order and polls, so the show switches and the Properties copies keep working.

The top half is pure Python (unit-tested outside Bforartists); ``bpy`` is imported only inside the
host functions.
"""
import contextlib
import logging

logger = logging.getLogger(__name__)

TABS = (
    # (tab key, bl_category, side preference, show preference)
    ("boneforge", "BoneCraft", "side_boneforge", "show_tab_boneforge"),
    ("cats", "CATS", "side_cats", "show_tab_cats"),
    ("rig_builder", "Rig Builder", "side_rig_builder", "show_tab_rig_builder"),
)
DEFAULT_SIDE = {"boneforge": "LEFT", "rig_builder": "LEFT", "cats": "RIGHT"}
REGION = {"LEFT": "TOOLS", "RIGHT": "UI"}
SIDE_ITEMS = (
    ("LEFT", "Left", "On the left Tool Shelf (T)"),
    ("RIGHT", "Right", "On the right sidebar (N)"),
)
_ADDON_KEY = "boneforge"
_PACKAGE = __name__.rpartition(".")[0]          # "boneforge" (or its installed package name)


def region_for(side):
    """``"LEFT"`` -> ``"TOOLS"``, ``"RIGHT"`` -> ``"UI"``; anything else -> ``"UI"``."""
    return REGION.get(side, "UI")


def tab(key):
    """The ``TABS`` row for ``key``."""
    return next(t for t in TABS if t[0] == key)


def parents_first(classes):
    """``classes`` ordered so each panel comes after its ``bl_parent_id`` (when that parent is in the list).

    Otherwise the input order is kept. A panel whose parent chain loops is put last."""
    ids = {c.bl_idname for c in classes}
    out, placed, rest = [], set(), list(classes)
    while rest:
        ready = [c for c in rest if getattr(c, "bl_parent_id", "") not in ids - placed]
        if not ready:
            out.extend(rest)
            break
        for c in ready:
            out.append(c)
            placed.add(c.bl_idname)
            rest.remove(c)
    return out


def side_of(key, context=None):
    """The side the preferences name for tab ``key``; its default when they cannot be read."""
    try:
        if context is None:
            import bpy
            context = bpy.context
        side = getattr(context.preferences.addons[_ADDON_KEY].preferences, tab(key)[2])
    except Exception:
        return DEFAULT_SIDE[key]
    return side if side in REGION else DEFAULT_SIDE[key]


# -- host ------------------------------------------------------------------------------------------

def _ours(cls):
    module = getattr(cls, "__module__", "") or ""
    return module == _PACKAGE or module.startswith(_PACKAGE + ".")


def panels_of(category):
    """Registered BoneCraft panels in the 3D viewport (either side) with ``bl_category == category``."""
    import bpy
    return [c for c in bpy.types.Panel.__subclasses__()
            if getattr(c, "is_registered", False) and _ours(c)
            and getattr(c, "bl_space_type", "") == "VIEW_3D"
            and getattr(c, "bl_region_type", "") in ("TOOLS", "UI")
            and getattr(c, "bl_category", "") == category]


def place(key, side=None, context=None):
    """Move tab ``key`` to ``side`` (default: the side its preference names). Never raises.

    All or nothing: if one panel cannot be registered on the new side, the whole tab goes back to its old
    side (a child cannot sit under a parent in another region). Returns the number of panels moved."""
    import bpy
    try:
        target = region_for(side or side_of(key, context))
        group = panels_of(tab(key)[1])
        moving = {c.bl_idname for c in group if c.bl_region_type != target}
        grew = True
        while grew:                                   # a moving panel takes its children along
            more = {c.bl_idname for c in group if getattr(c, "bl_parent_id", "") in moving} - moving
            moving |= more
            grew = bool(more)
        ordered = parents_first([c for c in group if c.bl_idname in moving])
    except Exception:
        logger.exception("[BoneCraft] could not work out tab %s", key)
        return 0
    for cls in reversed(ordered):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            logger.exception("[BoneCraft] could not unregister %s", cls.__name__)
    old = {cls: cls.bl_region_type for cls in ordered}
    done = []
    for cls in ordered:
        try:
            cls.bl_region_type = target
            bpy.utils.register_class(cls)
            done.append(cls)
        except Exception:
            logger.exception("[BoneCraft] could not move %s to %s; tab %s stays where it was", cls.__name__, target, key)
            break
    if len(done) < len(ordered):                      # put the whole tab back
        for cls in reversed(ordered):
            if getattr(cls, "is_registered", False):
                try:
                    bpy.utils.unregister_class(cls)
                except Exception:
                    logger.exception("[BoneCraft] could not unregister %s", cls.__name__)
        for cls in ordered:
            cls.bl_region_type = old[cls]
            try:
                bpy.utils.register_class(cls)
            except Exception:
                logger.exception("[BoneCraft] could not register %s again", cls.__name__)
        done = []
    _redraw()
    return len(done)


@contextlib.contextmanager
def placing():
    """While active, each BoneCraft viewport-tab panel registers straight on its tab's side.

    Used around switching a tool on: its panels may sit under a parent from another package that already sits
    on the chosen side, and Blender refuses a child whose parent is in another region, so moving them after
    registration would be too late."""
    import bpy
    real = bpy.utils.register_class

    def register_class(cls):
        try:
            if (isinstance(cls, type) and issubclass(cls, bpy.types.Panel) and _ours(cls)
                    and getattr(cls, "bl_space_type", "") == "VIEW_3D"
                    and getattr(cls, "bl_region_type", "") in ("TOOLS", "UI")):
                key = next((t[0] for t in TABS if t[1] == getattr(cls, "bl_category", "")), None)
                if key is not None:
                    cls.bl_region_type = region_for(side_of(key))
        except Exception:
            logger.exception("[BoneCraft] could not choose a side for %s", getattr(cls, "__name__", cls))
        return real(cls)

    bpy.utils.register_class = register_class
    try:
        yield
    finally:
        bpy.utils.register_class = real


def place_all(context=None):
    """Place every tab on the side its preference names."""
    for key, *_rest in TABS:
        place(key, context=context)


def _redraw():
    try:
        import bpy
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
    except Exception:
        pass


def schedule(key):
    """Move tab ``key`` on the next timer tick (panels cannot be registered while a preference draws).

    Returns the timer function."""
    import bpy

    def _tick():
        place(key)
        try:                                          # the side the tab moved to starts wide enough too
            from boneforge.core import shelf_width
            shelf_width.forget(region_for(side_of(key)))
        except Exception:
            logger.exception("[BoneCraft] could not re-check the shelf width")
        return None                                   # run once

    bpy.app.timers.register(_tick, first_interval=0.0)
    return _tick
