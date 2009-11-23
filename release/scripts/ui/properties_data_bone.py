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


class BoneButtonsPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    def poll(self, context):
        return (context.bone or context.edit_bone)


class BONE_PT_context_bone(BoneButtonsPanel):
    bl_label = ""
    bl_show_header = False

    def draw(self, context):
        layout = self.layout

        bone = context.bone
        if not bone:
            bone = context.edit_bone

        row = layout.row()
        row.label(text="", icon='ICON_BONE_DATA')
        row.prop(bone, "name", text="")


class BONE_PT_transform(BoneButtonsPanel):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        bone = context.bone
        wide_ui = context.region.width > narrowui

        if not bone:
            bone = context.edit_bone
            if wide_ui:
                row = layout.row()
                row.column().prop(bone, "head")
                row.column().prop(bone, "tail")

                col = row.column()
                sub = col.column(align=True)
                sub.label(text="Roll:")
                sub.prop(bone, "roll", text="")
                sub.label()
                sub.prop(bone, "locked")
            else:
                col = layout.column()
                col.prop(bone, "head")
                col.prop(bone, "tail")
                col.prop(bone, "roll")
                col.prop(bone, "locked")

        else:
            pchan = ob.pose.bones[context.bone.name]

            if wide_ui:
                row = layout.row()
                col = row.column()
                col.prop(pchan, "location")
                col.active = not (bone.parent and bone.connected)

                col = row.column()
                if pchan.rotation_mode == 'QUATERNION':
                    col.prop(pchan, "rotation_quaternion", text="Rotation")
                elif pchan.rotation_mode == 'AXIS_ANGLE':
                    #col.label(text="Rotation")
                    #col.prop(pchan, "rotation_angle", text="Angle")
                    #col.prop(pchan, "rotation_axis", text="Axis")
                    col.prop(pchan, "rotation_axis_angle", text="Rotation")
                else:
                    col.prop(pchan, "rotation_euler", text="Rotation")

                row.column().prop(pchan, "scale")

                layout.prop(pchan, "rotation_mode")
            else:
                col = layout.column()
                sub = col.column()
                sub.active = not (bone.parent and bone.connected)
                sub.prop(pchan, "location")
                col.label(text="Rotation:")
                col.prop(pchan, "rotation_mode", text="")
                if pchan.rotation_mode == 'QUATERNION':
                    col.prop(pchan, "rotation_quaternion", text="")
                elif pchan.rotation_mode == 'AXIS_ANGLE':
                    col.prop(pchan, "rotation_axis_angle", text="")
                else:
                    col.prop(pchan, "rotation_euler", text="")
                col.prop(pchan, "scale")


class BONE_PT_transform_locks(BoneButtonsPanel):
    bl_label = "Transform Locks"
    bl_default_closed = True

    def poll(self, context):
        return context.bone

    def draw(self, context):
        layout = self.layout

        ob = context.object
        bone = context.bone
        pchan = ob.pose.bones[context.bone.name]

        row = layout.row()
        col = row.column()
        col.prop(pchan, "lock_location")
        col.active = not (bone.parent and bone.connected)

        col = row.column()
        if pchan.rotation_mode in ('QUATERNION', 'AXIS_ANGLE'):
            col.prop(pchan, "lock_rotations_4d", text="Lock Rotation")
            if pchan.lock_rotations_4d:
                col.prop(pchan, "lock_rotation_w", text="W")
            col.prop(pchan, "lock_rotation", text="")
        else:
            col.prop(pchan, "lock_rotation", text="Rotation")

        row.column().prop(pchan, "lock_scale")


class BONE_PT_relations(BoneButtonsPanel):
    bl_label = "Relations"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        bone = context.bone
        arm = context.armature
        wide_ui = context.region.width > narrowui

        if not bone:
            bone = context.edit_bone
            pchan = None
        else:
            pchan = ob.pose.bones[context.bone.name]

        split = layout.split()

        col = split.column()
        col.label(text="Layers:")
        col.prop(bone, "layer", text="")

        col.separator()

        if ob and pchan:
            col.label(text="Bone Group:")
            col.prop_pointer(pchan, "bone_group", ob.pose, "bone_groups", text="")

        if wide_ui:
            col = split.column()
        col.label(text="Parent:")
        if context.bone:
            col.prop(bone, "parent", text="")
        else:
            col.prop_pointer(bone, "parent", arm, "edit_bones", text="")

        sub = col.column()
        sub.active = (bone.parent is not None)
        sub.prop(bone, "connected")
        sub.prop(bone, "hinge", text="Inherit Rotation")
        sub.prop(bone, "inherit_scale", text="Inherit Scale")


class BONE_PT_display(BoneButtonsPanel):
    bl_label = "Display"

    def poll(self, context):
        return context.bone

    def draw(self, context):
        layout = self.layout

        ob = context.object
        bone = context.bone
        wide_ui = context.region.width > narrowui

        if not bone:
            bone = context.edit_bone
            pchan = None
        else:
            pchan = ob.pose.bones[context.bone.name]

        if ob and pchan:

            split = layout.split()

            col = split.column()
            col.prop(bone, "draw_wire", text="Wireframe")
            col.prop(bone, "hidden", text="Hide")

            if wide_ui:
                col = split.column()
            col.label(text="Custom Shape:")
            col.prop(pchan, "custom_shape", text="")


class BONE_PT_deform(BoneButtonsPanel):
    bl_label = "Deform"
    bl_default_closed = True

    def draw_header(self, context):
        bone = context.bone

        if not bone:
            bone = context.edit_bone

        self.layout.prop(bone, "deform", text="")

    def draw(self, context):
        layout = self.layout

        bone = context.bone
        wide_ui = context.region.width > narrowui

        if not bone:
            bone = context.edit_bone

        layout.active = bone.deform

        split = layout.split()

        col = split.column()
        col.label(text="Envelope:")

        sub = col.column(align=True)
        sub.prop(bone, "envelope_distance", text="Distance")
        sub.prop(bone, "envelope_weight", text="Weight")
        col.prop(bone, "multiply_vertexgroup_with_envelope", text="Multiply")

        sub = col.column(align=True)
        sub.label(text="Radius:")
        sub.prop(bone, "head_radius", text="Head")
        sub.prop(bone, "tail_radius", text="Tail")

        if wide_ui:
            col = split.column()
        col.label(text="Curved Bones:")

        sub = col.column(align=True)
        sub.prop(bone, "bbone_segments", text="Segments")
        sub.prop(bone, "bbone_in", text="Ease In")
        sub.prop(bone, "bbone_out", text="Ease Out")

        col.label(text="Offset:")
        col.prop(bone, "cyclic_offset")


class BONE_PT_properties(BoneButtonsPanel):
    bl_label = "Properties"
    bl_default_closed = True

    def draw(self, context):
        import rna_prop_ui
        # reload(rna_prop_ui)
        obj = context.object
        if obj and obj.mode == 'POSE':
            item = "active_pchan"
        else:
            item = "active_bone"

        rna_prop_ui.draw(self.layout, context, item)

bpy.types.register(BONE_PT_context_bone)
bpy.types.register(BONE_PT_transform)
bpy.types.register(BONE_PT_transform_locks)
bpy.types.register(BONE_PT_relations)
bpy.types.register(BONE_PT_display)
bpy.types.register(BONE_PT_deform)
bpy.types.register(BONE_PT_properties)
