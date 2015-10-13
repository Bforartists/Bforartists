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

bl_info = {
    "name": "Class Viewer",
    "author": "Mackraken", "batFinger"
    "version": (0, 1, 2),
    "blender": (2, 58, 0),
    "location": "Text Editor > Toolbar, Text Editor > Right Click",
    "warning": "",
    "description": "List classes and definitions of a text block",
    "wiki_url": "https://sites.google.com/site/aleonserra/home/scripts/class-viewer",
    "tracker_url": "https://developer.blender.org/T29463",
    "category": "Development"}

import bpy

#lists all defs, comment or classes
#space = current text editor
#sort = sort result
#tipo = kind of struct to look for
#escape = character right next to the class or def name 

def getfunc(space, sort, tipo="def ", escape= ""):
    defs = []
    if space.type=="TEXT_EDITOR":
        if space.text!=None:
            txt = space.text
            
            for i, l in enumerate(txt.lines):
                try:
                    line = l.body
                except:
                    line=""
                
                if line[0:len(tipo)]==tipo:
                    end = line.find(escape)
                    if end==0:
                        func = line[len(tipo)::]
                    else:
                        func = line[len(tipo):end]
                    defs.append([func, i+1])
            
            if sort: defs.sort()
    
    return defs

class TEXT_OT_Jumptoline(bpy.types.Operator):
    bl_label = "Jump"
    bl_idname = "text.jumptoline"
    __doc__ = "Jump to line"
    line = bpy.props.IntProperty(default=-1)
    
    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].type!="TEXT_EDITOR":
            return False
        else: 
            return context.area.spaces[0].text!=None
    
    def execute(self, context):
        
        scn = context.scene

        if self.line!=-1:
            bpy.ops.text.jump(line=self.line)

        return {'FINISHED'}



class CommentsMenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_select_comments"
    bl_label = "Select"
    
    
    
    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].type!="TEXT_EDITOR":
            return False
        else: 
            return context.area.spaces[0].text!=None
        
    def draw(self, context):
    
        layout = self.layout
        space = context.area.spaces[0]
        
        items = getfunc(space, 1, "### ", "")
        
        for it in items:
            layout.operator("text.jumptoline",text=it[0]).line = it[1]

class DefsMenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_select_defs"
    bl_label = "Select"
    
    tipo = bpy.props.BoolProperty(default=False)
    
    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].type!="TEXT_EDITOR":
            return False
        else: 
            return context.area.spaces[0].text!=None
        
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        space = context.area.spaces[0]
        tipo = self.tipo
        
        
        items = getfunc(space, 1, "def ", "(")
        
        for it in items:
            layout.operator("text.jumptoline",text=it[0]).line = it[1]
                
class ClassesMenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_select_classes"
    bl_label = "Select"
    
    
    
    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].type!="TEXT_EDITOR":
            return False
        else: 
            return context.area.spaces[0].text!=None
        
    def draw(self, context):
    
        layout = self.layout
        space = context.area.spaces[0]
    
        
        
        items = getfunc(space, 1, "class ", "(")
        
        for it in items:
            layout.operator("text.jumptoline",text=it[0]).line = it[1]


            
def GotoComments(self, context): 
    self.layout.menu("OBJECT_MT_select_comments", text="Comments", icon='PLUGIN')
    return False

def GotoDefs(self, context): 
    self.layout.menu("OBJECT_MT_select_defs", text="Defs", icon='PLUGIN')
    return False

def GotoClasses(self, context): 
    self.layout.menu("OBJECT_MT_select_classes", text="Classes", icon='PLUGIN')
    return False


classes = [TEXT_OT_Jumptoline, ClassesMenu, DefsMenu, CommentsMenu]


def register():
    for c in classes:
        bpy.utils.register_class(c)
        
    bpy.types.TEXT_MT_toolbox.append(GotoComments)
    bpy.types.TEXT_MT_toolbox.append(GotoDefs)
    bpy.types.TEXT_MT_toolbox.append(GotoClasses)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
        
        bpy.types.TEXT_MT_toolbox.remove(GotoComments)
    bpy.types.TEXT_MT_toolbox.remove(GotoDefs)
    bpy.types.TEXT_MT_toolbox.remove(GotoClasses)
    
if __name__ == "__main__":
    register()
