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
import time

from bpy.props import *
from bpy import *
from mathutils import Vector
from math import isfinite

def toggleIKBone(self, context):
    if self.IKRetarget:
        if not self.is_in_ik_chain:
            print(self.name + " IK toggled ON!")
            ik = self.constraints.new('IK')
            #ik the whole chain up to the root
            chainLen = len(self.bone.parent_recursive)
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
            

bpy.types.Bone.map = bpy.props.StringProperty()
bpy.types.PoseBone.IKRetarget = bpy.props.BoolProperty(name="IK",
    description = "Toggles IK Retargeting method for given bone",
    update = toggleIKBone)

def hasIKConstraint(pose_bone):
    return ("IK" in [constraint.type for constraint in pose_bone.constraints])
    
def updateIKRetarget():
    for obj in bpy.data.objects:
        if obj.pose:
            bones = obj.pose.bones
            for pose_bone in bones:
                if pose_bone.is_in_ik_chain or hasIKConstraint(pose_bone):
                    pose_bone.IKRetarget = True
                else:
                    pose_bone.IKRetarget = False

updateIKRetarget()

import retarget
import mocap_tools


class MocapPanel(bpy.types.Panel):
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
        row2 = self.layout.row(align=True)
        row2.operator("mocap.looper", text='Loop animation')
        row2.operator("mocap.limitdof", text='Constrain Rig')
        self.layout.label("Retargeting")
        row3 = self.layout.row(align=True)
        column1 = row3.column(align=True)
        column1.label("Performer Rig")
        column2 = row3.column(align=True)
        column2.label("Enduser Rig")
        self.layout.label("Hierarchy mapping")
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
                            
                    self.layout.operator("mocap.retarget", text='RETARGET!')


class OBJECT_OT_RetargetButton(bpy.types.Operator):
    bl_idname = "mocap.retarget"
    bl_label = "Retargets active action from Performer to Enduser"

    def execute(self, context):
        retarget.totalRetarget()
        return {"FINISHED"}


class OBJECT_OT_ConvertSamplesButton(bpy.types.Operator):
    bl_idname = "mocap.samples"
    bl_label = "Converts samples / simplifies keyframes to beziers"

    def execute(self, context):
        mocap_tools.fcurves_simplify()
        return {"FINISHED"}


class OBJECT_OT_LooperButton(bpy.types.Operator):
    bl_idname = "mocap.looper"
    bl_label = "loops animation / sampled mocap data"

    def execute(self, context):
        mocap_tools.autoloop_anim()
        return {"FINISHED"}


class OBJECT_OT_DenoiseButton(bpy.types.Operator):
    bl_idname = "mocap.denoise"
    bl_label = "Denoises sampled mocap data "

    def execute(self, context):
        return {"FINISHED"}


class OBJECT_OT_LimitDOFButton(bpy.types.Operator):
    bl_idname = "mocap.limitdof"
    bl_label = "Analyzes animations Max/Min DOF and adds hard/soft constraints"

    def execute(self, context):
        return {"FINISHED"}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()