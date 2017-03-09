# -*- coding: utf-8 -*-

# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ------ ------
bl_info = {
    "name": "FilletPlus",
    "author": "Gert De Roost - original by zmj100",
    "version": (0, 4, 2),
    "blender": (2, 61, 0),
    "location": "View3D > Tool Shelf",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

# ------ ------
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty
import bmesh
from mathutils import Matrix
from math import cos, pi, degrees, sin, tan


def list_clear_(l):
    del l[:]
    return l


def get_adj_v_(list_):
    tmp = {}
    for i in list_:
        try:
            tmp[i[0]].append(i[1])
        except KeyError:
            tmp[i[0]] = [i[1]]
        try:
            tmp[i[1]].append(i[0])
        except KeyError:
            tmp[i[1]] = [i[0]]
    return tmp

# ------ ------


class f_buf():
    an = 0

# ------ ------


def f_(list_0, startv, vertlist, face, adj, n, out, flip, radius):

    dict_0 = get_adj_v_(list_0)
    list_1 = [[dict_0[i][0], i, dict_0[i][1]] for i in dict_0 if (len(dict_0[i]) == 2)][0]
    list_3 = []
    for elem in list_1:
        list_3.append(bm.verts[elem])
    list_2 = []

    p_ = list_3[1]
    p = (list_3[1].co).copy()
    p1 = (list_3[0].co).copy()
    p2 = (list_3[2].co).copy()

    vec1 = p - p1
    vec2 = p - p2

    ang = vec1.angle(vec2, any)
    f_buf.an = round(degrees(ang))

    # -- -- -- --
    if f_buf.an == 180 or f_buf.an == 0.0:
        return

    # -- -- -- --
    opp = adj

    if radius == False:
        h = adj * (1 / cos(ang * 0.5))
        adj_ = adj
    elif radius == True:
        h = opp / sin(ang * 0.5)
        adj_ = opp / tan(ang * 0.5)

    p3 = p - (vec1.normalized() * adj_)
    p4 = p - (vec2.normalized() * adj_)
    rp = p - ((p - ((p3 + p4) * 0.5)).normalized() * h)

    vec3 = rp - p3
    vec4 = rp - p4

    axis = vec1.cross(vec2)

    if out == False:
        if flip == False:
            rot_ang = vec3.angle(vec4)
        elif flip == True:
            rot_ang = vec1.angle(vec2)
    elif out == True:
        rot_ang = (2 * pi) - vec1.angle(vec2)

    for j in range(n + 1):
        new_angle = rot_ang * j / n
        mtrx = Matrix.Rotation(new_angle, 3, axis)
        if out == False:
            if flip == False:
                tmp = p4 - rp
                tmp1 = mtrx * tmp
                tmp2 = tmp1 + rp
            elif flip == True:
                p3 = p - (vec1.normalized() * opp)
                tmp = p3 - p
                tmp1 = mtrx * tmp
                tmp2 = tmp1 + p
        elif out == True:
            p4 = p - (vec2.normalized() * opp)
            tmp = p4 - p
            tmp1 = mtrx * tmp
            tmp2 = tmp1 + p

        v = bm.verts.new(tmp2)
        list_2.append(v)

    if flip == True:
        list_3[1:2] = list_2
    else:
        list_2.reverse()
        list_3[1:2] = list_2

    list_clear_(list_2)

    n1 = len(list_3)
    for t in range(n1 - 1):
        bm.edges.new([list_3[t], list_3[(t + 1) % n1]])

        v = bm.verts.new(p)
        bm.edges.new([v, p_])

    if face != None:
        for l in face.loops:
            if l.vert == list_3[0]:
                startl = l
                break
        vertlist2 = []
        if startl.link_loop_next.vert == startv:
            l = startl.link_loop_prev
            while len(vertlist) > 0:
                vertlist2.insert(0, l.vert)
                vertlist.pop(vertlist.index(l.vert))
                l = l.link_loop_prev
        else:
            l = startl.link_loop_next
            while len(vertlist) > 0:
                vertlist2.insert(0, l.vert)
                vertlist.pop(vertlist.index(l.vert))
                l = l.link_loop_next
        for v in list_3:
            vertlist2.append(v)
        bm.faces.new(vertlist2)

    bm.verts.remove(startv)
    list_3[1].select = 1
    list_3[-2].select = 1
    bm.edges.get([list_3[0], list_3[1]]).select = 1
    bm.edges.get([list_3[-1], list_3[-2]]).select = 1
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()

    me.update(calc_edges=True, calc_tessface=True)


def do_filletplus(pair):

    global inaction
    global flip

    list_0 = [list([e.verts[0].index, e.verts[1].index]) for e in pair]

    vertset = set([])
    bm.verts.ensure_lookup_table()
    vertset.add(bm.verts[list_0[0][0]])
    vertset.add(bm.verts[list_0[0][1]])
    vertset.add(bm.verts[list_0[1][0]])
    vertset.add(bm.verts[list_0[1][1]])

    v1, v2, v3 = vertset

    if len(list_0) != 2:
        self.report({'INFO'}, 'Two adjacent edges must be selected.')
        return
    else:
        inaction = 1
        vertlist = []
        found = 0
        for f in v1.link_faces:
            if v2 in f.verts and v3 in f.verts:
                found = 1
        if not(found):
            for v in [v1, v2, v3]:
                if v.index in list_0[0] and v.index in list_0[1]:
                    startv = v
            face = None
        else:
            for f in v1.link_faces:
                if v2 in f.verts and v3 in f.verts:
                    for v in f.verts:
                        if not(v in vertset):
                            vertlist.append(v)
                        if v in vertset and v.link_loops[0].link_loop_prev.vert in vertset and v.link_loops[0].link_loop_next.vert in vertset:
                            startv = v
                    face = f
        if out == True:
            flip = False
        f_(list_0, startv, vertlist, face, adj, n, out, flip, radius)


'''

# ------ panel 0 ------
class f_p0(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	#bl_idname = 'f_p0_id'
	bl_label = 'Fillet'
	bl_context = 'mesh_edit'

	def draw(self, context):
		layout = self.layout

		row = layout.split(0.80)
		row.operator('f.op0_id', text = 'Fillet plus')
		row.operator('f.op1_id', text = '?')
'''
# ------ operator 0 ------


class fillet_op0(bpy.types.Operator):
    bl_idname = 'fillet.op0_id'
    bl_label = 'Fillet'
    bl_description = 'Fillet ajoining edges'
    bl_options = {'REGISTER', 'UNDO'}

    adj = FloatProperty(name='', default=0.1, min=0.00001, max=100.0, step=1, precision=3)
    n = IntProperty(name='', default=3, min=1, max=100, step=1)
    out = BoolProperty(name='Outside', default=False)
    flip = BoolProperty(name='Flip', default=False)
    radius = BoolProperty(name='Radius', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout

        if f_buf.an == 180 or f_buf.an == 0.0:
            layout.label('Info:')
            layout.label('Angle equal to 0 or 180,')
            layout.label('can not fillet.')
        else:
            layout.prop(self, 'radius')
            if self.radius == True:
                layout.label('Radius:')
            elif self.radius == False:
                layout.label('Distance:')
            layout.prop(self, 'adj')
            layout.label('Number of sides:')
            layout.prop(self, 'n', slider=True)
            if self.n > 1:
                row = layout.row(align=False)
                row.prop(self, 'out')
                if self.out == False:
                    row.prop(self, 'flip')

    def execute(self, context):

        global inaction
        global bm, me, adj, n, out, flip, radius

        adj = self.adj
        n = self.n
        out = self.out
        flip = self.flip
        radius = self.radius

        inaction = 0

        ob_act = context.active_object
        me = ob_act.data
        bm = bmesh.from_edit_mesh(me)
#		e_mode = bpy.context.tool_settings.mesh_select_mode

        done = 1
        while done:
            tempset = set([])
            for v in bm.verts:
                if v.select:
                    tempset.add(v)
            done = 0
            for v in tempset:
                cnt = 0
                edgeset = set([])
                for e in v.link_edges:
                    if e.select:
                        edgeset.add(e)
                        cnt += 1
                if cnt == 2:
                    do_filletplus(edgeset)
                    done = 1
                    break
                    # return {'FINISHED'}
                if done:
                    break

        if inaction == 1:
            bpy.ops.mesh.select_all(action="DESELECT")
            for v in bm.verts:
                if len(v.link_edges) == 0:
                    bm.verts.remove(v)
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

# ------ operator 1 ------


class filletedgehelp(bpy.types.Operator):
    bl_idname = 'help.edge_fillet'
    bl_label = ''

    def draw(self, context):
        layout = self.layout
        layout.label('To use:')
        layout.label('Select two adjacent edges and press Fillet button.')
        layout.label('To Help:')
        layout.label('best used on flat plane.')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=350)

# ------ operator 2 ------


class fillet_op2(bpy.types.Operator):
    bl_idname = 'fillet.op2_id'
    bl_label = ''

    def execute(self, context):
        bpy.ops.f.op1_id('INVOKE_DEFAULT')
        return {'FINISHED'}
'''
# ------ ------
class_list = [ f_op0, f_op1, f_op2, f_p0]

# ------ register ------
def register():
	for c in class_list:
		bpy.utils.register_class(c)

# ------ unregister ------
def unregister():
	for c in class_list:
		bpy.utils.unregister_class(c)

# ------ ------
if __name__ == "__main__":
	register()
'''
