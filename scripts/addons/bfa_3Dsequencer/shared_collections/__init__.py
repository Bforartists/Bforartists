# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

from bfa_3Dsequencer.shared_collections import (
    core,
    ops,
    ui,
)


def register():
    core.register()
    ops.register()
    ui.register()


def unregister():
    core.unregister()
    ops.unregister()
    ui.unregister()
