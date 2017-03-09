bl_info = {
    "name": "Random Vertices",
    "author": "Oscurart, Greg",
    "version": (1, 1),
    "blender": (2, 6, 3),
    "api": 3900,
    "location": "Object > Transform > Random Vertices",
    "description": "Randomize selected components of active object.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}


import bpy
import random
import bmesh


def add_object(self, context, VALMIN, VALMAX, FACTOR, VGFILTER):

    # DISCRIMINA EN LA OPCION CON MAPA DE PESO O NO

    if VGFILTER == True:

        # GENERO VARIABLES
        MODE = bpy.context.active_object.mode
        OBJACT = bpy.context.active_object
        LISTVER = []

        # PASO A EDIT
        bpy.ops.object.mode_set(mode='EDIT')

        # BMESH OBJECT
        ODATA = bmesh.from_edit_mesh(OBJACT.data)
        ODATA.select_flush(False)

        # SI EL VERTICE ESTA SELECCIONADO LO SUMA A UNA LISTA
        for vertice in ODATA.verts[:]:
            if vertice.select:
                LISTVER.append(vertice.index)

        # SI EL VALOR MINIMO ES MAYOR AL MAXIMO, LE SUMA UN VALOR AL MAXIMO
        if VALMIN[0] >= VALMAX[0]:
            VALMAX[0] = VALMIN[0] + 1

        if VALMIN[1] >= VALMAX[1]:
            VALMAX[1] = VALMIN[1] + 1

        if VALMIN[2] >= VALMAX[2]:
            VALMAX[2] = VALMIN[2] + 1

        for vertice in LISTVER:
            if ODATA.verts[vertice].select:
                VERTEXWEIGHT = OBJACT.data.vertices[vertice].groups[0].weight
                ODATA.verts[vertice].co = (
                    (((random.randrange(VALMIN[0], VALMAX[0], 1)) * VERTEXWEIGHT * FACTOR) / 1000) + ODATA.verts[vertice].co[0],
                    (((random.randrange(VALMIN[1], VALMAX[1], 1)) * VERTEXWEIGHT * FACTOR) / 1000) + ODATA.verts[vertice].co[1],
                    (((random.randrange(VALMIN[2], VALMAX[2], 1)) * VERTEXWEIGHT * FACTOR) / 1000) + ODATA.verts[vertice].co[2]
                )

    else:

        if VGFILTER == False:

            # GENERO VARIABLES
            MODE = bpy.context.active_object.mode
            OBJACT = bpy.context.active_object
            LISTVER = []

            # PASO A MODO OBJECT
            bpy.ops.object.mode_set(mode='EDIT')

            # BMESH OBJECT
            ODATA = bmesh.from_edit_mesh(OBJACT.data)
            ODATA.select_flush(False)

            # SI EL VERTICE ESTA SELECCIONADO LO SUMA A UNA LISTA
            for vertice in ODATA.verts[:]:
                if vertice.select:
                    LISTVER.append(vertice.index)

            # SI EL VALOR MINIMO ES MAYOR AL MAXIMO, LE SUMA UN VALOR AL MAXIMO
            if VALMIN[0] >= VALMAX[0]:
                VALMAX[0] = VALMIN[0] + 1

            if VALMIN[1] >= VALMAX[1]:
                VALMAX[1] = VALMIN[1] + 1

            if VALMIN[2] >= VALMAX[2]:
                VALMAX[2] = VALMIN[2] + 1

            for vertice in LISTVER:
                ODATA.verts.ensure_lookup_table()
                if ODATA.verts[vertice].select:
                    ODATA.verts[vertice].co = (
                        (((random.randrange(VALMIN[0], VALMAX[0], 1)) * FACTOR) / 1000) + ODATA.verts[vertice].co[0],
                        (((random.randrange(VALMIN[1], VALMAX[1], 1)) * FACTOR) / 1000) + ODATA.verts[vertice].co[1],
                        (((random.randrange(VALMIN[2], VALMAX[2], 1)) * FACTOR) / 1000) + ODATA.verts[vertice].co[2]
                    )


class OBJECT_OT_add_object(bpy.types.Operator):
    """Add a Mesh Object"""
    bl_idname = "mesh.random_vertices"
    bl_label = "Random Vertices"
    bl_description = "Random Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    VGFILTER = bpy.props.BoolProperty(name="Vertex Group", default=False)
    FACTOR = bpy.props.FloatProperty(name="Factor", default=1)
    VALMIN = bpy.props.IntVectorProperty(name="Min XYZ", default=(0, 0, 0))
    VALMAX = bpy.props.IntVectorProperty(name="Max XYZ", default=(1, 1, 1))

    def execute(self, context):

        add_object(self, context, self.VALMIN, self.VALMAX, self.FACTOR, self.VGFILTER)

        return {'FINISHED'}


class random_help(bpy.types.Operator):
    bl_idname = 'help.random_vert'
    bl_label = ''

    def draw(self, context):
        layout = self.layout
        layout.label('To use:')
        layout.label('Make a selection or selection of Verts.')
        layout.label('Randomize displaced positions')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)

# Registration


def add_oscRandVerts_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_object.bl_idname,
        text="Random Vertices",
        icon="PLUGIN")


def register():
    bpy.utils.register_class(OBJECT_OT_add_object)
    bpy.types.VIEW3D_MT_transform.append(add_oscRandVerts_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_object)
    bpy.types.VIEW3D_MT_transform.remove(add_oscRandVerts_button)


if __name__ == '__main__':
    register()
