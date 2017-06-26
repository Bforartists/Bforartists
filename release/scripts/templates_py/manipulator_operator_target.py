# Example of a manipulator that activates an operator
# using the predefined dial manipulator to change the camera roll.
#
# Usage: Run this script and select a camera in the 3D view.
#
import bpy
from bpy.types import (
    ManipulatorGroup,
)

class MyCameraWidgetGroup(ManipulatorGroup):
    bl_idname = "OBJECT_WGT_test_camera"
    bl_label = "Object Camera Test Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.type == 'CAMERA')

    def setup(self, context):
        # Run an operator using the dial manipulator
        ob = context.object
        mpr = self.manipulators.new("MANIPULATOR_WT_dial_3d")
        props = mpr.target_set_operator("transform.rotate")
        props.constraint_axis = False, False, True
        props.constraint_orientation = 'LOCAL'
        props.release_confirm = True

        mpr.matrix_basis = ob.matrix_world.normalized()
        mpr.line_width = 3

        mpr.color = 0.8, 0.8, 0.8, 0.5
        mpr.color_highlight = 1.0, 1.0, 1.0, 1.0

        self.roll_widget = mpr

    def refresh(self, context):
        ob = context.object
        mpr = self.roll_widget
        mpr.matrix_basis = ob.matrix_world.normalized()

bpy.utils.register_class(MyCameraWidgetGroup)
