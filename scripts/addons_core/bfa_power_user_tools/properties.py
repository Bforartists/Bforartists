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
    BFA_PROP_toggle_insertframes: bpy.props.BoolProperty(name='Frames Insert/Remove Operators', description='Adds operators to insert/remove a frame on the left or right of the timeline cursor.\nLocated in the 3D View, Timeline, Dopesheet, and Graph editors', default=True)
    BFA_PROP_toggle_jumpframes: bpy.props.BoolProperty(name='Jump Frame Operators', description='Adds operators to intervals of frames to the left or right of the timeline cursor.\nLocated in Timeline editor Header to the left', default=True)
    BFA_PROP_toggle_animationpanel: bpy.props.BoolProperty(name='Animation Toolshelf Operators', description='Adds the animation operators from the header to the toolshelf. \nLocated in the tabbed toolshelf in the 3D View under the Animation Tab > Animation Panel', default=True)
    BFA_PROP_toggle_viewport: bpy.props.BoolProperty(name='Viewport Silhuette Toggle', description='Adds the viewport overlay silhuette toggle to the header of the 3D View editors. \nLocated header customizable buttons overlays in the 3D View under the drop down to the top right', default=True)

property_classes = [
    BFA_UI_toggles,
]


def register():
    for cls in property_classes:
        bpy.utils.register_class(cls)

    # Register the toggles
    bpy.types.WindowManager.BFA_UI_addon_props = bpy.props.PointerProperty(type=BFA_UI_toggles)

def unregister():
    for cls in property_classes:
        bpy.utils.unregister_class(cls)

    # Unregister the toggles
    del bpy.types.WindowManager.BFA_UI_addon_props
