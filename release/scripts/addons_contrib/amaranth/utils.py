#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

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
    if ob is not None and ob.animation_data is not None and ob.animation_data.action is not None:
        for fcu in ob.animation_data.action.fcurves:
            if frame in (p.co.x for p in fcu.keyframe_points):
                return True
    return False
