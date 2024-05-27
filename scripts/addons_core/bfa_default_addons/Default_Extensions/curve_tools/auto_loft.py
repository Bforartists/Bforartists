# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import BoolProperty
from bpy.types import Operator, Panel
from . import surfaces
from . import curves
from . import util


class OperatorAutoLoftCurves(Operator):
    bl_idname = "curvetools.create_auto_loft"
    bl_label = "Loft"
    bl_description = "Lofts selected curves"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected2Curves()

    def execute(self, context):
        #print("### TODO: OperatorLoftcurves.execute()")
        mesh = bpy.data.meshes.new("LoftMesh")

        curve0 = context.selected_objects[0]
        curve1 = context.selected_objects[1]

        ls = surfaces.LoftedSurface(curves.Curve(curve0), curves.Curve(curve1), "AutoLoft")

        ls.bMesh.to_mesh(mesh)

        loftobj = bpy.data.objects.new(self.name, mesh)

        context.collection.objects.link(loftobj)
        loftobj["autoloft"] = True
        ui_data = loftobj.id_properties_ui("autoloft")
        ui_data.update(description="Auto loft from %s to %s" % (curve0.name, curve1.name))
        loftobj["autoloft_curve0"] = curve0.name
        loftobj["autoloft_curve1"] = curve1.name

        return {'FINISHED'}

class AutoLoftModalOperator(Operator):
    """Auto Loft"""
    bl_idname = "curvetools.update_auto_loft_curves"
    bl_label = "Update Auto Loft"
    bl_description = "Update Lofts selected curves"

    _timer = None
    @classmethod
    def poll(cls, context):
        # two curves selected.
        return True

    def execute(self, context):
        scene = context.scene
        lofters = [o for o in scene.objects if "autoloft" in o.keys()]
        # quick hack
        #print("TIMER", lofters)

        for loftmesh in lofters:
            curve0 = scene.objects.get(loftmesh['autoloft_curve0'])
            curve1 = scene.objects.get(loftmesh['autoloft_curve1'])
            if curve0 and curve1:
                ls = surfaces.LoftedSurface(curves.Curve(curve0), curves.Curve(curve1), loftmesh.name)
                ls.bMesh.to_mesh(loftmesh.data)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(AutoLoftModalOperator)
    bpy.utils.register_class(OperatorAutoLoftCurves)
    bpy.types.WindowManager.auto_loft = BoolProperty(default=False,
                                                     name="Auto Loft")
    bpy.context.window_manager.auto_loft = False

def unregister():
    bpy.utils.unregister_class(AutoLoftModalOperator)
    bpy.utils.unregister_class(OperatorAutoLoftCurves)

if __name__ == "__main__":
    register()
