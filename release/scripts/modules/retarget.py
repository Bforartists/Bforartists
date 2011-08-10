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
from mathutils import *
from math import radians, acos
import cProfile


def hasIKConstraint(pose_bone):
    #utility function / predicate, returns True if given bone has IK constraint
    ik = [constraint for constraint in pose_bone.constraints if constraint.type == "IK"]
    if ik:
        return ik[0]
    else:
        return False


def createDictionary(perf_arm, end_arm):
    # clear any old data
    for end_bone in end_arm.bones:
        for mapping in end_bone.reverseMap:
            end_bone.reverseMap.remove(0)

    for perf_bone in perf_arm.bones:
        #find its match and add perf_bone to the match's mapping
        if perf_bone.map:
            end_bone = end_arm.bones[perf_bone.map]
            newMap = end_bone.reverseMap.add()
            newMap.name = perf_bone.name
            end_bone.foot = perf_bone.foot

    #root is the root of the enduser
    root = end_arm.bones[0].name
    feetBones = [bone.name for bone in perf_arm.bones if bone.foot]
    return feetBones, root

def loadMapping(perf_arm, end_arm):

    for end_bone in end_arm.bones:
        #find its match and add perf_bone to the match's mapping
        if end_bone.reverseMap:
            for perf_bone in end_bone.reverseMap:
                perf_arm.bones[perf_bone.name].map = end_bone.name

#creation of intermediate armature
# the intermediate armature has the hiearchy of the end user,
# does not have rotation inheritence
# and bone roll is identical to the performer
# its purpose is to copy over the rotations
# easily while concentrating on the hierarchy changes


def createIntermediate(performer_obj, enduser_obj, root, s_frame, e_frame, scene):
    #creates and keyframes an empty with its location
    #the original position of the tail bone
    #useful for storing the important data in the original motion
    #i.e. using this empty to IK the chain to that pos / DEBUG

    #Simple 1to1 retarget of a bone
    def singleBoneRetarget(inter_bone, perf_bone):
            perf_world_rotation = perf_bone.matrix * performer_obj.matrix_world
            inter_world_base_rotation = inter_bone.bone.matrix_local * inter_obj.matrix_world
            inter_world_base_inv = Matrix(inter_world_base_rotation)
            inter_world_base_inv.invert()
            return (inter_world_base_inv.to_3x3() * perf_world_rotation.to_3x3()).to_4x4()

    #uses 1to1 and interpolation/averaging to match many to 1 retarget
    def manyPerfToSingleInterRetarget(inter_bone, performer_bones_s):
        retarget_matrices = [singleBoneRetarget(inter_bone, perf_bone) for perf_bone in performer_bones_s]
        lerp_matrix = Matrix()
        for i in range(len(retarget_matrices) - 1):
            first_mat = retarget_matrices[i]
            next_mat = retarget_matrices[i + 1]
            lerp_matrix = first_mat.lerp(next_mat, 0.5)
        return lerp_matrix

    #determines the type of hierachy change needed and calls the
    #right function
    def retargetPerfToInter(inter_bone):
        if inter_bone.bone.reverseMap:
            perf_bone_name = inter_bone.bone.reverseMap
                # 1 to many not supported yet
                # then its either a many to 1 or 1 to 1
            if len(perf_bone_name) > 1:
                performer_bones_s = [performer_bones[map.name] for map in perf_bone_name]
                #we need to map several performance bone to a single
                inter_bone.matrix_basis = manyPerfToSingleInterRetarget(inter_bone, performer_bones_s)
            else:
                perf_bone = performer_bones[perf_bone_name[0].name]
                inter_bone.matrix_basis = singleBoneRetarget(inter_bone, perf_bone)
        inter_bone.keyframe_insert("rotation_quaternion")

    #creates the intermediate armature object
    inter_obj = enduser_obj.copy()
    inter_obj.data = inter_obj.data.copy()  # duplicate data
    bpy.context.scene.objects.link(inter_obj)
    inter_obj.name = "intermediate"
    bpy.context.scene.objects.active = inter_obj
    bpy.ops.object.mode_set(mode='EDIT')
    #add some temporary connecting bones in case end user bones are not connected to their parents
    print("creating temp bones")
    for bone in inter_obj.data.edit_bones:
        if not bone.use_connect and bone.parent:
            if inter_obj.data.bones[bone.parent.name].reverseMap or inter_obj.data.bones[bone.name].reverseMap:
                newBone = inter_obj.data.edit_bones.new("Temp")
                newBone.head = bone.parent.tail
                newBone.tail = bone.head
                newBone.parent = bone.parent
                bone.parent = newBone
                bone.use_connect = True
                newBone.use_connect = True
    #resets roll
    print("retargeting to intermediate")
    bpy.ops.armature.calculate_roll(type='Z')
    bpy.ops.object.mode_set(mode="OBJECT")
    inter_obj.data.name = "inter_arm"
    inter_arm = inter_obj.data
    performer_bones = performer_obj.pose.bones
    inter_bones = inter_obj.pose.bones
    #clears inheritance
    for inter_bone in inter_bones:
        if inter_bone.bone.reverseMap:
            inter_bone.bone.use_inherit_rotation = False
        else:
            inter_bone.bone.use_inherit_rotation = True

    for t in range(s_frame, e_frame):
        if (t - s_frame) % 10 == 0:
            print("First pass: retargeting frame {0}/{1}".format(t, e_frame - s_frame))
        scene.frame_set(t)
        for bone in inter_bones:
            retargetPerfToInter(bone)

    return inter_obj

# this procedure copies the rotations over from the intermediate
# armature to the end user one.
# As the hierarchies are 1 to 1, this is a simple matter of
# copying the rotation, while keeping in mind bone roll, parenting, etc.
# TODO: Control Bones: If a certain bone is constrained in a way
#       that its rotation is determined by another (a control bone)
#       We should determine the right pos of the control bone.
#       Scale: ? Should work but needs testing.


def retargetEnduser(inter_obj, enduser_obj, root, s_frame, e_frame, scene):
    inter_bones = inter_obj.pose.bones
    end_bones = enduser_obj.pose.bones

    def bakeTransform(end_bone):
        src_bone = inter_bones[end_bone.name]
        trg_bone = end_bone
        bake_matrix = src_bone.matrix
        rest_matrix = trg_bone.bone.matrix_local

        if trg_bone.parent and trg_bone.bone.use_inherit_rotation:
            srcParent = src_bone.parent
            if "Temp" in srcParent.name:
                srcParent = srcParent.parent
            parent_mat = srcParent.matrix
            parent_rest = trg_bone.parent.bone.matrix_local
            parent_rest_inv = parent_rest.copy()
            parent_rest_inv.invert()
            parent_mat_inv = parent_mat.copy()
            parent_mat_inv.invert()
            bake_matrix = parent_mat_inv * bake_matrix
            rest_matrix = parent_rest_inv * rest_matrix

        rest_matrix_inv = rest_matrix.copy()
        rest_matrix_inv.invert()
        bake_matrix = rest_matrix_inv * bake_matrix
        end_bone.matrix_basis = bake_matrix
        rot_mode = end_bone.rotation_mode
        if rot_mode == "QUATERNION":
            end_bone.keyframe_insert("rotation_quaternion")
        elif rot_mode == "AXIS_ANGLE":
            end_bone.keyframe_insert("rotation_axis_angle")
        else:
            end_bone.keyframe_insert("rotation_euler")
        if not end_bone.bone.use_connect:
            end_bone.keyframe_insert("location")

        for bone in end_bone.children:
            bakeTransform(bone)

    for t in range(s_frame, e_frame):
        if (t - s_frame) % 10 == 0:
            print("Second pass: retargeting frame {0}/{1}".format(t, e_frame - s_frame))
        scene.frame_set(t)
        end_bone = end_bones[root]
        end_bone.location = Vector((0, 0, 0))
        end_bone.keyframe_insert("location")
        bakeTransform(end_bone)

#recieves the performer feet bones as a variable
# by "feet" I mean those bones that have plants
# (they don't move, despite root moving) somewhere in the animation.


def copyTranslation(performer_obj, enduser_obj, perfFeet, root, s_frame, e_frame, scene, enduser_obj_mat):

    perf_bones = performer_obj.pose.bones
    end_bones = enduser_obj.pose.bones

    perfRoot = perf_bones[0].name
    endFeet = [perf_bones[perfBone].bone.map for perfBone in perfFeet]
    locDictKeys = perfFeet + endFeet + [perfRoot]

    def tailLoc(bone):
        return bone.center + (bone.vector / 2)

    #Step 1 - we create a dict that contains these keys:
    #(Performer) Hips, Feet
    #(End user) Feet
    # where the values are their world position on each frame in range (s,e)

    locDict = {}
    for key in locDictKeys:
        locDict[key] = []

    for t in range(scene.frame_start, scene.frame_end):
        scene.frame_set(t)
        for bone in perfFeet:
            locDict[bone].append(tailLoc(perf_bones[bone]))
        locDict[perfRoot].append(tailLoc(perf_bones[perfRoot]))
        for bone in endFeet:
            locDict[bone].append(tailLoc(end_bones[bone]))

    # now we take our locDict and analyze it.
    # we need to derive all chains

    locDeriv = {}
    for key in locDictKeys:
        locDeriv[key] = []

    for key in locDict.keys():
        graph = locDict[key]
        locDeriv[key] = [graph[t + 1] - graph[t] for t in range(len(graph) - 1)]

    # now find the plant frames, where perfFeet don't move much

    linearAvg = []

    for key in perfFeet:
        for i in range(len(locDeriv[key]) - 1):
            v = locDeriv[key][i]
            hipV = locDeriv[perfRoot][i]
            endV = locDeriv[perf_bones[key].bone.map][i]
            if (v.length < 0.1):
                #this is a plant frame.
                #lets see what the original hip delta is, and the corresponding
                #end bone's delta
                if endV.length != 0:
                    linearAvg.append(hipV.length / endV.length)

    action_name = performer_obj.animation_data.action.name
    #is there a stride_bone?
    if "stride_bone" in bpy.data.objects:
        stride_action = bpy.data.actions.new("Stride Bone " + action_name)
        stride_bone = enduser_obj.parent
        stride_bone.animation_data.action = stride_action
    else:
        bpy.ops.object.add()
        stride_bone = bpy.context.active_object
        stride_bone.name = "stride_bone"
    print(stride_bone)
    stride_bone.location = Vector((0, 0, 0))
    if linearAvg:
        #determine the average change in scale needed
        avg = sum(linearAvg) / len(linearAvg)
        scene.frame_set(s_frame)
        initialPos = (tailLoc(perf_bones[perfRoot]) / avg) + stride_bone.location
        for t in range(s_frame, e_frame):
            scene.frame_set(t)
            #calculate the new position, by dividing by the found ratio between performer and enduser
            newTranslation = (tailLoc(perf_bones[perfRoot]) / avg)
            stride_bone.location = enduser_obj_mat * (newTranslation - initialPos)
            stride_bone.keyframe_insert("location")
    stride_bone.animation_data.action.name = ("Stride Bone " + action_name)

    return stride_bone


def IKRetarget(performer_obj, enduser_obj, s_frame, e_frame, scene):
    end_bones = enduser_obj.pose.bones
    for pose_bone in end_bones:
        ik_constraint = hasIKConstraint(pose_bone)
        if ik_constraint:
            target_is_bone = False
            # set constraint target to corresponding empty if targetless,
            # if not, keyframe current target to corresponding empty
            perf_bone = pose_bone.bone.reverseMap[-1].name
            orgLocTrg = originalLocationTarget(pose_bone, enduser_obj)
            if not ik_constraint.target:
                ik_constraint.target = orgLocTrg
                target = orgLocTrg

            # There is a target now
            if ik_constraint.subtarget:
                target = ik_constraint.target.pose.bones[ik_constraint.subtarget]
                target.bone.use_local_location = False
                target_is_bone = True
            else:
                target = ik_constraint.target

            # bake the correct locations for the ik target bones
            for t in range(s_frame, e_frame):
                scene.frame_set(t)
                if target_is_bone:
                    final_loc = pose_bone.tail - target.bone.matrix_local.to_translation()
                else:
                    final_loc = pose_bone.tail
                target.location = final_loc
                target.keyframe_insert("location")
            ik_constraint.mute = False
    scene.frame_set(s_frame)


def turnOffIK(enduser_obj):
    end_bones = enduser_obj.pose.bones
    for pose_bone in end_bones:
        if pose_bone.is_in_ik_chain:
            pass
            # TODO:
            # set stiffness according to place on chain
            # and values from analysis that is stored in the bone
            #pose_bone.ik_stiffness_x = 0.5
            #pose_bone.ik_stiffness_y = 0.5
            #pose_bone.ik_stiffness_z = 0.5
        ik_constraint = hasIKConstraint(pose_bone)
        if ik_constraint:
            ik_constraint.mute = True


#copy the object matrixes and clear them (to be reinserted later)
def cleanAndStoreObjMat(performer_obj, enduser_obj):
    perf_obj_mat = performer_obj.matrix_world.copy()
    enduser_obj_mat = enduser_obj.matrix_world.copy()
    zero_mat = Matrix()
    performer_obj.matrix_world = zero_mat
    enduser_obj.matrix_world = zero_mat
    return perf_obj_mat, enduser_obj_mat


#restore the object matrixes after parenting the auto generated IK empties
def restoreObjMat(performer_obj, enduser_obj, perf_obj_mat, enduser_obj_mat, stride_bone):
    pose_bones = enduser_obj.pose.bones
    for pose_bone in pose_bones:
        if pose_bone.name + "Org" in bpy.data.objects:
            empty = bpy.data.objects[pose_bone.name + "Org"]
            empty.parent = stride_bone
    performer_obj.matrix_world = perf_obj_mat
    enduser_obj.parent = stride_bone
    enduser_obj.matrix_world = enduser_obj_mat


#create (or return if exists) the related IK empty to the bone
def originalLocationTarget(end_bone, enduser_obj):
    if not end_bone.name + "Org" in bpy.data.objects:
        bpy.ops.object.add()
        empty = bpy.context.active_object
        empty.name = end_bone.name + "Org"
        empty.empty_draw_size = 0.1
        empty.parent = enduser_obj
    empty = bpy.data.objects[end_bone.name + "Org"]
    return empty


#create the specified NLA setup for base animation, constraints and tweak layer.
def NLASystemInitialize(enduser_arm, context):#enduser_obj, name):
    enduser_obj = context.active_object
    NLATracks = enduser_arm.mocapNLATracks[enduser_obj.data.active_mocap]
    name = NLATracks.name
    anim_data = enduser_obj.animation_data
    s_frame = 0
    print(name)
    if ("Base " + name) in bpy.data.actions:
        mocapAction = bpy.data.actions[("Base " + name)]
    else:
        print("That retargeted anim has no base action")
    anim_data.use_nla = True
    for track in anim_data.nla_tracks:
        anim_data.nla_tracks.remove(track)
    mocapTrack = anim_data.nla_tracks.new()
    mocapTrack.name = "Base " + name
    NLATracks.base_track = mocapTrack.name
    mocapStrip = mocapTrack.strips.new("Base " + name, s_frame, mocapAction)
    constraintTrack = anim_data.nla_tracks.new()
    constraintTrack.name = "Auto fixes " + name
    NLATracks.auto_fix_track = constraintTrack.name
    if ("Auto fixes " + name) in bpy.data.actions:
        constraintAction = bpy.data.actions[("Auto fixes " + name)]
    else:
        constraintAction = bpy.data.actions.new("Auto fixes " + name)
    constraintStrip = constraintTrack.strips.new("Auto fixes " + name, s_frame, constraintAction)
    constraintStrip.extrapolation = "NOTHING"
    userTrack = anim_data.nla_tracks.new()
    userTrack.name = "Manual fixes " + name
    NLATracks.manual_fix_track = userTrack.name
    if ("Manual fixes " + name) in bpy.data.actions:
        userAction = bpy.data.actions[("Manual fixes " + name)]
    else:
        userAction = bpy.data.actions.new("Manual fixes " + name)
    userStrip = userTrack.strips.new("Manual fixes " + name, s_frame, userAction)
    userStrip.extrapolation = "HOLD"
    #userStrip.blend_type = "MULITPLY" - doesn't work due to work, will be activated soon
    anim_data.nla_tracks.active = constraintTrack
    #anim_data.action = constraintAction
    anim_data.action_extrapolation = "NOTHING"
    #set the stride_bone's action
    if "stride_bone" in bpy.data.objects:
        stride_bone = bpy.data.objects["stride_bone"]
        if NLATracks.stride_action:
            stride_bone.animation_data.action = bpy.data.actions[NLATracks.stride_action]
        else:
            NLATracks.stride_action = stride_bone.animation_data.action.name
    anim_data.action = None


#Main function that runs the retargeting sequence.
def totalRetarget(performer_obj, enduser_obj, scene, s_frame, e_frame):
    perf_arm = performer_obj.data
    end_arm = enduser_obj.data
    
    try:
        enduser_obj.animation_data.action = bpy.data.actions.new("temp")
    except:
        print("no need to create new action")
    
    
    print("creating Dictionary")
    feetBones, root = createDictionary(perf_arm, end_arm)
    print("cleaning stuff up")
    perf_obj_mat, enduser_obj_mat = cleanAndStoreObjMat(performer_obj, enduser_obj)
    turnOffIK(enduser_obj)
    print("Creating intermediate armature (for first pass)")
    inter_obj = createIntermediate(performer_obj, enduser_obj, root, s_frame, e_frame, scene)
    print("First pass: retargeting from intermediate to end user")

        
    retargetEnduser(inter_obj, enduser_obj, root, s_frame, e_frame, scene)
    name = performer_obj.animation_data.action.name
    enduser_obj.animation_data.action.name = "Base " + name
    print("Second pass: retargeting root translation and clean up")
    stride_bone = copyTranslation(performer_obj, enduser_obj, feetBones, root, s_frame, e_frame, scene, enduser_obj_mat)
    IKRetarget(performer_obj, enduser_obj, s_frame, e_frame, scene)
    restoreObjMat(performer_obj, enduser_obj, perf_obj_mat, enduser_obj_mat, stride_bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_name(name=inter_obj.name, extend=False)
    bpy.ops.object.delete()
    bpy.ops.object.select_name(name=enduser_obj.name, extend=False)

    if not name in [tracks.name for tracks in end_arm.mocapNLATracks]:
        NLATracks = end_arm.mocapNLATracks.add()
        NLATracks.name = name
    else:
        NLATracks = end_arm.mocapNLATracks[name]
    end_arm.active_mocap = name
    print("retargeting done!")

if __name__ == "__main__":
    totalRetarget()
