
import bpy, json
class EmptyProps(bpy.types.PropertyGroup):
    pass
bpy.utils.register_class(EmptyProps)
bpy.types.Scene.matlib_categories = bpy.props.CollectionProperty(type=EmptyProps)
cats = []
for cat in bpy.context.scene.matlib_categories:
    materials = []
    for mat in bpy.data.materials:
        if "category" in mat.keys() and mat['category'] == cat.name:
            materials.append(mat.name)
    cats.append([cat.name, materials])
with open("C:\\Users\\Dell\\Downloads\\blender-2.77-300716-win64\\blender-2.77.0-git.3d7cf80-AMD64\\2.77\\scripts\\addons_contrib\\materials_library_vx\\categories.txt", "w") as f: 
    f.write(json.dumps(cats, sort_keys=True, indent=4))
