# -*- coding: utf-8 -*-
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

"""
    cursor_utils.py
    Helper methods for accessing the 3D cursor
"""


import bpy


class CursorAccess:

    @classmethod
    def findSpace(cls):
        for area in bpy.data.window_managers[0].windows[0].screen.areas:
            if area.type == 'VIEW_3D':
                break
        else:
            return None

        for space in area.spaces:
            if space.type == 'VIEW_3D':
                break
        else:
            return None

        return space

    @classmethod
    def setCursor(cls, coordinates):
        spc = cls.findSpace()
        try:
            spc.cursor_location = coordinates
        except:
            pass

    @classmethod
    def getCursor(cls):
        spc = cls.findSpace()
        return spc.cursor_location if spc else None
