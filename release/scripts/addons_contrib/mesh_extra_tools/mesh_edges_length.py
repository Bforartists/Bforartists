bl_info = {
    'name': "set edges length",
    'description': "edges length",
    'author': "Giuseppe De Marco [BlenderLab] inspired by NirenYang",
    'version': (0, 1, 0),
    'blender': (2, 7, 0, 5),
    'location': '[Toolbar][Tools][Mesh Tools]: set Length(Shit+Alt+E)',
    'warning': "",
    'category': 'Mesh',
    "wiki_url": "",
    "tracker_url": "",
}


import bpy
import bmesh
import mathutils
from bpy.props import BoolProperty, FloatProperty, EnumProperty, StringProperty

edge_length_debug = False
_error_message = 'Please select one or more edge to fill select_history'

def set_edge_length(mesh, edge_index, edge_length=1.0):
    """
    Scales the edge to match the edge length provided as an argument.

    @param mesh: Mesh to modify edge on
    @param edge_index: Index of the edge
    @param edge_length: Final edge length
    """
    vt1 = mesh.edges[edge_index].vertices[0]
    vt2 = mesh.edges[edge_index].vertices[1]
    center = (mesh.vertices[vt1].co + mesh.vertices[vt2].co) * .5

    for v in (mesh.vertices[vt1], mesh.vertices[vt2]):
        # noinspection PyUnresolvedReferences
        new_co = (v.co - center).normalized() * (edge_length / 2.0)
        v.co = new_co + center


class EdgeEqualizeBase(bpy.types.Operator):
    bl_idname = "mesh.edgeequalizebase"
    bl_label = "Equalize Edges Length"
    """
    Never register this class as an operator, it's a base class used to keep
    polymorphism.
    """

    # --- This is here just to keep linter happy.
    # --- In child classes this is bpy.props.FloatProperty
    scale = 1.0

    def __init__(self):
        self.selected_edges = []
        self.edge_lengths = []
        self.active_edge_length = None

    @staticmethod
    def _get_active_edge_length(bm):
        """
        Finds the last selected edge.

        @param me: bmesh.types.BMesh object to look active edge in
        """
        active_edge_length = None
        bm.edges.ensure_lookup_table()
        for elem in reversed(bm.select_history):
            if isinstance(elem, bmesh.types.BMEdge):
                active_edge_length = elem.calc_length()
                break
        return active_edge_length

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        ob = context.object
        ob.update_from_editmode()

        # --- Get the mesh data
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)

        if len(me.edges) < 1:
            self.report({'ERROR'}, "This mesh has no edges!")
            return

        active_edge_length = self._get_active_edge_length(bm)
        if active_edge_length:
            self.active_edge_length = active_edge_length

        # --- gather selected edges
        edges = bpy.context.active_object.data.edges
        self.selected_edges = [i.index for i in edges if i.select is True]

        # --- if none report an error and quit
        if not self.selected_edges:
            self.report({'ERROR'}, "You have to select some edges!")
            return

        # --- gather lengths of the edges before the operator was applied
        for edge in self.selected_edges:
            vt1 = me.edges[edge].vertices[0]
            vt2 = me.edges[edge].vertices[1]
            a_to_b_vec = me.vertices[vt1].co - me.vertices[vt2].co
            self.edge_lengths.append(a_to_b_vec.length)

        length = self._get_target_length()
        if length is None:
            return {'CANCELLED'}

        self.scale = length

        return self.execute(context)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH' and (obj.mode == 'EDIT'):
            mesh = bmesh.new()
            mesh.from_mesh(obj.data)
            # --- Check if select_mode is 'EDGE'
            if context.scene.tool_settings.mesh_select_mode[1]:
                return True
        return False

    def do_equalize(self, ob, scale=1.0):
        me = ob.data
        current_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # target_length = self._get_target_length()

        for edge, base_length in zip(self.selected_edges, self.edge_lengths):
            set_edge_length(me, edge, self.scale)

        bpy.ops.object.mode_set(mode=current_mode, toggle=False)

    def _get_target_length(self):
        """
        Implement this method in your child classes to achieve different
        behaviours.
        """
        raise NotImplementedError()


class EdgeEqualizeAverageOperator(EdgeEqualizeBase):
    bl_idname = "mo.edge_equalize_average"
    bl_label = "Equalize edges length to average"
    bl_options = {'REGISTER', 'UNDO'}

    scale = bpy.props.FloatProperty(name="Length", unit="LENGTH")

    def _get_target_length(self):
        """
        Calculates the average length of all edges.
        """
        if not self.edge_lengths:
            return 0.0
        return sum(self.edge_lengths) / float(len(self.selected_edges))

    # noinspection PyUnusedLocal
    def execute(self, context):
        ob = bpy.context.object

        if ob.type != 'MESH':
            raise TypeError("Active object is not a Mesh")

        if ob:
            self.do_equalize(ob, self.scale)

        return {'FINISHED'}


class EdgeEqualizeShortestOperator(EdgeEqualizeBase):
    bl_idname = "mo.edge_equalize_short"
    bl_label = "Equalize edges length to shortest"
    bl_options = {'REGISTER', 'UNDO'}

    scale = bpy.props.FloatProperty(name="Length", unit="LENGTH")

    def _get_target_length(self):
        """
        Calculates the smallest length of all edges.
        """
        if not self.edge_lengths:
            return 0.0
        return min(self.edge_lengths)

    # noinspection PyUnusedLocal
    def execute(self, context):
        ob = bpy.context.object

        if ob.type != 'MESH':
            raise TypeError("Active object is not a Mesh")

        if ob:
            self.do_equalize(ob, self.scale)

        return {'FINISHED'}


class EdgeEqualizeLongestOperator(EdgeEqualizeBase):
    bl_idname = "mo.edge_equalize_long"
    bl_label = "Equalize edges length to longest"
    bl_options = {'REGISTER', 'UNDO'}

    scale = bpy.props.FloatProperty(name="Length", unit="LENGTH")

    def _get_target_length(self):
        """
        Calculates the biggest length of all edges.
        """
        if not self.edge_lengths:
            return 0.0
        return max(self.edge_lengths)

    def execute(self, context):
        ob = context.object

        if ob.type != 'MESH':
            raise TypeError("Active object is not a Mesh")

        if ob:
            self.do_equalize(ob, self.scale)

        return {'FINISHED'}


class EdgeEqualizeActiveOperator(EdgeEqualizeBase):
    bl_idname = "mo.edge_equalize_active"
    bl_label = "Equalize edges length to active"
    bl_options = {'REGISTER', 'UNDO'}

    scale = bpy.props.FloatProperty(name="Length", unit="LENGTH")

    def _get_target_length(self):
        """
        Calculates the active edge length.
        """
        if self.active_edge_length is None:
            self.report({'ERROR'}, "Failed to get the active edge!")
            return None

        return self.active_edge_length

    def execute(self, context):
        ob = context.object

        if ob.type != 'MESH':
            raise TypeError("Active object is not a Mesh")

        if ob:
            self.do_equalize(ob, self.scale)

        return {'FINISHED'}

class VIEW3D_MT_edit_mesh_edgelength(bpy.types.Menu):
    bl_label = "Match Edge Length"
    bl_description = "Edit Equal Edge Lengths"

    def draw(self, context):
        layout = self.layout

        layout.operator("mo.edge_equalize_average")
        layout.operator("mo.edge_equalize_short")
        layout.operator("mo.edge_equalize_long")
        layout.operator("mo.edge_equalize_active")

def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_edgelength")
    self.layout.separator()

def get_edge_vector(edge):
    verts = (edge.verts[0].co, edge.verts[1].co)

    # if verts[1] >= verts[0]:
    #vector = verts[1] - verts[0]
    # else:
    #vector = verts[0] - verts[1]
    vector = verts[1] - verts[0]
    return vector


def get_selected(bmesh_obj, geometry_type):
    """
    geometry type should be edges, verts or faces
    """
    selected = []
    for i in getattr(bmesh_obj, geometry_type):
        if i.select:
            selected.append(i)
    return tuple(selected)


def get_center_vector(verts):
    """
    verts = [mathutils.Vector((x,y,z)), mathutils.Vector((x,y,z))]
    """
    center_vector = mathutils.Vector((((verts[1][0] + verts[0][0]) / 2.), ((verts[1][1] + verts[0][1]) / 2.), ((verts[1][2] + verts[0][2]) / 2.)))
    return center_vector


class LengthSet(bpy.types.Operator):
    bl_idname = "object.mesh_edge_length_set"
    bl_label = "Set edge length"
    bl_description = "change One selected edge length"
    bl_options = {'REGISTER', 'UNDO'}

    old_length = StringProperty(name='originary length')  # , default = 0.00, unit = 'LENGTH', precision = 5, set = print(''))
    target_length = FloatProperty(name='length', default=0.00, unit='LENGTH', precision=5)

    # incremental = BoolProperty(\
    #    name="incremental",\
    #    default=False,\
    #    description="incremental")

    mode = EnumProperty(
        items=[
            ('fixed', 'fixed', 'fixed'),
            ('increment', 'increment', 'increment'),
            ('decrement', 'decrement', 'decrement'),
        ],
        name="mode")

    behaviour = EnumProperty(
        items=[
            ('proportional', 'proportional', 'Three'),
            #('invert', 'invert', 'Three'),
            ('clockwise', 'clockwise', 'One'),
            ('unclockwise', 'unclockwise', 'One'),
        ],
        name="Resize behaviour")

    originary_edge_length_dict = {}

    @classmethod
    def poll(cls, context):
        return (context.edit_object)

    def invoke(self, context, event):
        wm = context.window_manager

        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)

        bpy.ops.mesh.select_mode(type="EDGE")

        self.selected_edges = get_selected(bm, 'edges')

        if self.selected_edges:

            vertex_set = []

            for edge in self.selected_edges:
                vector = get_edge_vector(edge)

                if edge.verts[0].index not in vertex_set:
                    vertex_set.append(edge.verts[0].index)
                else:
                    self.report({'ERROR_INVALID_INPUT'}, 'edges with shared vertices not permitted. Use scale instead.')
                    return {'CANCELLED'}
                if edge.verts[1].index not in vertex_set:
                    vertex_set.append(edge.verts[1].index)
                else:
                    self.report({'ERROR_INVALID_INPUT'}, 'edges with shared vertices not permitted. Use scale instead.')
                    return {'CANCELLED'}

                # warning, it's a constant !
                verts_index = ''.join((str(edge.verts[0].index), str(edge.verts[1].index)))
                self.originary_edge_length_dict[verts_index] = vector
                self.old_length = str(vector.length)
        else:
            self.report({'ERROR'}, _error_message)
            return {'CANCELLED'}

        if edge_length_debug:
            self.report({'INFO'}, str(self.originary_edge_length_dict))

        if bpy.context.scene.unit_settings.system == 'IMPERIAL':
            # imperial conversion 2 metre conversion
            vector.length = (0.9144 * vector.length) / 3

        self.target_length = vector.length

        return wm.invoke_props_dialog(self)

    def execute(self, context):
        if edge_length_debug:
            self.report({'INFO'}, 'execute')

        bpy.ops.mesh.select_mode(type="EDGE")

        self.context = context

        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)

        self.selected_edges = get_selected(bm, 'edges')

        if not self.selected_edges:
            self.report({'ERROR'}, _error_message)
            return {'CANCELLED'}

        for edge in self.selected_edges:

            vector = get_edge_vector(edge)
            # what we shold see in originary length dialog field
            self.old_length = str(vector.length)

            vector.length = abs(self.target_length)
            center_vector = get_center_vector((edge.verts[0].co, edge.verts[1].co))

            verts_index = ''.join((str(edge.verts[0].index), str(edge.verts[1].index)))

            if edge_length_debug:
                self.report({'INFO'},
                            ' - '.join(('vector ' + str(vector),
                                        'originary_vector ' + str(self.originary_edge_length_dict[verts_index])
                                        )))

            verts = (edge.verts[0].co, edge.verts[1].co)

            if edge_length_debug:
                self.report({'INFO'},
                            '\n edge.verts[0].co ' + str(verts[0]) +
                            '\n edge.verts[1].co ' + str(verts[1]) +
                            '\n vector.length' + str(vector.length))

            # the clockwise direction have v1 -> v0, unclockwise v0 -> v1

            if self.target_length >= 0:
                if self.behaviour == 'proportional':
                    edge.verts[1].co = center_vector + vector / 2
                    edge.verts[0].co = center_vector - vector / 2

                    if self.mode == 'decrement':
                        edge.verts[0].co = (center_vector + vector / 2) - (self.originary_edge_length_dict[verts_index] / 2)
                        edge.verts[1].co = (center_vector - vector / 2) + (self.originary_edge_length_dict[verts_index] / 2)

                    elif self.mode == 'increment':
                        edge.verts[1].co = (center_vector + vector / 2) + self.originary_edge_length_dict[verts_index] / 2
                        edge.verts[0].co = (center_vector - vector / 2) - self.originary_edge_length_dict[verts_index] / 2

                elif self.behaviour == 'unclockwise':
                    if self.mode == 'increment':
                        edge.verts[1].co = verts[0] + (self.originary_edge_length_dict[verts_index] + vector)
                    elif self.mode == 'decrement':
                        edge.verts[0].co = verts[1] - (self.originary_edge_length_dict[verts_index] - vector)
                    else:
                        edge.verts[1].co = verts[0] + vector

                else:
                    if self.mode == 'increment':
                        edge.verts[0].co = verts[1] - (self.originary_edge_length_dict[verts_index] + vector)
                    elif self.mode == 'decrement':
                        edge.verts[1].co = verts[0] + (self.originary_edge_length_dict[verts_index] - vector)
                    else:
                        edge.verts[0].co = verts[1] - vector

            if bpy.context.scene.unit_settings.system == 'IMPERIAL':
                # yard conversion 2 metre conversion
                #vector.length = ( 3. * vector.length ) / 0.9144
                # metre 2 yard conversion
                #vector.length = ( 0.9144 * vector.length ) / 3.
                for mvert in edge.verts:
                    # school time: 0.9144 : 3 = X : mvert
                    mvert.co = (0.9144 * mvert.co) / 3

            if edge_length_debug:
                self.report({'INFO'},
                            '\n edge.verts[0].co' + str(verts[0]) +
                            '\n edge.verts[1].co' + str(verts[1]) +
                            '\n vector' + str(vector) + '\n v1 > v0:' + str((verts[1] >= verts[0])))

            bmesh.update_edit_mesh(obj.data, True)

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.separator()
    self.layout.label(text="Edges length:")
    row = self.layout.row(align=True)
    row.operator(LengthSet.bl_idname, "Set edges length")
    self.layout.separator()
    self.layout.menu("VIEW3D_MT_edit_mesh_edgelength")


class addarm_help(bpy.types.Operator):
    bl_idname = 'help.edge_length'
    bl_label = ''

    def draw(self, context):
        layout = self.layout
        layout.label('To use:')
        layout.label('Select a single edge')
        layout.label('Change length.')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)


def register():
    bpy.utils.register_class(LengthSet)
    bpy.utils.register_class(EdgeEqualizeBase)
    bpy.utils.register_class(EdgeEqualizeAverageOperator)
    bpy.utils.register_class(EdgeEqualizeShortestOperator)
    bpy.utils.register_class(EdgeEqualizeLongestOperator)
    bpy.utils.register_class(EdgeEqualizeActiveOperator)
    bpy.types.VIEW3D_PT_tools_meshedit.append(menu_func)

    # edge contextual edit menu ( CTRL + E )
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(menu_func)

    # hotkey
    kc = bpy.context.window_manager.keyconfigs.default.keymaps['Mesh']
    if LengthSet.bl_idname not in kc.keymap_items:
        kc.keymap_items.new(LengthSet.bl_idname, 'E', 'PRESS', shift=True, alt=True)


def unregister():
    bpy.utils.unregister_class(LengthSet)
    bpy.utils.register_class(EdgeEqualizeBase)
    bpy.utils.unregister_class(EdgeEqualizeAverageOperator)
    bpy.utils.unregister_class(EdgeEqualizeShortestOperator)
    bpy.utils.unregister_class(EdgeEqualizeLongestOperator)
    bpy.utils.unregister_class(EdgeEqualizeActiveOperator)
    bpy.types.VIEW3D_PT_tools_meshedit.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_func)

    # hotkey
    kc = bpy.context.window_manager.keyconfigs.default.keymaps['Mesh']
    if LengthSet.bl_idname in kc.keymap_items:
        kc.keymap_items.remove(kc.keymap_items[LengthSet.bl_idname])

if __name__ == "__main__":
    register()
