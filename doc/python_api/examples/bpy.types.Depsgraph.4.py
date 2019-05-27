"""
Dependency graph: Object.to_mesh()
+++++++++++++++++++++++++++++++++++

Function to get a mesh from any object with geometry. It is typically used by exporters, render
engines and tools that need to access the evaluated mesh as displayed in the viewport.

Object.to_mesh() is closely interacting with dependency graph: its behavior depends on whether it
is used on original or evaluated object.

When is used on original object, the result mesh is calculated from the object without taking
animation or modifiers into account:

- For meshes this is similar to duplicating the source mesh.
- For curves this disables own modifiers, and modifiers of objects used as bevel and taper.
- For metaballs this produces an empty mesh since polygonization is done as a modifier evaluation.

When is used on evaluated object all modifiers are taken into account.

.. note:: The result mesh is owned by the object. It can be freed by calling `object.to_mesh_clear()`.
.. note::
   The result mesh must be treated as temporary, and can not be referenced from objects in the main
   database. If the mesh intended to be used in a persistent manner use bpy.data.meshes.new_from_object()
   instead.
.. note:: If object does not have geometry (i.e. camera) the functions returns None.
"""
import bpy


class OBJECT_OT_object_to_mesh(bpy.types.Operator):
    """Convert selected object to mesh and show number of vertices"""
    bl_label = "DEG Object to Mesh"
    bl_idname = "object.object_to_mesh"

    def execute(self, context):
        # Access input original object.
        obj = context.object
        if obj is None:
            self.report({'INFO'}, "No active mesh object to convert to mesh")
            return {'CANCELLED'}
        # Avoid annoying None checks later on.
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
            self.report({'INFO'}, "Object can not be converted to mesh")
            return {'CANCELLED'}
        depsgraph = context.evaluated_depsgraph_get()
        # Invoke to_mesh() for original object.
        mesh_from_orig = obj.to_mesh()
        self.report({'INFO'}, f"{len(mesh_from_orig.vertices)} in new mesh without modifiers.")
        # Remove temporary mesh.
        obj.to_mesh_clear()
        # Invoke to_mesh() for evaluated object.
        object_eval = obj.evaluated_get(depsgraph)
        mesh_from_eval = object_eval.to_mesh()
        self.report({'INFO'}, f"{len(mesh_from_eval.vertices)} in new mesh with modifiers.")
        # Remove temporary mesh.
        object_eval.to_mesh_clear()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_object_to_mesh)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_object_to_mesh)


if __name__ == "__main__":
    register()
