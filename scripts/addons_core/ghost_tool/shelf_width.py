"""One-time Ghost shelf widening, adapted from BoneCraft's core/shelf_width.py.

The public region width is read-only. BoneCraft's workaround locates the native
stored width from matching dimensions, region type and UI scale, then requests
a relayout. Only one verified candidate is written; unknown/ambiguous layouts
stay untouched. This is an internal host-layout workaround, not a public API.
Ghost remains standalone and does not import BoneCraft.
"""
import math
import struct

REGION_TYPE = {'UI': 4, 'TOOLS': 5}
_SCAN = 448
_TYPE_WINDOW = 40
DEFAULT_MIN = 240
_done = set()


def locate(raw, width, height, rtype, scale=1.0):
    """Find a unique stored-width offset using BoneCraft's neighbor checks."""
    if (width <= 1 or height <= 1 or rtype not in REGION_TYPE.values()
            or not math.isfinite(scale) or scale <= 0):
        return None

    def short(offset):
        return struct.unpack_from('<h', raw, offset)[0]

    found = set()
    for off in range(0, len(raw) - 4, 2):
        if short(off) != width or short(off + 2) != height:
            continue
        for rt in range(off + 4, min(off + _TYPE_WINDOW, len(raw) - 8), 2):
            if short(rt) == rtype and abs(short(rt + 6) - width / scale) <= 1:
                found.add(rt + 6)
    return next(iter(found)) if len(found) == 1 else None


def target(width, sidebar_width, scale=1.0):
    """Match an open sidebar, otherwise use BoneCraft's left minimum; only widen."""
    if width <= 1 or not math.isfinite(scale) or scale <= 0:
        return None
    minimum = math.ceil(sidebar_width / scale) if sidebar_width > 1 else DEFAULT_MIN
    if not 1 < minimum < 32767:
        return None
    return minimum if width / scale < minimum else None


def _offset(region, scale):
    import ctypes
    rtype = REGION_TYPE.get(region.type)
    if rtype is None or region.width <= 1 or region.height <= 1:
        return None
    raw = (ctypes.c_char * _SCAN).from_address(region.as_pointer()).raw
    return locate(raw, region.width, region.height, rtype, scale)


def set_width(area, region, px, *, scale=None):
    """Write one verified stored-width short and request the native relayout."""
    import ctypes
    if not isinstance(px, int) or not 1 < px < 32767:
        return False
    if scale is None:
        import bpy
        scale = bpy.context.preferences.system.ui_scale
    off = _offset(region, scale)
    if off is None:
        return False
    ctypes.c_short.from_address(region.as_pointer() + off).value = px
    space = area.spaces.active
    flag = 'show_region_toolbar' if region.type == 'TOOLS' else 'show_region_ui'
    setattr(space, flag, False)
    setattr(space, flag, True)
    area.tag_redraw()
    return True


def widen_all():
    """Widen ordinary left Ghost homes once, preserving subsequent manual sizes."""
    import bpy
    from .ui_panel import display_location, supports_tool_shelf, _ordinary_viewports
    context = bpy.context
    addon = context.preferences.addons.get('ghost_tool')
    prefs = addon.preferences if addon else None
    if (not supports_tool_shelf() or display_location(context) != 'TOOLS'
            or not getattr(prefs, 'auto_widen_shelf', True)):
        return
    scale = context.preferences.system.ui_scale
    for window, area in _ordinary_viewports(context):
        space = area.spaces.active
        if not space.show_region_toolbar:
            continue
        tools = next((r for r in area.regions if r.type == 'TOOLS'), None)
        if tools is None or tools.width <= 1:
            continue
        key = (window.as_pointer(), area.as_pointer(), tools.as_pointer())
        if key in _done:
            continue
        sidebar = next((r for r in area.regions if r.type == 'UI'), None)
        if space.show_region_ui and (sidebar is None or sidebar.width <= 1):
            continue  # Wait for an opening N-panel to finish layout before matching it.
        reference = sidebar.width if space.show_region_ui else 0
        px = target(tools.width, reference, scale)
        if px is None or set_width(area, tools, px, scale=scale):
            _done.add(key)


def forget_all(*_args):
    """An explicit location/width preference change or file load permits a recheck."""
    _done.clear()


def _tick():
    try:
        widen_all()
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Ghost shelf widening failed')
    return 1.0


def register():
    import bpy
    forget_all()
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=0.5, persistent=True)
    bpy.app.handlers.persistent(forget_all)
    if forget_all not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(forget_all)


def unregister():
    import bpy
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    if forget_all in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(forget_all)
    forget_all()
