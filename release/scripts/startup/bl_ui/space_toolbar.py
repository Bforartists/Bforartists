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

        TOOLBAR_MT_file.hide_file_toolbar(context, layout) # bfa - show hide the complete file toolbar container
        TOOLBAR_MT_view.hide_view_toolbar(context, layout) # bfa - show hide the complete view toolbar container
        TOOLBAR_MT_primitives.hide_primitives_toolbar(context, layout) # bfa - show hide the complete primitives toolbar container

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

# Everything menu in this class is collapsible. See line 35.
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

class TOOLBAR_MT_menu_loadsave(Menu):
    bl_idname = "TOOLBAR_MT_menu_loadsave"
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
        layout.prop(scene.toolbar_file_loadsave, "bool") # Our checkbox

        layout.prop(scene.toolbar_file_linkappend, "bool") # Our checkbox

        layout.prop(scene.toolbar_file_importcommon, "bool") # Our checkbox
        layout.prop(scene.toolbar_file_importuncommon, "bool") # Our checkbox
        layout.prop(scene.toolbar_file_exportcommon, "bool") # Our checkbox
        layout.prop(scene.toolbar_file_exportuncommon, "bool") # Our checkbox
        layout.prop(scene.toolbar_file_render, "bool") # Our checkbox  
        layout.prop(scene.toolbar_file_render_view, "bool") # Our checkbox  
        layout.prop(scene.toolbar_file_render_misc, "bool") # Our checkbox  
            
############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_file(Menu):
    bl_idname = "TOOLBAR_MT_file"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        #rd = scene.render

        TOOLBAR_MT_menu_loadsave.draw_collapsible(context, layout)

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
        layout.prop(scene.toolbar_view_align, "bool") # Our checkbox
        layout.prop(scene.toolbar_view_camera, "bool") # Our checkbox


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
        layout.prop(scene.toolbar_primitives_mesh, "bool") # Our checkbox

            
############### bfa - Load Save menu hidable by the flag in the right click menu

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

        ## ------------------ primitives sub toolbars

        if scene.toolbar_primitives_mesh.bool: 

            row = layout.row(align=True)

            row.operator("wm.save_mainfile", text="", icon='FILE_TICK') # placeholder


if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
