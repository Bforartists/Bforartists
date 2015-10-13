import bpy
from bpy.types import Mesh, PointLamp, SpotLamp, HemiLamp, AreaLamp, SunLamp, Camera, TextCurve, MetaBall, Lattice, Armature


def new(name,datatype,naming_method):
    if name in bpy.data.objects and naming_method :
        ob = bpy.data.objects[name]
        if naming_method == 1 :
            ob.parent = None
            ob.user_clear()
        elif naming_method == 2 :
            ob = bpy.data.objects.new(name,datatype)
            ob.name = name
        elif naming_method == 3 :
            bpy.context.scene.objects.unlink(ob)
            ob.user_clear()
            bpy.data.objects.remove(ob)
            ob = bpy.data.objects.new(name,datatype)
    else :
        ob = bpy.data.objects.new(name,datatype)
    if ob.name not in bpy.context.scene.objects.keys() :
        bpy.context.scene.objects.link(ob)
    return ob

## returns an object or a list of objects
# @param ob 'all', 'active', 'selected', <object>, 'objectname'
# @return a list of objects or an empty list
def get(ob) :
    if type(ob) == str :
        if ob == 'all' : return bpy.context.scene.objects
        elif ob == 'active' : return [bpy.context.active_object] if bpy.context.active_object != None else []
        elif ob == 'selected' : return bpy.context.selected_objects
        else :
            try : return [bpy.data.objects[ob]]
            except : return []
    return [ob]


## remove an object from blender internal
def remove(ob,with_data=True) :
    objs = get(ob)
    #if objs :
    #    if type(objs) == bpy.types.Object : objs = [objs]
    for ob in objs :
            data = ob.data
            #and_data=False
            # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
            # if there's more than one user for this data, never wipeOutData. will be done with the last user
            # if in the list
            and_data = with_data
            try :
                if data.users > 1 :
                    and_data=False
            except :
                and_data=False # empties
                
            # odd (pre 2.60) :
            # ob=bpy.data.objects[ob.name]
            # if the ob (board) argument comes from bpy.data.groups['aGroup'].objects,
            #  bpy.data.groups['board'].objects['board'].users_scene
            ob.name = '_dead'
            for sc in ob.users_scene :
                sc.objects.unlink(ob)

            #try :
                #print('  removing object %s...'%(ob.name)),
            bpy.data.objects.remove(ob)
                #print('  done.')
            #except :
            #    print('removing failed, but renamed %s and unlinked'%ob.name)

            # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
            if and_data :
                wipeOutData(data)


## remove an object data from blender internal
## or rename it _dead if there's still users
def removeData(data) :
    #print('%s has %s user(s) !'%(data.name,data.users))
    
    if data.users <= 0 :

            #data.user_clear()
            data_type = type(data)
            
            # mesh
            if data_type == Mesh :
                bpy.data.meshes.remove(data)
            # lamp
            elif data_type in [ PointLamp, SpotLamp, HemiLamp, AreaLamp, SunLamp ] :
                bpy.data.lamps.remove(data)
            # camera
            elif data_type == Camera :
                bpy.data.cameras.remove(data)
            # Text, Curve
            elif data_type in [ Curve, TextCurve ] :
                bpy.data.curves.remove(data)
            # metaball
            elif data_type == MetaBall :
                bpy.data.metaballs.remove(data)
            # lattice
            elif data_type == Lattice :
                bpy.data.lattices.remove(data)
            # armature
            elif data_type == Armature :
                bpy.data.armatures.remove(data)
            else :
                print('  data still here : forgot %s type'%type(data))
        #except :
            # empty, field
        #    print('%s has no user_clear attribute ? (%s).'%(data.name,type(data)))
    else :
        #print('  not done, %s has %s user'%(data.name,data.users))
        data.name = '_dead'
        