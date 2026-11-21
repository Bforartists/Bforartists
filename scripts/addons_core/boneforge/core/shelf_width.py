"""The shelves holding BoneCraft's tabs start wide enough (owner, 2026-10-10).

Bforartists' Tool Shelf starts 132 px wide and its sidebar 220 px, and its Python API cannot set a
region's width (``Region.width`` is read-only; ``screen.region_scale`` only follows a mouse drag).
So this module writes the region's stored width (``ARegion.sizex``) directly, then has Bforartists lay
the region out again.

Safety: the field is written only where it is found beyond doubt. In memory the region's width and
height (``winx``, ``winy``) come first, then its region type a few bytes later, and ``sizex`` 6 bytes
after the type. All three must match what Python reports, and only one place may match. Otherwise
nothing is written: a future Bforartists that lays the struct out differently gets no widening, not a
crash. The pure part (``locate``, ``target``) imports without Bforartists and is unit-tested.

Each shelf is widened once per session, and only when it is narrower than the minimum: a shelf the
user drags narrower afterwards stays as they left it. Moving a tab to a side widens that side again.
"""
import struct

REGION_TYPE = {"UI": 4, "TOOLS": 5}       # DNA eRegion_Type
_SCAN = 448                               # bytes of ARegion searched (sizex sits near 200 in 5.2)
_TYPE_WINDOW = 40                         # bytes after winx/winy in which the region type must sit
DEFAULT_MIN = {"TOOLS": 240, "UI": 260}

_done = set()                             # (area pointer, region type) widened, or left alone, already
_timer = None


def locate(raw, width, height, rtype, scale=1.0):
    """Byte offset of ``sizex`` in the region bytes ``raw``, or None when not found beyond doubt."""
    def short(off):
        return struct.unpack_from("<h", raw, off)[0]

    stored = width / scale
    found = []
    for off in range(0, len(raw) - 4, 2):
        if short(off) != width or short(off + 2) != height:
            continue
        for rt in range(off + 4, min(off + _TYPE_WINDOW, len(raw) - 8), 2):
            if short(rt) == rtype and abs(short(rt + 6) - stored) <= 1:
                found.append(rt + 6)
                break
    return found[0] if len(found) == 1 else None


def target(width, minimum, scale):
    """The stored width (unscaled px) to give a region ``width`` screen px wide, or None to leave it."""
    return minimum if width / scale < minimum else None


# -- Bforartists side --------------------------------------------------------------------------

def _offset(region):
    import ctypes
    import bpy
    scale = bpy.context.preferences.system.ui_scale
    raw = (ctypes.c_char * _SCAN).from_address(region.as_pointer()).raw
    return locate(raw, region.width, region.height, REGION_TYPE.get(region.type, -1), scale)


def _relayout(area, region_type):
    """Hide and show the region: Bforartists lays it out again from its stored width."""
    space = area.spaces.active
    flag = "show_region_toolbar" if region_type == "TOOLS" else "show_region_ui"
    setattr(space, flag, False)
    setattr(space, flag, True)


def set_width(area, region, px):
    """Give ``region`` a stored width of ``px`` (unscaled). Returns True when written."""
    import ctypes
    off = _offset(region)
    if off is None:
        return False
    ctypes.c_short.from_address(region.as_pointer() + off).value = int(px)
    _relayout(area, region.type)
    return True


def _prefs():
    try:
        import bpy
        return bpy.context.preferences.addons["boneforge"].preferences
    except (AttributeError, KeyError):
        return None


def _sides_in_use(prefs):
    """Region types holding at least one shown BoneCraft tab."""
    from boneforge import tab_sides
    out = set()
    for key, _category, side_pref, show_pref in tab_sides.TABS:
        if prefs is not None and not getattr(prefs, show_pref, True):
            continue
        out.add(tab_sides.region_for(tab_sides.side_of(key)))
    return out


def widen_all():
    """Widen, once, every visible shelf holding a BoneCraft tab that is narrower than its minimum."""
    import bpy
    prefs = _prefs()
    if prefs is not None and not getattr(prefs, "auto_widen", True):
        return
    minimum = {"TOOLS": getattr(prefs, "shelf_min_left", DEFAULT_MIN["TOOLS"]),
               "UI": getattr(prefs, "shelf_min_right", DEFAULT_MIN["UI"])}
    scale = bpy.context.preferences.system.ui_scale
    sides = _sides_in_use(prefs)
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            space = area.spaces.active
            for region in area.regions:
                if region.type not in sides:
                    continue
                shown = space.show_region_toolbar if region.type == "TOOLS" else space.show_region_ui
                key = (area.as_pointer(), region.type)
                if not shown or region.width <= 1 or key in _done:
                    continue                      # hidden: widen it the first time it is opened
                _done.add(key)
                px = target(region.width, minimum[region.type], scale)
                if px is not None:
                    set_width(area, region, px)


def forget_all():
    """A width setting changed: check every shelf again on the next pass."""
    _done.clear()


def forget(region_type):
    """A tab moved to this side: widen it again on the next pass."""
    for key in [k for k in _done if k[1] == region_type]:
        _done.discard(key)


def _tick():
    try:
        widen_all()
    except Exception:                                      # noqa: BLE001 - never break the UI over this
        import logging
        logging.getLogger(__name__).exception("[BoneCraft] shelf widening failed")
    return 1.0                                             # new windows and 3D views are widened too


def register():
    global _timer
    import bpy
    if _timer is None or not bpy.app.timers.is_registered(_timer):
        _timer = _tick
        bpy.app.timers.register(_timer, first_interval=0.5, persistent=True)


def unregister():
    global _timer
    import bpy
    if _timer is not None and bpy.app.timers.is_registered(_timer):
        bpy.app.timers.unregister(_timer)
    _timer = None
    _done.clear()
