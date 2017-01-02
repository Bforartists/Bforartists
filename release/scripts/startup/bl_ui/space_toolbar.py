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
from bpy.types import Header, Menu


class TOOLBAR_HT_header(Header):
    bl_space_type = 'TOOLBAR'

    def draw(self, context):
        layout = self.layout

        window = context.window
        scene = context.scene
      
        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        TOOLBAR_MT_toolbar_type.draw_collapsible(context, layout) # bfa the toolbar type

        ############## toolbars ##########################################################################

        TOOLBAR_MT_file.hide_file_toolbar(context, layout) # bfa - show hide the complete toolbar container
        TOOLBAR_MT_view.hide_view_toolbar(context, layout)
        TOOLBAR_MT_primitives.hide_primitives_toolbar(context, layout)
        TOOLBAR_MT_image.hide_image_toolbar(context, layout)
        TOOLBAR_MT_tools.hide_tools_toolbar(context, layout)
        TOOLBAR_MT_animation.hide_animation_toolbar(context, layout)
        TOOLBAR_MT_edit.hide_edit_toolbar(context, layout)
        TOOLBAR_MT_misc.hide_misc_toolbar(context, layout)

########################################################################

# bfa - show hide the editortype menu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

########################################################################

################ Toolbar type

# Everything menu in this class is collapsible.
class TOOLBAR_MT_toolbar_type(Menu):
    bl_idname = "TOOLBAR_MT_toolbar_type"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.operator("screen.toolbar_toolbox", text="Type")


######################################## Toolbars ##############################################


######################################## LoadSave ##############################################


#################### Holds the Toolbars menu for file, collapsible

class TOOLBAR_MT_menu_file(Menu):
    bl_idname = "TOOLBAR_MT_menu_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_file_menu") # see class TOOLBAR_MT_file below


##################### Load Save sub toolbars menu

class TOOLBAR_MT_toolbars_file_menu(Menu):
    bl_label = "Toolbars File"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_file_loadsave, "bool")

        layout.prop(scene.toolbar_file_linkappend, "bool")

        layout.prop(scene.toolbar_file_importcommon, "bool")
        layout.prop(scene.toolbar_file_importuncommon, "bool")
        layout.prop(scene.toolbar_file_exportcommon, "bool")
        layout.prop(scene.toolbar_file_exportuncommon, "bool")
        layout.prop(scene.toolbar_file_render, "bool")  
        layout.prop(scene.toolbar_file_render_view, "bool")  
        layout.prop(scene.toolbar_file_render_misc, "bool")  
            
############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_file(Menu):
    bl_idname = "TOOLBAR_MT_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_file.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_file_loadsave.bool: 

            row = layout.row(align=True)

            row.operator("wm.read_homefile", text="", icon='NEW')

            row = layout.row(align=True)

            row.operator("wm.open_mainfile", text="", icon='FILE_FOLDER')
            row.menu("INFO_MT_file_open_recent", text="", icon='OPEN_RECENT')

            row = layout.row(align=True)

            row.operator("wm.save_mainfile", text="", icon='FILE_TICK')
            row.operator("wm.save_as_mainfile", text="", icon='SAVE_AS')
            row.operator("wm.save_as_mainfile", text="", icon='SAVE_COPY')

        ## ------------------ Link Append

        if scene.toolbar_file_linkappend.bool: 

            row = layout.row(align=True)

            row.operator("wm.link", text="", icon='LINK_BLEND')
            row.operator("wm.append", text="", icon='APPEND_BLEND')

        ## ------------------ Import common

        if scene.toolbar_file_importcommon.bool:

            row = layout.row(align=True)

            row.operator("import_scene.fbx", text="", icon='LOAD_FBX')
            row.operator("import_scene.obj", text="", icon='LOAD_OBJ')
            row.operator("wm.collada_import", text="", icon='LOAD_DAE')
            row.operator("import_anim.bvh", text="", icon='LOAD_BVH')
            row.operator("import_scene.autodesk_3ds", text="", icon='LOAD_3DS')

        ## ------------------ Import uncommon

        if scene.toolbar_file_importuncommon.bool:

            row = layout.row(align=True)

            row.operator("import_mesh.stl", text="", icon='LOAD_STL')
            row.operator("import_mesh.ply", text="", icon='LOAD_PLY')
            row.operator("import_scene.x3d", text="", icon='LOAD_WRL')
            row.operator("import_curve.svg", text="", icon='LOAD_SVG')
            
        ## ------------------ Export common

        if scene.toolbar_file_exportcommon.bool:

            row = layout.row(align=True)

            row.operator("export_scene.fbx", text="", icon='SAVE_FBX')
            row.operator("export_scene.obj", text="", icon='SAVE_OBJ')
            row.operator("wm.collada_export", text="", icon='SAVE_DAE')
            row.operator("export_anim.bvh", text="", icon='SAVE_BVH')
            row.operator("export_scene.autodesk_3ds", text="", icon='SAVE_3DS')

        ## ------------------ Export uncommon

        if scene.toolbar_file_exportuncommon.bool:

            row = layout.row(align=True)

            row.operator("export_mesh.stl", text="", icon='SAVE_STL')
            row.operator("export_mesh.ply", text="", icon='SAVE_PLY')
            row.operator("export_scene.x3d", text="", icon='SAVE_WRL') 

        ## ------------------ Render

        if scene.toolbar_file_render.bool:

            row = layout.row(align=True)

            row.operator("render.render", text="", icon='RENDER_STILL').use_viewport = True
            props = row.operator("render.render", text="", icon='RENDER_ANIMATION')
            props.animation = True
            props.use_viewport = True

        ## ------------------ Render

        if scene.toolbar_file_render_view.bool:

            row = layout.row(align=True)

            row.operator("render.opengl", text="", icon = 'RENDER_STILL_VIEW')
            row.operator("render.opengl", text="", icon = 'RENDER_ANI_VIEW').animation = True
            row.menu("INFO_MT_opengl_render", text = "", icon='TRIA_UP')

        ## ------------------ Render

        if scene.toolbar_file_render_misc.bool:

            row = layout.row(align=True)

            row.operator("sound.mixdown", text="", icon='PLAY_AUDIO')

            row = layout.row(align=True)

            row.operator("render.view_show", text="", icon = 'HIDE_RENDERVIEW')
            row.operator("render.play_rendered_anim", icon='PLAY', text="")

######################################## View ##############################################


#################### Holds the Toolbars menu for view, collapsible

class TOOLBAR_MT_menu_view(Menu):
    bl_idname = "TOOLBAR_MT_menu_view"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_view_menu") # see class TOOLBAR_MT_file below


##################### Load Save sub toolbars menu

class TOOLBAR_MT_toolbars_view_menu(Menu):
    bl_label = "Toolbars View"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_view_align, "bool")
        layout.prop(scene.toolbar_view_camera, "bool")


############### Change view classes

class VIEW3D_MT_totop(bpy.types.Operator):
    """Change view to Top\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.totop"
    bl_label = "view from top"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='TOP', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_tobottom(bpy.types.Operator):
    """Change view to Bottom\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.tobottom"
    bl_label = "view from bottom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='BOTTOM', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_tofront(bpy.types.Operator):
    """Change view to Top\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.tofront"
    bl_label = "view from front"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='FRONT', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_tobback(bpy.types.Operator):
    """Change view to Bottom\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.toback"
    bl_label = "view from back"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='BACK', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_toleft(bpy.types.Operator):
    """Change view to Left\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.toleft"
    bl_label = "view from left"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='LEFT', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_toright(bpy.types.Operator):
    """Change view to Right\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.toright"
    bl_label = "view from right"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='RIGHT', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_reset3dview(bpy.types.Operator):
    """Reset 3D View \nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.rese3dtview"
    bl_label = "view from right"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view.reset_3d_view()
        return {'FINISHED'} 

class VIEW3D_MT_tocam(bpy.types.Operator):
    """Switch to / from Camera view\nSwitches the scene display between active camera and world camera\nThis button is global, and changes all available 3D views\nUse the View menu to change the view just in selected 3d view"""
    bl_idname = "view3d.tocam"
    bl_label = "view from active camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='CAMERA', align_active=False)
        return {'FINISHED'} 

class VIEW3D_MT_switchactivecam(bpy.types.Operator):
    """Set Active Camera\nBe careful, you can also set objects as the active camera, not only other cameras.\nSo make sure that a camera is selected."""
    bl_idname = "view3d.switchactivecam"
    bl_label = "Set active Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context): 

        context = bpy.context
        scene = context.scene
        if context.active_object is not None:
            currentCameraObj = bpy.data.objects[bpy.context.active_object.name]
            scene.camera = currentCameraObj     
        return {'FINISHED'} 

            
############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_view(Menu):
    bl_idname = "TOOLBAR_MT_view"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        #rd = scene.render

        TOOLBAR_MT_menu_view.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_view_align.bool: 

            row = layout.row(align=True)
            
            row.operator("view3d.tofront", text="", icon ="VIEW_FRONT")
            row.operator("view3d.toback", text="", icon ="VIEW_BACK")
            row.operator("view3d.toleft", text="", icon ="VIEW_LEFT")
            row.operator("view3d.toright", text="", icon ="VIEW_RIGHT")
            row.operator("view3d.totop", text="", icon ="VIEW_TOP")
            row.operator("view3d.tobottom", text="", icon ="VIEW_BOTTOM")
            row.operator("view3d.rese3dtview", text="", icon ="VIEW_RESET")

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_view_camera.bool: 

            row = layout.row(align=True)
            
            row.operator("view3d.tocam", text="", icon ="VIEW_SWITCHTOCAM")
            row.operator("view3d.switchactivecam", text="", icon ="VIEW_SWITCHACTIVECAM")
            

######################################## Primitives ##############################################


#################### Holds the Toolbars menu for Primitives, collapsible

class TOOLBAR_MT_menu_primitives(Menu):
    bl_idname = "TOOLBAR_MT_menu_primitives"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_primitives_menu") # see class below


##################### Primitives toolbars menu

class TOOLBAR_MT_toolbars_primitives_menu(Menu):
    bl_label = "Toolbars Primitives"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_primitives_mesh, "bool")
        layout.prop(scene.toolbar_primitives_curve, "bool")
        layout.prop(scene.toolbar_primitives_surface, "bool")
        layout.prop(scene.toolbar_primitives_metaball, "bool")

        layout.prop(scene.toolbar_primitives_lamp, "bool")
        layout.prop(scene.toolbar_primitives_other, "bool")
        layout.prop(scene.toolbar_primitives_empties, "bool")
        layout.prop(scene.toolbar_primitives_forcefield, "bool")

            
############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_primitives(Menu):
    bl_idname = "TOOLBAR_MT_primitives"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        #rd = scene.render

        TOOLBAR_MT_menu_primitives.draw_collapsible(context, layout)

        obj = context.object 

        if obj is None:

            ## ------------------ primitives sub toolbars

            if scene.toolbar_primitives_mesh.bool: 

                row = layout.row(align=True)

                row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')       
                row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')

            if scene.toolbar_primitives_curve.bool: 

                row = layout.row(align=True)

                row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

            if scene.toolbar_primitives_surface.bool: 

                row = layout.row(align=True)

                row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

            if scene.toolbar_primitives_metaball.bool: 
                row = layout.row(align=True)

                row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

            if scene.toolbar_primitives_lamp.bool: 

                row = layout.row(align=True)

                row.operator("object.lamp_add", text="", icon='LAMP_POINT').type= 'POINT'
                row.operator("object.lamp_add", text="", icon='LAMP_SUN').type= 'SUN' 
                row.operator("object.lamp_add", text="", icon='LAMP_SPOT').type= 'SPOT' 
                row.operator("object.lamp_add", text="", icon='LAMP_HEMI').type= 'HEMI' 
                row.operator("object.lamp_add", text="", icon='LAMP_AREA').type= 'AREA' 

            if scene.toolbar_primitives_other.bool: 

                row = layout.row(align=True)

                row.operator("object.text_add", text="", icon='OUTLINER_OB_FONT')
                row.operator("object.armature_add", text="", icon='OUTLINER_OB_ARMATURE')
                row.operator("object.add", text="", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
                row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA')
                row.operator("object.speaker_add", text="", icon='OUTLINER_OB_SPEAKER')

            if scene.toolbar_primitives_empties.bool: 

                row = layout.row(align=True)

                row.operator("object.empty_add", text="", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
                row.operator("object.empty_add", text="", icon='EMPTY_SPHERE').type = 'SPHERE'
                row.operator("object.empty_add", text="", icon='EMPTY_CIRCLE').type = 'CIRCLE'
                row.operator("object.empty_add", text="", icon='EMPTY_CONE').type = 'CONE'
                row.operator("object.empty_add", text="", icon='EMPTY_CUBE').type = 'CUBE'      
                row.operator("object.empty_add", text="", icon='EMPTY_SINGLEARROW').type = 'SINGLE_ARROW'       
                row.operator("object.empty_add", text="", icon='EMPTY_ARROWS').type = 'ARROWS'
                row.operator("object.empty_add", text="", icon='EMPTY_IMAGE').type = 'IMAGE'

            if scene.toolbar_primitives_forcefield.bool: 

                row = layout.row(align=True)

                row.operator("object.effector_add", text="", icon='FORCE_BOID').type='BOID'
                row.operator("object.effector_add", text="", icon='FORCE_CHARGE').type='CHARGE'
                row.operator("object.effector_add", text="", icon='FORCE_CURVE').type='GUIDE'
                row.operator("object.effector_add", text="", icon='FORCE_DRAG').type='DRAG'
                row.operator("object.effector_add", text="", icon='FORCE_FORCE').type='FORCE'
                row.operator("object.effector_add", text="", icon='FORCE_HARMONIC').type='HARMONIC'
                row.operator("object.effector_add", text="", icon='FORCE_LENNARDJONES').type='LENNARDJ'
                row.operator("object.effector_add", text="", icon='FORCE_MAGNETIC').type='MAGNET'
                row.operator("object.effector_add", text="", icon='FORCE_SMOKEFLOW').type='SMOKE'
                row.operator("object.effector_add", text="", icon='FORCE_TEXTURE').type='TEXTURE'
                row.operator("object.effector_add", text="", icon='FORCE_TURBULENCE').type='TURBULENCE'
                row.operator("object.effector_add", text="", icon='FORCE_VORTEX').type='VORTEX'
                row.operator("object.effector_add", text="", icon='FORCE_WIND').type='WIND'

        elif obj is not None:

            mode = obj.mode

            if mode == 'OBJECT':

                ## ------------------ primitives sub toolbars

                if scene.toolbar_primitives_mesh.bool: 

                    row = layout.row(align=True)

                    row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                    row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                    row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                    row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                    row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')       
                    row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                    row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                    row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')

                if scene.toolbar_primitives_curve.bool: 

                    row = layout.row(align=True)

                    row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                    row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                    row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                    row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                    row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                if scene.toolbar_primitives_surface.bool: 

                    row = layout.row(align=True)

                    row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                    row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                    row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                    row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                    row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                    row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                if scene.toolbar_primitives_metaball.bool: 
                    row = layout.row(align=True)

                    row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                    row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                    row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                    row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                    row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

                if scene.toolbar_primitives_lamp.bool: 

                    row = layout.row(align=True)

                    row.operator("object.lamp_add", text="", icon='LAMP_POINT').type= 'POINT'
                    row.operator("object.lamp_add", text="", icon='LAMP_SUN').type= 'SUN' 
                    row.operator("object.lamp_add", text="", icon='LAMP_SPOT').type= 'SPOT' 
                    row.operator("object.lamp_add", text="", icon='LAMP_HEMI').type= 'HEMI' 
                    row.operator("object.lamp_add", text="", icon='LAMP_AREA').type= 'AREA' 

                if scene.toolbar_primitives_other.bool: 

                    row = layout.row(align=True)

                    row.operator("object.text_add", text="", icon='OUTLINER_OB_FONT')
                    row.operator("object.armature_add", text="", icon='OUTLINER_OB_ARMATURE')
                    row.operator("object.add", text="", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
                    row.operator("object.camera_add", text="", icon='OUTLINER_OB_CAMERA')
                    row.operator("object.speaker_add", text="", icon='OUTLINER_OB_SPEAKER')

                if scene.toolbar_primitives_empties.bool: 

                    row = layout.row(align=True)

                    row.operator("object.empty_add", text="", icon='OUTLINER_OB_EMPTY').type = 'PLAIN_AXES'
                    row.operator("object.empty_add", text="", icon='EMPTY_SPHERE').type = 'SPHERE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CIRCLE').type = 'CIRCLE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CONE').type = 'CONE'
                    row.operator("object.empty_add", text="", icon='EMPTY_CUBE').type = 'CUBE'      
                    row.operator("object.empty_add", text="", icon='EMPTY_SINGLEARROW').type = 'SINGLE_ARROW'       
                    row.operator("object.empty_add", text="", icon='EMPTY_ARROWS').type = 'ARROWS'
                    row.operator("object.empty_add", text="", icon='EMPTY_IMAGE').type = 'IMAGE'

                if scene.toolbar_primitives_forcefield.bool: 

                    row = layout.row(align=True)

                    row.operator("object.effector_add", text="", icon='FORCE_BOID').type='BOID'
                    row.operator("object.effector_add", text="", icon='FORCE_CHARGE').type='CHARGE'
                    row.operator("object.effector_add", text="", icon='FORCE_CURVE').type='GUIDE'
                    row.operator("object.effector_add", text="", icon='FORCE_DRAG').type='DRAG'
                    row.operator("object.effector_add", text="", icon='FORCE_FORCE').type='FORCE'
                    row.operator("object.effector_add", text="", icon='FORCE_HARMONIC').type='HARMONIC'
                    row.operator("object.effector_add", text="", icon='FORCE_LENNARDJONES').type='LENNARDJ'
                    row.operator("object.effector_add", text="", icon='FORCE_MAGNETIC').type='MAGNET'
                    row.operator("object.effector_add", text="", icon='FORCE_SMOKEFLOW').type='SMOKE'
                    row.operator("object.effector_add", text="", icon='FORCE_TEXTURE').type='TEXTURE'
                    row.operator("object.effector_add", text="", icon='FORCE_TURBULENCE').type='TURBULENCE'
                    row.operator("object.effector_add", text="", icon='FORCE_VORTEX').type='VORTEX'
                    row.operator("object.effector_add", text="", icon='FORCE_WIND').type='WIND'

            if mode == 'EDIT':

                if obj.type == 'MESH':

                    if scene.toolbar_primitives_mesh.bool: 

                        row = layout.row(align=True)

                        row.operator("mesh.primitive_plane_add", text="", icon='MESH_PLANE')
                        row.operator("mesh.primitive_cube_add", text="", icon='MESH_CUBE')
                        row.operator("mesh.primitive_circle_add", text="", icon='MESH_CIRCLE')
                        row.operator("mesh.primitive_uv_sphere_add", text="", icon='MESH_UVSPHERE')
                        row.operator("mesh.primitive_ico_sphere_add", text="", icon='MESH_ICOSPHERE')       
                        row.operator("mesh.primitive_cylinder_add", text="", icon='MESH_CYLINDER')
                        row.operator("mesh.primitive_cone_add", text="", icon='MESH_CONE')
                        row.operator("mesh.primitive_torus_add", text="", icon='MESH_TORUS')

                if obj.type == 'CURVE':

                    if scene.toolbar_primitives_curve.bool: 

                        row = layout.row(align=True)

                        row.operator("curve.primitive_bezier_curve_add", text="", icon='CURVE_BEZCURVE')
                        row.operator("curve.primitive_bezier_circle_add", text="", icon='CURVE_BEZCIRCLE')
                        row.operator("curve.primitive_nurbs_curve_add", text="", icon='CURVE_NCURVE')
                        row.operator("curve.primitive_nurbs_circle_add", text="", icon='CURVE_NCIRCLE')
                        row.operator("curve.primitive_nurbs_path_add", text="", icon='CURVE_PATH')

                if obj.type == 'SURFACE':

                    if scene.toolbar_primitives_surface.bool: 

                        row = layout.row(align=True)

                        row.operator("surface.primitive_nurbs_surface_curve_add", text="", icon='SURFACE_NCURVE')
                        row.operator("surface.primitive_nurbs_surface_circle_add", text="", icon='SURFACE_NCIRCLE')
                        row.operator("surface.primitive_nurbs_surface_surface_add", text="", icon='SURFACE_NSURFACE')
                        row.operator("surface.primitive_nurbs_surface_cylinder_add", text="", icon='SURFACE_NCYLINDER')
                        row.operator("surface.primitive_nurbs_surface_sphere_add", text="", icon='SURFACE_NSPHERE')
                        row.operator("surface.primitive_nurbs_surface_torus_add", text="", icon='SURFACE_NTORUS')

                if obj.type == 'META':

                    if scene.toolbar_primitives_metaball.bool: 

                        row = layout.row(align=True)

                        row.operator("object.metaball_add", text="", icon='META_BALL').type= 'BALL'
                        row.operator("object.metaball_add", text="", icon='META_CAPSULE').type= 'CAPSULE'
                        row.operator("object.metaball_add", text="", icon='META_PLANE').type= 'PLANE'
                        row.operator("object.metaball_add", text="", icon='META_ELLIPSOID').type= 'ELLIPSOID'
                        row.operator("object.metaball_add", text="", icon='META_CUBE').type= 'CUBE'

######################################## Image ##############################################

# Try to give unique tooltip fails at wrong context issue. Code remains for now. Maybe we find a solution here.

#class VIEW3D_MT_uv_straighten(bpy.types.Operator):
#    """Straighten\nStraightens the selected geometry"""
#    bl_idname = "image.uv_straighten"
#    bl_label = "straighten"
#    bl_options = {'REGISTER', 'UNDO'}

#    def execute(self, context):
#        for area in bpy.context.screen.areas:
#            if area.type == 'IMAGE_EDITOR':
#                override = bpy.context.copy()
#                override['area'] = area
#                bpy.ops.uv.align(axis = 'ALIGN_S')
#        return {'FINISHED'}


#################### Holds the Toolbars menu for Image, collapsible

class TOOLBAR_MT_menu_image(Menu):
    bl_idname = "TOOLBAR_MT_menu_image"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_image_menu") # see class below


##################### Image toolbars menu

class TOOLBAR_MT_toolbars_image_menu(Menu):
    bl_label = "Toolbars Image"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_image_uvcommon, "bool")
        layout.prop(scene.toolbar_image_uvmisc, "bool")
        layout.prop(scene.toolbar_image_uvalign, "bool")
            
############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_image(Menu):
    bl_idname = "TOOLBAR_MT_image"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_image.draw_collapsible(context, layout)

        ## ------------------ image sub toolbars

        if scene.toolbar_image_uvcommon.bool: 

            row = layout.row(align=True)

            row.operator("uv.pack_islands", text="", icon ="PACKISLAND")
            row.operator("uv.average_islands_scale", text="", icon ="AVERAGEISLANDSCALE")
            #row.operator("uv.minimize_stretch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.
            #row.operator("uv.stitch") # doesn't work in toolbar editor, needs to be performed in image editor where the uv mesh is.
            row.operator("uv.mark_seam", text="", icon ="MARK_SEAM").clear = False
            row.operator("uv.mark_seam", text="", icon ="CLEAR_SEAM").clear = True
            row.operator("uv.seams_from_islands", text="", icon ="SEAMSFROMISLAND")
            row.operator("mesh.faces_mirror_uv", text="", icon ="COPYMIRRORED")

        if scene.toolbar_image_uvmisc.bool: 

            row = layout.row(align=True)

            row.operator("uv.unwrap", text = "", icon='UNWRAP_ABF').method='ANGLE_BASED'
            row.operator("uv.unwrap", text = "", icon='UNWRAP_LSCM').method='CONFORMAL'   
            row.operator("uv.pin", text= "", icon = "PINNED").clear = False
            row.operator("uv.pin", text="", icon = "UNPINNED").clear = True

        if scene.toolbar_image_uvalign.bool: 

            row = layout.row(align=True)

            row.operator("uv.weld", text="", icon='WELD')
            row.operator("uv.remove_doubles", text="", icon='REMOVE_DOUBLES')
            #row.operator_enum("uv.align", "axis")  # W, 2/3/4 # bfa - enum is no good idea in header. It enums below each other. And the header just shows besides ...

            row.operator("uv.align", text= "", icon = "STRAIGHTEN").axis = 'ALIGN_S'
            row.operator("uv.align", text= "", icon = "STRAIGHTEN_X").axis = 'ALIGN_T'
            row.operator("uv.align", text= "", icon = "STRAIGHTEN_Y").axis = 'ALIGN_U'
            row.operator("uv.align", text= "", icon = "ALIGNAUTO").axis = 'ALIGN_AUTO'
            row.operator("uv.align", text= "", icon = "ALIGNHORIZONTAL").axis = 'ALIGN_X'
            row.operator("uv.align", text= "", icon = "ALIGNVERTICAL").axis = 'ALIGN_Y'

            # Try to give unique tooltip fails at wrong context issue. It throws an error when you are not in edit mode, have no uv editor open, and there is no mesh selected.
            # Code remains here for now. Maybe we find a solution at a later point.
            #row.operator("image.uv_straighten", text= "straighten")

######################################## Tools ##############################################

#################### Holds the Toolbars menu for Tools, collapsible

class TOOLBAR_MT_menu_tools(Menu):
    bl_idname = "TOOLBAR_MT_menu_tools"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_tools_menu") # see class below


##################### Tools toolbars menu

class TOOLBAR_MT_toolbars_tools_menu(Menu):
    bl_label = "Toolbars Tools"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_tools_history, "bool")
        layout.prop(scene.toolbar_tools_relations, "bool")
        layout.prop(scene.toolbar_tools_edit, "bool")
            
############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_tools(Menu):
    bl_idname = "TOOLBAR_MT_tools"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_tools.draw_collapsible(context, layout)

        obj = context.object 

        ## ------------------ Tools sub toolbars

        if scene.toolbar_tools_history.bool:

            row = layout.row(align=True)

            row.operator("ed.undo", icon='UNDO',text="")
            row.operator("ed.redo", icon='REDO',text="")
            if obj is None or obj.mode != 'SCULPT':
                # Sculpt mode does not generate an undo menu it seems...
                row.operator("ed.undo_history", icon='UNDO_HISTORY',text="")

            row = layout.row(align=True)

            row.operator("screen.repeat_last", icon='REPEAT', text="")
            row.operator("screen.repeat_history", icon='REDO_HISTORY', text="")

        if obj is not None:

            mode = obj.mode

            if mode == 'OBJECT':

                if scene.toolbar_tools_relations.bool:

                    row = layout.row(align=True)

                    row.operator("group.create", icon='NEW_GROUP', text="")
                    row.operator("group.objects_add_active", icon='ADD_TO_ACTIVE', text="")
                    row.operator("group.objects_remove", icon='REMOVE_FROM_GROUP', text="")

                    row = layout.row(align=True)
                    row.operator("group.objects_remove_active", icon='REMOVE_SELECTED_FROM_ACTIVE_GROUP', text="")
                    row.operator("group.objects_remove_all", icon='REMOVE_FROM_ALL_GROUPS', text="")

                    row = layout.row(align=True)

                    row.operator("object.parent_set", icon='PARENT_SET', text="")
                    row.operator("object.parent_clear", icon='PARENT_CLEAR', text="")

                    row = layout.row(align=True)

                    row.operator("object.make_links_data", icon='LINK_DATA', text="")
                    row.operator("object.make_single_user", icon='MAKE_SINGLE_USER', text="")

                    row = layout.row(align=True)

                    row.operator("object.make_local", icon='MAKE_LOCAL', text="")
                    row.operator("object.proxy_make", icon='MAKE_PROXY', text="")

                if scene.toolbar_tools_edit.bool:

                    obj_type = obj.type

                    row = layout.row(align=True)

                    row.operator("transform.mirror", icon='TRANSFORM_MIRROR', text="")
                    if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE'}:
                        row.operator("object.join", icon ='JOIN', text= "" )

                    if obj_type in {'MESH', 'CURVE', 'SURFACE', 'ARMATURE', 'FONT', 'LATTICE'}:
                        
                        row = layout.row(align=True)

                        row.operator("object.origin_set", icon ='GEOMETRY_TO_ORIGIN', text="").type='GEOMETRY_ORIGIN'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_GEOMETRY', text="").type='ORIGIN_GEOMETRY'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_CURSOR', text="").type='ORIGIN_CURSOR'
                        row.operator("object.origin_set", icon ='ORIGIN_TO_CENTEROFMASS', text="").type='ORIGIN_CENTER_OF_MASS'

                    if obj_type in {'MESH', 'CURVE', 'SURFACE'}:
                        
                        row = layout.row(align=True)

                        row.operator("object.shade_smooth", icon ='SHADING_SMOOTH', text="")
                        row.operator("object.shade_flat", icon ='SHADING_FLAT', text="")

                    if obj_type == 'MESH':
                        
                        row = layout.row(align=True)

                        row.operator("object.data_transfer", icon ='TRANSFER_DATA', text="")
                        row.operator("object.datalayout_transfer", icon ='TRANSFER_DATA_LAYOUT', text="")

            if mode == 'EDIT':

                if scene.toolbar_tools_relations.bool:

                    row = layout.row(align=True)

                    row.operator("object.vertex_parent_set")

                    if obj.type == 'ARMATURE':

                        row = layout.row(align=True)

                        row.operator("armature.parent_set", icon='PARENT_SET', text="")
                        row.operator("armature.parent_clear", icon='PARENT_CLEAR', text="")

######################################## Animation ##############################################

#################### Holds the Toolbars menu for Animation, collapsible

class TOOLBAR_MT_menu_animation(Menu):
    bl_idname = "TOOLBAR_MT_menu_animation"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_animation_menu") # see class below

##################### Animation toolbars menu

class TOOLBAR_MT_toolbars_animation_menu(Menu):
    bl_label = "Toolbars Animation"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_animation_keyframes, "bool")
        layout.prop(scene.toolbar_animation_range, "bool")
        layout.prop(scene.toolbar_animation_play, "bool")
        layout.prop(scene.toolbar_animation_sync, "bool")
        layout.prop(scene.toolbar_animation_keyingset, "bool")
         
############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_animation(Menu):
    bl_idname = "TOOLBAR_MT_animation"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        screen = context.screen
        toolsettings = context.tool_settings
        userprefs = context.user_preferences

        TOOLBAR_MT_menu_animation.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_animation_keyframes.bool: 

            obj = context.object

            if obj is not None:

                mode = obj.mode

                if mode == 'OBJECT':

                    row = layout.row(align=True)

                    row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text="")
                    row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="")
                    row.operator("nla.bake", icon= 'BAKE_ACTION',text="")
                    row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="")

                    row = layout.row(align=True)

                    row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text="")
                    row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="")                  

                if mode == 'POSE':

                    row = layout.row(align=True)

                    row.operator("pose.push", icon = 'PUSH_POSE', text="")
                    row.operator("pose.relax", icon = 'RELAX_POSE',text="")
                    row.operator("pose.breakdown", icon = 'BREAKDOWNER_POSE',text="")

                    row = layout.row(align=True)

                    row.operator("pose.propagate", text="Propagate")
                    row.menu("VIEW3D_MT_pose_propagate", icon='TRIA_RIGHT', text="")

                    row = layout.row(align=True)

                    row.operator("anim.keyframe_insert_menu", icon= 'KEYFRAMES_INSERT',text="")
                    row.operator("anim.keyframe_delete_v3d", icon= 'KEYFRAMES_REMOVE',text="")
                    row.operator("nla.bake", icon= 'BAKE_ACTION',text="")
                    row.operator("anim.keyframe_clear_v3d", icon= 'KEYFRAMES_CLEAR',text="")

                    row = layout.row(align=True)

                    row.operator("object.paths_calculate", icon ='MOTIONPATHS_CALCULATE',  text="")
                    row.operator("object.paths_clear", icon ='MOTIONPATHS_CLEAR',  text="")

        if scene.toolbar_animation_range.bool: 

            row = layout.row(align=True)

            row.prop(scene, "use_preview_range", text="", toggle=True)
            row.prop(scene, "lock_frame_selection_to_range", text="", toggle=True)

            row = layout.row(align=True)
            if not scene.use_preview_range:
                row.prop(scene, "frame_start", text="Start")
                row.prop(scene, "frame_end", text="End")
            else:
                row.prop(scene, "frame_preview_start", text="Start")
                row.prop(scene, "frame_preview_end", text="End")

        if scene.toolbar_animation_play.bool: 

            row = layout.row(align=True)

            layout.prop(scene, "frame_current", text="")

            layout.separator()

            row = layout.row(align=True)
            row.operator("screen.frame_jump", text="", icon='REW').end = False
            row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
            if not screen.is_animation_playing:
                # if using JACK and A/V sync:
                #   hide the play-reversed button
                #   since JACK transport doesn't support reversed playback
                if scene.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                    sub = row.row(align=True)
                    sub.scale_x = 2.0
                    sub.operator("screen.animation_play", text="", icon='PLAY')
                else:
                    row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                    row.operator("screen.animation_play", text="", icon='PLAY')
            else:
                sub = row.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PAUSE')
            row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
            row.operator("screen.frame_jump", text="", icon='FF').end = True

        if scene.toolbar_animation_sync.bool: 

            row = layout.row(align=True)

            layout.prop(scene, "sync_mode", text="")

        if scene.toolbar_animation_keyingset.bool: 

            row = layout.row(align=True)

            row.prop(toolsettings, "use_keyframe_insert_auto", text="", toggle=True)
            if toolsettings.use_keyframe_insert_auto:
                row.prop(toolsettings, "use_keyframe_insert_keyingset", text="", toggle=True)

                if screen.is_animation_playing and not userprefs.edit.use_keyframe_insert_available:
                    subsub = row.row(align=True)
                    subsub.prop(toolsettings, "use_record_with_nla", toggle=True)

            row = layout.row(align=True)
            row.prop_search(scene.keying_sets_all, "active", scene, "keying_sets_all", text="")
            row.operator("anim.keyframe_insert", text="", icon='KEY_HLT')
            row.operator("anim.keyframe_delete", text="", icon='KEY_DEHLT')

######################################## Edit ##############################################

#################### Holds the Toolbars menu for Edit, collapsible

class TOOLBAR_MT_menu_edit(Menu):
    bl_idname = "TOOLBAR_MT_menu_edit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        
    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_edit_menu") # see class below

##################### Tools toolbars menu

class TOOLBAR_MT_toolbars_edit_menu(Menu):
    bl_label = "Toolbars Edit"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_edit_edit, "bool")
        layout.prop(scene.toolbar_edit_weight, "bool")
            
############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_edit(Menu):
    bl_idname = "TOOLBAR_MT_edit"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        obj = context.object

        TOOLBAR_MT_menu_edit.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_edit_edit.bool: 

            if obj is not None:

                mode = obj.mode

                if mode == 'EDIT':

                    row = layout.row(align=True)

                    row.operator("mesh.dissolve_verts", icon='DISSOLVE_VERTS', text="")
                    row.operator("mesh.dissolve_edges", icon='DISSOLVE_EDGES', text="")
                    row.operator("mesh.dissolve_faces", icon='DISSOLVE_FACES', text="")
                    row.operator("mesh.dissolve_limited", icon='DISSOLVE_LIMITED', text="")
                    row.operator("mesh.dissolve_mode", icon='DISSOLVE_SELECTION', text="")
                    row.operator("mesh.edge_collapse", icon='EDGE_COLLAPSE', text="")

                    row = layout.row(align=True)

                    row.operator("mesh.remove_doubles", icon='REMOVE_DOUBLES', text="")

                    row = layout.row(align=True)

                    row.operator_menu_enum("mesh.merge", "type")
                    row.operator_menu_enum("mesh.separate", "type")

        if scene.toolbar_edit_weight.bool:

            if obj is not None:

                mode = obj.mode

                if mode in ( 'EDIT', 'WEIGHT_PAINT'):

                    row = layout.row(align=True)

                    row.operator("object.vertex_group_normalize_all", icon='WEIGHT_NORMALIZE_ALL', text="")
                    row.operator("object.vertex_group_normalize",icon='WEIGHT_NORMALIZE', text="")
                    row.operator("object.vertex_group_mirror",icon='WEIGHT_MIRROR', text="")
                    row.operator("object.vertex_group_invert", icon='WEIGHT_INVERT',text="")
                    row.operator("object.vertex_group_clean", icon='WEIGHT_CLEAN',text="")
                    row.operator("object.vertex_group_quantize", icon='WEIGHT_QUANTIZE',text="")
                    row.operator("object.vertex_group_levels", icon='WEIGHT_LEVELS',text="")
                    row.operator("object.vertex_group_smooth", icon='WEIGHT_SMOOTH',text="")
                    row.operator("object.vertex_group_limit_total", icon='WEIGHT_LIMIT_TOTAL',text="")
                    row.operator("object.vertex_group_fix", icon='WEIGHT_FIX_DEFORMS',text="")

######################################## Misc ##############################################

#################### Holds the Toolbars menu for Misc, collapsible

class TOOLBAR_MT_menu_misc(Menu):
    bl_idname = "TOOLBAR_MT_menu_misc"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_toolbars_misc_menu") # see class below

##################### Tools toolbars menu

class TOOLBAR_MT_toolbars_misc_menu(Menu):
    bl_label = "Toolbars Misc"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_misc_misc, "bool")
            
############### bfa - menu hidable by the flag in the right click menu

class TOOLBAR_MT_misc(Menu):
    bl_idname = "TOOLBAR_MT_misc"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene

        TOOLBAR_MT_menu_misc.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_misc_misc.bool: 

            row = layout.row(align=True)

            row.label(text=" - Misc Toolbar - ")

# -------------------- Register -------------------------------------------------------------------

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
