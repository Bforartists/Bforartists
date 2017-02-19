import bpy

'''
given name < 21
if material name exists :
naming_method = 0   blender default (increment name)
naming_method = 1   do nothing, abort creation and use existing
naming_method = 2   create new, rename existing, 
naming_method = 3   create new, replace existing
'''

def new(name, naming_method=0) :
    if name not in bpy.data.materials or naming_method == 0:
        return bpy.data.materials.new(name=name)
    
    elif naming_method == 1 :
        return bpy.data.materials[name]
    
    mat = bpy.data.materials.new(name=name)
    
    if naming_method == 2 :
        mat.name = name
        return mat
    
    # naming_method = 3 : replace 
    prevmat = bpy.data.materials[name]
    for ob in bpy.data.objects :
        for matslot in ob.material_slots :
            if matslot.material == prevmat :
                matslot.material = mat
    bpy.data.materials.remove(prevmat)
    return mat

