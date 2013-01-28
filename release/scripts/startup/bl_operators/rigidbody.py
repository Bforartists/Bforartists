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

# <pep8-80 compliant>

import bpy
from bpy.types import Operator
from bpy.props import IntProperty
from bpy.props import EnumProperty


class CopyRigidbodySettings(Operator):
    '''Copy Rigid Body settings from active object to selected'''
    bl_idname = "rigidbody.object_settings_copy"
    bl_label = "Copy Rigid Body Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.rigid_body)

    def execute(self, context):
        obj = context.object
        scene = context.scene

        # deselect all but mesh objects
        for o in context.selected_objects:
            if o.type != 'MESH':
                o.select = False

        objects = context.selected_objects
        if objects:
            # add selected objects to active one groups and recalculate
            bpy.ops.group.objects_add_active()
            scene.frame_set(scene.frame_current)

            # copy settings
            for o in objects:
                if o.rigid_body is None:
                    continue
                
                o.rigid_body.type = obj.rigid_body.type
                o.rigid_body.kinematic = obj.rigid_body.kinematic
                o.rigid_body.mass = obj.rigid_body.mass
                o.rigid_body.collision_shape = obj.rigid_body.collision_shape
                o.rigid_body.use_margin = obj.rigid_body.use_margin
                o.rigid_body.collision_margin = obj.rigid_body.collision_margin
                o.rigid_body.friction = obj.rigid_body.friction
                o.rigid_body.restitution = obj.rigid_body.restitution
                o.rigid_body.use_deactivation = obj.rigid_body.use_deactivation
                o.rigid_body.start_deactivated = obj.rigid_body.start_deactivated
                o.rigid_body.deactivate_linear_velocity = obj.rigid_body.deactivate_linear_velocity
                o.rigid_body.deactivate_angular_velocity = obj.rigid_body.deactivate_angular_velocity
                o.rigid_body.linear_damping = obj.rigid_body.linear_damping
                o.rigid_body.angular_damping = obj.rigid_body.angular_damping
                o.rigid_body.collision_groups = obj.rigid_body.collision_groups

        return {'FINISHED'}


class BakeToKeyframes(Operator):
    '''Bake rigid body transformations of selected objects to keyframes'''
    bl_idname = "rigidbody.bake_to_keyframes"
    bl_label = "Bake To Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    frame_start = IntProperty(
            name="Start Frame",
            description="Start frame for baking",
            min=0, max=300000,
            default=1,
            )
    frame_end = IntProperty(
            name="End Frame",
            description="End frame for baking",
            min=1, max=300000,
            default=250,
            )
    step = IntProperty(
            name="Frame Step",
            description="Frame Step",
            min=1, max=120,
            default=1,
            )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.rigid_body)

    def execute(self, context):
        bake = []
        objects = []
        scene = context.scene
        frame_orig = scene.frame_current
        frames = list(range(self.frame_start, self.frame_end + 1, self.step))

        # filter objects selection
        for obj in context.selected_objects:
            if not obj.rigid_body or obj.rigid_body.type != 'ACTIVE':
                obj.select = False

        objects = context.selected_objects

        if objects:
            # store transformation data
            for f in list(range(self.frame_start, self.frame_end + 1)):
                scene.frame_set(f)
                if f in frames:
                    mat = {}
                    for i, obj in enumerate(objects):
                        mat[i] = obj.matrix_world.copy()
                    bake.append(mat)

            # apply transformations as keyframes
            for i, f in enumerate(frames):
                scene.frame_set(f)
                obj_prev = objects[0]
                for j, obj in enumerate(objects):
                    mat = bake[i][j]

                    obj.location = mat.to_translation()

                    rot_mode = obj.rotation_mode
                    if rot_mode == 'QUATERNION':
                        obj.rotation_quaternion = mat.to_quaternion()
                    elif rot_mode == 'AXIS_ANGLE':
                        # this is a little roundabout but there's no better way right now
                        aa = mat.to_quaternion().to_axis_angle()
                        obj.rotation_axis_angle = (aa[1], ) + aa[0][:]
                    else: # euler
                        # make sure euler rotation is compatible to previous frame
                        obj.rotation_euler = mat.to_euler(rot_mode, obj_prev.rotation_euler)

                    obj_prev = obj

                bpy.ops.anim.keyframe_insert(type='BUILTIN_KSI_LocRot', confirm_success=False)

            # remove baked objects from simulation
            bpy.ops.rigidbody.objects_remove()

            # clean up keyframes
            for obj in objects:
                action = obj.animation_data.action
                for fcu in action.fcurves:
                    keyframe_points = fcu.keyframe_points
                    i = 1
                    # remove unneeded keyframes
                    while i < len(keyframe_points) - 1:
                        val_prev = keyframe_points[i - 1].co[1]
                        val_next = keyframe_points[i + 1].co[1]
                        val = keyframe_points[i].co[1]

                        if abs(val - val_prev) + abs(val - val_next) < 0.0001:
                            keyframe_points.remove(keyframe_points[i])
                        else:
                            i += 1
                    # use linear interpolation for better visual results
                    for keyframe in keyframe_points:
                        keyframe.interpolation = 'LINEAR'

            # return to the frame we started on
            scene.frame_set(frame_orig)

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        self.frame_start = scene.frame_start
        self.frame_end = scene.frame_end

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class ConnectRigidBodies(Operator):
    '''Create rigid body constraints between selected and active rigid bodies'''
    bl_idname = "rigidbody.connect"
    bl_label = "Connect Rigid Bodies"
    bl_options = {'REGISTER', 'UNDO'}

    con_type = EnumProperty(
        name="Type",
        description="Type of generated constraint",
        # XXX Would be nice to get icons too, but currently not possible ;)
        items=tuple((e.identifier, e.name, e.description, e. value)
                    for e in bpy.types.RigidBodyConstraint.bl_rna.properties["type"].enum_items),
        default='FIXED',)

    pivot_type = EnumProperty(
        name="Location",
        description="Constraint pivot location",
        items=(('CENTER', "Center", "Pivot location is between the constrained rigid bodies"),
               ('ACTIVE', "Active", "Pivot location is at the active object position"),
               ('SELECTED', "Selected", "Pivot location is at the selected object position")),
        default='CENTER',)

    @classmethod
    def poll(cls, context):
        obj = context.object
        objects = context.selected_objects
        return (obj and obj.rigid_body and (len(objects) > 1))

    def execute(self, context):

        objects = context.selected_objects
        obj_act = context.active_object

        for obj in objects:
            if obj == obj_act:
                continue
            if self.pivot_type == 'ACTIVE':
                loc = obj_act.location
            elif self.pivot_type == 'SELECTED':
                loc = obj.location
            else:
                loc = (obj_act.location + obj.location) / 2.0
            bpy.ops.object.add(type='EMPTY', view_align=False, enter_editmode=False, location=loc)
            bpy.ops.rigidbody.constraint_add()
            con = context.active_object.rigid_body_constraint
            con.type = self.con_type
            con.object1 = obj_act
            con.object2 = obj
        # restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objs:
            obj.select = True;
        bpy.context.scene.objects.active = obj_act

        return {'FINISHED'}
