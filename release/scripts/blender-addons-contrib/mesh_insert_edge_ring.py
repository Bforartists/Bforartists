# Simplified BSD License
#
# Copyright (c) 2012, Florian Meyer
# tstscr@web.de
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

bl_info = {
    "name": "Insert Edge Ring",
    "author": "tstscr (tstscr@web.de)",
    "version": (1, 0),
    "blender": (2, 64, 0),
    "location": "View3D > Edge Specials > Insert edge ring (Ctrl Alt R)",
    "description": "Insert an edge ring along the selected edge loop",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Mesh/Insert_Edge_Ring",
    "tracker_url": "https://developer.blender.org/T32424",
    "category": "Mesh"}


import bpy, bmesh, math
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from mathutils import Vector
from collections import deque
from bmesh.utils import vert_separate


def update(bme):
    bme.verts.index_update()
    bme.edges.index_update()

def selected_edges(component, invert=False):
    def is_vert(vert):
        if invert:
            return [e for e in component.link_edges if not e.select]
        return [e for e in component.link_edges if e.select]
    if type(component) == bmesh.types.BMVert:
        return is_vert(component)
    if type(component) == bmesh.types.BMEdge:
        edges = []
        for vert in component.verts:
            edges.extend(is_vert(vert))
        if component in edges:
            edges.remove(component)
        return edges

def edge_loop_from(v_start):

    def walk(vert, vert_loop=deque()):
        #print('from', vert.index)
        edges_select = selected_edges(vert)
        #print('length edges_select', len(edges_select))
        if not vert_loop:
            #print('inserting %d into vert_loop' %vert.index)
            vert_loop.append(vert)

        for edge in edges_select:
            other_vert = edge.other_vert(vert)
            #print('other_vert %d' %other_vert.index)

            edge_is_valid = True
            if edge.is_boundary \
            or other_vert in vert_loop \
            or len(edges_select) > 2 \
            or len(selected_edges(other_vert)) > 2:
                #print('is not valid')
                edge_is_valid = False

            if edge_is_valid:
                if vert == vert_loop[-1]:
                    #print('appending %d' %other_vert.index)
                    vert_loop.append(other_vert)
                else:
                    #print('prepending %d' %other_vert.index)
                    vert_loop.appendleft(other_vert)

                walk(other_vert, vert_loop)

        return vert_loop
    #####################################
    v_loop = walk(v_start)
    #print('returning', [v.index for v in v_loop])
    return v_loop


def collect_edge_loops(bme):
    edge_loops = []
    verts_to_consider = [v for v in bme.verts if v.select]

    while verts_to_consider:

        v_start = verts_to_consider[-1]
        #print('\nverts_to_consider', [v.index for v in verts_to_consider])
        edge_loop = edge_loop_from(v_start)
        #update(bme)
        #print('edge_loop', [v.index for v in edge_loop])
        for v in edge_loop:
            try:
                verts_to_consider.remove(v)
            except:
                print('tried to remove vert %d from verts_to_consider. \
                       Failed somehow' %v.index)

        if len(edge_loop) >= 3:
            edge_loops.append(edge_loop)
        else:
            for v in edge_loop:
                v.select = False

    if not verts_to_consider:
        #print('no more verts_to_consider')
        pass

    return edge_loops


def insert_edge_ring(self, context):
    def split_edge_loop(vert_loop):
        other_loop = deque()
        new_loop = deque()
        for vert in vert_loop:
            #print('OPERATING ON VERT', vert.index)
            edges = selected_edges(vert)
            v_new = bmesh.utils.vert_separate(vert, edges)
            #print('RIPPING vert %d into' %vert.index, [v.index for v in v_new][:], \
            #       'along edges', [e.index for e in edges])
            if not closed:
                if len(v_new) == 2:
                    other_loop.append([v for v in v_new if v != vert][0])
                else:
                    other_loop.append(vert)

            if closed:
                if not new_loop:
                    #print('start_new_loop')
                    new_loop.append(v_new[0])
                    other_loop.append(v_new[1])
                else:
                    neighbours = [e.other_vert(v_new[0]) for e in v_new[0].link_edges]
                    #print('neighbours', [n.index for n in neighbours])
                    for n in neighbours:
                        if n in new_loop and v_new[0] not in new_loop:
                            #print('v_detect')
                            new_loop.append(v_new[0])
                            other_loop.append(v_new[1])
                        if n in other_loop and v_new[0] not in other_loop:
                            #print('v_not_detect')
                            new_loop.append(v_new[1])
                            other_loop.append(v_new[0])

        return other_loop, new_loop

    def move_verts(vert_loop, other_vert_loop):

        ### Offsets ###
        def calc_offsets():
            #print('\nCALCULATING OFFSETS')
            offset = {}
            for i, vert in enumerate(vert_loop):
                edges_select = selected_edges(vert)
                edges_unselect = selected_edges(vert, invert=True)

                vert_opposite = other_vert_loop[i]
                edges_select_opposite = selected_edges(vert_opposite)
                edges_unselect_opposite = selected_edges(vert_opposite, invert=True)

                ### MESH END VERT
                if vert == other_vert_loop[0] or vert == other_vert_loop[-1]:
                    #print('vert %d is start-end in middle of mesh, \
                    #       does not need moving\n' %vert.index)
                    continue

                ### BOUNDARY VERT
                if len(edges_select) == 1:
                    #print('verts %d  %d are on boundary' \
                    #%(vert.index, other_vert_loop[i].index))
                    border_edge = [e for e in edges_unselect if e.is_boundary][0]
                    off = (border_edge.other_vert(vert).co - vert.co).normalized()
                    if self.direction == 'LEFT':
                        off *= 0
                    offset[vert] = off
                    #opposite vert
                    border_edge_opposite = [e for e in edges_unselect_opposite \
                                            if e.is_boundary][0]
                    off = (border_edge_opposite.other_vert(vert_opposite).co \
                           - vert_opposite.co).normalized()
                    if self.direction == 'RIGHT':
                        off *= 0
                    offset[vert_opposite] = off
                    continue

                ### MIDDLE VERT
                if len(edges_select) == 2:
                    #print('\nverts %d  %d are in middle of loop' \
                    #%(vert.index, other_vert_loop[i].index))
                    tangents = [e.calc_tangent(e.link_loops[0]) for e in edges_select]
                    off = (tangents[0] + tangents[1]).normalized()
                    angle = tangents[0].angle(tangents[1])
                    if self.even:
                        off += off * angle * 0.263910
                    if self.direction == 'LEFT':
                        off *= 0
                    offset[vert] = off
                    #opposite vert
                    tangents = [e.calc_tangent(e.link_loops[0]) \
                                for e in edges_select_opposite]
                    off = (tangents[0] + tangents[1]).normalized()
                    #angle= tangents[0].angle(tangents[1])
                    if self.even:
                        off += off * angle * 0.263910
                    if self.direction == 'RIGHT':
                        off *= 0
                    offset[vert_opposite] = off
                    continue

            return offset

        ### Moving ###
        def move(offsets):
            #print('\nMOVING VERTS')
            for vert in offsets:
                vert.co += offsets[vert] * self.distance

        offsets = calc_offsets()
        move(offsets)

    def generate_new_geo(vert_loop, other_vert_loop):
        #print('\nGENERATING NEW GEOMETRY')

        for i, vert in enumerate(vert_loop):
            if vert == other_vert_loop[i]:
                continue
            edge_new = bme.edges.new([vert, other_vert_loop[i]])
            edge_new.select = True

        bpy.ops.mesh.edge_face_add()

    #####################################################################################
    #####################################################################################
    #####################################################################################

    bme = bmesh.from_edit_mesh(context.object.data)

    ### COLLECT EDGE LOOPS ###
    e_loops = collect_edge_loops(bme)

    for e_loop in e_loops:

        #check for closed loop - douple vert at start-end
        closed = False
        edges_select = selected_edges(e_loop[0])
        for e in edges_select:
            if e_loop[-1] in e.verts:
                closed = True

        ### SPLITTING OF EDGES
        other_vert_loop, new_loop = split_edge_loop(e_loop)
        if closed:
            e_loop = new_loop

        ### MOVE RIPPED VERTS ###
        move_verts(e_loop, other_vert_loop)

        ### GENERATE NEW GEOMETRY ###
        if self.generate_geo:
            generate_new_geo(e_loop, other_vert_loop)

    update(bme)

###########################################################################
# OPERATOR
class MESH_OT_Insert_Edge_Ring(Operator):
    """insert_edge_ring"""
    bl_idname = "mesh.insert_edge_ring"
    bl_label = "Insert edge ring"
    bl_description = "Insert an edge ring along the selected edge loop"
    bl_options = {'REGISTER', 'UNDO'}

    distance = FloatProperty(
            name="distance",
            default=0.01,
            min=0, soft_min=0,
            precision=4,
            description="distance to move verts from original location")

    even = BoolProperty(
            name='even',
            default=True,
            description='keep 90 degrees angles straight')

    generate_geo = BoolProperty(
            name='Generate Geo',
            default=True,
            description='Fill edgering with faces')

    direction = EnumProperty(
            name='direction',
            description='Direction in which to expand the edge_ring',
            items={
            ('LEFT', '<|', 'only move verts left of loop (arbitrary)'),
            ('CENTER', '<|>', 'move verts on both sides of loop'),
            ('RIGHT', '|>', 'only move verts right of loop (arbitrary)'),
            },
            default='CENTER')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.prop(self, 'distance', slider=False)
        col.prop(self, 'even', toggle=True)
        col.prop(self, 'generate_geo', toggle=True)
        col.separator()
        col.label(text='Direction')
        row = layout.row(align=True)
        row.prop(self, 'direction', expand=True)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        #print('\nInserting edge ring')
        insert_edge_ring(self, context)
        return {'FINISHED'}

def insert_edge_ring_button(self, context):
    self.layout.operator(MESH_OT_Insert_Edge_Ring.bl_idname,
                         text="Insert edge ring")
###########################################################################
# REGISTRATION

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(insert_edge_ring_button)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new('mesh.insert_edge_ring', \
                                  'R', 'PRESS', ctrl=True, alt=True)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(insert_edge_ring_button)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps["3D View"]
        for kmi in km.keymap_items:
            if kmi.idname == 'mesh.insert_edge_ring':
                km.keymap_items.remove(kmi)
                break

if __name__ == "__main__":
    register()