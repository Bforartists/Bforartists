# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import importlib
import importlib.util
import re

from itertools import count
from typing import TYPE_CHECKING, Any, Optional
from bpy.types import bpy_struct, Constraint, Object, PoseBone, Bone, Armature

from bpy.types import bpy_prop_array  # noqa

from .misc import ArmatureObject, wrap_list_to_lines, IdPropSequence

if TYPE_CHECKING:
    from ..base_rig import BaseRig
    from .. import RigifyColorSet, RigifyArmatureLayer


RIG_DIR = "rigs"  # Name of the directory where rig types are kept
METARIG_DIR = "metarigs"  # Name of the directory where metarigs are kept
TEMPLATE_DIR = "ui_templates"  # Name of the directory where ui templates are kept

# noinspection SpellCheckingInspection
outdated_types = {"pitchipoy.limbs.super_limb": "limbs.super_limb",
                  "pitchipoy.limbs.super_arm": "limbs.super_limb",
                  "pitchipoy.limbs.super_leg": "limbs.super_limb",
                  "pitchipoy.limbs.super_front_paw": "limbs.super_limb",
                  "pitchipoy.limbs.super_rear_paw": "limbs.super_limb",
                  "pitchipoy.limbs.super_finger": "limbs.super_finger",
                  "pitchipoy.super_torso_turbo": "spines.super_spine",
                  "pitchipoy.simple_tentacle": "limbs.simple_tentacle",
                  "pitchipoy.super_face": "faces.super_face",
                  "pitchipoy.super_palm": "limbs.super_palm",
                  "pitchipoy.super_copy": "basic.super_copy",
                  "pitchipoy.tentacle": "",
                  "palm": "limbs.super_palm",
                  "basic.copy": "basic.super_copy",
                  "biped.arm": "",
                  "biped.leg": "",
                  "finger": "",
                  "neck_short": "",
                  "misc.delta": "",
                  "spine": ""
                  }


def get_rigify_type(pose_bone: PoseBone) -> str:
    rigify_type = pose_bone.rigify_type  # noqa
    return rigify_type.replace(" ", "")


def get_rigify_params(pose_bone: PoseBone) -> Any:
    return pose_bone.rigify_parameters  # noqa


def get_rigify_colors(arm: Armature) -> IdPropSequence['RigifyColorSet']:
    return arm.rigify_colors  # noqa


def get_rigify_layers(arm: Armature) -> IdPropSequence['RigifyArmatureLayer']:
    return arm.rigify_layers  # noqa


def get_rigify_target_rig(arm: Armature) -> Optional[ArmatureObject]:
    return arm.rigify_target_rig  # noqa


def get_rigify_rig_basename(arm: Armature) -> str:
    return arm.rigify_rig_basename  # noqa


def get_rigify_mirror_widgets(arm: Armature) -> bool:
    return arm.rigify_mirror_widgets  # noqa


def get_rigify_force_widget_update(arm: Armature) -> bool:
    return arm.rigify_force_widget_update  # noqa


def get_rigify_finalize_script(arm: Armature) -> Optional[bpy.types.Text]:
    return arm.rigify_finalize_script  # noqa


def is_rig_base_bone(obj: Object, name):
    return bool(get_rigify_type(obj.pose.bones[name]))


def upgrade_metarig_types(metarig: Object, revert=False):
    """
    Replaces rigify_type properties from old versions with their current names.

    metarig: rig to update.
    revert: revert types to previous version (if old type available)
    """

    if revert:
        vals = list(outdated_types.values())
        rig_defs = {v: k for k, v in outdated_types.items() if vals.count(v) == 1}
    else:
        rig_defs = outdated_types

    for bone in metarig.pose.bones:
        rig_type = bone.rigify_type
        if rig_type in rig_defs:
            bone.rigify_type = rig_defs[rig_type]

            parameters = get_rigify_params(bone)

            if 'leg' in rig_type:
                parameters.limb_type = 'leg'
            if 'arm' in rig_type:
                parameters.limb_type = 'arm'
            if 'paw' in rig_type:
                parameters.limb_type = 'paw'
            if rig_type == "basic.copy":
                parameters.make_widget = False


##############################################
# Misc
##############################################

def rig_is_child(rig: 'BaseRig', parent: Optional['BaseRig'], *, strict=False):
    """
    Checks if the rig is a child of the parent.
    Unless strict is True, returns true if the rig and parent are the same.
    """
    if parent is None:
        return True

    if rig and strict:
        rig = rig.rigify_parent

    while rig:
        if rig is parent:
            return True

        rig = rig.rigify_parent

    return False


def get_parent_rigs(rig: 'BaseRig') -> list['BaseRig']:
    """Returns a list containing the rig and all of its parents."""
    result = []
    while rig:
        result.append(rig)
        rig = rig.rigify_parent
    return result


def get_resource(resource_name):
    """ Fetches a rig module by name, and returns it.
    """
    module = importlib.import_module(resource_name)
    importlib.reload(module)
    return module


def connected_children_names(obj: ArmatureObject, bone_name: str) -> list[str]:
    """ Returns a list of bone names (in order) of the bones that form a single
        connected chain starting with the given bone as a parent.
        If there is a connected branch, the list stops there.
    """
    bone = obj.data.bones[bone_name]
    names = []

    while True:
        connects = 0
        con_name = ""

        for child in bone.children:
            if child.use_connect:
                connects += 1
                con_name = child.name

        if connects == 1:
            names += [con_name]
            bone = obj.data.bones[con_name]
        else:
            break

    return names


def has_connected_children(bone: Bone):
    """ Returns true/false whether a bone has connected children or not.
    """
    t = False
    for b in bone.children:
        t = t or b.use_connect
    return t


def _list_bone_names_depth_first_sorted_rec(result_list: list[str], bone: Bone):
    result_list.append(bone.name)

    for child in sorted(list(bone.children), key=lambda b: b.name):
        _list_bone_names_depth_first_sorted_rec(result_list, child)


def list_bone_names_depth_first_sorted(obj: ArmatureObject):
    """Returns a list of bone names in depth first name sorted order."""
    result_list = []

    for bone in sorted(list(obj.data.bones), key=lambda b: b.name):
        if bone.parent is None:
            _list_bone_names_depth_first_sorted_rec(result_list, bone)

    return result_list


def _get_property_value(obj, name: str):
    """Retrieve the attribute value, converting from Blender to python types."""
    value = getattr(obj, name, None)
    if isinstance(value, bpy_prop_array):
        value = tuple(value)
    return value


def _format_property_value(prefix: str, value: Any, *, limit=90, indent=4) -> list[str]:
    """Format a property value assignment to lines, wrapping if too long."""

    if isinstance(value, tuple):
        return wrap_list_to_lines(prefix, '()', map(repr, value), limit=limit, indent=indent)

    if isinstance(value, list):
        return wrap_list_to_lines(prefix, '[]', map(repr, value), limit=limit, indent=indent)

    return [prefix + repr(value)]


def _generate_properties(lines, prefix, obj: bpy_struct, base_class: type, *,
                         defaults: Optional[dict[str, Any]] = None,
                         objects: Optional[dict[Any, str]] = None):
    obj_rna: bpy.types.Struct = type(obj).bl_rna  # noqa
    base_rna: bpy.types.Struct = base_class.bl_rna  # noqa

    defaults = defaults or {}
    block_props = set(prop.identifier for prop in base_rna.properties) - set(defaults.keys())

    for prop in obj_rna.properties:
        if prop.identifier not in block_props and not prop.is_readonly:
            cur_value = _get_property_value(obj, prop.identifier)

            if prop.identifier in defaults:
                if cur_value == defaults[prop.identifier]:
                    continue

            if isinstance(cur_value, bpy_struct):
                if objects and cur_value in objects:
                    lines.append('%s.%s = %s' % (prefix, prop.identifier, objects[cur_value]))
            else:
                lines += _format_property_value('%s.%s = ' % (prefix, prop.identifier), cur_value)


def write_metarig_widgets(obj: Object):
    from .widgets import write_widget

    widget_set = set()

    for pbone in obj.pose.bones:
        if pbone.custom_shape:
            widget_set.add(pbone.custom_shape)

    id_set = set()
    widget_map = {}
    code = []

    for widget_obj in widget_set:
        ident = re.sub("[^0-9a-zA-Z_]+", "_", widget_obj.name)

        if ident in id_set:
            for i in count(1):
                if ident+'_'+str(i) not in id_set:
                    break

        id_set.add(ident)
        widget_map[widget_obj] = ident

        code.append(write_widget(widget_obj, name=ident, use_size=False))

    return widget_map, code


def write_metarig(obj: ArmatureObject, layers=False, func_name="create",
                  groups=False, widgets=False):
    """
    Write a metarig as a python script, this rig is to have all info needed for
    generating the real rig with rigify.
    """
    code = [
        "import bpy\n",
        "from mathutils import Color\n\n",
    ]

    # Widget object creation functions if requested
    if widgets:
        widget_map, widget_code = write_metarig_widgets(obj)

        if widget_map:
            code.append("from rigify.utils.widgets import widget_generator\n\n")
            code += widget_code
    else:
        widget_map = {}

    # Start of the metarig function
    code.append("def %s(obj):  # noqa" % func_name)
    code.append("    # generated by rigify.utils.write_metarig")
    bpy.ops.object.mode_set(mode='EDIT')
    code.append("    bpy.ops.object.mode_set(mode='EDIT')")
    code.append("    arm = obj.data")

    arm = obj.data

    # Rigify bone group colors info
    rigify_colors = get_rigify_colors(arm)

    if groups and len(rigify_colors) > 0:
        code.append("\n    for i in range(" + str(len(rigify_colors)) + "):")
        code.append("        arm.rigify_colors.add()\n")

        for i in range(len(rigify_colors)):
            name = rigify_colors[i].name
            active = rigify_colors[i].active
            normal = rigify_colors[i].normal
            select = rigify_colors[i].select
            standard_colors_lock = rigify_colors[i].standard_colors_lock
            code.append('    arm.rigify_colors[' + str(i) + '].name = "' + name + '"')
            code.append('    arm.rigify_colors[' + str(i)
                        + '].active = Color((%.4f, %.4f, %.4f))' % tuple(active[:]))
            code.append('    arm.rigify_colors[' + str(i)
                        + '].normal = Color((%.4f, %.4f, %.4f))' % tuple(normal[:]))
            code.append('    arm.rigify_colors[' + str(i)
                        + '].select = Color((%.4f, %.4f, %.4f))' % tuple(select[:]))
            code.append('    arm.rigify_colors[' + str(i)
                        + '].standard_colors_lock = ' + str(standard_colors_lock))

    # Rigify layer layout info
    rigify_layers = get_rigify_layers(arm)

    if layers and len(rigify_layers) > 0:
        code.append("\n    for i in range(" + str(len(rigify_layers)) + "):")
        code.append("        arm.rigify_layers.add()\n")

        for i in range(len(rigify_layers)):
            name = rigify_layers[i].name
            row = rigify_layers[i].row
            selset = rigify_layers[i].selset
            group = rigify_layers[i].group
            code.append('    arm.rigify_layers[' + str(i) + '].name = "' + name + '"')
            code.append('    arm.rigify_layers[' + str(i) + '].row = ' + str(row))
            code.append('    arm.rigify_layers[' + str(i) + '].selset = ' + str(selset))
            code.append('    arm.rigify_layers[' + str(i) + '].group = ' + str(group))

    # write parents first
    bones = [(len(bone.parent_recursive), bone.name) for bone in arm.edit_bones]
    bones.sort(key=lambda item: item[0])
    bones = [item[1] for item in bones]

    code.append("\n    bones = {}\n")

    for bone_name in bones:
        bone = arm.edit_bones[bone_name]
        code.append("    bone = arm.edit_bones.new(%r)" % bone.name)
        code.append("    bone.head = %.4f, %.4f, %.4f" % bone.head.to_tuple(4))
        code.append("    bone.tail = %.4f, %.4f, %.4f" % bone.tail.to_tuple(4))
        code.append("    bone.roll = %.4f" % bone.roll)
        code.append("    bone.use_connect = %s" % str(bone.use_connect))
        if bone.inherit_scale != 'FULL':
            code.append("    bone.inherit_scale = %r" % str(bone.inherit_scale))
        if bone.parent:
            code.append("    bone.parent = arm.edit_bones[bones[%r]]" % bone.parent.name)
        code.append("    bones[%r] = bone.name" % bone.name)

    bpy.ops.object.mode_set(mode='OBJECT')
    code.append("")
    code.append("    bpy.ops.object.mode_set(mode='OBJECT')")

    if widgets and widget_map:
        code.append("    widget_map = {}")

    # Rig type and other pose properties
    for bone_name in bones:
        pbone = obj.pose.bones[bone_name]

        rigify_type = get_rigify_type(pbone)
        rigify_parameters = get_rigify_params(pbone)

        code.append("    pbone = obj.pose.bones[bones[%r]]" % bone_name)
        code.append("    pbone.rigify_type = %r" % rigify_type)
        code.append("    pbone.lock_location = %s" % str(tuple(pbone.lock_location)))
        code.append("    pbone.lock_rotation = %s" % str(tuple(pbone.lock_rotation)))
        code.append("    pbone.lock_rotation_w = %s" % str(pbone.lock_rotation_w))
        code.append("    pbone.lock_scale = %s" % str(tuple(pbone.lock_scale)))
        code.append("    pbone.rotation_mode = %r" % pbone.rotation_mode)
        if layers:
            bone_layers = pbone.bone.layers
            code += _format_property_value("    pbone.bone.layers = ", list(bone_layers))

        # Rig type parameters
        for param_name in rigify_parameters.keys():
            param = _get_property_value(rigify_parameters, param_name)
            if param is not None:
                code.append("    try:")
                code += _format_property_value(
                    f"        pbone.rigify_parameters.{param_name} = ", param)
                code.append("    except AttributeError:")
                code.append("        pass")

        # Constraints
        for con in pbone.constraints:
            code.append("    con = pbone.constraints.new(%r)" % con.type)
            code.append("    con.name = %r" % con.name)
            # Add target first because of target_space handling
            if con.type == 'ARMATURE':
                for tgt in con.targets:
                    code.append("    tgt = con.targets.new()")
                    code.append("    tgt.target = obj")
                    code.append("    tgt.subtarget = %r" % tgt.subtarget)
                    code.append("    tgt.weight = %.3f" % tgt.weight)
            elif getattr(con, 'target', None) == obj:
                code.append("    con.target = obj")
            # Generic properties
            _generate_properties(
                code, "    con", con, Constraint,
                defaults={
                    'owner_space': 'WORLD', 'target_space': 'WORLD',
                    'mute': False, 'influence': 1.0,
                    'target': obj,
                },
                objects={obj: 'obj'},
            )
        # Custom widgets
        if widgets and pbone.custom_shape:
            widget_id = widget_map[pbone.custom_shape]
            code.append("    if %r not in widget_map:" % widget_id)
            code.append(("        widget_map[%r] = create_%s_widget(obj, pbone.name, "
                         "widget_name=%r, widget_force_new=True)")
                        % (widget_id, widget_id, pbone.custom_shape.name))
            code.append("    pbone.custom_shape = widget_map[%r]" % widget_id)

    code.append("\n    bpy.ops.object.mode_set(mode='EDIT')")
    code.append("    for bone in arm.edit_bones:")
    code.append("        bone.select = False")
    code.append("        bone.select_head = False")
    code.append("        bone.select_tail = False")

    code.append("    for b in bones:")
    code.append("        bone = arm.edit_bones[bones[b]]")
    code.append("        bone.select = True")
    code.append("        bone.select_head = True")
    code.append("        bone.select_tail = True")
    code.append("        bone.bbone_x = bone.bbone_z = bone.length * 0.05")
    code.append("        arm.edit_bones.active = bone")

    # Set appropriate layers visible
    if layers:
        # Find what layers have bones on them
        active_layers = []
        for bone_name in bones:
            bone = obj.data.bones[bone_name]
            for i in range(len(bone.layers)):
                if bone.layers[i]:
                    if i not in active_layers:
                        active_layers.append(i)
        active_layers.sort()

        code.append("\n    arm.layers = [(x in " + str(active_layers) +
                    ") for x in range(" + str(len(arm.layers)) + ")]")

    code.append("\n    return bones")

    code.append('\n\nif __name__ == "__main__":')
    code.append("    " + func_name + "(bpy.context.active_object)\n")

    return "\n".join(code)
