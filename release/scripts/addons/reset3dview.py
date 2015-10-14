# Big Thanks for the help with the code goes to pink vertex and CoDEmanX at the Blenderartists forum, and to Tobain at the german Blendpolis forum
# This script is under apache license

bl_info = {
    "name": "Reset 3D View",
    "description": "Resets the views of all 3D windows to standard view",
    "author": "Reiner 'Tiles' Prokein",
    "version": (1, 0, 2),
    "blender": (2, 69, 0),
    "location": "View3D > View",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Reset_3D_View",
    "category": "View"}


import bpy
import mathutils

class Reset3dView(bpy.types.Operator):
    """Reset 3D View"""
    bl_idname = "view.reset_3d_view"
    bl_label = "Reset 3D View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        viewmode = "none"
        
        view_matrix = ((0.41, -0.4017, 0.8188, 0.0), # This is the view matrix from Factory settings
               (0.912, 0.1936, -0.3617, 0.0),
               (-0.0133, 0.8959, 0.4458, 0.0),
               (0.0, 0.0, -14.9892, 1.0))
               
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                rv3d = area.spaces[0].region_3d
                if rv3d is not None:
                    # --------------------------- check for views -----------------------------------------------------------
                    # We check if the view is in top, left, etc. by comparing the quaternion of the region3d.view_rotation                    
                    viewrot = area.spaces[0].region_3d.view_rotation*10000000

                    vlist = [

                        ( (10000000.0000,-0.0000,-0.0000,-0.0000), "TOP" ),
                        ( (7071067.5000, 7071067.5000, -0.0000,-0.0000), "FRONT" ),
                        ( (5000000.0000, 5000000.0000, 5000000.0000, 5000000.0000), "RIGHT" ),
                        ( (0.0000, 10000000.0000,-0.0000,-0.0000), "BOTTOM" ),
                        ( (0.0000,-0.0000, 7071067.5000, 7071067.5000), "BACK" ),
                        ( (5000000.0000, 5000000.0000,-5000000.0000,-5000000.0000), "LEFT" ),
                    ]

                    for v, vm in vlist:
                        if viewrot == mathutils.Quaternion(v):
                            viewmode = vm
                                
                    #------------------------------set the views -----------------------------------------------------------
                    # When it is top, front etc. then just the distance gets resettet The rotation already fits.
                    if viewmode == "TOP":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                    if viewmode == "FRONT":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                    if viewmode == "RIGHT":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                    if viewmode == "BOTTOM":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                    if viewmode == "BACK":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                    if viewmode == "LEFT":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                    if viewmode == "none":
                        rv3d.view_distance = 15 # This is the original distance to the zero point from Factory settings.
                        rv3d.view_matrix = view_matrix # This resets the location and rotation back to the initial view matrix values
                        
                    # ----------- final bit, reset the viewmode variable for the next try
                    viewmode = "none"

        return {'FINISHED'}
    
def menu_func(self, context):
    self.layout.operator(Reset3dView.bl_idname)
    
# store keymaps here to access after registration
addon_keymaps = []
   

def register():
    bpy.utils.register_class(Reset3dView)
    bpy.types.VIEW3D_MT_view.append(menu_func)
    
    # handle the keymap
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(Reset3dView.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', ctrl=False, shift=False)
    addon_keymaps.append((km))

def unregister():
    bpy.utils.unregister_class(Reset3dView)
    bpy.types.VIEW3D_MT_view.remove(menu_func)
    
    # handle the keymap
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    # clear the list
    del addon_keymaps[:]


if __name__ == "__main__":
    register()
            
            
            