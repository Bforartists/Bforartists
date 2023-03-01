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

# This is the Bforartists 2 version of the script that uses the internal Bforartists icons.
#It will not work in Blender since the icons doesn't exist there.

import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
)
from bpy.types import (Operator, AddonPreferences, )
from bpy.props import BoolProperty

bl_info = {
    "name": "Align View Buttons",
    "author": "Reiner 'Tiles' Prokein",
    "version": (2, 0, 0),
    "blender": (2, 90, 0),
    "location": "Header of the 3D View",
    "description": "Adds a tab button row in the header of the 3D View to switch between views",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"}

def align_view_buttons(self, context):
    layout = self.layout
    view = context.space_data
    overlay = view.overlay

    preferences = context.preferences
    addon_prefs = preferences.addons["align_view_buttons"].preferences
    
    #View
    row = layout.row(align=True)

    if addon_prefs.align_buttons:
        row.operator("view3d.view_axis", text="", icon ="VIEW_FRONT").type = 'FRONT'
        row.operator("view3d.view_axis", text="", icon ="VIEW_BACK").type = 'BACK'
        row.operator("view3d.view_axis", text="", icon ="VIEW_RIGHT").type = 'RIGHT'
        row.operator("view3d.view_axis", text="", icon ="VIEW_LEFT").type = 'LEFT'
        row.operator("view3d.view_axis", text="", icon ="VIEW_TOP").type = 'TOP'
        row.operator("view3d.view_axis", text="", icon ="VIEW_BOTTOM").type = 'BOTTOM'
        row.separator()
        
    if addon_prefs.lock_camera_to_view:
        if context.space_data.region_3d.view_perspective == "CAMERA":
            row.prop(view, "lock_camera", icon = "LOCK_TO_CAMVIEW", icon_only=True )
            
    if addon_prefs.lock_view_rotation:
        row.prop(context.space_data.region_3d, 'lock_rotation', icon = "LOCK_ROTATION", icon_only=True )

    if addon_prefs.quad_view:
        row.operator("screen.region_quadview", text = "", icon = "QUADVIEW")

    if addon_prefs.persp_ortho:
        row.operator("view3d.view_persportho", text="", icon = "PERSP_ORTHO")

    if addon_prefs.camera_view:
        row.operator("view3d.view_camera", text="", icon = 'VIEW_SWITCHTOCAM')

    #navigation
    row.separator(factor = 0.5)

    if addon_prefs.camera_switch:
        row.operator("view3d.switchactivecamto", text="", icon ="VIEW_SWITCHACTIVECAM")

    if addon_prefs.frame_selected:
        row.operator("view3d.view_selected", text="", icon = "VIEW_SELECTED").use_all_regions = False
    if addon_prefs.frame_all:
        row.operator("view3d.view_all", text = "", icon = "VIEWALL").center = False

    if addon_prefs.reset_3dview:
        if hasattr(bpy.ops, "reset_3d_view"):
            row.operator("view3d.reset_3d_view", text="", icon ="VIEW_RESET")
            
    #overlay
    row.separator(factor = 0.5)
            
    if addon_prefs.groundgrid:  
        row.prop(overlay, "show_ortho_grid", toggle=True, icon_only = True, icon = "GROUNDGRID")
    if addon_prefs.wireframe: 
        row.prop(overlay, "show_wireframes", toggle=True, icon_only = True, icon = "NODE_WIREFRAME")
    if addon_prefs.cursor: 
        row.prop(overlay, "show_cursor", text="", toggle=True, icon_only = True, icon = "CURSOR")
    if addon_prefs.origin: 
        row.prop(overlay, "show_object_origins", text="", toggle=True, icon_only = True, icon = "ORIGIN")
    if addon_prefs.annotations: 
        row.prop(overlay, "show_annotation", text="", toggle=True, icon_only = True, icon = "GREASEPENCIL")

    row.popover(panel = "VIEW3D_PT_align_view_buttons_options", text = "")


class VIEW3D_PT_align_view_buttons_options(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Align View Buttons Options"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        preferences = context.preferences
        addon_prefs = preferences.addons["align_view_buttons"].preferences

        #view
        col = layout.column(align = True)
        col.label(text="View")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "align_buttons")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "quad_view")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "persp_ortho")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "camera_view")
        
        #navigation
        col = layout.column(align = True)
        col.label(text="Navigation")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "lock_camera_to_view")
        row = col.row()
        row.separator()        
        row.prop(addon_prefs, "lock_view_rotation")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "camera_switch")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "frame_selected")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "frame_all")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "reset_3dview")
        
        #overlay
        col = layout.column(align = True)
        col.label(text="Overlay")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "groundgrid")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "wireframe")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "cursor")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "origin")
        row = col.row()
        row.separator()
        row.prop(addon_prefs, "annotations")

        col = layout.column(align = True)
        col.label(text="Note!")
        col.label(text="Align View Buttons is an addon")
        col.label(text="It can be turned off in the Preferences")


class BFA_OT_align_view_buttons_prefs(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    # View
    align_buttons : BoolProperty(name="Align Buttons", default=True, description = "Align buttons allows you to switch to orthographic views. Front, left, top ...", )
    quad_view : BoolProperty(name="Toggle Quad View", default=False, description = "Toggle the quad view layout in the 3d view", )
    persp_ortho : BoolProperty(name="Perspective Orthographic", default=False, description = "Toggle between perspectivic and orthographic projection", )

    # Navigation
    lock_camera_to_view : BoolProperty(name="Lock Camera to View", default=False, description = "Navigate either the camera passepartout or the camera content\nJust active in camera view", )
    lock_view_rotation : BoolProperty(name="Lock View Rotation", default=False, description = "Lock the view rotations in side views", )
    camera_view : BoolProperty(name="Active Camera", default=False, description = "View through the render camera or through the viewport camera", )
    camera_switch : BoolProperty(name="Set Active Camera", default=False, description = "Set the currently selected camera as the active camera", )

    frame_selected : BoolProperty(name="Frame Selected", default=False, description = "Center the view at the selected object and zoom to fit", )
    frame_all : BoolProperty(name="Frame All", default=False, description = "Center the view at all content and zoom to fit", )

    reset_3dview : BoolProperty(name="Reset 3D View", default=False, description = "Resets the 3d view to the defaults.\rNote that this is the reset 3dview addon, so this button might not show if the addon is off!", )

    #Overlay
    groundgrid : BoolProperty(name="Groundgrid", default=False, description = "Show or hide the groundgrid", )
    wireframe : BoolProperty(name="Wireframe", default=False, description = "Show or hide the wireframe display in object mode", )
    cursor : BoolProperty(name="3D Cursor", default=False, description = "Show or hide the 3D cursor", )
    origin : BoolProperty(name="Origin", default=False, description = "Show or hide the origin", )
    annotations : BoolProperty(name="Annotations", default=False, description = "Show or hide annotations", )


classes = (
    VIEW3D_PT_align_view_buttons_options,
    BFA_OT_align_view_buttons_prefs,
    )

def register():

    from bpy.utils import register_class
    for cls in classes:
       register_class(cls)

    bpy.types.VIEW3D_HT_header.append(align_view_buttons) # Add buttons in the View 3D header.

def unregister():

    from bpy.utils import unregister_class
    for cls in classes:
       unregister_class(cls)

    bpy.types.VIEW3D_HT_header.remove(align_view_buttons)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.

if __name__ == "__main__":
    register()