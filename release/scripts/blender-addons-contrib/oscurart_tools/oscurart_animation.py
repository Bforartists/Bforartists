import bpy
from mathutils import Matrix

##---------------------------RELOAD IMAGES------------------

bpy.types.Scene.quick_animation_in = bpy.props.IntProperty(default=1)
bpy.types.Scene.quick_animation_out = bpy.props.IntProperty(default=250)

def DefQuickParent(inf,out):
    if bpy.context.object.type == "ARMATURE":
        ob = bpy.context.object
        target = [object for object in bpy.context.selected_objects if object != ob][0]
        ob = bpy.context.active_pose_bone if bpy.context.object.type == 'ARMATURE' else bpy.context.object
        target.select = False
        bpy.context.scene.frame_set(frame=bpy.context.scene.quick_animation_in)
        a = Matrix(target.matrix_world)
        a.invert()
        i = Matrix(ob.matrix)
        for frame in range(inf,out): 
            bpy.context.scene.frame_set(frame=frame)
            ob.matrix = target.matrix_world * a * i     
            bpy.ops.anim.keyframe_insert(type="LocRotScale")   
    else:
        ob = bpy.context.object
        target = [object for object in bpy.context.selected_objects if object != ob][0]
        ob = bpy.context.active_pose_bone if bpy.context.object.type == 'ARMATURE' else bpy.context.object
        target.select = False
        bpy.context.scene.frame_set(frame=bpy.context.scene.quick_animation_in)
        a = Matrix(target.matrix_world)
        a.invert()
        i = Matrix(ob.matrix_world)
        for frame in range(inf,out): 
            bpy.context.scene.frame_set(frame=frame)
            ob.matrix_world = target.matrix_world * a * i     
            bpy.ops.anim.keyframe_insert(type="LocRotScale")   

class QuickParent (bpy.types.Operator):
    bl_idname = "anim.quick_parent_osc"
    bl_label = "Quick Parent"
    bl_options = {"REGISTER", "UNDO"}      
    
    def execute(self,context):
        DefQuickParent(bpy.context.scene.quick_animation_in,bpy.context.scene.quick_animation_out)
        return {'FINISHED'}


