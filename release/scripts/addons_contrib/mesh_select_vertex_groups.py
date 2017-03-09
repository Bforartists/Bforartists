# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Select Vertex Groups",
    "author": "Martin Ellison",
    "version": (1, 0),
    "blender": (2, 71, 0),
    "location": "Toolbox",
    "description": "Finds all the vertex groups that chosen verts are in, & any verts that are not in any group",
    "warning": "Buggy", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Modeling/Select_Vertex_Groups",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Mesh"}

"""
This script finds all the vertex groups that chosen vertexes are in, and any vertexes that are not in any vertex group.

This is useful for cleaning up a mesh if vertex groups under animation go off to the wrong place (because they are in a vertex group that they should not be in, or not in the vertex group that they should be in).

How to use:
1. select a mesh and get into edit mode.
2. by default it will use all vertexes; alternatively, select vertexes of interest and click on 'use selected vertexes'. Note that subsequent selections and deselections of vertexes will not change the set of vertexes to be used, you need to click on these buttons again to do that.
3. click on 'select' and 'deselect' buttons for listed vertex groups, and for no vertex group, to select and deselect vertexes.

This only lists vertex groups that have used vertexes.

You may want to use the mesh select/deselect all (keyboard A) operator to start.

Once you have the right vertexes selected, you can use the standard vertex groups property editor to add them to or remove them from the desired vertex groups.
"""


import bpy
from bpy.props import *

global use_selected_only, used_vertexes, the_mesh, vertex_usage
use_selected_only = False
used_vertexes = set()
the_mesh = None
vertex_usage = ''

class UseAll(bpy.types.Operator):
    bl_idname = "mesh.primitive_fvg_useall"
    bl_label = "Use all Vertexes"
    bl_register = True
    bl_undo = True
    #limit = FloatProperty(name="limit", description="Ignore weights under this limit.", default= 0.01, min = 0.0, max = 1.0, soft_min=0.0, soft_max=1.0)

    def execute(self, context):
        global use_selected_only
        use_selected_only = False
        bpy.ops.object.editmode_toggle()
        set_used()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

class UseSelected(bpy.types.Operator):
    bl_idname = "mesh.primitive_fvg_useselected"
    bl_label = "Use Selected Vertexes"
    bl_register = True
    bl_undo = True

    def execute(self, context):
        global use_selected_only
        use_selected_only = True
        bpy.ops.object.editmode_toggle()
        set_used()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

class SelectFound(bpy.types.Operator):
    bl_idname = "mesh.primitive_fvg_selfound"
    bl_label = "Select"
    bl_register = True
    bl_undo = True
    vertexgroup = bpy.props.StringProperty(name = 'vertexgroup', description = 'vertexgroup', default = '', options = set())

    def execute(self, context):
        global the_mesh
        bpy.ops.object.editmode_toggle()
        vertexgroup = self.properties.vertexgroup
        fv = found_verts(vertexgroup)
        for v in fv: v.select = True
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

class DeselectFound(bpy.types.Operator):
    bl_idname = "mesh.primitive_fvg_deselfound"
    bl_label = "Deselect"
    bl_register = True
    bl_undo = True
    vertexgroup = bpy.props.StringProperty(name = 'vertexgroup', description = 'vertexgroup', default = '', options = set())

    def execute(self, context):
        global the_mesh
        bpy.ops.object.editmode_toggle()
        vertexgroup = self.properties.vertexgroup
        fv = found_verts(vertexgroup)
        for v in fv: v.select = False
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

def set_used():
    global use_selected_only, used_vertexes, the_mesh, vertex_usage
    obj = bpy.context.active_object
    used_vertexes = set()
    if use_selected_only:
        for v in obj.data.vertices:
            if v.select: used_vertexes.add(v.index)
    else:
        for v in obj.data.vertices: used_vertexes.add(v.index)
    the_mesh = obj
    vertex_usage = '%d vertexes used' % (len(used_vertexes))


def make_groups(limit):
    global used_vertexes
    vgp = []
    vgdict = {}
    vgused = {}
    obj = bpy.context.active_object
    all_in_group = True
    for vg in obj.vertex_groups:
        vgdict[vg.index] = vg.name
    for v in obj.data.vertices:
        in_group = False
        if v.index in used_vertexes:
            for g in v.groups:
                gr = g.group
                w = g.weight
                if w > limit:
                    if not gr in vgused: vgused[gr] = 0
                    vgused[gr] += 1
                    in_group = True
        if not in_group: all_in_group = False
    if not all_in_group:
        vgp.append(("no group", "(No group)"))
    for gn in vgused.keys():
        name = vgdict[gn]
        vgp.append((name, '%s has %d vertexes' % (name, vgused[gn]) ))
    print("%d groups found\n" % len(vgp))
    return vgp

def found_verts(vertex_group):
    global used_vertexes
    vgfound = []
    obj = bpy.context.active_object
    if vertex_group == 'no group':
        for v in obj.data.vertices:
            if v.index in used_vertexes and (not v.groups):
                vgfound.append(v)
    else:
        vgnum = obj.vertex_groups.find(vertex_group)
        for v in obj.data.vertices:
            if v.index in used_vertexes:
                for g in v.groups:
                    if g.group == vgnum:
                        vgfound.append(v)
                        break

    print('%d vertexes found for %s' % (len(vgfound), vertex_group))
    return vgfound


class VIEW3D_PT_FixVertexGroups(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Select Vertex Groups"
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        if bpy.context.active_object:
            obj = bpy.context.active_object
            if obj.type == 'MESH' and obj.mode == 'EDIT': return True
        return False

    def draw(self, context):
        global use_selected_only, used_vertexes, the_mesh, vertex_usage

        if bpy.context.active_object:
            obj = bpy.context.active_object
            if obj.type == 'MESH' and obj.mode == 'EDIT':
                layout = self.layout
                use_all = layout.operator("mesh.primitive_fvg_useall", "Use all vertexes")
                layout.operator("mesh.primitive_fvg_useselected", "Use selected vertexes")
                if use_selected_only:
                    layout.label(text = 'Using selected vertexes.')
                else:
                    layout.label(text = 'Using all vertexes.')
                layout.label(vertex_usage)
                if len(used_vertexes) == 0 or obj is not the_mesh: set_used()
                #layout.prop(use_all, 'limit', slider = True)
                #groups = make_groups(use_all.limitval)
                groups = make_groups(0.01)
                for gp in groups:
                    layout.label(text = gp[1])
                    row = layout.row()
                    sel_op = row.operator("mesh.primitive_fvg_selfound", "Select")
                    sel_op.vertexgroup = gp[0]
                    desel_op = row.operator("mesh.primitive_fvg_deselfound", "Deselect")
                    desel_op.vertexgroup = gp[0]

classes = [UseAll, UseSelected, SelectFound, DeselectFound]

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    print('------ executing --------')
    register()
