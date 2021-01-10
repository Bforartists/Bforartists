#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy
import math
from mathutils import Vector, Matrix, Color
from rna_prop_ui import rna_idprop_ui_prop_get

from .errors import MetarigError
from .naming import get_name, make_derived_name, is_control_bone
from .misc import pairwise

#=======================
# Bone collection
#=======================

class BoneDict(dict):
    """
    Special dictionary for holding bone names in a structured way.

    Allows access to contained items as attributes, and only
    accepts certain types of values.
    """

    @staticmethod
    def __sanitize_attr(key, value):
        if hasattr(BoneDict, key):
            raise KeyError("Invalid BoneDict key: %s" % (key))

        if (value is None or
            isinstance(value, str) or
            isinstance(value, list) or
            isinstance(value, BoneDict)):
            return value

        if isinstance(value, dict):
            return BoneDict(value)

        raise ValueError("Invalid BoneDict value: %r" % (value))

    def __init__(self, *args, **kwargs):
        super().__init__()

        for key, value in dict(*args, **kwargs).items():
            dict.__setitem__(self, key, BoneDict.__sanitize_attr(key, value))

        self.__dict__ = self

    def __repr__(self):
        return "BoneDict(%s)" % (dict.__repr__(self))

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, BoneDict.__sanitize_attr(key, value))

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            dict.__setitem__(self, key, BoneDict.__sanitize_attr(key, value))

    def flatten(self, key=None):
        """Return all contained bones or a single key as a list."""

        items = [self[key]] if key is not None else self.values()

        all_bones = []

        for item in items:
            if isinstance(item, BoneDict):
                all_bones.extend(item.flatten())
            elif isinstance(item, list):
                all_bones.extend(item)
            elif item is not None:
                all_bones.append(item)

        return all_bones

#=======================
# Bone manipulation
#=======================
#
# NOTE: PREFER USING BoneUtilityMixin IN NEW STYLE RIGS!

def get_bone(obj, bone_name):
    """Get EditBone or PoseBone by name, depending on the current mode."""
    if not bone_name:
        return None
    bones = obj.data.edit_bones if obj.mode == 'EDIT' else obj.pose.bones
    if bone_name not in bones:
        raise MetarigError("bone '%s' not found" % bone_name)
    return bones[bone_name]


def new_bone(obj, bone_name):
    """ Adds a new bone to the given armature object.
        Returns the resulting bone's name.
    """
    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        edit_bone = obj.data.edit_bones.new(bone_name)
        name = edit_bone.name
        edit_bone.head = (0, 0, 0)
        edit_bone.tail = (0, 1, 0)
        edit_bone.roll = 0
        return name
    else:
        raise MetarigError("Can't add new bone '%s' outside of edit mode" % bone_name)


def copy_bone(obj, bone_name, assign_name='', *, parent=False, inherit_scale=False, bbone=False, length=None, scale=None):
    """ Makes a copy of the given bone in the given armature object.
        Returns the resulting bone's name.
    """
    #if bone_name not in obj.data.bones:
    if bone_name not in obj.data.edit_bones:
        raise MetarigError("copy_bone(): bone '%s' not found, cannot copy it" % bone_name)

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        if assign_name == '':
            assign_name = bone_name
        # Copy the edit bone
        edit_bone_1 = obj.data.edit_bones[bone_name]
        edit_bone_2 = obj.data.edit_bones.new(assign_name)
        bone_name_1 = bone_name
        bone_name_2 = edit_bone_2.name

        # Copy edit bone attributes
        edit_bone_2.layers = list(edit_bone_1.layers)

        edit_bone_2.head = Vector(edit_bone_1.head)
        edit_bone_2.tail = Vector(edit_bone_1.tail)
        edit_bone_2.roll = edit_bone_1.roll

        if parent:
            edit_bone_2.parent = edit_bone_1.parent
            edit_bone_2.use_connect = edit_bone_1.use_connect

            edit_bone_2.use_inherit_rotation = edit_bone_1.use_inherit_rotation
            edit_bone_2.use_local_location = edit_bone_1.use_local_location

        if parent or inherit_scale:
            edit_bone_2.inherit_scale = edit_bone_1.inherit_scale

        if bbone:
            for name in ['bbone_segments',
                         'bbone_easein', 'bbone_easeout',
                         'bbone_rollin', 'bbone_rollout',
                         'bbone_curveinx', 'bbone_curveiny', 'bbone_curveoutx', 'bbone_curveouty',
                         'bbone_scaleinx', 'bbone_scaleiny', 'bbone_scaleoutx', 'bbone_scaleouty']:
                setattr(edit_bone_2, name, getattr(edit_bone_1, name))

        # Resize the bone after copy if requested
        if length is not None:
            edit_bone_2.length = length
        elif scale is not None:
            edit_bone_2.length *= scale

        return bone_name_2
    else:
        raise MetarigError("Cannot copy bones outside of edit mode")


def copy_bone_properties(obj, bone_name_1, bone_name_2, transforms=True, props=True, widget=True):
    """ Copy transform and custom properties from bone 1 to bone 2. """
    if obj.mode in {'OBJECT','POSE'}:
        # Get the pose bones
        pose_bone_1 = obj.pose.bones[bone_name_1]
        pose_bone_2 = obj.pose.bones[bone_name_2]

        # Copy pose bone attributes
        if transforms:
            pose_bone_2.rotation_mode = pose_bone_1.rotation_mode
            pose_bone_2.rotation_axis_angle = tuple(pose_bone_1.rotation_axis_angle)
            pose_bone_2.rotation_euler = tuple(pose_bone_1.rotation_euler)
            pose_bone_2.rotation_quaternion = tuple(pose_bone_1.rotation_quaternion)

            pose_bone_2.lock_location = tuple(pose_bone_1.lock_location)
            pose_bone_2.lock_scale = tuple(pose_bone_1.lock_scale)
            pose_bone_2.lock_rotation = tuple(pose_bone_1.lock_rotation)
            pose_bone_2.lock_rotation_w = pose_bone_1.lock_rotation_w
            pose_bone_2.lock_rotations_4d = pose_bone_1.lock_rotations_4d

        # Copy custom properties
        if props:
            from .mechanism import copy_custom_properties

            copy_custom_properties(pose_bone_1, pose_bone_2)

        if widget:
            pose_bone_2.custom_shape = pose_bone_1.custom_shape
    else:
        raise MetarigError("Cannot copy bone properties in edit mode")


def _legacy_copy_bone(obj, bone_name, assign_name=''):
    """LEGACY ONLY, DON'T USE"""
    new_name = copy_bone(obj, bone_name, assign_name, parent=True, bbone=True)
    # Mode switch PER BONE CREATION?!
    bpy.ops.object.mode_set(mode='OBJECT')
    copy_bone_properties(obj, bone_name, new_name)
    bpy.ops.object.mode_set(mode='EDIT')
    return new_name


def flip_bone(obj, bone_name):
    """ Flips an edit bone.
    """
    if bone_name not in obj.data.edit_bones:
        raise MetarigError("flip_bone(): bone '%s' not found, cannot copy it" % bone_name)

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        bone = obj.data.edit_bones[bone_name]
        head = Vector(bone.head)
        tail = Vector(bone.tail)
        bone.tail = head + tail
        bone.head = tail
        bone.tail = head
    else:
        raise MetarigError("Cannot flip bones outside of edit mode")


def flip_bone_chain(obj, bone_names):
    """Flips a connected bone chain."""
    assert obj.mode == 'EDIT'

    bones = [ obj.data.edit_bones[name] for name in bone_names ]

    # Verify chain and unparent
    for prev_bone, bone in pairwise(bones):
        assert bone.parent == prev_bone and bone.use_connect

    for bone in bones:
        bone.parent = None
        bone.use_connect = False
        for child in bone.children:
            child.use_connect = False

    # Flip bones
    for bone in bones:
        head, tail = Vector(bone.head), Vector(bone.tail)
        bone.tail = head + tail
        bone.head, bone.tail = tail, head

    # Re-parent
    for bone, next_bone in pairwise(bones):
        bone.parent = next_bone
        bone.use_connect = True


def put_bone(obj, bone_name, pos, *, matrix=None, length=None, scale=None):
    """ Places a bone at the given position.
    """
    if bone_name not in obj.data.edit_bones:
        raise MetarigError("put_bone(): bone '%s' not found, cannot move it" % bone_name)

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        bone = obj.data.edit_bones[bone_name]

        if matrix is not None:
            old_len = len(matrix)
            matrix = matrix.to_4x4()

            if pos is not None:
                matrix.translation = pos
            elif old_len < 4:
                matrix.translation = bone.head

            bone.matrix = matrix

        else:
            delta = pos - bone.head
            bone.translate(delta)

        if length is not None:
            bone.length = length
        elif scale is not None:
            bone.length *= scale
    else:
        raise MetarigError("Cannot 'put' bones outside of edit mode")


def disable_bbones(obj, bone_names):
    """Disables B-Bone segments on the specified bones."""
    assert(obj.mode != 'EDIT')
    for bone in bone_names:
        obj.data.bones[bone].bbone_segments = 1


def _legacy_make_nonscaling_child(obj, bone_name, location, child_name_postfix=""):
    """ Takes the named bone and creates a non-scaling child of it at
        the given location.  The returned bone (returned by name) is not
        a true child, but behaves like one sans inheriting scaling.

        It is intended as an intermediate construction to prevent rig types
        from scaling with their parents.  The named bone is assumed to be
        an ORG bone.

        LEGACY ONLY, DON'T USE
    """
    if bone_name not in obj.data.edit_bones:
        raise MetarigError("make_nonscaling_child(): bone '%s' not found, cannot copy it" % bone_name)

    if obj == bpy.context.active_object and bpy.context.mode == 'EDIT_ARMATURE':
        # Create desired names for bones
        name1 = make_derived_name(bone_name, 'mch', child_name_postfix + "_ns_ch")
        name2 = make_derived_name(bone_name, 'mch', child_name_postfix + "_ns_intr")

        # Create bones
        child = copy_bone(obj, bone_name, name1)
        intermediate_parent = copy_bone(obj, bone_name, name2)

        # Get edit bones
        eb = obj.data.edit_bones
        child_e = eb[child]
        intrpar_e = eb[intermediate_parent]

        # Parenting
        child_e.use_connect = False
        child_e.parent = None

        intrpar_e.use_connect = False
        intrpar_e.parent = eb[bone_name]

        # Positioning
        child_e.length *= 0.5
        intrpar_e.length *= 0.25

        put_bone(obj, child, location)
        put_bone(obj, intermediate_parent, location)

        # Object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        pb = obj.pose.bones

        # Add constraints
        con = pb[child].constraints.new('COPY_LOCATION')
        con.name = "parent_loc"
        con.target = obj
        con.subtarget = intermediate_parent

        con = pb[child].constraints.new('COPY_ROTATION')
        con.name = "parent_loc"
        con.target = obj
        con.subtarget = intermediate_parent

        bpy.ops.object.mode_set(mode='EDIT')

        return child
    else:
        raise MetarigError("Cannot make nonscaling child outside of edit mode")


#===================================
# Bone manipulation as rig methods
#===================================


class BoneUtilityMixin(object):
    """
    Provides methods for more convenient creation of bones.

    Requires self.obj to be the armature object being worked on.
    """
    def register_new_bone(self, new_name, old_name=None):
        """Registers creation or renaming of a bone based on old_name"""
        pass

    def new_bone(self, new_name):
        """Create a new bone with the specified name."""
        name = new_bone(self.obj, new_name)
        self.register_new_bone(name)
        return name

    def copy_bone(self, bone_name, new_name='', *, parent=False, inherit_scale=False, bbone=False, length=None, scale=None):
        """Copy the bone with the given name, returning the new name."""
        name = copy_bone(self.obj, bone_name, new_name, parent=parent, inherit_scale=inherit_scale, bbone=bbone, length=length, scale=scale)
        self.register_new_bone(name, bone_name)
        return name

    def copy_bone_properties(self, src_name, tgt_name, *, props=True, ui_controls=None, **kwargs):
        """Copy pose-mode properties of the bone."""
        if props:
            if ui_controls is None and is_control_bone(tgt_name) and hasattr(self, 'script'):
                ui_controls = [tgt_name]
            elif ui_controls is True:
                ui_controls = self.bones.flatten('ctrl')

        copy_bone_properties(self.obj, src_name, tgt_name, props=props and not ui_controls, **kwargs)

        if props and ui_controls:
            from .mechanism import copy_custom_properties_with_ui
            copy_custom_properties_with_ui(self, src_name, tgt_name, ui_controls=ui_controls)

    def rename_bone(self, old_name, new_name):
        """Rename the bone, returning the actual new name."""
        bone = self.get_bone(old_name)
        bone.name = new_name
        if bone.name != old_name:
            self.register_new_bone(bone.name, old_name)
        return bone.name

    def get_bone(self, bone_name):
        """Get EditBone or PoseBone by name, depending on the current mode."""
        return get_bone(self.obj, bone_name)

    def get_bone_parent(self, bone_name):
        """Get the name of the parent bone, or None."""
        return get_name(self.get_bone(bone_name).parent)

    def set_bone_parent(self, bone_name, parent_name, use_connect=False, inherit_scale=None):
        """Set the parent of the bone."""
        eb = self.obj.data.edit_bones
        bone = eb[bone_name]
        if use_connect is not None:
            bone.use_connect = use_connect
        if inherit_scale is not None:
            bone.inherit_scale = inherit_scale
        bone.parent = (eb[parent_name] if parent_name else None)

    def parent_bone_chain(self, bone_names, use_connect=None, inherit_scale=None):
        """Link bones into a chain with parenting. First bone may be None."""
        for parent, child in pairwise(bone_names):
            self.set_bone_parent(child, parent, use_connect=use_connect, inherit_scale=inherit_scale)

#=============================================
# B-Bones
#=============================================

def connect_bbone_chain_handles(obj, bone_names):
    assert obj.mode == 'EDIT'

    for prev_name, next_name in pairwise(bone_names):
        prev_bone = get_bone(obj, prev_name)
        next_bone = get_bone(obj, next_name)

        prev_bone.bbone_handle_type_end = 'ABSOLUTE'
        prev_bone.bbone_custom_handle_end = next_bone

        next_bone.bbone_handle_type_start = 'ABSOLUTE'
        next_bone.bbone_custom_handle_start = prev_bone

#=============================================
# Math
#=============================================


def is_same_position(obj, bone_name1, bone_name2):
    head1 = get_bone(obj, bone_name1).head
    head2 = get_bone(obj, bone_name2).head

    return (head1 - head2).length < 1e-5


def is_connected_position(obj, bone_name1, bone_name2):
    tail1 = get_bone(obj, bone_name1).tail
    head2 = get_bone(obj, bone_name2).head

    return (tail1 - head2).length < 1e-5


def copy_bone_position(obj, bone_name, target_bone_name, *, length=None, scale=None):
    """ Completely copies the position and orientation of the bone. """
    bone1_e = obj.data.edit_bones[bone_name]
    bone2_e = obj.data.edit_bones[target_bone_name]

    bone2_e.head = bone1_e.head
    bone2_e.tail = bone1_e.tail
    bone2_e.roll = bone1_e.roll

    # Resize the bone after copy if requested
    if length is not None:
        bone2_e.length = length
    elif scale is not None:
        bone2_e.length *= scale


def align_bone_orientation(obj, bone_name, target_bone_name):
    """ Aligns the orientation of bone to target bone. """
    bone1_e = obj.data.edit_bones[bone_name]
    bone2_e = obj.data.edit_bones[target_bone_name]

    axis = bone2_e.y_axis.normalized() * bone1_e.length

    bone1_e.tail = bone1_e.head + axis
    bone1_e.roll = bone2_e.roll


def align_bone_roll(obj, bone1, bone2):
    """ Aligns the roll of two bones.
    """
    bone1_e = obj.data.edit_bones[bone1]
    bone2_e = obj.data.edit_bones[bone2]

    bone1_e.roll = 0.0

    # Get the directions the bones are pointing in, as vectors
    y1 = bone1_e.y_axis
    x1 = bone1_e.x_axis
    y2 = bone2_e.y_axis
    x2 = bone2_e.x_axis

    # Get the shortest axis to rotate bone1 on to point in the same direction as bone2
    axis = y1.cross(y2)
    axis.normalize()

    # Angle to rotate on that shortest axis
    angle = y1.angle(y2)

    # Create rotation matrix to make bone1 point in the same direction as bone2
    rot_mat = Matrix.Rotation(angle, 3, axis)

    # Roll factor
    x3 = rot_mat @ x1
    dot = x2 @ x3
    if dot > 1.0:
        dot = 1.0
    elif dot < -1.0:
        dot = -1.0
    roll = math.acos(dot)

    # Set the roll
    bone1_e.roll = roll

    # Check if we rolled in the right direction
    x3 = rot_mat @ bone1_e.x_axis
    check = x2 @ x3

    # If not, reverse
    if check < 0.9999:
        bone1_e.roll = -roll


def align_bone_x_axis(obj, bone, vec):
    """ Rolls the bone to align its x-axis as closely as possible to
        the given vector.
        Must be in edit mode.
    """
    bone_e = obj.data.edit_bones[bone]

    vec = vec.cross(bone_e.y_axis)
    vec.normalize()

    dot = max(-1.0, min(1.0, bone_e.z_axis.dot(vec)))
    angle = math.acos(dot)

    bone_e.roll += angle

    dot1 = bone_e.z_axis.dot(vec)

    bone_e.roll -= angle * 2

    dot2 = bone_e.z_axis.dot(vec)

    if dot1 > dot2:
        bone_e.roll += angle * 2


def align_bone_z_axis(obj, bone, vec):
    """ Rolls the bone to align its z-axis as closely as possible to
        the given vector.
        Must be in edit mode.
    """
    bone_e = obj.data.edit_bones[bone]

    vec = bone_e.y_axis.cross(vec)
    vec.normalize()

    dot = max(-1.0, min(1.0, bone_e.x_axis.dot(vec)))
    angle = math.acos(dot)

    bone_e.roll += angle

    dot1 = bone_e.x_axis.dot(vec)

    bone_e.roll -= angle * 2

    dot2 = bone_e.x_axis.dot(vec)

    if dot1 > dot2:
        bone_e.roll += angle * 2


def align_bone_y_axis(obj, bone, vec):
    """ Matches the bone y-axis to
        the given vector.
        Must be in edit mode.
    """

    bone_e = obj.data.edit_bones[bone]
    vec.normalize()
    vec = vec * bone_e.length

    bone_e.tail = bone_e.head + vec


def compute_chain_x_axis(obj, bone_names):
    """
    Compute the x axis of all bones to be perpendicular
    to the primary plane in which the bones lie.
    """
    eb = obj.data.edit_bones

    assert(len(bone_names) > 1)
    first_bone = eb[bone_names[0]]
    last_bone = eb[bone_names[-1]]

    # Compute normal to the plane defined by the first bone,
    # and the end of the last bone in the chain
    chain_y_axis = last_bone.tail - first_bone.head
    chain_rot_axis = first_bone.y_axis.cross(chain_y_axis)

    if chain_rot_axis.length < first_bone.length/100:
        return first_bone.x_axis.normalized()
    else:
        return chain_rot_axis.normalized()


def align_chain_x_axis(obj, bone_names):
    """
    Aligns the x axis of all bones to be perpendicular
    to the primary plane in which the bones lie.
    """
    chain_rot_axis = compute_chain_x_axis(obj, bone_names)

    for name in bone_names:
        align_bone_x_axis(obj, name, chain_rot_axis)


def align_bone_to_axis(obj, bone_name, axis, *, length=None, roll=0, flip=False):
    """
    Aligns the Y axis of the bone to the global axis (x,y,z,-x,-y,-z),
    optionally adjusting length and initially flipping the bone.
    """
    bone_e = obj.data.edit_bones[bone_name]

    if length is None:
        length = bone_e.length
    if roll is None:
        roll = bone_e.roll

    if axis[0] == '-':
        length = -length
        axis = axis[1:]

    vec = Vector((0,0,0))
    setattr(vec, axis, length)

    if flip:
        base = Vector(bone_e.tail)
        bone_e.tail = base + vec
        bone_e.head = base
    else:
        bone_e.tail = bone_e.head + vec

    bone_e.roll = roll


def set_bone_widget_transform(obj, bone_name, transform_bone, use_size=True, scale=1.0, target_size=False):
    assert obj.mode != 'EDIT'

    bone = obj.pose.bones[bone_name]

    if transform_bone and transform_bone != bone_name:
        bone.custom_shape_transform = bone2 = obj.pose.bones[transform_bone]
        if use_size and target_size:
            scale *= bone2.length / bone.length
    else:
        bone.custom_shape_transform = None

    bone.use_custom_shape_bone_size = use_size
    bone.custom_shape_scale = scale
