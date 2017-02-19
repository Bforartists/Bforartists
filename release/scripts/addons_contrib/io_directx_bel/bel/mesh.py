##\file
# raw extract quick cleaning from blended cities2.6 project. thanks to myself for cooperation, but what a messy code we have here.
import bpy
import mathutils
from mathutils import *
import bmesh

from . import uv as buv
from . import ob as bob

debuglevel = 0
'''
wip.. naming behaviour previous to any data
name exist ?
no : create
yes :
    naming_method = 0   blender default (increment name)
    naming_method = 1   do nothing, abort creation and use existing
    naming_method = 2   create new, rename existing, 
    naming_method = 3   create new, remove existing
    
for now, and mesh data, 0 2 or 3
'''

'''
given name < 21
if material name exists :
naming_method = 0   blender default (increment name)
naming_method = 1   do nothing, abort creation and use existing
naming_method = 2   create new, rename existing, 
naming_method = 3   create new, replace existing
'''

def new(name, naming_method=0) :
    if name not in bpy.data.meshes or naming_method == 0:
        return bpy.data.meshes.new(name=name)

    if naming_method == 1 :
        return bpy.data.meshes[name]

    if naming_method == 2 :
        me = bpy.data.meshes.new(name=name)
        me.name = name
        return me
    
    # naming_method = 3 : replace, keep users
    me = bpy.data.meshes[name]
    bm = bmesh.new()
    bm.to_mesh(me)
    return me

## material listed in matslots must exist before creation of material slots

def write(obname,name, 
          verts=[], edges=[], faces=[], 
          matslots=[], mats=[], uvs=[], 
          groupnames=[], vindices=[], vweights=[],
          smooth=False,
          naming_method = 0,
          ) :

    
    obj = bpy.data.objects[obname] if obname in bpy.data.objects else False
    me = bpy.data.meshes[name] if name in bpy.data.meshes else False

    #print(naming_method,type(obj),type(me))
    #print(obj,me)
    #print()
    if naming_method == 1 and me and obj and obj.data == me :
        #print('%s and %s exist, reuse'%(obj.name,me.name))
        return obj
       
    if naming_method == 3 :
        if obj : 
            #print('remove ob %s'%obj.name)
            bob.remove(obj,False)
        if me :
            #print('remove me %s'%me.name)
            bob.removeData(me)
    

    me = bpy.data.meshes.new(name)
    if naming_method == 2 : me.name = name
    
    me.from_pydata(verts, edges, faces)
    me.update()

    if smooth : shadesmooth(me)

    # material slots
    matimage=[]
    if len(matslots) > 0 :
        for matname in matslots :
            '''
            if matname not in bpy.data.materials :
                mat = bpy.data.materials.new(name=matname)
                mat.diffuse_color=( random.uniform(0.0,1.0),random.uniform(0.0,1.0),random.uniform(0.0,1.0))
                mat.use_fake_user = True
                warn.append('Created missing material : %s'%matname)
            else :
            '''
            mat = bpy.data.materials[matname]
            me.materials.append(mat)
            texslot_nb = len(mat.texture_slots)
            if texslot_nb :
                texslot = mat.texture_slots[0]
                if type(texslot) != type(None) :
                    tex = texslot.texture
                    if tex.type == 'IMAGE' :
                        img = tex.image
                        if type(img) != type(None) :
                            matimage.append(img)
                            continue
            matimage.append(False)

    # uvs
    if len(uvs) > 0 :
        #buv.write(me, uvs, matimage)
        buv.flatwrite(me, uvs)

    # map a material to each face
    if len(mats) > 0 :
        for fi,f in enumerate(me.polygons) :
            f.material_index = mats[fi]

    obj = bpy.data.objects.new(name=obname, object_data=me)
    if naming_method != 0 :
        obj.name = obname
            
    '''
    else :
        ob = bpy.data.objects[name]
        ob.data = me
        if naming_method == 2 : ob.name = 
        ob.parent = None
        ob.matrix_local = Matrix()
        print('  reuse object %s'%ob.name)
    '''
            
    # vertexgroups
    if len(groupnames) > 0 :
        for gpi, groupname in enumerate(groupnames) :
            weightsadd(obj, groupname, vindices[gpi], vweights[gpi])
    
    # scene link check
    if obj.name not in bpy.context.scene.objects.keys() :
        bpy.context.scene.objects.link(obj)
        
    return obj

def shadesmooth(me,lst=True) :
    if type(lst) == list :
        for fi in lst :
            me.polygons[fi].use_smooth = True
    else :
        for fi,face in enumerate(me.polygons) :
            face.use_smooth = True
 
def shadeflat(me,lst=True) :
    if type(lst) == list :
        for fi in lst :
            me.polygons[fi].use_smooth = False
    else :
        for fi,face in enumerate(me.polygons) :
            face.use_smooth = False

def weightsadd(ob, groupname, vindices, vweights=False) :
    if vweights == False : vweights = [1.0 for i in range(len(vindices))]
    elif type(vweights) == float : vweights = [vweights for i in range(len(vindices))]
    group = ob.vertex_groups.new(groupname)
    for vi,v in enumerate(vindices) :
        group.add([v], vweights[vi], 'REPLACE')

def matToString(mat) :
    #print('*** %s %s'%(mat,type(mat)))
    return str(mat).replace('\n       ','')[6:]

def stringToMat(string) :
    return Matrix(eval(string))


def objectBuild(elm, verts, edges=[], faces=[], matslots=[], mats=[], uvs=[] ) :
    #print('build element %s (%s)'%(elm,elm.className()))
    dprint('object build',2)
    city = bpy.context.scene.city
    # apply current scale
    verts = metersToBu(verts)
    
    if type(elm) != str :
        obname = elm.objectName()
        if obname == 'not built' :
            obname = elm.name
    else : obname= elm

    obnew = createMeshObject(obname, True, verts, edges, faces, matslots, mats, uvs)
    #elm.asElement().pointer = str(ob.as_pointer())
    if type(elm) != str :
        if elm.className() == 'outlines' :
            obnew.lock_scale[2] = True
            if elm.parent :
                obnew.parent = elm.Parent().object()
        else :
            #otl = elm.asOutline()
            #ob.parent = otl.object()
            objectLock(obnew,True)
        #ob.matrix_local = Matrix() # not used
        #ob.matrix_world = Matrix() # world
    return obnew

def dprint(str,l=2) :
    if l <= debuglevel :
        print(str)


def materialsCheck(bld) :
    if hasattr(bld,'materialslots') == False :
        #print(bld.__class__.__name__)
        builderclass = eval('bpy.types.%s'%(bld.__class__.__name__))
        builderclass.materialslots=[bld.className()]

    matslots = bld.materialslots
    if len(matslots) > 0 :
        for matname in matslots :
            if matname not in bpy.data.materials :
                mat = bpy.data.materials.new(name=matname)
                mat.use_fake_user = True
                if hasattr(bld,'mat_%s'%(matname)) :
                    method = 'defined by builder'
                    matdef = eval('bld.mat_%s'%(matname))
                    mat.diffuse_color = matdef['diffuse_color']
                else :
                    method = 'random'
                    mat.diffuse_color=( random.uniform(0.0,1.0),random.uniform(0.0,1.0),random.uniform(0.0,1.0))
                dprint('Created missing material %s (%s)'%(matname,method),2)


