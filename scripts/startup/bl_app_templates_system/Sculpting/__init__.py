# SPDX-FileCopyrightText: 2018-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.app.handlers import persistent


@persistent
def load_handler(_):
    # BFA - Our startup file is saved in Sculpt Mode with its own mesh, unlike Blender's empty one.
    # In Sculpt Mode this operator adds to that mesh and pushes an undo step, and the undo stack
    # doesn't exist yet at this point, which crashed the template (#6941).
    if bpy.context.mode == 'SCULPT':
        return
    bpy.ops.mesh.primitive_quad_sphere_add(segments=64)
    bpy.ops.object.mode_set(mode='SCULPT')


def register():
    bpy.app.handlers.load_factory_startup_post.append(load_handler)


def unregister():
    bpy.app.handlers.load_factory_startup_post.remove(load_handler)
