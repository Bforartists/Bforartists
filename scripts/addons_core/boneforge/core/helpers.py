# bonecraft/boneforge/core/helpers.py
"""Show Helpers: one preference hides BoneCraft's teaching text everywhere (spec §7.1).

What / when lines, "How this works" notes and full guided-step sentences follow
it. Always shown, whatever it says: guided steps themselves, lists, Test,
warnings and Blender's own tooltips.
"""


def _prefs(context):
    try:
        return context.preferences.addons["boneforge"].preferences
    except (AttributeError, KeyError):
        return None


def helpers_on(context):
    prefs = _prefs(context)
    return True if prefs is None else bool(getattr(prefs, "show_helpers", True))


def say(context, long_text, short_text):
    """The full sentence when helpers are on, the short label when they are off."""
    return long_text if helpers_on(context) else short_text


def _is_wide(ch):
    import unicodedata
    return unicodedata.east_asian_width(ch) in "WF"


def wrap(text, width_px, measure, first_width=None):
    """Lines of ``text`` that each fit ``width_px`` as ``measure(str) -> px`` judges (owner, 2026-10-10).

    Breaks at spaces; text without spaces (Japanese, Chinese) breaks between characters; only a word
    wider than a whole line is split. ``first_width`` (default ``width_px``) is the first line's room,
    narrower when an icon sits on it; when even the first word does not fit there, the first line is
    "" so the caller can drop the icon. ``width_px`` 0 or less means the width is unknown: one line."""
    first = width_px if first_width is None else first_width
    if width_px <= 0 or measure(text) <= first:
        return [text]
    tokens = []                                       # (piece, joins to the previous piece with a space)
    for i, word in enumerate(text.split(" ")):
        if any(_is_wide(c) for c in word) and measure(word) > width_px:   # a run with no spaces (ja, zh)
            for j, ch in enumerate(word):
                tokens.append((ch, i > 0 and j == 0))
        else:
            tokens.append((word, i > 0))
    lines, line = [], ""
    for piece, spaced in tokens:
        limit = first if not lines else width_px
        candidate = (line + (" " if spaced and line else "") + piece) if line else piece
        if measure(candidate) <= limit:
            line = candidate
            continue
        if line or (not lines and first_width is not None and measure(piece) <= width_px):
            lines.append(line)                        # "": the first word misses only the icon's line
        line = piece
        while measure(line) > width_px and len(line) > 1:   # a single piece wider than a whole line
            hyphen = "" if any(_is_wide(c) for c in line) else "-"   # a Latin word carries a hyphen
            cut = len(line) - 1
            while cut > 1 and measure(line[:cut] + hyphen) > width_px:
                cut -= 1
            lines.append(line[:cut] + hyphen)
            line = line[cut:]
    lines.append(line)
    return lines


def clip(text, width_px, measure):
    """``text`` if it fits ``width_px``, else its longest start that fits with an ellipsis after it."""
    if measure(text) <= width_px:
        return text
    cut = len(text)
    while cut > 0 and measure(text[:cut].rstrip() + "…") > width_px:
        cut -= 1
    return text[:cut].rstrip() + "…"


def _measure(context):
    """A pixel measure for the UI font at the current scale, or None outside a drawn region."""
    try:
        import blf
        scale = context.preferences.system.ui_scale
        blf.size(0, 11 * scale)
        return lambda s: blf.dimensions(0, s)[0]
    except Exception:                                 # noqa: BLE001 - no font / no preferences: no wrapping
        return None


# px (at 1x) a label line loses to the region: category tabs ~20, panel margins and text padding ~36
_MARGIN, _ICON, _BOX, _MIN = 56, 24, 14, 48


def line_room(region_width, scale, icon=False, inset=0):
    """Px a label line may fill in a region ``region_width`` px wide; at least ``_MIN`` (1x) so text still wraps."""
    room = region_width - (_MARGIN + inset + (_ICON if icon else 0)) * scale
    return max(room, _MIN * scale)


def draw_wrapped(layout, context, text, icon='NONE', translate=False, inset=0):
    """``text`` as one label per line, wrapped to the region's width; one label outside a drawn region.

    ``inset``: extra px (at 1x) the layout loses, e.g. ``_BOX`` inside a box."""
    region = getattr(context, "region", None)
    measure = _measure(context) if region is not None else None
    if measure is None:
        layout.label(text=text, icon=icon, translate=translate)
        return
    icon, lines = _lines(context, region, measure, text, icon, inset, strict=True)
    for i, line in enumerate(lines):
        layout.label(text=line, icon=icon if i == 0 else 'NONE', translate=translate)


def _lines(context, region, measure, text, icon, inset, strict=False):
    """(icon, lines): the icon narrows only the first line; it is dropped when even the first word misses.

    ``strict`` (text lines): also dropped when its line would be under the minimum width. A button keeps
    its icon: it says what the button does, and a toggle's arrow says whether it is open."""
    scale = context.preferences.system.ui_scale
    full = line_room(region.width, scale, False, inset)
    if icon == 'NONE':
        return icon, wrap(text, full, measure)
    beside = region.width - (_MARGIN + inset + _ICON) * scale   # the icon's line, no minimum
    if strict and beside < _MIN * scale:                         # too little room: the icon goes, not the text
        return 'NONE', wrap(text, full, measure)
    lines = wrap(text, full, measure, first_width=max(beside, _MIN * scale))
    if lines[0] == "":
        return 'NONE', wrap(text, full, measure)
    return icon, lines


_BUTTON = 10      # px (at 1x) a button's frame and text padding take beyond a label's


def draw_wrapped_operator(layout, context, op, text, icon='NONE', inset=0, emboss=True):
    """A button for ``op`` whose text wraps to the region's width (owner, 2026-10-10).

    Blender cannot wrap a button, so a long one becomes a stack of aligned segments, one per line,
    all running ``op``: it reads as one tall button and nothing is cut off. The icon goes on the
    first segment. Returns every segment's operator properties: set the same values on each."""
    region = getattr(context, "region", None)
    measure = _measure(context) if region is not None else None
    lines = [text]
    if measure is not None:
        icon, lines = _lines(context, region, measure, text, icon, inset + _BUTTON)
    col = layout.column(align=True) if len(lines) > 1 else layout
    made = []
    for i, line in enumerate(lines):
        where = col
        if not emboss:                                    # a flat toggle reads as a heading: left-aligned
            where = col.row()
            where.alignment = 'LEFT'
        made.append(where.operator(op, text=line, icon=icon if i == 0 else 'NONE', emboss=emboss, translate=False))
    return made


def draw_helper(layout, context, line1, line2=None):
    """A subdued what / when box, wrapped to the panel width; nothing when Show Helpers is off."""
    if not helpers_on(context):
        return
    box = layout.box()
    col = box.column(align=True)
    col.scale_y = 0.75
    draw_wrapped(col, context, line1, icon='INFO', inset=_BOX)
    if line2:
        draw_wrapped(col, context, line2, inset=_BOX)


def options_fold(layout, key, text="Options", default_closed=True):
    """The settings of the actions drawn above, in a fold below them, closed by default: act first, tune
    later (UI critique, 2026-10-10). Returns the layout to draw them in, or None while the fold is closed.
    ``key`` names the fold; it must be unique within the panel. A layout without folds (a stand-in, an
    older host) gets a plain column, so the settings still draw."""
    from boneforge.i18n import T
    try:
        header, body = layout.panel(key, default_closed=default_closed)
    except (TypeError, ValueError, AttributeError):
        return layout.column()
    header.label(text=T(text))
    return body


def draw_compact_toggle(layout, context):
    """VRChat's Compact Mode button: a shortcut to Show Helpers (Compact Mode on = helpers off)."""
    from boneforge.i18n import T
    prefs = _prefs(context)
    if prefs is None:
        return
    layout.prop(prefs, "show_helpers", text=T("Compact Mode"), toggle=True, invert_checkbox=True, icon='HIDE_OFF')
