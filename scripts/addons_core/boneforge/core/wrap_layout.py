"""Every tab wraps to its region, on either side of the viewport (owner, 2026-10-10).

The Tool Shelf starts 132 px wide and the sidebar 220 px, and an add-on cannot widen either. Blender
cuts a label or button that does not fit to "...". ``install()`` makes every BoneCraft, CATS and Rig
Builder viewport panel draw through ``WrapLayout``: in a column or box, a label too wide for the
region becomes several lines (helpers.draw_wrapped) and a button becomes a stack of segments that
run the same operator (helpers.draw_wrapped_operator). Text that fits, rows and splits (their width
is shared), unusual arguments, and draws with no region (background, tests) pass through untouched.
"""
import inspect

from boneforge.core import helpers

CATEGORIES = {"BoneCraft", "CATS", "Rig Builder"}
_LABEL_KEYS = {"text", "icon", "translate"}
_OPERATOR_KEYS = {"text", "icon", "emboss", "translate"}
_PROP_KEYS = {"text", "icon", "toggle", "translate", "invert_checkbox"}
_HEADER = 68          # px (at 1x) a panel header loses to the tabs, its arrow and margins
_HANDLE = 10          # px (at 1x) more for a top-level section: its drag handle
_CHECKBOX = 22        # px (at 1x) a checkbox takes before its text


def _op_label(idname):
    """The label Blender shows for operator ``idname`` when it is given no text, or None."""
    try:
        import bpy
        mod, name = idname.split(".", 1)
        return getattr(getattr(bpy.ops, mod), name).get_rna_type().name or None
    except Exception:                                      # noqa: BLE001 - unknown operator: leave it to Blender
        return None


def _iface(text, translate):
    if not translate:
        return text
    try:
        import bpy
        return bpy.app.translations.pgettext_iface(text)
    except Exception:                                      # noqa: BLE001 - no translations: the text as given
        return text


class _Segments:
    """The operator properties of every segment of a wrapped button: a value set reaches them all."""
    def __init__(self, items):
        object.__setattr__(self, "_items", items)

    def __getattr__(self, name):
        return getattr(self._items[0], name)

    def __setattr__(self, name, value):
        for item in self._items:
            setattr(item, name, value)


def as_setting(kwargs):
    """A setting's arguments with the button look taken off: icons are for operators (UI critique,
    2026-10-10). An icon-only control and an unembossed fold arrow keep their icon: it is all they show."""
    if kwargs.get("text") != "" and kwargs.get("emboss", True) and not kwargs.get("icon_only"):
        kwargs = {k: v for k, v in kwargs.items() if k not in ("icon", "toggle")}
    return kwargs


class _Plain:
    """A row, split or flow: its width is shared, so nothing wraps, but a setting still never looks like
    a button."""

    def __init__(self, real):
        object.__setattr__(self, "_real", real)

    def __getattr__(self, name):
        return getattr(self._real, name)

    def __setattr__(self, name, value):
        setattr(self._real, name, value)

    def prop(self, *args, **kwargs):
        return self._real.prop(*args, **as_setting(kwargs))

    def _sub(name):
        def make(self, *args, **kwargs):
            return _Plain(getattr(self._real, name)(*args, **kwargs))
        return make

    row, column, split = _sub("row"), _sub("column"), _sub("split")
    box, grid_flow, column_flow = _sub("box"), _sub("grid_flow"), _sub("column_flow")
    del _sub


class WrapLayout:
    """A stand-in for a vertical UILayout that wraps what would not fit; everything else passes through."""

    def __init__(self, real, context, inset=0):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_ctx", context)
        object.__setattr__(self, "_inset", inset)
        object.__setattr__(self, "_last", None)          # "prop" or "op": what this column drew last

    def _kind(self, kind):
        """Settings and actions are set apart: a small gap where a column turns from one to the other
        (UI critique, 2026-10-10). A label or a separator starts a new group."""
        if kind and self._last and kind != self._last:
            self._real.separator(factor=0.5)
        object.__setattr__(self, "_last", kind)

    def separator(self, *args, **kwargs):
        self._kind(None)
        return self._real.separator(*args, **kwargs)

    def menu(self, *args, **kwargs):
        self._kind("op")
        return self._real.menu(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._real, name)

    def __setattr__(self, name, value):
        setattr(self._real, name, value)

    def column(self, *args, **kwargs):
        return WrapLayout(self._real.column(*args, **kwargs), self._ctx, self._inset)

    def box(self, *args, **kwargs):
        return WrapLayout(self._real.box(*args, **kwargs), self._ctx, self._inset + helpers._BOX)

    def row(self, *args, **kwargs):
        return _Plain(self._real.row(*args, **kwargs))

    def panel(self, *args, **kwargs):
        """A fold: its header passes through, its body (None while closed) wraps like this layout."""
        self._kind(None)
        header, body = self._real.panel(*args, **kwargs)
        return header, (WrapLayout(body, self._ctx, self._inset) if body is not None else None)

    def split(self, *args, **kwargs):
        return _Plain(self._real.split(*args, **kwargs))

    def grid_flow(self, *args, **kwargs):
        return _Plain(self._real.grid_flow(*args, **kwargs))

    def column_flow(self, *args, **kwargs):
        return _Plain(self._real.column_flow(*args, **kwargs))

    def _room(self, icon, extra=0):
        """(measure, px a line may fill), or None when the width cannot be known."""
        region = getattr(self._ctx, "region", None)
        if region is None:
            return None
        measure = helpers._measure(self._ctx)
        if measure is None:
            return None
        scale = self._ctx.preferences.system.ui_scale
        return measure, helpers.line_room(region.width, scale, icon not in (None, 'NONE'), self._inset + extra)

    def label(self, *args, **kwargs):
        self._kind(None)
        text = kwargs.get("text")
        if args or not text or set(kwargs) - _LABEL_KEYS:
            return self._real.label(*args, **kwargs)
        icon = kwargs.get("icon", 'NONE')
        shown = _iface(text, kwargs.get("translate", True))
        room = self._room(icon)
        if room is None or room[0](shown) <= room[1]:
            return self._real.label(*args, **kwargs)
        helpers.draw_wrapped(self._real, self._ctx, shown, icon=icon, translate=False, inset=self._inset)
        return None

    def operator(self, *args, **kwargs):
        self._kind("op")
        text = kwargs.get("text")
        if text is None and len(args) == 1:
            text = _op_label(args[0])                      # no text: Blender shows the operator's label
        if len(args) != 1 or not text or set(kwargs) - _OPERATOR_KEYS:
            return self._real.operator(*args, **kwargs)
        icon = kwargs.get("icon", 'NONE')
        shown = _iface(text, kwargs.get("translate", True))
        room = self._room(icon, helpers._BUTTON)
        if room is None or room[0](shown) <= room[1]:
            return self._real.operator(*args, **kwargs)
        made = helpers.draw_wrapped_operator(self._real, self._ctx, args[0], shown, icon=icon,
                                             inset=self._inset, emboss=kwargs.get("emboss", True))
        return _Segments(made)


    def prop(self, *args, **kwargs):
        """A setting whose label is too wide (its text, or the property's own name when it has none).
        A checkbox or toggle becomes a checkbox with its label wrapped: a stack of toggle segments among
        other toggles would read as several buttons. Any other setting puts its label above and its
        control the whole width below. Blender would cut the label to an ellipsis.

        Icons are for operators: a setting with text never shows one, and an icon toggle draws as a
        checkbox, so a setting never looks like a button. An icon-only control and an unembossed fold
        arrow keep their icon, since it is all they show."""
        self._kind("prop")
        kwargs = as_setting(kwargs)
        if len(args) != 2 or set(kwargs) - _PROP_KEYS or kwargs.get("text") == "":
            return self._real.prop(*args, **kwargs)
        data, name = args
        try:
            rna = data.bl_rna.properties[name]
        except Exception:                                  # noqa: BLE001 - not an RNA property: Blender decides
            return self._real.prop(*args, **kwargs)
        text = kwargs.get("text")
        if text is None:
            text, translate = rna.name, True               # no text: Blender shows the property's name
        else:
            translate = kwargs.get("translate", True)
        if not text:
            return self._real.prop(*args, **kwargs)
        kind = rna.type
        icon = kwargs.get("icon", 'NONE')
        shown = _iface(text, translate)
        room = self._room(icon, _CHECKBOX if kind == 'BOOLEAN' else 0)
        if room is None:
            return self._real.prop(*args, **kwargs)
        measure, width = room
        if kind != 'BOOLEAN':
            width *= 0.2                                   # Blender gives a setting's label about a fifth of the row
        if measure(shown) <= width:
            return self._real.prop(*args, **kwargs)
        rest = {k: v for k, v in kwargs.items() if k not in ("text", "icon", "translate", "toggle")}
        if kind != 'BOOLEAN':
            helpers.draw_wrapped(self._real, self._ctx, shown, translate=False, inset=self._inset)
            return self._real.prop(data, name, text="", icon=icon, **rest)
        # a checkbox, never an icon toggle (a setting with an icon draws as a button): its box narrows only
        # the first line; the lines below it have the full width
        scale = self._ctx.preferences.system.ui_scale
        width = self._ctx.region.width
        lines = helpers.wrap(shown, helpers.line_room(width, scale, False, self._inset), measure,
                             first_width=helpers.line_room(width, scale, False, self._inset + _CHECKBOX))
        self._real.prop(data, name, text=lines[0], translate=False, **rest)
        for line in lines[1:]:
            self._real.label(text=line, translate=False)
        return None


class HeaderLayout:
    """A panel header's layout. It never shows an icon (icons are for operators). A title cannot wrap, so in a
    narrow region it is shortened with an ellipsis. Blender would otherwise show no title at all."""

    def __init__(self, real, context, root=False):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_ctx", context)
        object.__setattr__(self, "_root", root)

    def __getattr__(self, name):
        return getattr(self._real, name)

    def __setattr__(self, name, value):
        setattr(self._real, name, value)

    def label(self, *args, **kwargs):
        kwargs.pop("icon", None)                 # icons are for operators: a panel header carries none (Bforartists)
        text = kwargs.get("text")
        region = getattr(self._ctx, "region", None)
        measure = helpers._measure(self._ctx) if region is not None else None
        if args or not text or set(kwargs) - _LABEL_KEYS or measure is None:
            return self._real.label(*args, **kwargs)
        shown = _iface(text, kwargs.get("translate", True))
        scale = self._ctx.preferences.system.ui_scale
        room = region.width - (_HEADER + (_HANDLE if self._root else 0)) * scale
        if measure(shown) <= room:
            return self._real.label(*args, **kwargs)
        return self._real.label(text=helpers.clip(shown, room, measure), translate=False)


class _Self:
    """The panel as its draw sees it: ``layout`` is the wrapper; helper methods are bound to this stand-in
    so they draw through the wrapper too; anything else is the panel's own."""

    def __init__(self, panel, layout, owner):
        object.__setattr__(self, "_panel", panel)
        object.__setattr__(self, "_owner", owner)
        object.__setattr__(self, "layout", layout)

    def __getattr__(self, name):
        for cls in (self._owner, type(self._panel)):
            attr = inspect.getattr_static(cls, name, None)
            if inspect.isfunction(attr):
                return attr.__get__(self)
        return getattr(self._panel, name)

    def __setattr__(self, name, value):
        setattr(self._panel, name, value)


def _wrap(cls):
    orig = cls.draw

    def draw(self, context):
        if isinstance(self.layout, WrapLayout):            # a hub's delegated draw: already wrapped
            return orig(self, context)
        return orig(_Self(self, WrapLayout(self.layout, context), cls), context)

    draw._bc_wrap_layout = True
    draw.__wrapped__ = orig
    cls.draw = draw
    head = getattr(cls, "draw_header", None)
    if callable(head) and not getattr(head, "_bc_wrap_layout", False):
        def draw_header(self, context):
            if isinstance(self.layout, HeaderLayout):
                return head(self, context)
            layout = HeaderLayout(self.layout, context, root=not getattr(cls, "bl_parent_id", ""))
            return head(_Self(self, layout, cls), context)

        draw_header._bc_wrap_layout = True
        draw_header.__wrapped__ = head
        cls.draw_header = draw_header


def _panels():
    import bpy
    out, todo = [], list(bpy.types.Panel.__subclasses__())
    while todo:
        c = todo.pop()
        out.append(c)
        todo.extend(c.__subclasses__())
    return out


def install():
    """Patch every registered BoneCraft / CATS / Rig Builder viewport panel in place. Idempotent.

    In place (not re-registered): Blender looks draw up on the class at each redraw, and re-registering
    would move a panel below its siblings."""
    for cls in _panels():
        if (getattr(cls, "is_registered", False) and getattr(cls, "bl_space_type", "") == 'VIEW_3D'
                and getattr(cls, "bl_category", "") in CATEGORIES
                and cls.__module__.startswith("boneforge") and callable(getattr(cls, "draw", None))
                and not getattr(cls.draw, "_bc_wrap_layout", False)):
            _wrap(cls)
