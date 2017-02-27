
# set a given name to a unique
# blender data name in its collection
def bpyname(name,collection,limit=63,suffix=4) :
    name = name[:limit-suffix]
    tpl = '%s.%.'+str(suffix)+'d'
    bname = name
    id = 0
    while bname in collection :
        id += 1
        bname = tpl%(name,id)
    return bname

## check if there's nested lists in a list. used by functions that need
# list(s) of vertices/faces/edges etc as input
# @param lst a list of vector or a list of list of vectors
# @returns always nested list(s)
# a boolean True if was nested, False if was not
def nested(lst) :
    try :
        t = lst[0][0][0]
        return lst, True
    except :
        return [lst], False