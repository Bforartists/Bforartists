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

narrowui = 180


class ObjectButtonsPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"


class OBJECT_PT_context_object(ObjectButtonsPanel):
    bl_label = ""
    bl_show_header = False

    def draw(self, context):
        layout = self.layout

        ob = context.object

        row = layout.row()
        row.itemL(text="", icon='ICON_OBJECT_DATA')
        row.itemR(ob, "name", text="")


class OBJECT_PT_transform(ObjectButtonsPanel):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        col2 = context.region.width > narrowui

        if col2:
            row = layout.row()

            row.column().itemR(ob, "location")
            if ob.rotation_mode == 'QUATERNION':
                row.column().itemR(ob, "rotation_quaternion", text="Rotation")
            elif ob.rotation_mode == 'AXIS_ANGLE':
                #row.column().itemL(text="Rotation")
                #row.column().itemR(pchan, "rotation_angle", text="Angle")
                #row.column().itemR(pchan, "rotation_axis", text="Axis")
                row.column().itemR(ob, "rotation_axis_angle", text="Rotation")
            else:
                row.column().itemR(ob, "rotation_euler", text="Rotation")

            row.column().itemR(ob, "scale")

            layout.itemR(ob, "rotation_mode")
        else:
            col = layout.column()
            col.itemR(ob, "location")
            col.itemL(text="Rotation:")
            col.itemR(ob, "rotation_mode", text="")
            if ob.rotation_mode == 'QUATERNION':
                col.itemR(ob, "rotation_quaternion", text="")
            elif ob.rotation_mode == 'AXIS_ANGLE':
                col.itemR(ob, "rotation_axis_angle", text="")
            else:
                col.itemR(ob, "rotation_euler", text="")
            col.itemR(ob, "scale")


class OBJECT_PT_transform_locks(ObjectButtonsPanel):
    bl_label = "Transform Locks"
    bl_default_closed = True

    def draw(self, context):
        layout = self.layout

        ob = context.object
        # col2 = context.region.width > narrowui

        row = layout.row()

        col = row.column()
        col.itemR(ob, "lock_location", text="Location")

        col = row.column()
        if ob.rotation_mode in ('QUATERNION', 'AXIS_ANGLE'):
            col.itemR(ob, "lock_rotations_4d", text="Rotation")
            if ob.lock_rotations_4d:
                col.itemR(ob, "lock_rotation_w", text="W")
            col.itemR(ob, "lock_rotation", text="")
        else:
            col.itemR(ob, "lock_rotation", text="Rotation")

        row.column().itemR(ob, "lock_scale", text="Scale")


class OBJECT_PT_relations(ObjectButtonsPanel):
    bl_label = "Relations"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.itemR(ob, "layers")
        col.itemS()
        col.itemR(ob, "pass_index")

        if col2:
            col = split.column()
        col.itemL(text="Parent:")
        col.itemR(ob, "parent", text="")

        sub = col.column()
        sub.itemR(ob, "parent_type", text="")
        parent = ob.parent
        if parent and ob.parent_type == 'BONE' and parent.type == 'ARMATURE':
            sub.item_pointerR(ob, "parent_bone", parent.data, "bones", text="")
        sub.active = parent != None


class OBJECT_PT_groups(ObjectButtonsPanel):
    bl_label = "Groups"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        col2 = context.region.width > narrowui

        if col2:
            split = layout.split()
            split.item_menu_enumO("object.group_add", "group", text="Add to Group")
            split.itemL()
        else:
            layout.item_menu_enumO("object.group_add", "group", text="Add to Group")

        for group in bpy.data.groups:
            if ob.name in group.objects:
                col = layout.column(align=True)

                col.set_context_pointer("group", group)

                row = col.box().row()
                row.itemR(group, "name", text="")
                row.itemO("object.group_remove", text="", icon='VICON_X')

                split = col.box().split()

                col = split.column()
                col.itemR(group, "layer", text="Dupli")

                if col2:
                    col = split.column()
                col.itemR(group, "dupli_offset", text="")


class OBJECT_PT_display(ObjectButtonsPanel):
    bl_label = "Display"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        col2 = context.region.width > narrowui

        split = layout.split()
        col = split.column()
        col.itemR(ob, "max_draw_type", text="Type")

        if col2:
            col = split.column()
        row = col.row()
        row.itemR(ob, "draw_bounds", text="Bounds")
        sub = row.row()
        sub.active = ob.draw_bounds
        sub.itemR(ob, "draw_bounds_type", text="")

        split = layout.split()

        col = split.column()
        col.itemR(ob, "draw_name", text="Name")
        col.itemR(ob, "draw_axis", text="Axis")
        col.itemR(ob, "draw_wire", text="Wire")

        if col2:
            col = split.column()
        col.itemR(ob, "draw_texture_space", text="Texture Space")
        col.itemR(ob, "x_ray", text="X-Ray")
        col.itemR(ob, "draw_transparent", text="Transparency")


class OBJECT_PT_duplication(ObjectButtonsPanel):
    bl_label = "Duplication"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        col2 = context.region.width > narrowui

        if col2:
            layout.itemR(ob, "dupli_type", expand=True)
        else:
            layout.itemR(ob, "dupli_type", text="")

        if ob.dupli_type == 'FRAMES':
            split = layout.split()

            col = split.column(align=True)
            col.itemR(ob, "dupli_frames_start", text="Start")
            col.itemR(ob, "dupli_frames_end", text="End")

            if col2:
                col = split.column(align=True)
            col.itemR(ob, "dupli_frames_on", text="On")
            col.itemR(ob, "dupli_frames_off", text="Off")

            layout.itemR(ob, "dupli_frames_no_speed", text="No Speed")

        elif ob.dupli_type == 'VERTS':
            layout.itemR(ob, "dupli_verts_rotation", text="Rotation")

        elif ob.dupli_type == 'FACES':
            split = layout.split()

            col = split.column()
            col.itemR(ob, "dupli_faces_scale", text="Scale")

            if col2:
                col = split.column()
            col.itemR(ob, "dupli_faces_inherit_scale", text="Inherit Scale")

        elif ob.dupli_type == 'GROUP':
            if col2:
                layout.itemR(ob, "dupli_group", text="Group")
            else:
                layout.itemR(ob, "dupli_group", text="")


class OBJECT_PT_animation(ObjectButtonsPanel):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        col2 = context.region.width > narrowui

        split = layout.split()

        col = split.column()
        col.itemL(text="Time Offset:")
        col.itemR(ob, "time_offset_edit", text="Edit")
        row = col.row()
        row.itemR(ob, "time_offset_particle", text="Particle")
        row.active = len(ob.particle_systems) != 0
        row = col.row()
        row.itemR(ob, "time_offset_parent", text="Parent")
        row.active = ob.parent != None
        row = col.row()
        row.itemR(ob, "slow_parent")
        row.active = ob.parent != None
        col.itemR(ob, "time_offset", text="Offset")

        if col2:
            col = split.column()
        col.itemL(text="Track:")
        col.itemR(ob, "track", text="")
        col.itemR(ob, "track_axis", text="Axis")
        col.itemR(ob, "up_axis", text="Up Axis")
        row = col.row()
        row.itemR(ob, "track_override_parent", text="Override Parent")
        row.active = ob.parent != None

bpy.types.register(OBJECT_PT_context_object)
bpy.types.register(OBJECT_PT_transform)
bpy.types.register(OBJECT_PT_transform_locks)
bpy.types.register(OBJECT_PT_relations)
bpy.types.register(OBJECT_PT_groups)
bpy.types.register(OBJECT_PT_display)
bpy.types.register(OBJECT_PT_duplication)
bpy.types.register(OBJECT_PT_animation)
