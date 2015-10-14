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
# some parts based on 3d_cursor_menu.py by Jonathan Smith (JayDez) & work by sim88 & sam. 
# view3d_advanced_dynamic_toolshelf_menu byBrendon Murphy (meta-androcto)

bl_info = {
    "name": "Dynamic Toolshelf Menu",
    "author": "meta-androcto",
    "version": (3, 0, 0),
    "blender": (2, 7, 1),
    "location": "View3D > Spacebar Key, Dynamic Tab",
    "description": "Context Sensitive Toolshelf Menu",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/Dynamic_Spacebar_Menu",
    "category": "3D View",
}

import bpy
from bpy import *

class View3DPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

class VIEW3D_PT_add_menu(View3DPanel,bpy.types.Panel):
    bl_label = "Dynamic Toolshelf"
    bl_category = "Dynamic"

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context
        if ob.mode == 'OBJECT':
            # Object mode

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Add Menu block
            layout.menu("VIEW3D_MT_AddMenu", icon='OBJECT_DATAMODE')

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor Block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Parent block
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')

            # Group block
            layout.menu("VIEW3D_MT_GroupMenu", icon='GROUP')

            # Modifier block
            layout.operator_menu_enum("object.modifier_add", "type",
                                      icon='MODIFIER')

            # Align block
            layout.menu("VIEW3D_MT_AlignMenu", icon='ALIGN')

            # Select block
            layout.menu("VIEW3D_MT_SelectMenu", icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", text= 'hide toolshelf', icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            #TODO: Add if statement to test whether editmode switch needs to
            #be added to the menu, since certain object can't enter edit mode
            #In which case we don't need the toggle
            # Toggle Editmode
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='EDITMODE_HLT')

            # Delete block
            layout.operator("object.delete", text="Delete Object",
                            icon='CANCEL')


        elif ob.mode == 'EDIT_MESH':
            # Edit mode

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Add block
            layout.menu("INFO_MT_mesh_add", text="Add Mesh",
                        icon='OUTLINER_OB_MESH')

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_EditCursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")

            # Edit block
            layout.menu("VIEW3D_MT_edit_TK", icon='EDITMODE_HLT')

            # Multi Select
            layout.menu("VIEW3D_MT_edit_multi", icon='VERTEXSEL')

            # Extrude block
            layout.menu("VIEW3D_MT_edit_mesh_extrude", icon='EDIT_VEC')

            # Tools block
            layout.menu("VIEW3D_MT_edit_mesh_specials", icon='MODIFIER')

			# UV Map block
            layout.menu("VIEW3D_MT_uv_map", icon='MOD_UVPROJECT')

            # Select block
            layout.menu("VIEW3D_MT_SelectEditMenu",
                        icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Object Mode
            layout.operator("object.editmode_toggle",
                            text="Enter Object Mode", icon='OBJECT_DATAMODE')

            # Delete Block
            layout.operator("mesh.delete", icon='CANCEL')

        if ob.mode == 'EDIT_CURVE':
            # Curve menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Add block
            layout.menu("INFO_MT_curve_add", text="Add Curve",
                        icon='OUTLINER_OB_CURVE')

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")

            # Edit Control Points
            layout.menu("VIEW3D_MT_EditCurveCtrlpoints",
                        icon='CURVE_BEZCURVE')

            # Edit Curve Specials
            layout.menu("VIEW3D_MT_EditCurveSpecials",
                        icon='MODIFIER')

            # Select Curve Block
            #Could use: VIEW3D_MT_select_edit_curve
            #Which is the default, instead of a hand written one, left it alone
            #for now though.
            layout.menu("VIEW3D_MT_SelectCurveMenu",
                        icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')

            # Delete block
            layout.operator("curve.delete", text="Delete Object",
                            icon='CANCEL')

        if ob.mode == 'EDIT_SURFACE':
            # Surface menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Add block
            layout.menu("INFO_MT_surface_add", text="Add Surface",
                        icon='OUTLINER_OB_SURFACE')

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")

            # Edit Curve Specials
            layout.menu("VIEW3D_MT_EditCurveSpecials",
                        icon='MODIFIER')

            # Select Surface
            layout.menu("VIEW3D_MT_SelectSurface", icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')


            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')

            # Delete block
            layout.operator("curve.delete", text="Delete Object",
                            icon='CANCEL')

        if ob.mode == 'EDIT_METABALL':
            # Metaball menu

            #Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Add block
            #layout.menu("INFO_MT_metaball_add", text="Add Metaball",
            #            icon='OUTLINER_OB_META')
            layout.operator_menu_enum("object.metaball_add", "type",
                                      text="Add Metaball",
                                      icon='OUTLINER_OB_META')

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")

            #Select Metaball
            layout.menu("VIEW3D_MT_SelectMetaball", icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')

            # Delete block
            layout.operator("mball.delete_metaelems", text="Delete Object",
                            icon='CANCEL')

        elif ob.mode == 'EDIT_LATTICE':
            # Lattice menu

            #Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon= "PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon= "SMOOTHCURVE")
            layout.operator("lattice.make_regular")

            #Select Lattice
            layout.menu("VIEW3D_MT_select_edit_lattice",
                        icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')

            # Delete block - Can't delete any lattice stuff so not needed
            #layout.operator("object.delete", text="Delete Object",
            #                icon='CANCEL')

        if  context.mode == 'PARTICLE':
            # Particle menu

            #Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon= "PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon= "SMOOTHCURVE")

            # Particle block
            layout.menu("VIEW3D_MT_particle", icon='PARTICLEMODE')

            #Select Particle
            layout.menu("VIEW3D_MT_select_particle",
                        icon='RESTRICT_SELECT_OFF')

            # History/Cursor Block
            layout.menu("VIEW3D_MT_undoS", icon='ARROW_LEFTRIGHT')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.mode_set", text="Enter Object Mode",
                            icon='OBJECT_DATA')

            # Delete block
            layout.operator("object.delete", text="Delete Object",
                            icon='CANCEL')

        ob = context
        if ob.mode == 'PAINT_WEIGHT':
            # Weight paint menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Weight Paint block
            layout.menu("VIEW3D_MT_paint_weight", icon='WPAINT_HLT')

            # History/Cursor Block
            layout.menu("VIEW3D_MT_undoS", icon='ARROW_LEFTRIGHT')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.mode_set", text="Enter Object Mode",
                            icon='OBJECT_DATA')

        elif ob.mode == 'PAINT_VERTEX':
            # Vertex paint menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Vertex Paint block
            layout.operator("paint.vertex_color_set", icon='VPAINT_HLT')

            # History/Cursor Block
            layout.menu("VIEW3D_MT_undoS", icon='ARROW_LEFTRIGHT')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.mode_set", text="Enter Object Mode",
                            icon='OBJECT_DATA')

        elif ob.mode == 'PAINT_TEXTURE':
            # Texture paint menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # History/Cursor Block
            layout.menu("VIEW3D_MT_undoS", icon='ARROW_LEFTRIGHT')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.mode_set", text="Enter Object Mode",
                            icon='OBJECT_DATA')

        elif ob.mode == 'SCULPT':
            # Sculpt menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Sculpt block
            layout.menu("VIEW3D_MT_sculpt", icon='SCULPTMODE_HLT')

            # History/Cursor Block
            layout.menu("VIEW3D_MT_undoS", icon='ARROW_LEFTRIGHT')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Objectmode
            layout.operator("object.mode_set", text="Enter Object Mode",
                            icon='OBJECT_DATA')

        elif ob.mode == 'EDIT_ARMATURE':
            # Armature Edit menu

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform block
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Mirror block
            layout.menu("VIEW3D_MT_MirrorMenu", icon='MOD_MIRROR')

            # Cursor block
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Proportional block
            layout.prop_menu_enum(settings, "proportional_edit",
                                  icon="PROP_CON")
            layout.prop_menu_enum(settings, "proportional_edit_falloff",
                                  icon="SMOOTHCURVE")
            layout.separator()

            # Edit Armature roll
            layout.menu("VIEW3D_MT_edit_armature_roll",
                        icon='BONE_DATA')

            # Edit Armature Toolkit
            layout.menu("VIEW3D_MT_EditArmatureTK",
                        icon='ARMATURE_DATA')

            # Edit Armature Name
            layout.menu("VIEW3D_MT_ArmatureName",
                        icon='NEW')

            # Parent block
            layout.menu("VIEW3D_MT_ParentMenu", icon='ROTACTIVE')

            # bone options block
            layout.menu("VIEW3D_MT_bone_options_toggle",
                        text="Bone Settings")

            # Edit Armature Specials
            layout.menu("VIEW3D_MT_armature_specials", icon='MODIFIER')

            # Edit Armature Select
            layout.menu("VIEW3D_MT_SelectArmatureMenu",
                        icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Posemode
            layout.operator("object.posemode_toggle", text="Enter Pose Mode",
                            icon='POSE_HLT')

            # Toggle Posemode
            layout.operator("object.editmode_toggle", text="Enter Object Mode",
                            icon='OBJECT_DATA')

            # Delete block
            layout.operator("armature.delete", text="Delete Object",
                            icon='CANCEL')

        if context.mode == 'POSE':
            # Pose mode menu
            arm = context.active_object.data

            # Search Menu
            layout.operator("wm.search_menu", text="Search", icon='VIEWZOOM')
            layout.separator()

            # Transform Menu
            layout.menu("VIEW3D_MT_TransformMenu", icon='MANIPUL')

            # Clear Transform
            layout.menu("VIEW3D_MT_pose_transform")

            # Cursor Menu
            layout.menu("VIEW3D_MT_CursorMenu", icon='CURSOR')

            # Pose Copy Block
            layout.menu("VIEW3D_MT_PoseCopy", icon='FILE')

            if arm.draw_type in {'BBONE', 'ENVELOPE'}:
                layout.operator("transform.transform",
                                text="Scale Envelope Distance").mode = 'BONE_SIZE'

            layout.menu("VIEW3D_MT_pose_apply")
            layout.operator("pose.relax")
            layout.menu("VIEW3D_MT_KeyframeMenu")
            layout.menu("VIEW3D_MT_pose_pose")
            layout.menu("VIEW3D_MT_pose_motion")
            layout.menu("VIEW3D_MT_pose_group")
            layout.menu("VIEW3D_MT_pose_ik")
            layout.menu("VIEW3D_MT_PoseNames")
            layout.menu("VIEW3D_MT_pose_constraints")
            layout.operator("pose.quaternions_flip")

            layout.operator_context = 'INVOKE_AREA'
            layout.operator("armature.armature_layers",
                            text="Change Armature Layers...")
            layout.operator("pose.bone_layers", text="Change Bone Layers...")

            layout.menu("VIEW3D_MT_pose_showhide")
            layout.menu("VIEW3D_MT_bone_options_toggle",
                        text="Bone Settings")

            # Select Pose Block
            layout.menu("VIEW3D_MT_SelectPoseMenu", icon='RESTRICT_SELECT_OFF')

            # Toolshelf block
            layout.operator("view3d.toolshelf", icon='MENU_PANEL')

            # Properties block
            layout.operator("view3d.properties", icon='MENU_PANEL')

            # Toggle Editmode
            layout.operator("object.editmode_toggle", text="Enter Edit Mode",
                            icon='EDITMODE_HLT')

            layout.operator("object.mode_set", text="Enter Object Mode",
                            icon='OBJECT_DATA').mode='OBJECT'

class VIEW3D_MT_AddMenu(bpy.types.Menu):
    bl_label = "Add Object Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("INFO_MT_mesh_add", text="Add Mesh",
                    icon='OUTLINER_OB_MESH')
        layout.menu("INFO_MT_curve_add", text="Add Curve",
                    icon='OUTLINER_OB_CURVE')
        layout.menu("INFO_MT_surface_add", text="Add Surface",
                    icon='OUTLINER_OB_SURFACE')
        layout.operator_menu_enum("object.metaball_add", "type",
                                  icon='OUTLINER_OB_META')
        layout.operator("object.text_add", text="Add Text",
                        icon='OUTLINER_OB_FONT')
        layout.separator()
        layout.menu("INFO_MT_armature_add", text="Add Armature",
                    icon='OUTLINER_OB_ARMATURE')
        layout.operator("object.add", text="Lattice",
                        icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.separator()
        layout.operator("object.add", text="Add Empty",
                        icon='OUTLINER_OB_EMPTY')
        layout.separator()
        layout.operator("object.speaker_add", text="Speaker", icon='OUTLINER_OB_SPEAKER')
        layout.separator()
        layout.operator("object.camera_add", text="Camera",
                        icon='OUTLINER_OB_CAMERA')
        layout.operator_menu_enum("object.lamp_add", "type",
                                  icon="OUTLINER_OB_LAMP")
        layout.separator()

        layout.operator_menu_enum("object.effector_add", "type",
                                  text="Force Field",
                                  icon='OUTLINER_OB_EMPTY')
        layout.operator_menu_enum("object.group_instance_add", "group",
                                  text="Group Instance",
                                  icon='OUTLINER_OB_EMPTY')


class VIEW3D_MT_TransformMenu(bpy.types.Menu):
    bl_label = "Transform Menu"

    # TODO: get rid of the custom text strings?
    def draw(self, context):
        layout = self.layout

        layout.operator("transform.translate", text="Grab/Move")
        # TODO: sub-menu for grab per axis
        layout.operator("transform.rotate", text="Rotate")
        # TODO: sub-menu for rot per axis
        layout.operator("transform.resize", text="Scale")
        # TODO: sub-menu for scale per axis
        layout.separator()

        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")
        layout.operator("transform.push_pull", text="Push/Pull")
        if context.edit_object and context.edit_object.type == 'ARMATURE':
            layout.operator("armature.align")
        else:
            layout.operator_context = 'EXEC_REGION_WIN'
            # @todo vvv See alignmenu() in edit.c of b2.4x to get this working.
            layout.operator("transform.transform",
                            text="Align to Transform Orientation").mode = 'ALIGN'
        layout.separator()

        layout.operator_context = 'EXEC_AREA'

        layout.operator("object.origin_set",
                        text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'
        layout.operator("object.origin_set",
                        text="Origin to Geometry").type = 'ORIGIN_GEOMETRY'
        layout.operator("object.origin_set",
                        text="Origin to 3D Cursor").type = 'ORIGIN_CURSOR'


class VIEW3D_MT_MirrorMenu(bpy.types.Menu):
    bl_label = "Mirror Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.mirror", text="Interactive Mirror")
        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'

        props = layout.operator("transform.mirror", text="X Global")
        props.constraint_axis = (True, False, False)
        props.constraint_orientation = 'GLOBAL'

        props = layout.operator("transform.mirror", text="Y Global")
        props.constraint_axis = (False, True, False)
        props.constraint_orientation = 'GLOBAL'

        props = layout.operator("transform.mirror", text="Z Global")
        props.constraint_axis = (False, False, True)
        props.constraint_orientation = 'GLOBAL'

        if context.edit_object:

            layout.separator()

            props = layout.operator("transform.mirror", text="X Local")
            props.constraint_axis = (True, False, False)
            props.constraint_orientation = 'LOCAL'
            props = layout.operator("transform.mirror", text="Y Local")
            props.constraint_axis = (False, True, False)
            props.constraint_orientation = 'LOCAL'
            props = layout.operator("transform.mirror", text="Z Local")
            props.constraint_axis = (False, False, True)
            props.constraint_orientation = 'LOCAL'

            layout.operator("object.vertex_group_mirror")

class VIEW3D_MT_ParentMenu(bpy.types.Menu):
    bl_label = "Parent Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.parent_set", text="Set")
        layout.operator("object.parent_clear", text="Clear")

class VIEW3D_MT_GroupMenu(bpy.types.Menu):
    bl_label = "Group Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("group.create")
        layout.operator("group.objects_remove")
        layout.separator()

        layout.operator("group.objects_add_active")
        layout.operator("group.objects_remove_active")

class VIEW3D_MT_AlignMenu(bpy.types.Menu):
    bl_label = "Align Menu"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_view_align_selected")
        layout.separator()

        layout.operator("view3d.view_all",
                        text="Center Cursor and View All").center = True
        layout.operator("view3d.camera_to_view",
                        text="Align Active Camera to View")
        layout.operator("view3d.view_selected")
        layout.operator("view3d.view_center_cursor")

class VIEW3D_MT_SelectMenu(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.separator()

        layout.operator("object.select_all").action = 'TOGGLE'
        layout.operator("object.select_all", text="Inverse").action = 'INVERT'
        layout.operator("object.select_random", text="Random")
        layout.operator("object.select_mirror", text="Mirror")
        layout.operator("object.select_by_layer", text="Select All by Layer")
        layout.operator_menu_enum("object.select_by_type", "type",
                                  text="Select All by Type...")
        layout.operator("object.select_camera", text="Select Camera")
        layout.separator()

        layout.operator_menu_enum("object.select_grouped", "type",
                                  text="Grouped")
        layout.operator_menu_enum("object.select_linked", "type",
                                  text="Linked")
        layout.operator("object.select_pattern", text="Select Pattern...")

class VIEW3D_MT_SelectEditMenu(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.separator()

        layout.operator("mesh.select_all").action = 'TOGGLE'
        layout.operator("mesh.select_all", text="Inverse").action = 'INVERT'
        layout.separator()

        layout.operator("mesh.select_random", text="Random")
        layout.operator("mesh.select_nth", text="Every N Number of Verts")
        layout.operator("mesh.edges_select_sharp", text="Sharp Edges")
        layout.operator("mesh.faces_select_linked_flat",
                        text="Linked Flat Faces")
        layout.operator("mesh.select_interior_faces", text="Interior Faces")
        layout.operator("mesh.select_axis", text="Side of Active")
        layout.separator()

        layout.operator("mesh.select_face_by_sides", text="By Number of Verts")
        if context.scene.tool_settings.mesh_select_mode[2] == False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold")
        layout.operator("mesh.select_loose", text="Loose Geometry")
        layout.operator("mesh.select_similar", text="Similar")

        layout.separator()

        layout.operator("mesh.select_less", text="Less")
        layout.operator("mesh.select_more", text="More")
        layout.separator()

        layout.operator("mesh.select_mirror", text="Mirror")

        layout.operator("mesh.select_linked", text="Linked")
        layout.operator("mesh.shortest_path_select", text="Shortest Path")
        layout.operator("mesh.loop_multi_select", text="Edge Loop")
        layout.operator("mesh.loop_multi_select", text="Edge Ring").ring = True
        layout.separator()

        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")

class VIEW3D_MT_SelectCurveMenu(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")
        layout.separator()

        layout.operator("curve.select_all").action = 'TOGGLE'
        layout.operator("curve.select_all").action = 'INVERT'
        layout.operator("curve.select_random")
        layout.operator("curve.select_nth")
        layout.separator()

        layout.operator("curve.de_select_first")
        layout.operator("curve.de_select_last")
        layout.operator("curve.select_next")
        layout.operator("curve.select_previous")
        layout.separator()

        layout.operator("curve.select_more")
        layout.operator("curve.select_less")

class VIEW3D_MT_SelectArmatureMenu(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.separator()

        layout.operator("armature.select_all")
        layout.operator("armature.select_inverse", text="Inverse")
        layout.separator()

        layout.operator("armature.select_hierarchy",
                        text="Parent").direction = 'PARENT'
        layout.operator("armature.select_hierarchy",
                        text="Child").direction = 'CHILD'
        layout.separator()

        props = layout.operator("armature.select_hierarchy",
                                text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy",
                                text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'

        layout.operator("object.select_pattern", text="Select Pattern...")


class VIEW3D_MT_SelectPoseMenu(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.separator()

        layout.operator("pose.select_all").action = 'TOGGLE'
        layout.operator("pose.select_all", text="Inverse").action = 'INVERT'
        layout.operator("pose.select_constraint_target",
                        text="Constraint Target")
        layout.operator("pose.select_linked", text="Linked")
        layout.separator()

        layout.operator("pose.select_hierarchy",
                        text="Parent").direction = 'PARENT'
        layout.operator("pose.select_hierarchy",
                        text="Child").direction = 'CHILD'
        layout.separator()

        props = layout.operator("pose.select_hierarchy", text="Extend Parent")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Extend Child")
        props.extend = True
        props.direction = 'CHILD'
        layout.separator()

        layout.operator_menu_enum("pose.select_grouped", "type",
                                  text="Grouped")
        layout.operator("object.select_pattern", text="Select Pattern...")

class VIEW3D_MT_PoseCopy(bpy.types.Menu):
    bl_label = "Pose Copy"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.copy")
        layout.operator("pose.paste")
        layout.operator("pose.paste",
                        text="Paste X-Flipped Pose").flipped = True
        layout.separator()

class VIEW3D_MT_PoseNames(bpy.types.Menu):
    bl_label = "Pose Copy"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.autoside_names",
                        text="AutoName Left/Right").axis = 'XAXIS'
        layout.operator("pose.autoside_names",
                        text="AutoName Front/Back").axis = 'YAXIS'
        layout.operator("pose.autoside_names",
                        text="AutoName Top/Bottom").axis = 'ZAXIS'

        layout.operator("pose.flip_names")


class VIEW3D_MT_SelectSurface(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")
        layout.operator("view3d.select_circle")

        layout.separator()

        layout.operator("curve.select_all").action = 'TOGGLE'
        layout.operator("curve.select_all").action = 'INVERT'
        layout.operator("curve.select_random")
        layout.operator("curve.select_nth")

        layout.separator()

        layout.operator("curve.select_row")

        layout.separator()

        layout.operator("curve.select_more")
        layout.operator("curve.select_less")

class VIEW3D_MT_SelectMetaball(bpy.types.Menu):
    bl_label = "Select Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.select_border")

        layout.separator()

        layout.operator("mball.select_all").action = 'TOGGLE'
        layout.operator("mball.select_all").action = 'INVERT'
        layout.operator("mball.select_random_metaelems")

class VIEW3D_MT_edit_TK(bpy.types.Menu):
    bl_label = "Edit Mesh Tools"

    def draw(self, context):
        layout = self.layout
        layout.row()  # XXX, is this needed?

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("VIEW3D_MT_edit_mesh_vertices", icon='VERTEXSEL')
        layout.menu("VIEW3D_MT_edit_mesh_edges", icon='EDGESEL')
        layout.menu("VIEW3D_MT_edit_mesh_faces", icon='FACESEL')
        layout.separator()
        layout.menu("VIEW3D_MT_edit_mesh_normals", icon='META_DATA')
        layout.operator("mesh.loopcut_slide",
                        text="Loopcut", icon='EDIT_VEC')



class VIEW3D_MT_edit_multi(bpy.types.Menu):
    bl_label = "Multi Select"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.separator()
        prop = layout.operator("wm.context_set_value", text="Vertex Select",
                               icon='VERTEXSEL')
        prop.value = "(True, False, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Edge Select",
                               icon='EDGESEL')
        prop.value = "(False, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Face Select",
                               icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge Select",
                               icon='EDITMODE_HLT')
        prop.value = "(True, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Face Select",
                               icon='ORTHO')
        prop.value = "(True, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
                               text="Edge & Face Select",
                               icon='SNAP_FACE')
        prop.value = "(False, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

        prop = layout.operator("wm.context_set_value",
                               text="Vertex & Edge & Face Select",
                               icon='SNAP_VOLUME')
        prop.value = "(True, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

class VIEW3D_MT_editM_Edge(bpy.types.Menu):
    bl_label = "Edges"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.mark_seam")
        layout.operator("mesh.mark_seam", text="Clear Seam").clear = True
        layout.separator()

        layout.operator("mesh.mark_sharp")
        layout.operator("mesh.mark_sharp", text="Clear Sharp").clear = True
        layout.operator("mesh.extrude_move_along_normals", text="Extrude")
        layout.separator()

        layout.operator("mesh.edge_rotate",
                        text="Rotate Edge CW").direction = 'CW'
        layout.operator("mesh.edge_rotate",
                        text="Rotate Edge CCW").direction = 'CCW'
        layout.separator()

        layout.operator("TFM_OT_edge_slide", text="Edge Slide")
        layout.operator("mesh.loop_multi_select", text="Edge Loop")
        layout.operator("mesh.loop_multi_select", text="Edge Ring").ring = True
        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")


class VIEW3D_MT_EditCurveCtrlpoints(bpy.types.Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type == 'CURVE':
            layout.operator("transform.transform").mode = 'TILT'
            layout.operator("curve.tilt_clear")
            layout.operator("curve.separate")

            layout.separator()

            layout.operator_menu_enum("curve.handle_type_set", "type")

            layout.separator()

            layout.menu("VIEW3D_MT_hook")


class VIEW3D_MT_EditCurveSegments(bpy.types.Menu):
    bl_label = "Curve Segments"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction")

class VIEW3D_MT_EditCurveSpecials(bpy.types.Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction")
        layout.operator("curve.spline_weight_set")
        layout.operator("curve.radius_set")
        layout.operator("curve.smooth")
        layout.operator("curve.smooth_weight")
        layout.operator("curve.smooth_radius")
        layout.operator("curve.smooth_tilt")

class VIEW3D_MT_EditArmatureTK(bpy.types.Menu):
    bl_label = "Armature Tools"

    def draw(self, context):
        layout = self.layout

        # Edit Armature

        layout.operator("transform.transform",
                        text="Scale Envelope Distance").mode = 'BONE_SIZE'

        layout.operator("transform.transform",
                        text="Scale B-Bone Width").mode = 'BONE_SIZE'
        layout.separator()

        layout.operator("armature.extrude_move")

        layout.operator("armature.extrude_forked")

        layout.operator("armature.duplicate_move")
        layout.operator("armature.merge")
        layout.operator("armature.fill")
        layout.operator("armature.delete")
        layout.operator("armature.separate")

        layout.separator()

        layout.operator("armature.subdivide", text="Subdivide")
        layout.operator("armature.switch_direction", text="Switch Direction")

class VIEW3D_MT_ArmatureName(bpy.types.Menu):
    bl_label = "Armature Name"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_AREA'
        layout.operator("armature.autoside_names",
                        text="AutoName Left/Right").type = 'XAXIS'
        layout.operator("armature.autoside_names",
                        text="AutoName Front/Back").type = 'YAXIS'
        layout.operator("armature.autoside_names",
                        text="AutoName Top/Bottom").type = 'ZAXIS'
        layout.operator("armature.flip_names")
        layout.separator()

class VIEW3D_MT_KeyframeMenu(bpy.types.Menu):
    bl_label = "Keyframe Menu"

    def draw(self, context):
        layout = self.layout

        # Keyframe Bleck
        layout.operator("anim.keyframe_insert_menu",
                        text="Insert Keyframe...")
        layout.operator("anim.keyframe_delete_v3d",
                        text="Delete Keyframe...")
        layout.operator("anim.keying_set_active_set",
                        text="Change Keying Set...")
        layout.separator()

# Classes for VIEW3D_MT_CursorMenu()
class VIEW3D_OT_pivot_cursor(bpy.types.Operator):
    "Cursor as Pivot Point"
    bl_idname = "view3d.pivot_cursor"
    bl_label = "Cursor as Pivot Point"

    @classmethod
    def poll(cls, context):
        return bpy.context.space_data.pivot_point != 'CURSOR'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'CURSOR'
        return {'FINISHED'}

class VIEW3D_OT_revert_pivot(bpy.types.Operator):
    "Revert Pivot Point"
    bl_idname = "view3d.revert_pivot"
    bl_label = "Reverts Pivot Point to median"

    @classmethod
    def poll(cls, context):
        return bpy.context.space_data.pivot_point != 'MEDIAN_POINT'

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        # @todo Change this to 'BOUDNING_BOX_CENTER' if needed...
        return{'FINISHED'}

class VIEW3D_MT_CursorMenu(bpy.types.Menu):
    bl_label = "Snap Cursor Menu"

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.separator()
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor")
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.separator()
        layout.operator("view3d.pivot_cursor",
                        text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot",
                        text="Revert Pivot Point")

class VIEW3D_MT_EditCursorMenu(bpy.types.Menu):
    bl_label = "Snap Cursor Menu"

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.separator()
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor")
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.separator()
        layout.operator("view3d.pivot_cursor",
                        text="Set Cursor as Pivot Point")
        layout.operator("view3d.revert_pivot",
                        text="Revert Pivot Point")
        layout.operator("view3d.snap_cursor_to_edge_intersection",
                        text="Cursor to Edge Intersection")
        layout.operator("transform.snap_type", text="Snap Tools",
                        icon='SNAP_ON')

def abs(val):
    if val > 0:
        return val
    return -val

def edgeIntersect(context, operator):
    from mathutils.geometry import intersect_line_line

    obj = context.active_object

    if (obj.type != "MESH"):
        operator.report({'ERROR'}, "Object must be a mesh")
        return None

    edges = []
    mesh = obj.data
    verts = mesh.vertices

    is_editmode = (obj.mode == 'EDIT')
    if is_editmode:
        bpy.ops.object.mode_set(mode='OBJECT')

    for e in mesh.edges:
        if e.select:
            edges.append(e)

            if len(edges) > 2:
                break

    if is_editmode:
        bpy.ops.object.mode_set(mode='EDIT')

    if len(edges) != 2:
        operator.report({'ERROR'},
                        "Operator requires exactly 2 edges to be selected")
        return

    line = intersect_line_line(verts[edges[0].vertices[0]].co,
                               verts[edges[0].vertices[1]].co,
                               verts[edges[1].vertices[0]].co,
                               verts[edges[1].vertices[1]].co)

    if line is None:
        operator.report({'ERROR'}, "Selected edges do not intersect")
        return

    point = line[0].lerp(line[1], 0.5)
    context.scene.cursor_location = obj.matrix_world * point

class VIEW3D_OT_CursorToEdgeIntersection(bpy.types.Operator):
    "Finds the mid-point of the shortest distance between two edges"

    bl_idname = "view3d.snap_cursor_to_edge_intersection"
    bl_label = "Cursor to Edge Intersection"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj != None and obj.type == 'MESH'

    def execute(self, context):
        edgeIntersect(context, self)
        return {'FINISHED'}

class VIEW3D_MT_undoS(bpy.types.Menu):
    bl_label = "Undo/Redo"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("ed.undo", icon='TRIA_LEFT')
        layout.operator("ed.redo", icon='TRIA_RIGHT')

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
