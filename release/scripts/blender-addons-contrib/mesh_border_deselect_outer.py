import bpy
import bmesh

bl_info = {
    "name": "Border Deselect Outer",
    "author": "CoDEmanX",
    "version": (1, 2),
    "blender": (2, 66, 0),
    "location": "View3D > EditMode > Select",
    "description": "Make a selection, then run this operator " \
        "to border-select the desired selection intersection",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php" \
        "?title=Extensions:2.6/Py/Scripts/Modeling/Border_Deselect_Outer",
    "tracker_url": "http://blenderartists.org/forum/showthread.php" \
        "?290617-Mesh-Border-Deselect-Outer-(selection-intersection-by-using-a-border-select)",
    "category": "Mesh"}


def store_sel():
    bm = MESH_OT_border_deselect_outer.bm

    if 'select_old' in bm.loops.layers.int.keys():
        sel = bm.loops.layers.int['select_old']
    else:
        sel = bm.loops.layers.int.new("select_old")

    for v in bm.verts:
        v.link_loops[0][sel] = v.select

def restore_sel(me):
    bm = MESH_OT_border_deselect_outer.bm

    sel = bm.loops.layers.int['select_old']

    for v in bm.verts:
        if not (v.select and v.link_loops[0][sel]):
            v.select_set(False)

    bm.loops.layers.int.remove(sel)

    #bm.select_mode = {'VERT'}
    #bm.select_flush_mode()
    bm.select_flush(False)
    me.update()


def changed_sel():
    bm = MESH_OT_border_deselect_outer.bm

    sel = bm.loops.layers.int['select_old']

    for v in bm.verts:
        if v.select != v.link_loops[0][sel]:
            return True
    return False


class MESH_OT_border_deselect_outer(bpy.types.Operator):
    """Border select an existing selection and make only the intersection selected"""
    bl_idname = "mesh.border_deselect_outer"
    bl_label = "Border Deselect Outer"
    bl_options = {'REGISTER'}

    init = True
    bm = None
    mode_change = False

    def modal(self, context, event):

        if changed_sel() or not self.init:
            restore_sel(context.object.data)
            return {'FINISHED'}

        elif event.type in ('RIGHTMOUSE', 'ESC'):
            return {'CANCELLED'}

        if self.init:
            bpy.ops.view3d.select_border('INVOKE_DEFAULT', extend=False)
            self.init = False

        return {'RUNNING_MODAL'}
        #return {'PASS_THROUGH'} # Makes no difference

    @staticmethod
    def modecheck(context):
        return (context.area.type == 'VIEW_3D' and
                context.object and
                context.object.type == 'MESH' and
                context.object.mode == 'EDIT')

    @classmethod
    def poll(cls, context):
        return cls.modecheck(context)

    def invoke(self, context, event):
        if self.__class__.modecheck(context):

            MESH_OT_border_deselect_outer.bm = bmesh.from_edit_mesh(context.object.data)
            store_sel()
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active editmesh!")
            return {'CANCELLED'}

def menu_func(self, context):
    self.layout.operator("mesh.border_deselect_outer")


def register():
    bpy.utils.register_class(MESH_OT_border_deselect_outer)
    bpy.types.VIEW3D_MT_select_edit_mesh.prepend(menu_func)

def unregister():
    bpy.utils.unregister_class(MESH_OT_border_deselect_outer)
    bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_func)

if __name__ == "__main__":
    register()
