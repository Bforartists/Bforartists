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
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import bpy


class DataButtonsPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def poll(self, context):
        return context.mesh


class DATA_PT_context_mesh(DataButtonsPanel):
    bl_label = ""
    bl_show_header = False

    def draw(self, context):
        layout = self.layout

        ob = context.object
        mesh = context.mesh
        space = context.space_data

        split = layout.split(percentage=0.65)

        if ob:
            split.template_ID(ob, "data")
            split.itemS()
        elif mesh:
            split.template_ID(space, "pin_id")
            split.itemS()


class DATA_PT_normals(DataButtonsPanel):
    bl_label = "Normals"

    def draw(self, context):
        layout = self.layout

        mesh = context.mesh

        split = layout.split()

        col = split.column()
        col.itemR(mesh, "autosmooth")
        sub = col.column()
        sub.active = mesh.autosmooth
        sub.itemR(mesh, "autosmooth_angle", text="Angle")

        col = split.column()
        col.itemR(mesh, "vertex_normal_flip")
        col.itemR(mesh, "double_sided")


class DATA_PT_settings(DataButtonsPanel):
    bl_label = "Settings"

    def draw(self, context):
        layout = self.layout

        mesh = context.mesh

        split = layout.split()

        col = split.column()
        col.itemR(mesh, "texture_mesh")


class DATA_PT_vertex_groups(DataButtonsPanel):
    bl_label = "Vertex Groups"

    def poll(self, context):
        return (context.object and context.object.type in ('MESH', 'LATTICE'))

    def draw(self, context):
        layout = self.layout

        ob = context.object
        group = ob.active_vertex_group

        rows = 2
        if group:
            rows = 5

        row = layout.row()
        row.template_list(ob, "vertex_groups", ob, "active_vertex_group_index", rows=rows)

        col = row.column(align=True)
        col.itemO("object.vertex_group_add", icon='ICON_ZOOMIN', text="")
        col.itemO("object.vertex_group_remove", icon='ICON_ZOOMOUT', text="")

        col.itemO("object.vertex_group_copy", icon='ICON_COPY_ID', text="")
        if ob.data.users > 1:
            col.itemO("object.vertex_group_copy_to_linked", icon='ICON_LINK_AREA', text="")

        if group:
            row = layout.row()
            row.itemR(group, "name")

        if ob.mode == 'EDIT' and len(ob.vertex_groups) > 0:
            row = layout.row()

            sub = row.row(align=True)
            sub.itemO("object.vertex_group_assign", text="Assign")
            sub.itemO("object.vertex_group_remove_from", text="Remove")

            sub = row.row(align=True)
            sub.itemO("object.vertex_group_select", text="Select")
            sub.itemO("object.vertex_group_deselect", text="Deselect")

            layout.itemR(context.tool_settings, "vertex_group_weight", text="Weight")


class DATA_PT_shape_keys(DataButtonsPanel):
    bl_label = "Shape Keys"

    def poll(self, context):
        return (context.object and context.object.type in ('MESH', 'LATTICE', 'CURVE', 'SURFACE'))

    def draw(self, context):
        layout = self.layout

        ob = context.object
        key = ob.data.shape_keys
        kb = ob.active_shape_key

        enable_edit = ob.mode != 'EDIT'
        enable_edit_value = False

        if ob.shape_key_lock == False:
            if enable_edit or (ob.type == 'MESH' and ob.shape_key_edit_mode):
                enable_edit_value = True

        row = layout.row()

        rows = 2
        if kb:
            rows = 5
        row.template_list(key, "keys", ob, "active_shape_key_index", rows=rows)

        col = row.column()

        subcol = col.column(align=True)
        subcol.itemO("object.shape_key_add", icon='ICON_ZOOMIN', text="")
        subcol.itemO("object.shape_key_remove", icon='ICON_ZOOMOUT', text="")

        if kb:
            col.itemS()

            subcol = col.column(align=True)
            subcol.item_enumO("object.shape_key_move", "type", 'UP', icon='ICON_TRIA_UP', text="")
            subcol.item_enumO("object.shape_key_move", "type", 'DOWN', icon='ICON_TRIA_DOWN', text="")

            split = layout.split(percentage=0.4)
            sub = split.row()
            sub.enabled = enable_edit
            sub.itemR(key, "relative")

            sub = split.row()
            sub.alignment = 'RIGHT'

            subrow = sub.row(align=True)
            subrow.active = enable_edit_value
            if ob.shape_key_lock:
                subrow.itemR(ob, "shape_key_lock", icon='ICON_PINNED', text="")
            else:
                subrow.itemR(ob, "shape_key_lock", icon='ICON_UNPINNED', text="")
            if kb.mute:
                subrow.itemR(kb, "mute", icon='ICON_MUTE_IPO_ON', text="")
            else:
                subrow.itemR(kb, "mute", icon='ICON_MUTE_IPO_OFF', text="")
            subrow.itemO("object.shape_key_clear", icon='ICON_X', text="")

            sub.itemO("object.shape_key_mirror", icon='ICON_MOD_MIRROR', text="")

            sub.itemR(ob, "shape_key_edit_mode", text="")

            row = layout.row()
            row.itemR(kb, "name")

            if key.relative:
                if ob.active_shape_key_index != 0:
                    row = layout.row()
                    row.active = enable_edit_value
                    row.itemR(kb, "value")

                    split = layout.split()
                    sub = split.column(align=True)
                    sub.active = enable_edit_value
                    sub.itemL(text="Range:")
                    sub.itemR(kb, "slider_min", text="Min")
                    sub.itemR(kb, "slider_max", text="Max")

                    sub = split.column(align=True)
                    sub.active = enable_edit_value
                    sub.itemL(text="Blend:")
                    sub.item_pointerR(kb, "vertex_group", ob, "vertex_groups", text="")
                    sub.item_pointerR(kb, "relative_key", key, "keys", text="")

            else:
                row = layout.row()
                row.active = enable_edit_value
                row.itemR(key, "slurph")


class DATA_PT_uv_texture(DataButtonsPanel):
    bl_label = "UV Texture"

    def draw(self, context):
        layout = self.layout

        me = context.mesh

        row = layout.row()
        col = row.column()

        col.template_list(me, "uv_textures", me, "active_uv_texture_index", rows=2)

        col = row.column(align=True)
        col.itemO("mesh.uv_texture_add", icon='ICON_ZOOMIN', text="")
        col.itemO("mesh.uv_texture_remove", icon='ICON_ZOOMOUT', text="")

        lay = me.active_uv_texture
        if lay:
            layout.itemR(lay, "name")


class DATA_PT_vertex_colors(DataButtonsPanel):
    bl_label = "Vertex Colors"

    def draw(self, context):
        layout = self.layout

        me = context.mesh

        row = layout.row()
        col = row.column()

        col.template_list(me, "vertex_colors", me, "active_vertex_color_index", rows=2)

        col = row.column(align=True)
        col.itemO("mesh.vertex_color_add", icon='ICON_ZOOMIN', text="")
        col.itemO("mesh.vertex_color_remove", icon='ICON_ZOOMOUT', text="")

        lay = me.active_vertex_color
        if lay:
            layout.itemR(lay, "name")

bpy.types.register(DATA_PT_context_mesh)
bpy.types.register(DATA_PT_normals)
bpy.types.register(DATA_PT_settings)
bpy.types.register(DATA_PT_vertex_groups)
bpy.types.register(DATA_PT_shape_keys)
bpy.types.register(DATA_PT_uv_texture)
bpy.types.register(DATA_PT_vertex_colors)
