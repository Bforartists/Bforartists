import bpy
from bpy.props import BoolProperty
from bpy.types import Operator, Panel
from curve_tools.Surfaces import LoftedSurface
from curve_tools.Curves import Curve
from curve_tools import Util


class OperatorAutoLoftCurves(Operator):
    bl_idname = "curvetools2.create_auto_loft"
    bl_label = "Loft"
    bl_description = "Lofts selected curves"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorLoftCurves.execute()")
        mesh = bpy.data.meshes.new("LoftMesh")

        curve0 = context.selected_objects[0]
        curve1 = context.selected_objects[1]

        ls = LoftedSurface(Curve(curve0), Curve(curve1), "AutoLoft")

        ls.bMesh.to_mesh(mesh)

        loftobj = bpy.data.objects.new(self.name, mesh)

        context.collection.objects.link(loftobj)
        loftobj["autoloft"] = True
        if loftobj.get('_RNA_UI') is None:
            loftobj['_RNA_UI'] = {}
        loftobj['_RNA_UI']["autoloft"] = {
                           "name": "Auto Loft",
                           "description": "Auto loft from %s to %s" % (curve0.name, curve1.name),
                           "curve0": curve0.name,
                           "curve1": curve1.name}
        print(loftobj['_RNA_UI'].to_dict())
        self.report({'INFO'}, "OperatorAutoLoftCurves.execute()")

        return {'FINISHED'}


class AutoLoftModalOperator(Operator):
    """Auto Loft"""
    bl_idname = "wm.auto_loft_curve"
    bl_label = "Auto Loft"
    bl_description = "Lofts selected curves"

    _timer = None
    @classmethod
    def poll(cls, context):
        # two curves selected.
        return True

    def modal(self, context, event):
        scene = context.scene
        wm = context.window_manager
        if event.type in {'ESC'}:
            wm.auto_loft = False

        if not wm.auto_loft:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            lofters = [o for o in scene.objects if "autoloft" in o.keys()]
            # quick hack
            #print("TIMER", lofters)

            for loftmesh in lofters:
                loftmesh.hide_select = True
                rna = loftmesh['_RNA_UI']["autoloft"].to_dict()
                curve0 = scene.objects.get(rna["curve0"])
                curve1 = scene.objects.get(rna["curve1"])
                if curve0 and curve1:
                    ls = LoftedSurface(Curve(curve0), Curve(curve1), loftmesh.name)
                    ls.bMesh.to_mesh(loftmesh.data)

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)



def run_auto_loft(self, context):
    if self.auto_loft:
        bpy.ops.wm.auto_loft_curve()
    return None

def register():
    bpy.utils.register_class(AutoLoftModalOperator)
    bpy.utils.register_class(OperatorAutoLoftCurves)
    bpy.types.WindowManager.auto_loft = BoolProperty(default=False,
                                                     name="Auto Loft",
                                                     update=run_auto_loft)
    bpy.context.window_manager.auto_loft = False

def unregister():
    bpy.utils.unregister_class(AutoLoftModalOperator)
    bpy.utils.unregister_class(OperatorAutoLoftCurves)

if __name__ == "__main__":
    register()


    # test call
    #bpy.ops.wm.modal_timer_operator()
