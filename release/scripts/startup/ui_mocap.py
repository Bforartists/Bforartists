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

from bpy.props import *
from bpy import *
import mocap_constraints
import retarget
import mocap_tools
### reloads modules (for testing purposes only)
from imp import reload
reload(mocap_constraints)
reload(retarget)
reload(mocap_tools)

from mocap_constraints import *

# MocapConstraint class
# Defines MocapConstraint datatype, used to add and configute mocap constraints
# Attached to Armature data


class MocapConstraint(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Name",
        default="Mocap Constraint",
        description="Name of Mocap Constraint",
        update=setConstraint)
    constrained_bone = bpy.props.StringProperty(name="Bone",
        default="",
        description="Constrained Bone",
        update=updateConstraintBoneType)
    constrained_boneB = bpy.props.StringProperty(name="Bone (2)",
        default="",
        description="Other Constrained Bone (optional, depends on type)",
        update=setConstraint)
    s_frame = bpy.props.IntProperty(name="S",
        default=1,
        description="Start frame of constraint",
        update=setConstraint)
    e_frame = bpy.props.IntProperty(name="E",
        default=500,
        description="End frame of constrain",
        update=setConstraint)
    smooth_in = bpy.props.IntProperty(name="In",
        default=10,
        description="Amount of frames to smooth in",
        update=setConstraint,
        min=0)
    smooth_out = bpy.props.IntProperty(name="Out",
        default=10,
        description="Amount of frames to smooth out",
        update=setConstraint,
        min=0)
    targetMesh = bpy.props.StringProperty(name="Mesh",
        default="",
        description="Target of Constraint - Mesh (optional, depends on type)",
        update=setConstraint)
    active = bpy.props.BoolProperty(name="Active",
        default=True,
        description="Constraint is active",
        update=setConstraint)
    targetPoint = bpy.props.FloatVectorProperty(name="Point", size=3,
        subtype="XYZ", default=(0.0, 0.0, 0.0),
        description="Target of Constraint - Point",
        update=setConstraint)
    targetDist = bpy.props.FloatProperty(name="Offset",
        default=0.0,
        description="Distance and Floor Constraints - Desired offset",
        update=setConstraint)
    targetSpace = bpy.props.EnumProperty(
        items=[("WORLD", "World Space", "Evaluate target in global space"),
            ("LOCAL", "Object space", "Evaluate target in object space"),
            ("constrained_boneB", "Other Bone Space", "Evaluate target in specified other bone space")],
        name="Space",
        description="In which space should Point type target be evaluated",
        update=setConstraint)
    type = bpy.props.EnumProperty(name="Type of constraint",
        items=[("point", "Maintain Position", "Bone is at a specific point"),
            ("freeze", "Maintain Position at frame", "Bone does not move from location specified in target frame"),
            ("floor", "Stay above", "Bone does not cross specified mesh object eg floor"),
            ("distance", "Maintain distance", "Target bones maintained specified distance")],
        description="Type of constraint",
        update=updateConstraintBoneType)
    real_constraint = bpy.props.StringProperty()
    real_constraint_bone = bpy.props.StringProperty()


bpy.utils.register_class(MocapConstraint)

bpy.types.Armature.mocap_constraints = bpy.props.CollectionProperty(type=MocapConstraint)

#Update function for IK functionality. Is called when IK prop checkboxes are toggled.


def toggleIKBone(self, context):
    if self.IKRetarget:
        if not self.is_in_ik_chain:
            print(self.name + " IK toggled ON!")
            ik = self.constraints.new('IK')
            #ik the whole chain up to the root, excluding
            chainLen = 0
            for parent_bone in self.parent_recursive:
                chainLen += 1
                if hasIKConstraint(parent_bone):
                    break
                deformer_children = [child for child in parent_bone.children if child.bone.use_deform]
                if len(deformer_children) > 1:
                    break
            ik.chain_count = chainLen
            for bone in self.parent_recursive:
                if bone.is_in_ik_chain:
                    bone.IKRetarget = True
    else:
        print(self.name + " IK toggled OFF!")
        cnstrn_bone = False
        if hasIKConstraint(self):
            cnstrn_bone = self
        elif self.is_in_ik_chain:
            cnstrn_bone = [child for child in self.children_recursive if hasIKConstraint(child)][0]
        if cnstrn_bone:
            # remove constraint, and update IK retarget for all parents of cnstrn_bone up to chain_len
            ik = [constraint for constraint in cnstrn_bone.constraints if constraint.type == "IK"][0]
            cnstrn_bone.constraints.remove(ik)
            cnstrn_bone.IKRetarget = False
            for bone in cnstrn_bone.parent_recursive:
                if not bone.is_in_ik_chain:
                    bone.IKRetarget = False


class MocapMapping(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()

bpy.utils.register_class(MocapMapping)

bpy.types.Bone.map = bpy.props.StringProperty()
bpy.types.Bone.reverseMap = bpy.props.CollectionProperty(type=MocapMapping)
bpy.types.Bone.foot = bpy.props.BoolProperty(name="Foot",
    description="Marks this bone as a 'foot', which determines retargeted animation's translation",
    default=False)
bpy.types.PoseBone.IKRetarget = bpy.props.BoolProperty(name="IK",
    description="Toggles IK Retargeting method for given bone",
    update=toggleIKBone, default=False)


def updateIKRetarget():
    # ensures that Blender constraints and IK properties are in sync
    # currently runs when module is loaded, should run when scene is loaded
    # or user adds a constraint to armature. Will be corrected in the future,
    # once python callbacks are implemented
    for obj in bpy.data.objects:
        if obj.pose:
            bones = obj.pose.bones
            for pose_bone in bones:
                if pose_bone.is_in_ik_chain or hasIKConstraint(pose_bone):
                    pose_bone.IKRetarget = True
                else:
                    pose_bone.IKRetarget = False

updateIKRetarget()


class MocapPanel(bpy.types.Panel):
    # Motion capture retargeting panel
    bl_label = "Mocap tools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        self.layout.label("Preprocessing")
        row = self.layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("mocap.samples", text='Samples to Beziers')
        row.operator("mocap.denoise", text='Clean noise')
        row.operator("mocap.rotate_fix", text='Fix BVH Axis Orientation')
        row.operator("mocap.scale_fix", text='Auto scale Performer')
        row2 = self.layout.row(align=True)
        row2.operator("mocap.looper", text='Loop animation')
        row2.operator("mocap.limitdof", text='Constrain Rig')
        self.layout.label("Retargeting")
        row3 = self.layout.row(align=True)
        column1 = row3.column(align=True)
        column1.label("Performer Rig")
        column2 = row3.column(align=True)
        column2.label("Enduser Rig")
        enduser_obj = bpy.context.active_object
        performer_obj = [obj for obj in bpy.context.selected_objects if obj != enduser_obj]
        if enduser_obj is None or len(performer_obj) != 1:
            self.layout.label("Select performer rig and target rig (as active)")
        else:
            performer_obj = performer_obj[0]
            if performer_obj.data and enduser_obj.data:
                if performer_obj.data.name in bpy.data.armatures and enduser_obj.data.name in bpy.data.armatures:
                    perf = performer_obj.data
                    enduser_arm = enduser_obj.data
                    perf_pose_bones = enduser_obj.pose.bones
                    for bone in perf.bones:
                        row = self.layout.row()
                        row.prop(data=bone, property='foot', text='', icon='POSE_DATA')
                        row.label(bone.name)
                        row.prop_search(bone, "map", enduser_arm, "bones")
                        label_mod = "FK"
                        if bone.map:
                            pose_bone = perf_pose_bones[bone.map]
                            if pose_bone.is_in_ik_chain:
                                label_mod = "ik chain"
                            if hasIKConstraint(pose_bone):
                                label_mod = "ik end"
                            row.prop(pose_bone, 'IKRetarget')
                            row.label(label_mod)
                        else:
                            row.label(" ")
                            row.label(" ")
                    mapRow = self.layout.row()
                    mapRow.operator("mocap.savemapping", text='Save mapping')
                    mapRow.operator("mocap.loadmapping", text='Load mapping')
                    self.layout.operator("mocap.retarget", text='RETARGET!')


class MocapConstraintsPanel(bpy.types.Panel):
    #Motion capture constraints panel
    bl_label = "Mocap constraints"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        if context.active_object:
            if context.active_object.data:
                if context.active_object.data.name in bpy.data.armatures:
                    enduser_obj = context.active_object
                    enduser_arm = enduser_obj.data
                    layout.operator("mocap.addconstraint")
                    layout.operator("mocap.bakeconstraints")
                    layout.operator("mocap.unbakeconstraints")
                    layout.separator()
                    for i, m_constraint in enumerate(enduser_arm.mocap_constraints):
                        box = layout.box()
                        box.prop(m_constraint, 'name')
                        box.prop(m_constraint, 'type')
                        box.prop_search(m_constraint, 'constrained_bone', enduser_obj.pose, "bones")
                        if m_constraint.type == "distance" or m_constraint.type == "point":
                            box.prop_search(m_constraint, 'constrained_boneB', enduser_obj.pose, "bones")
                        frameRow = box.row()
                        frameRow.label("Frame Range:")
                        frameRow.prop(m_constraint, 's_frame')
                        frameRow.prop(m_constraint, 'e_frame')
                        smoothRow = box.row()
                        smoothRow.label("Smoothing:")
                        smoothRow.prop(m_constraint, 'smooth_in')
                        smoothRow.prop(m_constraint, 'smooth_out')
                        targetRow = box.row()
                        targetLabelCol = targetRow.column()
                        targetLabelCol.label("Target settings:")
                        targetPropCol = targetRow.column()
                        if m_constraint.type == "floor":
                            targetPropCol.prop_search(m_constraint, 'targetMesh', bpy.data, "objects")
                        if m_constraint.type == "point" or m_constraint.type == "freeze":
                            box.prop(m_constraint, 'targetSpace')
                        if m_constraint.type == "point":
                            targetPropCol.prop(m_constraint, 'targetPoint')
                        if m_constraint.type == "distance" or m_constraint.type == "floor":
                            targetPropCol.prop(m_constraint, 'targetDist')
                        checkRow = box.row()
                        checkRow.prop(m_constraint, 'active')
                        layout.operator("mocap.removeconstraint", text="Remove constraint").constraint = i
                        layout.separator()


class OBJECT_OT_RetargetButton(bpy.types.Operator):
    '''Retarget animation from selected armature to active armature '''
    bl_idname = "mocap.retarget"
    bl_label = "Retargets active action from Performer to Enduser"

    def execute(self, context):
        enduser_obj = context.active_object
        performer_obj = [obj for obj in context.selected_objects if obj != enduser_obj]
        if enduser_obj is None or len(performer_obj) != 1:
            print("Need active and selected armatures")
        else:
            performer_obj = performer_obj[0]
        scene = context.scene
        s_frame = scene.frame_start
        e_frame = scene.frame_end
        retarget.totalRetarget(performer_obj, enduser_obj, scene, s_frame, e_frame)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            activeIsArmature = isinstance(context.active_object.data, bpy.types.Armature)
        performer_obj = [obj for obj in context.selected_objects if obj != context.active_object]
        if performer_obj:
            return activeIsArmature and isinstance(performer_obj[0].data, bpy.types.Armature)
        else:
            return False


class OBJECT_OT_SaveMappingButton(bpy.types.Operator):
    '''Save mapping to active armature (for future retargets) '''
    bl_idname = "mocap.savemapping"
    bl_label = "Saves user generated mapping from Performer to Enduser"

    def execute(self, context):
        enduser_obj = bpy.context.active_object
        performer_obj = [obj for obj in bpy.context.selected_objects if obj != enduser_obj][0]
        retarget.createDictionary(performer_obj.data, enduser_obj.data)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            activeIsArmature = isinstance(context.active_object.data, bpy.types.Armature)
        performer_obj = [obj for obj in context.selected_objects if obj != context.active_object]
        if performer_obj:
            return activeIsArmature and isinstance(performer_obj[0].data, bpy.types.Armature)
        else:
            return False


class OBJECT_OT_LoadMappingButton(bpy.types.Operator):
    '''Load saved mapping from active armature'''
    bl_idname = "mocap.loadmapping"
    bl_label = "Loads user generated mapping from Performer to Enduser"

    def execute(self, context):
        enduser_obj = bpy.context.active_object
        performer_obj = [obj for obj in bpy.context.selected_objects if obj != enduser_obj][0]
        retarget.loadMapping(performer_obj.data, enduser_obj.data)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            activeIsArmature = isinstance(context.active_object.data, bpy.types.Armature)
        performer_obj = [obj for obj in context.selected_objects if obj != context.active_object]
        if performer_obj:
            return activeIsArmature and isinstance(performer_obj[0].data, bpy.types.Armature)
        else:
            return False


class OBJECT_OT_ConvertSamplesButton(bpy.types.Operator):
    '''Convert active armature's sampled keyframed to beziers'''
    bl_idname = "mocap.samples"
    bl_label = "Converts samples / simplifies keyframes to beziers"

    def execute(self, context):
        mocap_tools.fcurves_simplify()
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        return context.active_object.animation_data


class OBJECT_OT_LooperButton(bpy.types.Operator):
    '''Trim active armature's animation to a single cycle, given a cyclic animation (such as a walk cycle)'''
    bl_idname = "mocap.looper"
    bl_label = "loops animation / sampled mocap data"

    def execute(self, context):
        mocap_tools.autoloop_anim()
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        return context.active_object.animation_data


class OBJECT_OT_DenoiseButton(bpy.types.Operator):
    '''Denoise active armature's animation. Good for dealing with 'bad' frames inherent in mocap animation'''
    bl_idname = "mocap.denoise"
    bl_label = "Denoises sampled mocap data "

    def execute(self, context):
        mocap_tools.denoise_median()
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        return context.active_object

    @classmethod
    def poll(cls, context):
        return context.active_object.animation_data


class OBJECT_OT_LimitDOFButton(bpy.types.Operator):
    '''UNIMPLEMENTED: Create limit constraints on the active armature from the selected armature's animation's range of motion'''
    bl_idname = "mocap.limitdof"
    bl_label = "Analyzes animations Max/Min DOF and adds hard/soft constraints"

    def execute(self, context):
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            activeIsArmature = isinstance(context.active_object.data, bpy.types.Armature)
        performer_obj = [obj for obj in context.selected_objects if obj != context.active_object]
        if performer_obj:
            return activeIsArmature and isinstance(performer_obj[0].data, bpy.types.Armature)
        else:
            return False


class OBJECT_OT_RotateFixArmature(bpy.types.Operator):
    '''Realign the active armature's axis system to match Blender (Commonly needed after bvh import)'''
    bl_idname = "mocap.rotate_fix"
    bl_label = "Rotates selected armature 90 degrees (fix for bvh import)"

    def execute(self, context):
        mocap_tools.rotate_fix_armature(context.active_object.data)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return isinstance(context.active_object.data, bpy.types.Armature)


class OBJECT_OT_ScaleFixArmature(bpy.types.Operator):
    '''Rescale selected armature to match the active animation, for convienence'''
    bl_idname = "mocap.scale_fix"
    bl_label = "Scales performer armature to match target armature"

    def execute(self, context):
        enduser_obj = bpy.context.active_object
        performer_obj = [obj for obj in bpy.context.selected_objects if obj != enduser_obj][0]
        mocap_tools.scale_fix_armature(performer_obj, enduser_obj)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            activeIsArmature = isinstance(context.active_object.data, bpy.types.Armature)
        performer_obj = [obj for obj in context.selected_objects if obj != context.active_object]
        if performer_obj:
            return activeIsArmature and isinstance(performer_obj[0].data, bpy.types.Armature)
        else:
            return False


class OBJECT_OT_AddMocapConstraint(bpy.types.Operator):
    '''Add a post-retarget fix - useful for fixing certain artifacts following the retarget'''
    bl_idname = "mocap.addconstraint"
    bl_label = "Add constraint to target armature"

    def execute(self, context):
        enduser_obj = bpy.context.active_object
        enduser_arm = enduser_obj.data
        new_mcon = enduser_arm.mocap_constraints.add()
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return isinstance(context.active_object.data, bpy.types.Armature)


class OBJECT_OT_RemoveMocapConstraint(bpy.types.Operator):
    '''Remove this post-retarget fix'''
    bl_idname = "mocap.removeconstraint"
    bl_label = "Removes constraints from target armature"
    constraint = bpy.props.IntProperty()

    def execute(self, context):
        enduser_obj = bpy.context.active_object
        enduser_arm = enduser_obj.data
        m_constraints = enduser_arm.mocap_constraints
        m_constraint = m_constraints[self.constraint]
        if m_constraint.real_constraint:
            bone = enduser_obj.pose.bones[m_constraint.real_constraint_bone]
            cons_obj = getConsObj(bone)
            removeConstraint(m_constraint, cons_obj)
        m_constraints.remove(self.constraint)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return isinstance(context.active_object.data, bpy.types.Armature)


class OBJECT_OT_BakeMocapConstraints(bpy.types.Operator):
    '''Bake all post-retarget fixes to the Retarget Fixes NLA Track'''
    bl_idname = "mocap.bakeconstraints"
    bl_label = "Bake all constraints to target armature"

    def execute(self, context):
        bakeConstraints(context)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return isinstance(context.active_object.data, bpy.types.Armature)


class OBJECT_OT_UnbakeMocapConstraints(bpy.types.Operator):
    '''Unbake all post-retarget fixes - removes the baked data from the Retarget Fixes NLA Track'''
    bl_idname = "mocap.unbakeconstraints"
    bl_label = "Unbake all constraints to target armature"

    def execute(self, context):
        unbakeConstraints(context)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return isinstance(context.active_object.data, bpy.types.Armature)


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
