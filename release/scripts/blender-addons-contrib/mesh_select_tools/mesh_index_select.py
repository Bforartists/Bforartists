bl_info = {
    "name": "Select by index",
    "author": "liero",
    "version": (0, 2),
    "blender": (2, 55, 0),
    "location": "View3D > Tool Shelf",
    "description": "Select mesh data by index / area / length / cursor",
    "category": "Mesh"}

import bpy, mathutils
from mathutils import Vector

class SelVert(bpy.types.Operator):
    bl_idname = 'mesh.select_vert_index'
    bl_label = 'Verts'
    bl_description = 'Select vertices by index'
    bl_options = {'REGISTER', 'UNDO'}

    indice = bpy.props.FloatProperty(name='Selected', default=0, min=0, max=100, description='Percentage of selected edges', precision = 2, subtype = 'PERCENTAGE')
    delta = bpy.props.BoolProperty(name='Use Cursor', default=False, description='Select by Index / Distance to Cursor')
    flip = bpy.props.BoolProperty(name='Reverse Order', default=False, description='Reverse selecting order')

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'indice', slider=True)
        layout.prop(self,'delta')
        layout.prop(self,'flip')

    def execute(self, context):
        obj = bpy.context.object
        mode = [a for a in bpy.context.tool_settings.mesh_select_mode]
        if mode != [True, False, False]:
            bpy.context.tool_settings.mesh_select_mode = [True, False, False]
        ver = obj.data.vertices
        loc = context.scene.cursor_location
        sel = []
        for v in ver:
            d = v.co - loc
            sel.append((d.length, v.index))
        sel.sort(reverse=self.flip)
        bpy.ops.object.mode_set()
        valor = round(len(sel) / 100 * self.indice)
        if self.delta:
            for i in range(len(sel[:valor])):
                ver[sel[i][1]].select = True
        else:
            for i in range(len(sel[:valor])):
                if self.flip:
                    ver[len(sel)-i-1].select = True
                else:
                    ver[i].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

class SelEdge(bpy.types.Operator):
    bl_idname = 'mesh.select_edge_index'
    bl_label = 'Edges'
    bl_description = 'Select edges by index'
    bl_options = {'REGISTER', 'UNDO'}

    indice = bpy.props.FloatProperty(name='Selected', default=0, min=0, max=100, description='Percentage of selected edges', precision = 2, subtype = 'PERCENTAGE')
    delta = bpy.props.BoolProperty(name='Use Edges Length', default=False, description='Select Edges by Index / Length')
    flip = bpy.props.BoolProperty(name='Reverse Order', default=False, description='Reverse selecting order')

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'indice', slider=True)
        layout.prop(self,'delta')
        layout.prop(self,'flip')

    def execute(self, context):
        obj = bpy.context.object
        mode = [a for a in bpy.context.tool_settings.mesh_select_mode]
        if mode != [False, True, False]:
            bpy.context.tool_settings.mesh_select_mode = [False, True, False]
        ver = obj.data.vertices
        edg = obj.data.edges
        sel = []
        for e in edg:
            d = ver[e.vertices[0]].co - ver[e.vertices[1]].co
            sel.append((d.length, e.index))
        sel.sort(reverse=self.flip)
        bpy.ops.object.mode_set()
        valor = round(len(sel) / 100 * self.indice)
        if self.delta:
            for i in range(len(sel[:valor])):
                edg[sel[i][1]].select = True
        else:
            for i in range(len(sel[:valor])):
                if self.flip:
                    edg[len(sel)-i-1].select = True
                else:
                    edg[i].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

class SelFace(bpy.types.Operator):
    bl_idname = 'mesh.select_face_index'
    bl_label = 'Faces'
    bl_description = 'Select faces by index'
    bl_options = {'REGISTER', 'UNDO'}

    indice = bpy.props.FloatProperty(name='Selected', default=0, min=0, max=100, description='Percentage of selected faces', precision = 2, subtype = 'PERCENTAGE')
    delta = bpy.props.BoolProperty(name='Use Faces Area', default=False, description='Select Faces by Index / Area')
    flip = bpy.props.BoolProperty(name='Reverse Order', default=False, description='Reverse selecting order')

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'indice', slider=True)
        layout.prop(self,'delta')
        layout.prop(self,'flip')

    def execute(self, context):
        obj = bpy.context.object
        mode = [a for a in bpy.context.tool_settings.mesh_select_mode]
        if mode != [False, False, True]:
            bpy.context.tool_settings.mesh_select_mode = [False, False, True]
        fac = obj.data.polygons
        sel = []
        for f in fac:
            sel.append((f.area, f.index))
        sel.sort(reverse=self.flip)
        print (sel)
        bpy.ops.object.mode_set()
        valor = round(len(sel) / 100 * self.indice)
        if self.delta:
            for i in range(len(sel[:valor])):
                fac[sel[i][1]].select = True
        else:
            for i in range(len(sel[:valor])):
                if self.flip:
                    fac[len(sel)-i-1].select = True
                else:
                    fac[i].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

class GUI(bpy.types.Panel):
    bl_label = 'Select mesh data'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator('mesh.select_vert_index')
        row.operator('mesh.select_edge_index')
        row.operator('mesh.select_face_index')

def register():
    bpy.utils.register_class(SelVert)
    bpy.utils.register_class(SelEdge)
    bpy.utils.register_class(SelFace)
    bpy.utils.register_class(GUI)

def unregister():
    bpy.utils.unregister_class(SelVert)
    bpy.utils.unregister_class(SelEdge)
    bpy.utils.unregister_class(SelFace)
    bpy.utils.unregister_class(GUI)

if __name__ == '__main__':
    register()

