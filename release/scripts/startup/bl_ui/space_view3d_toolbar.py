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
from bpy.types import Menu, Panel, UIList
from bl_ui.properties_grease_pencil_common import (
        GreasePencilDrawingToolsPanel,
        GreasePencilStrokeEditPanel,
        GreasePencilInterpolatePanel,
        GreasePencilStrokeSculptPanel,
        GreasePencilBrushPanel,
        GreasePencilBrushCurvesPanel
        )
from bl_ui.properties_paint_common import (
        UnifiedPaintPanel,
        brush_texture_settings,
        brush_texpaint_common,
        brush_mask_texture_settings,
        )


class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'


# **************** standard tool clusters ******************

# Keyframing tools
def draw_keyframing_tools(context, layout):
    col = layout.column(align=True)
    col.label(text="Keyframes:")
    col.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT', text="Insert              ")
    col.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="Remove          ")
    col.operator("nla.bake", icon= 'BAKE_ACTION',text="Bake Action    ")  
    col.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="Clear               ")

    col = layout.column(align=True)
    col.label(text="Set Keying Set:")
    row = col.row(align=True)
    row.alignment = 'RIGHT'
    col.operator("anim.keying_set_active_set", icon='TRIA_RIGHT', text="Set Keying Set")

# Keyframing tools just icons
def draw_keyframing_tools_icons(context, layout):
    col = layout.column(align=True)
    col.label(text="Keyframes:")
    row = col.row(align=False)
    row.alignment = 'LEFT'
    row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text = "")
    row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text = "")
    row.operator("nla.bake", icon= 'BAKE_ACTION',text = "")
    row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text = "")

    col = layout.column(align=True)
    col.label(text="Set Keying Set:")
    col.operator("anim.keying_set_active_set", icon='TRIA_RIGHT', text="Set Keying Set")

# Used by vertex & weight paint
def draw_vpaint_symmetry(layout, vpaint):
    col = layout.column(align=True)
    col.label(text="Mirror:")
    row = col.row(align=True)

    row.prop(vpaint, "use_symmetry_x", text="X", toggle=True)
    row.prop(vpaint, "use_symmetry_y", text="Y", toggle=True)
    row.prop(vpaint, "use_symmetry_z", text="Z", toggle=True)

    col = layout.column()
    col.prop(vpaint, "radial_symmetry", text="Radial")

# ********** default tools for object-mode ****************

class VIEW3D_MT_snap_panel(View3DPanel, Panel):
    """Snap Tools"""
    bl_label = "Snap"
    bl_category = "Tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
        obj = context.active_object

        # text
        if not view.show_iconbuttons: 

            col = layout.column(align=True)

            col.label(text="Selection to ... :")
            
            col.operator("view3d.snap_selected_to_cursor", text="Cursor              ", icon = "SELECTIONTOCURSOR").use_offset = False
            col.operator("view3d.snap_selected_to_cursor", text="Cursor (Offset) ", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
            col.operator("view3d.snap_selected_to_active", text="Active              ", icon = "SELECTIONTOACTIVE")
            col.operator("view3d.snap_selected_to_grid", text="Grid                  ", icon = "SELECTIONTOGRID")

            col = layout.column(align=True)

            col.label(text="Cursor to ... :")
            col.operator("view3d.snap_cursor_to_selected", text="Selected          ", icon = "CURSORTOSELECTION")
            col.operator("view3d.snap_cursor_to_center", text="Center              ", icon = "CURSORTOCENTER")          
            col.operator("view3d.snap_cursor_to_active", text="Active              ", icon = "CURSORTOACTIVE")
            col.operator("view3d.snap_cursor_to_grid", text="Grid                 ", icon = "CURSORTOGRID")

            if obj:

                if obj.type == 'MESH' and obj.mode in {'EDIT'}:
            
                    col = layout.column(align=True)

                    col.label(text="Snap to ... :")
                    col.operator("mesh.symmetry_snap", text = "Symmetry      ", icon = "SNAP_SYMMETRY")

        else: 

            col = layout.column(align=True)
            col.label(text="Selection to ... :")
            row = col.row(align=False)
            row.alignment = 'LEFT'

            row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
            row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
            row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
            row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

            col.label(text="Cursor to ... :")
            row = col.row(align=False)
            row.alignment = 'LEFT'

            row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")         
            row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")         
            row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
            row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

            if obj:

                if obj.type == 'MESH' and obj.mode in {'EDIT'}:

                    col.label(text="Snap to ... :")
                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("mesh.symmetry_snap", text = "", icon = "SNAP_SYMMETRY")


class VIEW3D_PT_tools_object(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "objectmode"
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)

        obj = context.active_object
        if obj:
            obj_type = obj.type

            view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
            # text
            if not view.show_iconbuttons: 
                col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror                   ")
                if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE'}:
                    col = layout.column(align=True)                    
                    col.operator("object.join", icon ='JOIN', text="Join                      ")
                    
                if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'FONT', 'LATTICE'}:
                    col = layout.column(align=True)
                    col.operator_menu_enum("object.origin_set", "type", text="Set Origin")

                if obj_type in {'MESH', 'CURVE', 'SURFACE'}:
                    col = layout.column(align=True)
                    col.label(text="Shading:")
                    #row = col.row(align=True)
                    col.operator("object.shade_smooth", text="Smooth                ", icon ='SHADING_SMOOTH')
                    col.operator("object.shade_flat", text="Flat                       ", icon ='SHADING_FLAT')

                if obj_type == 'MESH':
                    
                    mesh = context.active_object.data

                    col = layout.column()

                    # bfa - autosmooth below shading.
                    col.prop(mesh, "use_auto_smooth")
                    sub = col.column()
                    sub.active = mesh.use_auto_smooth and not mesh.has_custom_normals
                    sub.prop(mesh, "auto_smooth_angle", text="Angle")
                    col.prop(mesh, "show_double_sided")
                    
                    # data transfer
                    col = layout.column(align=True)
                    col.label(text="Data Transfer:")
                    col.operator("object.data_transfer", icon ='TRANSFER_DATA', text="Data                     ")
                    col.operator("object.datalayout_transfer", icon ='TRANSFER_DATA_LAYOUT', text="Data Layout         ")
                    col.operator("object.join_uvs", icon ='TRANSFER_UV', text = "UV Map                ")
                   
            
            # icons
            else:

                row = layout.row(align=False)
                row.alignment = 'LEFT'
                row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")
                if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE'}:
                    row.operator("object.join", icon ='JOIN', text= "" )

                if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'FONT', 'LATTICE'}:
                    col = layout.column(align=True)
                    col.label(text="Set Origin:")
                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    #col.operator_menu_enum("object.origin_set", "type", text="Set Origin")
                    row.operator("object.origin_set", icon ='GEOMETRY_TO_ORIGIN', text = "").type='GEOMETRY_ORIGIN'
                    row.operator("object.origin_set", icon ='ORIGIN_TO_GEOMETRY', text = "").type='ORIGIN_GEOMETRY'
                    row.operator("object.origin_set", icon ='ORIGIN_TO_CURSOR', text = "").type='ORIGIN_CURSOR'
                    row.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text = "").type='ORIGIN_CENTER_OF_MASS'

                if obj_type in {'MESH', 'CURVE', 'SURFACE'}:
                    col = layout.column(align=True)
                    col.label(text="Shading:")
                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("object.shade_smooth", icon ='SHADING_SMOOTH', text = "")
                    row.operator("object.shade_flat", icon ='SHADING_FLAT', text = "")

                if obj_type == 'MESH':

                    mesh = context.active_object.data

                    col = layout.column()

                    # bfa - autosmooth below shading.
                    col.prop(mesh, "use_auto_smooth")
                    sub = col.column()
                    sub.active = mesh.use_auto_smooth and not mesh.has_custom_normals
                    sub.prop(mesh, "auto_smooth_angle", text="Angle")
                    col.prop(mesh, "show_double_sided")
                    
                    # data transfer
                    col = layout.column(align=True)
                    col.label(text="Data Transfer:")
                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("object.data_transfer", icon ='TRANSFER_DATA', text = "")
                    row.operator("object.datalayout_transfer", icon ='TRANSFER_DATA_LAYOUT', text = "")
                    row.operator("object.join_uvs", icon ='TRANSFER_UV', text = "")


class VIEW3D_PT_tools_add_object(View3DPanel, Panel):
    bl_category = "Create"
    bl_context = "objectmode"
    bl_label = "Add Primitive"

    @staticmethod
    def draw_add_mesh(layout, label=False):
        if label:
            layout.label(text="Primitives:")
        layout.operator("mesh.primitive_plane_add", text="Plane             ", icon='MESH_PLANE')
        layout.operator("mesh.primitive_cube_add", text="Cube             ", icon='MESH_CUBE')
        layout.operator("mesh.primitive_circle_add", text="Circle            ", icon='MESH_CIRCLE')
        layout.operator("mesh.primitive_uv_sphere_add", text=" UV Sphere     ", icon='MESH_UVSPHERE')
        layout.operator("mesh.primitive_ico_sphere_add", text="Ico Sphere    ", icon='MESH_ICOSPHERE')
        layout.operator("mesh.primitive_cylinder_add", text="Cylinder        ", icon='MESH_CYLINDER')
        layout.operator("mesh.primitive_cone_add", text="Cone             ", icon='MESH_CONE')
        layout.operator("mesh.primitive_torus_add", text="Torus              ", icon='MESH_TORUS')

        if label:
            layout.label(text="Special:")
        else:
            layout.separator()
        layout.operator("mesh.primitive_grid_add", text="Grid               ", icon='MESH_GRID')
        layout.operator("mesh.primitive_monkey_add", text="Monkey         ", icon='MESH_MONKEY')

    @staticmethod
    def draw_add_mesh_icons(layout, label=False):
        if label:
            layout.label(text="Primitives:")
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("mesh.primitive_plane_add", text = "", icon='MESH_PLANE')
        row.operator("mesh.primitive_cube_add", text = "", icon='MESH_CUBE')
        row.operator("mesh.primitive_circle_add", text = "", icon='MESH_CIRCLE')
        row.operator("mesh.primitive_uv_sphere_add", text = "", icon='MESH_UVSPHERE')
        layout.separator()
        row = layout.row(align=False)
        row.operator("mesh.primitive_ico_sphere_add", text = "", icon='MESH_ICOSPHERE')       
        row.operator("mesh.primitive_cylinder_add", text = "", icon='MESH_CYLINDER')
        row.operator("mesh.primitive_cone_add", text = "", icon='MESH_CONE')
        row.operator("mesh.primitive_torus_add", text = "", icon='MESH_TORUS')

        if label:
            layout.label(text="Special:")
        else:
            layout.separator()
        row = layout.row(align=False)
        row.operator("mesh.primitive_grid_add", text = "", icon='MESH_GRID')
        row.operator("mesh.primitive_monkey_add", text = "", icon='MESH_MONKEY')

    @staticmethod
    def draw_add_curve(layout, label=False):
        if label:
            layout.label(text="Bezier:")
        layout.operator("curve.primitive_bezier_curve_add", text="Bezier            ", icon='CURVE_BEZCURVE')
        layout.operator("curve.primitive_bezier_circle_add", text="Circle             ", icon='CURVE_BEZCIRCLE')

        if label:
            layout.label(text="Nurbs:")
        else:
            layout.separator()
        layout.operator("curve.primitive_nurbs_curve_add", text="Nurbs Curve  ", icon='CURVE_NCURVE')
        layout.operator("curve.primitive_nurbs_circle_add", text="Nurbs Circle  ", icon='CURVE_NCIRCLE')
        layout.operator("curve.primitive_nurbs_path_add", text="Path               ", icon='CURVE_PATH')
        
        layout.separator()

        layout.operator("curve.draw", icon='LINE_DATA')
        
    @staticmethod
    def draw_add_curve_icons(layout, label=False):
        if label:
            layout.label(text="Bezier:")
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("curve.primitive_bezier_curve_add", text = "", icon='CURVE_BEZCURVE')
        row.operator("curve.primitive_bezier_circle_add", text = "", icon='CURVE_BEZCIRCLE')

        if label:
            layout.label(text="Nurbs:")
        else:
            layout.separator()
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("curve.primitive_nurbs_curve_add", text = "", icon='CURVE_NCURVE')
        row.operator("curve.primitive_nurbs_circle_add", text = "", icon='CURVE_NCIRCLE')
        row.operator("curve.primitive_nurbs_path_add", text = "", icon='CURVE_PATH')
        
        row.operator("curve.draw", text = "", icon='LINE_DATA')

    @staticmethod
    def draw_add_surface(layout):
        layout.operator("surface.primitive_nurbs_surface_curve_add", text="Surface Curve ", icon='SURFACE_NCURVE')
        layout.operator("surface.primitive_nurbs_surface_circle_add", text="Surface Circle ", icon='SURFACE_NCIRCLE')
        layout.operator("surface.primitive_nurbs_surface_surface_add", text="Surface Patch  ", icon='SURFACE_NSURFACE')
        layout.operator("surface.primitive_nurbs_surface_cylinder_add", text="Surface Cylinder", icon='SURFACE_NCYLINDER')
        layout.operator("surface.primitive_nurbs_surface_sphere_add", text="Surface Sphere", icon='SURFACE_NSPHERE')
        layout.operator("surface.primitive_nurbs_surface_torus_add", text="Surface Torus  ", icon='SURFACE_NTORUS')

    @staticmethod
    def draw_add_surface_icons(layout):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("surface.primitive_nurbs_surface_curve_add", text = "", icon='SURFACE_NCURVE')
        row.operator("surface.primitive_nurbs_surface_circle_add", text = "", icon='SURFACE_NCIRCLE')
        row.operator("surface.primitive_nurbs_surface_surface_add", text = "", icon='SURFACE_NSURFACE')
        row.operator("surface.primitive_nurbs_surface_cylinder_add", text = "", icon='SURFACE_NCYLINDER')
        layout.separator()
        row = layout.row(align=False)
        row.operator("surface.primitive_nurbs_surface_sphere_add", text = "", icon='SURFACE_NSPHERE')
        row.operator("surface.primitive_nurbs_surface_torus_add", text = "", icon='SURFACE_NTORUS')

    @staticmethod
    def draw_add_mball(layout):
        #layout.operator_enum("object.metaball_add", "type")
        layout.operator("object.metaball_add", text="Ball                 ", icon='META_BALL').type= 'BALL'
        layout.operator("object.metaball_add", text="Capsule          ", icon='META_CAPSULE').type= 'CAPSULE'
        layout.operator("object.metaball_add", text="Plane              ", icon='META_PLANE').type= 'PLANE'
        layout.operator("object.metaball_add", text="Ellipsoid         ", icon='META_ELLIPSOID').type= 'ELLIPSOID'
        layout.operator("object.metaball_add", text="Cube              ", icon='META_CUBE').type= 'CUBE'
 
    @staticmethod
    def draw_add_mball_icons(layout):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("object.metaball_add", text = "", icon='META_BALL').type= 'BALL'
        row.operator("object.metaball_add", text = "", icon='META_CAPSULE').type= 'CAPSULE'
        row.operator("object.metaball_add", text = "", icon='META_PLANE').type= 'PLANE'
        row.operator("object.metaball_add", text = "", icon='META_ELLIPSOID').type= 'ELLIPSOID'
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.metaball_add", text = "", icon='META_CUBE').type= 'CUBE'

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
        col = layout.column(align=True)

        col.label(text="Mesh:")
        if not view.show_iconbuttons: 
            self.draw_add_mesh(col)
        else:
            self.draw_add_mesh_icons(col)

        col = layout.column(align=True)
        col.label(text="Curve:")
        if not view.show_iconbuttons: 
            self.draw_add_curve(col)
        else:
            self.draw_add_curve_icons(col)

        col = layout.column(align=True)
        col.label(text="Surface:")
        if not view.show_iconbuttons: 
            self.draw_add_surface(col)
        else:
            self.draw_add_surface_icons(col)

        col = layout.column(align=True)
        col.label(text="Metaball:")
        if not view.show_iconbuttons: 
            self.draw_add_mball(col)
        else:
            self.draw_add_mball_icons(col)

        layout.separator()

        # note, don't use 'EXEC_SCREEN' or operators wont get the 'v3d' context.

        # Note: was EXEC_AREA, but this context does not have the 'rv3d', which prevents
        #       "align_view" to work on first call (see [#32719]).

        layout.operator_context = 'EXEC_REGION_WIN'

        if len(bpy.data.groups) > 10:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("object.group_instance_add", text="Group Instance...", icon='OUTLINER_OB_GROUP_INSTANCE')
        else:
            layout.operator_menu_enum("object.group_instance_add", "group", text="Group Instance", icon='OUTLINER_OB_GROUP_INSTANCE')

class VIEW3D_PT_tools_add_misc(View3DPanel, Panel):
    bl_category = "Create"
    bl_context = "objectmode"
    bl_label = "Add Misc"

    @staticmethod
    def draw_add_lamp(layout):
        #layout.operator_enum("object.lamp_add", "type")

        layout.operator("object.lamp_add", text="Point               ", icon='LAMP_POINT').type= 'POINT'
        layout.operator("object.lamp_add", text="Sun                 ", icon='LAMP_SUN').type= 'SUN' 
        layout.operator("object.lamp_add", text="Spot                ", icon='LAMP_SPOT').type= 'SPOT' 
        layout.operator("object.lamp_add", text="Hemi              ", icon='LAMP_HEMI').type= 'HEMI' 
        layout.operator("object.lamp_add", text="Area               ", icon='LAMP_AREA').type= 'AREA' 
  

    @staticmethod
    def draw_add_lamp_icons(layout):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("object.lamp_add", text = "", icon='LAMP_POINT').type= 'POINT'
        row.operator("object.lamp_add", text = "", icon='LAMP_SUN').type= 'SUN' 
        row.operator("object.lamp_add", text = "", icon='LAMP_SPOT').type= 'SPOT' 
        row.operator("object.lamp_add", text = "", icon='LAMP_HEMI').type= 'HEMI' 
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.lamp_add", text = "", icon='LAMP_AREA').type= 'AREA' 

    @staticmethod
    def draw_add_other(layout):
        layout.operator("object.text_add", text="Text                ", icon='OUTLINER_OB_FONT')
        layout.operator("object.armature_add", text="Armature       ", icon='OUTLINER_OB_ARMATURE')
        layout.operator("object.add", text="Lattice           ", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.operator("object.camera_add", text="Camera          ", icon='OUTLINER_OB_CAMERA')
        layout.operator("object.speaker_add", text="Speaker         ", icon='OUTLINER_OB_SPEAKER')
        

    @staticmethod
    def draw_add_other_icons(layout):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("object.text_add", text = "", icon='OUTLINER_OB_FONT')
        row.operator("object.armature_add", text = "", icon='OUTLINER_OB_ARMATURE')
        row.operator("object.add", text = "", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        row.operator("object.camera_add", text = "", icon='OUTLINER_OB_CAMERA')
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.speaker_add", text = "", icon='OUTLINER_OB_SPEAKER')


    @staticmethod
    def draw_add_empties(layout):
        layout.operator("object.empty_add", text="Plain Axes      ", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
        layout.operator("object.empty_add", text="Sphere            ", icon='EMPTY_SPHERE').type = 'SPHERE'
        layout.operator("object.empty_add", text="Circle             ", icon='EMPTY_CIRCLE').type = 'CIRCLE'
        layout.operator("object.empty_add", text="Cone               ", icon='EMPTY_CONE').type = 'CONE'
        layout.operator("object.empty_add", text="Cube               ", icon='EMPTY_CUBE').type = 'CUBE'       
        layout.operator("object.empty_add", text="Single Arrow  ", icon='EMPTY_SINGLEARROW').type = 'SINGLE_ARROW'
        layout.operator("object.empty_add", text="Arrows           ", icon='EMPTY_ARROWS').type = 'ARROWS'       
        layout.operator("object.empty_add", text="Image             ", icon='EMPTY_IMAGE').type = 'IMAGE'

    @staticmethod
    def draw_add_empties_icons(layout):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("object.empty_add", text = "", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
        row.operator("object.empty_add", text = "", icon='EMPTY_SPHERE').type = 'SPHERE'
        row.operator("object.empty_add", text = "", icon='EMPTY_CIRCLE').type = 'CIRCLE'
        row.operator("object.empty_add", text = "", icon='EMPTY_CONE').type = 'CONE'
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.empty_add", text = "", icon='EMPTY_CUBE').type = 'CUBE'      
        row.operator("object.empty_add", text = "", icon='EMPTY_SINGLEARROW').type = 'SINGLE_ARROW'       
        row.operator("object.empty_add", text = "", icon='EMPTY_ARROWS').type = 'ARROWS'
        row.operator("object.empty_add", text = "", icon='EMPTY_IMAGE').type = 'IMAGE'

    @staticmethod
    def draw_add_force_field(layout):
        layout.operator("object.effector_add", text="Boid                ", icon='FORCE_BOID').type='BOID'
        layout.operator("object.effector_add", text="Charge           ", icon='FORCE_CHARGE').type='CHARGE'
        layout.operator("object.effector_add", text="Curve Guide   ", icon='FORCE_CURVE').type='GUIDE'
        layout.operator("object.effector_add", text="Drag                ", icon='FORCE_DRAG').type='DRAG'
        layout.operator("object.effector_add", text="Force              ", icon='FORCE_FORCE').type='FORCE'
        layout.operator("object.effector_add", text="Harmonic       ", icon='FORCE_HARMONIC').type='HARMONIC'
        layout.operator("object.effector_add", text="Lennard-Jones", icon='FORCE_LENNARDJONES').type='LENNARDJ'
        layout.operator("object.effector_add", text="Magnetic        ", icon='FORCE_MAGNETIC').type='MAGNET'
        layout.operator("object.effector_add", text="Smoke flow    ", icon='FORCE_SMOKEFLOW').type='SMOKE'
        layout.operator("object.effector_add", text="Texture           ", icon='FORCE_TEXTURE').type='TEXTURE'
        layout.operator("object.effector_add", text="Turbulence     ", icon='FORCE_TURBULENCE').type='TURBULENCE'
        layout.operator("object.effector_add", text="Vortex            ", icon='FORCE_VORTEX').type='VORTEX'
        layout.operator("object.effector_add", text="Wind               ", icon='FORCE_WIND').type='WIND'

    @staticmethod
    def draw_add_force_field_icons(layout):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("object.effector_add", text = "", icon='FORCE_BOID').type='BOID'
        row.operator("object.effector_add", text = "", icon='FORCE_CHARGE').type='CHARGE'
        row.operator("object.effector_add", text = "", icon='FORCE_CURVE').type='GUIDE'
        row.operator("object.effector_add", text = "", icon='FORCE_DRAG').type='DRAG'
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.effector_add", text = "", icon='FORCE_FORCE').type='FORCE'
        row.operator("object.effector_add", text = "", icon='FORCE_HARMONIC').type='HARMONIC'
        row.operator("object.effector_add", text = "", icon='FORCE_LENNARDJONES').type='LENNARDJ'
        row.operator("object.effector_add", text = "", icon='FORCE_MAGNETIC').type='MAGNET'
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.effector_add", text = "", icon='FORCE_SMOKEFLOW').type='SMOKE'
        row.operator("object.effector_add", text = "", icon='FORCE_TEXTURE').type='TEXTURE'
        row.operator("object.effector_add", text = "", icon='FORCE_TURBULENCE').type='TURBULENCE'
        row.operator("object.effector_add", text = "", icon='FORCE_VORTEX').type='VORTEX'
        layout.separator()
        row = layout.row(align=False)
        row.operator("object.effector_add", text = "", icon='FORCE_WIND').type='WIND'


    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        obj = context.active_object
        mode_string = context.mode
        edit_object = context.edit_object
        gp_edit = context.gpencil_data and context.gpencil_data.use_stroke_edit_mode

        col = layout.column(align=True)
        col.label(text="Lamp:")
        if not view.show_iconbuttons: 
            self.draw_add_lamp(col)
        else:
            self.draw_add_lamp_icons(col)

        col = layout.column(align=True)
        col.label(text="Other:")
        if not view.show_iconbuttons:
            self.draw_add_other(col)
        else:
            self.draw_add_other_icons(col)

        col = layout.column(align=True)
        col.label(text="Empties:")
        if not view.show_iconbuttons:
            self.draw_add_empties(col)
        else:
            self.draw_add_empties_icons(col)

        col = layout.column(align=True)
        col.label(text="Force Field:")
        if not view.show_iconbuttons:
            self.draw_add_force_field(col)
        else:
            self.draw_add_force_field_icons(col)

        # Add menu for addons.
        col = layout.column(align=True)
        col.label(text="Addons add:")
        if gp_edit:
            pass
        elif mode_string == 'OBJECT':
            col.menu("INFO_MT_add", text="Add")
        elif mode_string == 'EDIT_MESH':
            col.menu("INFO_MT_mesh_add", text="Add")
        elif mode_string == 'EDIT_CURVE':
            col.menu("INFO_MT_curve_add", text="Add")
        elif mode_string == 'EDIT_SURFACE':
            col.menu("INFO_MT_surface_add", text="Add")
        elif mode_string == 'EDIT_METABALL':
            col.menu("INFO_MT_metaball_add", text="Add")
        elif mode_string == 'EDIT_ARMATURE':
            col.menu("INFO_MT_edit_armature_add", text="Add")


class VIEW3D_PT_tools_relations(View3DPanel, Panel):
    bl_category = "Relations"
    #bl_context = "objectmode"
    bl_label = "Relations"

    def draw(self, context):
        layout = self.layout

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        obj = context.active_object

        if obj is not None:

            mode = obj.mode
                # Particle edit
            if mode == 'OBJECT':

                if not view.show_iconbuttons: 

                    col = layout.column(align=True)

                    col.label(text="Group:")
                    col.operator("group.create", icon='NEW_GROUP', text="New Group           ")
                    col.operator("group.objects_add_active", icon='ADD_TO_ACTIVE', text="Add to Active       ")
                    col.operator("group.objects_remove", icon='REMOVE_FROM_GROUP', text="Remove from Group")
                    col.separator()
                    col.operator("group.objects_remove_active", icon='REMOVE_SELECTED_FROM_ACTIVE_GROUP', text="Remove from Active")
                    col.operator("group.objects_remove_all", icon='REMOVE_FROM_ALL_GROUPS', text="Remove from All  ")

                    col.separator()

                    col.label(text="Parent:")
                    row = col.row(align=True)
                    row.operator("object.parent_set", icon='PARENT_SET', text="Set")
                    row.operator("object.parent_clear", icon='PARENT_CLEAR', text="Clear")

                    col.separator()

                    col.label(text="Object Data:")
                    col.operator("object.make_single_user", icon='MAKE_SINGLE_USER', text = "Make Single User ")
                    
                    col.menu("VIEW3D_MT_make_links")
                    
                    operator_context_default = layout.operator_context
                    if len(bpy.data.scenes) > 10:
                        col.operator_context = 'INVOKE_REGION_WIN'
                        col.operator("object.make_links_scene", text="Link to SCN", icon='OUTLINER_OB_EMPTY')
                    else:
                        col.operator_context = 'EXEC_REGION_WIN'
                        col.operator_menu_enum("object.make_links_scene", "scene", text="Link to SCN")

                    col.separator()

                    col.label(text="Linked Objects:")
                    col.operator("object.make_local", icon='MAKE_LOCAL', text = "Make Local          ")
                    col.operator("object.proxy_make", icon='MAKE_PROXY', text = "Make Proxy          ")

                else:
                    col = layout.column(align=True)
                    col.label(text="Group:")
                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("group.create", icon='NEW_GROUP', text = "")
                    row.operator("group.objects_add_active", icon='ADD_TO_ACTIVE', text = "")
                    row.operator("group.objects_remove", icon='REMOVE_FROM_GROUP', text = "")

                    layout.separator()
                    row = layout.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("group.objects_remove_active", icon='REMOVE_SELECTED_FROM_ACTIVE_GROUP', text = "")
                    row.operator("group.objects_remove_all", icon='REMOVE_FROM_ALL_GROUPS', text = "")

                    col = layout.column(align=True)
                    col.label(text="Parent:")

                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("object.parent_set", icon='PARENT_SET', text = "")
                    row.operator("object.parent_clear", icon='PARENT_CLEAR', text = "")

                    col = layout.column(align=True)
                    col.label(text="Object Data:")

                    row = col.row(align=False)
                    row.alignment = 'LEFT'

                    row.operator("object.make_single_user", icon='MAKE_SINGLE_USER', text = "")

                    row.menu("VIEW3D_MT_make_links", text = "", icon='LINK_DATA' ) # bfa - link data 
                
                    operator_context_default = layout.operator_context
                    if len(bpy.data.scenes) > 10:
                        layout.operator_context = 'INVOKE_REGION_WIN'
                        layout.operator("object.make_links_scene", text="Link to SCN", icon='OUTLINER_OB_EMPTY')
                    else:
                        layout.operator_context = 'EXEC_REGION_WIN'
                        layout.operator_menu_enum("object.make_links_scene", "scene", text="Link to SCN")

                    col = layout.column(align=True)
                    col.label(text="Linked Objects:")

                    row = col.row(align=False)
                    row.alignment = 'LEFT'
                    row.operator("object.make_local", icon='MAKE_LOCAL', text = "")
                    row.operator("object.proxy_make", icon='MAKE_PROXY', text = "")

            if mode == 'EDIT':

                col = layout.column(align=True)
                
                
                if not view.show_iconbuttons: 
                        col = layout.column(align=True)
                        row = col.row(align=True)
                
                        col.label(text="Parent:")
                        layout.operator("object.vertex_parent_set", icon = "VERTEX_PARENT")
                        
                        if obj.type == 'ARMATURE':
                            col = layout.column(align=True)
                            row = col.row(align=True)
                            row.operator("armature.parent_set", icon='PARENT_SET', text="Make")
                            row.operator("armature.parent_clear", icon='PARENT_CLEAR', text="Clear")
                        
                else:
                        col = layout.column(align=True)
                        col.label(text="Parent:")
                        
                        row = col.row(align=False)
                        row.alignment = 'LEFT'
                        row.operator("object.vertex_parent_set", text= "", icon = "VERTEX_PARENT")
                        
                        if obj.type == 'ARMATURE':
                            row.operator("armature.parent_set", icon='PARENT_SET', text = "")
                            row.operator("armature.parent_clear", icon='PARENT_CLEAR', text = "")

            if mode == 'POSE':

                if obj.type == 'ARMATURE':

                    col = layout.column(align=True)
                    col.label(text="Parent:")

                    if not view.show_iconbuttons: 
                        col = layout.column(align=True)
                        row = col.row(align=True)
                        row.operator("object.parent_set", icon='PARENT_SET', text="Set")
                        row.operator("object.parent_clear", icon='PARENT_CLEAR', text="Clear")

                    else:
                        col = layout.column(align=True)
                        row = col.row(align=False)
                        row.alignment = 'LEFT'
                        row.operator("object.parent_set", icon='PARENT_SET', text = "")
                        row.operator("object.parent_clear", icon='PARENT_CLEAR', text = "")


class VIEW3D_PT_tools_animation(View3DPanel, Panel):
    bl_category = "Animation"
    bl_context = "objectmode"
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            draw_keyframing_tools(context, layout)

            col = layout.column(align=True)
            col.label(text="Motion Paths:")
            col.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE', text="Calculate        ")
            col.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="Clear               ")

        else:
            draw_keyframing_tools_icons(context, layout)

            col = layout.column(align=True)
            col.label(text="Motion Paths:")

            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text = "")
            row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text = "")


class VIEW3D_PT_tools_rigid_body(View3DPanel, Panel):
    bl_category = "Physics"
    bl_context = "objectmode"
    bl_label = "Rigid Body Tools"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons:

            col = layout.column(align=True)
            col.label(text="Add/Remove:")
            col.operator("rigidbody.objects_add", icon='RIGID_ADD_ACTIVE', text="Add Active          ").type = 'ACTIVE'
            col.operator("rigidbody.objects_add", icon='RIGID_ADD_PASSIVE', text="Add Passive         ").type = 'PASSIVE'
            col.operator("rigidbody.objects_remove", icon='RIGID_REMOVE', text="Remove               ")

            col = layout.column(align=True)
            col.label(text="Object Tools:")
            col.operator("rigidbody.shape_change", icon='RIGID_CHANGE_SHAPE', text="Change Shape      ")
            col.operator("rigidbody.mass_calculate", icon='RIGID_CALCULATE_MASS', text="Calculate Mass    ")
            col.operator("rigidbody.object_settings_copy", icon='RIGID_COPY_FROM_ACTIVE', text="Copy from Active")
            col.operator("object.visual_transform_apply", icon='RIGID_APPLY_TRANS', text="Apply Visual Trans")
            col.operator("rigidbody.bake_to_keyframes", icon='RIGID_BAKE_TO_KEYFRAME', text="Bake To Keyframes")
            col.label(text="Constraints:")
            col.operator("rigidbody.connect", icon='RIGID_CONSTRAINTS_CONNECT', text="Connect               ")
        else:
            col = layout.column(align=True)
            col.label(text="Add/Remove:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("rigidbody.objects_add", icon='RIGID_ADD_ACTIVE', text = "").type = 'ACTIVE'
            row.operator("rigidbody.objects_add", icon='RIGID_ADD_PASSIVE', text = "").type = 'PASSIVE'
            row.operator("rigidbody.objects_remove", icon='RIGID_REMOVE', text = "")

            col = layout.column(align=True)
            col.label(text="Object Tools:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("rigidbody.shape_change", icon='RIGID_CHANGE_SHAPE', text = "")
            row.operator("rigidbody.mass_calculate", icon='RIGID_CALCULATE_MASS', text = "")
            row.operator("rigidbody.object_settings_copy", icon='RIGID_COPY_FROM_ACTIVE', text = "")
            row.operator("object.visual_transform_apply", icon='RIGID_APPLY_TRANS', text = "")

            col.separator()

            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("rigidbody.bake_to_keyframes", icon='RIGID_BAKE_TO_KEYFRAME', text = "")

            col = layout.column(align=True)
            col.label(text="Constraints:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("rigidbody.connect", icon='RIGID_CONSTRAINTS_CONNECT', text = "")


# ********** default tools for editmode_mesh ****************


class VIEW3D_PT_tools_meshedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "mesh_edit"
    bl_label = "Mesh Tools"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            col = layout.column(align=True)
            col.operator("transform.shrink_fatten", icon = 'SHRINK_FATTEN', text="Shrink/Fatten   ")
            col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror              ")
            col.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP", text = "Mirror Vertex Group")
            col.operator("mesh.symmetrize", icon = "SYMMETRIZE", text = "Symmetrize")

            # --------------------------------------

            col = layout.column(align=True)
            col.label(text="Modify:")
            
            col.operator("view3d.edit_mesh_extrude_move_normal", icon='EXTRUDE_REGION', text="Extrude Region")
            col.operator("view3d.edit_mesh_extrude_individual_move", icon='EXTRUDE_INDIVIDUAL', text="Individual        ")
            col.menu("VIEW3D_MT_edit_mesh_extrude")

            col = layout.column(align=True)

            col.operator("mesh.spin", icon='SPIN', text="Spin                 ")
            col.operator("mesh.screw", icon='SCREW', text="Screw              ")
            col.operator("mesh.inset", icon='INSET_FACES', text="Inset Faces      ")
            col.operator("mesh.edge_face_add", icon='MAKE_EDGEFACE', text="Make Edge/Face   ")

            col = layout.column(align=True)

            col.operator("mesh.bevel", icon='BEVEL', text="Bevel               ")
            col.operator("mesh.bevel", icon='VERTEXBEVEL',text = "Vertex Bevel    ").vertex_only = True          
            col.operator("mesh.subdivide", icon='SUBDIVIDE_EDGES', text="Subdivide        ")
            col.operator("mesh.bridge_edge_loops", icon = "BRIDGE_EDGELOOPS")

            # --------------------------------------

            col = layout.column(align=True)
            col.label(text="Cut/Slide:")

            props = col.operator("mesh.knife_tool", icon='KNIFE', text="Knife                ")
            props.use_occlude_geometry = True
            props.only_selected = False
            props = col.operator("mesh.knife_tool", icon='KNIFE_SELECT', text="Knife Select    ")
            props.use_occlude_geometry = False
            props.only_selected = True
            col.operator("mesh.loopcut_slide", icon='LOOP_CUT_AND_SLIDE', text="Loop Cut n Slide  ")
            col.operator("mesh.offset_edge_loops_slide", icon='OFFSET_EDGE_SLIDE')

            col = layout.column(align=True)

            col.operator("mesh.knife_project", icon='KNIFE_PROJECT', text="Knife Project   ")
            col.operator("mesh.bisect", icon='BISECT', text="Bisect              ")

            # --------------------------------------

            col = layout.column(align=True)
            col.label(text="Merge/Separate:")

            col.operator_menu_enum("mesh.merge", "type", icon = "MERGE")
            col.operator_menu_enum("mesh.separate", "type", icon = "SEPARATE")

            # --------------------------------------

            col = layout.column(align=True)
            col.label(text="Deform:")

            col.operator("transform.edge_slide", icon='SLIDE_EDGE', text="Edge Slide       ")
            col.operator("transform.vert_slide", icon='SLIDE_VERTEX', text="Vertex Slide    ")
            col.operator("mesh.vertices_smooth", icon='SMOOTH_VERTEX')
            col.operator("mesh.vertices_smooth_laplacian", icon='LAPLACIAN_SMOOTH_VERTEX')

            # --------------------------------------
            
            col.label(text="Dissolve:")
            col.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS')
            col.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES')
            col.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES')
            col.operator("mesh.remove_doubles", icon='REMOVE_DOUBLES')

            col = layout.column(align=True)

            col.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED') 
            col.operator("mesh.dissolve_mode", icon='DISSOLVE_SELECTION')
            col.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE')

        else:

            row = layout.row(align=False)
            row.alignment = 'LEFT'

            row.operator("transform.shrink_fatten", icon = 'SHRINK_FATTEN', text = "")
            row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")
            row.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP", text = "")
            row.operator("mesh.symmetrize", icon = "SYMMETRIZE", text = "")

            # --------------------------------------

            col = layout.column(align=False)
            col.label(text="Modify:")

            row = col.row(align=False)
            row.alignment = 'LEFT' 
            
            row.operator("view3d.edit_mesh_extrude_move_normal", icon='EXTRUDE_REGION', text = "")
            row.operator("view3d.edit_mesh_extrude_individual_move", icon='EXTRUDE_INDIVIDUAL', text = "")
            row.menu("VIEW3D_MT_edit_mesh_extrude", text = "", icon = "EXTRUDE_REGION")         

            col.separator()

            row = col.row(align=False)  
            row.operator("mesh.spin", icon='SPIN', text = "")
            row.operator("mesh.screw", icon='SCREW', text = "")
            row.operator("mesh.inset", icon='INSET_FACES', text = "")
            row.operator("mesh.edge_face_add", icon='MAKE_EDGEFACE', text = "")   
                     
            col.separator()

            row = col.row(align=False)
            row.operator("mesh.bevel", icon='BEVEL', text = "")
            row.operator("mesh.bevel", icon='VERTEXBEVEL',text = "").vertex_only = True
            row.operator("mesh.subdivide", icon='SUBDIVIDE_EDGES', text = "")
            row.operator("mesh.bridge_edge_loops", icon = "BRIDGE_EDGELOOPS", text = "")

            # --------------------------------------

            col = layout.column(align=False)
            col.label(text="Cut/Slide:")

            row = col.row(align=False)
            row.alignment = 'LEFT'
            props = row.operator("mesh.knife_tool", icon='KNIFE', text = "")
            props.use_occlude_geometry = True
            props.only_selected = False
            props = row.operator("mesh.knife_tool", icon='KNIFE_SELECT', text = "")
            props.use_occlude_geometry = False
            props.only_selected = True
            row.operator("mesh.loopcut_slide", icon='LOOP_CUT_AND_SLIDE', text = "")
            row.operator("mesh.offset_edge_loops_slide", icon='OFFSET_EDGE_SLIDE', text = "")

            col.separator()
            row = col.row(align=False)

            row.operator("mesh.knife_project", icon='KNIFE_PROJECT', text = "")
            row.operator("mesh.bisect", icon='BISECT', text = "")

            # --------------------------------------

            col.label(text="Merge/Separate:")
            row = col.row(align=False)
            row.alignment = 'LEFT'

            row.operator_menu_enum("mesh.merge", "type", text = "", icon = "MERGE")
            row.operator_menu_enum("mesh.separate", "type", text = "", icon = "SEPARATE")

            # --------------------------------------

            col = layout.column(align=True)
            col.label(text="Deform:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("transform.edge_slide", icon='SLIDE_EDGE', text = "")
            row.operator("transform.vert_slide", icon='SLIDE_VERTEX', text = "")
            row.operator("mesh.vertices_smooth", icon='SMOOTH_VERTEX', text = "")
            row.operator("mesh.vertices_smooth_laplacian", icon='LAPLACIAN_SMOOTH_VERTEX', text = "")

            # --------------------------------------

            col.label(text="Dissolve:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS', text = "")
            row.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES', text = "")
            row.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES', text = "")
            row.operator("mesh.remove_doubles", icon='REMOVE_DOUBLES', text = "")

            col.separator()

            row = col.row(align=False)
            row.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED', text = "")
            row.operator("mesh.dissolve_mode", icon='DISSOLVE_SELECTION', text = "")
            row.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE', text = "")


class VIEW3D_PT_tools_meshweight(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "mesh_edit"
    bl_label = "Weight Tools"
    bl_options = {'DEFAULT_CLOSED'}

    # Used for Weight-Paint mode and Edit-Mode
    @staticmethod
    def draw_generic(layout):

        col = layout.column()
        col.operator("object.vertex_group_normalize_all", icon='WEIGHT_NORMALIZE_ALL', text="Normalize All  ")
        col.operator("object.vertex_group_normalize",icon='WEIGHT_NORMALIZE', text="Normalize       ")
        col.operator("object.vertex_group_mirror",icon='WEIGHT_MIRROR', text="Mirror              ")
        col.operator("object.vertex_group_invert", icon='WEIGHT_INVERT',text="Invert              ")
        col.operator("object.vertex_group_clean", icon='WEIGHT_CLEAN',text="Clean               ")
        col.operator("object.vertex_group_quantize", icon='WEIGHT_QUANTIZE',text="Quantize         ")
        col.operator("object.vertex_group_levels", icon='WEIGHT_LEVELS',text="Levels             ")
        col.operator("object.vertex_group_smooth", icon='WEIGHT_SMOOTH',text="Smooth           ")
        col.operator("object.vertex_group_limit_total", icon='WEIGHT_LIMIT_TOTAL',text="Limit Total       ")
        col.operator("object.vertex_group_fix", icon='WEIGHT_FIX_DEFORMS',text="Fix Deforms    ")

    # Used for Weight-Paint mode and Edit-Mode
    @staticmethod
    def draw_generic_icons(layout):

        row = layout.row(align=False)
        row.alignment = 'LEFT'
        row.operator("object.vertex_group_normalize_all", icon='WEIGHT_NORMALIZE_ALL', text = "")
        row.operator("object.vertex_group_normalize",icon='WEIGHT_NORMALIZE', text = "")
        row.operator("object.vertex_group_mirror",icon='WEIGHT_MIRROR', text = "")
        row.operator("object.vertex_group_invert", icon='WEIGHT_INVERT',text = "")
        row = layout.row(align=False)
        row.operator("object.vertex_group_clean", icon='WEIGHT_CLEAN',text = "")
        row.operator("object.vertex_group_quantize", icon='WEIGHT_QUANTIZE',text = "")
        row.operator("object.vertex_group_levels", icon='WEIGHT_LEVELS',text = "")
        row.operator("object.vertex_group_smooth", icon='WEIGHT_SMOOTH',text = "")
        row = layout.row(align=False)
        row.operator("object.vertex_group_limit_total", icon='WEIGHT_LIMIT_TOTAL',text = "")
        row.operator("object.vertex_group_fix", icon='WEIGHT_FIX_DEFORMS',text = "")


    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 
            self.draw_generic(layout)
        else:
            self.draw_generic_icons(layout)


class VIEW3D_PT_tools_add_mesh_edit(View3DPanel, Panel):
    bl_category = "Create"
    bl_context = "mesh_edit"
    bl_label = "Add Meshes"

    def draw(self, context):
        layout = self.layout
        scene = context.scene # Our data is in the current scene
        col = layout.column(align=True)

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        # bfa - icon or text buttons
        if not view.show_iconbuttons: 
            VIEW3D_PT_tools_add_object.draw_add_mesh(col, label=True) # the original class
        else:
            VIEW3D_PT_tools_add_object.draw_add_mesh_icons(col, label=True) # the modified class with icon buttons


# Workaround to separate the tooltips for Recalculate Outside and Recalculate Inside
class VIEW3D_normals_make_consistent_inside(bpy.types.Operator):
    """Recalculate Normals Inside\nMake selected faces and normals point inside the mesh"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.normals_recalculate_inside"        # unique identifier for buttons and menu items to reference.
    bl_label = "Recalculate Inside"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.normals_make_consistent(inside=True)
        return {'FINISHED'}  

class VIEW3D_PT_tools_shading(View3DPanel, Panel):
    bl_category = "Shade / UVs"
    bl_context = "mesh_edit"
    bl_label = "Shading"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 
            col = layout.column(align=True)
            col.label(text="Faces:")
            row = col.row(align=True)
            row.operator("mesh.faces_shade_smooth", icon = 'SHADING_SMOOTH', text="Smooth")
            row.operator("mesh.faces_shade_flat", icon = 'SHADING_FLAT',  text="Flat")
            col.label(text="Edges:")
            row = col.row(align=True)
            row.operator("mesh.mark_sharp", icon = 'SHADING_SMOOTH', text="Smooth").clear = True
            row.operator("mesh.mark_sharp", icon = 'SHADING_FLAT', text="Sharp")
            col.label(text="Vertices:")
            row = col.row(align=True)
            props = row.operator("mesh.mark_sharp", icon = 'SHADING_SMOOTH', text="Smooth")
            props.use_verts = True
            props.clear = True
            row.operator("mesh.mark_sharp", icon = 'SHADING_FLAT', text="Sharp").use_verts = True

            col = layout.column(align=True)
            col.label(text="Normals:")
            col.operator("mesh.normals_make_consistent", icon = 'RECALC_NORMALS', text="Recalc Outside      ")
            col.operator("mesh.normals_recalculate_inside", icon = 'RECALC_NORMALS_INSIDE', text="Recalc Inside        ")
            col.operator("mesh.flip_normals", icon = 'FLIP_NORMALS', text="Flip Direction        ")
            col.operator("mesh.set_normals_from_faces", text=" Set From Faces        ", icon = 'SET_FROM_FACES')

        else:
            col = layout.column(align=True)
            col.label(text="Faces:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("mesh.faces_shade_smooth", icon = 'SHADING_SMOOTH', text = "")
            row.operator("mesh.faces_shade_flat", icon = 'SHADING_FLAT',  text = "")
            col.label(text="Edges:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("mesh.mark_sharp", icon = 'SHADING_SMOOTH', text = "").clear = True
            row.operator("mesh.mark_sharp", icon = 'SHADING_FLAT', text = "")
            col.label(text="Vertices:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            props = row.operator("mesh.mark_sharp", icon = 'SHADING_SMOOTH', text = "")
            props.use_verts = True
            props.clear = True
            row.operator("mesh.mark_sharp", icon = 'SHADING_FLAT', text = "").use_verts = True

            col = layout.column(align=True)
            col.label(text="Normals:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("mesh.normals_make_consistent", icon = 'RECALC_NORMALS', text = "")
            row.operator("mesh.normals_recalculate_inside", icon = 'RECALC_NORMALS_INSIDE', text = "")
            row.operator("mesh.flip_normals", icon = 'FLIP_NORMALS', text = "")
            row.operator("mesh.set_normals_from_faces", text = "", icon = 'SET_FROM_FACES')


# Tooltip and operator for Clear Seam.
class VIEW3D_markseam_clear(bpy.types.Operator):
    """Clear Seam\nClears the UV Seam for selected edges"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.clear_seam"        # unique identifier for buttons and menu items to reference.
    bl_label = "Clear seam"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.mark_seam(clear=True)
        return {'FINISHED'}  


class VIEW3D_PT_tools_uvs(View3DPanel, Panel):
    bl_category = "Shade / UVs"
    bl_context = "mesh_edit"
    bl_label = "UVs"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
        col = layout.column(align=True)
        col.label(text="UV Mapping:")
        col.menu("VIEW3D_MT_uv_map", text="Unwrap")

        if not view.show_iconbuttons:          
            col.operator("mesh.mark_seam", icon = 'MARK_SEAM', text="Mark Seam            ").clear = False
            col.operator("mesh.clear_seam", icon = 'CLEAR_SEAM', text="Clear Seam           ")

        else:
            col.separator()
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("mesh.mark_seam", icon = 'MARK_SEAM', text = "").clear = False
            row.operator("mesh.clear_seam", icon = 'CLEAR_SEAM', text = "")


class VIEW3D_PT_tools_meshedit_options(View3DPanel, Panel):
    bl_category = "Options"
    bl_context = "mesh_edit"
    bl_label = "Mesh Options"

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout

        ob = context.active_object

        tool_settings = context.tool_settings
        mesh = ob.data

        col = layout.column(align=True)
        col.prop(mesh, "use_mirror_x")

        row = col.row(align=True)
        row.active = ob.data.use_mirror_x
        row.prop(mesh, "use_mirror_topology")

        col = layout.column(align=True)
        col.label("Edge Select Mode:")
        col.prop(tool_settings, "edge_path_mode", text = "")
        col.prop(tool_settings, "edge_path_live_unwrap")
        col.label("Double Threshold:")
        col.prop(tool_settings, "double_threshold", text = "")

        if mesh.show_weight:
            col.label("Show Zero Weights:")
            col.row().prop(tool_settings, "vertex_group_user", expand=True)

# ********** default tools for editmode_curve ****************


class VIEW3D_PT_tools_curveedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "curve_edit"
    bl_label = "Curve Tools"

    def draw(self, context):
        layout = self.layout

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            col = layout.column(align=True) 
            col.operator("transform.tilt", icon = 'TILT', text="Tilt                  ")
            col.operator("transform.transform", icon = 'SHRINK_FATTEN', text="Shrink/Fatten  ").mode = 'CURVE_SHRINKFATTEN'
            col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror              ")

            col = layout.column(align=True)
            col.label(text="Curve:")
            col.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC', text="Toggle Cyclic  ")
            col.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION', text="Switch Direction")
            col.operator("curve.spline_type_set", icon = 'CURVE_DATA', text="Set Spline Type")
            col.operator("curve.radius_set", icon = 'RADIUS', text="Set Curve Radius")

            col = layout.column(align=True)
            col.label(text="Handles:")
            row = col.row(align=True)
            row.operator("curve.handle_type_set", icon = 'HANDLE_AUTO', text="Auto").type = 'AUTOMATIC'
            row.operator("curve.handle_type_set", icon = 'HANDLE_VECTOR', text="Vector").type = 'VECTOR'
            row = col.row(align=True)
            row.operator("curve.handle_type_set", icon = 'HANDLE_ALIGN',text="Align").type = 'ALIGNED'
            row.operator("curve.handle_type_set", icon = 'HANDLE_FREE', text="Free   ").type = 'FREE_ALIGN'

            col = layout.column(align=True)
            col.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS', text="Recalc Normals")

            col = layout.column(align=True)
            col.label(text="Modeling:")
            col.operator("curve.extrude_move", icon = 'EXTRUDE_REGION', text="Extrude            ")
            col.operator("curve.subdivide", icon = 'SUBDIVIDE_EDGES', text="Subdivide        ")
            col.operator("curve.smooth", icon = 'SHADING_SMOOTH', text="Smooth           ")

        else:

            row = layout.row(align=False)
            row.alignment = 'LEFT'
            row.operator("transform.tilt", icon = 'TILT', text = "")
            row.operator("transform.transform", icon = 'SHRINK_FATTEN', text = "").mode = 'CURVE_SHRINKFATTEN'
            row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")

            col = layout.column(align=True)
            col.label(text="Curve:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC', text = "")
            row.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION', text = "")
            row.operator("curve.spline_type_set", icon = 'CURVE_DATA', text = "")
            row.operator("curve.radius_set", icon = 'RADIUS', text = "")

            col = layout.column(align=True)
            col.label(text="Handles:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("curve.handle_type_set", icon = 'HANDLE_AUTO', text = "").type = 'AUTOMATIC'
            row.operator("curve.handle_type_set", icon = 'HANDLE_VECTOR',text = "").type = 'VECTOR'
            row.operator("curve.handle_type_set", icon = 'HANDLE_ALIGN',text = "").type = 'ALIGNED'
            row.operator("curve.handle_type_set", icon = 'HANDLE_FREE',text = "").type = 'FREE_ALIGN'

            col.separator()

            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("curve.normals_make_consistent", icon = 'RECALC_NORMALS', text = "")

            col = layout.column(align=True)
            col.label(text="Modeling:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("curve.extrude_move", icon = 'EXTRUDE_REGION', text = "")
            row.operator("curve.subdivide", icon = 'SUBDIVIDE_EDGES', text = "")
            row.operator("curve.smooth", icon = 'SHADING_SMOOTH', text = "")


class VIEW3D_PT_tools_add_curve_edit(View3DPanel, Panel):
    bl_category = "Create"
    bl_context = "curve_edit"
    bl_label = "Add Curves"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
        col = layout.column(align=True)

        # bfa - icon or text buttons
        if not view.show_iconbuttons: 
            VIEW3D_PT_tools_add_object.draw_add_curve(col, label=True) # the original class
        else:
            VIEW3D_PT_tools_add_object.draw_add_curve_icons(col, label=True) # the modified class with icon buttons


class VIEW3D_PT_tools_curveedit_options_stroke(View3DPanel, Panel):
    bl_category = "Options"
    bl_context = "curve_edit"
    bl_label = "Curve Stroke"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        cps = tool_settings.curve_paint_settings

        col = layout.column()

        col.prop(cps, "curve_type")

        if cps.curve_type == 'BEZIER':
            col.label("Bezier Options:")
            col.prop(cps, "error_threshold")
            col.prop(cps, "fit_method")
            col.prop(cps, "use_corners_detect")

            col = layout.column()
            col.active = cps.use_corners_detect
            col.prop(cps, "corner_angle")

        col.label("Pressure Radius:")
        row = layout.row(align=True)
        rowsub = row.row(align=True)
        rowsub.prop(cps, "radius_min", text="Min")
        rowsub.prop(cps, "radius_max", text="Max")

        row.prop(cps, "use_pressure_radius", text = "", icon_only=True)

        col = layout.column()
        col.label("Taper Radius:")
        row = layout.row(align=True)
        row.prop(cps, "radius_taper_start", text="Start")
        row.prop(cps, "radius_taper_end", text="End")

        col = layout.column()
        col.label("Projection Depth:")
        row = layout.row(align=True)
        row.prop(cps, "depth_mode", expand=True)

        col = layout.column()
        if cps.depth_mode == 'SURFACE':
            col.prop(cps, "surface_offset")
            col.prop(cps, "use_offset_absolute")
            col.prop(cps, "use_stroke_endpoints")
            if cps.use_stroke_endpoints:
                colsub = layout.column(align=True)
                colsub.prop(cps, "surface_plane", expand=True)


# ********** default tools for editmode_surface ****************


class VIEW3D_PT_tools_surfaceedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "surface_edit"
    bl_label = "Surface Tools"

    def draw(self, context):
        layout = self.layout

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            col = layout.column(align=True)
            col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror              ")
            col.label(text="Curve:")
            col.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC', text="Toggle Cyclic  ")
            col.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION', text="Switch Direction")

            col = layout.column(align=True)
            col.label(text="Modeling:")
            col.operator("curve.extrude", icon='EXTRUDE_REGION', text="Extrude           ")
            col.operator("curve.spin", icon = 'SPIN', text="Spin                 ")  
            col.operator("curve.subdivide", icon='SUBDIVIDE_EDGES', text="Subdivide        ")

        else:

            col = layout.column(align=True)
            row = col.row(align=False)
            row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")
            col.label(text="Curve:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("curve.cyclic_toggle", icon = 'TOGGLE_CYCLIC', text = "")
            row.operator("curve.switch_direction", icon = 'SWITCH_DIRECTION', text = "")

            col = layout.column(align=True)
            col.label(text="Modeling:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("curve.extrude", icon='EXTRUDE_REGION', text = "")
            row.operator("curve.spin", icon = 'SPIN', text = "")
            row.operator("curve.subdivide", icon='SUBDIVIDE_EDGES', text = "")


class VIEW3D_PT_tools_add_surface_edit(View3DPanel, Panel):
    bl_category = "Create"
    bl_context = "surface_edit"
    bl_label = "Add Surfaces"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
        col = layout.column(align=True)

        # bfa - icon or text buttons
        if not view.show_iconbuttons: 
            VIEW3D_PT_tools_add_object.draw_add_surface(col) # the original class
        else:
            VIEW3D_PT_tools_add_object.draw_add_surface_icons(col) # the modified class with icon buttons


# ********** default tools for editmode_text ****************


class VIEW3D_PT_tools_textedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "text_edit"
    bl_label = "Text Tools"

    def draw(self, context):
        layout = self.layout

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 
            col = layout.column(align=True)
            col.label(text="Set Case:")
            col.operator("font.case_set", icon = 'SET_UPPERCASE', text="To Upper          ").case = 'UPPER'
            col.operator("font.case_set", icon = 'SET_LOWERCASE', text="To Lower         ").case = 'LOWER'

            col = layout.column(align=True)
            col.label(text="Style:")
            col.operator("font.style_toggle", icon = 'BOLD', text="Bold                 ").style = 'BOLD'
            col.operator("font.style_toggle", icon = 'ITALIC', text="Italic                ").style = 'ITALIC'
            col.operator("font.style_toggle", icon = 'UNDERLINED', text="Underline         ").style = 'UNDERLINE'
            col.operator("font.style_toggle", text="Toggle Small Caps", icon = "SMALL_CAPS").style = 'SMALL_CAPS'

        else: 
            col = layout.column(align=True)
            col.label(text="Set Case:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("font.case_set", icon = 'SET_UPPERCASE', text = "").case = 'UPPER'
            row.operator("font.case_set", icon = 'SET_LOWERCASE', text = "").case = 'LOWER'

            col = layout.column(align=True)
            col.label(text="Style:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("font.style_toggle", icon = 'BOLD', text = "").style = 'BOLD'
            row.operator("font.style_toggle", icon = 'ITALIC', text = "").style = 'ITALIC'
            row.operator("font.style_toggle", icon = 'UNDERLINED', text = "").style = 'UNDERLINE'
            row.operator("font.style_toggle", text = "", icon = "SMALL_CAPS").style = 'SMALL_CAPS'


# ********** default tools for editmode_armature ****************


class VIEW3D_PT_tools_armatureedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "armature_edit"
    bl_label = "Armature Tools"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 
            col = layout.column(align=True)
            col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror                   ")
            col = layout.column(align=True)
            col.label(text="Bones:")
            col.operator("armature.bone_primitive_add", icon = 'BONE_DATA', text="Add                      ")
            col.operator("armature.merge", text="Merge Bones        ", icon = "MERGE")
            col.operator("armature.fill", text="Fill between Joints", icon = "FILLBETWEEN")
            col.operator("armature.split",  text="Split                     ", icon = "SPLIT")
            col.operator("armature.separate", text="Separate                ", icon = "SEPARATE")
            col.operator("armature.switch_direction", text="Switch Direction  ", icon = "SWITCH_DIRECTION")

            col = layout.column(align=True)
            col.label(text="Modeling:")
            col.operator("armature.extrude_move", icon = 'EXTRUDE_REGION', text="Extrude                ")
            col.operator("armature.subdivide", icon = 'SUBDIVIDE_EDGES', text="Subdivide            ")

        else:
            col = layout.column(align=True)
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")
            col = layout.column(align=True)
            col.label(text="Bones:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("armature.bone_primitive_add", icon = 'BONE_DATA', text = "")
            row.operator("armature.merge", text = "", icon = "MERGE")
            row.operator("armature.fill", text = "", icon = "FILLBETWEEN")
            row.operator("armature.split", text = "", icon = "SPLIT")

            col = layout.column(align=True)
            row = col.row(align=False)
            row.alignment = 'LEFT'

            row.operator("armature.separate", text = "", icon = "SEPARATE")
            row.operator("armature.switch_direction", text="", icon = "SWITCH_DIRECTION")

            col = layout.column(align=True)
            col.label(text="Modeling:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("armature.extrude_move", icon = 'EXTRUDE_REGION', text = "")
            row.operator("armature.subdivide", icon = 'SUBDIVIDE_EDGES', text = "")


class VIEW3D_PT_tools_armatureedit_options(View3DPanel, Panel):
    bl_category = "Options"
    bl_context = "armature_edit"
    bl_label = "Armature Options"

    def draw(self, context):
        arm = context.active_object.data

        self.layout.prop(arm, "use_mirror_x")


# ********** default tools for editmode_mball ****************


class VIEW3D_PT_tools_mballedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "mball_edit"
    bl_label = "Meta Tools"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            col = layout.column(align=True)
            col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror                ")

        else:
            
            col = layout.column(align=True)
            row = col.row(align=False)
            row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")


class VIEW3D_PT_tools_add_mball_edit(View3DPanel, Panel):
    bl_category = "Create"
    bl_context = "mball_edit"
    bl_label = "Add Metaball"

    def draw(self, context):
        layout = self.layout
        scene = context.scene # Our data is in the current scene
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        col = layout.column(align=True)

        # bfa - icon or text buttons
        if not view.show_iconbuttons: 
            VIEW3D_PT_tools_add_object.draw_add_mball(col) # the original class
        else:
            VIEW3D_PT_tools_add_object.draw_add_mball_icons(col) # the modified class with icon buttons


# ********** default tools for editmode_lattice ****************


class VIEW3D_PT_tools_latticeedit(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "lattice_edit"
    bl_label = "Lattice Tools"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            col = layout.column(align=True)
            col.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="Mirror                   ")
            col.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP", text = "Mirror Vertex Group    ")
            col.operator("lattice.make_regular", icon = 'MAKE_REGULAR', text = "Make Regular  ")

        else:
            col = layout.column(align=True)

            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text = "")
            row.operator("object.vertex_group_mirror", icon = "MIRROR_VERTEXGROUP", text = "")
            row.operator("lattice.make_regular", icon = 'MAKE_REGULAR', text = "")
           


# ********** default tools for pose-mode ****************


class VIEW3D_PT_tools_posemode(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "posemode"
    bl_label = "Pose Tools"

    def draw(self, context):
        layout = self.layout
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons: 

            col = layout.column(align=True)
            col.label(text="In-Between:")
            row = col.row(align=True)
            row.operator("pose.push", icon = 'PUSH_POSE', text="Push")
            row.operator("pose.relax", icon = 'RELAX_POSE',text="Relax")
            col.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE',text="Breakdowner  ")

            col = layout.column(align=True)
            col.label(text="Pose:")
            row = col.row(align=True)

            row = layout.row(align=True)
            row.operator("pose.propagate", text="Propagate")

            # bfa - Double menu entry. But stays available for further modifications
            #col = layout.column(align=True)
            #col.operator("poselib.pose_add", icon = 'ADD_TO_LIBRARY', text="Add To Library")

            draw_keyframing_tools(context, layout)

            col = layout.column(align=True)
            col.label(text="Motion Paths:")
            row = col.row(align=True)
            row.operator("pose.paths_calculate", icon ='MOTIONPATHS_CALCULATE', text="Calculate")
            row.operator("pose.paths_clear", icon ='MOTIONPATHS_CLEAR', text="Clear")

        else:
            col = layout.column(align=True)
            col.label(text="In-Between:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("pose.push", icon = 'PUSH_POSE', text = "")
            row.operator("pose.relax", icon = 'RELAX_POSE',text = "")
            row.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE',text = "")

            col = layout.column(align=True)
            col.label(text="Pose:")

            # bfa - Double menu entry. But stays available for further modifications
            #row = col.row(align=False)
            #row.operator("poselib.pose_add", icon = 'ADD_TO_LIBRARY', text = "")

            row = col.row(align=True)
            row.operator("pose.propagate", text="Propagate")

            draw_keyframing_tools_icons(context, layout)

            col = layout.column(align=True)
            col.label(text="Motion Paths:")
            row = col.row(align=False)
            row.alignment = 'LEFT'
            row.operator("pose.paths_calculate", icon ='MOTIONPATHS_CALCULATE', text = "")
            row.operator("pose.paths_clear", icon ='MOTIONPATHS_CLEAR', text = "")


class VIEW3D_PT_tools_posemode_options(View3DPanel, Panel):
    bl_category = "Options"
    bl_context = "posemode"
    bl_label = "Pose Options"

    def draw(self, context):
        arm = context.active_object.data

        self.layout.prop(arm, "use_auto_ik")

# ********** default tools for paint modes ****************


class View3DPaintPanel(UnifiedPaintPanel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'


class VIEW3D_PT_imapaint_tools_missing(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Missing Data"

    @classmethod
    def poll(cls, context):
        toolsettings = context.tool_settings.image_paint
        return context.image_paint_object and not toolsettings.detect_data()

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings.image_paint

        col = layout.column()
        col.label("Missing Data", icon='ERROR')
        if toolsettings.missing_uvs:
            col.separator()
            col.label("Missing UVs", icon='INFO')
            col.label("Unwrap the mesh in edit mode or generate a simple UV layer")
            col.operator("paint.add_simple_uvs")

        if toolsettings.mode == 'MATERIAL':
            if toolsettings.missing_materials:
                col.separator()
                col.label("Missing Materials", icon='INFO')
                col.label("Add a material and paint slot below")
                col.operator_menu_enum("paint.add_texture_paint_slot", "type", text="Add Paint Slot")
            elif toolsettings.missing_texture:
                ob = context.active_object
                mat = ob.active_material

                col.separator()
                if mat:
                    col.label("Missing Texture Slots", icon='INFO')
                    col.label("Add a paint slot below")
                    col.operator_menu_enum("paint.add_texture_paint_slot", "type", text="Add Paint Slot")
                else:
                    col.label("Missing Materials", icon='INFO')
                    col.label("Add a material and paint slot below")
                    col.operator_menu_enum("paint.add_texture_paint_slot", "type", text="Add Paint Slot")

        elif toolsettings.mode == 'IMAGE':
            if toolsettings.missing_texture:
                col.separator()
                col.label("Missing Canvas", icon='INFO')
                col.label("Add or assign a canvas image below")
                col.label("Canvas Image:")
                # todo this should be combinded into a single row
                col.template_ID(toolsettings, "canvas", open="image.open")
                col.operator("image.new", text="New").gen_context = 'PAINT_CANVAS'

        if toolsettings.missing_stencil:
            col.separator()
            col.label("Missing Stencil", icon='INFO')
            col.label("Add or assign a stencil image below")
            col.label("Stencil Image:")
            # todo this should be combinded into a single row
            col.template_ID(toolsettings, "stencil_image", open="image.open")
            col.operator("image.new", text="New").gen_context = 'PAINT_STENCIL'


class VIEW3D_PT_tools_brush(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Brush"

    @classmethod
    def poll(cls, context):
        return cls.paint_settings(context)

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        settings = self.paint_settings(context)
        brush = settings.brush

        obj = context.active_object
        mode = obj.mode   

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences

        if not context.particle_edit_object:
            col = layout.split().column()
            col.template_ID_preview(settings, "brush", new="brush.add", rows=3, cols=8)

        # Particle Mode #
        if context.particle_edit_object:
            tool = settings.tool

            layout.column().prop(settings, "tool", expand=True)

            if tool != 'NONE':
                col = layout.column()
                col.prop(brush, "size", slider=True)

                myvar = layout.operator("wm.radial_control", text = "Radial Control Size")
                myvar.data_path_primary = 'tool_settings.particle_edit.brush.size'

                if tool != 'ADD':
                    col.prop(brush, "strength", slider=True)

                    myvar = layout.operator("wm.radial_control", text = "Radial Control Strength")
                    myvar.data_path_primary = 'tool_settings.particle_edit.brush.strength'

            if tool == 'ADD':
                col.prop(brush, "count")
                col = layout.column()
                col.prop(settings, "use_default_interpolate")
                col.prop(brush, "steps", slider=True)
                col.prop(settings, "default_key_count", slider=True)
            elif tool == 'LENGTH':
                layout.row().prop(brush, "length_mode", expand=True)
            elif tool == 'PUFF':
                layout.row().prop(brush, "puff_mode", expand=True)
                layout.prop(brush, "use_puff_volume")

        # Sculpt Mode #

        elif context.sculpt_object and brush:
            capabilities = brush.sculpt_capabilities

            col = layout.column()

            col.separator()

            row = col.row(align=True)

            ups = toolsettings.unified_paint_settings
            if ((ups.use_unified_size and ups.use_locked_size) or
                    ((not ups.use_unified_size) and brush.use_locked_size)):
                self.prop_unified_size(row, context, brush, "use_locked_size", icon='LOCKED')
                self.prop_unified_size(row, context, brush, "unprojected_radius", slider=True, text="Radius")
            else:
                self.prop_unified_size(row, context, brush, "use_locked_size", icon='UNLOCKED')
                self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")

            self.prop_unified_size(row, context, brush, "use_pressure_size")

            # strength, use_strength_pressure, and use_strength_attenuation
            col.separator()
            row = col.row(align=True)

            if capabilities.has_space_attenuation:
                row.prop(brush, "use_space_attenuation", toggle=True, icon_only=True)

            self.prop_unified_strength(row, context, brush, "strength", text="Strength")

            if capabilities.has_strength_pressure:
                self.prop_unified_strength(row, context, brush, "use_pressure_strength")

            # auto_smooth_factor and use_inverse_smooth_pressure
            if capabilities.has_auto_smooth:
                col.separator()

                row = col.row(align=True)
                row.prop(brush, "auto_smooth_factor", slider=True)
                row.prop(brush, "use_inverse_smooth_pressure", toggle=True, text = "")

            # normal_weight
            if capabilities.has_normal_weight:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "normal_weight", slider=True)

            # crease_pinch_factor
            if capabilities.has_pinch_factor:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "crease_pinch_factor", slider=True, text="Pinch")

            # rake_factor
            if capabilities.has_rake_factor:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "rake_factor", slider=True)
                
                        # direction
            col.separator()
            col.row().prop(brush, "direction", expand=True)
            col.separator()

            # use_original_normal and sculpt_plane
            if capabilities.has_sculpt_plane:

                row = col.row(align=True)

                row.prop(brush, "use_original_normal", toggle=True, icon_only=True)

                row.prop(brush, "sculpt_plane", text = "")
                
                col.separator()

            if brush.sculpt_tool == 'MASK':
                col.prop(brush, "mask_tool", text = "")

            # plane_offset, use_offset_pressure, use_plane_trim, plane_trim
            if capabilities.has_plane_offset:
                row = col.row(align=True)
                row.prop(brush, "plane_offset", slider=True)
                row.prop(brush, "use_offset_pressure", text = "")

                col.separator()

                row = col.row()
                row.prop(brush, "use_plane_trim", text="Trim")
                
                if brush.use_plane_trim:                
                    row = col.row()
                    row.active = brush.use_plane_trim
                    row.prop(brush, "plane_trim", slider=True, text="Distance")

            # height
            if capabilities.has_height:
                row = col.row()
                row.prop(brush, "height", slider=True, text="Height")

            # use_frontface
            row = col.row()
            row.prop(brush, "use_frontface", text="Front Faces Only")          

            # use_accumulate
            if capabilities.has_accumulate:

                col.prop(brush, "use_accumulate")

            # use_persistent, set_persistent_base
            if capabilities.has_persistence:
                col.separator()

                ob = context.sculpt_object
                do_persistent = True

                # not supported yet for this case
                for md in ob.modifiers:
                    if md.type == 'MULTIRES':
                        do_persistent = False
                        break

                if do_persistent:
                    col.prop(brush, "use_persistent")
                    col.operator("sculpt.set_persistent_base")

        # Texture Paint Mode #

        elif context.image_paint_object and brush:
            brush_texpaint_common(self, context, layout, brush, settings, True)

        # Weight Paint Mode #
        elif context.weight_paint_object and brush:

            col = layout.column()

            row = col.row(align=True)
            self.prop_unified_weight(row, context, brush, "weight", slider=True, text="Weight")

            row = col.row(align=True)
            self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
            self.prop_unified_size(row, context, brush, "use_pressure_size")

            row = col.row(align=True)
            self.prop_unified_strength(row, context, brush, "strength", text="Strength")
            self.prop_unified_strength(row, context, brush, "use_pressure_strength")

            col.prop(brush, "vertex_tool", text="Blend")
            
            row = col.row(align=True)

            if brush.vertex_tool != 'SMEAR':
                row.prop(brush, "use_accumulate")

            row.prop(toolsettings, "use_auto_normalize", text="Auto Normalize")
            row.prop(toolsettings, "use_multipaint", text="Multi-Paint")

        # Vertex Paint Mode #
        elif context.vertex_paint_object and brush:
            col = layout.column()

            #Hidable color picker dialog
            if not addon_prefs.brushpanel_hide_colorpicker:
                self.prop_unified_color_picker(col, context, brush, "color", value_slider=True)

            if settings.palette:
                col.template_palette(settings, "palette", color=True)

            row = col.row(align=True)
            self.prop_unified_color(row, context, brush, "color", text="")
            self.prop_unified_color(row, context, brush, "secondary_color", text="")
            row.separator()

            row.operator("paint.brush_colors_flip", icon='FILE_REFRESH', text="")
            row.operator("paint.sample_color", icon='EYEDROPPER', text = "") # And finally the eyedropper

            col.separator()
            row = col.row(align=True)
            self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
            self.prop_unified_size(row, context, brush, "use_pressure_size")

            row = col.row(align=True)
            self.prop_unified_strength(row, context, brush, "strength", text="Strength")
            self.prop_unified_strength(row, context, brush, "use_pressure_strength")

            # XXX - TODO
            # row = col.row(align=True)
            # row.prop(brush, "jitter", slider=True)
            # row.prop(brush, "use_pressure_jitter", toggle=True, text = "")

            col.separator()
            col.prop(brush, "vertex_tool", text="Blend")

            row = col.row(align=True)
            row.prop(brush, "use_accumulate")
            row.prop(brush, "use_alpha")

            # Hidable palette settings
            if not addon_prefs.brushpanel_hide_palette:
                col.separator()
                col.template_ID(settings, "palette", new="palette.new")

        # Options just for vertex and texture paint
        if mode != 'WEIGHT_PAINT':

            if not addon_prefs.brushpanel_display_options:
                layout.prop(addon_prefs,"brushpanel_display_options", emboss=False, icon="SETUP", text=" ")

            else:
                layout.prop(addon_prefs,"brushpanel_display_options", emboss=False, icon="SETUP", text="Display Options")

                layout.prop(addon_prefs, "brushpanel_hide_colorpicker")
                layout.prop(addon_prefs, "brushpanel_hide_palette")
            


class TEXTURE_UL_texpaintslots(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = data

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text = "", emboss=False, icon_value=icon)
            if (not mat.use_nodes) and context.scene.render.engine in {'BLENDER_RENDER', 'BLENDER_GAME'}:
                mtex_index = mat.texture_paint_slots[index].index
                layout.prop(mat, "use_textures", text = "", index=mtex_index)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text = "")


class VIEW3D_MT_tools_projectpaint_uvlayer(Menu):
    bl_label = "Clone Layer"

    def draw(self, context):
        layout = self.layout

        for i, tex in enumerate(context.active_object.data.uv_textures):
            props = layout.operator("wm.context_set_int", text=tex.name, translate=False)
            props.data_path = "active_object.data.uv_textures.active_index"
            props.value = i


class VIEW3D_PT_slots_projectpaint(View3DPanel, Panel):
    bl_context = "imagepaint"
    bl_label = "Slots"
    bl_category = "Slots"

    @classmethod
    def poll(cls, context):
        brush = context.tool_settings.image_paint.brush
        ob = context.active_object
        return (brush is not None and ob is not None)

    def draw(self, context):
        layout = self.layout

        settings = context.tool_settings.image_paint
        # brush = settings.brush

        ob = context.active_object
        col = layout.column()

        col.label("Painting Mode:")
        col.prop(settings, "mode", text = "")
        col.separator()

        if settings.mode == 'MATERIAL':
            if len(ob.material_slots) > 1:
                col.label("Materials:")
                col.template_list("MATERIAL_UL_matslots", "layers",
                                  ob, "material_slots",
                                  ob, "active_material_index", rows=2)

            mat = ob.active_material
            if mat:
                col.label("Available Paint Slots:")
                col.template_list("TEXTURE_UL_texpaintslots", "",
                                  mat, "texture_paint_images",
                                  mat, "paint_active_slot", rows=2)

                if mat.texture_paint_slots:
                    slot = mat.texture_paint_slots[mat.paint_active_slot]
                else:
                    slot = None

                if (not mat.use_nodes) and context.scene.render.engine in {'BLENDER_RENDER', 'BLENDER_GAME'}:
                    row = col.row(align=True)
                    row.operator_menu_enum("paint.add_texture_paint_slot", "type")
                    row.operator("paint.delete_texture_paint_slot", text = "", icon='X')

                    if slot:
                        col.prop(mat.texture_slots[slot.index], "blend_type")
                        col.separator()

                if slot and slot.index != -1:
                    col.label("UV Map:")
                    col.prop_search(slot, "uv_layer", ob.data, "uv_textures", text = "")

        elif settings.mode == 'IMAGE':
            mesh = ob.data
            uv_text = mesh.uv_textures.active.name if mesh.uv_textures.active else ""
            col.label("Canvas Image:")
            # todo this should be combinded into a single row
            col.template_ID(settings, "canvas", open="image.open")
            col.operator("image.new", text="New").gen_context = 'PAINT_CANVAS'
            col.label("UV Map:")
            col.menu("VIEW3D_MT_tools_projectpaint_uvlayer", text=uv_text, translate=False)

        col.separator()
        col.operator("image.save_dirty", text="Save All Images")


class VIEW3D_PT_stencil_projectpaint(View3DPanel, Panel):
    bl_context = "imagepaint"
    bl_label = "Mask"
    bl_category = "Slots"

    @classmethod
    def poll(cls, context):
        brush = context.tool_settings.image_paint.brush
        ob = context.active_object
        return (brush is not None and ob is not None)

    def draw_header(self, context):
        ipaint = context.tool_settings.image_paint
        self.layout.prop(ipaint, "use_stencil_layer", text = "")

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        ipaint = toolsettings.image_paint
        ob = context.active_object
        mesh = ob.data

        col = layout.column()
        col.active = ipaint.use_stencil_layer

        stencil_text = mesh.uv_texture_stencil.name if mesh.uv_texture_stencil else ""
        col.label("UV Map:")
        col.menu("VIEW3D_MT_tools_projectpaint_stencil", text=stencil_text, translate=False)

        col.label("Stencil Image:")
        # todo this should be combinded into a single row
        col.template_ID(ipaint, "stencil_image", open="image.open")
        col.operator("image.new", text="New").gen_context = 'PAINT_STENCIL'

        col.label("Visualization:")
        row = col.row(align=True)
        row.prop(ipaint, "stencil_color", text = "")
        row.prop(ipaint, "invert_stencil", text = "", icon='IMAGE_ALPHA')


class VIEW3D_PT_tools_brush_overlay(Panel, View3DPaintPanel):
    bl_category = "Options"
    bl_label = "Overlay"

    @classmethod
    def poll(cls, context):
        settings = cls.paint_settings(context)
        return (settings and
                settings.brush and
                (context.sculpt_object or
                 context.vertex_paint_object or
                 context.weight_paint_object or
                 context.image_paint_object))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush
        tex_slot = brush.texture_slot
        tex_slot_mask = brush.mask_texture_slot

        col = layout.column()

        col.label(text="Curve:")

        row = col.row(align=True)
        if brush.use_cursor_overlay:
            row.prop(brush, "use_cursor_overlay", toggle=True, text = "", icon='RESTRICT_VIEW_OFF')
        else:
            row.prop(brush, "use_cursor_overlay", toggle=True, text = "", icon='RESTRICT_VIEW_ON')

        sub = row.row(align=True)
        sub.prop(brush, "cursor_overlay_alpha", text="Alpha")
        sub.prop(brush, "use_cursor_overlay_override", toggle=True, text = "", icon='BRUSH_DATA')

        col.active = brush.brush_capabilities.has_overlay

        if context.image_paint_object or context.sculpt_object or context.vertex_paint_object:
            col.label(text="Texture:")
            row = col.row(align=True)
            if tex_slot.map_mode != 'STENCIL':
                if brush.use_primary_overlay:
                    row.prop(brush, "use_primary_overlay", toggle=True, text = "", icon='RESTRICT_VIEW_OFF')
                else:
                    row.prop(brush, "use_primary_overlay", toggle=True, text = "", icon='RESTRICT_VIEW_ON')

            sub = row.row(align=True)
            sub.prop(brush, "texture_overlay_alpha", text="Alpha")
            sub.prop(brush, "use_primary_overlay_override", toggle=True, text = "", icon='BRUSH_DATA')

        if context.image_paint_object:
            col.label(text="Mask Texture:")

            row = col.row(align=True)
            if tex_slot_mask.map_mode != 'STENCIL':
                if brush.use_secondary_overlay:
                    row.prop(brush, "use_secondary_overlay", toggle=True, text = "", icon='RESTRICT_VIEW_OFF')
                else:
                    row.prop(brush, "use_secondary_overlay", toggle=True, text = "", icon='RESTRICT_VIEW_ON')

            sub = row.row(align=True)
            sub.prop(brush, "mask_overlay_alpha", text="Alpha")
            sub.prop(brush, "use_secondary_overlay_override", toggle=True, text = "", icon='BRUSH_DATA')


class VIEW3D_PT_tools_brush_texture(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Texture"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = cls.paint_settings(context)
        return (settings and settings.brush and
                (context.sculpt_object or context.image_paint_object or context.vertex_paint_object))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush

        col = layout.column()

        col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

        brush_texture_settings(col, brush, context.sculpt_object)


class VIEW3D_PT_tools_mask_texture(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_context = "imagepaint"
    bl_label = "Texture Mask"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = cls.paint_settings(context)
        return (settings and settings.brush and context.image_paint_object)

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.image_paint.brush

        col = layout.column()

        col.template_ID_preview(brush, "mask_texture", new="texture.new", rows=3, cols=8)

        brush_mask_texture_settings(col, brush)


class VIEW3D_PT_tools_brush_stroke(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Stroke"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = cls.paint_settings(context)
        return (settings and
                settings.brush and
                (context.sculpt_object or
                 context.vertex_paint_object or
                 context.weight_paint_object or
                 context.image_paint_object))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush

        col = layout.column()

        col.label(text="Stroke Method:")

        col.prop(brush, "stroke_method", text = "")

        if brush.use_anchor:
            col.separator()
            col.prop(brush, "use_edge_to_edge", "Edge To Edge")

        if brush.use_airbrush:
            col.separator()
            col.prop(brush, "rate", text="Rate", slider=True)

        if brush.use_space:
            col.separator()
            row = col.row(align=True)
            row.prop(brush, "spacing", text="Spacing")
            row.prop(brush, "use_pressure_spacing", toggle=True, text = "")

        if brush.use_line or brush.use_curve:
            col.separator()
            row = col.row(align=True)
            row.prop(brush, "spacing", text="Spacing")

        if brush.use_curve:
            col.separator()
            col.operator("paintcurve.add_point_slide")
            col.template_ID(brush, "paint_curve", new="paintcurve.new")
            col.operator("paintcurve.draw")

        if context.sculpt_object:
            if brush.sculpt_capabilities.has_jitter:
                col.separator()

                row = col.row(align=True)
                row.prop(brush, "use_relative_jitter", icon_only=True)
                if brush.use_relative_jitter:
                    row.prop(brush, "jitter", slider=True)
                else:
                    row.prop(brush, "jitter_absolute")
                row.prop(brush, "use_pressure_jitter", toggle=True, text = "")

            if brush.sculpt_capabilities.has_smooth_stroke:
                col = layout.column()
                col.separator()

                col.prop(brush, "use_smooth_stroke")
                
                if brush.use_smooth_stroke:

                    sub = col.column()
                    sub.active = brush.use_smooth_stroke
                    sub.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
                    sub.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)
                    
                    layout.prop(settings, "input_samples")
                    
        else:
            col.separator()

            row = col.row(align=True)
            row.prop(brush, "use_relative_jitter", icon_only=True)
            if brush.use_relative_jitter:
                row.prop(brush, "jitter", slider=True)
            else:
                row.prop(brush, "jitter_absolute")
            row.prop(brush, "use_pressure_jitter", toggle=True, text = "")

            col = layout.column()
            col.separator()

            if brush.brush_capabilities.has_smooth_stroke:
                col.prop(brush, "use_smooth_stroke")
                
                if brush.use_smooth_stroke:

                    sub = col.column()
                    sub.active = brush.use_smooth_stroke
                    sub.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
                    sub.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)

                    layout.prop(settings, "input_samples")


class VIEW3D_PT_tools_brush_curve(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Curve"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = cls.paint_settings(context)
        return (settings and settings.brush and settings.brush.curve)

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)

        brush = settings.brush

        layout.template_curve_mapping(brush, "curve", brush=True)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("brush.curve_preset", icon='SMOOTHCURVE', text = "").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon='SPHERECURVE', text = "").shape = 'ROUND'
        row.operator("brush.curve_preset", icon='ROOTCURVE', text = "").shape = 'ROOT'
        row.operator("brush.curve_preset", icon='SHARPCURVE', text = "").shape = 'SHARP'
        row.operator("brush.curve_preset", icon='LINCURVE', text = "").shape = 'LINE'
        row.operator("brush.curve_preset", icon='NOCURVE', text = "").shape = 'MAX'


class VIEW3D_PT_sculpt_dyntopo(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Dyntopo"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.sculpt_object and context.tool_settings.sculpt)

    def draw_header(self, context):
        layout = self.layout
        layout.operator(
                "sculpt.dynamic_topology_toggle",
                icon='CHECKBOX_HLT' if context.sculpt_object.use_dynamic_topology_sculpting else 'CHECKBOX_DEHLT',
                text = "",
                emboss=False,
                )

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        sculpt = toolsettings.sculpt
        settings = self.paint_settings(context)
        brush = settings.brush

        layout.operator("sculpt.set_detail_size", text="Set detail size")

        col = layout.column()
        col.active = context.sculpt_object.use_dynamic_topology_sculpting
        sub = col.column(align=True)
        sub.active = (brush and brush.sculpt_tool != 'MASK')
        if (sculpt.detail_type_method == 'CONSTANT'):
            row = sub.row(align=True)
            row.prop(sculpt, "constant_detail_resolution")
            row.operator("sculpt.sample_detail_size", text = "", icon='EYEDROPPER')
        elif (sculpt.detail_type_method == 'BRUSH'):
            sub.prop(sculpt, "detail_percent")
        else:
            sub.prop(sculpt, "detail_size")
        sub.prop(sculpt, "detail_refine_method", text = "")
        sub.prop(sculpt, "detail_type_method", text = "")
        col.separator()
        col.prop(sculpt, "use_smooth_shading")
        col.operator("sculpt.optimize")
        if (sculpt.detail_type_method == 'CONSTANT'):
            col.operator("sculpt.detail_flood_fill")
        col.separator()
        col.prop(sculpt, "symmetrize_direction")
        col.operator("sculpt.symmetrize")


class VIEW3D_PT_sculpt_options(Panel, View3DPaintPanel):
    bl_category = "Options"
    bl_label = "Options"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.sculpt_object and context.tool_settings.sculpt)

    def draw(self, context):
        layout = self.layout
        # scene = context.scene

        toolsettings = context.tool_settings
        sculpt = toolsettings.sculpt
        capabilities = sculpt.brush.sculpt_capabilities

        col = layout.column(align=True)
        col.active = capabilities.has_gravity
        col.label(text="Dab Gravity:")
        col.prop(sculpt, "gravity", slider=True, text="Factor")
        col.prop(sculpt, "gravity_object")

        layout.label(text = "Performance:")

        layout.prop(sculpt, "use_threaded", text="Threaded Sculpt")
        layout.prop(sculpt, "show_low_resolution")
        layout.prop(sculpt, "use_deform_only")
        
        layout.label(text = "Misc:")
        
        layout.prop(sculpt, "show_diffuse_color")
        layout.prop(sculpt, "show_mask")

        self.unified_paint_settings(layout, context)

        # brush paint modes
        layout.label("Enabled Brush Modes:")
        layout.menu("VIEW3D_MT_brush_paint_modes")


class VIEW3D_PT_sculpt_symmetry(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_label = "Symmetry/Lock"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.sculpt_object and context.tool_settings.sculpt)

    def draw(self, context):
        layout = self.layout

        sculpt = context.tool_settings.sculpt

        col = layout.column(align=True)
        col.label(text="Mirror:")
        row = col.row(align=True)
        row.prop(sculpt, "use_symmetry_x", text="X", toggle=True)
        row.prop(sculpt, "use_symmetry_y", text="Y", toggle=True)
        row.prop(sculpt, "use_symmetry_z", text="Z", toggle=True)

        layout.column().prop(sculpt, "radial_symmetry", text="Radial")
        layout.prop(sculpt, "use_symmetry_feather", text="Feather")

        layout.label(text="Lock:")

        row = layout.row(align=True)
        row.prop(sculpt, "lock_x", text="X", toggle=True)
        row.prop(sculpt, "lock_y", text="Y", toggle=True)
        row.prop(sculpt, "lock_z", text="Z", toggle=True)

        layout.label(text="Tiling:")

        row = layout.row(align=True)
        row.prop(sculpt, "tile_x", text="X", toggle=True)
        row.prop(sculpt, "tile_y", text="Y", toggle=True)
        row.prop(sculpt, "tile_z", text="Z", toggle=True)

        layout.column().prop(sculpt, "tile_offset", text="Tile Offset")


class VIEW3D_PT_tools_brush_appearance(Panel, View3DPaintPanel):
    bl_category = "Options"
    bl_label = "Appearance"

    @classmethod
    def poll(cls, context):
        settings = cls.paint_settings(context)
        return (settings is not None) and (not isinstance(settings, bpy.types.ParticleEdit))

    def draw(self, context):
        layout = self.layout

        settings = self.paint_settings(context)
        brush = settings.brush

        if brush is None:  # unlikely but can happen
            layout.label(text="Brush Unset")
            return

        col = layout.column()
        col.prop(settings, "show_brush")

        sub = col.column()
        sub.active = settings.show_brush

        if context.sculpt_object and context.tool_settings.sculpt:
            if brush.sculpt_capabilities.has_secondary_color:
                sub.row().prop(brush, "cursor_color_add", text="Add")
                sub.row().prop(brush, "cursor_color_subtract", text="Subtract")
            else:
                sub.prop(brush, "cursor_color_add", text = "")
        else:
            sub.prop(brush, "cursor_color_add", text = "")

        col.separator()

        col = col.column(align=True)
        col.prop(brush, "use_custom_icon", text = "Custom Brush Icon")
        sub = col.column()
        sub.active = brush.use_custom_icon
        sub.prop(brush, "icon_filepath", text = "")

# ********** default tools for weight-paint ****************


class VIEW3D_PT_tools_weightpaint(View3DPanel, Panel):
    bl_category = "Tools"
    bl_context = "weightpaint"
    bl_label = "Weight Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene # Our data for the icon_or_text flag is in the current scene
        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop

        if not view.show_iconbuttons:
            VIEW3D_PT_tools_meshweight.draw_generic(layout)

            col = layout.column()
            col.operator("paint.weight_gradient", icon = 'WEIGHT_GRADIENT')
            props = col.operator("object.data_transfer", icon = 'WEIGHT_TRANSFER_WEIGHTS', text="Transfer Weights")
            props.use_reverse_transfer = True
            props.data_type = 'VGROUP_WEIGHTS'
            
        else:
            VIEW3D_PT_tools_meshweight.draw_generic_icons(layout)

class VIEW3D_PT_tools_weightpaint_symmetry(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_context = "weightpaint"
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Symmetry"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings
        wpaint = toolsettings.weight_paint
        draw_vpaint_symmetry(layout, wpaint)


class VIEW3D_PT_tools_weightpaint_options(Panel, View3DPaintPanel):
    bl_category = "Options"
    bl_context = "weightpaint"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        wpaint = tool_settings.weight_paint

        col = layout.column()
        col.prop(wpaint, "use_group_restrict")

        obj = context.weight_paint_object
        if obj.type == 'MESH':
            mesh = obj.data
            col.prop(mesh, "use_mirror_x")
            row = col.row()
            row.active = mesh.use_mirror_x
            row.prop(mesh, "use_mirror_topology")

        col.label("Show Zero Weights:")
        sub = col.row()
        sub.prop(tool_settings, "vertex_group_user", expand=True)

        self.unified_paint_settings(col, context)

        # brush paint modes
        layout.label("Enabled Brush Modes:")
        layout.menu("VIEW3D_MT_brush_paint_modes")

# ********** default tools for vertex-paint ****************


class VIEW3D_PT_tools_vertexpaint(Panel, View3DPaintPanel):
    bl_category = "Options"
    bl_context = "vertexpaint"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        vpaint = toolsettings.vertex_paint

        col = layout.column()

        self.unified_paint_settings(col, context)

        # brush paint modes
        layout.label("Enabled Brush Modes:")
        layout.menu("VIEW3D_MT_brush_paint_modes")


class VIEW3D_PT_tools_vertexpaint_symmetry(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_context = "vertexpaint"
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Symmetry"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings
        vpaint = toolsettings.vertex_paint
        draw_vpaint_symmetry(layout, vpaint)


# ********** default tools for texture-paint ****************


class VIEW3D_PT_tools_imagepaint_external(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_context = "imagepaint"
    bl_label = "External"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        ipaint = toolsettings.image_paint

        col = layout.column()
        row = col.split(align=True, percentage=0.55)
        row.operator("image.project_edit", text="Quick Edit")
        row.operator("image.project_apply", text="Apply")

        col.row().prop(ipaint, "screen_grab_size", text = "")

        col.operator("paint.project_image", text="Apply Camera Image")


class VIEW3D_PT_tools_imagepaint_symmetry(Panel, View3DPaintPanel):
    bl_category = "Tools"
    bl_context = "imagepaint"
    bl_label = "Symmetry"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        ipaint = toolsettings.image_paint

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(ipaint, "use_symmetry_x", text="X", toggle=True)
        row.prop(ipaint, "use_symmetry_y", text="Y", toggle=True)
        row.prop(ipaint, "use_symmetry_z", text="Z", toggle=True)


class VIEW3D_PT_tools_projectpaint(View3DPaintPanel, Panel):
    bl_category = "Options"
    bl_context = "imagepaint"
    bl_label = "Project Paint"

    @classmethod
    def poll(cls, context):
        brush = context.tool_settings.image_paint.brush
        return (brush is not None)

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        ipaint = toolsettings.image_paint

        col = layout.column()

        col.prop(ipaint, "use_occlude")
        col.prop(ipaint, "use_backface_culling")

        row = layout.row()
        row.prop(ipaint, "use_normal_falloff")

        sub = row.row()
        sub.active = (ipaint.use_normal_falloff)
        sub.prop(ipaint, "normal_angle", text = "")

        layout.prop(ipaint, "use_cavity")
        if ipaint.use_cavity:
            layout.template_curve_mapping(ipaint, "cavity_curve", brush=True)

        layout.prop(ipaint, "seam_bleed")
        layout.prop(ipaint, "dither")
        self.unified_paint_settings(layout, context)

        # brush paint modes
        layout.label("Enabled Brush Modes:")
        layout.menu("VIEW3D_MT_brush_paint_modes")


class VIEW3D_PT_imagepaint_options(View3DPaintPanel):
    bl_category = "Options"
    bl_label = "Options"

    @classmethod
    def poll(cls, context):
        return (context.image_paint_object and context.tool_settings.image_paint)

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        self.unified_paint_settings(col, context)

        # brush paint modes
        layout.label("Enabled Brush Modes:")
        layout.menu("VIEW3D_MT_brush_paint_modes")


class VIEW3D_MT_tools_projectpaint_stencil(Menu):
    bl_label = "Mask Layer"

    def draw(self, context):
        layout = self.layout
        for i, tex in enumerate(context.active_object.data.uv_textures):
            props = layout.operator("wm.context_set_int", text=tex.name, translate=False)
            props.data_path = "active_object.data.uv_texture_stencil_index"
            props.value = i


class VIEW3D_PT_tools_particlemode(View3DPanel, Panel):
    """Default tools for particle mode"""
    bl_context = "particlemode"
    bl_label = "Options"
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout

        pe = context.tool_settings.particle_edit
        ob = pe.object

        layout.prop(pe, "type", text = "")

        ptcache = None

        if pe.type == 'PARTICLES':
            if ob.particle_systems:
                if len(ob.particle_systems) > 1:
                    layout.template_list("UI_UL_list", "particle_systems", ob, "particle_systems",
                                         ob.particle_systems, "active_index", rows=2, maxrows=3)

                ptcache = ob.particle_systems.active.point_cache
        else:
            for md in ob.modifiers:
                if md.type == pe.type:
                    ptcache = md.point_cache

        if ptcache and len(ptcache.point_caches) > 1:
            layout.template_list("UI_UL_list", "particles_point_caches", ptcache, "point_caches",
                                 ptcache.point_caches, "active_index", rows=2, maxrows=3)

        if not pe.is_editable:
            layout.label(text="Point cache must be baked")
            layout.label(text="in memory to enable editing!")

        col = layout.column(align=True)
        if pe.is_hair:
            col.active = pe.is_editable
            col.prop(pe, "use_emitter_deflect", text="Deflect Emitter")
            sub = col.row(align=True)
            sub.active = pe.use_emitter_deflect
            sub.prop(pe, "emitter_distance", text="Distance")

        col = layout.column(align=True)
        col.active = pe.is_editable
        col.label(text="Keep:")
        col.prop(pe, "use_preserve_length", text="Lengths")
        col.prop(pe, "use_preserve_root", text="Root")
        if not pe.is_hair:
            col.label(text="Correct:")
            col.prop(pe, "use_auto_velocity", text="Velocity")
        col.prop(ob.data, "use_mirror_x")

        col.prop(pe, "shape_object")
        col.operator("particle.shape_cut")

        col = layout.column(align=True)
        col.active = pe.is_editable
        col.label(text="Draw:")
        col.prop(pe, "draw_step", text="Path Steps")
        if pe.is_hair:
            col.prop(pe, "show_particles", text="Children")
        else:
            if pe.type == 'PARTICLES':
                col.prop(pe, "show_particles", text="Particles")
            col.prop(pe, "use_fade_time")
            sub = col.row(align=True)
            sub.active = pe.use_fade_time
            sub.prop(pe, "fade_frames", slider=True)


# Grease Pencil drawing tools
class VIEW3D_PT_tools_grease_pencil_draw(GreasePencilDrawingToolsPanel, Panel):
    bl_space_type = 'VIEW_3D'


# Grease Pencil stroke editing tools
class VIEW3D_PT_tools_grease_pencil_edit(GreasePencilStrokeEditPanel, Panel):
    bl_space_type = 'VIEW_3D'


# Grease Pencil stroke interpolation tools
class VIEW3D_PT_tools_grease_pencil_interpolate(GreasePencilInterpolatePanel, Panel):
    bl_space_type = 'VIEW_3D'


# Grease Pencil stroke sculpting tools
class VIEW3D_PT_tools_grease_pencil_sculpt(GreasePencilStrokeSculptPanel, Panel):
    bl_space_type = 'VIEW_3D'


# Grease Pencil drawing brushes
class VIEW3D_PT_tools_grease_pencil_brush(GreasePencilBrushPanel, Panel):
    bl_space_type = 'VIEW_3D'

# Grease Pencil drawingcurves
class VIEW3D_PT_tools_grease_pencil_brushcurves(GreasePencilBrushCurvesPanel, Panel):
    bl_space_type = 'VIEW_3D'


# Note: moved here so that it's always in last position in 'Tools' panels!
class VIEW3D_PT_tools_history(View3DPanel, Panel):
    bl_category = "Tools"
    # No bl_context, we are always available!
    bl_label = "History"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        view = context.space_data # Our data for the icon_or_text flag is in space_data. A c prop
        # Flag is off, draw buttons as text
        if not view.show_iconbuttons: 
            col = layout.column(align=True)
            row = col.row(align=True)
            row.operator("ed.undo", icon='UNDO')
            row.operator("ed.redo", icon='REDO')
            if obj is None or obj.mode != 'SCULPT':
                # Sculpt mode does not generate an undo menu it seems...
                col.operator("ed.undo_history", icon='UNDO_HISTORY', text = "Undo History   ")

            col = layout.column(align=True)
            col.label(text="Repeat:")
            col.operator("screen.repeat_last", icon='REPEAT', text = "Repeat Last     ")
            col.operator("screen.repeat_history", icon='REDO_HISTORY', text="Repeat History")

        # Flag is on, draw buttons as icons.
        else:
            col = layout.column(align=True)
            row = col.row(align=False)
            row.operator("ed.undo", icon='UNDO',text = "")
            row.operator("ed.redo", icon='REDO',text = "")
            row.operator("ed.undo_history", icon='UNDO_HISTORY',text = "")

            col = layout.column(align=True)
            col.label(text="Repeat:")
            row = col.row(align=False)
            row.operator("screen.repeat_last", icon='REPEAT', text = "")
            row.operator("screen.repeat_history", icon='REDO_HISTORY', text = "")

# Bake in Blender Internal

class RENDER_PT_bake(bpy.types.Panel):
    bl_label = "Bake Blender Render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "TOOLS"
    bl_category = "Tools"
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "objectmode"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}
    
    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene and (scene.render.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        layout.operator("object.bake_image", icon='RENDER_STILL')

        layout.prop(rd, "bake_type", text = "")

        multires_bake = False
        if rd.bake_type in ['NORMALS', 'DISPLACEMENT', 'DERIVATIVE', 'AO']:
            layout.prop(rd, "use_bake_multires")
            multires_bake = rd.use_bake_multires

        if not multires_bake:
            if rd.bake_type == 'NORMALS':
                layout.prop(rd, "bake_normal_space")
            elif rd.bake_type in {'DISPLACEMENT', 'AO'}:
                layout.prop(rd, "use_bake_normalize")

            # col.prop(rd, "bake_aa_mode")
            # col.prop(rd, "use_bake_antialiasing")
            
            col = layout.column()
            
            col.prop(rd, "use_bake_selected_to_active")
            col.prop(rd, "use_bake_to_vertex_color")
            sub = col.column()
            sub.active = not rd.use_bake_to_vertex_color
            sub.prop(rd, "use_bake_clear")
            
            sub.prop(rd, "bake_quad_split", text="Split")
            sub.prop(rd, "bake_margin")
            
            sub = col.column()
            sub.active = rd.use_bake_selected_to_active
            sub.prop(rd, "bake_distance")
            sub.prop(rd, "bake_bias")
        else:

            col.prop(rd, "use_bake_clear")
            col.prop(rd, "bake_margin")

            if rd.bake_type == 'DISPLACEMENT':
                col = split.column()
                col.prop(rd, "use_bake_lores_mesh")

            if rd.bake_type == 'AO':
                col = split.column()
                col.prop(rd, "bake_bias")
                col.prop(rd, "bake_samples")

        if rd.bake_type == 'DERIVATIVE':
            row = layout.row()
            row.prop(rd, "use_bake_user_scale", text = "")

            sub = row.column()
            sub.active = rd.use_bake_user_scale
            sub.prop(rd, "bake_user_scale", text="User Scale")

# Link Data menu

class VIEW3D_MT_make_links(Menu):
    bl_label = "Link Data"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.make_links_data", text = "Object Data", icon='LINK_DATA').type = 'OBDATA'
        layout.operator("object.make_links_data", text = "Materials", icon='LINK_DATA').type = 'MATERIAL'
        layout.operator("object.make_links_data", text = "Animation Data", icon='LINK_DATA').type = 'ANIMATION'
        layout.operator("object.make_links_data", text = "Group", icon='LINK_DATA').type = 'GROUPS'
        layout.operator("object.make_links_data", text = "Dupli Group", icon='LINK_DATA').type = 'DUPLIGROUP'
        layout.operator("object.make_links_data", text = "Modifiers", icon='LINK_DATA').type = 'MODIFIERS'
        layout.operator("object.make_links_data", text = "Fonts", icon='LINK_DATA').type = 'FONTS'

classes = (
    VIEW3D_MT_snap_panel,
    VIEW3D_PT_tools_object,
    VIEW3D_PT_tools_add_object,
    VIEW3D_PT_tools_add_misc,
    VIEW3D_PT_tools_relations,
    VIEW3D_PT_tools_animation,
    VIEW3D_PT_tools_rigid_body,
    VIEW3D_PT_tools_meshedit,
    VIEW3D_normals_make_consistent_inside,
    VIEW3D_PT_tools_meshweight,
    VIEW3D_PT_tools_add_mesh_edit,
    VIEW3D_PT_tools_shading,
    VIEW3D_markseam_clear,
    VIEW3D_PT_tools_uvs,
    VIEW3D_PT_tools_meshedit_options,
    VIEW3D_PT_tools_curveedit,
    VIEW3D_PT_tools_add_curve_edit,
    VIEW3D_PT_tools_curveedit_options_stroke,
    VIEW3D_PT_tools_surfaceedit,
    VIEW3D_PT_tools_add_surface_edit,
    VIEW3D_PT_tools_textedit,
    VIEW3D_PT_tools_armatureedit,
    VIEW3D_PT_tools_armatureedit_options,
    VIEW3D_PT_tools_mballedit,
    VIEW3D_PT_tools_add_mball_edit,
    VIEW3D_PT_tools_latticeedit,
    VIEW3D_PT_tools_posemode,
    VIEW3D_PT_tools_posemode_options,
    VIEW3D_PT_imapaint_tools_missing,
    VIEW3D_PT_tools_brush,
    TEXTURE_UL_texpaintslots,
    VIEW3D_MT_tools_projectpaint_uvlayer,
    VIEW3D_PT_slots_projectpaint,
    VIEW3D_PT_stencil_projectpaint,
    VIEW3D_PT_tools_brush_overlay,
    VIEW3D_PT_tools_brush_texture,
    VIEW3D_PT_tools_mask_texture,
    VIEW3D_PT_tools_brush_stroke,
    VIEW3D_PT_tools_brush_curve,
    VIEW3D_PT_sculpt_dyntopo,
    VIEW3D_PT_sculpt_options,
    VIEW3D_PT_sculpt_symmetry,
    VIEW3D_PT_tools_brush_appearance,
    VIEW3D_PT_tools_weightpaint,
    VIEW3D_PT_tools_weightpaint_symmetry,
    VIEW3D_PT_tools_weightpaint_options,
    VIEW3D_PT_tools_vertexpaint,
    VIEW3D_PT_tools_vertexpaint_symmetry,
    VIEW3D_PT_tools_imagepaint_external,
    VIEW3D_PT_tools_imagepaint_symmetry,
    VIEW3D_PT_tools_projectpaint,
    VIEW3D_MT_tools_projectpaint_stencil,
    VIEW3D_PT_tools_particlemode,
    VIEW3D_PT_tools_grease_pencil_draw,
    VIEW3D_PT_tools_grease_pencil_edit,
    VIEW3D_PT_tools_grease_pencil_interpolate,
    VIEW3D_PT_tools_grease_pencil_sculpt,
    VIEW3D_PT_tools_grease_pencil_brush,
    VIEW3D_PT_tools_grease_pencil_brushcurves,
    VIEW3D_PT_tools_history,
    RENDER_PT_bake,
    VIEW3D_MT_make_links,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
