
print(30*"+")
import bpy
if not hasattr(bpy.context.scene, "matlib_categories"):
	class EmptyProps(bpy.types.PropertyGroup):
		pass
	bpy.utils.register_class(EmptyProps)
	bpy.types.Scene.matlib_categories = bpy.props.CollectionProperty(type=EmptyProps)
cats = bpy.context.scene.matlib_categories
for cat in cats:
	cats.remove(0)

bpy.ops.wm.save_mainfile(filepath="C:\\Users\\Dell\\Downloads\\blender-2.76-301115-win64\\blender-2.76.0-git.3780158-AMD64\\2.76\\scripts\\addons\\matlib_cycles\\car_paint.blend", check_existing=False, compress=True)