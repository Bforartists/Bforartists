# This script is a simple example for an operator that gets called by a button.
# The button to execute it is in the Properties sidebar of the 3D view, in the View tab.
# The output of the operator gets printed to the console.
# You can't read it in the Info editor.

import bpy

# Our Operator
class XX_OT_print_me(bpy.types.Operator):
    """Print me\nPrint Text to Console"""
    bl_idname = "view.print_me"
    bl_label = "Print hotkey"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Operator is executing")
        return {'FINISHED'}

# Our Panel
class XX_PT_printmepanel(bpy.types.Panel):
    bl_label = "Print hotkey"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator(XX_OT_print_me.bl_idname, text="Print")

# Registering our classes. The classes tuple.
classes = (
    XX_OT_print_me,
    XX_PT_printmepanel,
)

# ------------------- Register Unregister
def register():
    from bpy.utils import register_class
    for cls in classes:
       register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
       unregister_class(cls)

# For scripting only
if __name__ == "__main__":
    register()