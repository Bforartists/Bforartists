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

from bl_ui.properties_paint_common import UnifiedPaintPanel
from .object_menus import *

# Select Menu's #

# Object Select #
class VIEW3D_MT_Select_Object(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()
        layout.operator("object.select_all", text="All").action = 'SELECT'
        layout.operator("object.select_all", text="None").action = 'DESELECT'
        layout.operator("object.select_all", text="Invert").action = 'INVERT'
        layout.separator()
        layout.operator("object.select_camera", text="Select Active Camera")
        layout.operator("object.select_mirror", text="Mirror Selection")
        layout.operator("object.select_random", text="Select Random")
        layout.separator()
        layout.operator_menu_enum("object.select_by_type", "type", text="Select All by Type...")
        layout.operator_menu_enum("object.select_grouped", "type", text="Select Grouped")
        layout.operator_menu_enum("object.select_linked", "type", text="Select Linked")
        layout.separator()
        layout.menu("VIEW3D_MT_Select_Object_More_Less", text="More/Less")
        layout.operator("object.select_pattern", text="Select Pattern...")


class VIEW3D_MT_Select_Object_More_Less(Menu):
    bl_label = "Select More/Less"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.select_more", text="More")
        layout.operator("object.select_less", text="Less")
        layout.separator()
        props = layout.operator("object.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'
        props = layout.operator("object.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'
        layout.separator()
        props = layout.operator("object.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'
        props = layout.operator("object.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'


# Edit Curve Select #
class VIEW3D_MT_Select_Edit_Curve(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()
        layout.operator("curve.select_all").action = 'TOGGLE'
        layout.operator("curve.select_all", text="Inverse").action = 'INVERT'
        layout.operator("curve.select_nth")
        layout.separator()
        layout.operator("curve.select_random")
        layout.operator("curve.select_linked", text="Select Linked")
        layout.operator("curve.select_similar", text="Select Similar")
        layout.operator("curve.de_select_first")
        layout.operator("curve.de_select_last")
        layout.operator("curve.select_next")
        layout.operator("curve.select_previous")
        layout.separator()
        layout.operator("curve.select_more")
        layout.operator("curve.select_less")


# Armature Select #
class VIEW3D_MT_SelectArmatureMenu(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("armature.select_all")
        layout.operator("armature.select_inverse", text="Inverse")
        layout.operator("armature.select_hierarchy",
                        text="Parent").direction = 'PARENT'
        layout.operator("armature.select_hierarchy",
                        text="Child").direction = 'CHILD'
        props = layout.operator("armature.select_hierarchy",
                                text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'
        props = layout.operator("armature.select_hierarchy",
                                text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'
        layout.operator("object.select_pattern", text="Select Pattern...")


class VIEW3D_MT_Select_Edit_Armature(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")

        layout.separator()

        layout.operator("armature.select_all").action = 'TOGGLE'
        layout.operator("armature.select_all", text="Inverse").action = 'INVERT'
        layout.operator("armature.select_mirror", text="Mirror").extend = False

        layout.separator()

        layout.operator("armature.select_more", text="More")
        layout.operator("armature.select_less", text="Less")

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'

        layout.operator_menu_enum("armature.select_similar", "type", text="Similar")
        layout.operator("object.select_pattern", text="Select Pattern...")


class VIEW3D_MT_Select_Pose(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()
        layout.operator("pose.select_all").action = 'TOGGLE'
        layout.operator("pose.select_all", text="Inverse").action = 'INVERT'
        layout.operator("pose.select_mirror", text="Flip Active")
        layout.operator("pose.select_constraint_target",
                        text="Constraint Target")
        layout.separator()
        layout.operator("pose.select_linked", text="Linked")
        layout.operator("pose.select_hierarchy",
                        text="Parent").direction = 'PARENT'
        layout.operator("pose.select_hierarchy",
                        text="Child").direction = 'CHILD'
        props = layout.operator("pose.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'
        props = layout.operator("pose.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'
        layout.operator_menu_enum("pose.select_grouped", "type",
                                  text="Grouped")
        layout.separator()
        layout.operator("object.select_pattern", text="Select Pattern...")
        layout.menu("VIEW3D_MT_select_pose_more_less")


class VIEW3D_MT_Select_Pose_More_Less(Menu):
    bl_label = "Select More/Less"

    def draw(self, context):
        layout = self.layout
        props = layout.operator("pose.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'

        props = layout.operator("pose.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'



# Surface Select #
class VIEW3D_MT_Select_Edit_Surface(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()
        layout.operator("curve.select_all").action = 'TOGGLE'
        layout.operator("curve.select_all", text="Inverse").action = 'INVERT'
        layout.operator("curve.select_random")
        layout.operator("curve.select_nth")
        layout.operator("curve.select_linked", text="Select Linked")
        layout.operator("curve.select_similar", text="Select Similar")
        layout.operator("curve.select_row")
        layout.separator()
        layout.operator("curve.select_more")
        layout.operator("curve.select_less")


# Metaball Select #
class VIEW3D_MT_SelectMetaball(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()
        layout.operator("mball.select_all").action = 'TOGGLE'
        layout.operator("mball.select_all").action = 'INVERT'
        layout.operator("mball.select_random_metaelems")


class VIEW3D_MT_Select_Edit_Metaball(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.operator("mball.select_all").action = 'TOGGLE'
        layout.operator("mball.select_all", text="Inverse").action = 'INVERT'
        layout.operator("mball.select_random_metaelems")
        layout.operator_menu_enum("mball.select_similar", "type", text="Similar")


# Particle Select #
class VIEW3D_MT_Selection_Mode_Particle(Menu):
    bl_label = "Particle Select and Display Mode"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings

        layout.prop(toolsettings.particle_edit, "select_mode", expand=True)


class VIEW3D_MT_Select_Particle(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()

        layout.operator("particle.select_all").action = 'TOGGLE'
        layout.operator("particle.select_linked")
        layout.operator("particle.select_all", text="Inverse").action = 'INVERT'

        layout.separator()
        layout.operator("particle.select_more")
        layout.operator("particle.select_less")

        layout.separator()
        layout.operator("particle.select_random")

        layout.separator()
        layout.operator("particle.select_roots", text="Roots")
        layout.operator("particle.select_tips", text="Tips")


# Lattice Edit Select #
class VIEW3D_MT_Select_Edit_Lattice(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.separator()
        layout.operator("lattice.select_mirror")
        layout.operator("lattice.select_random")
        layout.operator("lattice.select_all").action = 'TOGGLE'
        layout.operator("lattice.select_all", text="Inverse").action = 'INVERT'
        layout.separator()
        layout.operator("lattice.select_ungrouped", text="Ungrouped Verts")


# Grease Pencil Select #
class VIEW3D_MT_Select_Gpencil(Menu):
    # To Do: used in 3dview header might work if mapped to mouse
    # Not in Class List yet
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.select_box")
        layout.operator("gpencil.select_circle")

        layout.separator()

        layout.operator("gpencil.select_all", text="(De)select All").action = 'TOGGLE'
        layout.operator("gpencil.select_all", text="Inverse").action = 'INVERT'
        layout.operator("gpencil.select_linked", text="Linked")
        # layout.operator_menu_enum("gpencil.select_grouped", "type", text="Grouped")
        layout.operator("gpencil.select_grouped", text="Grouped")

        layout.separator()

        layout.operator("gpencil.select_more")
        layout.operator("gpencil.select_less")


# Text Select #
class VIEW3D_MT_Select_Edit_Text(Menu):
    # To Do: used in 3dview header might work if mapped to mouse
    # Not in Class List yet
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout
        layout.operator("font.text_copy", text="Copy")
        layout.operator("font.text_cut", text="Cut")
        layout.operator("font.text_paste", text="Paste")
        layout.operator("font.text_paste_from_file")
        layout.operator("font.select_all")


# Paint Mode Menus #
class VIEW3D_MT_Select_Paint_Mask(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.operator("paint.face_select_all").action = 'TOGGLE'
        layout.operator("paint.face_select_all", text="Inverse").action = 'INVERT'
        layout.operator("paint.face_select_linked", text="Linked")


class VIEW3D_MT_Select_Paint_Mask_Vertex(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.select_box")
        layout.operator("view3d.select_circle")
        layout.operator("paint.vert_select_all").action = 'TOGGLE'
        layout.operator("paint.vert_select_all", text="Inverse").action = 'INVERT'
        layout.operator("paint.vert_select_ungrouped", text="Ungrouped Verts")



# List The Classes #

classes = (
    VIEW3D_MT_Select_Object,
    VIEW3D_MT_Select_Object_More_Less,
    VIEW3D_MT_Select_Edit_Curve,
    VIEW3D_MT_SelectArmatureMenu,
    VIEW3D_MT_Select_Edit_Armature,
    VIEW3D_MT_Select_Pose,
    VIEW3D_MT_Select_Pose_More_Less,
    VIEW3D_MT_Select_Edit_Surface,
    VIEW3D_MT_SelectMetaball,
    VIEW3D_MT_Select_Edit_Metaball,
    VIEW3D_MT_Select_Particle,
    VIEW3D_MT_Select_Edit_Lattice,
    VIEW3D_MT_Select_Paint_Mask,
    VIEW3D_MT_Select_Paint_Mask_Vertex,
    VIEW3D_MT_Selection_Mode_Particle,
    VIEW3D_MT_Select_Gpencil,
    VIEW3D_MT_Select_Edit_Text,
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
