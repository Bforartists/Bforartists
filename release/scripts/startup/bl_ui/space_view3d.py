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
from bpy.types import Header, Menu, Panel
from bl_ui.properties_grease_pencil_common import GreasePencilDataPanel
from bl_ui.properties_paint_common import UnifiedPaintPanel
from bpy.app.translations import contexts as i18n_contexts

class VIEW3D_HT_header(Header):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        # mode_string = context.mode
        obj = context.active_object
        toolsettings = context.tool_settings

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        VIEW3D_MT_editor_menus.draw_collapsible(context, layout)

        # Contains buttons like Mode, Pivot, Manipulator, Layer, Mesh Select Mode...
        row = layout
        layout.template_header_3D()

        if obj:
            mode = obj.mode
            # Particle edit
            if mode == 'PARTICLE_EDIT':
                row.prop(toolsettings.particle_edit, "select_mode", text="", expand=True)

            # Occlude geometry
            if ((view.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'} and (mode == 'PARTICLE_EDIT' or (mode == 'EDIT' and obj.type == 'MESH'))) or
                    (mode == 'WEIGHT_PAINT')):
                row.prop(view, "use_occlude_geometry", text="")

            # Proportional editing
            if context.gpencil_data and context.gpencil_data.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(toolsettings, "proportional_edit", icon_only=True)
                if toolsettings.proportional_edit != 'DISABLED':
                    row.prop(toolsettings, "proportional_edit_falloff", icon_only=True)
            elif mode in {'EDIT', 'PARTICLE_EDIT'}:
                row = layout.row(align=True)
                row.prop(toolsettings, "proportional_edit", icon_only=True)
                if toolsettings.proportional_edit != 'DISABLED':
                    row.prop(toolsettings, "proportional_edit_falloff", icon_only=True)
            elif mode == 'OBJECT':
                row = layout.row(align=True)
                row.prop(toolsettings, "use_proportional_edit_objects", icon_only=True)
                if toolsettings.use_proportional_edit_objects:
                    row.prop(toolsettings, "proportional_edit_falloff", icon_only=True)
        else:
            # Proportional editing
            if context.gpencil_data and context.gpencil_data.use_stroke_edit_mode:
                row = layout.row(align=True)
                row.prop(toolsettings, "proportional_edit", icon_only=True)
                if toolsettings.proportional_edit != 'DISABLED':
                    row.prop(toolsettings, "proportional_edit_falloff", icon_only=True)

        # Snap
        if not obj or mode not in {'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT', 'TEXTURE_PAINT'}:
            snap_element = toolsettings.snap_element
            row = layout.row(align=True)
            row.prop(toolsettings, "use_snap", text="")
            row.prop(toolsettings, "snap_element", icon_only=True)
            if snap_element == 'INCREMENT':
                row.prop(toolsettings, "use_snap_grid_absolute", text="")
            else:
                row.prop(toolsettings, "snap_target", text="")
                if obj:
                    if mode in {'OBJECT', 'POSE'} and snap_element != 'VOLUME':
                        row.prop(toolsettings, "use_snap_align_rotation", text="")
                    elif mode == 'EDIT':
                        row.prop(toolsettings, "use_snap_self", text="")

            if snap_element == 'VOLUME':
                row.prop(toolsettings, "use_snap_peel_object", text="")
            elif snap_element == 'FACE':
                row.prop(toolsettings, "use_snap_project", text="")

        # AutoMerge editing
        if obj:
            if (mode == 'EDIT' and obj.type == 'MESH'):
                layout.prop(toolsettings, "use_mesh_automerge", text="", icon='AUTOMERGE_ON')


# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

# the normal text menus 
class VIEW3D_MT_editor_menus(Menu):
    bl_space_type = 'VIEW3D_MT_editor_menus'
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        obj = context.active_object
        mode_string = context.mode
        edit_object = context.edit_object

        layout.menu("VIEW3D_MT_view")
        layout.menu("VIEW3D_MT_view_navigation")

        # Select Menu
        if mode_string in {'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE'}:
            mesh = obj.data
            if mesh.use_paint_mask:
                layout.menu("VIEW3D_MT_select_paint_mask")
            elif mesh.use_paint_mask_vertex and mode_string == 'PAINT_WEIGHT':
                layout.menu("VIEW3D_MT_select_paint_mask_vertex")
        elif mode_string != 'SCULPT':
            layout.menu("VIEW3D_MT_select_%s" % mode_string.lower())

        if edit_object:
            layout.menu("VIEW3D_MT_edit_%s" % edit_object.type.lower())
        elif obj:
            if mode_string != 'PAINT_TEXTURE':
                layout.menu("VIEW3D_MT_%s" % mode_string.lower())
            if mode_string in {'SCULPT', 'PAINT_VERTEX', 'PAINT_WEIGHT', 'PAINT_TEXTURE'}:
                layout.menu("VIEW3D_MT_brush")
            if mode_string == 'SCULPT':
                layout.menu("VIEW3D_MT_hide_mask")
        else:
            layout.menu("VIEW3D_MT_object")


# ********** Utilities **********


# Standard transforms which apply to all cases
# NOTE: this doesn't seem to be able to be used directly
class VIEW3D_MT_transform_base(Menu):
    bl_label = "Transform"

    # TODO: get rid of the custom text strings?
    def draw(self, context):
        layout = self.layout

        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")

        if context.mode != 'OBJECT':
            layout.operator("transform.vertex_warp", text="Warp")


# Generic transform menu - geometry types
class VIEW3D_MT_transform(VIEW3D_MT_transform_base):
    def draw(self, context):
        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # generic...
        layout = self.layout

        layout.separator()

        layout.operator("transform.translate", text="Move Texture Space").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space").texture_space = True

        layout.separator()

        layout.operator("transform.skin_resize", text="Skin Resize")


# Object-specific extensions to Transform menu
class VIEW3D_MT_transform_object(VIEW3D_MT_transform_base):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # object-specific option follow...
        layout.separator()

        layout.operator("transform.translate", text="Move Texture Space").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space").texture_space = True

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("transform.transform", text="Align to Transform Orientation").mode = 'ALIGN'  # XXX see alignmenu() in edit.c of b2.4x to get this working

        layout.separator()

        layout.operator_context = 'EXEC_AREA'

        layout.operator("object.randomize_transform")
        layout.operator("object.align")

        layout.separator()

        layout.operator("object.anim_transforms_to_deltas")


# Armature EditMode extensions to Transform menu
class VIEW3D_MT_transform_armature(VIEW3D_MT_transform_base):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # armature specific extensions follow...
        layout.separator()

        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:
            if obj.data.draw_type == 'BBONE':
                layout.operator("transform.transform", text="Scale BBone").mode = 'BONE_SIZE'
            elif obj.data.draw_type == 'ENVELOPE':
                layout.operator("transform.transform", text="Scale Envelope Distance").mode = 'BONE_SIZE'
                layout.operator("transform.transform", text="Scale Radius").mode = 'BONE_ENVELOPE'

        if context.edit_object and context.edit_object.type == 'ARMATURE':
            layout.operator("armature.align")


class VIEW3D_MT_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout

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


class VIEW3D_MT_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.snap_selected_to_grid", text="Selection to Grid")
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Offset)").use_offset = True

        layout.separator()

        layout.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center", text="Cursor to Center")
        layout.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active", text="Cursor to Active")


class VIEW3D_MT_uv_map(Menu):
    bl_label = "UV Mapping"

    def draw(self, context):
        layout = self.layout

        layout.operator("uv.unwrap", text="Unwrap ABF").method='ANGLE_BASED'
        layout.operator("uv.unwrap", text="Unwrap LSCM").method='CONFORMAL'

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("uv.smart_project")
        layout.operator("uv.lightmap_pack")
        layout.operator("uv.follow_active_quads")

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("uv.cube_project")
        layout.operator("uv.cylinder_project")
        layout.operator("uv.sphere_project")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("uv.project_from_view").scale_to_bounds = False
        layout.operator("uv.project_from_view", text="Project from View (Bounds)").scale_to_bounds = True

        layout.separator()

        layout.operator("uv.reset")


# ********** View menus **********

# Workaround to separate the tooltips
class VIEW3D_MT_view_all_all_regions(bpy.types.Operator):
    """View All all Regions\nView all objects in scene in all four Quad View views\nJust relevant for Quad View """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_all_all_regions"        # unique identifier for buttons and menu items to reference.
    bl_label = "View All all Regions"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_all(use_all_regions = True)
        return {'FINISHED'}  

    # Workaround to separate the tooltips
class VIEW3D_MT_view_center_cursor_and_view_all(bpy.types.Operator):
    """Center Cursor and View All\nViews all objects in scene and centers the 3D cursor"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_all_center_cursor"        # unique identifier for buttons and menu items to reference.
    bl_label = "Center Cursor and View All"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_all(center = True)
        return {'FINISHED'}  

    # Workaround to separate the tooltips
class VIEW3D_MT_view_view_selected_all_regions(bpy.types.Operator):
    """View Selected All Regions\nMove the View to the selection center in all Quad View views"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "view3d.view_selected_all_regions"        # unique identifier for buttons and menu items to reference.
    bl_label = "View Selected All Regions"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.view3d.view_selected(use_all_regions = True)
        return {'FINISHED'}  


class VIEW3D_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.properties", icon='MENU_PANEL')
        layout.operator("view3d.toolshelf", icon='MENU_PANEL')

        layout.separator()

        layout.operator("view3d.object_as_camera", icon = 'VIEW_SWITCHACTIVECAM')
        layout.operator("view3d.viewnumpad", text="Active Camera", icon = 'VIEW_SWITCHTOCAM').type = 'CAMERA'
        layout.operator("view3d.view_center_camera")

        layout.separator()

        layout.menu("VIEW3D_MT_view_align")
        layout.menu("VIEW3D_MT_view_align_selected")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'

        # restrict render and clear restrict render. I would love to simply disable it, 
        # means grey out when there are no objects selected. But that's ways too much hassle. 
        # So for now we simply hide the two menu items when there is no object selected.

        if context.object :
            props = layout.operator("object.hide_render_set")
            props = layout.operator("object.isolate_type_render")
            props = layout.operator("object.hide_render_clear_all")

            layout.separator()

        layout.operator("view3d.clip_border", text="Clipping Border")
        layout.operator("view3d.clear_render_border", text="Clear Render Border")
        layout.operator("view3d.render_border", text="Render Border").camera_only = False

        layout.separator()

        layout.operator("view3d.layers", text="Show All Layers").nr = 0

        layout.separator()

        
        myvar= layout.operator("transform.create_orientation", text="Create Orientation")
        myvar.use_view = True
        myvar.use = True

        layout.separator()

        layout.operator("view3d.localview", text="View Global/Local")
        #layout.operator("view3d.view_selected", text = "View Selected all Regions" ).use_all_regions = True
        layout.operator("view3d.view_selected_all_regions", text = "View Selected all Regions" )
        layout.operator("view3d.view_selected").use_all_regions = False
        #layout.operator("view3d.view_all", text = "View All all Regions" ).use_all_regions = True
        #layout.operator("view3d.view_all", text="Center Cursor and View All").center = True
        layout.operator("view3d.view_all_all_regions", text = "View All all Regions" ) # bfa - separated tooltip
        layout.operator("view3d.view_all_center_cursor", text="Center Cursor and View All") # bfa - separated tooltip
        layout.operator("view3d.view_all").center = False

        layout.separator()

        layout.operator("screen.area_dupli")
        layout.operator("screen.region_quadview")
        #layout.operator("screen.screen_full_area", text="Toggle Maximize Area")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area").use_hide_panels = True


class VIEW3D_MT_view_navigation(Menu):
    bl_label = "Navi"

    def draw(self, context):
        from math import pi
        layout = self.layout

        layout.operator_enum("view3d.view_orbit", "type")
        props = layout.operator("view3d.view_orbit", "Orbit Opposite")
        props.type = 'ORBITRIGHT'
        props.angle = pi

        layout.separator()

        layout.operator("view3d.view_roll", text="Roll Left").angle = pi / -12.0
        layout.operator("view3d.view_roll", text="Roll Right").angle = pi / 12.0

        layout.separator()

        layout.operator_enum("view3d.view_pan", "type")

        layout.separator()

        layout.operator("view3d.zoom_border", text="Zoom Border")
        layout.operator("view3d.zoom", text="Zoom In").delta = 1
        layout.operator("view3d.zoom", text="Zoom Out").delta = -1
        layout.operator("view3d.zoom_camera_1_to_1", text="Zoom Camera 1:1")
        layout.operator("view3d.dolly", text="Dolly View")
        layout.operator("view3d.view_center_pick")

        layout.separator()

        layout.operator("view3d.fly")
        layout.operator("view3d.walk")

        layout.separator()

        layout.operator("screen.animation_play", text="Playback Animation")

        layout.separator()

        layout.operator("transform.translate", icon='TRANSFORM_MOVE')
        layout.operator("transform.rotate", icon='TRANSFORM_ROTATE')
        layout.operator("transform.resize", icon='TRANSFORM_SCALE', text="Scale")


class VIEW3D_MT_view_align(Menu):
    bl_label = "Align View"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.camera_to_view", text="Align Active Camera to View")
        layout.operator("view3d.camera_to_view_selected", text="Align Active Camera to Selected")
        layout.operator("view3d.view_center_cursor")

        layout.separator()

        layout.operator("view3d.view_lock_to_active")
        layout.operator("view3d.view_center_lock")
        layout.operator("view3d.view_lock_clear")

        layout.separator()

        # Rest of align

        layout.operator("view3d.view_persportho")

        layout.separator()

        layout.operator("view3d.viewnumpad", text="Top", icon ="VIEW_TOP").type = 'TOP'
        layout.operator("view3d.viewnumpad", text="Bottom", icon ="VIEW_BOTTOM").type = 'BOTTOM'
        layout.operator("view3d.viewnumpad", text="Front", icon ="VIEW_FRONT").type = 'FRONT'
        layout.operator("view3d.viewnumpad", text="Back", icon ="VIEW_BACK").type = 'BACK'
        layout.operator("view3d.viewnumpad", text="Right", icon ="VIEW_RIGHT").type = 'RIGHT'
        layout.operator("view3d.viewnumpad", text="Left", icon ="VIEW_LEFT").type = 'LEFT'


class VIEW3D_MT_view_align_selected(Menu):
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


# ********** Select menus, suffix from context.mode **********

# Workaround to separate the tooltips
class VIEW3D_MT_select_object_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_object(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("object.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("object.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("object.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("object.select_random", text="Random")
        layout.operator("object.select_mirror", text="Mirror")

        layout.operator("object.select_camera", text="Camera")

        layout.separator()

        layout.operator_menu_enum("object.select_grouped", "type", text="Grouped")
        layout.operator_menu_enum("object.select_linked", "type", text="Linked")
        layout.operator("object.select_pattern", text="By Pattern...")
        layout.operator("object.select_by_layer", text="All by Layer")
        layout.operator_menu_enum("object.select_by_type", "type", text="All by Type ...")
        layout.separator()

        myvar = layout.operator("object.select_hierarchy", text="Parent")
        myvar.direction = 'PARENT'
        myvar.extend = False
        myvar = layout.operator("object.select_hierarchy", text="Child")
        myvar.direction = 'CHILD'
        myvar.extend = False

        myvar = layout.operator("object.select_hierarchy", text="Parent Extended")
        myvar.direction = 'PARENT'
        myvar.extend = True
        myvar = layout.operator("object.select_hierarchy", text="Child Extended")
        myvar.direction = 'CHILD'
        myvar.extend = True

        layout.separator()

# Workaround to separate the tooltips
class VIEW3D_MT_select_pose_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "pose.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.pose.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_pose(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("pose.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("pose.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("pose.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("pose.select_mirror", text="Flip Active")
        layout.operator("pose.select_constraint_target", text="Constraint Target")

        layout.separator()

        layout.operator_menu_enum("pose.select_grouped", "type", text="Grouped")
        layout.operator("pose.select_linked", text="Linked")      
        layout.operator("object.select_pattern", text="By Pattern...")

        layout.separator()

        props = layout.operator("pose.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'

        props = layout.operator("pose.select_hierarchy", text="Parent Extended")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child Extended")
        props.extend = True
        props.direction = 'CHILD'

        layout.separator()



# Workaround to separate the tooltips
class VIEW3D_MT_select_particle_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "particle.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.particle.select_all(action = 'INVERT')
        return {'FINISHED'}  

class VIEW3D_MT_select_particle(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')

        layout.separator()

        layout.operator("particle.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("particle.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("particle.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("particle.select_random", text="Random")
        layout.operator("particle.select_roots", text="Roots")
        layout.operator("particle.select_tips", text="Tips")
        
        layout.separator()

        layout.operator("particle.select_linked", text="Linked").deselect = False
        layout.operator("particle.select_linked", text="Deselect Linked").deselect = True
        layout.separator()

        layout.operator("particle.select_more", text="More")
        layout.operator("particle.select_less", text="Less")


class VIEW3D_MT_edit_mesh_select_similar(Menu):
    bl_label = "Select Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("mesh.select_similar", "type")

        layout.separator()

        layout.operator("mesh.select_similar_region", text="Face Regions")

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_mesh_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.select_all(action = 'INVERT')
        return {'FINISHED'}  

class VIEW3D_MT_select_edit_mesh(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        # primitive
        layout.operator("mesh.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("mesh.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("mesh.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        # numeric
        layout.operator("mesh.select_random", text="Random")   
        layout.operator("mesh.select_mirror", text="Mirror")
        layout.operator("mesh.select_nth")
        layout.operator("mesh.shortest_path_select", text="Shortest Path")
        layout.operator("mesh.select_axis", text="Side of Active")


        layout.separator()

        # geometric
        layout.operator("mesh.edges_select_sharp", text="Sharp Edges")
        

        # topology
        layout.operator("mesh.select_loose", text="Loose Geometry")
        if context.scene.tool_settings.mesh_select_mode[2] is False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold")
        layout.operator("mesh.select_interior_faces", text="Interior Faces")
        layout.operator("mesh.select_face_by_sides", text = "Faces by Side")
        

        layout.separator()

        layout.operator("mesh.loop_multi_select", text="Edge Loops").ring = False
        layout.operator("mesh.loop_multi_select", text="Edge Rings").ring = True
        layout.operator("mesh.loop_to_region", text = "Loop Inner-Region")
        layout.operator("mesh.region_to_loop", text = "Boundary Loop")

        layout.separator()

        # other ...
        layout.operator("mesh.select_ungrouped", text="Ungrouped Verts")
        layout.menu("VIEW3D_MT_edit_mesh_select_similar")
        layout.operator("mesh.faces_select_linked_flat", text="Linked Flat Faces")
        layout.operator("mesh.select_linked", text="Linked")
        layout.operator("mesh.select_linked_pick", text="Linked Pick Select").deselect = False
        layout.operator("mesh.select_linked_pick", text="Linked Pick Deselect").deselect = True
   

        layout.separator()

        layout.operator("mesh.select_more", text="More")
        layout.operator("mesh.select_less", text="Less")

        layout.separator()

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_curve_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "curve.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.curve.select_all(action = 'INVERT')
        return {'FINISHED'}  

class VIEW3D_MT_select_edit_curve(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("curve.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("curve.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("curve.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("curve.select_random", text="Random")
        layout.operator("curve.select_nth")

        layout.separator()

        layout.operator("curve.select_linked", text="Linked")
        layout.operator("curve.select_linked_pick", text="Linked Pick Select").deselect = False
        layout.operator("curve.select_linked_pick", text="Linked Pick Deselect").deselect = True
        layout.operator("curve.select_similar", text="Similar")

        layout.separator()

        layout.operator("curve.de_select_first")
        layout.operator("curve.de_select_last")
        layout.operator("curve.select_next", text = "Next")
        layout.operator("curve.select_previous", text = "Previous")

        layout.separator()

        layout.operator("curve.select_more", text = "More")
        layout.operator("curve.select_less", text = "Less")

        layout.separator()

class VIEW3D_MT_select_edit_surface(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("curve.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("curve.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("curve.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("curve.select_random", text="Random")
        layout.operator("curve.select_nth")

        layout.separator()

        layout.operator("curve.select_linked", text="Linked")
        layout.operator("curve.select_linked_pick", text="Linked Pick Select").deselect = False
        layout.operator("curve.select_linked_pick", text="Linked Pick Deselect").deselect = True
        layout.operator("curve.select_similar", text="Similar")

        layout.separator()

        layout.operator("curve.select_row")

        layout.separator()

        layout.operator("curve.select_more", text = "More")
        layout.operator("curve.select_less", text = "Less")

        layout.separator()


class VIEW3D_MT_select_edit_text(Menu):
    # intentional name mis-match
    # select menu for 3d-text doesn't make sense
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.text_copy", text="Copy")
        layout.operator("font.text_cut", text="Cut")
        layout.operator("font.text_paste", text="Paste")

        layout.separator()

        layout.operator("font.text_paste_from_file")
        layout.operator("font.text_paste_from_clipboard")

        layout.separator()

        layout.operator("font.select_all")

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_metaball_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.select_all(action = 'INVERT')
        return {'FINISHED'}  

class VIEW3D_MT_select_edit_metaball(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("mball.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("mball.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("mball.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("mball.select_random_metaelems", text="Random")

        layout.separator()

        layout.operator_menu_enum("mball.select_similar", "type", text="Similar")

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_lattice_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "lattice.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.lattice.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_edit_lattice(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("lattice.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("lattice.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("uv.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("lattice.select_random", text="Random")
        layout.operator("lattice.select_mirror", text ="Mirror")

        layout.separator()

        layout.operator("lattice.select_ungrouped", text="Ungrouped Verts")

        layout.separator()

        layout.operator("lattice.select_more", text ="More")
        layout.operator("lattice.select_less", text ="Less")

        layout.separator()

# Workaround to separate the tooltips
class VIEW3D_MT_select_edit_armature_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "armature.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.armature.select_all(action = 'INVERT')
        return {'FINISHED'}  


class VIEW3D_MT_select_edit_armature(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("armature.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("armature.select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("armature.select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("armature.select_mirror", text="Mirror").extend = False

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Parent")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child")
        props.extend = False
        props.direction = 'CHILD'

        props = layout.operator("armature.select_hierarchy", text="Parent Extended")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child Extended")
        props.extend = True
        props.direction = 'CHILD'

        layout.separator()

        layout.operator_menu_enum("armature.select_similar", "type", text="Similar")
        layout.operator("object.select_pattern", text="Pattern...")

        layout.separator()

        layout.operator("armature.select_more", text="More")
        layout.operator("armature.select_less", text="Less")

        layout.separator()

# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.face_select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.face_select_all(action = 'INVERT')
        return {'FINISHED'}  

class VIEW3D_MT_select_paint_mask(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("paint.face_select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("paint.face_select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("paint.face_select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("paint.face_select_linked", text="Linked")
        layout.operator("paint.face_select_linked_pick", text="Linked Pick Select").deselect = False
        layout.operator("paint.face_select_linked_pick", text="Linked Pick Deselect").deselect = True

# Workaround to separate the tooltips
class VIEW3D_MT_select_paint_mask_vertex_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "paint.vert_select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.vert_select_all(action = 'INVERT')
        return {'FINISHED'}  

class VIEW3D_MT_select_paint_mask_vertex(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='SELECT_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='SELECT_BORDER')
        layout.operator("view3d.select_circle", icon = 'SELECT_CIRCLE')

        layout.separator()

        layout.operator("paint.vert_select_all", icon='SELECT_ALL').action = 'TOGGLE'
        #layout.operator("paint.vert_select_all", text="Inverse", icon='SELECT_INVERSE').action = 'INVERT'
        layout.operator("paint.vert_select_all_inverse", text="Inverse", icon='SELECT_INVERSE')

        layout.separator()

        layout.operator("paint.vert_select_ungrouped", text="Ungrouped Verts")


class VIEW3D_MT_angle_control(Menu):
    bl_label = "Angle Control"

    @classmethod
    def poll(cls, context):
        settings = UnifiedPaintPanel.paint_settings(context)
        if not settings:
            return False

        brush = settings.brush
        tex_slot = brush.texture_slot

        return tex_slot.has_texture_angle and tex_slot.has_texture_angle_source

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        sculpt = (context.sculpt_object is not None)

        tex_slot = brush.texture_slot

        layout.prop(tex_slot, "use_rake", text="Rake")

        if brush.brush_capabilities.has_random_texture_angle and tex_slot.has_random_texture_angle:
            if sculpt:
                if brush.sculpt_capabilities.has_random_texture_angle:
                    layout.prop(tex_slot, "use_random", text="Random")
            else:
                layout.prop(tex_slot, "use_random", text="Random")




# ********** Object menu **********

# Workaround to separate the tooltips
class VIEW3D_MT_object_delete_global(bpy.types.Operator):
    """Delete global\nDeletes the selected object(s) globally in all opened scenes"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.delete_global"        # unique identifier for buttons and menu items to reference.
    bl_label = "Delete Global"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.delete(use_global = True)
        return {'FINISHED'}  


class VIEW3D_MT_object(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.object

        # The former Specials menu content. Special settings for Camera, Curve, Font, Empty and Lamp
        if context.object :

            if obj.type == 'CAMERA':
                layout.operator_context = 'INVOKE_REGION_WIN'

                if obj.data.type == 'PERSP':
                    props = layout.operator("wm.context_modal_mouse", text="Camera Lens Angle")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.lens"
                    props.input_scale = 0.1
                    if obj.data.lens_unit == 'MILLIMETERS':
                        props.header_text = "Camera Lens Angle: %.1fmm"
                    else:
                        props.header_text = "Camera Lens Angle: %.1f\u00B0"

                else:
                    props = layout.operator("wm.context_modal_mouse", text="Camera Lens Scale")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.ortho_scale"
                    props.input_scale = 0.01
                    props.header_text = "Camera Lens Scale: %.3f"

                if not obj.data.dof_object:
                    view = context.space_data
                    if view and view.camera == obj and view.region_3d.view_perspective == 'CAMERA':
                        props = layout.operator("ui.eyedropper_depth", text="DOF Distance (Pick)")
                    else:
                        props = layout.operator("wm.context_modal_mouse", text="DOF Distance")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.dof_distance"
                        props.input_scale = 0.02
                        props.header_text = "DOF Distance: %.3f"
                    del view

                layout.separator()

            if obj.type in {'CURVE', 'FONT'}:
                layout.operator_context = 'INVOKE_REGION_WIN'

                props = layout.operator("wm.context_modal_mouse", text="Extrude Size")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.extrude"
                props.input_scale = 0.01
                props.header_text = "Extrude Size: %.3f"

                props = layout.operator("wm.context_modal_mouse", text="Width Size")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.offset"
                props.input_scale = 0.01
                props.header_text = "Width Size: %.3f"

                layout.separator()

            if obj.type == 'EMPTY':
                layout.operator_context = 'INVOKE_REGION_WIN'

                props = layout.operator("wm.context_modal_mouse", text="Empty Draw Size")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "empty_draw_size"
                props.input_scale = 0.01
                props.header_text = "Empty Draw Size: %.3f"

                layout.separator()

            if obj.type == 'LAMP':
                lamp = obj.data

                layout.operator_context = 'INVOKE_REGION_WIN'

                if scene.render.use_shading_nodes:
                    try:
                        value = lamp.node_tree.nodes["Emission"].inputs["Strength"].default_value
                    except AttributeError:
                        value = None

                    if value is not None:
                        props = layout.operator("wm.context_modal_mouse", text="Strength")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.node_tree.nodes[\"Emission\"].inputs[\"Strength\"].default_value"
                        props.header_text = "Lamp Strength: %.3f"
                        props.input_scale = 0.1
                    del value

                    if lamp.type == 'AREA':
                        props = layout.operator("wm.context_modal_mouse", text="Size X")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.size"
                        props.header_text = "Lamp Size X: %.3f"

                        if lamp.shape == 'RECTANGLE':
                            props = layout.operator("wm.context_modal_mouse", text="Size Y")
                            props.data_path_iter = "selected_editable_objects"
                            props.data_path_item = "data.size_y"
                            props.header_text = "Lamp Size Y: %.3f"

                    elif lamp.type in {'SPOT', 'POINT', 'SUN'}:
                        props = layout.operator("wm.context_modal_mouse", text="Size")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.shadow_soft_size"
                        props.header_text = "Lamp Size: %.3f"
                else:
                    props = layout.operator("wm.context_modal_mouse", text="Energy")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.energy"
                    props.header_text = "Lamp Energy: %.3f"

                    if lamp.type in {'SPOT', 'AREA', 'POINT'}:
                        props = layout.operator("wm.context_modal_mouse", text="Falloff Distance")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.distance"
                        props.input_scale = 0.1
                        props.header_text = "Lamp Falloff Distance: %.1f"

                if lamp.type == 'SPOT':
                    layout.separator()
                    props = layout.operator("wm.context_modal_mouse", text="Spot Size")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.spot_size"
                    props.input_scale = 0.01
                    props.header_text = "Spot Size: %.2f"

                    props = layout.operator("wm.context_modal_mouse", text="Spot Blend")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.spot_blend"
                    props.input_scale = -0.01
                    props.header_text = "Spot Blend: %.2f"

                    if not scene.render.use_shading_nodes:
                        props = layout.operator("wm.context_modal_mouse", text="Clip Start")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.shadow_buffer_clip_start"
                        props.input_scale = 0.05
                        props.header_text = "Clip Start: %.2f"

                        props = layout.operator("wm.context_modal_mouse", text="Clip End")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.shadow_buffer_clip_end"
                        props.input_scale = 0.05
                        props.header_text = "Clip End: %.2f"

                layout.separator()

        # End former Specials menu content.

        layout.menu("VIEW3D_MT_transform_object")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("view3d.copybuffer", text = "Copy")
        layout.operator("view3d.pastebuffer", text = "Paste")
        layout.operator("object.duplicate_move")
        layout.operator("object.duplicate_move_linked")
        #layout.operator("object.delete", text="Delete Global").use_global = True
        layout.operator("object.delete_global", text="Delete Global") # bfa - separated tooltip
        layout.operator("object.delete", text="Delete...").use_global = False
        layout.menu("VIEW3D_MT_make_links", text="Make Links...")
        layout.operator("object.make_dupli_face")
        layout.menu("VIEW3D_MT_make_single_user")

        layout.separator()

        layout.menu("VIEW3D_MT_object_track")
        layout.menu("VIEW3D_MT_object_constraints")

        layout.separator()

        layout.menu("VIEW3D_MT_object_quick_effects")
        layout.menu("VIEW3D_subdivision_set")

        layout.separator()

        layout.operator("object.data_transfer")
        layout.operator("object.datalayout_transfer")

        layout.separator()

        layout.menu("VIEW3D_MT_object_showhide")

        layout.operator_menu_enum("object.convert", "target")


class VIEW3D_MT_object_clear(Menu):
    bl_label = "Clear"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.location_clear", text="Location", icon = "CLEARMOVE")
        layout.operator("object.rotation_clear", text="Rotation", icon = "CLEARROTATE")
        layout.operator("object.scale_clear", text="Scale", icon = "CLEARSCALE")
        layout.operator("object.origin_clear", text="Origin", icon = "CLEARORIGIN")


class VIEW3D_MT_object_apply(Menu):
    bl_label = "Apply"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("object.transform_apply", text="Location", text_ctxt=i18n_contexts.default, icon = "APPLYMOVE")
        props.location, props.rotation, props.scale = True, False, False

        props = layout.operator("object.transform_apply", text="Rotation", text_ctxt=i18n_contexts.default, icon = "APPLYROTATE")
        props.location, props.rotation, props.scale = False, True, False

        props = layout.operator("object.transform_apply", text="Scale", text_ctxt=i18n_contexts.default, icon = "APPLYSCALE")
        props.location, props.rotation, props.scale = False, False, True

        props = layout.operator("object.transform_apply", text="All", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
        props.location, props.rotation, props.scale = True, True, True

        layout.separator()

        layout.operator("object.visual_transform_apply", text="Visual Transform", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
        layout.operator("object.duplicates_make_real", icon = "MAKEDUPLIREAL")


class VIEW3D_MT_object_track(Menu):
    bl_label = "Track"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("object.track_set", "type")
        layout.separator()
        layout.operator_enum("object.track_clear", "type")

class VIEW3D_MT_object_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.constraint_add_with_targets")
        layout.operator("object.constraints_copy")
        layout.operator("object.constraints_clear")


class VIEW3D_MT_object_quick_effects(Menu):
    bl_label = "Quick Effects"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.quick_fur")
        layout.operator("object.quick_explode")
        layout.operator("object.quick_smoke")
        layout.operator("object.quick_fluid")


class VIEW3D_subdivision_set(Menu):
    bl_label = "Subdivide"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.subdivision_set").level = 0
        layout.operator("object.subdivision_set").level = 1
        layout.operator("object.subdivision_set").level = 2
        layout.operator("object.subdivision_set").level = 3
        layout.operator("object.subdivision_set").level = 4
        layout.operator("object.subdivision_set").level = 5

# Workaround to separate the tooltips for Show Hide
class VIEW3D_hide_view_set_unselected(bpy.types.Operator):
    """Hide Unselected\nHides the unselected Object(s)"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.object.hide_view_set(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_object_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.hide_view_clear", text="Show Hidden")
        layout.operator("object.hide_view_set", text="Hide Selected").unselected = False
        layout.operator("object.hide_unselected", text="Hide Unselected")


class VIEW3D_MT_make_single_user(Menu):
    bl_label = "Make Single User"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("object.make_single_user", text="Object")
        props.object = True
        props.obdata = props.material = props.texture = props.animation = False

        props = layout.operator("object.make_single_user", text="Object & Data")
        props.object = props.obdata = True
        props.material = props.texture = props.animation = False

        props = layout.operator("object.make_single_user", text="Object & Data & Materials+Tex")
        props.object = props.obdata = props.material = props.texture = True
        props.animation = False

        props = layout.operator("object.make_single_user", text="Materials+Tex")
        props.material = props.texture = True
        props.object = props.obdata = props.animation = False

        props = layout.operator("object.make_single_user", text="Object Animation")
        props.animation = True
        props.object = props.obdata = props.material = props.texture = False


class VIEW3D_MT_make_links(Menu):
    bl_label = "Make Links"

    def draw(self, context):
        layout = self.layout
        operator_context_default = layout.operator_context
        if len(bpy.data.scenes) > 10:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("object.make_links_scene", text="Objects to Scene...", icon='OUTLINER_OB_EMPTY')
        else:
            layout.operator_context = 'EXEC_REGION_WIN'
            layout.operator_menu_enum("object.make_links_scene", "scene", text="Objects to Scene...")
        layout.operator_context = operator_context_default

        layout.operator_enum("object.make_links_data", "type")  # inline

        layout.operator("object.join_uvs")  # stupid place to add this!


# Show hide menu for face selection masking
class VIEW3D_MT_facemask_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.face_select_reveal", text="Show Hidden")
        layout.operator("paint.face_select_hide", text="Hide Selected").unselected = False
        layout.operator("paint.face_select_hide", text="Hide Unselected").unselected = True


# ********** Brush menu **********
class VIEW3D_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        ups = context.tool_settings.unified_paint_settings
        layout.prop(ups, "use_unified_size", text="Unified Size")
        layout.prop(ups, "use_unified_strength", text="Unified Strength")
        if context.image_paint_object or context.vertex_paint_object:
            layout.prop(ups, "use_unified_color", text="Unified Color")
        layout.separator()

        # brush paint modes
        layout.menu("VIEW3D_MT_brush_paint_modes")

        # brush tool
        if context.sculpt_object:
            layout.operator("brush.reset")
            layout.prop_menu_enum(brush, "sculpt_tool")
        elif context.image_paint_object:
            layout.prop_menu_enum(brush, "image_tool")
        elif context.vertex_paint_object or context.weight_paint_object:
            layout.prop_menu_enum(brush, "vertex_tool")

        # skip if no active brush
        if not brush:
            return

        # TODO: still missing a lot of brush options here

        # sculpt options
        if context.sculpt_object:

            sculpt_tool = brush.sculpt_tool

            layout.separator()
            layout.operator_menu_enum("brush.curve_preset", "shape", text="Curve Preset")
            layout.separator()

            if sculpt_tool != 'GRAB':
                layout.prop_menu_enum(brush, "stroke_method")

                if sculpt_tool in {'DRAW', 'PINCH', 'INFLATE', 'LAYER', 'CLAY'}:
                    layout.prop_menu_enum(brush, "direction")

                if sculpt_tool == 'LAYER':
                    layout.prop(brush, "use_persistent")
                    layout.operator("sculpt.set_persistent_base")

        layout.separator()

        layout.menu("VIEW3D_MT_facemask_showhide") ### show hide for face mask tool


class VIEW3D_MT_brush_paint_modes(Menu):
    bl_label = "Enabled Modes"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = settings.brush

        layout.prop(brush, "use_paint_sculpt", text="Sculpt")
        layout.prop(brush, "use_paint_vertex", text="Vertex Paint")
        layout.prop(brush, "use_paint_weight", text="Weight Paint")
        layout.prop(brush, "use_paint_image", text="Texture Paint")

# ********** Vertex paint menu **********


class VIEW3D_MT_paint_vertex(Menu):
    bl_label = "Paint"

    def draw(self, context):
        layout = self.layout

        layout.operator("ed.undo")
        layout.operator("ed.redo")

        layout.separator()

        layout.operator("paint.vertex_color_set")
        layout.operator("paint.vertex_color_smooth")
        layout.operator("paint.vertex_color_dirt")


class VIEW3D_MT_hook(Menu):
    bl_label = "Hooks"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.hook_add_newob")
        layout.operator("object.hook_add_selob").use_bone = False
        layout.operator("object.hook_add_selob", text="Hook to Selected Object Bone").use_bone = True

        if [mod.type == 'HOOK' for mod in context.active_object.modifiers]:
            layout.separator()
            layout.operator_menu_enum("object.hook_assign", "modifier")
            layout.operator_menu_enum("object.hook_remove", "modifier")
            layout.separator()
            layout.operator_menu_enum("object.hook_select", "modifier")
            layout.operator_menu_enum("object.hook_reset", "modifier")
            layout.operator_menu_enum("object.hook_recenter", "modifier")


class VIEW3D_MT_vertex_group(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.vertex_group_assign_new")

        ob = context.active_object
        if ob.mode == 'EDIT' or (ob.mode == 'WEIGHT_PAINT' and ob.type == 'MESH' and ob.data.use_paint_mask_vertex):
            if ob.vertex_groups.active:
                layout.separator()
                layout.operator("object.vertex_group_assign", text="Assign to Active Group")
                layout.operator("object.vertex_group_remove_from", text="Remove from Active Group").use_all_groups = False
                layout.operator("object.vertex_group_remove_from", text="Remove from All").use_all_groups = True
                layout.separator()

        if ob.vertex_groups.active:
            layout.operator_menu_enum("object.vertex_group_set_active", "group", text="Set Active Group")
            layout.operator("object.vertex_group_remove", text="Remove Active Group").all = False
            layout.operator("object.vertex_group_remove", text="Remove All Groups").all = True

# ********** Weight paint menu **********


class VIEW3D_MT_paint_weight(Menu):
    bl_label = "Weights"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.weight_from_bones", text="Assign Automatic From Bones").type = 'AUTOMATIC'
        layout.operator("paint.weight_from_bones", text="Assign From Bone Envelopes").type = 'ENVELOPES'

        layout.separator()

        layout.operator("object.vertex_group_normalize_all", text="Normalize All")
        layout.operator("object.vertex_group_normalize", text="Normalize")
        layout.operator("object.vertex_group_mirror", text="Mirror")
        layout.operator("object.vertex_group_invert", text="Invert")
        layout.operator("object.vertex_group_clean", text="Clean")
        layout.operator("object.vertex_group_quantize", text="Quantize")
        layout.operator("object.vertex_group_levels", text="Levels")
        layout.operator("object.vertex_group_smooth", text="Smooth")
        props = layout.operator("object.data_transfer", text="Transfer Weights")
        props.use_reverse_transfer = True
        props.data_type = 'VGROUP_WEIGHTS'
        layout.operator("object.vertex_group_limit_total", text="Limit Total")
        layout.operator("object.vertex_group_fix", text="Fix Deforms")

        layout.separator()

        layout.operator("paint.weight_set")

# ********** Sculpt menu **********


class VIEW3D_MT_sculpt(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        sculpt = toolsettings.sculpt

        layout.operator("ed.undo")
        layout.operator("ed.redo")

        layout.separator()

        layout.prop(sculpt, "use_symmetry_x")
        layout.prop(sculpt, "use_symmetry_y")
        layout.prop(sculpt, "use_symmetry_z")
        layout.separator()
        layout.prop(sculpt, "lock_x")
        layout.prop(sculpt, "lock_y")
        layout.prop(sculpt, "lock_z")

        layout.separator()

        layout.prop(sculpt, "use_threaded", text="Threaded Sculpt")
        layout.prop(sculpt, "show_low_resolution")
        layout.prop(sculpt, "show_brush")
        layout.prop(sculpt, "use_deform_only")
        layout.prop(sculpt, "show_diffuse_color")

        layout.separator()

        layout.menu("VIEW3D_subdivision_set")


class VIEW3D_MT_hide_mask(Menu):
    bl_label = "Hide/Mask"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("paint.hide_show", text="Show All")
        props.action = 'SHOW'
        props.area = 'ALL'

        props = layout.operator("paint.hide_show", text="Hide Bounding Box")
        props.action = 'HIDE'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Show Bounding Box")
        props.action = 'SHOW'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Hide Masked")
        props.area = 'MASKED'
        props.action = 'HIDE'

        layout.separator()

        props = layout.operator("paint.mask_flood_fill", text="Invert Mask")
        props.mode = 'INVERT'

        props = layout.operator("paint.mask_flood_fill", text="Fill Mask")
        props.mode = 'VALUE'
        props.value = 1

        props = layout.operator("paint.mask_flood_fill", text="Clear Mask")
        props.mode = 'VALUE'
        props.value = 0

        props = layout.operator("view3d.select_border", text="Box Mask")
        props = layout.operator("paint.mask_lasso_gesture", text="Lasso Mask")


# ********** Particle menu **********

# Workaround to separate the tooltips for Show Hide for Particles in Particle mode
class VIEW3D_particle_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide the unselected Particles"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "particle.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.particle.hide(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_particle_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("particle.reveal", text="Show Hidden")
        layout.operator("particle.hide", text="Hide Selected").unselected = False
        layout.operator("particle.hide_unselected", text="Hide Unselected")


class VIEW3D_MT_particle(Menu):
    bl_label = "Particle"

    def draw(self, context):
        layout = self.layout

        particle_edit = context.tool_settings.particle_edit

        layout.operator("particle.mirror")

        layout.separator()

        layout.operator("particle.remove_doubles")
        layout.operator("particle.delete")

        if particle_edit.select_mode == 'POINT':
            layout.operator("particle.subdivide")

        layout.operator("particle.rekey")
        layout.operator("particle.weight_set")

        layout.separator()

        layout.menu("VIEW3D_MT_particle_show_hide") # bfa - the new menu with separated tooltip


# ********** Pose Menu **********

# Workaround to separate the tooltips for Show Hide for Armature in Pose mode
class VIEW3D_pose_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected Bones"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "pose.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.pose.hide(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_pose_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.reveal", text="Show Hidden")
        layout.operator("pose.hide", text="Hide Selected").unselected = False
        layout.operator("pose.hide_unselected", text="Hide Unselected")

class VIEW3D_MT_pose(Menu):
    bl_label = "Pose"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_transform_armature")

        layout.menu("VIEW3D_MT_pose_transform")
        layout.menu("VIEW3D_MT_pose_apply")

        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("pose.copy")
        layout.operator("pose.paste").flipped = False
        layout.operator("pose.paste", text="Paste X-Flipped Pose").flipped = True

        layout.separator()

        layout.menu("VIEW3D_MT_pose_library")
        layout.menu("VIEW3D_MT_pose_group")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_ik")
        layout.menu("VIEW3D_MT_pose_constraints")

        layout.separator()

        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.autoside_names", text="AutoName Left/Right").axis = 'XAXIS'
        layout.operator("pose.autoside_names", text="AutoName Front/Back").axis = 'YAXIS'
        layout.operator("pose.autoside_names", text="AutoName Top/Bottom").axis = 'ZAXIS'

        layout.operator("pose.flip_names")

        layout.operator("pose.quaternions_flip")

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("armature.armature_layers", text="Change Armature Layers...")
        layout.operator("pose.bone_layers", text="Change Bone Layers...")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_show_hide") # bfa - new show hide menu with separated tooltips
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")


class VIEW3D_MT_pose_transform(Menu):
    bl_label = "Clear Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.transforms_clear", text="All")

        layout.separator()

        layout.operator("pose.loc_clear", text="Location")
        layout.operator("pose.rot_clear", text="Rotation")
        layout.operator("pose.scale_clear", text="Scale")

        layout.separator()

        layout.operator("pose.user_transforms_clear", text="Clear User Transforms (All)").only_selected = False
        layout.operator("pose.user_transforms_clear", text="Reset unkeyed")




class VIEW3D_MT_pose_slide(Menu):
    bl_label = "In-Betweens"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.push")
        layout.operator("pose.relax")
        layout.operator("pose.breakdown")


class VIEW3D_MT_pose_propagate(Menu):
    bl_label = "Propagate"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.propagate").mode = 'WHILE_HELD'

        layout.separator()

        layout.operator("pose.propagate", text="To Next Keyframe").mode = 'NEXT_KEY'
        layout.operator("pose.propagate", text="To Last Keyframe (Make Cyclic)").mode = 'LAST_KEY'

        layout.separator()

        layout.operator("pose.propagate", text="On Selected Keyframes").mode = 'SELECTED_KEYS'

        layout.separator()

        layout.operator("pose.propagate", text="On Selected Markers").mode = 'SELECTED_MARKERS'


class VIEW3D_MT_pose_library(Menu):
    bl_label = "Pose Library"

    def draw(self, context):
        layout = self.layout

        layout.operator("poselib.browse_interactive", text="Browse Poses...")

        layout.separator()

        layout.operator("poselib.pose_add", text="Add Pose...")
        layout.operator("poselib.pose_rename", text="Rename Pose...")
        layout.operator("poselib.pose_remove", text="Remove Pose...")


class VIEW3D_MT_pose_motion(Menu):
    bl_label = "Motion Paths"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.paths_calculate", text="Calculate")
        layout.operator("pose.paths_clear", text="Clear")


class VIEW3D_MT_pose_group(Menu):
    bl_label = "Bone Groups"

    def draw(self, context):
        layout = self.layout

        pose = context.active_object.pose

        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.group_assign", text="Assign to New Group").type = 0
        if pose.bone_groups:
            active_group = pose.bone_groups.active_index + 1
            layout.operator("pose.group_assign", text="Assign to Group").type = active_group

            layout.separator()

            #layout.operator_context = 'INVOKE_AREA'
            layout.operator("pose.group_unassign")
            layout.operator("pose.group_remove")


class VIEW3D_MT_pose_ik(Menu):
    bl_label = "Inverse Kinematics"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.ik_add")
        layout.operator("pose.ik_clear")


class VIEW3D_MT_pose_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.constraint_add_with_targets", text="Add (With Targets)...")
        layout.operator("pose.constraints_copy")
        layout.operator("pose.constraints_clear")


class VIEW3D_MT_pose_apply(Menu):
    bl_label = "Apply"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.armature_apply")
        layout.operator("pose.visual_transform_apply")


class BoneOptions:
    def draw(self, context):
        layout = self.layout

        options = [
            "show_wire",
            "use_deform",
            "use_envelope_multiply",
            "use_inherit_rotation",
            "use_inherit_scale",
        ]

        if context.mode == 'EDIT_ARMATURE':
            bone_props = bpy.types.EditBone.bl_rna.properties
            data_path_iter = "selected_bones"
            opt_suffix = ""
            options.append("lock")
        else:  # pose-mode
            bone_props = bpy.types.Bone.bl_rna.properties
            data_path_iter = "selected_pose_bones"
            opt_suffix = "bone."

        for opt in options:
            props = layout.operator("wm.context_collection_boolean_set", text=bone_props[opt].name,
                                    text_ctxt=i18n_contexts.default)
            props.data_path_iter = data_path_iter
            props.data_path_item = opt_suffix + opt
            props.type = self.type


class VIEW3D_MT_bone_options_toggle(Menu, BoneOptions):
    bl_label = "Toggle Bone Options"
    type = 'TOGGLE'


class VIEW3D_MT_bone_options_enable(Menu, BoneOptions):
    bl_label = "Enable Bone Options"
    type = 'ENABLE'


class VIEW3D_MT_bone_options_disable(Menu, BoneOptions):
    bl_label = "Disable Bone Options"
    type = 'DISABLE'

# ********** Edit Menus, suffix from ob.type **********


# Workaround to separate the tooltips for Show Hide for Mesh in Edit Mode
class VIEW3D_mesh_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected geometry in Edit Mode"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.hide(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_edit_mesh_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.reveal", text="Show Hidden")
        layout.operator("mesh.hide", text="Hide Selected").unselected = False
        layout.operator("mesh.hide_unselected", text="Hide Unselected")


class VIEW3D_MT_edit_mesh(Menu):
    bl_label = "Mesh"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        layout.menu("VIEW3D_MT_transform")
        layout.operator("object.vertex_group_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mesh.duplicate_move")
        layout.menu("VIEW3D_MT_edit_mesh_delete")   

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_select_mode")
        layout.menu("VIEW3D_MT_edit_mesh_vertices")
        layout.menu("VIEW3D_MT_edit_mesh_edges")
        layout.menu("VIEW3D_MT_edit_mesh_faces")
        layout.menu("VIEW3D_MT_edit_mesh_clean")

        layout.separator()

        layout.menu("VIEW3D_subdivision_set")
        layout.operator("mesh.symmetrize")
        layout.operator("mesh.noise", icon='NOISE')
        layout.operator("mesh.symmetry_snap")
        layout.operator_menu_enum("mesh.sort_elements", "type", text="Sort Elements...")

        layout.separator()

        layout.prop(toolsettings, "use_mesh_automerge")
        layout.prop_menu_enum(toolsettings, "proportional_edit")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_show_hide")# bfa - the new show hide menu with separated tooltip


class VIEW3D_MT_edit_mesh_select_mode(Menu):
    bl_label = "Mesh Select Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.select_mode", text="Vertex", icon='VERTEXSEL').type = 'VERT'
        layout.operator("mesh.select_mode", text="Edge", icon='EDGESEL').type = 'EDGE'
        layout.operator("mesh.select_mode", text="Face", icon='FACESEL').type = 'FACE'


class VIEW3D_MT_edit_mesh_extrude_dupli(bpy.types.Operator):
    """Duplicate or Extrude to Cursor\nCreates a slightly rotated copy of the current mesh selection\nThe tool can also extrude the selected geometry, dependant of the selection\nHotkey tool! """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.dupli_extrude_cursor_norotate"        # unique identifier for buttons and menu items to reference.
    bl_label = "Duplicate or Extrude to Cursor"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.dupli_extrude_cursor('INVOKE_DEFAULT',rotate_source = False)
        return {'FINISHED'}

class VIEW3D_MT_edit_mesh_extrude_dupli_rotate(bpy.types.Operator):
    """Duplicate or Extrude to Cursor Rotated\nCreates a slightly rotated copy of the current mesh selection, and rotates the source slightly\nThe tool can also extrude the selected geometry, dependant of the selection\nHotkey tool!"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.dupli_extrude_cursor_rotate"        # unique identifier for buttons and menu items to reference.
    bl_label = "Duplicate or Extrude to Cursor Rotated"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mesh.dupli_extrude_cursor('INVOKE_DEFAULT', rotate_source = True)
        return {'FINISHED'}


class VIEW3D_MT_edit_mesh_extrude(Menu):
    bl_label = "Extrude"

    _extrude_funcs = {
        'VERT': lambda layout:
            layout.operator("mesh.extrude_vertices_move", text="Vertices Only"),
        'EDGE': lambda layout:
            layout.operator("mesh.extrude_edges_move", text="Edges Only"),
        'FACE': lambda layout:
            layout.operator("mesh.extrude_faces_move", text="Individual Faces"),
        #'INDIVIDUAL': lambda layout:
        #    layout.operator("view3d.edit_mesh_extrude_individual_move", icon='EXTRUDE_INDIVIDUAL', text="Individual"),
        'REGION_VERT_NORMAL': lambda layout:
            layout.operator("view3d.edit_mesh_extrude_move_shrink_fatten", text="Region (Vertex Normals)"),
        'DUPLI_EXTRUDE': lambda layout:
            layout.operator("mesh.dupli_extrude_cursor_norotate", text="Dupli Extrude", icon='DUPLI_EXTRUDE'),
        'DUPLI_EX_ROTATE': lambda layout:
            layout.operator("mesh.dupli_extrude_cursor_rotate", text="Dupli Extrude Rotate", icon='DUPLI_EXTRUDE_ROTATE')
    }

    @staticmethod
    def extrude_options(context):
        mesh = context.object.data
        select_mode = context.tool_settings.mesh_select_mode

        menu = []
        if mesh.total_face_sel:
            menu += ['REGION_VERT_NORMAL', 'FACE']
        if mesh.total_edge_sel and (select_mode[0] or select_mode[1]):
            menu += ['EDGE']
        if mesh.total_vert_sel and select_mode[0]:
            menu += ['VERT']
        menu += ['DUPLI_EXTRUDE', 'DUPLI_EX_ROTATE']

        # should never get here
        return menu

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        for menu_id in self.extrude_options(context):
            self._extrude_funcs[menu_id](layout)


class VIEW3D_MT_edit_mesh_vertices(Menu):
    bl_label = "Vertices"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.rip_move")
        layout.operator("mesh.rip_move_fill")
        layout.operator("mesh.rip_edge_move")
        layout.operator("mesh.split")
        layout.operator("mesh.vert_connect_path", text="Connect Vertex Path")
        layout.operator("mesh.vert_connect", text="Connect Vertices")

        layout.separator()

        layout.operator("mesh.mark_sharp", text="Mark Sharp Edges").use_verts = True
        props = layout.operator("mesh.mark_sharp", text="Clear Sharp Edges")
        props.use_verts = True
        props.clear = True

        layout.separator()

        layout.operator("mesh.convex_hull")
        layout.operator("mesh.blend_from_shape")
        layout.operator("object.vertex_group_smooth")
        layout.operator("mesh.shape_propagate_to_all")

        layout.separator()

        layout.menu("VIEW3D_MT_vertex_group")
        layout.menu("VIEW3D_MT_hook")


class VIEW3D_MT_edit_mesh_edges(Menu):
    bl_label = "Edges"

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.unsubdivide")

        layout.separator()

        layout.operator("transform.edge_crease")
        layout.operator("transform.edge_bevelweight")

        layout.separator()

        layout.operator("mesh.mark_sharp")
        layout.operator("mesh.mark_sharp", text="Clear Sharp").clear = True

        layout.separator()

        if with_freestyle:
            layout.operator("mesh.mark_freestyle_edge").clear = False
            layout.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge").clear = True
            layout.separator()

        layout.operator("mesh.edge_rotate", text="Rotate Edge CW").use_ccw = False
        layout.operator("mesh.edge_rotate", text="Rotate Edge CCW").use_ccw = True

        layout.separator()

        layout.operator("mesh.edge_split")
        layout.operator("mesh.bridge_edge_loops")


class VIEW3D_MT_edit_mesh_faces(Menu):
    bl_label = "Faces"
    bl_idname = "VIEW3D_MT_edit_mesh_faces"

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = 'INVOKE_REGION_WIN'
    
        layout.operator("mesh.fill")
        layout.operator("mesh.fill_grid")
        layout.operator("mesh.beautify_fill")
        layout.operator("mesh.solidify")
        layout.operator("mesh.intersect")
        layout.operator("mesh.wireframe")

        layout.separator()

        if with_freestyle:
            layout.operator("mesh.mark_freestyle_face").clear = False
            layout.operator("mesh.mark_freestyle_face", text="Clear Freestyle Face").clear = True
            layout.separator()

        layout.operator("mesh.poke")
        props = layout.operator("mesh.quads_convert_to_tris")
        props.quad_method = props.ngon_method = 'BEAUTY'
        layout.operator("mesh.tris_convert_to_quads")
        layout.operator("mesh.face_split_by_edges")

        layout.separator()

        layout.operator("mesh.edge_rotate", text="Rotate Edge CW").use_ccw = False

        layout.separator()

        layout.operator("mesh.uvs_rotate")
        layout.operator("mesh.uvs_reverse")
        layout.operator("mesh.colors_rotate")
        layout.operator("mesh.colors_reverse")


class VIEW3D_MT_edit_mesh_normals(Menu):
    bl_label = "Normals"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.normals_make_consistent", text="Recalculate Outside").inside = False
        layout.operator("mesh.normals_make_consistent", text="Recalculate Inside").inside = True

        layout.separator()

        layout.operator("mesh.flip_normals")


class VIEW3D_MT_edit_mesh_clean(Menu):
    bl_label = "Clean up"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.delete_loose")

        layout.separator()

        layout.operator("mesh.dissolve_degenerate")
        layout.operator("mesh.face_make_planar")
        layout.operator("mesh.vert_connect_nonplanar")
        layout.operator("mesh.vert_connect_concave")
        layout.operator("mesh.fill_holes")

# Delete menu quiz
class VIEW3D_MT_edit_mesh_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("mesh.delete", "type")

        layout.separator()

        layout.operator("mesh.delete_edgeloop", text="Edge Loops")


class VIEW3D_MT_edit_gpencil_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("gpencil.delete", "type")

        layout.separator()

        layout.operator("gpencil.dissolve")


# Edit Curve
# draw_curve is used by VIEW3D_MT_edit_curve and VIEW3D_MT_edit_surface

# Workaround to separate the tooltips for Show Hide for Curve in Edit Mode
class VIEW3D_curve_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected Control Points"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "curve.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.curve.hide(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_edit_curve_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.reveal", text="Show Hidden")
        layout.operator("curve.hide", text="Hide Selected").unselected = False
        layout.operator("curve.hide_unselected", text="Hide Unselected")


def draw_curve(self, context):
    layout = self.layout

    toolsettings = context.tool_settings

    layout.menu("VIEW3D_MT_transform")
    layout.operator("object.vertex_group_mirror")
    layout.menu("VIEW3D_MT_snap")

    layout.separator()

    layout.operator("curve.spin")
    layout.operator("curve.duplicate_move")
    layout.operator("curve.split")
    layout.operator("curve.separate")
    layout.operator("curve.make_segment")
    layout.operator("curve.delete", text="Delete...")

    layout.separator()

    layout.operator("curve.smooth_tilt")
    layout.operator("curve.smooth_radius")
    layout.operator("curve.smooth_weight")
    layout.operator("curve.spline_weight_set")
    
    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_ctrlpoints")

    layout.separator()

    layout.prop_menu_enum(toolsettings, "proportional_edit")
    layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")

    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_show_hide")# bfa - the new show hide menu with separated tooltips


class VIEW3D_MT_edit_curve(Menu):
    bl_label = "Curve"

    draw = draw_curve


class VIEW3D_MT_edit_curve_ctrlpoints(Menu):
    bl_label = "Control Points"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object

        if edit_object.type == 'CURVE':
            layout.operator("transform.tilt")
            layout.operator("curve.tilt_clear")

            layout.separator()

        layout.menu("VIEW3D_MT_hook")


class VIEW3D_MT_edit_surface(Menu):
    bl_label = "Surface"

    draw = draw_curve


class VIEW3D_MT_edit_font(Menu):
    bl_label = "Text"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_edit_text_chars")

        layout.separator()

        layout.operator("font.style_toggle", text="Toggle Bold").style = 'BOLD'
        layout.operator("font.style_toggle", text="Toggle Italic").style = 'ITALIC'
        layout.operator("font.style_toggle", text="Toggle Underline").style = 'UNDERLINE'
        layout.operator("font.style_toggle", text="Toggle Small Caps").style = 'SMALL_CAPS'

        layout.separator()

        layout.operator("font.delete").type = 'NEXT_OR_SELECTION'




class VIEW3D_MT_edit_text_chars(Menu):
    bl_label = "Special Characters"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.text_insert", text="Copyright").text = "\u00A9"
        layout.operator("font.text_insert", text="Registered Trademark").text = "\u00AE"

        layout.separator()

        layout.operator("font.text_insert", text="Degree Sign").text = "\u00B0"
        layout.operator("font.text_insert", text="Multiplication Sign").text = "\u00D7"
        layout.operator("font.text_insert", text="Circle").text = "\u008A"
        layout.operator("font.text_insert", text="Superscript 1").text = "\u00B9"
        layout.operator("font.text_insert", text="Superscript 2").text = "\u00B2"
        layout.operator("font.text_insert", text="Superscript 3").text = "\u00B3"
        layout.operator("font.text_insert", text="Double >>").text = "\u00BB"
        layout.operator("font.text_insert", text="Double <<").text = "\u00AB"
        layout.operator("font.text_insert", text="Promillage").text = "\u2030"

        layout.separator()

        layout.operator("font.text_insert", text="Dutch Florin").text = "\u00A4"
        layout.operator("font.text_insert", text="British Pound").text = "\u00A3"
        layout.operator("font.text_insert", text="Japanese Yen").text = "\u00A5"

        layout.separator()

        layout.operator("font.text_insert", text="German S").text = "\u00DF"
        layout.operator("font.text_insert", text="Spanish Question Mark").text = "\u00BF"
        layout.operator("font.text_insert", text="Spanish Exclamation Mark").text = "\u00A1"


class VIEW3D_MT_edit_meta(Menu):
    bl_label = "Metaball"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        layout.menu("VIEW3D_MT_transform")
        layout.operator("object.vertex_group_mirror")
        layout.menu("VIEW3D_MT_snap")

        layout.separator()

        layout.operator("mball.delete_metaelems", text="Delete...")
        layout.operator("mball.duplicate_metaelems")

        layout.separator()

        layout.prop_menu_enum(toolsettings, "proportional_edit")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_meta_showhide")

# Workaround to separate the tooltips for Show Hide for Curve in Edit Mode
class VIEW3D_MT_edit_meta_showhide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected metaelement(s)"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mball.hide_metaelems_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.mball.hide_metaelems(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_edit_meta_showhide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("mball.reveal_metaelems", text="Show Hidden")
        layout.operator("mball.hide_metaelems", text="Hide Selected").unselected = False
        layout.operator("mball.hide_metaelems_unselected", text="Hide Unselected")


class VIEW3D_MT_edit_lattice(Menu):
    bl_label = "Lattice"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_mirror")

        layout.menu("VIEW3D_MT_snap")
        layout.operator_menu_enum("lattice.flip", "axis")

        layout.separator()

        layout.operator("lattice.make_regular")

        layout.separator()

        layout.prop_menu_enum(toolsettings, "proportional_edit")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")


# Workaround to separate the tooltips for Show Hide for Armature in Edit Mode
class VIEW3D_armature_hide_unselected(bpy.types.Operator):
    """Hide Unselected\nHide unselected Bones in Edit Mode"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "armature.hide_unselected"        # unique identifier for buttons and menu items to reference.
    bl_label = "Hide Unselected"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.armature.hide(unselected = True)
        return {'FINISHED'}  


class VIEW3D_MT_armature_show_hide(Menu):
    bl_label = "Show/Hide"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.reveal", text="Show Hidden")
        layout.operator("armature.hide", text="Hide Selected").unselected = False
        layout.operator("armature.hide_unselected", text="Hide Unselected")

class VIEW3D_MT_edit_armature(Menu):
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data

        layout.menu("VIEW3D_MT_transform_armature")
        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_snap")
        layout.menu("VIEW3D_MT_edit_armature_roll")

        layout.separator()

        layout.operator("armature.extrude_move")
        layout.operator("armature.extrude_forked")

        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked")

        layout.operator("armature.duplicate_move")
        layout.operator("armature.merge")
        layout.operator("armature.fill")
        layout.operator("armature.delete")
        layout.operator("armature.split")
        layout.operator("armature.separate")

        layout.separator()

        layout.operator("armature.subdivide", text="Subdivide")
        layout.operator("armature.switch_direction", text="Switch Direction")

        layout.separator()

        layout.operator_context = 'EXEC_AREA'
        layout.operator("armature.symmetrize")
        layout.operator("armature.autoside_names", text="AutoName Left/Right").type = 'XAXIS'
        layout.operator("armature.autoside_names", text="AutoName Front/Back").type = 'YAXIS'
        layout.operator("armature.autoside_names", text="AutoName Top/Bottom").type = 'ZAXIS'
        layout.operator("armature.flip_names")

        layout.separator()

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("armature.armature_layers")
        layout.operator("armature.bone_layers")

        layout.separator()

        layout.menu("VIEW3D_MT_armature_show_hide") # bfa - the new show hide menu with split tooltip
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")

class VIEW3D_MT_edit_armature_roll(Menu):
    bl_label = "Bone Roll"

    def draw(self, context):
        layout = self.layout

        layout.operator_menu_enum("armature.calculate_roll", "type")

        layout.separator()

        layout.operator("transform.transform", text="Set Roll").mode = 'BONE_ROLL'


class VIEW3D_MT_edit_armature_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.delete", text="Delete Bones")

        layout.separator()

        layout.operator("armature.dissolve", text="Dissolve")


# ********** Panel **********

class VIEW3D_PT_view3d_name(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Item"

    @classmethod
    def poll(cls, context):
        return (context.space_data and context.active_object)

    def draw(self, context):
        layout = self.layout

        ob = context.active_object
        row = layout.row()
        row.label(text="", icon='OBJECT_DATA')
        row.prop(ob, "name", text="")

        if ob.type == 'ARMATURE' and ob.mode in {'EDIT', 'POSE'}:
            bone = context.active_bone
            if bone:
                row = layout.row()
                row.label(text="", icon='BONE_DATA')
                row.prop(bone, "name", text="")



class VIEW3D_PT_grease_pencil(GreasePencilDataPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    # NOTE: this is just a wrapper around the generic GP Panel


class VIEW3D_PT_view3d_properties(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view)

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        col = layout.column()
        col.active = bool(view.region_3d.view_perspective != 'CAMERA' or view.region_quadviews)
        col.prop(view, "lens")
          
        col = layout.column(align=True)
        col.label(text="Clip:")
        col.prop(view, "clip_start", text="Start")
        col.prop(view, "clip_end", text="End")
        
        col = layout.column(align=True)
        col.prop(view, "use_render_border")
        
        wm = context.window_manager # Our bool is in the windows_manager
  
        # The subtab is closed by default.
        # When the click at it then it opens. And shows the hidden ui elements.
        if not wm.subtab_3dview_properties_view_lock:
            layout.prop(wm,"subtab_3dview_properties_view_lock", emboss=False, icon="TRIA_RIGHT", text="- Lock -")

        else:
            layout.prop(wm,"subtab_3dview_properties_view_lock", emboss=False, icon="TRIA_DOWN", text="+ Lock +")
            
            col = layout.column()
            col.prop(view, "lock_camera_and_layers")

            subcol = col.column(align=True)
            subcol.enabled = not view.lock_camera_and_layers
            
            subcol.label(text="Local Camera:")
            subcol.prop(view, "camera", text="")

            col = layout.column(align=True)
            col.active = view.region_3d.view_perspective != 'CAMERA'
            
            col = layout.column()
            col.prop(view, "lock_camera")
            
            col.label(text="Lock to Object:")
            col.prop(view, "lock_object", text="")
            lock_object = view.lock_object
            if lock_object:
                if lock_object.type == 'ARMATURE':
                    col.prop_search(view, "lock_bone", lock_object.data,
                                    "edit_bones" if lock_object.mode == 'EDIT'
                                    else "bones",
                                    text="")
            else:
                col.prop(view, "lock_cursor", text="Lock to Cursor")


class VIEW3D_PT_view3d_cursor(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "3D Cursor"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view is not None)

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        layout.column().prop(view, "cursor_location", text="Location")


class VIEW3D_PT_view3d_display(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view)

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        scene = context.scene

        # bfa - Our checkbox for icon or text buttons.
        # The prop is defined in the __init__.py. When we define it in this file
        # then we get an error that the scene has no UITweaks attribute. 
        # Most probably a order of registration problem.
        layout.prop(scene.UItweaks, "icon_or_text")
        col = layout.column()
        col.prop(view, "show_cursor", text="3D Cursor") # bfa - show hide cursor checkbox
  
        col = layout.column()
        display_all = not view.show_only_render
        col.active = display_all
        col.prop(view, "hide_groundgrid", text="Groundgrid") # bfa - show hide groundgrid checkbox

        if view.hide_groundgrid:
            col = layout.column()
            col.active = display_all
            split = col.split(percentage=0.55)
            split.prop(view, "show_floor", text="Grid Floor")

            row = split.row(align=True)
            row.prop(view, "show_axis_x", text="X", toggle=True)
            row.prop(view, "show_axis_y", text="Y", toggle=True)
            row.prop(view, "show_axis_z", text="Z", toggle=True)

            sub = col.column(align=True)
            sub.active = (display_all and view.show_floor)
            sub.prop(view, "grid_lines", text="Lines")
            sub.prop(view, "grid_scale", text="Scale")
            subsub = sub.column(align=True)
            subsub.active = scene.unit_settings.system == 'NONE'
            subsub.prop(view, "grid_subdivisions", text="Subdivisions")

        if view.region_quadviews:
            region = view.region_quadviews[2]
            col = layout.column()
            col.prop(region, "lock_rotation")
            row = col.row()
            row.enabled = region.lock_rotation
            row.prop(region, "show_sync_view")
            row = col.row()
            row.enabled = region.lock_rotation and region.show_sync_view
            row.prop(region, "use_box_clip")

        wm = context.window_manager # Our bool is in the windows_manager
        # The subtab is closed by default.
        # When the click at it then it opens. And shows the hidden ui elements.
        if not wm.subtab_3dview_properties_display_misc:
            layout.prop(wm,"subtab_3dview_properties_display_misc", emboss=False, icon="TRIA_RIGHT", text="- Miscellaneous -")

        else:
            layout.prop(wm,"subtab_3dview_properties_display_misc", emboss=False, icon="TRIA_DOWN", text="+ Miscellaneous +")

            col = layout.column()
            col.prop(view, "show_only_render")
            col.prop(view, "show_world")
            col.prop(view, "show_outline_selected")
            col.prop(view, "show_all_objects_origin")
            col.prop(view, "show_relationship_lines")
            
            col.prop(view, "lock_3d_cursor", text="Lock 3D Cursor") # bfa - show hide lock 3d cursor checkbox
            

class VIEW3D_PT_view3d_stereo(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Stereoscopy"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene

        multiview = scene.render.use_multiview
        return context.space_data and multiview

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        basic_stereo = context.scene.render.views_format == 'STEREO_3D'

        col = layout.column()
        col.row().prop(view, "stereo_3d_camera", expand=True)

        col.label(text="Display:")
        row = col.row()
        row.active = basic_stereo
        row.prop(view, "show_stereo_3d_cameras")
        row = col.row()
        row.active = basic_stereo
        split = row.split()
        split.prop(view, "show_stereo_3d_convergence_plane")
        split = row.split()
        split.prop(view, "stereo_3d_convergence_plane_alpha", text="Alpha")
        split.active = view.show_stereo_3d_convergence_plane
        row = col.row()
        split = row.split()
        split.prop(view, "show_stereo_3d_volume")
        split = row.split()
        split.prop(view, "stereo_3d_volume_alpha", text="Alpha")


class VIEW3D_PT_view3d_shading(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Shading"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        scene = context.scene
        gs = scene.game_settings
        obj = context.object

        col = layout.column()

        if not scene.render.use_shading_nodes:
            col.prop(gs, "material_mode", text="")

        if view.viewport_shade == 'SOLID':
            col.prop(view, "show_textured_solid")
            col.prop(view, "use_matcap")
            if view.use_matcap:
                col.template_icon_view(view, "matcap_icon")
        elif view.viewport_shade == 'TEXTURED':
            if scene.render.use_shading_nodes or gs.material_mode != 'GLSL':
                col.prop(view, "show_textured_shadeless")

        col.prop(view, "show_backface_culling")

        if view.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:
            if obj and obj.mode == 'EDIT':
                col.prop(view, "show_occlude_wire")

        fx_settings = view.fx_settings

        if view.viewport_shade not in {'BOUNDBOX', 'WIREFRAME'}:
            sub = col.column()
            sub.active = view.region_3d.view_perspective == 'CAMERA'
            sub.prop(fx_settings, "use_dof")
            col.prop(fx_settings, "use_ssao", text="Ambient Occlusion")
            if fx_settings.use_ssao:
                ssao_settings = fx_settings.ssao
                subcol = col.column(align=True)
                subcol.prop(ssao_settings, "factor")
                subcol.prop(ssao_settings, "distance_max")
                subcol.prop(ssao_settings, "attenuation")
                subcol.prop(ssao_settings, "samples")
                subcol.prop(ssao_settings, "color")


class VIEW3D_PT_view3d_motion_tracking(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Motion Tracking"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view)

    def draw_header(self, context):
        view = context.space_data

        self.layout.prop(view, "show_reconstruction", text="")

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        col = layout.column()
        col.active = view.show_reconstruction
        col.prop(view, "show_camera_path", text="Camera Path")
        col.prop(view, "show_bundle_names", text="3D Marker Names")
        col.label(text="Track Type and Size:")
        row = col.row(align=True)
        row.prop(view, "tracks_draw_type", text="")
        row.prop(view, "tracks_draw_size", text="")


class VIEW3D_PT_view3d_meshdisplay(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Mesh Display"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # The active object check is needed because of local-mode
        return (context.active_object and (context.mode == 'EDIT_MESH'))

    def draw(self, context):
        layout = self.layout
        with_freestyle = bpy.app.build_options.freestyle

        mesh = context.active_object.data
        scene = context.scene
        
        ################# Normals

        col = layout.column()

        col.label(text="Normals:")
        row = col.row(align=True)

        row.prop(mesh, "show_normal_vertex", text="", icon='VERTEXSEL')
        row.prop(mesh, "show_normal_loop", text="", icon='LOOPSEL')
        row.prop(mesh, "show_normal_face", text="", icon='FACESEL')

        sub = row.row(align=True)
        sub.active = mesh.show_normal_vertex or mesh.show_normal_face or mesh.show_normal_loop
        sub.prop(scene.tool_settings, "normal_size", text="Size")
        
        wm = context.window_manager # Our bool is in the windows_manager
        
        ################ Overlay Options
  
        # The subtab is closed by default.
        # When the click at it then it opens. And shows the hidden ui elements.
        if not wm.subtab_3dview_properties_meshdisplay_overlay:
            layout.prop(wm,"subtab_3dview_properties_meshdisplay_overlay", emboss=False, icon="TRIA_RIGHT", text="- Overlay Options -")

        else:
            layout.prop(wm,"subtab_3dview_properties_meshdisplay_overlay", emboss=False, icon="TRIA_DOWN", text="+ Overlay Options +")
            
            split = layout.split()
            col = split.column()
            col.prop(mesh, "show_faces", text="Faces")
            col.prop(mesh, "show_edges", text="Edges")
            col.prop(mesh, "show_edge_crease", text="Creases")
            if with_freestyle:
                col.prop(mesh, "show_edge_seams", text="Seams")

            layout.prop(mesh, "show_weight")

            col = split.column()
            if not with_freestyle:
                col.prop(mesh, "show_edge_seams", text="Seams")
            col.prop(mesh, "show_edge_sharp", text="Sharp", text_ctxt=i18n_contexts.plural)
            col.prop(mesh, "show_edge_bevel_weight", text="Bevel")
            if with_freestyle:
                col.prop(mesh, "show_freestyle_edge_marks", text="Edge Marks")
                col.prop(mesh, "show_freestyle_face_marks", text="Face Marks")
                
        
        ################## Info options

  
        # The subtab is closed by default.
        # When the click at it then it opens. And shows the hidden ui elements.
        if not wm.subtab_3dview_properties_meshdisplay_info:
            layout.prop(wm,"subtab_3dview_properties_meshdisplay_info", emboss=False, icon="TRIA_RIGHT", text="- Info Options -")

        else:
            layout.prop(wm,"subtab_3dview_properties_meshdisplay_info", emboss=False, icon="TRIA_DOWN", text="+ Info Options +")

            split = layout.split()
            col = split.column()
            col.label(text="Edge Info:")
            col.prop(mesh, "show_extra_edge_length", text="Length")
            col.prop(mesh, "show_extra_edge_angle", text="Angle")
            col = split.column()
            col.label(text="Face Info:")
            col.prop(mesh, "show_extra_face_area", text="Area")
            col.prop(mesh, "show_extra_face_angle", text="Angle")
            if bpy.app.debug:
                layout.prop(mesh, "show_extra_indices")


class VIEW3D_PT_view3d_meshstatvis(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Mesh Analysis"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # The active object check is needed because of local-mode
        return (context.active_object and (context.mode == 'EDIT_MESH'))

    def draw_header(self, context):
        mesh = context.active_object.data

        self.layout.prop(mesh, "show_statvis", text="")

    def draw(self, context):
        layout = self.layout

        mesh = context.active_object.data
        statvis = context.tool_settings.statvis
        layout.active = mesh.show_statvis

        layout.prop(statvis, "type")
        statvis_type = statvis.type
        if statvis_type == 'OVERHANG':
            row = layout.row(align=True)
            row.prop(statvis, "overhang_min", text="")
            row.prop(statvis, "overhang_max", text="")
            layout.prop(statvis, "overhang_axis", expand=True)
        elif statvis_type == 'THICKNESS':
            row = layout.row(align=True)
            row.prop(statvis, "thickness_min", text="")
            row.prop(statvis, "thickness_max", text="")
            layout.prop(statvis, "thickness_samples")
        elif statvis_type == 'INTERSECT':
            pass
        elif statvis_type == 'DISTORT':
            row = layout.row(align=True)
            row.prop(statvis, "distort_min", text="")
            row.prop(statvis, "distort_max", text="")
        elif statvis_type == 'SHARP':
            row = layout.row(align=True)
            row.prop(statvis, "sharp_min", text="")
            row.prop(statvis, "sharp_max", text="")


class VIEW3D_PT_view3d_curvedisplay(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Curve Display"

    @classmethod
    def poll(cls, context):
        editmesh = context.mode == 'EDIT_CURVE'
        return (editmesh)

    def draw(self, context):
        layout = self.layout

        curve = context.active_object.data

        col = layout.column()
        row = col.row()
        row.prop(curve, "show_handles", text="Handles")
        row.prop(curve, "show_normal_face", text="Normals")
        col.prop(context.scene.tool_settings, "normal_size", text="Normal Size")


class VIEW3D_PT_background_image(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Background Images"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        view = context.space_data

        self.layout.prop(view, "show_background_images", text="")

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        use_multiview = context.scene.render.use_multiview

        col = layout.column()
        col.operator("view3d.background_image_add", text="Add Image")

        for i, bg in enumerate(view.background_images):
            layout.active = view.show_background_images
            box = layout.box()
            row = box.row(align=True)
            row.prop(bg, "show_expanded", text="", emboss=False)
            if bg.source == 'IMAGE' and bg.image:
                row.prop(bg.image, "name", text="", emboss=False)
            elif bg.source == 'MOVIE_CLIP' and bg.clip:
                row.prop(bg.clip, "name", text="", emboss=False)
            else:
                row.label(text="Not Set")

            if bg.show_background_image:
                row.prop(bg, "show_background_image", text="", emboss=False, icon='RESTRICT_VIEW_OFF')
            else:
                row.prop(bg, "show_background_image", text="", emboss=False, icon='RESTRICT_VIEW_ON')

            row.operator("view3d.background_image_remove", text="", emboss=False, icon='X').index = i            

            if bg.show_expanded:
                row = box.row()
                row.prop(bg, "source", expand=True)
                
                has_bg = False
                if bg.source == 'IMAGE':
                    row = box.row()
                    row.template_ID(bg, "image", open="image.open")
                    if bg.image is not None:
                        has_bg = True
                        
                        # Settings subtab
                        wm = context.window_manager # Our bool is in the windows_manager
                        if not wm.subtab_3dview_properties_bgimg_settings:
                            box.prop(wm,"subtab_3dview_properties_bgimg_settings", emboss=False, icon="TRIA_RIGHT", text="- Settings -")

                        else:
                            box.prop(wm,"subtab_3dview_properties_bgimg_settings", emboss=False, icon="TRIA_DOWN", text="+ Settings +")
                            
                            box.prop(bg, "opacity", slider=True)
                            box.prop(bg, "view_axis", text="Axis")
                            box.template_image(bg, "image", bg.image_user, compact=True)                          

                            if use_multiview and bg.view_axis in {'CAMERA','ALL'}:
                                box.prop(bg.image, "use_multiview")

                                column = box.column()
                                column.active = bg.image.use_multiview

                                column.label(text="Views Format:")
                                column.row().prop(bg.image, "views_format", expand=True)

                                sub = column.box()
                                sub.active = bg.image.views_format == 'STEREO_3D'
                                sub.template_image_stereo_3d(bg.image.stereo_3d_format)

                elif bg.source == 'MOVIE_CLIP':
                
                    box.prop(bg, "opacity", slider=True)
                    box.prop(bg, "view_axis", text="Axis")
                    box.prop(bg, "use_camera_clip")                   

                    column = box.column()
                    column.active = not bg.use_camera_clip
                    column.template_ID(bg, "clip", open="clip.open")

                    if bg.clip:
                        column.template_movieclip(bg, "clip", compact=True)

                    if bg.use_camera_clip or bg.clip:
                        has_bg = True

                    column = box.column()
                    column.active = has_bg
                    column.prop(bg.clip_user, "proxy_render_size", text="")
                    column.prop(bg.clip_user, "use_render_undistorted")
                    
                if has_bg:
                    
                    # Align Subtab
                    wm = context.window_manager # Our bool is in the windows_manager
                    if not wm.subtab_3dview_properties_bgimg_align:
                        box.prop(wm,"subtab_3dview_properties_bgimg_align", emboss=False, icon="TRIA_RIGHT", text="- Align -")

                    else:
                        box.prop(wm,"subtab_3dview_properties_bgimg_align", emboss=False, icon="TRIA_DOWN", text="+ Align +")

                        col = box.column()
                        col.row().prop(bg, "draw_depth", expand=True)

                        if bg.view_axis in {'CAMERA', 'ALL'}:
                            col.row().prop(bg, "frame_method", expand=True)

                        box = col.box()
                        row = box.row()
                        row.prop(bg, "offset_x", text="X")
                        row.prop(bg, "offset_y", text="Y")

                        row = box.row()
                        row.prop(bg, "use_flip_x")
                        row.prop(bg, "use_flip_y")

                        row = box.row()
                        if bg.view_axis != 'CAMERA':
                            row.prop(bg, "rotation")
                            row.prop(bg, "size")


class VIEW3D_PT_etch_a_ton(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Skeleton Sketching"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        scene = context.space_data
        ob = context.active_object
        return scene and ob and ob.type == 'ARMATURE' and ob.mode == 'EDIT'

    def draw_header(self, context):
        layout = self.layout
        toolsettings = context.scene.tool_settings

        layout.prop(toolsettings, "use_bone_sketching", text="")

    def draw(self, context):
        layout = self.layout

        toolsettings = context.scene.tool_settings

        col = layout.column()

        col.prop(toolsettings, "use_etch_quick")
        col.prop(toolsettings, "use_etch_overdraw")

        col.separator()

        col.prop(toolsettings, "etch_convert_mode")

        if toolsettings.etch_convert_mode == 'LENGTH':
            col.prop(toolsettings, "etch_length_limit")
        elif toolsettings.etch_convert_mode == 'ADAPTIVE':
            col.prop(toolsettings, "etch_adaptive_limit")
        elif toolsettings.etch_convert_mode == 'FIXED':
            col.prop(toolsettings, "etch_subdivision_number")
        elif toolsettings.etch_convert_mode == 'RETARGET':
            col.prop(toolsettings, "etch_template")
            col.prop(toolsettings, "etch_roll_mode")

            col.separator()

            colsub = col.column(align=True)
            colsub.prop(toolsettings, "use_etch_autoname")
            sub = colsub.column(align=True)
            sub.enabled = not toolsettings.use_etch_autoname
            sub.prop(toolsettings, "etch_number")
            sub.prop(toolsettings, "etch_side")

        col.separator()

        col.operator("sketch.convert", text="Convert to Bones")
        col.operator("sketch.delete", text="Delete Strokes")


class VIEW3D_PT_context_properties(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Properties"
    bl_options = {'DEFAULT_CLOSED'}

    def _active_context_member(context):
        obj = context.object
        if obj:
            mode = obj.mode
            if mode == 'POSE':
                return "active_pose_bone"
            elif mode == 'EDIT' and obj.type == 'ARMATURE':
                return "active_bone"
            else:
                return "object"

        return ""

    @classmethod
    def poll(cls, context):
        import rna_prop_ui
        member = cls._active_context_member(context)

        if member:
            context_member, member = rna_prop_ui.rna_idprop_context_value(context, member, object)
            return context_member and rna_prop_ui.rna_idprop_has_properties(context_member)

        return False

    def draw(self, context):
        import rna_prop_ui
        member = VIEW3D_PT_context_properties._active_context_member(context)

        if member:
            # Draw with no edit button
            rna_prop_ui.draw(self.layout, context, member, object, False)

#-----------------------------------------------------------------------------

def register():
    
    # Subtab bools
    bpy.types.WindowManager.subtab_3dview_properties_view_lock = bpy.props.BoolProperty(name="Lock", description="Contains the Lock Items", default = False)
    
    bpy.utils.register_module(__name__)

def unregister():
    
    # Subtab bools
    del bpy.types.WindowManager.subtab_3dview_properties_view_lock # Unregister our flag when unregister.   
    
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
