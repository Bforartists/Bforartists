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

from rna_prop_ui import rna_idprop_ui_create

#=============================================
# Constraint creation utilities
#=============================================

_TRACK_AXIS_MAP =  {
    'X': 'TRACK_X', '-X': 'TRACK_NEGATIVE_X',
    'Y': 'TRACK_Y', '-Y': 'TRACK_NEGATIVE_Y',
    'Z': 'TRACK_Z', '-Z': 'TRACK_NEGATIVE_Z',
}

def make_constraint(
        owner, type, target=None, subtarget=None, *,
        space=None, track_axis=None, use_xyz=None,
        **options):
    """
    Creates and initializes constraint of the specified type for the owner bone.

    Specially handled keyword arguments:

      target, subtarget: if both not None, passed through to the constraint
      space            : assigned to both owner_space and target_space
      track_axis       : allows shorter X, Y, Z, -X, -Y, -Z notation
      use_xyz          : list of 3 items is assigned to use_x, use_y and use_z options
      min/max_x/y/z    : a corresponding use_min/max_x/y/z option is set to True

    Other keyword arguments are directly assigned to the constraint options.
    Returns the newly created constraint.
    """
    con = owner.constraints.new(type)

    if target is not None and hasattr(con, 'target'):
        con.target = target

    if subtarget is not None:
        con.subtarget = subtarget

    if space is not None:
        con.owner_space = con.target_space = space

    if track_axis is not None:
        con.track_axis = _TRACK_AXIS_MAP.get(track_axis, track_axis)

    if use_xyz is not None:
        con.use_x, con.use_y, con.use_z = use_xyz[0:3]

    for key in ['min_x', 'max_x', 'min_y', 'max_y', 'min_z', 'max_z']:
        if key in options and 'use_'+key not in options:
            options['use_'+key] = True

    for p, v in options.items():
        setattr(con, p, v)

    return con

#=============================================
# Custom property creation utilities
#=============================================

def make_property(owner, name, default, *, min=0.0, max=1.0, soft_min=None, soft_max=None, description=None, overridable=True):
    """
    Creates and initializes a custom property of owner.

    The soft_min and soft_max parameters default to min and max.
    Description defaults to the property name.
    """

    # Some keyword argument defaults differ
    return rna_idprop_ui_create(
        owner, name, default = default,
        min = min, max = max, soft_min = soft_min, soft_max = soft_max,
        description = description or name,
        overridable = overridable,
    )

#=============================================
# Driver creation utilities
#=============================================

def _init_driver_target(drv_target, var_info, target_id):
    """Initialize a driver variable target from a specification."""

    # Parse the simple list format for the common case.
    if isinstance(var_info, tuple):
        # [ (target_id,) subtarget, ...path ]

        # If target_id is supplied as parameter, allow omitting it
        if target_id is None or isinstance(var_info[0], bpy.types.ID):
            target_id,subtarget,*refs = var_info
        else:
            subtarget,*refs = var_info

        # Simple path string case.
        if len(refs) == 0:
            # [ (target_id,) path_str ]
            path = subtarget
        else:
            # If subtarget is a string, look up a bone in the target
            if isinstance(subtarget, str):
                subtarget = target_id.pose.bones[subtarget]

            # Use ".foo" type path items verbatim, otherwise quote
            path = subtarget.path_from_id()
            for item in refs:
                path += item if item[0] == '.' else '["'+item+'"]'

        drv_target.id = target_id
        drv_target.data_path = path

    else:
        # { 'id': ..., ... }
        target_id = var_info.get('id', target_id)

        if target_id is not None:
            drv_target.id = target_id

        for tp, tv in var_info.items():
            setattr(drv_target, tp, tv)


def _add_driver_variable(drv, var_name, var_info, target_id):
    """Add and initialize a driver variable."""

    var = drv.variables.new()
    var.name = var_name

    # Parse the simple list format for the common case.
    if isinstance(var_info, tuple):
        # [ (target_id,) subtarget, ...path ]
        var.type = "SINGLE_PROP"

        _init_driver_target(var.targets[0], var_info, target_id)

    else:
        # Variable info as generic dictionary - assign properties.
        # { 'type': 'SINGLE_PROP', 'targets':[...] }
        var.type = var_info['type']

        for p, v in var_info.items():
            if p == 'targets':
                for i, tdata in enumerate(v):
                    _init_driver_target(var.targets[i], tdata, target_id)
            elif p != 'type':
                setattr(var, p, v)

def make_driver(owner, prop, *, index=-1, type='SUM', expression=None, variables={}, polynomial=None, target_id=None):
    """
    Creates and initializes a driver for the 'prop' property of owner.

    Arguments:
      index           : item index for vector properties
      type, expression: mutually exclusive options to set core driver mode.
      variables       : either a list or dictionary of variable specifications.
      polynomial      : coefficients of the POLYNOMIAL driver modifier
      target_id       : specifies the target ID of variables implicitly

    Specification format:
        If the variables argument is a dictionary, keys specify variable names.
        Otherwise names are set to var, var1, var2, ... etc:

          variables = [ ..., ..., ... ]
          variables = { 'var': ..., 'var1': ..., 'var2': ... }

        Variable specifications are constructed as nested dictionaries and lists that
        follow the property structure of the original Blender objects, but the most
        common case can be abbreviated as a simple tuple.

        The following specifications are equivalent:

          ( target, subtarget, '.foo', 'bar' )

          { 'type': 'SINGLE_PROP', 'targets':[( target, subtarget, '.foo', 'bar' )] }

          { 'type': 'SINGLE_PROP',
            'targets':[{ 'id': target, 'data_path': subtarget.path_from_id() + '.foo["bar"]' }] }

        If subtarget is as string, it is automatically looked up within target as a bone.

        It is possible to specify path directly as a simple string without following items:

          ( target, 'path' )

          { 'type': 'SINGLE_PROP', 'targets':[{ 'id': target, 'data_path': 'path' }] }

        If the target_id parameter is not None, it is possible to omit target:

          ( subtarget, '.foo', 'bar' )

          { 'type': 'SINGLE_PROP',
            'targets':[{ 'id': target_id, 'data_path': subtarget.path_from_id() + '.foo["bar"]' }] }

    Returns the newly created driver FCurve.
    """
    fcu = owner.driver_add(prop, index)
    drv = fcu.driver

    if expression is not None:
        drv.type = 'SCRIPTED'
        drv.expression = expression
    else:
        drv.type = type

    if isinstance(variables, list):
        # variables = [ info, ... ]
        for i, var_info in enumerate(variables):
            var_name = 'var' if i == 0 else 'var' + str(i)
            _add_driver_variable(drv, var_name, var_info, target_id)
    else:
        # variables = { 'varname': info, ... }
        for var_name, var_info in variables.items():
            _add_driver_variable(drv, var_name, var_info, target_id)

    if polynomial is not None:
        drv_modifier = fcu.modifiers[0]
        drv_modifier.mode = 'POLYNOMIAL'
        drv_modifier.poly_order = len(polynomial)-1
        for i,v in enumerate(polynomial):
            drv_modifier.coefficients[i] = v

    return fcu


def driver_var_transform(target, bone=None, *, type='LOC_X', space='WORLD'):
    """
    Create a Transform Channel driver variable specification.

    Usage:
        make_driver(..., variables=[driver_var_transform(...)])
    """

    assert space in {'WORLD', 'TRANSFORM', 'LOCAL'}

    target_map = {
        'id': target,
        'transform_type': type,
        'transform_space': space + '_SPACE',
    }

    if bone is not None:
        target_map['bone_target'] = bone

    return { 'type': 'TRANSFORMS', 'targets': [ target_map ] }


#=============================================
# Utility mixin
#=============================================

class MechanismUtilityMixin(object):
    """
    Provides methods for more convenient creation of constraints, properties
    and drivers within an armature (by implicitly providing context).

    Requires self.obj to be the armature object being worked on.
    """

    def make_constraint(self, bone, type, subtarget=None, **args):
        assert(self.obj.mode == 'OBJECT')
        return make_constraint(self.obj.pose.bones[bone], type, self.obj, subtarget, **args)

    def make_property(self, bone, name, default, **args):
        assert(self.obj.mode == 'OBJECT')
        return make_property(self.obj.pose.bones[bone], name, default, **args)

    def make_driver(self, owner, prop, **args):
        assert(self.obj.mode == 'OBJECT')
        if isinstance(owner, str):
            owner = self.obj.pose.bones[owner]
        return make_driver(owner, prop, target_id=self.obj, **args)
