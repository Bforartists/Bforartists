# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

from bfa_3Dsequencer.scene import (
    core,
    naming,
    ops,
    ui,
)


def register():
    core.register()
    naming.register()
    ops.register()
    ui.register()


def unregister():
    core.unregister()
    naming.unregister()
    ops.unregister()
    ui.unregister()
