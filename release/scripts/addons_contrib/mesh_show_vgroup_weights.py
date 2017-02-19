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

# <pep8 compliant> (Thanks to CodemanX on IRC)

bl_info = {
    "name": "Show Vertex Groups/Weights",
    "author": "Jason van Gumster (Fweeb), Bartius Crouch, CoDEmanX",
    "version": (0, 7, 2),
    "blender": (2, 65, 4),
    "location": "3D View > Properties Region > Show Weights",
    "description": "Finds the vertex groups of a selected vertex "
        "and displays the corresponding weights",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Modeling/Show_Vertex_Group_Weights",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Mesh"}

#TODO - Add button for selecting vertices with no groups


import bpy, bmesh, bgl, blf, mathutils


# Borrowed/Modified from Bart Crouch's old Index Visualizer add-on
def calc_callback(self, context):
    #polling
    if context.mode != "EDIT_MESH" or len(context.active_object.vertex_groups) == 0:
        return

    # get color info from theme
    acol = context.user_preferences.themes[0].view_3d.editmesh_active
    tcol = (acol[0] * 0.85, acol[1] * 0.85, acol[2] * 0.85)

    # get screen information
    mid_x = context.region.width / 2.0
    mid_y = context.region.height / 2.0
    width = context.region.width
    height = context.region.height

    # get matrices
    view_mat = context.space_data.region_3d.perspective_matrix
    ob_mat = context.active_object.matrix_world
    total_mat = view_mat * ob_mat

    # calculate location info
    texts = []
    locs = []
    weights  = []
    me = context.active_object.data
    bm = bmesh.from_edit_mesh(me)
    dvert_lay = bm.verts.layers.deform.active

    verts_max = context.scene.show_vgroups_weights_limit
    verts_used = []

    for elem in reversed(bm.select_history):
        if not isinstance(elem, bmesh.types.BMVert): #or elem.hide:
            continue
        if bm.select_history.active == elem:
            locs.append([acol[0], acol[1], acol[2], elem.index, elem.co.to_4d()])
        else:
            locs.append([tcol[0], tcol[1], tcol[2], elem.index, elem.co.to_4d()])
        dvert = elem[dvert_lay]
        for vgroup in context.active_object.vertex_groups:
            if vgroup.index in dvert.keys():
                weights += [elem.index, vgroup.index, dvert[vgroup.index]]
        verts_used.append(elem)
        verts_max -= 1
        if verts_max <= 0:
            break

    for v in bm.verts:
        if v.select and v not in verts_used: #XXX Should check v.hide here, but it doesn't work
            if isinstance(bm.select_history.active, bmesh.types.BMVert) and bm.select_history.active.index == v.index:
                locs.append([acol[0], acol[1], acol[2], v.index, v.co.to_4d()])
            else:
                locs.append([tcol[0], tcol[1], tcol[2], v.index, v.co.to_4d()])
            dvert = v[dvert_lay]
            for vgroup in context.active_object.vertex_groups:
                if vgroup.index in dvert.keys():
                    weights += [v.index, vgroup.index, dvert[vgroup.index]]
            verts_max -= 1
            if verts_max <= 0:
                break


    for loc in locs:
        vec = total_mat * loc[4] # order is important
        # dehomogenise
        vec = mathutils.Vector((vec[0] / vec[3], vec[1] / vec[3], vec[2] / vec[3]))
        x = int(mid_x + vec[0] * width / 2.0)
        y = int(mid_y + vec[1] * height / 2.0)
        texts += [loc[0], loc[1], loc[2], loc[3], x, y, 0]

    # store as ID property in mesh
    context.active_object.data["show_vgroup_verts"] = texts
    context.active_object.data["show_vgroup_weights"] = weights


# draw in 3d-view
def draw_callback(self, context):
    # polling
    if context.mode != "EDIT_MESH" or len(context.active_object.vertex_groups) == 0:
        return
    # retrieving ID property data
    try:
        texts = context.active_object.data["show_vgroup_verts"]
        weights = context.active_object.data["show_vgroup_weights"]
    except:
        return
    if not texts:
        return

    bm = bmesh.from_edit_mesh(context.active_object.data)

    if bm.select_mode == {'VERT'} and bm.select_history.active is not None:
        active_vert = bm.select_history.active
    else:
        active_vert = None

    # draw
    blf.size(0, 13, 72)
    blf.enable(0, blf.SHADOW)
    blf.shadow(0, 3, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(0, 2, -2)
    for i in range(0, len(texts), 7):
        bgl.glColor3f(texts[i], texts[i+1], texts[i+2])
        blf.position(0, texts[i+4], texts[i+5], texts[i+6])
        blf.draw(0, "Vertex " + str(int(texts[i+3])) + ":")
        font_y = texts[i+5]
        group_name = ""
        for j in range(0, len(weights), 3):
            if int(weights[j]) == int(texts[i+3]):
                font_y -= 13
                blf.position(0, texts[i+4] + 10, font_y, texts[i+6])
                for group in context.active_object.vertex_groups:
                    if group.index == int(weights[j+1]):
                        group_name = group.name
                        break
                blf.draw(0, group_name + ": %.3f" % weights[j+2])
        if group_name == "":
            font_y -= 13
            blf.position(0, texts[i+4] + 10, font_y, texts[i+6])
            blf.draw(0, "No Groups")

    # restore defaults
    blf.disable(0, blf.SHADOW)


# operator
class ShowVGroupWeights(bpy.types.Operator):
    bl_idname = "view3d.show_vgroup_weights"
    bl_label = "Show Vertex Group Weights"
    bl_description = "Toggle the display of the vertex groups and weights for selected vertices"

    _handle_calc = None
    _handle_draw = None

    @staticmethod
    def handle_add(self, context):
        ShowVGroupWeights._handle_calc = bpy.types.SpaceView3D.draw_handler_add(
            calc_callback, (self, context), 'WINDOW', 'POST_VIEW')
        ShowVGroupWeights._handle_draw = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_remove():
        if ShowVGroupWeights._handle_calc is not None:
            bpy.types.SpaceView3D.draw_handler_remove(ShowVGroupWeights._handle_calc, 'WINDOW')
        if ShowVGroupWeights._handle_draw is not None:
            bpy.types.SpaceView3D.draw_handler_remove(ShowVGroupWeights._handle_draw, 'WINDOW')
        ShowVGroupWeights._handle_calc = None
        ShowVGroupWeights._handle_draw = None

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            if not context.scene.show_vgroups_weights:
                # operator is called and not running, start everything
                ShowVGroupWeights.handle_add(self, context)
                context.scene.show_vgroups_weights = True
            else:
                # operator is called again, stop displaying
                ShowVGroupWeights.handle_remove()
                context.scene.show_vgroups_weights = False
                clear_properties(full=False)
            context.area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, can't run operator")
            return {'CANCELLED'}

class VGroupsWeights(bpy.types.PropertyGroup):
    vgroup = bpy.props.IntProperty()
    weight = bpy.props.FloatProperty(min=0.0, max=1.0)

class AssignVertexWeight(bpy.types.Operator):
    bl_idname = "mesh.vertex_group_assign"
    bl_label = "Assign Weights"
    bl_description = "Assign weights for all of the groups on a specific vertex"

    index = bpy.props.IntProperty()

    vgroup_weights = bpy.props.CollectionProperty(
        description="Vertex Group Weights",
        type=VGroupsWeights)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        me = context.active_object.data
        bm = bmesh.from_edit_mesh(me)
        dvert_lay = bm.verts.layers.deform.active
        weights = {}
        for item in self.vgroup_weights:
            weights[item.vgroup] = item.weight

        for v in bm.verts:
            if v.index == self.index:
                dvert = v[dvert_lay]
                for vgroup in dvert.keys():
                    dvert[vgroup] = weights[vgroup]
                break
        context.area.tag_redraw()
        return {'FINISHED'}


class RemoveFromVertexGroup(bpy.types.Operator):
    bl_idname = "mesh.vertex_group_remove"
    bl_label = "Remove Vertex from Group"
    bl_description = "Remove a specific vertex from a specific vertex group"

    #XXX abusing vector props here a bit; the first element is the vert index and the second is the group index
    vert_and_group = bpy.props.IntVectorProperty(name = "Vertex and Group to remove", size = 2)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        # Save current selection
        selected_verts = []
        for v in bm.verts:
            if v.select is True:
                selected_verts.append(v.index)
                if v.index != self.vert_and_group[0]:
                    v.select = False

        ob.vertex_groups.active_index = self.vert_and_group[1]
        bpy.ops.object.vertex_group_remove_from()

        # Re-select vertices
        for v in bm.verts:
            if v.index in selected_verts:
                v.select = True

        #XXX Hacky, but there's no other way to update the UI panels
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


class AddToVertexGroup(bpy.types.Operator):
    bl_idname = "mesh.vertex_group_add"
    bl_label = "Add Vertex to Group"
    bl_description = "Add a specific vertex to a specific vertex group"

    def avail_vgroups(self, context):
        if context is None:
            return []
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        dvert_lay = bm.verts.layers.deform.active
        items = []
        self.vertex = bm.select_history.active.index

        dvert = bm.select_history.active[dvert_lay]

        #XXX since we need an identifier here, user won't be able to add a vgroup with that name ('-1')
        #XXX could check against vgroup names and find an unused name, but it's a rare case after all.
        items.append(("-1", "New Vertex Group", "Add a new vertex group to the active object", -1))

        for i in ob.vertex_groups:
            if i.index not in dvert.keys():
                items.append((i.name, i.name, str(i.index), i.index))

        return items

    vertex = bpy.props.IntProperty()
    available_vgroups = bpy.props.EnumProperty(items=avail_vgroups, name="Available Groups")

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        #print(self.available_vgroups)

        # Save current selection
        selected_verts = []
        for v in bm.verts:
            if v.select is True:
                selected_verts.append(v.index)
                if v.index != self.vertex:
                    v.select = False

        weight = context.tool_settings.vertex_group_weight
        context.tool_settings.vertex_group_weight = 1.0
        if self.available_vgroups == "-1":
            bpy.ops.object.vertex_group_assign(new=True) #XXX Assumes self.vertex is the active vertex
        else:
            bpy.ops.object.vertex_group_set_active(group = self.available_vgroups)
            bpy.ops.object.vertex_group_assign() #XXX Assumes self.vertex is the active vertex
        context.tool_settings.vertex_group_weight = weight

        # Re-select vertices
        for v in bm.verts:
            if v.index in selected_verts:
                v.select = True

        #XXX Hacky, but there's no other way to update the UI panels
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


class PanelShowWeights(bpy.types.Panel):
    bl_label = "Show Weights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        dvert_lay = bm.verts.layers.deform.active

        row = layout.row(align=True)

        text = "Show" if not context.scene.show_vgroups_weights else "Hide"
        row.operator(ShowVGroupWeights.bl_idname, text=text)
        row.prop(context.scene, "show_vgroups_weights_limit")

        if len(ob.vertex_groups) > 0:
            # Active vertex
            active_vert = bm.select_history.active
            sub = layout.box()
            col = sub.column(align = True)
            if bm.select_mode == {'VERT'} and active_vert is not None:
                col.label(text = "Active Vertex")
                row = col.row()
                row.label(text = "Vertex " + str(active_vert.index) + ":")
                row.operator_menu_enum("mesh.vertex_group_add", "available_vgroups", text = "Add Group", icon = 'GROUP_VERTEX')
                has_groups = False
                vgroup_weights = []

                for i in me.vertices:
                    if i.index == active_vert.index:
                        vgroup_weights_index = i.index
                        for j in range(len(i.groups)):
                            for k in ob.vertex_groups:
                                if k.index == i.groups[j].group:
                                    has_groups = True
                                    split = col.split(percentage = 0.90, align = True)
                                    vgroup_weights.append((k.index, i.groups[j].weight))
                                    row = split.row(align = True)
                                    row.prop(i.groups[j], "weight", text = k.name, slider = True, emboss = not k.lock_weight)
                                    row = split.row(align = True)
                                    row.operator("mesh.vertex_group_remove", text="", icon='X').vert_and_group = (i.index, k.index)

                if not has_groups:
                    col.label(text = "    No Groups")
                else:
                    props = col.operator("mesh.vertex_group_assign")
                    props.index = vgroup_weights_index

                    for vgroup, weight in vgroup_weights:
                        item = props.vgroup_weights.add()
                        item.vgroup = vgroup
                        item.weight = weight

                layout.separator()
            else:
                col.label(text = "No Active Vertex")
            layout.prop(context.window_manager, "show_vgroups_show_all", toggle = True)
            # All selected vertices (except for the active vertex)
            if context.window_manager.show_vgroups_show_all:
                for v in bm.verts:
                    if v.select:
                        if active_vert is not None and v.index == active_vert.index:
                            continue
                        sub = layout.box()
                        col = sub.column(align = True)
                        col.label(text = "Vertex " + str(v.index) + ":")
                        has_groups = False
                        vgroup_weights = []
                        for i in me.vertices:
                            if i.index == v.index:
                                vgroup_weights_index = i.index
                                for j in range(len(i.groups)):
                                    for k in ob.vertex_groups:
                                        if k.index == i.groups[j].group:
                                            has_groups = True
                                            split = col.split(percentage = 0.90, align = True)
                                            vgroup_weights.append((k.index, i.groups[j].weight))
                                            row = split.row(align = True)
                                            row.prop(i.groups[j], "weight", text = k.name, slider = True, emboss = not k.lock_weight)
                                            row = split.row(align = True)
                                            row.operator("mesh.vertex_group_remove", text="", icon='X').vert_and_group = (i.index, k.index)
                        if not has_groups:
                            col.label(text = "    No Groups")
                        else:
                            props = col.operator("mesh.vertex_group_assign")
                            props.index = vgroup_weights_index

                            for vgroup, weight in vgroup_weights:
                                item = props.vgroup_weights.add()
                                item.vgroup = vgroup
                                item.weight = weight

        else:
            layout.label(text = "No Groups")


def create_properties():
    bpy.types.WindowManager.show_vgroups_show_all = bpy.props.BoolProperty(
        name = "Show All Selected Vertices",
        description = "Show all vertices with vertex groups assigned to them",
        default=False)

    bpy.types.Mesh.assign_vgroup = bpy.props.StringProperty()

    bpy.types.Scene.show_vgroups_weights = bpy.props.BoolProperty(
        name="Show Vertex Groups/Weights",
        default=False)

    bpy.types.Scene.show_vgroups_weights_limit = bpy.props.IntProperty(
        name="Limit",
        description="Maximum number of weight overlays to draw",
        default=20,
        min=1,
        max=1000,
        soft_max=100)

# removal of ID-properties when script is disabled
def clear_properties(full=True):

    if bpy.context.active_object is not None:
        me = bpy.context.active_object.data

        if hasattr(me, "show_vgroup_verts"):
            del me["show_vgroup_verts"]
        if hasattr(me, "show_vgroup_weights"):
            del me["show_vgroup_weights"]

    if full:
        del bpy.types.WindowManager.show_vgroups_show_all
        del bpy.types.Mesh.assign_vgroup
        del bpy.types.Scene.show_vgroups_weights
        del bpy.types.Scene.show_vgroups_weights_limit

def register():
    bpy.utils.register_module(__name__)
    create_properties()

def unregister():
    ShowVGroupWeights.handle_remove()
    bpy.utils.unregister_module(__name__)
    clear_properties()

if __name__ == "__main__":
    register()
