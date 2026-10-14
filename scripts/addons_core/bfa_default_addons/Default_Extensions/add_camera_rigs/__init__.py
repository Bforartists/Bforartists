# SPDX-FileCopyrightText: 2019 Wayne Dixon
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import build_rigs
from . import operators
from . import ui_panels
from . import prefs
from . import composition_guides_menu

# =========================================================================
# Registration:
# =========================================================================

def register():
    build_rigs.register()
    operators.register()
    ui_panels.register()
    prefs.register()
    composition_guides_menu.register()


def unregister():
    build_rigs.unregister()
    operators.unregister()
    ui_panels.unregister()
    prefs.unregister()
    composition_guides_menu.unregister()


if __name__ == "__main__":
    register()
