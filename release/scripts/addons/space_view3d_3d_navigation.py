# 3D NAVIGATION TOOLBAR v1.2 - 3Dview Addon - Blender 2.5x
#
# THIS SCRIPT IS LICENSED UNDER GPL,
# please read the license block.

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
# contributed to by: Demohero, uriel, jbelcik, meta-androcto

bl_info = {
    "name": "3D Navigation",
    "author": "Demohero, uriel",
    "version": (1, 2, 6),
    "blender": (2, 92, 0),
    "location": "View3D > Sidebar > View Tab",
    "description": "Navigate the Camera & 3D Viewport from the Sidebar",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/3d_view/3d_navigation.html",
    "category": "3D View",
}

import bpy
from bpy.types import (
        AddonPreferences,
        Operator,
        Panel,
        )
from bpy.props import StringProperty


# main class of this toolbar

# re-ordered (reversed) Orbit Operators
class VIEW3D_OT_OrbitUpView1(Operator):
    bl_idname = "opr.orbit_up_view1"
    bl_label = "Orbit Up View"
    bl_description = "Orbit the view towards you"

    def execute(self, context):
        bpy.ops.view3d.view_orbit(type='ORBITUP')
        return {'FINISHED'}


class VIEW3D_OT_OrbitLeftView1(Operator):
    bl_idname = "opr.orbit_left_view1"
    bl_label = "Orbit Left View"
    bl_description = "Orbit the view around to your Right"

    def execute(self, context):
        bpy.ops.view3d.view_orbit(type='ORBITLEFT')
        return {'FINISHED'}


class VIEW3D_OT_OrbitRightView1(Operator):
    bl_idname = "opr.orbit_right_view1"
    bl_label = "Orbit Right View"
    bl_description = "Orbit the view around to your Left"

    def execute(self, context):
        bpy.ops.view3d.view_orbit(type='ORBITRIGHT')
        return {'FINISHED'}


class VIEW3D_OT_OrbitDownView1(Operator):
    bl_idname = "opr.orbit_down_view1"
    bl_label = "Orbit Down View"
    bl_description = "Orbit the view away from you"

    def execute(self, context):
        bpy.ops.view3d.view_orbit(type='ORBITDOWN')
        return {'FINISHED'}


# re-ordered (reversed) Pan Operators
# just pass the enum from the VIEW3D_PT_pan_navigation1 Panel
class VIEW3D_OT_PanUpViewsAll(Operator):
    bl_idname = "opr.pan_up_views_all"
    bl_label = "Pan View"
    bl_description = "Pan the 3D View"

    panning: StringProperty(
            default="PANUP",
            options={"HIDDEN"}
            )

    def execute(self, context):
        try:
            bpy.ops.view3d.view_pan("INVOKE_REGION_WIN", type=self.panning)
        except Exception as e:
            self.report({"WARNING"},
                        "Pan Views could not be completed. Operation Cancelled")
            print("\n[3D Navigation]\nOperator: opr.pan_up_views_all\n {}\n".format(e))

            return {"CANCELLED"}

        return {'FINISHED'}


# Zoom Operators
class VIEW3D_OT_ZoomInView1(Operator):
    bl_idname = "opr.zoom_in_view1"
    bl_label = "Zoom In View"
    bl_description = "Zoom In the View/Camera View"

    def execute(self, context):
        bpy.ops.view3d.zoom(delta=1)
        return {'FINISHED'}


class VIEW3D_OT_ZoomOutView1(Operator):
    bl_idname = "opr.zoom_out_view1"
    bl_label = "Zoom Out View"
    bl_description = "Zoom out In the View/Camera View"

    def execute(self, context):
        bpy.ops.view3d.zoom(delta=-1)
        return {'FINISHED'}


# Roll Operators
class VIEW3D_OT_RollLeftView1(Operator):
    bl_idname = "opr.roll_left_view1"
    bl_label = "Roll Left View"
    bl_description = "Roll the view Left"

    def execute(self, context):
        bpy.ops.view3d.view_roll(angle=-0.261799)
        return {'FINISHED'}


class VIEW3D_OT_RollRightView1(Operator):
    bl_idname = "opr.roll_right_view1"
    bl_label = "Roll Right View"
    bl_description = "Roll the view Right"

    def execute(self, context):
        bpy.ops.view3d.view_roll(angle=0.261799)
        return {'FINISHED'}


# View Operators
class VIEW3D_OT_LeftViewpoint1(Operator):
    bl_idname = "opr.left_viewpoint1"
    bl_label = "Left Viewpoint"
    bl_description = "View from the Left"

    def execute(self, context):
        bpy.ops.view3d.view_axis(type='LEFT')
        return {'FINISHED'}


class VIEW3D_OT_RightViewpoint1(Operator):
    bl_idname = "opr.right_viewpoint1"
    bl_label = "Right Viewpoint"
    bl_description = "View from the Right"

    def execute(self, context):
        bpy.ops.view3d.view_axis(type='RIGHT')
        return {'FINISHED'}


class VIEW3D_OT_FrontViewpoint1(Operator):
    bl_idname = "opr.front_viewpoint1"
    bl_label = "Front Viewpoint"
    bl_description = "View from the Front"

    def execute(self, context):
        bpy.ops.view3d.view_axis(type='FRONT')
        return {'FINISHED'}


class VIEW3D_OT_BackViewpoint1(Operator):
    bl_idname = "opr.back_viewpoint1"
    bl_label = "Back Viewpoint"
    bl_description = "View from the Back"

    def execute(self, context):
        bpy.ops.view3d.view_axis(type='BACK')
        return {'FINISHED'}


class VIEW3D_OT_TopViewpoint1(Operator):
    bl_idname = "opr.top_viewpoint1"
    bl_label = "Top Viewpoint"
    bl_description = "View from the Top"

    def execute(self, context):
        bpy.ops.view3d.view_axis(type='TOP')
        return {'FINISHED'}


class VIEW3D_OT_BottomViewpoint1(Operator):
    bl_idname = "opr.bottom_viewpoint1"
    bl_label = "Bottom Viewpoint"
    bl_description = "View from the Bottom"

    def execute(self, context):
        bpy.ops.view3d.view_axis(type='BOTTOM')
        return {'FINISHED'}


# Panel class of this toolbar
class VIEW3D_PT_3dnavigationPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "3D Navigation"
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        # Triple buttons
        col = layout.column(align=True)
        col.operator("view3d.localview", text="View Global/Local")
        col.operator("view3d.view_persportho", text="Perspective/Orthographic")
        col.operator("view3d.view_camera", text="View Camera", icon='CAMERA_DATA')

        # group of 6 buttons
        col = layout.column(align=True)
        col.label(text="Align view from:", icon="VIEW3D")
        row = col.row()
        row.operator("view3d.view_axis", text="Front").type = 'FRONT'
        row.operator("view3d.view_axis", text="Back").type = 'BACK'
        row = col.row()
        row.operator("view3d.view_axis", text="Left").type = 'LEFT'
        row.operator("view3d.view_axis", text="Right").type = 'RIGHT'
        row = col.row()
        row.operator("view3d.view_axis", text="Top").type = 'TOP'
        row.operator("view3d.view_axis", text="Bottom").type = 'BOTTOM'

        # group of 2 buttons
        col = layout.column(align=True)
        col.label(text="Lock View to Object:", icon="LOCKED")
        col.prop(view, "lock_object", text="")
        col.operator("view3d.view_selected", text="View to Selected")

        col = layout.column(align=True)
        col.label(text="Cursor:", icon='PIVOT_CURSOR')
        row = col.row(align=True)
        row.operator("view3d.snap_cursor_to_center", text="World Origin")
        row.operator("view3d.view_center_cursor", text="View")
        col.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected")


class VIEW3D_PT_3dnavigationPanel2(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Pan Orbit Zoom Roll"
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Screen View Perspective")

        row = layout.row()
        row.label(text="Pan:")
        row = layout.row()

        row.operator("opr.pan_up_views_all", text="Up",
                    icon="TRIA_UP").panning = "PANDOWN"
        row.operator("opr.pan_up_views_all", text="Down",
                    icon="TRIA_DOWN").panning = "PANUP"

        row = layout.row()
        row.operator("opr.pan_up_views_all", text="Left",
                    icon="BACK").panning = "PANRIGHT"
        row.operator("opr.pan_up_views_all", text="Right",
                    icon="FORWARD").panning = "PANLEFT"

        row = layout.row()
        row.label(text="Orbit:")
        row = layout.row()
        row.operator("opr.orbit_down_view1", text="Up", icon="TRIA_UP")
        row.operator("opr.orbit_up_view1", text="Down", icon="TRIA_DOWN")

        row = layout.row()
        row.operator("opr.orbit_right_view1", text="Left", icon="BACK")
        row.operator("opr.orbit_left_view1", text="Right", icon="FORWARD")

        row = layout.row()
        row.label(text="Zoom:")
        row = layout.row()
        row.operator("opr.zoom_in_view1", text="In", icon='ADD')
        row.operator("opr.zoom_out_view1", text="Out", icon='REMOVE')

        row = layout.row()
        row.label(text="Roll:")
        row = layout.row()
        row.operator("opr.roll_left_view1", text="Left", icon="LOOP_BACK")
        row.operator("opr.roll_right_view1", text="Right", icon="LOOP_FORWARDS")


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        VIEW3D_PT_3dnavigationPanel,
        VIEW3D_PT_3dnavigationPanel2,
        )


def update_panel(self, context):
    message = ": Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class NavAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="View",
            update=update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")


classes = (
    VIEW3D_PT_3dnavigationPanel,
    VIEW3D_PT_3dnavigationPanel2,
    VIEW3D_OT_OrbitUpView1,
    VIEW3D_OT_OrbitLeftView1,
    VIEW3D_OT_OrbitRightView1,
    VIEW3D_OT_OrbitDownView1,
    VIEW3D_OT_ZoomInView1,
    VIEW3D_OT_ZoomOutView1,
    VIEW3D_OT_RollLeftView1,
    VIEW3D_OT_RollRightView1,
    VIEW3D_OT_LeftViewpoint1,
    VIEW3D_OT_RightViewpoint1,
    VIEW3D_OT_FrontViewpoint1,
    VIEW3D_OT_BackViewpoint1,
    VIEW3D_OT_TopViewpoint1,
    VIEW3D_OT_BottomViewpoint1,
    VIEW3D_OT_PanUpViewsAll,
    NavAddonPreferences,
    )


# Register
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    update_panel(None, bpy.context)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
