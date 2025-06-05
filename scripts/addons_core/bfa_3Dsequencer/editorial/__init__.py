# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

# BFA - temporariliy removed

from bfa_3Dsequencer.editorial import (
    ops,
    ui,
    vse_io,
)


def register():
    ops.register()
    vse_io.register()
    ui.register()


def unregister():
    ops.unregister()
    vse_io.unregister()
    ui.unregister()
