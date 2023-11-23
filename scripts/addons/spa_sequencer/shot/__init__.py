# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from spa_sequencer.shot import (
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
