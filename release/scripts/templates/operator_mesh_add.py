import bpy


def add_box(width, height, depth):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    vertices = [1.0, 1.0, -1.0,
                1.0, -1.0, -1.0,
                -1.0, -1.0, -1.0,
                -1.0, 1.0, -1.0,
                1.0, 1.0, 1.0,
                1.0, -1.0, 1.0,
                -1.0, -1.0, 1.0,
                -1.0, 1.0, 1.0,
                ]

    faces = [0, 1, 2, 3,
             4, 7, 6, 5,
             0, 4, 5, 1,
             1, 5, 6, 2,
             2, 6, 7, 3,
             4, 0, 3, 7,
            ]

    # apply size
    for i in range(0, len(vertices), 3):
        vertices[i] *= width
        vertices[i + 1] *= depth
        vertices[i + 2] *= height

    return vertices, faces


from bpy.props import *


class AddBox(bpy.types.Operator):
    '''Add a simple box mesh'''
    bl_idname = "mesh.primitive_box_add"
    bl_label = "Add Box"
    bl_options = {'REGISTER', 'UNDO'}

    width = FloatProperty(name="Width",
            description="Box Width",
            default=1.0, min=0.01, max=100.0)

    height = FloatProperty(name="Height",
            description="Box Height",
            default=1.0, min=0.01, max=100.0)

    depth = FloatProperty(name="Depth",
            description="Box Depth",
            default=1.0, min=0.01, max=100.0)

    # generic transform props
    view_align = BoolProperty(name="Align to View",
            default=False)
    location = FloatVectorProperty(name="Location",
            subtype='TRANSLATION')
    rotation = FloatVectorProperty(name="Rotation",
            subtype='EULER')

    def execute(self, context):

        verts_loc, faces = add_box(self.width,
                                     self.height,
                                     self.depth,
                                     )

        mesh = bpy.data.meshes.new("Box")

        mesh.vertices.add(len(verts_loc) // 3)
        mesh.faces.add(len(faces) // 4)

        mesh.vertices.foreach_set("co", verts_loc)
        mesh.faces.foreach_set("vertices_raw", faces)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        import add_object_utils
        add_object_utils.object_data_add(context, mesh, operator=self)

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(AddBox.bl_idname, icon='MESH_CUBE')


def register():
    bpy.utils.register_class(AddBox)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(AddBox)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.mesh.primitive_box_add()
