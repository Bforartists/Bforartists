# SPDX-License-Identifier: GPL-3.0-or-later


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
