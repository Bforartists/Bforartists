# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy


# FUNCTION: Checks if cycles is available
def cycles_exists():
    return hasattr(bpy.types.Scene, "cycles")


# FUNCTION: Checks if cycles is the active renderer
def cycles_active(context):
    return context.scene.render.engine == "CYCLES"


# FUNCTION: Check if material has Emission (for select and stats)
def cycles_is_emission(context, ob):
    is_emission = False

    if not ob.material_slots:
        return is_emission

    for ma in ob.material_slots:
        if not ma.material:
            continue
        if ma.material.node_tree and ma.material.node_tree.nodes:
            for no in ma.material.node_tree.nodes:
                if not no.type in ("EMISSION", "GROUP"):
                    continue
                for ou in no.outputs:
                    if not ou.links:
                        continue
                    if no.type == "GROUP" and no.node_tree and no.node_tree.nodes:
                        for gno in no.node_tree.nodes:
                            if gno.type != "EMISSION":
                                continue
                            for gou in gno.outputs:
                                if ou.links and gou.links:
                                    is_emission = True
                    elif no.type == "EMISSION":
                        if ou.links:
                            is_emission = True
    return is_emission


# FUNCTION: Check if object has keyframes for a specific frame
def is_keyframe(ob, frame):
    if ob is None or ob and ob.animation_data is None:
        return False

    if ob.animation_data.action is None:
        return False

    from bpy_extras import anim_utils
    action = ob.animation_data.action
    for slot in action.slots:
        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)

        for fcu in channelbag.fcurves:
            if frame in (p.co.x for p in fcu.keyframe_points):
                return True
    return False


# FUNCTION: Check if Blender's major version is older than 5.
def is_blender_version_4():
    return (bpy.app.version[0] < 5)
