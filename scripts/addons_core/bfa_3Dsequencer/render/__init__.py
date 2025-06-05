# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

# BFA - temporariliy removed

from bfa_3Dsequencer.render import (
    props,
    ops,
    ui,
)


def register():
    props.register()
    ops.register()
    ui.register()


def unregister():
    props.unregister()
    ops.unregister()
    ui.unregister()
