# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    'name': 'Curve Fillet',
    'author': 'Spivak Vladimir (cwolf3d)',
    'version': (0, 0, 1),
    'blender': (2, 80, 0),
    'location': 'Curve Tools addon. (N) Panel',
    'description': 'Various types of fillet (chamfering)',
    'warning': '', # used for warning icon and text in addons panel
    'doc_url': '',
    'tracker_url': '',
    'category': 'Curve',
}


import bpy
from bpy.props import *
from bpy_extras import object_utils, view3d_utils
from mathutils import  *
from math import  *

def click(self, context, event):
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.context.view_layer.update()


def remove_handler(handlers):
    for handler in handlers:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        except:
            pass
    for handler in handlers:
        handlers.remove(handler)


class Fillet(bpy.types.Operator):
    bl_idname = "curvetools.fillet"
    bl_label = "Curve Fillet"
    bl_description = "Curve Fillet"
    bl_options = {'REGISTER', 'UNDO'}

    x: IntProperty(name="x", description="x")
    y: IntProperty(name="y", description="y")
    location3D: FloatVectorProperty(name = "",
                description = "Start location",
                default = (0.0, 0.0, 0.0),
                subtype = 'XYZ')

    handlers = []

    def execute(self, context):
        self.report({'INFO'}, "ESC or TAB - cancel")
        bpy.ops.object.mode_set(mode = 'EDIT')

        # color change in the panel
        self.path_color = bpy.context.scene.curvetools.path_color
        self.path_thickness = bpy.context.scene.curvetools.path_thickness

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'ESC', 'TAB'}:  # Cancel
            remove_handler(self.handlers)
            return {'CANCELLED'}

        if event.type in {'X', 'DEL'}:  # Cancel
            remove_handler(self.handlers)
            bpy.ops.curve.delete(type='VERT')
            return {'RUNNING_MODAL'}

        elif event.alt and event.shift and event.type == 'LEFTMOUSE':
            click(self, context, event)

        elif event.alt and not event.shift and event.type == 'LEFTMOUSE':
            remove_handler(self.handlers)
            bpy.ops.curve.select_all(action='DESELECT')
            click(self, context, event)

        elif event.alt and event.type == 'RIGHTMOUSE':
           remove_handler(self.handlers)
           bpy.ops.curve.select_all(action='DESELECT')
           click(self, context, event)

        elif event.alt and not event.shift and event.shift and event.type == 'RIGHTMOUSE':
            click(self, context, event)

        elif event.type == 'A':
            remove_handler(self.handlers)
            bpy.ops.curve.select_all(action='DESELECT')

        elif event.type == 'MOUSEMOVE':  #
            self.x = event.mouse_x
            self.y = event.mouse_y
            region = bpy.context.region
            rv3d = bpy.context.space_data.region_3d
            self.location3D = view3d_utils.region_2d_to_location_3d(
                region,
                rv3d,
                (event.mouse_region_x, event.mouse_region_y),
                (0.0, 0.0, 0.0)
                )

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'CURVE')

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()

operators = [Fillet]
