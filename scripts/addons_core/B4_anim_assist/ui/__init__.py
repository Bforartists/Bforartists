"""UI subpackage, class collection for registration, and Bforartists detection."""

from __future__ import annotations

#: Cached detection result. ``None`` until first queried; resolved lazily so
#: the header draw callbacks never see a stale default.
IS_BFORARTISTS: bool | None = None


def is_bforartists() -> bool:
    if IS_BFORARTISTS is None:
        init_detection()
    return bool(IS_BFORARTISTS)


def init_detection() -> None:
    """Resolve Bforartists detection using the package-level multi-signal check.

    Previously this compared ``bpy.app.version_string`` alone, which on
    Bforartists 5.x is the bare Blender base version (e.g. ``"5.2.0 Alpha"``)
    and never contains "bforartists" - and it was also never invoked, so the
    flag stayed ``False`` everywhere.  The parent package's ``_is_bforartists``
    also inspects ``bpy.app.bforartists``, ``build_branch`` (``Bfa...``) and
    ``binary_path``.
    """
    global IS_BFORARTISTS
    from .. import _is_bforartists  # parent package is fully imported by now
    IS_BFORARTISTS = _is_bforartists()


from .diagnostics_panel import AA_PT_diagnostics  # noqa: E402
from .panels import classes as _panel_classes       # noqa: E402
from .menus import classes as _menu_classes         # noqa: E402
from .p2_panels import classes as _p2_panel_classes  # noqa: E402
from .p3_panels import CLASSES as _p3_panel_classes  # noqa: E402
from .p4_panels import CLASSES as _p4_panel_classes  # noqa: E402
from .p5_panels import CLASSES as _p5_panel_classes  # noqa: E402
from .p6_panels import CLASSES as _p6_panel_classes  # noqa: E402
from .p7_panels import CLASSES as _p7_panel_classes  # noqa: E402
from .p8_panels import CLASSES as _p8_panel_classes  # noqa: E402
from .p9_panels import CLASSES as _p9_panel_classes  # noqa: E402
from .p10_panels import CLASSES as _p10_panel_classes  # noqa: E402
from .p10_pie_menus import CLASSES as _p10_pie_menu_classes  # noqa: E402
from .p11_panels import CLASSES as _p11_panel_classes  # noqa: E402
# --- LIPSYNC LAYER PANELS (Phase 12) ---
from .p12_panels import CLASSES as _p12_panel_classes  # noqa: E402
from . import headers                               # noqa: E402
from . import header_toolbars                       # noqa: E402
from .help_browser import classes as _help_browser_classes  # noqa: E402
from ..core import ui_state as _ui_state_mod        # noqa: E402
from . import ui_helpers as ui_helpers              # noqa: E402, F401
from . import panel_anatomy as panel_anatomy        # noqa: E402, F401
from . import editor_placement as editor_placement  # noqa: E402, F401
from . import scope_ui as scope_ui                  # noqa: E402, F401
from . import layout_homes                          # noqa: E402
from . import header_menus                         # noqa: E402


from .nla_panels import CLASSES as _nla_classes
from .driver_panels import CLASSES as _driver_classes, CURVE_MENUS as _driver_menus

CLASSES: tuple[type, ...] = layout_homes.arrange((
    *_driver_classes,
    *_driver_menus,
    *_nla_classes,
    *_ui_state_mod.CLASSES,
    AA_PT_diagnostics,
    *_panel_classes,
    *_menu_classes,
    *_p2_panel_classes,
    *_p3_panel_classes,
    *_p4_panel_classes,
    *_p5_panel_classes,
    *_p6_panel_classes,
    *_p7_panel_classes,
    *_p8_panel_classes,
    *_p9_panel_classes,
    *_p10_panel_classes,
    *_p10_pie_menu_classes,
    *_p11_panel_classes,
    # --- LIPSYNC LAYER PANELS (Phase 12) ---
    *_p12_panel_classes,
    *_help_browser_classes,
    *header_menus.CLASSES,
))
