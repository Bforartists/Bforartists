import bpy

def main(context):
    for ob in context.scene.objects:
        print(ob)

class SimpleOperator(bpy.types.Operator):
    ''''''
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"

    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


if __name__ == "__main__":
    bpy.ops.object.simple_operator()
