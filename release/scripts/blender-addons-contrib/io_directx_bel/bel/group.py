import bpy
'''
given name < 21
if material name exists :
naming_method = 0   blender default (increment name)
naming_method = 1   do nothing, abort creation and use existing
naming_method = 2   create new, rename existing, 
naming_method = 3   create new, replace existing
'''

def new(name,naming_method):
    if name in bpy.data.groups and naming_method :
        grp = bpy.data.groups[name]
        # if naming_method == 1 return existing
        if naming_method == 2 :
            grp = bpy.data.groups.new(name)
            grp.name = name
        elif naming_method == 3 :
            bpy.data.groups.remove(grp)
            grp = bpy.data.groups.new(name)
    else :
        grp = bpy.data.groups.new(name)
    return grp

##  TODO
# @param ob 'all', 'active', 'selected', <object>, 'objectname'
# @return a list of objects or an empty list
def get(grp) :
    if type(ob) == str :
        if ob == 'all' : return bpy.context.scene.objects
        elif ob == 'active' : return [bpy.context.active_object] if bpy.context.active_object != None else []
        elif ob == 'selected' : return bpy.context.selected_objects
        else :
            try : return [bpy.data.objects[ob]]
            except : return []
    return [ob]


## TODO remove an object from blender internal
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

