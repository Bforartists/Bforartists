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
from bl_ui.properties_grease_pencil_common import (
        GreasePencilDataPanel,
        GreasePencilPaletteColorPanel,
        )
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
                    (mode in {'WEIGHT_PAINT', 'VERTEX_PAINT'})):
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
        show_snap = False
        if obj is None:
            show_snap = True
        else:
            if mode not in {'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT', 'TEXTURE_PAINT'}:
                show_snap = True
            else:
                paint_settings = UnifiedPaintPanel.paint_settings(context)
                if paint_settings:
                    brush = paint_settings.brush
                    if brush and brush.stroke_method == 'CURVE':
                        show_snap = True

        if show_snap:
            snap_element = toolsettings.snap_element
            row = layout.row(align=True)
            row.prop(toolsettings, "use_snap", text="")
            row.prop(toolsettings, "snap_element", icon_only=True)
            if snap_element == 'INCREMENT':
                row.prop(toolsettings, "use_snap_grid_absolute", text="")
            else:
                row.prop(toolsettings, "snap_target", text="")
                if obj:
                    if mode == 'EDIT':
                        row.prop(toolsettings, "use_snap_self", text="")
                    if mode in {'OBJECT', 'POSE', 'EDIT'} and snap_element != 'VOLUME':
                        row.prop(toolsettings, "use_snap_align_rotation", text="")

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
        gp_edit = context.gpencil_data and context.gpencil_data.use_stroke_edit_mode

        layout.menu("VIEW3D_MT_view")
        layout.menu("VIEW3D_MT_view_navigation")

        # Select Menu
        if gp_edit:
            layout.menu("VIEW3D_MT_select_gpencil")
        elif mode_string in {'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE'}:
            mesh = obj.data
            if mesh.use_paint_mask:
                layout.menu("VIEW3D_MT_select_paint_mask")
            elif mesh.use_paint_mask_vertex and mode_string in {'PAINT_WEIGHT', 'PAINT_VERTEX'}:
                layout.menu("VIEW3D_MT_select_paint_mask_vertex")
        elif mode_string != 'SCULPT':
            layout.menu("VIEW3D_MT_select_%s" % mode_string.lower())

        if gp_edit:
            layout.menu("VIEW3D_MT_edit_gpencil")
        elif edit_object:
            layout.menu("VIEW3D_MT_edit_%s" % edit_object.type.lower())
        elif obj:
            if mode_string != 'PAINT_TEXTURE':
                layout.menu("VIEW3D_MT_%s" % mode_string.lower())
            #if mode_string in {'SCULPT', 'PAINT_VERTEX', 'PAINT_WEIGHT', 'PAINT_TEXTURE'}: # bfa - deactivated the brush menu in all other modes for now.
            if mode_string in {'SCULPT'}:
                layout.menu("VIEW3D_MT_brush")
            if mode_string == 'SCULPT':
                layout.menu("VIEW3D_MT_hide_mask")
        else:
            layout.menu("VIEW3D_MT_object")


# ********** Menu **********


# ********** Utilities **********


# Standard transforms which apply to all cases
# NOTE: this doesn't seem to be able to be used directly
class VIEW3D_MT_transform_base(Menu):
    bl_label = "Transform"

    # TODO: get rid of the custom text strings?
    def draw(self, context):
        layout = self.layout

        layout.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
        layout.operator("transform.shear", text="Shear", icon = "SHEAR")
        layout.operator("transform.bend", text="Bend", icon = "BEND")
        layout.operator("transform.push_pull", text="Push/Pull", icon = 'PUSH_PULL')

        if context.mode != 'OBJECT':
            layout.operator("transform.vertex_warp", text="Warp", icon = "MOD_WARP")
            layout.operator("transform.vertex_random", text="Randomize", icon = 'RANDOMIZE')

# Generic transform menu - geometry types
class VIEW3D_MT_transform(VIEW3D_MT_transform_base):
    def draw(self, context):
        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # generic...
        layout = self.layout

        layout.separator()

        #layout.operator("transform.translate", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
        layout.operator("transform.translate_texture", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
        #layout.operator("transform.resize", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True
        layout.operator("transform.resize_texture", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True

        layout.separator()

        layout.operator("transform.skin_resize", text="Skin Resize", icon = "MOD_SKIN")


# Object-specific extensions to Transform menu
class VIEW3D_MT_transform_object(VIEW3D_MT_transform_base):
    def draw(self, context):
        layout = self.layout

        # base menu
        VIEW3D_MT_transform_base.draw(self, context)

        # object-specific option follow...
        layout.separator()

        #layout.operator("transform.translate", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
        layout.operator("transform.translate_texture", text="Move Texture Space", icon = "MOVE_TEXTURESPACE").texture_space = True
        #layout.operator("transform.resize", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True
        layout.operator("transform.resize_texture", text="Scale Texture Space", icon = "SCALE_TEXTURESPACE").texture_space = True

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("transform.transform", text="Align to Transform Orientation", icon = "ALIGN_TRANSFORM").mode = 'ALIGN'  # XXX see alignmenu() in edit.c of b2.4x to get this working

        layout.separator()

        layout.operator_context = 'EXEC_AREA'

        layout.operator("object.randomize_transform", icon = "RANDOMIZE_TRANSFORM")
        layout.operator("object.align", icon = "ALIGN")


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
            layout.operator("armature.align",icon = "ALIGN")

class VIEW3D_MT_snap(Menu):
    bl_label = "Snap"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.snap_selected_to_grid", text="Selection to Grid")
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_active", text="Selection to Active")

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

         # OpenGL render
        layout.operator("render.opengl", text="OpenGL Render Image", icon='RENDER_STILL')
        layout.operator("render.opengl", text="OpenGL Render Animation", icon='RENDER_ANIMATION').animation = True

        layout.separator()

        layout.operator("view3d.object_as_camera", icon = 'VIEW_SWITCHACTIVECAM')
        layout.operator("view3d.viewnumpad", text="Active Camera", icon = 'VIEW_SWITCHTOCAM').type = 'CAMERA'
        layout.operator("view3d.view_center_camera", icon = "VIEWCAMERACENTER")

        layout.separator()

        layout.menu("VIEW3D_MT_view_align")
        layout.menu("VIEW3D_MT_view_align_selected")

        layout.separator()

        layout.operator_context = 'INVOKE_REGION_WIN'

        # restrict render and clear restrict render. I would love to simply disable it, 
        # means grey out when there are no objects selected. But that's ways too much hassle. 
        # So for now we simply hide the two menu items when there is no object selected.

        if context.object :
            props = layout.operator("object.hide_render_set", text = "Render unselected", icon = "RESTRICT_RENDER_OFF")
            props = layout.operator("object.isolate_type_render", text = "Render selected", icon = "RESTRICT_RENDER_OFF")
            props = layout.operator("object.hide_render_clear_all", text = "Render all", icon = "RESTRICT_RENDER_OFF")

            layout.separator()

        layout.operator("view3d.clip_border", text="Clipping Border", icon = "CLIPPINGBORDER")
        layout.operator("view3d.clear_render_border", text="Clear Render Border", icon = "RENDERBORDER_CLEAR")
        layout.operator("view3d.render_border", text="Render Border", icon = "RENDERBORDER").camera_only = False
   
        layout.separator()

        layout.operator("view3d.localview", text="View Global/Local", icon = "VIEW_GLOBAL_LOCAL")
        layout.operator("view3d.view_selected_all_regions", text = "View Selected all Regions", icon = "VIEW_SELECTED" )
        layout.operator("view3d.view_selected", icon = "VIEW_SELECTED").use_all_regions = False
        layout.operator("view3d.view_all_all_regions", text = "View All all Regions", icon = "VIEWALL" ) # bfa - separated tooltip
        layout.operator("view3d.view_all_center_cursor", text="Center Cursor and View All", icon = "VIEWALL_RESETCURSOR") # bfa - separated tooltip
        layout.operator("view3d.view_all", icon = "VIEWALL").center = False

        layout.separator()

        layout.operator("screen.area_dupli", icon = "NEW_WINDOW")
        layout.operator("screen.region_quadview", icon = "QUADVIEW")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area", icon = "MAXIMIZE_AREA") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", icon = "FULLSCREEN_AREA", text = "Toggle Fullscreen Area").use_hide_panels = True


class VIEW3D_MT_view_navigation(Menu):
    bl_label = "Navi"

    def draw(self, context):
        from math import pi
        layout = self.layout

        layout.operator("view3d.view_orbit", text= "Orbit Down", icon = "ORBIT_DOWN").type='ORBITDOWN'
        layout.operator("view3d.view_orbit", text= "Orbit Up", icon = "ORBIT_UP").type='ORBITUP'
        layout.operator("view3d.view_orbit", text= "Orbit Right", icon = "ORBIT_RIGHT").type='ORBITRIGHT'
        layout.operator("view3d.view_orbit", text= "Orbit Left", icon = "ORBIT_LEFT").type='ORBITLEFT'
        props = layout.operator("view3d.view_orbit", "Orbit Opposite", icon = "ORBIT_OPPOSITE")
        props.type = 'ORBITRIGHT'
        props.angle = pi

        layout.separator()

        layout.operator("view3d.view_roll", text="Roll Left", icon = "ROLL_LEFT").angle = pi / -12.0
        layout.operator("view3d.view_roll", text="Roll Right", icon = "ROLL_RIGHT").angle = pi / 12.0

        layout.separator()

        layout.operator("view3d.view_pan", text= "Pan Down", icon = "PAN_DOWN").type = 'PANDOWN'
        layout.operator("view3d.view_pan", text= "Pan Up", icon = "PAN_UP").type = 'PANUP'
        layout.operator("view3d.view_pan", text= "Pan Right", icon = "PAN_RIGHT").type = 'PANRIGHT'
        layout.operator("view3d.view_pan", text= "Pan Left", icon = "PAN_LEFT").type = 'PANLEFT'

        layout.separator()

        layout.operator("view3d.zoom_border", text="Zoom Border", icon = "ZOOM_BORDER")
        layout.operator("view3d.zoom", text="Zoom In", icon = "ZOOM_IN").delta = 1
        layout.operator("view3d.zoom", text="Zoom Out", icon = "ZOOM_OUT").delta = -1
        layout.operator("view3d.zoom_camera_1_to_1", text="Zoom Camera 1:1", icon = "ZOOM_CAMERA")
        layout.operator("view3d.dolly", text="Dolly View", icon = "DOLLY")
        layout.operator("view3d.view_center_pick", icon = "CENTERTOMOUSE")

        layout.separator()

        layout.operator("view3d.fly", icon = "FLY_NAVIGATION")
        layout.operator("view3d.walk", icon = "WALK_NAVIGATION")
        layout.operator("view3d.navigate", icon = "VIEW_NAVIGATION")

        layout.separator()

        layout.operator("screen.animation_play", text="Playback Animation", icon = "TRIA_RIGHT")

        layout.separator()

        layout.operator("transform.translate", icon='TRANSFORM_MOVE')
        layout.operator("transform.rotate", icon='TRANSFORM_ROTATE')
        layout.operator("transform.resize", icon='TRANSFORM_SCALE', text="Scale")


class VIEW3D_MT_view_align(Menu):
    bl_label = "Align View"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.camera_to_view", text="Align Active Camera to View", icon = "ALIGNCAMERA_VIEW")
        layout.operator("view3d.camera_to_view_selected", text="Align Active Camera to Selected", icon = "ALIGNCAMERA_ACTIVE")
        layout.operator("view3d.view_center_cursor", icon = "CENTERTOCURSOR")

        layout.separator()

        layout.operator("view3d.view_lock_to_active", icon = "LOCKTOACTIVE")
        layout.operator("view3d.view_center_lock", icon = "LOCKTOCENTER")
        layout.operator("view3d.view_lock_clear", icon = "LOCK_CLEAR")

        layout.separator()

        # Rest of align

        layout.operator("view3d.view_persportho", icon = "PERSP_ORTHO")

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

        props = layout.operator("view3d.viewnumpad", text="Top", icon = "VIEW_ACTIVE_TOP")
        props.align_active = True
        props.type = 'TOP'

        props = layout.operator("view3d.viewnumpad", text="Bottom", icon ="VIEW_ACTIVE_BOTTOM")
        props.align_active = True
        props.type = 'BOTTOM'

        props = layout.operator("view3d.viewnumpad", text="Front", icon ="VIEW_ACTIVE_FRONT")
        props.align_active = True
        props.type = 'FRONT'

        props = layout.operator("view3d.viewnumpad", text="Back", icon ="VIEW_ACTIVE_BACK")
        props.align_active = True
        props.type = 'BACK'

        props = layout.operator("view3d.viewnumpad", text="Right" , icon ="VIEW_ACTIVE_RIGHT")
        props.align_active = True
        props.type = 'RIGHT'

        props = layout.operator("view3d.viewnumpad", text="Left", icon ="VIEW_ACTIVE_LEFT")
        props.align_active = True
        props.type = 'LEFT'


class VIEW3D_MT_view_cameras(Menu):
    bl_label = "Cameras"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.object_as_camera")
        layout.operator("view3d.viewnumpad", text="Active Camera").type = 'CAMERA'

        layout.separator()

        layout.operator("view3d.view_center_camera")


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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("object.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("object.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("object.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("object.select_mirror", text="Mirror", icon = "TRANSFORM_MIRROR")

        layout.operator("object.select_camera", text="Camera", icon = "CAMERA_DATA")

        layout.separator()

        layout.menu ("VIEW3D_MT_select_grouped")
        layout.menu ("VIEW3D_MT_select_linked")
        layout.operator("object.select_pattern", text="By Pattern...", icon = "PATTERN")
        layout.operator("object.select_by_layer", text="All by Layer", icon = "LAYER")
        layout.menu ("VIEW3D_MT_select_by_type")
        layout.separator()

        myvar = layout.operator("object.select_hierarchy", text="Parent", icon = "PARENT")
        myvar.direction = 'PARENT'
        myvar.extend = False
        myvar = layout.operator("object.select_hierarchy", text="Child", icon = "CHILD")
        myvar.direction = 'CHILD'
        myvar.extend = False

        myvar = layout.operator("object.select_hierarchy", text="Parent Extended", icon = "PARENT")
        myvar.direction = 'PARENT'
        myvar.extend = True
        myvar = layout.operator("object.select_hierarchy", text="Child Extended", icon = "CHILD")
        myvar.direction = 'CHILD'
        myvar.extend = True

        layout.separator()
        
        layout.operator("object.select_more", text="More", icon = "SELECTMORE")
        layout.operator("object.select_less", text="Less", icon = "SELECTLESS")

class VIEW3D_MT_select_grouped(Menu):
    bl_label = "Grouped"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_grouped", text= "Group", icon = "GROUP").type = 'GROUP'
        layout.operator("object.select_grouped", text= "Type", icon = "TYPE").type = 'TYPE'
        layout.operator("object.select_grouped", text= "Layer", icon = "LAYER").type = 'LAYER'

        layout.separator()

        layout.operator("object.select_grouped", text= "Siblings", icon = "SIBLINGS").type = 'SIBLINGS'
        layout.operator("object.select_grouped", text= "Parent", icon = "PARENT").type = 'PARENT'      
        layout.operator("object.select_grouped", text= "Children", icon = "CHILD_RECURSIVE").type = 'CHILDREN_RECURSIVE'
        layout.operator("object.select_grouped", text= "Immediate Children", icon = "CHILD").type = 'CHILDREN'

        layout.separator()

        layout.operator("object.select_grouped", text= "Color", icon = "COLOR").type = 'COLOR'
        layout.operator("object.select_grouped", text= "Hook", icon = "HOOK").type = 'HOOK'
        layout.operator("object.select_grouped", text= "Keying Set", icon = "KEYINGSET").type = 'KEYINGSET'
        layout.operator("object.select_grouped", text= "Lamp Type", icon = "LAMP").type = 'LAMP_TYPE'
        layout.operator("object.select_grouped", text= "Pass", icon = "PASS").type = 'PASS'
        layout.operator("object.select_grouped", text= "Properties", icon = "BUTS").type = 'PROPERTIES'      
        

class VIEW3D_MT_select_by_type(Menu):
    bl_label = "All by Type"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_by_type", text= "Mesh", icon = "OUTLINER_OB_MESH").type = 'MESH'
        layout.operator("object.select_by_type", text= "Curve", icon = "OUTLINER_OB_CURVE").type = 'CURVE'
        layout.operator("object.select_by_type", text= "Surface", icon = "OUTLINER_OB_SURFACE").type = 'SURFACE'
        layout.operator("object.select_by_type", text= "Meta", icon = "OUTLINER_OB_META").type = 'META'
        layout.operator("object.select_by_type", text= "Font", icon = "OUTLINER_OB_FONT").type = 'FONT'

        layout.separator()

        layout.operator("object.select_by_type", text= "Armature", icon = "OUTLINER_OB_ARMATURE").type = 'ARMATURE'
        layout.operator("object.select_by_type", text= "Lattice", icon = "OUTLINER_OB_LATTICE").type = 'LATTICE'
        layout.operator("object.select_by_type", text= "Empty", icon = "OUTLINER_OB_EMPTY").type = 'EMPTY'

        layout.separator()

        layout.operator("object.select_by_type", text= "Camera", icon = "OUTLINER_OB_CAMERA").type = 'CAMERA'
        layout.operator("object.select_by_type", text= "Lamp", icon = "OUTLINER_OB_LAMP").type = 'LAMP'
        layout.operator("object.select_by_type", text= "Speaker", icon = "OUTLINER_OB_SPEAKER").type = 'SPEAKER'

class VIEW3D_MT_select_linked(Menu):
    bl_label = "Linked"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.select_linked", text= "Object Data", icon = "OBJECT_DATA").type = 'OBDATA'
        layout.operator("object.select_linked", text= "Material", icon = "MATERIAL_DATA").type = 'MATERIAL'
        layout.operator("object.select_linked", text= "Texture", icon = "TEXTURE_DATA").type = 'TEXTURE'
        layout.operator("object.select_linked", text= "Dupli Group", icon = "GROUP").type = 'DUPGROUP'
        layout.operator("object.select_linked", text= "Particle System", icon = "PARTICLES").type = 'PARTICLE'
        layout.operator("object.select_linked", text= "Library", icon = "LIBRARY").type = 'LIBRARY'
        layout.operator("object.select_linked", text= "Library (Object Data)", icon = "LIBRARY_OBJECT").type = 'LIBRARY_OBDATA'



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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("pose.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("pose.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("pose.select_mirror", text="Flip Active", icon = "FLIP")
        layout.operator("pose.select_constraint_target", text="Constraint Target", icon = "CONSTRAINT_BONE")

        layout.separator()

        layout.operator_menu_enum("pose.select_grouped", "type", text="Grouped")
        layout.operator("pose.select_linked", text="Connected", icon = "CONNECTED")   
        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")

        layout.separator()

        props = layout.operator("pose.select_hierarchy", text="Parent", icon = "PARENT")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child", icon = "CHILD")
        props.extend = False
        props.direction = 'CHILD'

        props = layout.operator("pose.select_hierarchy", text="Parent Extended", icon = "PARENT")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("pose.select_hierarchy", text="Child Extended", icon = "CHILD")
        props.extend = True
        props.direction = 'CHILD'


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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')

        layout.separator()

        layout.operator("particle.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("particle.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("particle.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("particle.select_roots", text="Roots", icon = "SELECT_ROOT")
        layout.operator("particle.select_tips", text="Tips", icon = "SELECT_TIP")
        
        layout.separator()

        layout.operator("particle.select_linked", text="Linked", icon = "LINKED").deselect = False
        layout.operator("particle.select_linked", text="Deselect Linked", icon = "LINKED").deselect = True
        layout.separator()

        layout.operator("particle.select_more", text="More", icon = "SELECTMORE")
        layout.operator("particle.select_less", text="Less", icon = "SELECTLESS")


class VIEW3D_MT_edit_mesh_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        select_mode = context.tool_settings.mesh_select_mode 

        #layout.operator_enum("mesh.select_similar", "type") #bfa - The Blender way. Short, elegant, and crap. Enums cannot have icons ...

        # Vertices select mode
        if tuple(select_mode) == (True, False, False):

            layout.operator("mesh.select_similar", text= "Normal", icon = "RECALC_NORMALS").type='NORMAL'
            layout.operator("mesh.select_similar", text= "Amount of Adjacent Faces", icon = "FACESEL").type='FACE'
            layout.operator("mesh.select_similar", text= "Vertex Groups", icon = "GROUP_VERTEX").type='VGROUP'
            layout.operator("mesh.select_similar", text= "Amount of connecting Edges", icon = "EDGESEL").type='EDGE'
        
        # Edges select mode
        if tuple(select_mode) == (False, True, False):

            layout.operator("mesh.select_similar", text= "Length", icon = "RULER").type='LENGTH'
            layout.operator("mesh.select_similar", text= "Direction", icon = "SWITCH_DIRECTION").type='DIR'
            layout.operator("mesh.select_similar", text= "Amount of Faces around an edge", icon = "FACESEL").type='FACE'
            layout.operator("mesh.select_similar", text= "Face Angles", icon = "ANGLE").type='FACE_ANGLE'
            layout.operator("mesh.select_similar", text= "Crease", icon = "CREASE").type='CREASE'
            layout.operator("mesh.select_similar", text= "Bevel", icon = "BEVEL").type='BEVEL'
            layout.operator("mesh.select_similar", text= "Seam", icon = "MARK_SEAM").type='SEAM'
            layout.operator("mesh.select_similar", text= "Sharpness", icon = "SELECT_SHARPEDGES").type='SHARP'
            layout.operator("mesh.select_similar", text= "Freestyle Edge Marks", icon = "MARK_FS_EDGE").type='FREESTYLE_EDGE'
        
        # Faces select mode
        if tuple(select_mode) == (False, False, True ):

            layout.operator("mesh.select_similar", text= "Material", icon = "MATERIAL").type='MATERIAL'
            layout.operator("mesh.select_similar", text= "Image", icon = "TEXTURE").type='IMAGE'
            layout.operator("mesh.select_similar", text= "Area", icon = "AREA").type='AREA'
            layout.operator("mesh.select_similar", text= "Polygon Sides", icon = "POLYGONSIDES").type='SIDES'
            layout.operator("mesh.select_similar", text= "Perimeter", icon = "PERIMETER").type='PERIMETER'
            layout.operator("mesh.select_similar", text= "Normal", icon = "RECALC_NORMALS").type='NORMAL'
            layout.operator("mesh.select_similar", text= "Co-Planar", icon = "MAKE_PLANAR").type='COPLANAR'
            layout.operator("mesh.select_similar", text= "Flat / Smooth", icon = "SHADING_SMOOTH").type='SMOOTH'
            layout.operator("mesh.select_similar", text= "Freestyle Face Marks", icon = "MARKFSFACE").type='FREESTYLE_FACE'

        layout.separator()

        layout.operator("mesh.select_similar_region", text="Face Regions", icon = "FACEREGIONS")


class VIEW3D_MT_edit_mesh_select_by_trait(Menu):
    bl_label = "Select All by Trait"

    def draw(self, context):
        layout = self.layout
        if context.scene.tool_settings.mesh_select_mode[2] is False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold", icon = "SELECT_NONMANIFOLD")
        layout.operator("mesh.select_loose", text="Loose Geometry", icon = "SELECT_LOOSE")
        layout.operator("mesh.select_interior_faces", text="Interior Faces", icon = "SLEECT_INTERIOR")
        layout.operator("mesh.select_face_by_sides", text = "Faces by Side", icon = "SELECT_FACES_BY_SIDE")

        layout.separator()

        layout.operator("mesh.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")

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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        # primitive
        layout.operator("mesh.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("mesh.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        # numeric
        layout.operator("mesh.select_random", text="Random", icon = "RANDOMIZE")   
        layout.operator("mesh.select_mirror", text="Mirror", icon = "TRANSFORM_MIRROR")
        layout.operator("mesh.select_nth", icon = "CHECKER_DESELECT")
        layout.operator("mesh.shortest_path_select", text="Shortest Path", icon = "SELECT_SHORTESTPATH")
        layout.operator("mesh.select_axis", text="Side of Active", icon = "SELECT_SIDEOFACTIVE")

        layout.separator()

        # geometric
        layout.operator("mesh.edges_select_sharp", text="Sharp Edges", icon = "SELECT_SHARPEDGES")
        

        # topology
        layout.operator("mesh.select_loose", text="Loose Geometry", icon = "SELECT_LOOSE")
        if context.scene.tool_settings.mesh_select_mode[2] is False:
            layout.operator("mesh.select_non_manifold", text="Non Manifold", icon = "SELECT_NONMANIFOLD")
        layout.operator("mesh.select_interior_faces", text="Interior Faces", icon = "SLEECT_INTERIOR")
        layout.operator("mesh.select_face_by_sides", text = "Faces by Side", icon = "SELECT_FACES_BY_SIDE")
        

        layout.separator()

        layout.operator("mesh.loop_multi_select", text="Edge Loops", icon = "SELECT_EDGELOOP").ring = False
        layout.operator("mesh.loop_multi_select", text="Edge Rings", icon = "SELECT_EDGERING").ring = True
        layout.operator("mesh.loop_to_region", text = "Loop Inner-Region", icon = "SELECT_LOOPINNER")
        layout.operator("mesh.region_to_loop", text = "Boundary Loop", icon = "SELECT_BOUNDARY")

        layout.separator()

        # other ...
        layout.operator("mesh.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")
        layout.menu("VIEW3D_MT_edit_mesh_select_similar")
        layout.operator("mesh.faces_select_linked_flat", text="Linked Flat Faces", icon = "LINKED")
        layout.operator("mesh.select_linked", text="Linked", icon = "LINKED")
        layout.operator("mesh.select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("mesh.select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True

        layout.separator()

        layout.operator("mesh.select_next_item", text="Next Active", icon = "NEXTACTIVE")
        layout.operator("mesh.select_prev_item", text="Previous Active", icon = "PREVIOUSACTIVE")

        layout.separator()

        layout.operator("mesh.select_more", text="More", icon = "SELECTMORE")
        layout.operator("mesh.select_less", text="Less", icon = "SELECTLESS")



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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("curve.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("curve.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("curve.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("curve.select_nth", icon = "CHECKER_DESELECT")

        layout.separator()

        layout.operator("curve.select_linked", text="Linked", icon = "LINKED")
        layout.operator("curve.select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("curve.select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True
        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")

        layout.separator()

        layout.operator("curve.de_select_first", icon = "SELECT_FIRST")
        layout.operator("curve.de_select_last", icon = "SELECT_LAST")
        layout.operator("curve.select_next", text = "Next", icon = "NEXTACTIVE")
        layout.operator("curve.select_previous", text = "Previous", icon = "PREVIOUSACTIVE")

        layout.separator()

        layout.operator("curve.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("curve.select_less", text = "Less", icon = "SELECTLESS")


class VIEW3D_MT_select_edit_surface(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("curve.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("curve.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("curve.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("curve.select_nth", icon = "CHECKER_DESELECT")

        layout.separator()

        layout.operator("curve.select_linked", text="Linked", icon = "LINKED")
        layout.operator("curve.select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("curve.select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True
        layout.menu("VIEW3D_MT_select_edit_curve_select_similar")

        layout.separator()

        layout.operator("curve.select_row", icon = "CONTROLPOINTROW")

        layout.separator()

        layout.operator("curve.select_more", text = "More", icon = "SELECTMORE")
        layout.operator("curve.select_less", text = "Less", icon = "SELECTLESS")

class VIEW3D_MT_select_edit_curve_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.select_similar", text="Type", icon = "TYPE").type = 'TYPE'
        layout.operator("curve.select_similar", text="Radius", icon = "RADIUS").type = 'RADIUS'
        layout.operator("curve.select_similar", text="Weight", icon = "MOD_VERTEX_WEIGHT").type = 'WEIGHT'
        layout.operator("curve.select_similar", text="Direction", icon = "SWITCH_DIRECTION").type = 'DIRECTION'


class VIEW3D_MT_select_edit_text(Menu):
    # intentional name mismatch
    # select menu for 3d-text doesn't make sense
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.text_copy", text="Copy", icon = "COPYDOWN")
        layout.operator("font.text_cut", text="Cut", icon = "CUT")
        layout.operator("font.text_paste", text="Paste", icon = "PASTEDOWN")

        layout.separator()

        layout.operator("font.text_paste_from_file", icon = "PASTEFILE")

        layout.separator()

        layout.operator("font.select_all", icon = "SELECT_ALL")

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

        myvar = layout.operator("view3d.select_lasso", icon = "BORDER_LASSO")
        myvar.deselect = False
        layout.operator("view3d.select_border", icon = "BORDER_RECT")
        layout.operator("view3d.select_circle", icon = "CIRCLE_SELECT")

        layout.separator()

        layout.operator("mball.select_all", icon = "SELECT_ALL").action = 'TOGGLE'
        layout.operator("mball.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("mball.select_random_metaelems", text="Random", icon = "RANDOMIZE")

        layout.separator()

        layout.menu("VIEW3D_MT_select_edit_metaball_select_similar")

class VIEW3D_MT_select_edit_metaball_select_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("mball.select_similar", text="Type", icon = "TYPE").type = 'TYPE'
        layout.operator("mball.select_similar", text="Radius", icon = "RADIUS").type = 'RADIUS'
        layout.operator("mball.select_similar", text="Stiffness", icon = "BEND").type = 'STIFFNESS'
        layout.operator("mball.select_similar", text="Rotation", icon = "ROTATE").type = 'ROTATION'


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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("lattice.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("lattice.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("lattice.select_random", text="Random", icon = "RANDOMIZE")
        layout.operator("lattice.select_mirror", text ="Mirror", icon = "TRANSFORM_MIRROR")

        layout.separator()

        layout.operator("lattice.select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")

        layout.separator()

        layout.operator("lattice.select_more", text ="More", icon = "SELECTMORE")
        layout.operator("lattice.select_less", text ="Less", icon = "SELECTLESS")


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

        myvar = layout.operator("view3d.select_lasso", icon='BORDER_LASSO')
        myvar.deselect = False
        layout.operator("view3d.select_border", icon='BORDER_RECT')
        layout.operator("view3d.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("armature.select_all", icon='SELECT_ALL').action = 'TOGGLE'
        layout.operator("armature.select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("armature.select_mirror", text="Mirror", icon = "TRANSFORM_MIRROR").extend = False

        layout.separator()

        props = layout.operator("armature.select_hierarchy", text="Parent", icon = "PARENT")
        props.extend = False
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child", icon = "CHILD")
        props.extend = False
        props.direction = 'CHILD'

        props = layout.operator("armature.select_hierarchy", text="Parent Extended", icon = "PARENT")
        props.extend = True
        props.direction = 'PARENT'

        props = layout.operator("armature.select_hierarchy", text="Child Extended", icon = "CHILD")
        props.extend = True
        props.direction = 'CHILD'

        layout.separator()

        layout.operator("armature.select_linked", text = "Connected", icon = "CONNECTED")   
        layout.menu("VIEW3D_MT_select_edit_armature_similar")
        layout.operator("object.select_pattern", text="By Pattern", icon = "PATTERN")

        layout.separator()

        layout.operator("armature.select_more", text="More", icon = "SELECTMORE")
        layout.operator("armature.select_less", text="Less", icon = "SELECTLESS")

class VIEW3D_MT_select_edit_armature_similar(Menu):
    bl_label = "Similar"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.select_similar", text="Children", icon = "CHILD").type = 'CHILDREN'
        layout.operator("armature.select_similar", text="Immediate Children", icon = "CHILD").type = 'CHILDREN_IMMEDIATE'
        layout.operator("armature.select_similar", text="Siblings", icon = "SIBLINGS").type = 'SIBLINGS'
        layout.operator("armature.select_similar", text="Length", icon = "RULER").type = 'LENGTH'
        layout.operator("armature.select_similar", text="Direction (Y Axis)", icon = "Y_ICON").type = 'DIRECTION'
        layout.operator("armature.select_similar", text="Prefix", icon = "PREFIX").type = 'PREFIX'
        layout.operator("armature.select_similar", text="Suffix", icon = "SUFFIX").type = 'SUFFIX'
        layout.operator("armature.select_similar", text="Layer", icon = "LAYER").type = 'LAYER'
        layout.operator("armature.select_similar", text="Group", icon = "GROUP").type = 'GROUP'
        layout.operator("armature.select_similar", text="Shape", icon = "SHAPEKEY_DATA").type = 'SHAPE'

class VIEW3D_MT_select_gpencil(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.select_border", icon = 'BORDER_RECT')
        layout.operator("gpencil.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("gpencil.select_all", text="(De)select All", icon = "SELECT_ALL").action = 'TOGGLE'
        layout.operator("gpencil.select_all", text="Inverse", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("gpencil.select_linked", text="Linked", icon = "LINKED")  
        layout.menu("VIEW3D_MT_select_gpencil_grouped", text="Grouped")

        layout.separator()

        layout.operator("gpencil.select_first", icon = "SELECT_FIRST")
        layout.operator("gpencil.select_last", icon = "SELECT_LAST")

        layout.separator()

        layout.operator("gpencil.select_more", icon = "SELECTMORE")
        layout.operator("gpencil.select_less", icon = "SELECTLESS")

class VIEW3D_MT_select_gpencil_grouped(Menu):
    bl_label = "Grouped"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.select_grouped", text="Layer", icon = "LAYER").type = 'LAYER'
        layout.operator("gpencil.select_grouped", text="Color", icon = "COLOR").type = 'COLOR'


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

        myvar = layout.operator("view3d.select_lasso", icon = "BORDER_LASSO")
        myvar.deselect = False
        layout.operator("view3d.select_border", icon = "BORDER_RECT")
        layout.operator("view3d.select_circle", icon = "CIRCLE_SELECT")

        layout.separator()

        layout.operator("paint.face_select_all", icon = "SELECT_ALL").action = 'TOGGLE'
        layout.operator("paint.face_select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("paint.face_select_linked", text="Linked", icon = "LINKED")
        layout.operator("paint.face_select_linked_pick", text="Linked Pick Select", icon = "LINKED").deselect = False
        layout.operator("paint.face_select_linked_pick", text="Linked Pick Deselect", icon = "LINKED").deselect = True


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

        myvar = layout.operator("view3d.select_lasso", icon = "BORDER_LASSO")
        myvar.deselect = False
        layout.operator("view3d.select_border", icon = "BORDER_RECT")
        layout.operator("view3d.select_circle", icon = "CIRCLE_SELECT")

        layout.separator()

        layout.operator("paint.vert_select_all", icon = "SELECT_ALL").action = 'TOGGLE'
        layout.operator("paint.vert_select_all_inverse", text="Inverse", icon='INVERSE')

        layout.separator()

        layout.operator("paint.vert_select_ungrouped", text="Ungrouped Verts", icon = "SELECT_UNGROUPED_VERTS")


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
                    layout.prop(tex_slot, "use_random", text="Random", icon = "RANDOMIZE")
            else:
                layout.prop(tex_slot, "use_random", text="Random", icon = "RANDOMIZE")

# ********** Add menu **********

# XXX: INFO_MT_ names used to keep backwards compatibility (Addons etc that hook into the menu)
# XXX: bfa - the whole add menu is just 


class INFO_MT_mesh_add(Menu):
    bl_idname = "INFO_MT_mesh_add"
    bl_label = "Mesh"

    def draw(self, context):
        from .space_view3d_toolbar import VIEW3D_PT_tools_add_object

        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        VIEW3D_PT_tools_add_object.draw_add_mesh(layout)


class INFO_MT_curve_add(Menu):
    bl_idname = "INFO_MT_curve_add"
    bl_label = "Curve"

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
        

    def draw(self, context):
        from .space_view3d_toolbar import VIEW3D_PT_tools_add_object
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        self.draw_add_curve(layout)


class INFO_MT_surface_add(Menu):
    bl_idname = "INFO_MT_surface_add"
    bl_label = "Surface"

    @staticmethod
    def draw_add_surface(layout):
        layout.operator("surface.primitive_nurbs_surface_curve_add", text="Surface Curve ", icon='SURFACE_NCURVE')
        layout.operator("surface.primitive_nurbs_surface_circle_add", text="Surface Circle ", icon='SURFACE_NCIRCLE')
        layout.operator("surface.primitive_nurbs_surface_surface_add", text="Surface Patch  ", icon='SURFACE_NSURFACE')
        layout.operator("surface.primitive_nurbs_surface_cylinder_add", text="Surface Cylinder", icon='SURFACE_NCYLINDER')
        layout.operator("surface.primitive_nurbs_surface_sphere_add", text="Surface Sphere", icon='SURFACE_NSPHERE')
        layout.operator("surface.primitive_nurbs_surface_torus_add", text="Surface Torus  ", icon='SURFACE_NTORUS')


    def draw(self, context):
        from .space_view3d_toolbar import VIEW3D_PT_tools_add_object
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        self.draw_add_surface(layout)


class INFO_MT_metaball_add(Menu):
    bl_idname = "INFO_MT_metaball_add"
    bl_label = "Metaball"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.metaball_add", "type")


class INFO_MT_edit_curve_add(Menu):
    bl_idname = "INFO_MT_edit_curve_add"
    bl_label = "Add"

    def draw(self, context):
        is_surf = context.active_object.type == 'SURFACE'

        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'

        if is_surf:
            INFO_MT_surface_add.draw(self, context)
        else:
            INFO_MT_curve_add.draw(self, context)


class INFO_MT_edit_armature_add(Menu):
    bl_idname = "INFO_MT_edit_armature_add"
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("armature.bone_primitive_add", text="Single Bone", icon='BONE_DATA')


class INFO_MT_armature_add(Menu):
    bl_idname = "INFO_MT_armature_add"
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.armature_add", text="Single Bone", icon='BONE_DATA')


class INFO_MT_lamp_add(Menu):
    bl_idname = "INFO_MT_lamp_add"
    bl_label = "Lamp"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.lamp_add", "type")


class INFO_MT_add(Menu):
    bl_label = "Add"

    def draw(self, context):
        layout = self.layout

        # note, don't use 'EXEC_SCREEN' or operators won't get the 'v3d' context.

        # Note: was EXEC_AREA, but this context does not have the 'rv3d', which prevents
        #       "align_view" to work on first call (see [#32719]).
        layout.operator_context = 'EXEC_REGION_WIN'

        # layout.operator_menu_enum("object.mesh_add", "type", text="Mesh", icon='OUTLINER_OB_MESH')
        layout.menu("INFO_MT_mesh_add", icon='OUTLINER_OB_MESH')

        # layout.operator_menu_enum("object.curve_add", "type", text="Curve", icon='OUTLINER_OB_CURVE')
        layout.menu("INFO_MT_curve_add", icon='OUTLINER_OB_CURVE')
        # layout.operator_menu_enum("object.surface_add", "type", text="Surface", icon='OUTLINER_OB_SURFACE')
        layout.menu("INFO_MT_surface_add", icon='OUTLINER_OB_SURFACE')
        layout.menu("INFO_MT_metaball_add", text="Metaball", icon='OUTLINER_OB_META')
        layout.operator("object.text_add", text="Text", icon='OUTLINER_OB_FONT')
        layout.separator()

        layout.menu("INFO_MT_armature_add", icon='OUTLINER_OB_ARMATURE')
        layout.operator("object.add", text="Lattice", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.operator_menu_enum("object.empty_add", "type", text="Empty", icon='OUTLINER_OB_EMPTY')
        layout.separator()

        layout.operator("object.speaker_add", text="Speaker", icon='OUTLINER_OB_SPEAKER')
        layout.separator()

        if INFO_MT_camera_add.is_extended():
            layout.menu("INFO_MT_camera_add", icon='OUTLINER_OB_CAMERA')
        else:
            INFO_MT_camera_add.draw(self, context)

        layout.menu("INFO_MT_lamp_add", icon='OUTLINER_OB_LAMP')
        layout.separator()

        layout.operator_menu_enum("object.effector_add", "type", text="Force Field", icon='OUTLINER_OB_FORCE_FIELD')
        layout.separator()

        if len(bpy.data.groups) > 10:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("object.group_instance_add", text="Group Instance...", icon='OUTLINER_OB_GROUP_INSTANCE')
        else:
            layout.operator_menu_enum(
                "object.group_instance_add",
                "group",
                text="Group Instance",
                icon='OUTLINER_OB_GROUP_INSTANCE',
            )


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
        view = context.space_data
        is_local_view = (view.local_view is not None)

        scene = context.scene
        obj = context.object

        # The  Specials menu content. Special settings for Camera, Curve, Font, Empty and Lamp
        # Now also available in the normal menu.
        if context.object :

            if obj.type == 'CAMERA':
                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.separator()

                if obj.data.type == 'PERSP':
                    props = layout.operator("wm.context_modal_mouse", text="Camera Lens Angle", icon = "LENS_ANGLE")
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
                        props = layout.operator("ui.eyedropper_depth", text="DOF Distance (Pick)", icon = "DOF")
                    else:
                        props = layout.operator("wm.context_modal_mouse", text="DOF Distance", icon = "DOF")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.dof_distance"
                        props.input_scale = 0.02
                        props.header_text = "DOF Distance: %.3f"
                    del view

            if obj.type in {'CURVE', 'FONT'}:
                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.separator()

                props = layout.operator("wm.context_modal_mouse", text="Extrude Size", icon = "EXTRUDESIZE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.extrude"
                props.input_scale = 0.01
                props.header_text = "Extrude Size: %.3f"

                props = layout.operator("wm.context_modal_mouse", text="Width Size", icon = "WIDTH_SIZE" )
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "data.offset"
                props.input_scale = 0.01
                props.header_text = "Width Size: %.3f"


            if obj.type == 'EMPTY':
                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.separator()

                props = layout.operator("wm.context_modal_mouse", text="Empty Draw Size", icon = "DRAWSIZE")
                props.data_path_iter = "selected_editable_objects"
                props.data_path_item = "empty_draw_size"
                props.input_scale = 0.01
                props.header_text = "Empty Draw Size: %.3f"


            if obj.type == 'LAMP':
                lamp = obj.data

                layout.operator_context = 'INVOKE_REGION_WIN'
                layout.separator()

                if scene.render.use_shading_nodes:
                    try:
                        value = lamp.node_tree.nodes["Emission"].inputs["Strength"].default_value
                    except AttributeError:
                        value = None

                    if value is not None:
                        props = layout.operator("wm.context_modal_mouse", text="Strength", icon = "LIGHT_STRENGTH")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.node_tree.nodes[\"Emission\"].inputs[\"Strength\"].default_value"
                        props.header_text = "Lamp Strength: %.3f"
                        props.input_scale = 0.1
                    del value

                    if lamp.type == 'AREA':
                        props = layout.operator("wm.context_modal_mouse", text="Size X", icon = "LIGHT_SIZE")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.size"
                        props.header_text = "Lamp Size X: %.3f"

                        if lamp.shape == 'RECTANGLE':
                            props = layout.operator("wm.context_modal_mouse", text="Size Y", icon = "LIGHT_SIZE")
                            props.data_path_iter = "selected_editable_objects"
                            props.data_path_item = "data.size_y"
                            props.header_text = "Lamp Size Y: %.3f"

                    elif lamp.type in {'SPOT', 'POINT', 'SUN'}:
                        props = layout.operator("wm.context_modal_mouse", text="Size", icon = "LIGHT_SIZE")
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

        # End former Specials menu content.


        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator_enum("object.lamp_add", "type")


class INFO_MT_camera_add(Menu):
    bl_idname = "INFO_MT_camera_add"
    bl_label = "Camera"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.camera_add", text="Camera", icon='OUTLINER_OB_CAMERA')


# ********** Object menu **********


class VIEW3D_MT_object(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        is_local_view = (view.local_view is not None)

        #layout.menu("VIEW3D_MT_transform_object")
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")

        layout.separator()

        layout.operator("view3d.pastebuffer", text = "Paste", icon = "PASTEDOWN")
        layout.operator("view3d.copybuffer", text = "Copy", icon = "COPYDOWN")
        layout.operator("object.duplicate_move", icon = "DUPLICATE")
        layout.operator("object.duplicate_move_linked", icon = "DUPLICATE")
        layout.operator("object.delete_global", text="Delete Global", icon = "DELETE") # bfa - separated tooltip
        layout.operator("object.delete", text="Delete...", icon = "DELETE").use_global = False

        layout.separator()

        layout.operator("object.make_dupli_face", icon = "MAKEDUPLIFACE")

        layout.separator()

        layout.menu("VIEW3D_MT_object_constraints")

        layout.separator()

        layout.menu("VIEW3D_MT_object_quick_effects")
        layout.menu("VIEW3D_MT_subdivision_set")

        layout.separator()

        layout.menu("VIEW3D_MT_object_game")

        layout.separator()

        layout.menu("VIEW3D_MT_object_showhide")

        layout.operator_menu_enum("object.convert", "target")

# bfa - The animation menu is removed from the traditional menus as a double menu entry. 
# But in Blender 2.8 it gets used in grease pencil mode too. So we have to keep it it seems.
class VIEW3D_MT_object_animation(Menu):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout

        layout.operator("anim.keyframe_insert_menu", text="Insert Keyframe", icon= 'KEYFRAMES_INSERT')
        layout.operator("anim.keyframe_delete_v3d", text="Delete Keyframes", icon= 'KEYFRAMES_REMOVE')
        layout.operator("anim.keyframe_clear_v3d", text="Clear Keyframes", icon= 'KEYFRAMES_CLEAR')
        layout.operator("anim.keying_set_active_set", text="Change Keying Set", icon='TRIA_RIGHT')

        layout.separator()

        layout.operator("nla.bake", text="Bake Action", icon= 'BAKE_ACTION')


class VIEW3D_MT_object_clear(Menu):
    bl_label = "Clear"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.location_clear", text="Location", icon = "CLEARMOVE").clear_delta = False
        layout.operator("object.rotation_clear", text="Rotation", icon = "CLEARROTATE").clear_delta = False
        layout.operator("object.scale_clear", text="Scale", icon = "CLEARSCALE").clear_delta = False
        layout.operator("object.origin_clear", text="Origin", icon = "CLEARORIGIN")


class VIEW3D_MT_object_specials(Menu):
    bl_label = "Specials"

    @classmethod
    def poll(cls, context):
        # add more special types
        return context.object

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        obj = context.object

        if obj.type == 'CAMERA':
            layout.operator_context = 'INVOKE_REGION_WIN'

            if obj.data.type == 'PERSP':
                props = layout.operator("wm.context_modal_mouse", text="Camera Lens Angle", icon = "LENS_ANGLE")
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
                    props = layout.operator("ui.eyedropper_depth", text="DOF Distance (Pick)", icon = "DOF")
                else:
                    props = layout.operator("wm.context_modal_mouse", text="DOF Distance", icon = "DOF")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.dof_distance"
                    props.input_scale = 0.02
                    props.header_text = "DOF Distance: %.3f"
                del view

        if obj.type in {'CURVE', 'FONT'}:
            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Extrude Size", icon = "EXTRUDESIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.extrude"
            props.input_scale = 0.01
            props.header_text = "Extrude Size: %.3f"

            props = layout.operator("wm.context_modal_mouse", text="Width Size", icon = "WIDTH_SIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "data.offset"
            props.input_scale = 0.01
            props.header_text = "Width Size: %.3f"

        if obj.type == 'EMPTY':
            layout.operator_context = 'INVOKE_REGION_WIN'

            props = layout.operator("wm.context_modal_mouse", text="Empty Draw Size", icon = "DRAWSIZE")
            props.data_path_iter = "selected_editable_objects"
            props.data_path_item = "empty_draw_size"
            props.input_scale = 0.01
            props.header_text = "Empty Draw Size: %.3f"

        if obj.type == 'LAMP':
            lamp = obj.data

            layout.operator_context = 'INVOKE_REGION_WIN'

            if scene.render.use_shading_nodes:
                try:
                    value = lamp.node_tree.nodes["Emission"].inputs["Strength"].default_value
                except AttributeError:
                    value = None

                if value is not None:
                    props = layout.operator("wm.context_modal_mouse", text="Strength", icon = "LIGHT_STRENGTH")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.node_tree.nodes[\"Emission\"].inputs[\"Strength\"].default_value"
                    props.header_text = "Lamp Strength: %.3f"
                    props.input_scale = 0.1
                del value

                if lamp.type == 'AREA':
                    props = layout.operator("wm.context_modal_mouse", text="Size X", icon = "LIGHT_SIZE")
                    props.data_path_iter = "selected_editable_objects"
                    props.data_path_item = "data.size"
                    props.header_text = "Lamp Size X: %.3f"

                    if lamp.shape == 'RECTANGLE':
                        props = layout.operator("wm.context_modal_mouse", text="Size Y", icon = "LIGHT_SIZE")
                        props.data_path_iter = "selected_editable_objects"
                        props.data_path_item = "data.size_y"
                        props.header_text = "Lamp Size Y: %.3f"

                elif lamp.type in {'SPOT', 'POINT', 'SUN'}:
                    props = layout.operator("wm.context_modal_mouse", text="Size", icon = "LIGHT_SIZE")
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

        props = layout.operator("object.isolate_type_render")
        props = layout.operator("object.hide_render_clear_all")


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
        props = layout.operator("object.transform_apply", text="Rotation & Scale", text_ctxt=i18n_contexts.default, icon = "APPLYALL")
        props.location, props.rotation, props.scale = False, True, True

        layout.separator()

        layout.operator("object.transforms_to_deltas", text="Location to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYMOVEDELTA").mode = 'LOC'
        layout.operator("object.transforms_to_deltas", text="Rotation to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYROTATEDELTA").mode = 'ROT'
        layout.operator("object.transforms_to_deltas", text="Scale to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYSCALEDELTA").mode = 'SCALE'

        layout.operator("object.transforms_to_deltas", text="All Transforms to Deltas", text_ctxt=i18n_contexts.default, icon = "APPLYALLDELTA").mode = 'ALL'
        layout.operator("object.anim_transforms_to_deltas", icon = "APPLYANIDELTA")

        layout.separator()

        layout.operator("object.visual_transform_apply", text="Visual Transform", text_ctxt=i18n_contexts.default, icon = "VISUALTRANSFORM")
        layout.operator("object.duplicates_make_real", icon = "MAKEDUPLIREAL")


class VIEW3D_MT_object_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.constraint_add_with_targets", icon = "CONSTRAINT_DATA")
        layout.operator("object.constraints_copy", icon = "COPYDOWN")
        layout.operator("object.constraints_clear", icon = "CLEAR_CONSTRAINT")

        layout.separator()

        layout.operator("object.track_clear", text= "Clear Track", icon = "CLEAR_TRACK").type = 'CLEAR'
        layout.operator("object.track_clear", text= "Clear Track - Keep Transformation", icon = "CLEAR_TRACK").type = 'CLEAR_KEEP_TRANSFORM'


class VIEW3D_MT_object_quick_effects(Menu):
    bl_label = "Quick Effects"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.quick_fur", icon = "HAIR")
        layout.operator("object.quick_explode", icon = "MOD_EXPLODE")
        layout.operator("object.quick_smoke", icon = "MOD_SMOKE")
        layout.operator("object.quick_fluid", icon = "MOD_FLUIDSIM")

class VIEW3D_MT_subdivision_set(Menu):
    bl_label = "Subdivide"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.subdivision_set", icon = "SUBDIVIDE_EDGES").level = 0
        layout.operator("object.subdivision_set", icon = "SUBDIVIDE_EDGES").level = 1
        layout.operator("object.subdivision_set", icon = "SUBDIVIDE_EDGES").level = 2
        layout.operator("object.subdivision_set", icon = "SUBDIVIDE_EDGES").level = 3
        layout.operator("object.subdivision_set", icon = "SUBDIVIDE_EDGES").level = 4
        layout.operator("object.subdivision_set", icon = "SUBDIVIDE_EDGES").level = 5


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

        layout.operator("object.hide_view_clear", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("object.hide_view_set", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("object.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") # hide unselected with new tooltip

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


class VIEW3D_MT_object_game(Menu):
    bl_label = "Game"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.logic_bricks_copy", text="Copy Logic Bricks")
        layout.operator("object.game_physics_copy", text="Copy Physics Properties")

        layout.separator()

        layout.operator("object.game_property_copy", text="Replace Properties").operation = 'REPLACE'
        layout.operator("object.game_property_copy", text="Merge Properties").operation = 'MERGE'
        layout.operator_menu_enum("object.game_property_copy", "property", text="Copy Properties...")

        layout.separator()

        layout.operator("object.game_property_clear")


# ********** Brush menu **********

# bfa deactivated the brush menu in all other modes but sculpting. 
# See class VIEW3D_MT_editor_menus at the beginning of the script.
# This class may need further cleanups therefore.

class VIEW3D_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout

        settings = UnifiedPaintPanel.paint_settings(context)
        brush = getattr(settings, "brush", None)

        # brush tool
        if context.sculpt_object:
            layout.operator("brush.reset", icon = "BRUSH_RESET")

        # skip if no active brush
        if not brush:
            layout.label(text="No Brushes currently available", icon='INFO')
            return


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

        layout.operator("paint.vertex_color_set", icon = "COLOR")
        layout.operator("paint.vertex_color_smooth", icon = "SMOOTH")
        layout.operator("paint.vertex_color_dirt", icon = "DIRTY_VERTEX")
        layout.operator("paint.vertex_color_from_weight", icon = "VERTCOLFROMWEIGHT")

        layout.separator()

        layout.operator("paint.vertex_color_invert", text="Invert", icon = "REVERSE_COLORS")
        layout.operator("paint.vertex_color_levels", text="Levels", icon = "LEVELS")
        layout.operator("paint.vertex_color_hsv", text="Hue Saturation Value", icon = "HUESATVAL")
        layout.operator("paint.vertex_color_brightness_contrast", text="Bright/Contrast", icon = "BRIGHTNESS_CONTRAST")


class VIEW3D_MT_hook(Menu):
    bl_label = "Hooks"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.hook_add_newob", icon = "HOOK_NEW")
        layout.operator("object.hook_add_selob", icon = "HOOK_SELECTED").use_bone = False
        layout.operator("object.hook_add_selob", text="Hook to Selected Object Bone", icon = "HOOK_BONE").use_bone = True

        if [mod.type == 'HOOK' for mod in context.active_object.modifiers]:
            layout.separator()
            layout.operator_menu_enum("object.hook_assign", "modifier", icon = "HOOK_ASSIGN")
            layout.operator_menu_enum("object.hook_remove", "modifier", icon = "HOOK_REMOVE")
            layout.separator()
            layout.operator_menu_enum("object.hook_select", "modifier", icon = "HOOK_SELECT")
            layout.operator_menu_enum("object.hook_reset", "modifier", icon = "HOOK_RESET")
            layout.operator_menu_enum("object.hook_recenter", "modifier", icon = "HOOK_RECENTER")


class VIEW3D_MT_vertex_group(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.vertex_group_assign_new", icon = "NEW_GROUP")

        ob = context.active_object
        if ob.mode == 'EDIT' or (ob.mode == 'WEIGHT_PAINT' and ob.type == 'MESH' and ob.data.use_paint_mask_vertex):
            if ob.vertex_groups.active:
                layout.separator()
                layout.operator("object.vertex_group_assign", text="Assign to Active Group",  icon = 'ADD_TO_ACTIVE')
                layout.operator("object.vertex_group_remove_from", text="Remove from Active Group", icon = 'REMOVE_SELECTED_FROM_ACTIVE_GROUP').use_all_groups = False
                layout.operator("object.vertex_group_remove_from", text="Remove from All", icon = 'REMOVE_FROM_ALL_GROUPS').use_all_groups = True
                layout.separator()

        if ob.vertex_groups.active:
            layout.operator_menu_enum("object.vertex_group_set_active", "group", text="Set Active Group")
            layout.operator("object.vertex_group_remove", text="Remove Active Group", icon = "REMOVE_ACTIVE_GROUP").all = False
            layout.operator("object.vertex_group_remove", text="Remove All Groups", icon = "REMOVE_ALL_GROUPS").all = True

# ********** Weight paint menu **********


class VIEW3D_MT_paint_weight(Menu):
    bl_label = "Weights"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.weight_from_bones", text="Assign Automatic From Bones", icon = "BONE_DATA").type = 'AUTOMATIC'
        layout.operator("paint.weight_from_bones", text="Assign From Bone Envelopes", icon = "ENVELOPE_MODIFIER").type = 'ENVELOPES'

        layout.separator()

        layout.operator("paint.weight_set", icon = "MOD_VERTEX_WEIGHT")

# ********** Sculpt menu **********


class VIEW3D_MT_sculpt(Menu):
    bl_label = "Sculpt"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings
        sculpt = toolsettings.sculpt

        layout.menu("VIEW3D_MT_subdivision_set")


class VIEW3D_MT_hide_mask(Menu):
    bl_label = "Hide/Mask"

    def draw(self, context):
        layout = self.layout

        props = layout.operator("paint.hide_show", text="Show All", icon = "RESTRICT_VIEW_OFF")
        props.action = 'SHOW'
        props.area = 'ALL'

        props = layout.operator("paint.hide_show", text="Hide Bounding Box", icon = "RESTRICT_VIEW_ON")
        props.action = 'HIDE'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Show Bounding Box", icon = "RESTRICT_VIEW_OFF")
        props.action = 'SHOW'
        props.area = 'INSIDE'

        props = layout.operator("paint.hide_show", text="Hide Masked", icon = "RESTRICT_VIEW_ON")
        props.area = 'MASKED'
        props.action = 'HIDE'

        layout.separator()

        props = layout.operator("paint.mask_flood_fill", text="Invert Mask", icon = "INVERT_MASK")
        props.mode = 'INVERT'

        props = layout.operator("paint.mask_flood_fill", text="Fill Mask", icon = "FILL_MASK")
        props.mode = 'VALUE'
        props.value = 1

        props = layout.operator("paint.mask_flood_fill", text="Clear Mask", icon = "CLEAR_MASK")
        props.mode = 'VALUE'
        props.value = 0

        props = layout.operator("view3d.select_border", text="Box Mask", icon = "BOX_MASK")
        props = layout.operator("paint.mask_lasso_gesture", text="Lasso Mask", icon = "LASSO_MASK")


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

        layout.operator("particle.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("particle.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("particle.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_particle(Menu):
    bl_label = "Particle"

    def draw(self, context):
        layout = self.layout

        layout.operator("particle.delete", icon = "DELETE")

        layout.separator()

        layout.menu("VIEW3D_MT_particle_show_hide")


class VIEW3D_MT_particle_specials(Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        particle_edit = context.tool_settings.particle_edit

        layout.operator("particle.rekey")
        layout.operator("particle.delete", icon = "DELETE")
        layout.operator("particle.remove_doubles")
        layout.operator("particle.unify_length")

        if particle_edit.select_mode == 'POINT':
            layout.operator("particle.subdivide")

        layout.operator("particle.weight_set")
        layout.separator()

        layout.operator("particle.mirror")

        if particle_edit.select_mode == 'POINT':
            layout.separator()
            layout.operator("particle.select_roots")
            layout.operator("particle.select_tips")

            layout.separator()

            layout.operator("particle.select_random")

            layout.separator()

            layout.operator("particle.select_more", icon = "SELECTMORE")
            layout.operator("particle.select_less", icon = "SELECTLESS")

            layout.separator()

            layout.operator("particle.select_all", icon = "SELECT_ALL").action = 'TOGGLE'
            layout.operator("particle.select_linked")
            layout.operator("particle.select_all", text="Inverse", icon='INVERSE').action = 'INVERT'

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

        layout.operator("pose.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("pose.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("pose.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_pose(Menu):
    bl_label = "Pose"

    def draw(self, context):
        layout = self.layout

        #layout.menu("VIEW3D_MT_transform_armature")

        layout.menu("VIEW3D_MT_pose_transform")
        layout.menu("VIEW3D_MT_pose_apply")

        layout.separator()

        layout.operator("pose.copy", icon = "COPYDOWN")
        layout.operator("pose.paste", icon = "PASTEDOWN").flipped = False
        layout.operator("pose.paste", text="Paste X-Flipped Pose", icon = "PASTEDOWN").flipped = True

        layout.separator()

        layout.menu("VIEW3D_MT_pose_library")
        layout.menu("VIEW3D_MT_pose_group")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_ik")
        layout.menu("VIEW3D_MT_pose_constraints")

        layout.separator()

        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.autoside_names", text="AutoName Left/Right", icon = "STRING").axis = 'XAXIS'
        layout.operator("pose.autoside_names", text="AutoName Front/Back", icon = "STRING").axis = 'YAXIS'
        layout.operator("pose.autoside_names", text="AutoName Top/Bottom", icon = "STRING").axis = 'ZAXIS'

        layout.operator("pose.flip_names", icon = "FLIP")
        layout.operator("pose.quaternions_flip", icon = "FLIP")

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("armature.armature_layers", text="Change Armature Layers", icon = "LAYER")
        layout.operator("pose.bone_layers", text="Change Bone Layers", icon = "LAYER")

        layout.separator()

        layout.menu("VIEW3D_MT_pose_show_hide") # bfa - new show hide menu with separated tooltips
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")


class VIEW3D_MT_pose_transform(Menu):
    bl_label = "Clear Transform"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.transforms_clear", text="All", icon = "CLEAR")

        layout.separator()

        layout.operator("pose.loc_clear", text="Location", icon = "CLEARMOVE")
        layout.operator("pose.rot_clear", text="Rotation", icon = "CLEARROTATE")
        layout.operator("pose.scale_clear", text="Scale", icon = "CLEARSCALE")

        layout.separator()

        layout.operator("pose.user_transforms_clear", text="Reset Unkeyed", icon = "RESET")


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

        layout.operator("poselib.browse_interactive", text="Browse Poses", icon = "FILESEL")

        layout.separator()

        layout.operator("poselib.pose_add", text="Add Pose", icon = "LIBRARY")
        layout.operator("poselib.pose_rename", text="Rename Pose", icon = "STRING")
        layout.operator("poselib.pose_remove", text="Remove Pose", icon = "DELETE")


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
        layout.operator("pose.group_assign", text="Assign to New Group", icon = "NEW_GROUP").type = 0
        if pose.bone_groups:
            active_group = pose.bone_groups.active_index + 1
            layout.operator("pose.group_assign", text="Assign to Group", icon = "ADD_TO_ACTIVE").type = active_group

            layout.separator()

            # layout.operator_context = 'INVOKE_AREA'
            layout.operator("pose.group_unassign", icon = "REMOVE_SELECTED_FROM_ACTIVE_GROUP")
            layout.operator("pose.group_remove", icon = "REMOVE_FROM_ALL_GROUPS")


class VIEW3D_MT_pose_ik(Menu):
    bl_label = "Inverse Kinematics"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.ik_add", icon= "ADD_IK")
        layout.operator("pose.ik_clear", icon = "CLEAR_IK")


class VIEW3D_MT_pose_constraints(Menu):
    bl_label = "Constraints"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.constraint_add_with_targets", text="Add (With Targets)...", icon = "CONSTRAINT_DATA")
        layout.operator("pose.constraints_copy", icon = "COPYDOWN")
        layout.operator("pose.constraints_clear", icon = "CLEAR_CONSTRAINT")


class VIEW3D_MT_pose_apply(Menu):
    bl_label = "Apply"

    def draw(self, context):
        layout = self.layout

        layout.operator("pose.armature_apply", icon = "MOD_ARMATURE")
        layout.operator("pose.visual_transform_apply", icon = "APPLYMOVE")


class VIEW3D_MT_pose_specials(Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator("paint.weight_from_bones", text="Assign Automatic from Bones").type = 'AUTOMATIC'
        layout.operator("paint.weight_from_bones", text="Assign from Bone Envelopes").type = 'ENVELOPES'

        layout.separator()

        layout.operator("pose.select_constraint_target")
        layout.operator("pose.flip_names")
        layout.operator("pose.paths_calculate")
        layout.operator("pose.paths_clear")
        layout.operator("pose.user_transforms_clear")
        layout.operator("pose.user_transforms_clear", text="Clear User Transforms (All)").only_selected = False
        layout.operator("pose.relax")

        layout.separator()

        layout.operator_menu_enum("pose.autoside_names", "axis")


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

        layout.operator("mesh.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("mesh.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("mesh.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_edit_mesh(Menu):
    bl_label = "Mesh"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        #layout.menu("VIEW3D_MT_transform")

        layout.separator()

        layout.operator("mesh.duplicate_move", icon = "DUPLICATE")
        layout.menu("VIEW3D_MT_edit_mesh_delete")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_select_mode")
        layout.menu("VIEW3D_MT_vertex_group")
        layout.menu("VIEW3D_MT_hook")

        layout.separator()

        layout.menu("VIEW3D_MT_subdivision_set")
        layout.operator("mesh.noise", icon='NOISE')      
        layout.menu("VIEW3D_MT_edit_mesh_sort_elements")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_mesh_show_hide")

class VIEW3D_MT_edit_mesh_sort_elements(Menu):
    bl_label = "Sort Elements"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.sort_elements", text="View Z Axis", icon = "Z_ICON").type = 'VIEW_ZAXIS'
        layout.operator("mesh.sort_elements", text="View Y Axis", icon = "Y_ICON").type = 'VIEW_XAXIS'
        layout.operator("mesh.sort_elements", text="Cursor Distance", icon = "CURSOR").type = 'CURSOR_DISTANCE'
        layout.operator("mesh.sort_elements", text="Material", icon = "MATERIAL").type = 'MATERIAL'
        layout.operator("mesh.sort_elements", text="Selected", icon = "RESTRICT_SELECT_OFF").type = 'SELECTED'
        layout.operator("mesh.sort_elements", text="Randomize", icon = "RANDOMIZE").type = 'RANDOMIZE'
        layout.operator("mesh.sort_elements", text="Reverse", icon = "SWITCH_DIRECTION").type = 'REVERSE'


class VIEW3D_MT_edit_mesh_specials(Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.subdivide", text="Subdivide").smoothness = 0.0
        layout.operator("mesh.subdivide", text="Subdivide Smooth").smoothness = 1.0

        layout.separator()

        layout.operator("mesh.merge", text="Merge...")
        layout.operator("mesh.remove_doubles")

        layout.separator()

        layout.operator("mesh.hide", text="Hide").unselected = False
        layout.operator("mesh.reveal", text="Reveal")
        layout.operator("mesh.select_all", text="Select Inverse", icon='INVERSE').action = 'INVERT'

        layout.separator()

        layout.operator("mesh.flip_normals")
        layout.operator("mesh.vertices_smooth", text="Smooth")
        layout.operator("mesh.vertices_smooth_laplacian", text="Laplacian Smooth")

        layout.separator()

        layout.operator("mesh.inset")
        layout.operator("mesh.bevel", text="Bevel")
        layout.operator("mesh.bridge_edge_loops")

        layout.separator()

        layout.operator("mesh.faces_shade_smooth")
        layout.operator("mesh.faces_shade_flat")

        layout.separator()

        layout.operator("mesh.blend_from_shape")
        layout.operator("mesh.shape_propagate_to_all")
        layout.operator("mesh.shortest_path_select")
        layout.operator("mesh.sort_elements")
        layout.operator("mesh.symmetrize")
        layout.operator("mesh.symmetry_snap")


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

# bfa - Not longer connected. but the menu remains available for the Blender keymap.
class VIEW3D_MT_edit_mesh_vertices(Menu):
    bl_label = "Vertices"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        with_bullet = bpy.app.build_options.bullet

        layout.operator("mesh.rip_move", icon = "RIP")
        layout.operator("mesh.rip_move_fill", icon = "RIP_FILL")
        layout.operator("mesh.rip_edge_move", icon = "EXTEND_VERTICES")
        layout.operator("mesh.split", icon = "SPLIT")
        layout.operator("mesh.vert_connect_path", text="Connect Vertex Path", icon = "VERTEXCONNECTPATH")
        layout.operator("mesh.vert_connect", text="Connect Vertices", icon = "VERTEXCONNECT")

        layout.separator()

        if with_bullet:
            layout.operator("mesh.convex_hull", icon = "CONVEXHULL")

        layout.operator("mesh.blend_from_shape", icon = "BLENDFROMSHAPE")
        layout.operator("mesh.shape_propagate_to_all", icon = "SHAPEPROPAGATE")

# bfa - Not longer connected. but the menu remains available for the Blender keymap.
class VIEW3D_MT_edit_mesh_edges(Menu):
    bl_label = "Edges"

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.subdivide_edgering", icon = "SUBDIV_EDGERING")
        layout.operator("mesh.unsubdivide", icon = "UNSUBDIVIDE")

        layout.separator()

        layout.operator("transform.edge_crease", icon = "CREASE")
        layout.operator("transform.edge_bevelweight", icon = "BEVEL")

        layout.separator()

        layout.operator("mesh.mark_sharp", icon = "MARKSHARPEDGES")
        layout.operator("mesh.mark_sharp", text="Clear Sharp", icon = "CLEARSHARPEDGES").clear = True

        layout.separator()

        if with_freestyle:
            layout.operator("mesh.mark_freestyle_edge", icon = "MARK_FS_EDGE").clear = False
            layout.operator("mesh.mark_freestyle_edge", text="Clear Freestyle Edge", icon = "CLEAR_FS_EDGE").clear = True
            layout.separator()

        layout.operator("mesh.edge_rotate", text="Rotate Edge CW", icon = "ROTATECW").use_ccw = False

        layout.separator()

        layout.operator("mesh.edge_split", icon = "SPLITEDGE")

# bfa - Not longer connected. but the menu remains available for the Blender keymap.
class VIEW3D_MT_edit_mesh_faces(Menu):
    bl_label = "Faces"
    bl_idname = "VIEW3D_MT_edit_mesh_faces"

    def draw(self, context):
        layout = self.layout

        with_freestyle = bpy.app.build_options.freestyle

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.fill", icon = "FILL")
        layout.operator("mesh.fill_grid", icon = "GRIDFILL")
        layout.operator("mesh.beautify_fill", icon = "BEAUTIFY")
        layout.operator("mesh.solidify", icon = "SOLIDIFY")
        layout.operator("mesh.intersect", icon = "INTERSECT")
        layout.operator("mesh.intersect_boolean", icon = "BOOLEAN_INTERSECT")
        layout.operator("mesh.wireframe", icon = "WIREFRAME")

        layout.separator()

        if with_freestyle:
            layout.operator("mesh.mark_freestyle_face", icon = "MARKFSFACE").clear = False
            layout.operator("mesh.mark_freestyle_face", text="Clear Freestyle Face", icon = "CLEARFSFACE").clear = True
            layout.separator()

        layout.operator("mesh.poke", icon = "POKEFACES")
        props = layout.operator("mesh.quads_convert_to_tris", icon = "TRIANGULATE")
        props.quad_method = props.ngon_method = 'BEAUTY'
        layout.operator("mesh.tris_convert_to_quads", icon = "TRISTOQUADS")
        layout.operator("mesh.face_split_by_edges", icon = "SPLITBYEDGES")

        layout.separator()

        layout.operator("mesh.uvs_rotate", icon = "ROTATE_UVS")
        layout.operator("mesh.uvs_reverse", icon = "REVERSE_UVS")
        layout.operator("mesh.colors_rotate", icon = "ROTATE_COLORS")
        layout.operator("mesh.colors_reverse", icon = "REVERSE_COLORS")

# bfa - Not longer connected. but the menu remains available for the Blender keymap.
class VIEW3D_MT_edit_mesh_clean(Menu):
    bl_label = "Clean up"

    def draw(self, context):
        layout = self.layout

        layout.operator("mesh.delete_loose", icon = "DELETE_LOOSE")

        layout.separator()

        layout.operator("mesh.decimate", icon = "DECIMATE")
        layout.operator("mesh.dissolve_degenerate", icon = "DEGENERATE_DISSOLVE")
        layout.operator("mesh.face_make_planar", icon = "MAKE_PLANAR")
        layout.operator("mesh.vert_connect_nonplanar", icon = "SPLIT_NONPLANAR")
        layout.operator("mesh.vert_connect_concave", icon = "SPLIT_CONCAVE")
        layout.operator("mesh.fill_holes", icon = "FILL_HOLE")


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

        layout.operator("gpencil.delete", text = "Points", icon = "DELETE").type = 'POINTS'
        layout.operator("gpencil.delete", text = "Strokes", icon = "DELETE").type = 'STROKES'
        layout.operator("gpencil.delete", text = "Frame", icon = "DELETE").type = 'FRAME'

        layout.separator()

        layout.operator("gpencil.dissolve", icon = "DELETE")

        layout.separator()

        layout.operator("gpencil.active_frames_delete_all", icon = "DELETE")


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

        layout.operator("curve.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("curve.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("curve.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


def draw_curve(self, context):
    layout = self.layout

    toolsettings = context.tool_settings
    ob = context.active_object

    #layout.menu("VIEW3D_MT_transform")

    layout.separator()

    layout.operator("curve.duplicate_move", icon = "DUPLICATE")
    layout.operator("curve.delete", text="Delete...", icon = "DELETE")
    
    layout.separator()

    layout.menu("VIEW3D_MT_hook")

    layout.separator()

    layout.menu("VIEW3D_MT_edit_curve_show_hide")# bfa - the new show hide menu with separated tooltips


class VIEW3D_MT_edit_curve(Menu):
    bl_label = "Curve"

    draw = draw_curve    


class VIEW3D_MT_edit_curve_specials(Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator("curve.subdivide")
        layout.operator("curve.switch_direction", icon = "SWITCH_DIRECTION")
        layout.operator("curve.spline_weight_set")
        layout.operator("curve.radius_set")
        layout.operator("curve.smooth")
        layout.operator("curve.smooth_weight")
        layout.operator("curve.smooth_radius")
        layout.operator("curve.smooth_tilt")


class VIEW3D_MT_edit_curve_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator_enum("curve.delete", "type")

        layout.separator()

        layout.operator("curve.dissolve_verts")


class VIEW3D_MT_edit_surface(Menu):
    bl_label = "Surface"

    draw = draw_curve


class VIEW3D_MT_edit_font(Menu):
    bl_label = "Text"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_edit_text_chars")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_font_move_select")

        layout.separator()

        layout.operator("font.delete", icon = "DELETE").type = 'NEXT_OR_SELECTION'

# move_select submenu
class VIEW3D_MT_edit_font_move_select(Menu):
    bl_label = "Select Text"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.move_select", text = "Line End", icon = "HAND").type = 'LINE_END'
        layout.operator("font.move_select", text = "Line Begin", icon = "HAND").type = 'LINE_BEGIN'
        layout.operator("font.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("font.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'
        layout.operator("font.move_select", text = "Previous Word", icon = "HAND").type = 'PREVIOUS_WORD'
        layout.operator("font.move_select", text = "Next Word", icon = "HAND").type = 'NEXT_WORD'
        layout.operator("font.move_select", text = "Previous Line", icon = "HAND").type = 'PREVIOUS_LINE'
        layout.operator("font.move_select", text = "Next Line", icon = "HAND").type = 'NEXT_LINE'
        layout.operator("font.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("font.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'
        

class VIEW3D_MT_edit_text_chars(Menu):
    bl_label = "Special Characters"

    def draw(self, context):
        layout = self.layout

        layout.operator("font.text_insert", text="Copyright", icon = "COPYRIGHT").text = "\u00A9"
        layout.operator("font.text_insert", text="Registered Trademark", icon = "TRADEMARK").text = "\u00AE"

        layout.separator()

        layout.operator("font.text_insert", text="Degree Sign", icon = "DEGREE").text = "\u00B0"
        layout.operator("font.text_insert", text="Multiplication Sign", icon = "MULTIPLICATION").text = "\u00D7"
        layout.operator("font.text_insert", text="Circle", icon = "CIRCLE").text = "\u008A"
        layout.operator("font.text_insert", text="Superscript 1", icon = "SUPER_ONE").text = "\u00B9"
        layout.operator("font.text_insert", text="Superscript 2", icon = "SUPER_TWO").text = "\u00B2"
        layout.operator("font.text_insert", text="Superscript 3", icon = "SUPER_THREE").text = "\u00B3"
        layout.operator("font.text_insert", text="Double >>", icon = "DOUBLE_RIGHT").text = "\u00BB"
        layout.operator("font.text_insert", text="Double <<", icon = "DOUBLE_LEFT").text = "\u00AB"
        layout.operator("font.text_insert", text="Promillage", icon = "PROMILLE").text = "\u2030"

        layout.separator()

        layout.operator("font.text_insert", text="Dutch Florin", icon = "DUTCH_FLORIN").text = "\u00A4"
        layout.operator("font.text_insert", text="British Pound", icon = "POUND").text = "\u00A3"
        layout.operator("font.text_insert", text="Japanese Yen", icon = "YEN").text = "\u00A5"

        layout.separator()

        layout.operator("font.text_insert", text="German S", icon = "GERMAN_S").text = "\u00DF"
        layout.operator("font.text_insert", text="Spanish Question Mark", icon = "SPANISH_QUESTION").text = "\u00BF"
        layout.operator("font.text_insert", text="Spanish Exclamation Mark", icon = "SPANISH_EXCLAMATION").text = "\u00A1"


class VIEW3D_MT_edit_meta(Menu):
    bl_label = "Metaball"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        #layout.menu("VIEW3D_MT_transform")

        layout.separator()

        layout.operator("mball.delete_metaelems", text="Delete", icon = "DELETE")
        layout.operator("mball.duplicate_move", icon = "DUPLICATE")

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

        layout.operator("mball.reveal_metaelems", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("mball.hide_metaelems", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("mball.hide_metaelems_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED") 


class VIEW3D_MT_edit_lattice(Menu):
    bl_label = "Lattice"

    def draw(self, context):
        layout = self.layout

        toolsettings = context.tool_settings

        #layout.menu("VIEW3D_MT_transform")
        layout.menu("VIEW3D_MT_edit_lattice_flip")

class VIEW3D_MT_edit_lattice_flip(Menu):
    bl_label = "Flip"

    def draw(self, context):
        layout = self.layout

        layout.operator("lattice.flip", text = " U (X) axis", icon = "FLIP_X").axis = 'U'
        layout.operator("lattice.flip", text = " V (Y) axis", icon = "FLIP_Y").axis = 'V'
        layout.operator("lattice.flip", text = " W (Z) axis", icon = "FLIP_Z").axis = 'W'



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

        layout.operator("armature.reveal", text="Show Hidden", icon = "RESTRICT_VIEW_OFF")
        layout.operator("armature.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("armature.hide_unselected", text="Hide Unselected", icon = "HIDE_UNSELECTED")


class VIEW3D_MT_edit_armature(Menu):
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout

        edit_object = context.edit_object
        arm = edit_object.data

        #layout.menu("VIEW3D_MT_transform_armature")
        layout.menu("VIEW3D_MT_edit_armature_roll")
        layout.menu("VIEW3D_MT_edit_recalc_roll")

        layout.separator()

        if arm.use_mirror_x:
            layout.operator("armature.extrude_forked" , icon = "EXTRUDE_REGION")

        layout.operator("armature.duplicate_move", icon = "DUPLICATE")
        layout.operator("armature.delete", text = "Delete", icon = "DELETE")

        layout.separator()

        layout.operator_context = 'EXEC_AREA'
        layout.operator("armature.autoside_names", text="AutoName Left/Right", icon = "STRING").type = 'XAXIS'
        layout.operator("armature.autoside_names", text="AutoName Front/Back", icon = "STRING").type = 'YAXIS'
        layout.operator("armature.autoside_names", text="AutoName Top/Bottom", icon = "STRING").type = 'ZAXIS'
        layout.operator("armature.flip_names", icon = "FLIP")

        layout.separator()

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("armature.armature_layers", icon = "LAYER")
        layout.operator("armature.bone_layers", icon = "LAYER")

        layout.separator()

        layout.menu("VIEW3D_MT_armature_show_hide") # bfa - the new show hide menu with split tooltip
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")


class VIEW3D_MT_armature_specials(Menu):
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("armature.subdivide", text="Subdivide")
        layout.operator("armature.switch_direction", text="Switch Direction")

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("armature.autoside_names", text="AutoName Left/Right").type = 'XAXIS'
        layout.operator("armature.autoside_names", text="AutoName Front/Back").type = 'YAXIS'
        layout.operator("armature.autoside_names", text="AutoName Top/Bottom").type = 'ZAXIS'
        layout.operator("armature.flip_names", text="Flip Names")
        layout.operator("armature.symmetrize")


class VIEW3D_MT_edit_armature_roll(Menu):
    bl_label = "Bone Roll"

    def draw(self, context):
        layout = self.layout

        layout.operator("transform.transform", text="Set Roll", icon = "SET_ROLL").mode = 'BONE_ROLL'
        layout.operator("armature.roll_clear", icon = "CLEAR_ROLL")

class VIEW3D_MT_edit_recalc_roll(Menu):
    bl_label = "Recalculate Roll"

    def draw(self, context):
        layout = self.layout
        layout.label(text="- Positive: -")
        layout.operator("armature.calculate_roll", text= "Local + X Tangent", icon = "ROLL_X_TANG_POS").type = 'POS_X'
        layout.operator("armature.calculate_roll", text= "Local + Z Tangent", icon = "ROLL_Z_TANG_POS").type = 'POS_Z'
        layout.operator("armature.calculate_roll", text= "Global + X Axis", icon = "ROLL_X_POS").type = 'GLOBAL_POS_X'
        layout.operator("armature.calculate_roll", text= "Global + Y Axis", icon = "ROLL_Y_POS").type = 'GLOBAL_POS_Y'
        layout.operator("armature.calculate_roll", text= "Global + Z Axis", icon = "ROLL_Z_POS").type = 'GLOBAL_POS_Z'
        layout.label(text="- Negative: -")
        layout.operator("armature.calculate_roll", text= "Local - X Tangent", icon = "ROLL_X_TANG_NEG").type = 'NEG_X'
        layout.operator("armature.calculate_roll", text= "Local - Z Tangent", icon = "ROLL_Z_TANG_NEG").type = 'NEG_Z'
        layout.operator("armature.calculate_roll", text= "Global - X Axis", icon = "ROLL_X_NEG").type = 'GLOBAL_NEG_X'
        layout.operator("armature.calculate_roll", text= "Global - Y Axis", icon = "ROLL_Y_NEG").type = 'GLOBAL_NEG_Y'
        layout.operator("armature.calculate_roll", text= "Global - Z Axis", icon = "ROLL_Z_NEG").type = 'GLOBAL_NEG_Z'
        layout.label(text="- Other: -")
        layout.operator("armature.calculate_roll", text= "Active Bone", icon = "BONE_DATA").type = 'ACTIVE'
        layout.operator("armature.calculate_roll", text= "View Axis", icon = "MANIPUL").type = 'VIEW'
        layout.operator("armature.calculate_roll", text= "Cursor", icon = "CURSOR").type = 'CURSOR'

class VIEW3D_MT_edit_armature_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("armature.delete", text="Delete Bones", icon = "DELETE")

        layout.separator()

        layout.operator("armature.dissolve", text="Dissolve")


# ********** GPencil Stroke Edit menu **********

class VIEW3D_MT_edit_gpencil_pie(Menu):
    bl_label = "Pie Menus"

    def draw(self, context):
        layout = self.layout

        layout.label(text = "Pie menus are hotkey tools!")

        props = layout.operator("wm.call_menu_pie", text = "Tools Pie menu", icon = "MENU_PANEL")
        props.name = 'GPENCIL_MT_pie_tool_palette'

        props = layout.operator("wm.call_menu_pie", text = "Settings Pie menu", icon = "MENU_PANEL")
        props.name = 'GPENCIL_MT_pie_settings_palette'

        props = layout.operator("wm.call_menu_pie", text = "Sculpt Pie menu", icon = "MENU_PANEL")
        props.name = 'GPENCIL_MT_pie_sculpt'
        


class VIEW3D_MT_edit_gpencil(Menu):
    bl_label = "GPencil"

    def draw(self, context):
        toolsettings = context.tool_settings

        layout = self.layout

        layout.menu("VIEW3D_MT_edit_gpencil_pie")

        layout.separator()

        layout.operator("gpencil.copy", text="Copy", icon = "COPYDOWN")
        layout.operator("gpencil.paste", text="Paste", icon = "PASTEDOWN")

        layout.separator()

        layout.menu("VIEW3D_MT_edit_gpencil_delete")
        layout.operator("gpencil.duplicate_move", text="Duplicate", icon = "DUPLICATE")

        layout.separator()

        layout.menu("GPENCIL_MT_snap")

        layout.separator()

        layout.menu("VIEW3D_MT_object_animation")   # NOTE: provides keyingset access...

        layout.separator()

        layout.operator("gpencil.layer_isolate", icon = "LAYER")
        layout.operator("gpencil.reveal", icon = "RESTRICT_VIEW_OFF")
        layout.operator("gpencil.hide", text="Show Active Layer Only", icon = "HIDE_UNSELECTED").unselected = True
        layout.operator("gpencil.hide", text="Hide Active Layer", icon = "RESTRICT_VIEW_ON").unselected = False

        layout.separator()

        layout.operator_menu_enum("gpencil.move_to_layer", "layer", text="Move to Layer")

        layout.separator()

        layout.operator_menu_enum("gpencil.convert", "type", text="Convert to Geometry...")



class VIEW3D_MT_edit_gpencil_interpolate(Menu):
    bl_label = "Interpolate"

    def draw(self, context):
        layout = self.layout

        layout.operator("gpencil.interpolate", text="Interpolate")
        layout.operator("gpencil.interpolate_sequence", text="Sequence")


# ********** Panel **********


class VIEW3D_PT_grease_pencil(GreasePencilDataPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    # NOTE: this is just a wrapper around the generic GP Panel


class VIEW3D_PT_grease_pencil_palettecolor(GreasePencilPaletteColorPanel, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

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
        col.prop(view, "clip_start", text="Near")
        col.prop(view, "clip_end", text="Far")
        
        col = layout.column(align=True)
        col.prop(view, "use_render_border")
        
        ##############  Lock #####################

        layout.label(text= "Lock:")

        col = layout.column()
        col.prop(view, "lock_camera")
            
        col = layout.column()
        col.prop(view, "lock_camera_and_layers")

        subcol = col.column(align=True)
        subcol.enabled = not view.lock_camera_and_layers
        
        if not bpy.context.space_data.lock_camera_and_layers:
            subcol.label(text="Local Camera:")
            subcol.prop(view, "camera", text="")

        
        col = layout.column(align=True)
        col.active = view.region_3d.view_perspective != 'CAMERA'
              
        col.label(text="Lock to Object:")
        col.prop(view, "lock_object", text="")
        lock_object = view.lock_object

        col.separator()

        if lock_object:
            if lock_object.type == 'ARMATURE':
                col.prop_search(view, "lock_bone", lock_object.data,
                                "edit_bones" if lock_object.mode == 'EDIT'
                                else "bones",
                                text="")
        else:
            col.prop(view, "lock_cursor", text="Lock to Cursor")
      
        
        ################################################
        


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
        layout.prop(view, "lock_3d_cursor", text="Lock 3D Cursor") # bfa - show hide lock 3d cursor checkbox
        layout.prop(view, "show_cursor", text="Show 3D Cursor") # bfa - show hide cursor checkbox  

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


class VIEW3D_PT_view3d_display(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Viewport Display"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view)

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        scene = context.scene

        col = layout.column()
        col.prop(view, "show_iconbuttons", text="Icon or Text Buttons") # bfa - show hide icon or text checkbox      
        col.prop(view, "show_only_render")
        col.prop(view, "show_world")
  
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
            layout.label(text="Quadview Options:")
            region = view.region_quadviews[2]
            col = layout.column()
            col.prop(region, "lock_rotation")
            row = col.row()
            row.enabled = region.lock_rotation
            row.prop(region, "show_sync_view")
            row = col.row()
            row.enabled = region.lock_rotation and region.show_sync_view
            row.prop(region, "use_box_clip")

        ############## Subtab Miscellaneous #####################
        
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences

        if not addon_prefs.subtab_3dview_properties_display_obj_related:
            layout.prop(addon_prefs,"subtab_3dview_properties_display_obj_related", emboss=False, icon="TRIA_RIGHT", text="- Object related -")

        else:
            layout.prop(addon_prefs,"subtab_3dview_properties_display_obj_related", emboss=False, icon="TRIA_DOWN", text="+ Object related +")

            col = layout.column()
            col.prop(view, "show_outline_selected")
            col.prop(view, "show_all_objects_origin")
            col.prop(view, "show_relationship_lines")

        ################################################


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
    bl_label = "Object Shading"
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
        if view.viewport_shade == 'TEXTURED' or context.mode == 'PAINT_TEXTURE':
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
                
                
        # --------------------------- Wireframe colors subtab
        
        obj = context.object
        
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences

        if not addon_prefs.SP_object_display_wireframecols:
            layout.prop(addon_prefs,"SP_object_display_wireframecols", emboss=False, icon="TRIA_RIGHT", text="- Wireframe Colors -")

        else:
            layout.prop(addon_prefs,"SP_object_display_wireframecols", emboss=False, icon="TRIA_DOWN", text="+ Wireframe Colors +")

            if obj is not None:
                # Custom wire color sets
                col = layout.column()
                col.prop(obj, "wire_color_set", text = "Color Set:")
                if obj.wire_color_set:
                    col = layout.column()
                    sub = col.row(align=True)
                    sub.enabled = obj.is_custom_wire_color_set  # only custom colors are editable
                    sub.prop(obj.wire_colors, "normal", text="")
                    sub.prop(obj.wire_colors, "select", text="")
                    sub.prop(obj.wire_colors, "active", text="")
            else:
                layout.label(text =  "Select an object!")


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
        
        ################ Overlay Options #############################
  
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences

        # When the click at it then it opens. And shows the hidden ui elements.
        if not addon_prefs.subtab_3dview_properties_meshdisplay_overlay:
            layout.prop(addon_prefs,"subtab_3dview_properties_meshdisplay_overlay", emboss=False, icon="TRIA_RIGHT", text="- Overlay Options -")

        else:
            layout.prop(addon_prefs,"subtab_3dview_properties_meshdisplay_overlay", emboss=False, icon="TRIA_DOWN", text="+ Overlay Options +")
            
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
                
        
        ################## Info options #########################

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences
  
        if not addon_prefs.subtab_3dview_properties_meshdisplay_info:
            layout.prop(addon_prefs,"subtab_3dview_properties_meshdisplay_info", emboss=False, icon="TRIA_RIGHT", text="- Info Options -")

        else:
            layout.prop(addon_prefs,"subtab_3dview_properties_meshdisplay_info", emboss=False, icon="TRIA_DOWN", text="+ Info Options +")

            split = layout.split()
            col = split.column()
            col.label(text="Edge Info:")
            col.prop(mesh, "show_extra_edge_length", text="Length")
            col.prop(mesh, "show_extra_edge_angle", text="Angle")
            col = split.column()
            col.label(text="Face Info:")
            col.prop(mesh, "show_extra_face_area", text="Area")
            col.prop(mesh, "show_extra_face_angle", text="Angle")
            
            row=layout.row()
            
            if bpy.app.debug:
                row.prop(mesh, "show_extra_indices")
            else:
                row.enabled = False
                row.prop(mesh, "show_extra_indices")


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
            layout.row().prop(statvis, "overhang_axis", expand=True)
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

                        ############## Subtab Settings #####################
        
                        user_preferences = context.user_preferences
                        addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences
                        
                        if not addon_prefs.subtab_3dview_properties_bgimg_settings:
                            box.prop(addon_prefs,"subtab_3dview_properties_bgimg_settings", emboss=False, icon="TRIA_RIGHT", text="- Settings -")

                        else:
                            box.prop(addon_prefs,"subtab_3dview_properties_bgimg_settings", emboss=False, icon="TRIA_DOWN", text="+ Settings +")
                            
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

                        #######################################################

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
                    
                    ################## Align Subtab ##########################
        
                    user_preferences = context.user_preferences
                    addon_prefs = user_preferences.addons["bforartists_UI_flags"].preferences

                    if not addon_prefs.subtab_3dview_properties_bgimg_align:
                        box.prop(addon_prefs,"subtab_3dview_properties_bgimg_align", emboss=False, icon="TRIA_RIGHT", text="- Align -")

                    else:
                        box.prop(addon_prefs,"subtab_3dview_properties_bgimg_align", emboss=False, icon="TRIA_DOWN", text="+ Align +")

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

                    ###########################################################

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

class VIEW3D_PT_transform_orientations(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Transform Orientations"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view)

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        orientation = view.current_orientation

        row = layout.row(align=True)
        row.prop(view, "transform_orientation", text="")

        if orientation:
            row = layout.row(align=True)
            row.prop(orientation, "name", text="")
            row.operator("transform.delete_orientation", text="", icon='X')

        myvar= layout.operator("transform.create_orientation", text="Create Orientation", icon = "MANIPUL")
        myvar.use_view = True
        myvar.use = True

classes = (
    VIEW3D_HT_header,
    ALL_MT_editormenu,
    VIEW3D_MT_editor_menus,
    VIEW3D_PT_view3d_name,
    VIEW3D_PT_view3d_cursor,
    VIEW3D_MT_transform,
    VIEW3D_MT_transform_base,
    VIEW3D_MT_transform_object,
    VIEW3D_MT_transform_armature,
    VIEW3D_MT_snap,
    VIEW3D_MT_uv_map,
    VIEW3D_MT_view_all_all_regions,
    VIEW3D_MT_view_center_cursor_and_view_all,
    VIEW3D_MT_view_view_selected_all_regions,
    VIEW3D_MT_view,
    VIEW3D_MT_view_navigation,
    VIEW3D_MT_view_align,
    VIEW3D_MT_view_align_selected,
    VIEW3D_MT_view_cameras,
    VIEW3D_MT_select_object_inverse,
    VIEW3D_MT_select_object,
    VIEW3D_MT_select_grouped,
    VIEW3D_MT_select_by_type,
    VIEW3D_MT_select_linked,
    VIEW3D_MT_select_pose_inverse,
    VIEW3D_MT_select_pose,
    VIEW3D_MT_select_particle_inverse,
    VIEW3D_MT_select_particle,
    VIEW3D_mesh_hide_unselected,
    VIEW3D_MT_edit_mesh_show_hide,
    VIEW3D_MT_edit_mesh,
    VIEW3D_MT_edit_mesh_sort_elements,
    VIEW3D_MT_edit_mesh_select_similar,
    VIEW3D_MT_edit_mesh_select_by_trait,
    VIEW3D_MT_select_edit_mesh_inverse,
    VIEW3D_MT_select_edit_mesh,
    VIEW3D_MT_select_edit_curve_inverse,
    VIEW3D_MT_select_edit_curve,
    VIEW3D_MT_select_edit_surface,
    VIEW3D_MT_select_edit_curve_select_similar,
    VIEW3D_MT_select_edit_text,
    VIEW3D_MT_select_edit_metaball_inverse,
    VIEW3D_MT_select_edit_metaball,
    VIEW3D_MT_select_edit_metaball_select_similar,
    VIEW3D_MT_select_edit_lattice_inverse,
    VIEW3D_MT_select_edit_lattice,
    VIEW3D_MT_select_edit_armature_inverse,
    VIEW3D_MT_select_edit_armature,
    VIEW3D_MT_select_edit_armature_similar,
    VIEW3D_MT_select_gpencil,
    VIEW3D_MT_select_gpencil_grouped,
    VIEW3D_MT_select_paint_mask_inverse,
    VIEW3D_MT_select_paint_mask,
    VIEW3D_MT_select_paint_mask_vertex_inverse,
    VIEW3D_MT_select_paint_mask_vertex,
    VIEW3D_MT_angle_control,
    INFO_MT_camera_add,
    INFO_MT_curve_add,
    INFO_MT_edit_curve_add,
    INFO_MT_surface_add,
    INFO_MT_metaball_add,
    INFO_MT_armature_add,
    INFO_MT_lamp_add,
    INFO_MT_mesh_add,
    INFO_MT_add,
    VIEW3D_MT_object_delete_global,
    VIEW3D_MT_object,
    VIEW3D_MT_object_animation,
    VIEW3D_MT_object_clear,
    VIEW3D_MT_object_specials,
    VIEW3D_MT_object_apply,
    VIEW3D_MT_object_constraints,
    VIEW3D_MT_object_quick_effects,
    VIEW3D_MT_subdivision_set,
    VIEW3D_hide_view_set_unselected,
    VIEW3D_MT_object_showhide,
    VIEW3D_MT_make_single_user,
    VIEW3D_MT_object_game,
    VIEW3D_MT_brush,
    VIEW3D_MT_brush_paint_modes,
    VIEW3D_MT_paint_vertex,
    VIEW3D_MT_hook,
    VIEW3D_MT_vertex_group,
    VIEW3D_MT_paint_weight,
    VIEW3D_MT_sculpt,
    VIEW3D_MT_hide_mask,
    VIEW3D_particle_hide_unselected,
    VIEW3D_MT_particle_show_hide,
    VIEW3D_MT_particle,
    VIEW3D_MT_particle_specials,
    VIEW3D_pose_hide_unselected,
    VIEW3D_MT_pose_show_hide,
    VIEW3D_MT_pose,
    VIEW3D_MT_pose_transform,
    VIEW3D_MT_pose_slide,
    VIEW3D_MT_pose_propagate,
    VIEW3D_MT_pose_library,
    VIEW3D_MT_pose_motion,
    VIEW3D_MT_pose_group,
    VIEW3D_MT_pose_ik,
    VIEW3D_MT_pose_constraints,
    VIEW3D_MT_pose_apply,
    VIEW3D_MT_pose_specials,
    VIEW3D_MT_bone_options_toggle,
    VIEW3D_MT_bone_options_enable,
    VIEW3D_MT_bone_options_disable,
    VIEW3D_MT_edit_mesh_specials,
    VIEW3D_MT_edit_mesh_select_mode,
    VIEW3D_MT_edit_mesh_extrude_dupli,
    VIEW3D_MT_edit_mesh_extrude_dupli_rotate,
    VIEW3D_MT_edit_mesh_extrude,
    VIEW3D_MT_edit_mesh_vertices,
    VIEW3D_MT_edit_mesh_edges,
    VIEW3D_MT_edit_mesh_faces,
    VIEW3D_MT_edit_mesh_clean,
    VIEW3D_MT_edit_mesh_delete,
    VIEW3D_MT_edit_gpencil_pie,
    VIEW3D_MT_edit_gpencil,
    VIEW3D_MT_edit_gpencil_delete,
    VIEW3D_curve_hide_unselected,
    VIEW3D_MT_edit_curve_show_hide,
    VIEW3D_MT_edit_curve,
    VIEW3D_MT_edit_curve_specials,
    VIEW3D_MT_edit_curve_delete,
    VIEW3D_MT_edit_surface,
    VIEW3D_MT_edit_font,
    VIEW3D_MT_edit_font_move_select,
    VIEW3D_MT_edit_text_chars,
    VIEW3D_MT_edit_meta,
    VIEW3D_MT_edit_meta_showhide_unselected,
    VIEW3D_MT_edit_meta_showhide,
    VIEW3D_MT_edit_lattice,
    VIEW3D_MT_edit_lattice_flip,
    VIEW3D_armature_hide_unselected,
    VIEW3D_MT_armature_show_hide,
    VIEW3D_MT_edit_armature,
    VIEW3D_MT_armature_specials,
    VIEW3D_MT_edit_armature_roll,
    VIEW3D_MT_edit_recalc_roll,
    VIEW3D_MT_edit_armature_delete,
    VIEW3D_MT_edit_gpencil_interpolate,
    VIEW3D_PT_grease_pencil,
    VIEW3D_PT_grease_pencil_palettecolor,
    VIEW3D_PT_view3d_properties,
    VIEW3D_PT_view3d_display,
    VIEW3D_PT_view3d_stereo,
    VIEW3D_PT_view3d_shading,
    VIEW3D_PT_view3d_motion_tracking,
    VIEW3D_PT_view3d_meshdisplay,
    VIEW3D_PT_view3d_meshstatvis,
    VIEW3D_PT_view3d_curvedisplay,
    VIEW3D_PT_background_image,
    VIEW3D_PT_etch_a_ton,
    VIEW3D_PT_context_properties,
    VIEW3D_PT_transform_orientations,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
