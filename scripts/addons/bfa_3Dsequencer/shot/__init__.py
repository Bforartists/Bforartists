# SPDX-License-Identifier: GPL-3.0-or-later


from bfa_3Dsequencer.shot import (
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
