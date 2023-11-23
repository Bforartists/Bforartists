# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Timeline Synchronization package.
"""

from spa_sequencer.sync import (
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
