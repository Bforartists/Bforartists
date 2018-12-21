### BEGIN GPL LICENSE BLOCK #####
#
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
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy, time, sys
from math import *

def ifloor(x):
    return int(x) if x >= 0.0 else int(x) - 1

def iceil(x):
    return int(x) + 1 if x >= 0.0 else int(x)

# based on http://code.activestate.com/recipes/578114-round-number-to-specified-number-of-significant-di/
def round_sigfigs(num, sig_figs):
    if num != 0:
        return round(num, -int(floor(log10(abs(num))) - (sig_figs - 1)))
    else:
        return 0  # Can't take the log of 0

class OperatorCallContext():
    def __enter__(self):
        scene = bpy.context.scene
        prefs = bpy.context.user_preferences

        # store active/selected state to restore it after operator execution
        self.curact = scene.objects.active
        self.cursel = { ob : ob.select for ob in scene.objects }

        # undo can store files a lot when running operators internally,
        # disable since we only need one undo step after main operators anyway
        self.use_global_undo = prefs.edit.use_global_undo
        prefs.edit.use_global_undo = False

        return (self.curact, self.cursel)

    def __exit__(self, exc_type, exc_value, traceback):
        scene = bpy.context.scene
        prefs = bpy.context.user_preferences

        # restore active/selected state
        scene.objects.active = self.curact
        for ob in scene.objects:
            ob.select = self.cursel.get(ob, False)

        prefs.edit.use_global_undo = self.use_global_undo

def select_single_object(ob):
    scene = bpy.context.scene

    scene.objects.active = ob
    for tob in scene.objects:
        tob.select = (tob == ob)
