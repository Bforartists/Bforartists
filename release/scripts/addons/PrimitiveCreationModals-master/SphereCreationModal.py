bl_info = {
    "name": "Add Sphere modal",
    "author": "CC",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "View3D",
    "description": "Adds a new Mesh Object",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
    }

import bpy
import bmesh
import mathutils
import math
from bpy.props import IntProperty, FloatProperty, FloatVectorProperty, IntVectorProperty, BoolVectorProperty
from bpy_extras import view3d_utils
from math import degrees
from mathutils import Matrix
from mathutils import Vector
from .primitive_Circle import UpdateCircle
from .primitive_Sphere import UpdateSphere

from .gen_func import RayCastForScene, getUnitScale, PointOnGrid, CastToPlaneFromCamera, updateHeaderText
from .View_3d_HUD import draw_callback_px

def AddObject(self, context):
    #State 1 and 0 should be the same 
    if self.state == 0 or self.state == 1 :
        bpy.ops.mesh.add_primcircle(location=self.loc, rotation=self.rot, scale=self.scale, center=self.center, seg=self.seg)
    #State 2 should be state 1 plus it's Z Axis i.e. state 1 = plane, state 2 = box
    if self.state == 2:
        bpy.ops.mesh.add_primsphere(location=self.loc, rotation=self.rot, scale=self.scale, center=self.center, seg=self.seg)

     #Has the possibility to be extended for extra functionality. i.e. if you wanted to make a cone you could extend the cylinder with an extra state to drag for the top of the cones size.

    #If the state is larger than max number of clicks use this mesh (should be the same as the one for the last click) (!this ensures that the redo panel uses the right mesh!)
    if self.state > self.max_states:
        bpy.ops.mesh.add_primsphere(location=self.loc, rotation=self.rot, scale=self.scale, center=self.center, seg=self.seg)



def UndoRedoObject(self, context):
    
    if self.mode == 'EDIT':
        #Apparently the operator memory is dumped in edit mode so doing this in edit mode isn't very intensive
        bpy.ops.mesh.delete(type='VERT')
        AddObject(self, context)
    else:
        #Turn on wire frame so you can see the subdivisions in the mesh.
        if self.wire:
            if bpy.context.scene.objects.active.show_wire != self.wire:
                bpy.context.scene.objects.active.show_wire = self.wire
                bpy.context.scene.objects.active.show_all_edges = self.wire
        
        #use the primitive updates in object mode as a more memory efficient method.
        if self.state == 0 or self.state == 1:
            UpdateCircle(cont=context, scale=self.scale, center=self.center, seg=self.seg)
        if self.state == 2:
            UpdateSphere(cont=context, scale=self.scale, center=self.center, seg=self.seg)
            

def ResetObjectParams(self, context):
    if self.wire:
        if not self.mode == 'EDIT':
            bpy.context.scene.objects.active.show_wire = False
            bpy.context.scene.objects.active.show_all_edges = False
            self.wire = False

    


class SphereCreationModalOperator(bpy.types.Operator):
    bl_idname = "object.sphere_creation_modal_operator"
    bl_label = "Sphere Creation Modal"
    bl_description = "Sphere Modal- \nAllows Sphere creation by dragging\nClick once to place the object, Click a second time to set the radius, Click again to confirm the height."
    bl_options = {'REGISTER', 'GRAB_CURSOR', 'BLOCKING', 'UNDO'}
    
    #init Vars
    state = 0
    max_states = 2
    mode = "OBJECT"
    loc = (0, 0, 0)
    rot = (0, 0, 0)
    norm = (0, 0, 0)
    even = True
    flip = False
    xAxis = (0, 0, 0)
    yAxis = (0, 0, 0)
    first_mouse_y = 0
    wire = False
    boxDrawMode = 'GRID'
    snapInc = 1
    temp_ZScale = 0
    bm = None
    
    
    type = IntProperty(
            name="State",
            default=0,
            description="The current object state\nState 1 is a 2d state\nState 2 is state 1 with the addition of the Z dimension",
            min=1,
            max=max_states
            )
    
    scale = FloatVectorProperty(
            name="Scale",
            default=(1.0, 1.0, 1.0),
            subtype='TRANSLATION',
            description="Scaling",
            )
            
    seg = IntVectorProperty(
            name="Segments",
            default=(32.0, 16.0, 0.0),
            min=0,
            subtype='TRANSLATION',
            description="Segments\nX Segments are the segments around the outer edge\nY Segments are the segments up the outside also known as rings on the uv sphere\nZ Segments is an unused field and has no impact",
            )
            
    center = BoolVectorProperty(
                name="Centered",
                default=(True, True, True),
                description="Toggles for centering the mesh on the X,Y,Z axis"
                )
    
    def modal(self, context, event):
        #Make it redraw the hud.
        context.area.tag_redraw()
        
        updateHeaderText(context, self, event)
        
        #Set type to state so that in the redo panel the state is correct after creating the mesh.
        self.type = self.state
        
        #
        #
        #
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            #Allow navigation to pass though so you can reposition
            if self.state == 0:
                return {'PASS_THROUGH'}
            
            #Increase or decrease, segments for the first state or grid snap increments.
            if self.state == 1:
                if event.type == 'WHEELUPMOUSE':
                    if not event.ctrl:
                        self.seg[0] += 1
                    else:
                        if self.snapInc < 1:
                            self.snapInc += 0.25
                        else:
                            self.snapInc += 1
                
                if event.type == 'WHEELDOWNMOUSE':    
                    if not event.ctrl:
                        self.seg[0] -= 1
                        self.seg[0] = max(self.seg[0], 3)
                    else:
                        if self.snapInc <= 1:
                            self.snapInc -= 0.25
                        else:
                            self.snapInc -= 1
                        self.snapInc = max(self.snapInc, 0.25)
                
                if self.seg[0] > 3 or self.seg[1] > 3:
                    if not self.mode == 'EDIT':
                        self.wire = True

                UndoRedoObject(self, context)
            
            #Increase or decrease, segments for the second state or grid snap increments.      
            if self.state == 2:
                if event.type == 'WHEELUPMOUSE':
                    if not event.ctrl:
                        self.seg[1] += 1
                        
                    else:
                        if self.snapInc < 1:
                            self.snapInc += 0.25
                        else:
                            self.snapInc += 1
                
                if event.type == 'WHEELDOWNMOUSE':    
                    if not event.ctrl:
                        self.seg[1] -= 1
                        self.seg[1] = max(self.seg[1], 3)
                    else:
                        if self.snapInc <= 1:
                            self.snapInc -= 0.25
                        else:
                            self.snapInc -= 1
                        self.snapInc = max(self.snapInc, 0.25)
                
                UndoRedoObject(self, context)
                
                if self.seg[1] > 3:
                    if not self.mode == 'EDIT':
                        self.wire = True
                        
        #
        #
        #
        #Do Key Toggles
        if event.value == 'PRESS':
            
            #Set the mesh to Even Sided
            if event.type == 'E':
                self.even = not self.even
                self.first_mouse_y = event.mouse_y
                UndoRedoObject(self, context)
                            
            #Set the mesh to Center the origin
            if event.type == 'C':
                if self.state == 1:
                    self.center[0] = not self.center[0]
                    self.center[1] = not self.center[1]
                
                if self.state == 2:
                    self.center[2] = not self.center[2]
                UndoRedoObject(self, context)
            
            #Flip the current even side for the mesh Z Axis. i.e. set Z axis to copy Y axis size instead of X, while in even mode
            if event.type == 'F': 
                self.flip = not self.flip
                UndoRedoObject(self, context)
        
        #
        #
        #
        #Do all the mouse movement operations
        if event.type == 'MOUSEMOVE':
            
            #Do planar drag
            if self.state == 1:
                #init vars
                planeRay = CastToPlaneFromCamera(context, event,self.loc, self.norm)
                if self.mode == 'EDIT':
                    objloc = self.loc
                else:
                    objloc = bpy.context.scene.objects.active.location
                hypotenuse = planeRay - objloc
                hypotenuseVect = hypotenuse.normalized()
                hypotenuseL = hypotenuse.length
                
                
                #Make sure the hypotenuse vector is not Zero, Doesn't effect final result just removes Error
                if hypotenuseVect.x == 0 and hypotenuseVect.y == 0 and hypotenuseVect.z == 0  :
                    hypotenuseVect = Vector((0.5, 0.5, 0))
                    

                #Get the angle difference between the hypotenuse and the X and Y Vectors of the object
                angleA = hypotenuseVect.angle(self.yAxis)
                angleT = hypotenuseVect.angle(self.xAxis)
                angleTdegrees = angleT * 180 / 3.14
                angleAdegrees = angleA * 180 / 3.14
                
                #Make sure the angles stay acute
                if angleAdegrees > 90:
                    angleAdegrees -= 90
                if angleTdegrees > 90:
                    angleTdegrees -= 90
                
                #Calculate the local X Y difference between the origin and the mouse position.
                
                #x    
                if angleT * 180 / 3.14 > 90:
                    self.scale.x = (hypotenuseL * math.sin(math.radians(angleTdegrees))) * (-1)
                else:
                    self.scale.x = hypotenuseL * math.cos(math.radians(angleTdegrees))
                #y
                if angleA * 180 / 3.14 > 90:
                    self.scale.y = (hypotenuseL * math.sin(math.radians(angleAdegrees))) * (-1)
                else:
                    self.scale.y = hypotenuseL * math.cos(math.radians(angleAdegrees))
                
                #Make Size Even
                if self.even:
                    if self.scale.x < 0:
                        self.scale.x = hypotenuseL * -1
                    else:
                        self.scale.x = hypotenuseL
                    if self.scale.y < 0:
                        self.scale.y = hypotenuseL * -1
                    else:
                        self.scale.y = hypotenuseL
                
                #Set the scale to follow the grid.
                if event.ctrl:
                    self.scale.x = (round(self.scale.x / (getUnitScale() * max(self.snapInc, 0.25)), 0)) * (getUnitScale() * max(self.snapInc, 0.25))
                    self.scale.y = (round(self.scale.y / (getUnitScale() * max(self.snapInc, 0.25)), 0)) * (getUnitScale() * max(self.snapInc, 0.25))
                
                #Sets so if the obj is centered the size still matches the mouse position
                if self.center[0] and self.center[1]:
                    self.scale.x = self.scale.x * 2
                    self.scale.y = self.scale.y * 2
                
                UndoRedoObject(self, context)
            
            #Do Depth drag    
            if self.state == 2:
                
                user_preferences = context.user_preferences
                addon_prefs = user_preferences.addons[__package__].preferences
                
                deltay = self.first_mouse_y - event.mouse_y
                #Set the smaller Z sensetivity value for when shift is held
                if event.shift: 
                    sens = 0.001 * addon_prefs.Zsensitivity
                else:
                    sens = 0.01 * addon_prefs.Zsensitivity
                #Set the scale to 1 if using the blender units so that the scaling is not accidentally ruined by a value that is not being used by blender itself.
                if bpy.context.scene.unit_settings.system == 'NONE':
                    scale = 1
                else:
                    scale = bpy.context.scene.unit_settings.scale_length
                self.temp_ZScale += deltay * ((-1 / scale) * sens)
                
                #Make Even sides and flip between X Y copy.
                if self.even:
                    if self.flip:
                        self.temp_ZScale = max(abs(self.scale.x), abs(self.scale.y))
                    else:
                        self.temp_ZScale = min(abs(self.scale.x), abs(self.scale.y))
                    if deltay > 0:
                        self.temp_ZScale = self.temp_ZScale * -1
                else:
                    self.first_mouse_y = event.mouse_y
                
                #Incremental Grid snapping
                if event.ctrl:
                    self.scale.z = (round(self.temp_ZScale / (getUnitScale() * max(self.snapInc, 0.25)), 0)) * (getUnitScale() * max(self.snapInc, 0.25))
                else:
                    self.scale.z = self.temp_ZScale
                UndoRedoObject(self, context)
                
                
        #
        #
        #
        #Left mouse press events and state switching
        if event.type == 'LEFTMOUSE': 
            if event.value == 'PRESS':
                
                #If holding shift reset the modal to continue making a new object without having to press a button again, good for making several objects quickly.
                if event.shift:
                    self.state = 0
                    ResetObjectParams(self, context)
                    self.scale = (0, 0, 1)
                    self.seg = (32, 16, 1)
                    self.temp_ZScale = 0
                    return {'RUNNING_MODAL'}
                
                #Mesh start location and begin planar drag
                if self.state == 0:
                    #Undo push so you can undo per object created while in the modal
                    bpy.ops.ed.undo_push(message="Add an undo step *function may be moved*")
                    
                    print('click1')
                    self.loc, self.norm, self.rot, self.boxDrawMode = RayCastForScene(context, event)
                    if event.ctrl:
                        #Don't Grid snap if you're creating a box on another object
                        if self.boxDrawMode == 'GRID' or self.boxDrawMode == 'SPACE':
                            self.loc = PointOnGrid(self.loc)
                    self.scale = (0, 0, 1)
                    AddObject(self, context)
                    
                    #init the axis vars for the planar calculations in the mouse move event.
                    ObjMatrix = self.rot.to_matrix()
                    self.xAxis = (ObjMatrix[0][0], ObjMatrix[1][0], ObjMatrix[2][0])
                    self.yAxis = (ObjMatrix[0][1], ObjMatrix[1][1], ObjMatrix[2][1])
                    
                    
            
                #Set radial size, and start Depth drag
                if self.state == 1:
                    self.scale.z = 0
                    self.first_mouse_y = event.mouse_y
                    
                    
                #Set Depth
                if self.state == 2:
                   print("click 2")
                   
                #Increment the state and stop the modal if it's ovet the max amount
                self.state += 1
                if self.state > self.max_states:
                    ResetObjectParams(self, context)
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    self.state = self.max_states
                    context.area.header_text_set()
                    return {'FINISHED'}
                
                #Deletes the mesh and remakes it (this is basically only here to make sure the mesh is renamed properly to Box.xxx)
                if self.mode == 'OBJECT':
                    if self.state > 1:
                        bpy.ops.object.delete()
                        AddObject(self, context)
                
            
        #Confirm Modal
        if event.type in {'RET', 'NUMPAD_ENTER'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.header_text_set()
            return {'FINISHED'}
        
        #Cancel modal        
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            #Allows you to cancel the operation while keeping everything made until this point, good for making planes and such.
            if event.shift:
                ResetObjectParams(self, context)
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.area.header_text_set()
                return {'FINISHED'}
            #Reverts the mesh by one state it's like holding shift but it allows you to lock in you scaling before canceling the operation.
            if event.alt:
                self.state = self.state - 1
                self.type = self.state
                if self.mode == 'EDIT':
                    bpy.ops.mesh.delete(type='VERT')
                else:
                    bpy.ops.object.delete()
                AddObject(self, context)
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.area.header_text_set()
                return{'FINISHED'}
            #Don't try to delete any objects if you haven't made any objects.
            if not self.state > 0:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.area.header_text_set()
                return {'CANCELLED'}
            #Canceling the modal with just a right click or esc, will delete any progress in making a mesh that you have done thus far.
            if self.mode == 'EDIT':
                bpy.ops.mesh.delete(type='VERT')
            else:
                bpy.ops.object.delete(use_global=False)
            
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.header_text_set()
            return {'CANCELLED'}
                
        return{'RUNNING_MODAL'}  
                
    #Makes sure that you can redo using the redo panel.
    def execute(self, context):
        #!!!Theres some sort of bug with this that makes it not possible to use the Shift+A add object panel in edit mode NEED TO FIX!!!#
        #Do redo panel stuff here
        self.state = self.type
        AddObject(self, context)
        return{'FINISHED'}

    def invoke(self, context, event):
        #Make sure you are in a the 3d view
        if context.space_data.type == 'VIEW_3D':
            #init some vars
            self.first_mouse_y = event.mouse_y
            self.scale = (0.1, 0.1, 0.1)
            self.seg = (32, 16, 0)
            self.center = (True, True, True)
            if bpy.context.object:
                self.mode = bpy.context.object.mode
                
            
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
                
            updateHeaderText(context, self, event)
                
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        
        #Run the Modal
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(SphereCreationModalOperator)

def unregister():
    bpy.utils.unregister_class(SphereCreationModalOperator)

if __name__ == "__main__":
    register()