"""A UILayout wrapper for narrow regions (pure: works on any layout object).

When Rig Builder sits in a narrow Tool Shelf, its draw code receives a
``CompactLayout`` instead of the real layout: ``row`` / ``split`` /
``column_flow`` / ``grid_flow`` become columns, so side-by-side controls stack.

Labels, buttons and settings keep their full text, info lines included (show,
don't hide; owner, 2026-10-10): text too wide for the shelf wraps instead
(core.wrap_layout). Everything else is forwarded unchanged to the wrapped layout.
"""

_COLUMN_KEYS = ("align", "heading", "heading_ctxt", "translate")


def _column_kwargs(kwargs):
    return {k: v for k, v in kwargs.items() if k in _COLUMN_KEYS}


class CompactLayout:
    __slots__ = ("_layout",)

    def __init__(self, layout):
        object.__setattr__(self, "_layout", layout)

    def __getattr__(self, name):
        return getattr(self._layout, name)

    def __setattr__(self, name, value):
        setattr(self._layout, name, value)

    def _wrap(self, sub):
        return CompactLayout(sub)

    def column(self, **kwargs):
        return self._wrap(self._layout.column(**kwargs))

    def row(self, **kwargs):
        return self._wrap(self._layout.column(**_column_kwargs(kwargs)))

    def split(self, **kwargs):
        return self._wrap(self._layout.column(**_column_kwargs(kwargs)))

    def column_flow(self, **kwargs):
        return self._wrap(self._layout.column(**_column_kwargs(kwargs)))

    def grid_flow(self, **kwargs):
        return self._wrap(self._layout.column(**_column_kwargs(kwargs)))

    def box(self):
        return self._wrap(self._layout.box())
