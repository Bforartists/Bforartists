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
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )

from .object_menus import *


# View Menu's #

class VIEW3D_MT_View_Directions(Menu):
    bl_label = "Viewpoint"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.view_camera", text="Camera")

        layout.separator()

        layout.operator("view3d.view_axis", text="Top").type = 'TOP'
        layout.operator("view3d.view_axis", text="Bottom").type = 'BOTTOM'

        layout.separator()

        layout.operator("view3d.view_axis", text="Front").type = 'FRONT'
        layout.operator("view3d.view_axis", text="Back").type = 'BACK'

        layout.separator()

        layout.operator("view3d.view_axis", text="Right").type = 'RIGHT'
        layout.operator("view3d.view_axis", text="Left").type = 'LEFT'


class VIEW3D_MT_View_Border(Menu):
    bl_label = "View Border"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
#        layout.operator("view3d.clip_border", text="Clipping Border...")
        layout.operator("view3d.zoom_border", text="Zoom Border...")
        layout.operator("view3d.render_border", text="Render Border...")
        layout.operator("view3d.clear_render_border")


class VIEW3D_MT_View_Menu(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        layout.menu("INFO_MT_area")
        layout.separator()
        layout.operator("view3d.view_selected", text="Frame Selected").use_all_regions = False
        if view.region_quadviews:
            layout.operator("view3d.view_selected", text="Frame Selected (Quad View)").use_all_regions = True
        layout.operator("view3d.view_all", text="Frame All").center = False
        layout.operator("view3d.view_persportho", text="Perspective/Orthographic")
        layout.menu("VIEW3D_MT_View_Local")
        layout.separator()
        layout.menu("VIEW3D_MT_view_cameras", text="Cameras")
        layout.separator()
        layout.menu("VIEW3D_MT_View_Directions")
        layout.menu("VIEW3D_MT_View_Navigation")
        layout.separator()
        layout.menu("VIEW3D_MT_View_Align")
        layout.menu("VIEW3D_MT_view_align_selected")
        layout.separator()
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_view_regions", text="View Regions")
        layout.menu("VIEW3D_MT_Shade")
        layout.separator()
        layout.operator("render.opengl", icon='RENDER_STILL')
        layout.operator("render.opengl", text="Viewport Render Animation", icon='RENDER_ANIMATION').animation = True


class VIEW3D_MT_View_Navigation(Menu):
    bl_label = "Navigation"

    def draw(self, context):
        from math import pi
        layout = self.layout
        layout.operator_enum("view3d.view_orbit", "type")
        props = layout.operator("view3d.view_orbit", text ="Orbit Opposite")
        props.type = 'ORBITRIGHT'
        props.angle = pi

        layout.separator()
        layout.operator("view3d.view_roll", text="Roll Left").type = 'LEFT'
        layout.operator("view3d.view_roll", text="Roll Right").type = 'RIGHT'
        layout.separator()
        layout.operator_enum("view3d.view_pan", "type")
        layout.separator()
        layout.operator("view3d.zoom", text="Zoom In").delta = 1
        layout.operator("view3d.zoom", text="Zoom Out").delta = -1
        layout.separator()
        layout.operator("view3d.zoom_camera_1_to_1", text="Zoom Camera 1:1")
        layout.separator()
        layout.operator("view3d.fly")
        layout.operator("view3d.walk")


class VIEW3D_MT_View_Align(Menu):
    bl_label = "Align View"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.camera_to_view", text="Align Active Camera to View")
        layout.operator("view3d.camera_to_view_selected", text="Align Active Camera to Selected")
        layout.separator()
        layout.operator("view3d.view_all", text="Center Cursor and View All").center = True
        layout.operator("view3d.view_center_cursor")
        layout.separator()
        layout.operator("view3d.view_lock_to_active")
        layout.operator("view3d.view_lock_clear")


class VIEW3D_MT_View_Align_Selected(Menu):
    bl_label = "Align View to Active"

    def draw(self, context):
        layout = self.layout
        props = layout.operator("view3d.viewnumpad", text="Top")
        props.align_active = True
        props.type = 'TOP'
        props = layout.operator("view3d.viewnumpad", text="Bottom")
        props.align_active = True
        props.type = 'BOTTOM'
        props = layout.operator("view3d.viewnumpad", text="Front")
        props.align_active = True
        props.type = 'FRONT'
        props = layout.operator("view3d.viewnumpad", text="Back")
        props.align_active = True
        props.type = 'BACK'
        props = layout.operator("view3d.viewnumpad", text="Right")
        props.align_active = True
        props.type = 'RIGHT'
        props = layout.operator("view3d.viewnumpad", text="Left")
        props.align_active = True
        props.type = 'LEFT'


class VIEW3D_MT_View_Cameras(Menu):
    bl_label = "Cameras"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.object_as_camera")
        layout.operator("view3d.viewnumpad", text="Active Camera").type = 'CAMERA'

class VIEW3D_MT_View_Local(Menu):
    bl_label = "Local View"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        layout.operator("view3d.localview", text="Toggle Local View")
        layout.operator("view3d.localview_remove_from")
        layout.operator("view3d.view_persportho")


# List The Classes #

classes = (
    VIEW3D_MT_View_Directions,
    VIEW3D_MT_View_Border,
    VIEW3D_MT_View_Menu,
    VIEW3D_MT_View_Navigation,
    VIEW3D_MT_View_Align,
    VIEW3D_MT_View_Align_Selected,
    VIEW3D_MT_View_Cameras,
    VIEW3D_MT_View_Local,
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
