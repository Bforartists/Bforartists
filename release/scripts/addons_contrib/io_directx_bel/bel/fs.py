# v0.1
import bpy
from os import path as os_path, listdir as os_listdir
from bpy import path as bpy_path

# cross platform paths (since ms conform to / path ;) )
# maybe add utf8 replace to old ascii blender builtin
# // can be omitted for relative
def clean(path) :
    path = path.strip().replace('\\','/')
    if ('/') not in path : path = '//'+path
    return path
    
## test for existence of a file or a dir
def exist(path) :
    if isfile(path) or isdir(path) : return True
    return False

## test for existence of a file
def isfile(path) :
    if os_path.isfile(path) : return True
    # could be blender relative
    path = bpy_path.abspath(path)
    if os_path.isfile(path) : return True
    return False

## test for existence of a dir
def isdir(path) :
    if os_path.isdir(path) : return True
    # could be blender relative
    path = bpy_path.abspath(path)
    if os_path.isdir(path) : return True
    return False

## returns a list of every absolute filepath
# to each file within the 'ext' extensions
# from a folder and its subfolders
# warning, in windows filename are returned in lowercase.
def scanDir(path,ext='all') :
    files = []
    fields = os_listdir(path)
    if ext != 'all' and type(ext) != list : ext = [ext]
    for item in fields :
        if os_path.isfile(path + '/' + item) and (ext == 'all' or item.split('.')[-1] in ext) :
            #print('  file %s'%item)
            files.append(path + '/' + item)
        elif os_path.isdir(path + '/' + item) :
            #print('folder %s/%s :'%(path,item))
            files.extend(scanDir(path + '/' + item,ext))
    return files

def saveOptions(op,operator_name, tokens, filename='last_run'):
    #print(op.as_keywords())
    #print(dir(op))
    target_path = os_path.join("operator", operator_name)
    target_path = os_path.join("presets", target_path)
    target_path = bpy.utils.user_resource('SCRIPTS',target_path,create=True)
    if target_path:
        filepath = os_path.join(target_path, filename) + ".py"
        file_preset = open(filepath, 'w')
        file_preset.write("import bpy\nop = bpy.context.active_operator\n\n")
        properties_blacklist = bpy.types.Operator.bl_rna.properties.keys()
        for key, value in tokens.items() :
            if key not in properties_blacklist :
                # convert thin wrapped sequences to simple lists to repr()
                try:
                    value = value[:]
                except:
                    pass
    
                file_preset.write("op.%s = %r\n" % (key, value))

        file_preset.close()
    
