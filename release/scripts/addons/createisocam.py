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
    "version": (1, 0, 1),
    "blender": (2, 69, 0),
    "location": "Toolshelf",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://www.reinerstilesets.de/de/anderes/blender-addons/create-isocam/",
    "category": "Create"}


import bpy

# ----------------------------------------- true isometric camera
class createtrueisocam(bpy.types.Operator):
    """Creates a camera for mathematical correct isometric view"""
    bl_idname = "scene.create_trueisocam"
    bl_label = "TrueIsocam"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        # ----------------------------Create Camera with correct position and rotation
        bpy.ops.object.camera_add(location=(30.60861, -30.60861, 30.60861)) # Create Camera. I would love to set the rotation here too. Blender not. Not that there are no tutorials around which shows that it should work ... . 

        #So that's what the next two lines are good for. Setting the rotation of the camera ...

        object = bpy.context.scene.objects.active
        object.rotation_euler = (0.955324, 0, 0.785398) #Attention, these are radians. Euler angles are (54.736,0,45) Here we set the rotation for a mathematical correct isometric view. Not to mix with the Isoview for a 2D game!

        # ------------------------------Here we adjust some settings ---------------------------------
        object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
        object.data.ortho_scale = 14.123 # Let's fit the camera to a basetile in size of 10
        object.name = "TrueIsoCam" # let's rename the cam so that it cannot be confused with other cameras.
        bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through

        return {'FINISHED'}
# ----------------------------------------- Game isometric camera
class creategameisocam(bpy.types.Operator):
    """Creates a camera with isometric view for game needs"""
    bl_idname = "scene.create_gameisocam"
    bl_label = "GameIsocam"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        # ----------------------------Create Camera with correct position and rotation
        bpy.ops.object.camera_add(location=(30.60861, -30.60861, 25.00000)) # Create Camera. I would love to set the rotation here too. Blender not. Not that there are no tutorials around which shows that it should work ... . 

        #So that's what the next two lines are good for. Setting the rotation of the camera ...

        object = bpy.context.scene.objects.active
        object.rotation_euler = (1.047198, 0, 0.785398)#Attention, these are radians. Euler angles are (60,0,45) Here we set the rotation for a isometric view that is used in 2D games. Not to mix with the mathematical correct Isoview!

        # ------------------------------Here we adjust some settings ---------------------------------
        object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
        object.data.ortho_scale = 14.123  # Let's fit the camera to our basetile in size of 10
        object.name = "GameIsoCam" # let's rename the cam so that it cannot be confused with other cameras.
        bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through


        return {'FINISHED'} 

# ----------------------------------------- Game isometric camera 4 to 3
# This format is not so common. But is also used here and there. It is more topdown. With a basetile of 64 to 48 pixels

class creategameisocam4to3(bpy.types.Operator):
    """Creates a camera with a special 4:3 iso view for game needs"""
    bl_idname = "scene.create_gameisocam4to3"
    bl_label = "GameIsocam4to3"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        # ----------------------------Create Camera with correct position and rotation
        bpy.ops.object.camera_add(location=(23.42714, -23.42714, 37.4478)) # Create Camera. I would love to set the rotation here too. Blender not. Not that there are no tutorials around which shows that it should work ... . 

        #So that's what the next two lines are good for. Setting the rotation of the camera ...

        object = bpy.context.scene.objects.active
        object.rotation_euler = (0.724312, 0, 0.785398)#Attention, these are radians. Euler angles are (41.5,0,45) Here we set the rotation for a isometric view that is used in 2D games. Not to mix with the mathematical correct Isoview!

        # ------------------------------Here we adjust some settings ---------------------------------
        object.data.type = 'ORTHO' # We want Iso, so set the type of the camera to orthographic
        object.data.ortho_scale = 14.123  # Let's fit the camera to our basetile in size of 10
        object.name = "GameIso4to3Cam" # let's rename the cam so that it cannot be confused with other cameras.
        bpy.ops.view3d.object_as_camera() # Set the current camera as the active one to look through


        return {'FINISHED'} 
    
# ----------------------------------------- Create a ground plane

class creategroundplane(bpy.types.Operator):
    """Creates a groundplane in size of ten where you can put your things on"""
    bl_idname = "scene.create_groundplane"
    bl_label = "Groundplane"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0)) # Create Camera. I would love to set the scale here too. Blender not. So let's do it in an extra step 

        object = bpy.context.scene.objects.active
        object.scale = (5, 5, 0)#The plane object is created with a size of 2. Scaling it to 10 means to scale it by factor 5
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)# apply scale

        return {'FINISHED'}   
    
#----------------------------------------- Create panel in the toolshelf -------------------------------------------------

class Createisocampanel(bpy.types.Panel):
    bl_label = "Create IsoCam"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Create"

    def draw(self, context):
        
        # column buttons solution. Less space than single buttons ...
        layout = self.layout
        view = context.space_data
        # Three buttons
        col = layout.column(align=True)
        col.operator("scene.create_trueisocam", text="TrueIsocam")
        col.operator("scene.create_gameisocam", text="GameIsocam")
        col.operator("scene.create_gameisocam4to3", text="GameIso4to3cam") 
        col.operator("scene.create_groundplane", text="Groundplane")
# -------------------------------------------------------------------------------------------

# store keymaps here to access after registration
addon_keymaps = []
   

def register():
    bpy.utils.register_class(createtrueisocam)
    bpy.utils.register_class(creategameisocam)
    bpy.utils.register_class(creategameisocam4to3)
    bpy.utils.register_class(creategroundplane)
    bpy.utils.register_class(Createisocampanel)

	    # handle the keymap
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    kmi = km.keymap_items.new(createtrueisocam.bl_idname, 'ONE', 'PRESS', ctrl=True, shift=True, alt=True)
    kmi = km.keymap_items.new(creategameisocam.bl_idname, 'TWO', 'PRESS', ctrl=True, shift=True, alt=True)
    kmi = km.keymap_items.new(creategameisocam4to3.bl_idname, 'THREE', 'PRESS', ctrl=True, shift=True, alt=True)
    kmi = km.keymap_items.new(creategroundplane.bl_idname, 'FOUR', 'PRESS', ctrl=True, shift=True, alt=True)

    addon_keymaps.append(km)

def unregister():
    bpy.utils.unregister_class(createtrueisocam)
    bpy.utils.unregister_class(creategameisocam)
    bpy.utils.unregister_class(creategameisocam4to3)
    bpy.utils.unregister_class(creategroundplane)
    bpy.utils.unregister_class(Createisocampanel)

	    # handle the keymap
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    # clear the list
    del addon_keymaps[:]


if __name__ == "__main__":
    register()
            
            
            