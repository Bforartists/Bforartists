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

# This script enables a selection method by moving the mouse over the element you want to select.
# Thanks for help with updating the checkbox when using hotkeys goes to the Blender Stack Exchange.

# The core of this script is based on paint select by Kjartan and minikuof


import bpy
from bpy.props import BoolProperty

bl_info = {
    'name'        : "Stroke Select",
    'author'      : "Reiner 'Tiles' Prokein",
    'description' : "Stroke Select - Enables selection by mouse strokes",
    'category'    : "Mesh",
    'blender'     : (2, 76),
    'version'     : (1, 0, 3),
    'wiki_url'    : 'http://www.reinerstilesets.de',
}

# ----------------------------------------------------------------------------------------------------
# Updating the UI when switching the select / deselect flag by hotkey.
# ----------------------------------------------------------------------------------------------------

def area_ui_update(type):
    ''' tag redraw on areas of type '''

    def ui_update(self, context):
        # This part is not necessary it seems
#        areas = [a for a in screen.areas if a.type == type]
#        for a in areas:
#            area.tag_redraw()
        return None
    return ui_update

# ----------------------------------------------------------------------------------------------------
# The core class for the stroke select. See outcommented part at the end of the script for more switches. 
# But for our needs it's enough to have the deselect, extend and toggle flag.
# And to work with the tool it's enough to have access to the deselect flag.
# ----------------------------------------------------------------------------------------------------

class StrokeSelect(bpy.types.Operator):
    """Stroke select\nHold down hotkey, stroke select with left mouse button
To toggle between select and deselect hold down hotkey and right click"""
    bl_idname = "view3d.stroke_select"
    bl_label = "Stroke Select"
    bl_options = {'REGISTER', 'UNDO'}
    
    deselect = BoolProperty(name="Deselect", default=False)
    #extend = BoolProperty(name="Extend", default=False)

    def modal(self, context, event):
        
        wm = context.window_manager # Our bool is in the windows_manager
        
        if wm.stroke_select_bool:
            bpy.ops.view3d.select('INVOKE_DEFAULT', extend=False, deselect=True, toggle=True)
        else:
            bpy.ops.view3d.select('INVOKE_DEFAULT', extend=True, deselect=False)

        if event.value == 'RELEASE':
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
 # -----------------------------------------------------------------------------------------------------
 # the panel in the properties sidebar. Visual feedback in what state the deselect bool currently is    
 # -----------------------------------------------------------------------------------------------------
 
class VIEW3D_PT_StrokeSelectPanel(bpy.types.Panel):
    bl_label = "Stroke Select"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    # Just show when there is an object in the scene
    @classmethod
    def poll(self,context):
        return context.object is not None

    # now draw the panel and the checkbox
    def draw(self, context):
        layout = self.layout
        
        wm = context.window_manager # Our bool is in the windows_manager
        layout.prop(wm, "stroke_select_bool") # Our checkbox
 
# The menu entry in the Select menu. The operator. See also def register for the location
def menu_func(self, context):
    self.layout.operator("view3d.stroke_select", icon = "STROKE_SELECT")
    

# ------------------------------ register unregister --------------------------------------------------------  

def register():
    # Our bool. The checkbox. Note the update=area_UI_update part in the bool. This is updating the display when the bool gets toggled by hotkey.
    bpy.types.WindowManager.stroke_select_bool = bpy.props.BoolProperty( 
    name="Deselect", description="Stroke Select/Deselect mode\nCheck it to deselect\nYou can also click with right mouse button to toggle", default = False, update=area_ui_update('VIEW_3D')) 
    bpy.utils.register_module(__name__)
    
    # The menu entry in the Select menu. The locations.
    bpy.types.VIEW3D_MT_select_object.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_edit_mesh.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_edit_curve.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_edit_surface.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_edit_lattice.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_edit_armature.prepend(menu_func)
    bpy.types.VIEW3D_MT_select_pose.prepend(menu_func)
    
               
def unregister():
    del bpy.types.WindowManager.stroke_select_bool # Unregister our flag when unregister.
    bpy.utils.unregister_module(__name__)

    bpy.types.VIEW3D_MT_select_object.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_curve.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_surface.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_lattice.remove(menu_func)
    bpy.types.VIEW3D_MT_select_edit_armature.remove(menu_func)
    bpy.types.VIEW3D_MT_select_pose.remove(menu_func)
        
if __name__ == "__main__":
    register()

# Possible parameters for select. In case somebody wants to extend the script later:

 #bpy.ops.view3d.select(extend=False, deselect=False, toggle=False, center=False, enumerate=False, object=False)

 #   Activate/select item(s)
 #   Parameters:	

 #       extend (boolean, (optional)) – Extend, Extend selection instead of deselecting everything first
 #       deselect (boolean, (optional)) – Deselect, Remove from selection
 #       toggle (boolean, (optional)) – Toggle Selection, Toggle the selection
 #       center (boolean, (optional)) – Center, Use the object center when selecting, in editmode used to extend object selection
 #       enumerate (boolean, (optional)) – Enumerate, List objects under the mouse (object mode only)
 #       object (boolean, (optional)) – Object, Use object selection (editmode only)
