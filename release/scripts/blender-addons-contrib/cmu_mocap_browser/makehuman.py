# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

import bpy
from mathutils import Matrix, Quaternion
from math import radians


bindings = [d.split() for d in"""\
root MasterFloor
root Root
rhand Wrist_R
lhand Wrist_L
rfoot LegIK_R
lfoot LegIK_L
""".splitlines()]


T_pose_align = [d.split() for d in """\
clavicle UpArmRot 
humerus LoArm 
radius Hand .8
wrist Hand
hipjoint UpLeg 
femur LoLeg 
tibia Foot 
foot Toe""".splitlines()]


def scan_for_armature(objs, look_for_mhx=False):
    """
        scans the objects for armatures
    """
    for o in objs:
        if o.type != 'ARMATURE':
            continue
        if 'MhxRig' in o:
            if o['MhxRig'] == 'MHX' and look_for_mhx:
                return o
        else:
            if 'root' in o.data.bones and not look_for_mhx:
                return o
    return None


def scan_armatures(context):
    """
        scans the selected objects or the scene for a source (regular)
        armature and a destination (Make Human) armature
    """
    src = (
        scan_for_armature(context.selected_objects)
        or scan_for_armature(context.scene.objects)
        )
    dst = (
        scan_for_armature(context.selected_objects, look_for_mhx=True)
        or scan_for_armature(context.scene.objects, look_for_mhx=True)
        )
    if not src or not dst:
        raise LookupError("Couldn't find source or target armatures")
    return src, dst


class CMUMocapAlignArmatures(bpy.types.Operator):
    #
    "Align a CMU armature to a MakeHuman one for subsequent animation transfer"
    #
    bl_idname = "object.cmu_align"
    bl_label = "Align selected armatures at frame 0"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cml = context.user_preferences.addons['cmu_mocap_browser'].preferences
        self.src, self.dst = scan_armatures(context)
        context.scene.frame_set(0)

        SMW = self.src.matrix_world
        DMW = self.dst.matrix_world
        SPB = self.src.pose.bones
        DPB = self.dst.pose.bones

        # clear frame poses, leave source selected
        for o in self.dst, self.src:
            context.scene.objects.active = o
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.pose.rot_clear()
            bpy.ops.pose.loc_clear()
            bpy.ops.pose.scale_clear()

        # create the head IK target if it doesn't exist
        if 'head_ik' not in SPB:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.select_all(action='DESELECT')
            self.src.data.edit_bones['upperneck'].select_tail = True
            bpy.ops.armature.extrude()
            self.src.data.edit_bones[-1].name = 'head_ik'
            self.src.data.edit_bones[-1].use_connect = False
            bpy.ops.transform.translate(value=(.1, 0, 0))
            bpy.ops.armature.extrude()
            self.src.data.edit_bones[-1].name = 'head_pole'
            bpy.ops.transform.translate(value=(.1, 0, 0))
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')

        # get reference points
        a_s = SPB['upperneck'].matrix.translation
        c_s = SPB['lfemur'].matrix.translation
        b_s = .5 * (c_s + SPB['rfemur'].matrix.translation)
        a_d = DPB['Shoulders'].matrix.translation
        c_d = DPB['Hip_L'].matrix.translation
        b_d = .5 * (c_d + DPB['Hip_R'].matrix.translation)

        # get alignment matrix        
        S = Matrix().to_3x3()
        S[0] = (c_s - b_s).normalized()
        S[1] = (a_s - b_s).normalized()
        S[2] = -S[0].cross(S[1])
        S = SMW.to_3x3() * S
        D = Matrix().to_3x3()
        D[0] = (c_d - b_d).normalized()
        D[1] = (a_d - b_d).normalized()
        D[2] = -D[0].cross(D[1])
        D = DMW.to_3x3() * D
        T = D * S.transposed()

        # scale source to match destination
        s = (a_d - b_d).length / (a_s - b_s).length
        bpy.ops.transform.resize(value=(s, s, s))
        
        # align armatures
        rot = T.to_quaternion()
        bpy.ops.transform.rotate(value=rot.angle, axis=rot.axis)
        a_s = SPB['upperneck'].matrix.translation
        a_s = SMW * a_s
        bpy.ops.transform.translate(value=a_d - a_s)
        
        bpy.ops.pose.select_all(action='DESELECT')
        for bdef in T_pose_align:
            for side in "lr":
                sb = side + bdef[0]
                db = bdef[1] + "_" + side.upper()
                scale = 1. if len(bdef) == 2 else float(bdef[2])
                SPB[sb].bone.select = True
                a = SMW * SPB[sb].tail
                b = SMW * SPB[sb].head
                c = DMW * DPB[db].head
                rot = (a - b).rotation_difference(c - b)
                bpy.ops.transform.rotate(value=rot.angle, axis=rot.axis)
                s = (c - b).length / (a - b).length * scale
                bpy.ops.transform.resize(value=(s, s, s))
                if cml.feet_angle:
                    if bdef[0] == 'foot':
                        bpy.ops.transform.rotate(
                            value=radians(cml.feet_angle),
                            axis=(1, 0, 0)
                            )
                SPB[sb].bone.select = False

        SPB['head_ik'].bone.select = True
        b = SMW * SPB['head_ik'].head
        c = DMW * DPB['Head'].head
        bpy.ops.transform.translate(value=(c-b))

        # record pose
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.anim.keyframe_insert_menu(type='LocRotScale')
        return {'FINISHED'}


class CMUMocapTransferer(bpy.types.Operator):
    #
    "Transfer an animation to a MakeHuman armature"
    #
    bl_idname = "object.cmu_transfer"
    bl_label = "Transfer an animation to a MakeHuman armature"
    bl_options = {'REGISTER', 'UNDO'}

    timer = None
    bindings = None

    def set_inverses(self):
        self.inverses = {}
        for sb, db in bindings:
            D = self.dst.matrix_world * self.dst.pose.bones[db].matrix
            S = self.src.matrix_world * self.src.pose.bones[sb].matrix
            Sr = S.to_3x3().to_4x4()
            St = Sr.Translation(S.translation)
            self.inverses[db] = Sr.inverted() * St.inverted() * D

    def transfer_pose(self, frame):
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.rot_clear()
        bpy.ops.pose.loc_clear()
        for sb, db in bindings:
            self.dst.data.bones.active = self.dst.data.bones[db]
            S = self.src.pose.bones[sb].matrix
            S = self.src.matrix_world * self.src.pose.bones[sb].matrix
            self.dst.pose.bones[db].matrix = S * self.inverses[db]
            self.dst.pose.bones[db].keyframe_insert('rotation_quaternion', -1, frame, db)
            self.dst.pose.bones[db].keyframe_insert('location', -1, frame, db)
            bpy.context.scene.update()  # recalculate constraints
        # get locrot of fk bones and locally set them
        # ... TODO
#        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)
        if event.type == 'TIMER':
            context.scene.frame_set(self.frame)
            self.transfer_pose(self.frame)
            self.frame += 1
            if self.frame > self.end_frame:
                return self.cancel(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        cml = context.user_preferences.addons['cmu_mocap_browser'].preferences
        self.src, self.dst = scan_armatures(context)
        DPB = self.dst.pose.bones
        self.set_inverses()
        context.scene.frame_set(0)
        context.scene.objects.active = self.dst
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')
        for sb, db, cc in [
            ('rradius', 'UpArm_R', 1),
            ('lradius', 'UpArm_L', 1),
            ('rtibia', 'UpLeg_R', 1),
            ('ltibia', 'UpLeg_L', 1),
            ('upperneck', 'Spine3', 4),
            ('head_ik', 'Neck', 1),
            ]:
            self.dst.data.bones.active = self.dst.data.bones[db]
            name = "CMU IK " + sb
            if name not in DPB[db].constraints:
                if 'IK' not in DPB[db].constraints:
                    bpy.ops.pose.constraint_add(type='IK')
                c = DPB[db].constraints["IK"]
                c.name = name
                for i in range(3):
                    bpy.ops.constraint.move_up(constraint=name, owner='BONE')
            c = DPB[db].constraints[name]
            c.target = self.src
            c.subtarget = sb
            if sb == "head_ik":
                c.pole_target = self.src
                c.pole_subtarget = "head_pole"
                c.pole_angle = radians(90)
            else:
                c.pole_target = None
            c.influence = 1
            DPB[db].constraints[name].chain_count = cc

        if cml.floor:
            floor = bpy.data.objects[cml.floor]
            for side in "LR":
                db = "ToeRev_" + side
                self.dst.data.bones.active = self.dst.data.bones[db]
                name = "CMU FLOOR"
                if name not in DPB[db].constraints:
                    bpy.ops.pose.constraint_add(type='FLOOR')
                    c = DPB[db].constraints["Floor"]
                    c.name = name
                    c.target = floor
        
        bpy.ops.mhx.toggle_fk_ik(toggle="MhaArmIk_L 1 2 3")
        bpy.ops.mhx.toggle_fk_ik(toggle="MhaArmIk_R 1 18 19")
        bpy.ops.mhx.toggle_fk_ik(toggle="MhaLegIk_L 1 4 5")
        bpy.ops.mhx.toggle_fk_ik(toggle="MhaLegIk_R 1 20 21")

        self.frame, self.end_frame = self.src.animation_data.action.frame_range
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.\
            event_timer_add(0.001, context.window)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        context.window_manager.event_timer_remove(self.timer)
        bpy.ops.object.mode_set(mode='OBJECT')

