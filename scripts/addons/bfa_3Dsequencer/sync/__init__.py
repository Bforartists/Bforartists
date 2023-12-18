# SPDX-License-Identifier: GPL-3.0-or-later


"""
Timeline Synchronization package.
"""

from bfa_3Dsequencer.sync import (
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
