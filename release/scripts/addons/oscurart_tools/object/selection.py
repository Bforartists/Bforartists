# ##### BEGIN GPL LICENSE BLOCK #####
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

import bpy



# ------------------------------------ SELECTION -------------------------
bpy.selection_osc = []


def select_osc():
    if bpy.context.mode == "OBJECT":
        obj = bpy.context.object
        sel = len(bpy.context.selected_objects)

        if sel == 0:
            bpy.selection_osc = []
        else:
            if sel == 1:
                bpy.selection_osc = []
                bpy.selection_osc.append(obj)
            elif sel > len(bpy.selection_osc):
                for sobj in bpy.context.selected_objects:
                    if (sobj in bpy.selection_osc) is False:
                        bpy.selection_osc.append(sobj)

            elif sel < len(bpy.selection_osc):
                for it in bpy.selection_osc:
                    if (it in bpy.context.selected_objects) is False:
                        bpy.selection_osc.remove(it)


class OscSelection(bpy.types.Header):
    bl_label = "Selection Osc"
    bl_space_type = "VIEW_3D"

    def __init__(self):
        select_osc()

    def draw(self, context):
        """
        layout = self.layout
        row = layout.row()
        row.label("Sels: "+str(len(bpy.selection_osc)))
        """
 

