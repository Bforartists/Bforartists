# The script is under Apache license

# Big thanks to the helpful souls at Blendpolis.
# Also big thanks to aeon for his studio setup tips.
# Credits for Studio Diffuse White and Studio Diffuse White Rim goes to Tilation.
# Both members of the german 3D community 3D Ring.

import bpy
import os

from bpy.props import StringProperty

bl_info = {
    "name": "Minilightlib",
    "description": "A mini library addon with predefined light setups",
    "author": "Reiner 'Tiles' Prokein",
    "version": (0,6,0),
    "blender": (2, 76, 0),
    "location": "Tool Shelf > Create > Mini Lightlib",
    "warning": "", 
    "wiki_url": "http://www.reinerstilesets.de/anderes/blender-addons/mini-lightlib/",
    "category": "Create"}

 # -----------------------------------------------------------------------------------------------------
 # the Minilib panel is in the Tool Shelf in the Create tab
 # -----------------------------------------------------------------------------------------------------
 
mylist = [] # the list to retreive the files in the target folder
my_listing = [] # the list to create the dropdown box.

############################# Read Asset

class VIEW3D_mini_lightlib_read_asset(bpy.types.Operator):
    """Append the currently selected asset""" 
    bl_idname = "view3d.read_asset" 
    bl_label = "View Selected All Regions"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context): 

        scn = bpy.context.scene # current scene    
        filepath = scn.path + "/" + str(mylist[int(context.scene.MyEnum)] + ".blend") # path to the blend       
        link = False # append, set to true to keep the link to the original file. There is no append item.      
        
        #append all objects from .blend file
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            data_to.objects = data_from.objects
                        
         # When you want to load just specific object types
#        obj_name = "Cube" # name of object(s) in the lib file to append or link   
#        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
#            data_to.objects = [name for name in data_from.objects if name.startswith(obj_name)]

        #link object to current scene
        for obj in data_to.objects:
            if obj is not None:
               scn.objects.link(obj)
               obj.select = False # We don't want to have the asset selected after loading
        return {'FINISHED'}

############################# read directory

def mini_lightlib_read_dir(path):
    mylist.clear() # clear the list. We don't want double, triple, etc. entries.
    my_listing.clear() # clear the list. We don't want double, triple, etc. entries.
    for path,dirs,files in os.walk(path):
        for filename in files:
            if filename.endswith(".blend"):
                filename = os.path.splitext(filename)[0] # just filename, no extention name
                mylist.append(os.path.join(filename)) # add the files to the mylist list.
        
    # fill the list my_listing
    for n, entry in enumerate(mylist):
        my_listing.append((str(n), entry, entry+".blend"))
    return my_listing

class VIEW3D_Mini_lightlib_read_dir(bpy.types.Operator):
    """Blubb"""
    bl_idname = "view3d.mini_lightlib_read_dir"
    bl_label = "Read Dir"

    def execute(self, context):
        
        mini_lightlib_read_dir(path)
        return {'FINISHED'}
    
#################### Enumerate the dropdown list in the dropdown prop

old_path = ""
old_dir = ""

def item_cb(self, context):
    global old_path, old_dir
    # Check if path is the same
    if bpy.context.scene.path == old_path:
        return old_dir
    #Path has changed or is not set. So read the dir again.
    old_path = bpy.context.scene.path
    old_dir = mini_lightlib_read_dir(bpy.context.scene.path)
    return old_dir
    
########################### the panel #############################

class VIEW3D_PT_Minilightlib(bpy.types.Panel):
    bl_label = "Mini Lightlib"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "TOOLS"
    bl_category = "Create"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.label("Select Asset:")
        layout.prop(scene, "MyEnum", text = "") # Dropdown box
        layout.operator("view3d.read_asset", text="Append Asset") # Load asset
        layout.separator()
        layout.prop(context.scene, "path", text="") # Here you can change the path.

# ------------------------------ register unregister --------------------------------------------------------

def register():
    bpy.types.Scene.path = bpy.props.StringProperty(name="dir_path", description="", default=os.path.dirname(os.path.abspath(__file__))+"/lightlib", maxlen=1024, subtype='DIR_PATH') # Directory loader       
    bpy.types.Scene.MyEnum = bpy.props.EnumProperty(name="Assets", items = item_cb)    # The dropdown box
    
    bpy.utils.register_module(__name__)
    
def unregister():    
    del bpy.types.Scene.MyEnum
    del bpy.types.Scene.path
    
    bpy.utils.unregister_module(__name__)   
        
if __name__ == "__main__":
    register()
