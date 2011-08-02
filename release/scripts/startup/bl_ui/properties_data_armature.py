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

# <pep8 compliant>
import bpy
from rna_prop_ui import PropertyPanel
from blf import gettext as _

class ArmatureButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.armature


class DATA_PT_context_arm(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout

        ob = context.object
        arm = context.armature
        space = context.space_data

        if ob:
            layout.template_ID(ob, "data")
        elif arm:
            layout.template_ID(space, "pin_id")


class DATA_PT_skeleton(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = _("Skeleton")

    def draw(self, context):
        layout = self.layout

        arm = context.armature

        layout.prop(arm, "pose_position", expand=True)

        col = layout.column()
        col.label(text=_("Layers:"))
        col.prop(arm, "layers", text="")
        col.label(text=_("Protected Layers:"))
        col.prop(arm, "layers_protected", text="")

        layout.label(text="Deform:")
        flow = layout.column_flow()
        flow.prop(arm, "use_deform_vertex_groups", text=_("Vertex Groups"))
        flow.prop(arm, "use_deform_envelopes", text=_("Envelopes"))
        flow.prop(arm, "use_deform_preserve_volume", text=_("Quaternion"))


class DATA_PT_display(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = _("Display")

    def draw(self, context):
        layout = self.layout

        ob = context.object
        arm = context.armature

        layout.prop(arm, "draw_type", expand=True)

        split = layout.split()

        col = split.column()
        col.prop(arm, "show_names", text=_("Names"))
        col.prop(arm, "show_axes", text=_("Axes"))
        col.prop(arm, "show_bone_custom_shapes", text=_("Shapes"))

        col = split.column()
        col.prop(arm, "show_group_colors", text=_("Colors"))
        if ob:
            col.prop(ob, "show_x_ray", text=_("X-Ray"))
        col.prop(arm, "use_deform_delay", text=_("Delay Refresh"))


class DATA_PT_bone_groups(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = _("Bone Groups")

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'ARMATURE' and context.object.pose)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        pose = ob.pose

        row = layout.row()
        row.template_list(pose, "bone_groups", pose.bone_groups, "active_index", rows=2)

        col = row.column(align=True)
        col.active = (ob.proxy is None)
        col.operator("pose.group_add", icon='ZOOMIN', text="")
        col.operator("pose.group_remove", icon='ZOOMOUT', text="")

        group = pose.bone_groups.active
        if group:
            col = layout.column()
            col.active = (ob.proxy is None)
            col.prop(group, "name")

            split = layout.split()
            split.active = (ob.proxy is None)

            col = split.column()
            col.prop(group, "color_set")
            if group.color_set:
                col = split.column()
                sub = col.row(align=True)
                sub.prop(group.colors, "normal", text="")
                sub.prop(group.colors, "select", text="")
                sub.prop(group.colors, "active", text="")

        row = layout.row()
        row.active = (ob.proxy is None)

        sub = row.row(align=True)
        sub.operator("pose.group_assign", text=_("Assign"))
        sub.operator("pose.group_unassign", text=_("Remove"))  # row.operator("pose.bone_group_remove_from", text=_("Remove"))

        sub = row.row(align=True)
        sub.operator("pose.group_select", text=_("Select"))
        sub.operator("pose.group_deselect", text=_("Deselect"))


class DATA_PT_pose_library(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = _("Pose Library")
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'ARMATURE' and context.object.pose)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        poselib = ob.pose_library

        layout.template_ID(ob, "pose_library", new="poselib.new", unlink="poselib.unlink")

        if poselib:
            row = layout.row()
            row.template_list(poselib, "pose_markers", poselib.pose_markers, "active_index", rows=5)

            col = row.column(align=True)
            col.active = (poselib.library is None)

            # invoke should still be used for 'add', as it is needed to allow
            # add/replace options to be used properly
            col.operator("poselib.pose_add", icon='ZOOMIN', text="")

            col.operator_context = 'EXEC_DEFAULT'  # exec not invoke, so that menu doesn't need showing

            pose_marker_active = poselib.pose_markers.active

            if pose_marker_active is not None:
                col.operator("poselib.pose_remove", icon='ZOOMOUT', text="").pose = pose_marker_active.name
                col.operator("poselib.apply_pose", icon='ZOOM_SELECTED', text="").pose_index = poselib.pose_markers.active_index

            layout.operator("poselib.action_sanitise")


# TODO: this panel will soon be depreceated too
class DATA_PT_ghost(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = _("Ghost")

    def draw(self, context):
        layout = self.layout

        arm = context.armature

        layout.prop(arm, "ghost_type", expand=True)

        split = layout.split()

        col = split.column(align=True)

        if arm.ghost_type == 'RANGE':
            col.prop(arm, "ghost_frame_start", text=_("Start"))
            col.prop(arm, "ghost_frame_end", text=_("End"))
            col.prop(arm, "ghost_size", text=_("Step"))
        elif arm.ghost_type == 'CURRENT_FRAME':
            col.prop(arm, "ghost_step", text=_("Range"))
            col.prop(arm, "ghost_size", text=_("Step"))

        col = split.column()
        col.label(text=_("Display:"))
        col.prop(arm, "show_only_ghost_selected", text=_("Selected Only"))


class DATA_PT_iksolver_itasc(ArmatureButtonsPanel, bpy.types.Panel):
    bl_label = _("iTaSC parameters")
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.pose)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        itasc = ob.pose.ik_param

        layout.prop(ob.pose, "ik_solver")

        if itasc:
            layout.prop(itasc, "mode", expand=True)
            simulation = (itasc.mode == 'SIMULATION')
            if simulation:
                layout.label(text=_("Reiteration:"))
                layout.prop(itasc, "reiteration_method", expand=True)

            row = layout.row()
            row.active = not simulation or itasc.reiteration_method != 'NEVER'
            row.prop(itasc, "precision")
            row.prop(itasc, "iterations")

            if simulation:
                layout.prop(itasc, "use_auto_step")
                row = layout.row()
                if itasc.use_auto_step:
                    row.prop(itasc, "step_min", text=_("Min"))
                    row.prop(itasc, "step_max", text=_("Max"))
                else:
                    row.prop(itasc, "step_count")

            layout.prop(itasc, "solver")
            if simulation:
                layout.prop(itasc, "feedback")
                layout.prop(itasc, "velocity_max")
            if itasc.solver == 'DLS':
                row = layout.row()
                row.prop(itasc, "damping_max", text=_("Damp"), slider=True)
                row.prop(itasc, "damping_epsilon", text="Eps", slider=True)

from bl_ui.properties_animviz import (
    MotionPathButtonsPanel,
    OnionSkinButtonsPanel,
    )


class DATA_PT_motion_paths(MotionPathButtonsPanel, bpy.types.Panel):
    #bl_label = "Bones Motion Paths"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        # XXX: include posemode check?
        return (context.object) and (context.armature)

    def draw(self, context):
        layout = self.layout

        ob = context.object

        self.draw_settings(context, ob.pose.animation_visualisation, bones=True)

        layout.separator()

        split = layout.split()
        split.operator("pose.paths_calculate", text=_("Calculate Paths"))
        split.operator("pose.paths_clear", text=_("Clear Paths"))


class DATA_PT_onion_skinning(OnionSkinButtonsPanel):  # , bpy.types.Panel): # inherit from panel when ready
    #bl_label = "Bones Onion Skinning"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        # XXX: include posemode check?
        return (context.object) and (context.armature)

    def draw(self, context):
        ob = context.object
        self.draw_settings(context, ob.pose.animation_visualisation, bones=True)


class DATA_PT_custom_props_arm(ArmatureButtonsPanel, PropertyPanel, bpy.types.Panel):
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}
    _context_path = "object.data"
    _property_type = bpy.types.Armature

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
