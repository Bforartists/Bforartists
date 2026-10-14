# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    import importlib

    importlib.reload(cm_init)
    importlib.reload(internals)
    importlib.reload(operator_utils)
    importlib.reload(operators)
    importlib.reload(qcd_move_widget)
    importlib.reload(qcd_operators)
    importlib.reload(ui)
    importlib.reload(qcd_init)
    importlib.reload(preferences)

else:
    from . import cm_init
    from . import internals
    from . import operator_utils
    from . import operators
    from . import qcd_move_widget
    from . import qcd_operators
    from . import ui
    from . import qcd_init
    from . import preferences

import bpy

def register():
    cm_init.register_cm()

    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.register_qcd()

def unregister():
    if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
        qcd_init.unregister_qcd()

    cm_init.unregister_cm()


if __name__ == "__main__":
    register()
