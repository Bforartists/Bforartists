import bpy, mathutils


bl_info = {
    'name': 'Curve Remove Doubles',
    'author': 'Michael Soluyanov',
    'version': (1, 1),
    'blender': (2, 80, 0),
    'location': 'View3D > Context menu (W/RMB) > Remove Doubles',
    'description': 'Adds comand "Remove Doubles" for curves',
    'category': 'Object'
}

def main(context, distance = 0.01):
    
    obj = context.active_object
    dellist = []
    
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='EDIT')
    
    for spline in obj.data.splines: 
        if len(spline.bezier_points) > 1:
            for i in range(0, len(spline.bezier_points)): 
                
                if i == 0:
                    ii = len(spline.bezier_points) - 1
                else:        
                    ii = i - 1
                    
                dot = spline.bezier_points[i];
                dot1 = spline.bezier_points[ii];   
                    
                while dot1 in dellist and i != ii:
                    ii -= 1
                    if ii < 0: 
                        ii = len(spline.bezier_points)-1
                    dot1 = spline.bezier_points[ii]
                    
                if dot.select_control_point and dot1.select_control_point and (i!=0 or spline.use_cyclic_u):   
                    
                    if (dot.co-dot1.co).length < distance:
                        # remove points and recreate hangles
                        dot1.handle_right_type = "FREE"
                        dot1.handle_right = dot.handle_right
                        dot1.co = (dot.co + dot1.co) / 2
                        dellist.append(dot)
                        
                    else:
                        # Handles that are on main point position converts to vector,
                        # if next handle are also vector
                        if dot.handle_left_type == 'VECTOR' and (dot1.handle_right - dot1.co).length < distance:
                            dot1.handle_right_type = "VECTOR"
                        if dot1.handle_right_type == 'VECTOR' and (dot.handle_left - dot.co).length < distance:
                            dot.handle_left_type = "VECTOR"  
                      
                            
    
    bpy.ops.curve.select_all(action = 'DESELECT')

    for dot in dellist:
        dot.select_control_point = True
        
    count = len(dellist)
    
    bpy.ops.curve.delete(type = 'VERT')
    
    bpy.ops.curve.select_all(action = 'SELECT')
    
    return count
    


class CurveRemvDbs(bpy.types.Operator):
    """Merge consecutive points that are near to each other"""
    bl_idname = 'curve.remove_doubles'
    bl_label = 'Remove Doubles'
    bl_options = {'REGISTER', 'UNDO'}

    distance: bpy.props.FloatProperty(name = 'Distance', default = 0.01)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE')

    def execute(self, context):
        removed=main(context, self.distance)
        self.report({'INFO'}, "Removed %d bezier points" % removed)
        return {'FINISHED'}




def menu_func(self, context):
    self.layout.operator(CurveRemvDbs.bl_idname, text='Remove Doubles')

def register():
    bpy.utils.register_class(CurveRemvDbs)
    bpy.types.VIEW3D_MT_edit_curve_context_menu.append(menu_func)

def unregister():
    bpy.utils.unregister_class(CurveRemvDbs)
    bpy.types.VIEW3D_MT_edit_curve_context_menu.remove(menu_func)

if __name__ == "__main__":
    register()



