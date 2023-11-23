# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from spa_sequencer.render import (
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
