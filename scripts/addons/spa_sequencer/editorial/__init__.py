# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from spa_sequencer.editorial import (
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
