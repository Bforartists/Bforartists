
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
with open("C:\\Users\\x\\Downloads\\blender-2.78.0-git.0e5089c-windows64\\2.78\\scripts\\addons_contrib\\materials_library_vx\\categories.txt", "w") as f: 
    f.write(json.dumps(cats, sort_keys=True, indent=4))
