# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

from bfa_3Dsequencer.sequence import (
    overlay,
    props,
    ops,
    ui,
)


def register():
    props.register()
    ops.register()
    overlay.register()
    ui.register()


def unregister():
    props.unregister()
    ops.unregister()
    overlay.unregister()
    ui.unregister()
