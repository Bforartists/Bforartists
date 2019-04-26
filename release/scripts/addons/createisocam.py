# This script creates two kinds of isometric cameras. 
#The one, TrueIsocam called camera, is the mathematical correct isometric camera with the 54.736 rotation to get the 30 degrees angles at the sides of the rhombus. 
#The other, GameIsocam called camera, is a camera with which you can render isometric tiles for a 2d game. Here we need a 60 degrees angle instedad of the 54.736 one to get a proper stairs effect and a ratio of 2:1
# Then there is the special case with a 4:3 ratio, which is button 3. You can also make 2D games with that one. The view is more topdown though as with a 2:1 ratio of the traditional game iso view.
# The fourth button creates a simple groundplane where you can place your stuff at.

#You can of course set up everything by hand. This script is a convenient solution so that you don't have to setup it again and again.

# The script is under Apache license

# Fixed for Bforartists

bl_info = {
    "name": "Create IsoCam",
    "description": "Creates a true isometric camera or a isometric camera for game needs",
    "author": "Reiner 'Tiles' Prokein",
    "version": (1, 0, 3),
    "blender": (2, 80, 0),
    "location": "3D View - Add menu",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Create"}

import bpy
from bpy.types import Menu

# ----------------------------------------- true isometric camera
class CIC_OT_createtrueisocam(bpy.types.Operator):
    """Creates a camera for mathematical correct isometric view"""
    bl_idname = "scene.cic_create_trueisocam"
    bl_label = "TrueIsocam"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        # ----------------------------Create Camera with correct position and rotation
        bpy.ops.object.camera_add(location=(30.60861, -30.60861, 30.60861), rotation = (0.955324, 0, 0.785398)) # Create Camera.
        #object = bpy.context.scene.objects.active
        object = bpy.context.object # Pick the active object, our new created camera

        # ------------------------------Here we adjust some settings ---------------------------------
        object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
        object.data.ortho_scale = 14.123 # Let's fit the camera to a basetile in size of 10
        object.name = "TrueIsoCam" # let's rename the cam so that it cannot be confused with other cameras.
        bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through

        return {'FINISHED'}
# ----------------------------------------- Game isometric camera
class CIC_OT_creategameisocam(bpy.types.Operator):
    """Creates a camera with isometric view for game needs"""
    bl_idname = "scene.cic_create_gameisocam"
    bl_label = "GameIsocam"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        # ----------------------------Create Camera with correct position and rotation
        bpy.ops.object.camera_add(location=(30.60861, -30.60861, 25.00000), rotation = (1.047198, 0, 0.785398) ) # Create Camera.
        object = bpy.context.object # Pick the active object, our new created camera

        # ------------------------------Here we adjust some settings ---------------------------------
        object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
        object.data.ortho_scale = 14.123  # Let's fit the camera to our basetile in size of 10
        object.name = "GameIsoCam" # let's rename the cam so that it cannot be confused with other cameras.
        bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through


        return {'FINISHED'} 

# ----------------------------------------- Game isometric camera 4 to 3
# This format is not so common. But is also used here and there. It is more topdown. With a basetile of 64 to 48 pixels

class CIC_OT_creategameisocam4to3(bpy.types.Operator):
    """Creates a camera with a special 4:3 iso view for game needs"""
    bl_idname = "scene.cic_create_gameisocam4to3"
    bl_label = "GameIsocam4to3"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        # ----------------------------Create Camera with correct position and rotation
        bpy.ops.object.camera_add(location=(23.42714, -23.42714, 37.4478), rotation = (0.724312, 0, 0.785398)) # Create Camera.

        object = bpy.context.object # Pick the active object, our new created camera

        # ------------------------------Here we adjust some settings ---------------------------------
        object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
        object.data.ortho_scale = 14.123  # Let's fit the camera to our basetile in size of 10
        object.name = "GameIso4to3Cam" # let's rename the cam so that it cannot be confused with other cameras.
        bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through

        return {'FINISHED'} 
    
# ----------------------------------------- Create a ground plane

class CIC_OT_creategroundplane(bpy.types.Operator):
    """Creates a groundplane in size of ten where you can put your things on"""
    bl_idname = "scene.cic_create_groundplane"
    bl_label = "Groundplane"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size = 10, location=(0, 0, 0)) # Create groundplane with size 10

        return {'FINISHED'}   
    
#----------------------------------------- Create panel in the toolshelf -------------------------------------------------

## DEACTIVATED FOR NOW!

# class CIC_MT_createisocampanel(bpy.types.Panel):
#     bl_label = "Create IsoCam"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "TOOLS"
#     bl_category = "Create"

#     def draw(self, context):
        
#         # column buttons solution. Less space than single buttons ...
#         layout = self.layout
#         view = context.space_data
#         # Three buttons
#         col = layout.column(align=True)
#         col.operator("scene.cic_create_trueisocam", text="TrueIsocam")
#         col.operator("scene.cic_create_gameisocam", text="GameIsocam")
#         col.operator("scene.cic_create_gameisocam4to3", text="GameIso4to3cam") 
#         col.operator("scene.cic_create_groundplane", text="Groundplane")

# -------------------------------------------------------------------------------------------

class CIC_MT_createisocammenu(bpy.types.Menu):
    bl_idname = "CIC_MT_createisocammenu"
    bl_label = "Create Isocam"

    def draw(self, context):
        layout = self.layout

        layout.operator("scene.cic_create_trueisocam", text="TrueIsocam", icon = "OUTLINER_OB_CAMERA")
        layout.operator("scene.cic_create_gameisocam", text="GameIsocam", icon = "OUTLINER_OB_CAMERA")
        layout.operator("scene.cic_create_gameisocam4to3", text="GameIso4to3cam", icon = "OUTLINER_OB_CAMERA")
        layout.operator("scene.cic_create_groundplane", text="Groundplane", icon='MESH_PLANE')

classes = (
    CIC_OT_createtrueisocam, 
    CIC_OT_creategameisocam, 
    CIC_OT_creategameisocam4to3, 
    CIC_OT_creategroundplane,
    CIC_MT_createisocammenu,
)

def menu_func(self, context):
    self.layout.menu("CIC_MT_createisocammenu")

## store keymaps here to access after registration
#addon_keymaps = []

def register():
    from bpy.utils import register_class
    for cls in classes:
       register_class(cls)

    bpy.types.VIEW3D_MT_add.append(menu_func)

	   # # handle the keymap
    #wm = bpy.context.window_manager
    #km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    #kmi = km.keymap_items.new(CIC_OT_createtrueisocam.bl_idname, 'ONE', 'PRESS', ctrl=True, shift=True, alt=True)
    #kmi = km.keymap_items.new(CIC_OT_creategameisocam.bl_idname, 'TWO', 'PRESS', ctrl=True, shift=True, alt=True)
    #kmi = km.keymap_items.new(CIC_OT_creategameisocam4to3.bl_idname, 'THREE', 'PRESS', ctrl=True, shift=True, alt=True)
    #kmi = km.keymap_items.new(CIC_OT_creategroundplane.bl_idname, 'FOUR', 'PRESS', ctrl=True, shift=True, alt=True)

    #addon_keymaps.append(km)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
       unregister_class(cls)

    bpy.types.VIEW3D_MT_add.remove(menu_func)

	   # # handle the keymap
    #wm = bpy.context.window_manager
    #for km in addon_keymaps:
    #    wm.keyconfigs.addon.keymaps.remove(km)
    ## clear the list
    #del addon_keymaps[:]

            
