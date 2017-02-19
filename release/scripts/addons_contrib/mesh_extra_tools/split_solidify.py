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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ------ ------
bl_info = {
    'name': 'Split Solidify',
    'author': 'zmj100, updated by zeffii to bmesh ',
    'version': (0, 1, 2),
    'blender': (2, 7, 7),
    'location': 'View3D > Tool Shelf',
    'description': '',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'}

import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty
import random
from math import cos
import bmesh

# define the functions
def f_(self, list_0):

    b_rnd = self.b_rnd
    rnd = self.rnd
    opp = self.opp
    th = self.th
    b_del = self.b_del
    en0 = self.en0

    bm = self.bm

    for fi in list_0:
        bm.faces.ensure_lookup_table()
        f = bm.faces[fi]
        list_1 = []
        list_2 = []

        if b_rnd:
            d = rnd * random.randrange(0, 10)
        elif not b_rnd:
            d = opp

# add new verts.
        for vi in f.verts:
            bm.verts.ensure_lookup_table()
            v = bm.verts[vi.index]

            if en0 == 'opt0':
                p1 = (v.co).copy() + ((f.normal).copy() * d)      # out
                p2 = (v.co).copy() + ((f.normal).copy() * (d - th))      # in
            elif en0 == 'opt1':
                ang = ((v.normal).copy()).angle((f.normal).copy())
                h = th / cos(ang)
                p1 = (v.co).copy() + ((f.normal).copy() * d)
                p2 = p1 + (-h * (v.normal).copy())

            v1 = bm.verts.new(p1)
            v2 = bm.verts.new(p2)
            v1.select = False
            v2.select = False
            list_1.append(v1)
            list_2.append(v2)

# add new faces, allows faces with more than 4 verts.
        n = len(list_1)

        k = bm.faces.new(list_1)
        k.select = False
        for i in range(n):
            j = (i + 1) % n
            vseq = list_1[i], list_2[i], list_2[j], list_1[j]
            k = bm.faces.new(vseq)
            k.select = False

        list_2.reverse()
        k = bm.faces.new(list_2)
        k.select = False
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bmesh.update_edit_mesh(self.me, True)


class sp_sol_op0(bpy.types.Operator):

    bl_idname = 'sp_sol.op0_id'
    bl_label = 'Split Solidify'
    bl_description = 'Split & Solidify selected Faces'
    bl_options = {'REGISTER', 'UNDO'}

    opp = FloatProperty(name='', default=0.4, min=-
                        100.0, max=100.0, step=1, precision=3)
    th = FloatProperty(name='', default=0.04, min=-
                       100.0, max=100.0, step=1, precision=3)
    rnd = FloatProperty(name='', default=0.06, min=-
                        10.0, max=10.0, step=1, precision=3)

    b_rnd = BoolProperty(name='Random', default=False)
    b_del = BoolProperty(name='Delete original faces', default=True)

    en0 = EnumProperty(items=(('opt0', 'Face', ''),
                              ('opt1', 'Vertex', '')),
                       name='Normal',
                       default='opt0')

    def draw(self, context):

        layout = self.layout
        layout.label('Normal:')
        layout.prop(self, 'en0', expand=True)
        layout.prop(self, 'b_rnd')

        if not self.b_rnd:
            layout.label('Distance:')
            layout.prop(self, 'opp')
        elif self.b_rnd:
            layout.label('Random distance:')
            layout.prop(self, 'rnd')

        layout.label('Thickness:')
        layout.prop(self, 'th')
        layout.prop(self, 'b_del')

    def execute(self, context):

        obj = bpy.context.active_object
        self.me = obj.data
        self.bm = bmesh.from_edit_mesh(self.me)
        self.me.update()

        list_0 = [f.index for f in self.bm.faces if f.select]

        if len(list_0) == 0:
            self.report({'INFO'}, 'No faces selected')
            return {'CANCELLED'}
        elif len(list_0) != 0:

            f_(self, list_0)
            context.tool_settings.mesh_select_mode = (True, True, True)
            if self.b_del:
                bpy.ops.mesh.delete(type='FACE')
            else:
                pass
            return {'FINISHED'}


class solidify_help(bpy.types.Operator):
    bl_idname = 'help.solidify'
    bl_label = ''

    def draw(self, context):
        layout = self.layout
        layout.label('To use:')
        layout.label('Make a selection or selection of Faces.')
        layout.label('Split Faces & Extrude results')
        layout.label('Similar to a shatter/explode effect')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)
# ------ ------
class_list = [sp_sol_op0]

# ------ register ------
def register():
    for c in class_list:
        bpy.utils.register_class(c)

# ------ unregister ------
def unregister():
    for c in class_list:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
