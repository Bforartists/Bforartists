# SPDX-License-Identifier: GPL-3.0-or-later


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
