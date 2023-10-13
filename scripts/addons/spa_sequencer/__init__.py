# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from spa_sequencer import (
    editorial,
    keymaps,
    preferences,
    render,
    sequence,
    shared_folders,
    shot,
    sync,
)


bl_info = {
    "name": "Sequencer",
    "author": "The SPA Studios",
    "description": "Toolset to improve the sequence workflow in Blender.",
    "blender": (3, 3, 0),
    "version": (1, 0, 0),
    "location": "",
    "warning": "",
    "category": "SPA",
}


packages = (
    sync,
    shot,
    sequence,
    render,
    editorial,
    shared_folders,
    preferences,
    keymaps,
)


def register():
    for package in packages:
        package.register()


def unregister():
    for package in packages:
        package.unregister()
