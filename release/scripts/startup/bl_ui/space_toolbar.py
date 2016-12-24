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

        TOOLBAR_MT_loadsave.hide_loadsave(context, layout) # bfa - show hide the complete load save toolbar container

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

        layout.menu("TOOLBAR_MT_type") #see below

################## Toolbar Type menu

class TOOLBAR_MT_type(Menu):
    bl_label = "Type"

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view)

    def draw(self, context):
        layout = self.layout

        screen = context.screen

        #rd = context.scene.render
        #layout.prop(rd, "use_stamp") # This one works. Why not the prop in the screen?

        layout.operator("screen.header_toolbar_loadsave") 

        # layout.prop(screen,"header_toggle_menus") # why does this not work?


######################################## Toolbars ##############################################


######################################## LoadSave ##############################################


#################### Holds the Toolbars menu for Load Save, collapsible

class TOOLBAR_MT_menu_loadsave(Menu):
    bl_idname = "TOOLBAR_MT_menu_loadsave"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)
        

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        rd = scene.render

        layout.menu("TOOLBAR_MT_file") # see class TOOLBAR_MT_file below


##################### Load Save sub toolbars menu

class TOOLBAR_MT_file(Menu):
    bl_label = "Toolbars File"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.toolbar_loadsave, "loadsave_bool") # Our checkbox

        layout.prop(scene.toolbar_linkappend, "linkappend_bool") # Our checkbox

        layout.prop(scene.toolbar_importcommon, "importcommon_bool") # Our checkbox
        layout.prop(scene.toolbar_importuncommon, "importuncommon_bool") # Our checkbox
        layout.prop(scene.toolbar_exportcommon, "exportcommon_bool") # Our checkbox
        layout.prop(scene.toolbar_exportuncommon, "exportuncommon_bool") # Our checkbox
        
            
############### bfa - Load Save menu hidable by the flag in the right click menu

class TOOLBAR_MT_loadsave(Menu):
    bl_idname = "TOOLBAR_MT_loadsave"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)     

    @staticmethod
    def draw_menus(layout, context):
        scene = context.scene
        #rd = scene.render

        TOOLBAR_MT_menu_loadsave.draw_collapsible(context, layout)

        ## ------------------ Load / Save sub toolbars

        if scene.toolbar_loadsave.loadsave_bool: 

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

        if scene.toolbar_linkappend.linkappend_bool: 

            row = layout.row(align=True)

            row.operator("wm.link", text="", icon='LINK_BLEND')
            row.operator("wm.append", text="", icon='APPEND_BLEND')

        ## ------------------ Import common

        if scene.toolbar_importcommon.importcommon_bool:

            row = layout.row(align=True)

            row.operator("import_scene.fbx", text="", icon='LOAD_FBX')
            row.operator("import_scene.obj", text="", icon='LOAD_OBJ')
            row.operator("wm.collada_import", text="", icon='LOAD_DAE')
            row.operator("import_anim.bvh", text="", icon='LOAD_BVH')
            row.operator("import_scene.autodesk_3ds", text="", icon='LOAD_3DS')

        ## ------------------ Import uncommon

        if scene.toolbar_importuncommon.importuncommon_bool:

            row = layout.row(align=True)

            row.operator("import_mesh.stl", text="", icon='LOAD_STL')
            row.operator("import_mesh.ply", text="", icon='LOAD_PLY')
            row.operator("import_scene.x3d", text="", icon='LOAD_WRL')
            row.operator("import_curve.svg", text="", icon='LOAD_SVG')
            
        ## ------------------ Export common

        if scene.toolbar_exportcommon.exportcommon_bool:

            row = layout.row(align=True)

            row.operator("export_scene.fbx", text="", icon='SAVE_FBX')
            row.operator("export_scene.obj", text="", icon='SAVE_OBJ')
            row.operator("wm.collada_export", text="", icon='SAVE_DAE')
            row.operator("export_anim.bvh", text="", icon='SAVE_BVH')
            row.operator("export_scene.autodesk_3ds", text="", icon='SAVE_3DS')

        ## ------------------ Export uncommon

        if scene.toolbar_exportuncommon.exportuncommon_bool:

            row = layout.row(align=True)

            row.operator("export_mesh.stl", text="", icon='SAVE_STL')
            row.operator("export_mesh.ply", text="", icon='SAVE_PLY')
            row.operator("export_scene.x3d", text="", icon='SAVE_WRL')      


if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
