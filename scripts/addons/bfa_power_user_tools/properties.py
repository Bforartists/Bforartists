# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

class BFA_UI_toggles(bpy.types.PropertyGroup):
    BFA_PROP_toggle_insertkeyframes: bpy.props.BoolProperty(name='Insert Keyframes', description='Adds operators to insert a blank keyframe to the left or right of the timeline.\nLocated in the 3D View, Timeline, Dopesheet, and Graph editors', default=True)

